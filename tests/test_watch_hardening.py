#!/usr/bin/env python3
"""Issue #2101: watch-layer hardening — lease/TTL auto-requeue,
progress-carrying renewal, level-triggered reconcile sweep, dead-man's
switch, declared waits.

Everything under test is ADVISORY-ONLY per the watch-coverage policy:
mechanisms print advisories, write ledger events, and return items to
dispatchable state — they never block, refuse, or kill. A regression test
asserts no watch-class path gained blocking behavior.
"""
import inspect
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent))
import spawn
import roster

from _spawn_test_support import *  # noqa: F401,F403


class _LedgerSpy:
    def __init__(self):
        self.events = []

    def __call__(self, entry):
        self.events.append(entry)

    def named(self, event):
        return [e for e in self.events if e.get("event") == event]


def _entry(td, key="issue-7/implementation", **kw):
    """A roster entry with a real workspace dir (for claim/wait files)."""
    work = Path(td) / "ws" / key.replace("/", "-")
    work.mkdir(parents=True, exist_ok=True)
    e = {"pid": 1, "issue": 7, "role": "implementation", "work": str(work),
         "log": str(Path(td) / "log.jsonl"), "ts": time.time()}
    e.update(kw)
    return key, e


class _HardeningCase(unittest.TestCase):
    """Shared fixture: isolated roster file, spied ledger, silenced dedup."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        td = Path(self._td.name)
        self.addCleanup(self._td.cleanup)
        self.root = td / "board"
        self.root.mkdir()
        self.ledger = _LedgerSpy()
        patches = [
            mock.patch.object(spawn, "ROSTER", td / "runs" / "active.json"),
            mock.patch.object(spawn, "DEADMAN_MARKER",
                              td / "runs" / "watch-coverage-ok"),
            mock.patch.object(spawn, "ledger_write", self.ledger),
            # Dedup always admits: these tests assert single-call behavior.
            mock.patch.object(spawn, "ledger_check_and_stamp",
                              lambda *a, **k: True),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.td = td


class LeaseExpiryRequeue(_HardeningCase):
    """Mechanism 1: expired lease => item dispatchable again in one sweep."""

    def test_expired_lease_requeues_within_one_sweep(self):
        now = time.time()
        key, e = _entry(self.td, lease_expires_at=now - 5)
        claim = spawn._spawn_claim_path(e["work"])
        claim.write_text(json.dumps({"pid": 12345, "ts": 1}))
        spawn.roster_register(key, e)
        d_all = spawn._roster_load()
        with mock.patch.object(spawn, "_alive", return_value=False):
            count = spawn.lease_reconcile_sweep(root=self.root, d_all=d_all,
                                                now=now)
        self.assertGreaterEqual(count, 1)
        # State change: roster entry gone, spawn claim gone => dispatchable.
        self.assertNotIn(key, spawn._roster_load())
        self.assertFalse(claim.exists())
        self.assertNotIn(key, d_all)  # not re-reported by the same tick
        events = self.ledger.named("lease_expired_requeued")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["key"], key)
        self.assertEqual(events[0]["issue"], 7)

    def test_unexpired_lease_dead_session_is_advisory_not_requeued(self):
        """Mechanism 3: claimed item with no live session but a still-valid
        lease is surfaced as a discrepancy advisory, never requeued."""
        now = time.time()
        key, e = _entry(self.td, lease_expires_at=now + 3600)
        spawn.roster_register(key, e)
        d_all = spawn._roster_load()
        with mock.patch.object(spawn, "_alive", return_value=False):
            spawn.lease_reconcile_sweep(root=self.root, d_all=d_all, now=now)
        self.assertIn(key, spawn._roster_load())  # claim kept
        self.assertEqual(self.ledger.named("lease_expired_requeued"), [])
        events = self.ledger.named("claim_without_live_session")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["key"], key)

    def test_requeue_path_contains_no_detector_logic(self):
        """The requeue path is self-correcting: ledger event + state change
        only. No log classification, health diagnosis, or liveness
        heuristics execute inside it."""
        src = inspect.getsource(spawn._lease_requeue)
        for detector in ("watchdog_check_one", "diagnose_health",
                         "session_end_verdict", "_classify", "_alive",
                         "_deadlock_signature", "heartbeat"):
            self.assertNotIn(detector, src)


class FlatProgressRenewal(_HardeningCase):
    """Mechanism 2: K flat renewals => STALLED-FLAT-PROGRESS advisory;
    mechanism 5: a valid declared wait exempts."""

    def _renew_flat(self, e, times, now):
        anomalies = []
        with mock.patch.object(spawn, "_lease_progress_indicator",
                               return_value="42:abc"):
            for i in range(times):
                anomalies = spawn.lease_renew("issue-7/implementation", e,
                                              root=self.root, now=now + i)
        return anomalies

    def test_flat_progress_x_k_renewals_yields_advisory(self):
        now = time.time()
        _, e = _entry(self.td)
        anomalies = self._renew_flat(e, spawn.LEASE_FLAT_RENEWALS_K + 1, now)
        self.assertEqual(len(anomalies), 1)
        self.assertTrue(anomalies[0].startswith("flat-progress"))
        self.assertIn("advisory", anomalies[0])
        # Renewal carried the lease forward regardless of flatness.
        self.assertGreater(e["lease_expires_at"], now)

    def test_progress_change_resets_flat_counter(self):
        now = time.time()
        _, e = _entry(self.td)
        self._renew_flat(e, spawn.LEASE_FLAT_RENEWALS_K, now)
        with mock.patch.object(spawn, "_lease_progress_indicator",
                               return_value="43:def"):
            anomalies = spawn.lease_renew("issue-7/implementation", e,
                                          root=self.root, now=now + 99)
        self.assertEqual(anomalies, [])
        self.assertEqual(e["lease_flat_renewals"], 0)

    def test_valid_declared_wait_exempts_flat_progress(self):
        """OpenHands false-positive lesson: a session with a valid declared
        wait (existing awaited object) is not classified hung."""
        now = time.time()
        _, e = _entry(self.td)
        (self.root / spawn.BOARD / "issue-9").mkdir(parents=True)
        (Path(e["work"]) / spawn.DECLARED_WAIT_FILENAME).write_text(
            json.dumps({"object": "issue:9"}))
        anomalies = self._renew_flat(e, spawn.LEASE_FLAT_RENEWALS_K + 2, now)
        self.assertEqual(anomalies, [])

    def test_wait_on_missing_object_does_not_exempt(self):
        now = time.time()
        _, e = _entry(self.td)
        (Path(e["work"]) / spawn.DECLARED_WAIT_FILENAME).write_text(
            json.dumps({"object": "issue:9"}))  # no such board subject
        anomalies = self._renew_flat(e, spawn.LEASE_FLAT_RENEWALS_K + 1, now)
        self.assertEqual(len(anomalies), 1)

    def test_diagnose_health_maps_flat_progress_to_advisory_state(self):
        """The #1966 classifier vocabulary gained STALLED-FLAT-PROGRESS;
        next_action stays resume-watch (re-observe only)."""
        _, e = _entry(self.td)
        with mock.patch.object(spawn, "_alive", return_value=True), \
             mock.patch.object(spawn, "_deadlock_signature",
                               return_value=None):
            health = spawn.diagnose_health(
                "issue-7/implementation", e, root=self.root,
                anomalies=["flat-progress: lease renewed 3x (advisory)"])
        self.assertEqual(health["state"], "STALLED-FLAT-PROGRESS")
        self.assertEqual(health["next_action"], "resume-watch")

    def test_tool_call_activity_without_commits_is_not_flat(self):
        """Issue #2188: a session issuing tool calls (reading source, no
        commits) across several lease renewals must not trip
        STALLED-FLAT-PROGRESS -- regression for the issue-2186 shape
        (`sed -n '190,235p' tests/...` mid-investigation: transcript log
        growing every tick, events.jsonl/HEAD untouched because reads
        never hit a Write/Edit or a commit-shaped Bash prefix)."""
        now = time.time()
        key, e = _entry(self.td)
        log_path = Path(e["log"])
        anomalies = []
        for i in range(spawn.LEASE_FLAT_RENEWALS_K + 2):
            # Each tick appends a transcript line, as a live session's tool
            # calls (Read/Grep/sed/TaskOutput/...) would -- events.jsonl and
            # HEAD stay flat the whole time.
            with log_path.open("a") as fh:
                fh.write(json.dumps({"type": "tool_use", "n": i}) + "\n")
            anomalies = spawn.lease_renew(key, e, root=self.root, now=now + i)
        self.assertEqual(anomalies, [])
        self.assertEqual(e["lease_flat_renewals"], 0)

    def test_true_stall_with_no_log_growth_still_flags(self):
        """Regression guard (issue #2188): widening the indicator to cover
        tool-call activity must not blind the check entirely -- a session
        that genuinely issues no tool calls (log never grows, no commits)
        across K renewals is still reported."""
        now = time.time()
        key, e = _entry(self.td)  # log.jsonl path named but never written
        anomalies = []
        for i in range(spawn.LEASE_FLAT_RENEWALS_K + 1):
            anomalies = spawn.lease_renew(key, e, root=self.root, now=now + i)
        self.assertEqual(len(anomalies), 1)
        self.assertTrue(anomalies[0].startswith("flat-progress"))


class ReconcileSweepDeclaredWaits(_HardeningCase):
    """Mechanism 3+5: the sweep verifies declared waits reference existing
    objects."""

    def test_wait_on_nonexistent_object_is_surfaced(self):
        now = time.time()
        key, e = _entry(self.td)
        (Path(e["work"]) / spawn.DECLARED_WAIT_FILENAME).write_text(
            json.dumps({"object": "issue:404"}))
        with mock.patch.object(spawn, "_alive", return_value=True):
            count = spawn.lease_reconcile_sweep(root=self.root,
                                                d_all={key: e}, now=now)
        self.assertEqual(count, 1)
        events = self.ledger.named("declared_wait_missing_object")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["object"], "issue:404")

    def test_wait_on_existing_path_object_is_clean(self):
        now = time.time()
        key, e = _entry(self.td)
        awaited = Path(e["work"]) / "artifact.md"
        awaited.write_text("x")
        (Path(e["work"]) / spawn.DECLARED_WAIT_FILENAME).write_text(
            json.dumps({"object": "artifact.md"}))
        with mock.patch.object(spawn, "_alive", return_value=True):
            count = spawn.lease_reconcile_sweep(root=self.root,
                                                d_all={key: e}, now=now)
        self.assertEqual(count, 0)
        self.assertEqual(self.ledger.named("declared_wait_missing_object"), [])


class ApprovalWaitSurfacing(_HardeningCase):
    """Issue #2133: a HEALTHY checkpoint-mode approval pause is actively
    surfaced every tick — [awaiting-approval] line with remaining time,
    [EXPIRING] under 20% budget, one ledger event per wait instance."""

    def _wait_file(self, e, **fields):
        payload = {"object": "issue:9", "reason": "approve-token",
                   "issue": 9, "role": "implementation"}
        payload.update(fields)
        (Path(e["work"]) / spawn.DECLARED_WAIT_FILENAME).write_text(
            json.dumps(payload))

    def _sweep(self, key, e, now):
        import io, contextlib
        buf = io.StringIO()
        with mock.patch.object(spawn, "_alive", return_value=True), \
             contextlib.redirect_stdout(buf):
            count = spawn.lease_reconcile_sweep(root=self.root,
                                                d_all={key: e}, now=now)
        return count, buf.getvalue()

    def test_healthy_wait_emits_line_with_issue_role_remaining(self):
        now = time.time()
        key, e = _entry(self.td, key="issue-9/implementation", issue=9)
        (self.root / spawn.BOARD / "issue-9").mkdir(parents=True)
        self._wait_file(e, ts=now - 300, budget_sec=1800)
        count, out = self._sweep(key, e, now)
        self.assertIn("[awaiting-approval] issue-9/implementation: "
                      "APPROVE issue-9/implementation needed, "
                      "25m remaining of 30m", out)
        self.assertNotIn("[EXPIRING]", out)
        self.assertEqual(count, 0)  # a healthy wait is not an anomaly
        events = self.ledger.named("approval_wait_surfaced")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["issue"], 9)
        self.assertEqual(events[0]["role"], "implementation")

    def test_under_20_percent_budget_flips_expiring_prefix(self):
        now = time.time()
        key, e = _entry(self.td, key="issue-9/implementation", issue=9)
        (self.root / spawn.BOARD / "issue-9").mkdir(parents=True)
        self._wait_file(e, ts=now - 1500, budget_sec=1800)  # 300s < 20%
        _, out = self._sweep(key, e, now)
        self.assertIn("[awaiting-approval][EXPIRING] issue-9/implementation",
                      out)
        self.assertIn("5m remaining of 30m", out)

    def test_ledger_event_once_per_wait_instance(self):
        now = time.time()
        key, e = _entry(self.td, key="issue-9/implementation", issue=9)
        (self.root / spawn.BOARD / "issue-9").mkdir(parents=True)
        stamped = set()

        def once_per_key(dedup_key, *a, **k):
            if dedup_key in stamped:
                return False
            stamped.add(dedup_key)
            return True

        with mock.patch.object(spawn, "ledger_check_and_stamp",
                               once_per_key):
            self._wait_file(e, ts=int(now - 300), budget_sec=1800)
            self._sweep(key, e, now)
            self._sweep(key, e, now + 60)  # same instance, second tick
            self.assertEqual(
                len(self.ledger.named("approval_wait_surfaced")), 1)
            self._wait_file(e, ts=int(now + 100), budget_sec=1800)
            self._sweep(key, e, now + 200)  # NEW wait instance (new ts)
            self.assertEqual(
                len(self.ledger.named("approval_wait_surfaced")), 2)

    def test_wait_file_without_timestamp_fields_is_remaining_unknown(self):
        """Compat: a pre-#2133 wait file (no ts/budget_sec) surfaces as
        remaining unknown — never a crash."""
        now = time.time()
        key, e = _entry(self.td, key="issue-9/implementation", issue=9)
        (self.root / spawn.BOARD / "issue-9").mkdir(parents=True)
        (Path(e["work"]) / spawn.DECLARED_WAIT_FILENAME).write_text(
            json.dumps({"object": "issue:9", "reason": "approve-token",
                        "issue": 9, "role": "implementation"}))
        count, out = self._sweep(key, e, now)
        self.assertIn("[awaiting-approval] issue-9/implementation: "
                      "APPROVE issue-9/implementation needed, "
                      "remaining unknown", out)
        self.assertNotIn("[EXPIRING]", out)
        self.assertEqual(count, 0)

    def test_garbage_timestamp_fields_never_crash(self):
        now = time.time()
        key, e = _entry(self.td, key="issue-9/implementation", issue=9)
        (self.root / spawn.BOARD / "issue-9").mkdir(parents=True)
        for ts, budget in [("soon", 1800), (now, "lots"), (now, 0),
                           (True, True), (None, None)]:
            self._wait_file(e, ts=ts, budget_sec=budget)
            _, out = self._sweep(key, e, now)
            self.assertIn("remaining unknown", out)

    def test_non_approval_wait_emits_nothing(self):
        now = time.time()
        key, e = _entry(self.td)
        awaited = Path(e["work"]) / "artifact.md"
        awaited.write_text("x")
        (Path(e["work"]) / spawn.DECLARED_WAIT_FILENAME).write_text(
            json.dumps({"object": "artifact.md"}))
        _, out = self._sweep(key, e, now)
        self.assertNotIn("awaiting-approval", out)
        self.assertEqual(self.ledger.named("approval_wait_surfaced"), [])

    def test_negative_case_advisories_unchanged(self):
        """Regression: an approve-token wait on a MISSING object still emits
        the declared_wait_missing_object advisory exactly as before (the
        healthy-wait line rides alongside, not instead)."""
        now = time.time()
        key, e = _entry(self.td, key="issue-404/implementation", issue=404)
        self._wait_file(e, object="issue:404", issue=404,
                        ts=now - 60, budget_sec=1800)
        count, out = self._sweep(key, e, now)
        self.assertEqual(
            len(self.ledger.named("declared_wait_missing_object")), 1)
        self.assertIn("missing object", out)
        self.assertEqual(count, 1)


class DeadMansSwitch(_HardeningCase):
    """Mechanism 4: absence of the coverage-OK marker is the alert, checked
    from outside the watchdog process."""

    def test_stale_marker_fires_loud_advisory(self):
        now = time.time()
        stale_by = spawn.DEADMAN_INTERVAL_SEC * spawn.DEADMAN_STALE_INTERVALS
        spawn.deadman_mark(now=now - stale_by - 60)
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = spawn.deadman_check(now=now)
        self.assertEqual(rc, 1)
        self.assertIn("WATCH LAYER ITSELF IS DEAD", buf.getvalue())
        self.assertIn("Advisory only", buf.getvalue())
        self.assertEqual(len(self.ledger.named("deadman_stale")), 1)

    def test_fresh_marker_is_silent(self):
        now = time.time()
        spawn.deadman_mark(now=now - 1)
        self.assertEqual(spawn.deadman_check(now=now), 0)
        self.assertEqual(self.ledger.named("deadman_stale"), [])

    def test_no_marker_yet_is_not_an_alert(self):
        """Fresh install / first tick: no baseline, no false alarm."""
        self.assertEqual(spawn.deadman_check(now=time.time()), 0)

    def test_sweep_refreshes_marker(self):
        now = time.time()
        with mock.patch.object(spawn, "_alive", return_value=True):
            spawn.lease_reconcile_sweep(root=self.root, d_all={}, now=now)
        self.assertTrue(spawn.DEADMAN_MARKER.exists())
        self.assertAlmostEqual(spawn.DEADMAN_MARKER.stat().st_mtime, now,
                               delta=2)

    def test_checkable_outside_watchdog_via_cli_branch(self):
        """`spawn.py deadman-check` exists as a standalone CLI branch so the
        poll hooks can call it without the watchdog process."""
        src = Path(spawn.__file__).read_text(encoding="utf-8")
        self.assertIn('a.role == "deadman-check"', src)
        # The CLI branch calls only deadman_check — no watchdog lock, no
        # roster scan, no canonical guard.
        branch = src.split('a.role == "deadman-check"')[1].split("if a.role")[0]
        self.assertIn("deadman_check()", branch)
        self.assertNotIn("watchdog_lock_acquire", branch)
        self.assertNotIn("roster_watchdog", branch)


class WatchClassNoBlockingRegression(unittest.TestCase):
    """Watch-coverage policy regression guard: no watch-class path added by
    issue #2101 blocks, refuses, exits, or kills."""

    HARDENING_FNS = [
        "lease_renew", "_lease_requeue", "lease_reconcile_sweep",
        "deadman_check", "deadman_mark", "_declared_wait",
        "_declared_wait_object_exists", "_declared_wait_valid",
        "_lease_progress_indicator", "_sweep_completion_in_flight",
        "_surface_approval_wait",  # issue #2133
    ]
    # Constructs that would make a watch-class path blocking or lethal.
    # (Prose like "nothing is blocked" is fine — these are code constructs.)
    FORBIDDEN = ["sys.exit", "SystemExit", "os.kill", "roster_kill",
                 ".terminate(", ".kill(", "raise ", "admission_gate"]

    def test_no_hardening_function_contains_blocking_constructs(self):
        for name in self.HARDENING_FNS:
            src = inspect.getsource(getattr(spawn, name))
            for token in self.FORBIDDEN:
                self.assertNotIn(
                    token, src,
                    f"{name} contains {token!r} — watch-class checks must "
                    f"stay advisory-only (watch-coverage policy)")

    def test_hardening_functions_never_raise_on_garbage(self):
        """Behavioral half of the guard: garbage input yields advisories or
        silence, never an exception (nothing upstream can be blocked by a
        watch-class crash)."""
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(spawn, "ledger_write", lambda e: None), \
                 mock.patch.object(spawn, "ledger_check_and_stamp",
                                   lambda *a, **k: True), \
                 mock.patch.object(spawn, "ROSTER",
                                   Path(td) / "active.json"), \
                 mock.patch.object(spawn, "DEADMAN_MARKER",
                                   Path(td) / "marker"):
                spawn.lease_renew("k", {}, root=Path(td))
                spawn.lease_reconcile_sweep(
                    root=Path(td),
                    d_all={"k": {}, "j": {"pid": "not-an-int",
                                          "work": "/nonexistent"}})
                spawn.deadman_check()
                spawn.deadman_mark()
                self.assertIsNone(spawn._declared_wait("/nonexistent"))
                self.assertFalse(spawn._declared_wait_object_exists(
                    Path(td), None, {"not": "a string"}))
                # issue #2133: garbage wait dict never crashes the surfacer
                spawn._surface_approval_wait(
                    "k", {}, {"reason": "approve-token"}, time.time())


class SpawnAttemptPruneLiveness(unittest.TestCase):
    """Issue #2413: an unresolved spawn-attempt record (`outcome is None`)
    used to be kept forever, so a dead-pid orphan (SIGKILL/OOM/hard crash,
    or — before #2393's pytest-origin guard — a synthetic test fixture
    record) never aged out and was re-reported on every watchdog tick. The
    fix pairs a cheap on-demand liveness probe (`_pid_is_alive`, signal-0
    `os.kill`) with the same `SPAWN_ATTEMPTS_RETENTION_SEC` window the
    adjacent `halted` branch already uses, instead of inventing a new
    knob."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.path = Path(self._td.name) / "spawn-attempts.jsonl"
        patch = mock.patch.object(spawn, "SPAWN_ATTEMPTS_PATH", self.path)
        patch.start()
        self.addCleanup(patch.stop)

    def _write(self, records):
        with self.path.open("w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec) + "\n")

    def _dead_pid(self):
        """A pid guaranteed not to be alive: fork, exit immediately, reap."""
        pid = os.fork()
        if pid == 0:
            os._exit(0)
        os.waitpid(pid, 0)
        return pid

    def _remaining_ids(self):
        return {json.loads(l)["attempt_id"]
                for l in self.path.read_text().splitlines()}

    def test_live_pid_survives_regardless_of_age(self):
        """A genuinely in-flight attempt must never be pruned out from
        under a running spawn — even once it's older than the retention
        window, as long as its pid is still alive."""
        now = time.time()
        old_ts = now - spawn.SPAWN_ATTEMPTS_RETENTION_SEC - 3600
        self._write([{"event": "spawn_attempt", "attempt_id": "a1",
                      "issue": 1, "role": "implementation",
                      "pid": os.getpid(), "ts": old_ts}])
        dropped = spawn._prune_spawn_attempts(now=now)
        self.assertEqual(dropped, 0)
        self.assertIn("a1", self._remaining_ids())

    def test_dead_pid_within_retention_is_kept(self):
        """A pid that died recently (inside the retention window) is kept
        — spawn_attempt_sweep() must still get its chance to report it as
        a halt once SPAWN_ATTEMPT_GRACE_SEC elapses, and to keep
        re-surfacing it for the rest of the retention window."""
        now = time.time()
        dead_pid = self._dead_pid()
        recent_ts = now - 3600  # 1 hour old — well inside the 7-day window
        self._write([{"event": "spawn_attempt", "attempt_id": "a2",
                      "issue": 2, "role": "implementation",
                      "pid": dead_pid, "ts": recent_ts}])
        dropped = spawn._prune_spawn_attempts(now=now)
        self.assertEqual(dropped, 0)
        self.assertIn("a2", self._remaining_ids())

    def test_dead_pid_past_retention_is_pruned(self):
        """The bug: a dead-pid, no-outcome record older than the retention
        window used to be kept forever. Now it's dropped."""
        now = time.time()
        dead_pid = self._dead_pid()
        old_ts = now - spawn.SPAWN_ATTEMPTS_RETENTION_SEC - 3600
        self._write([{"event": "spawn_attempt", "attempt_id": "a3",
                      "issue": 31, "role": "implementation",
                      "pid": dead_pid, "ts": old_ts}])
        dropped = spawn._prune_spawn_attempts(now=now)
        self.assertEqual(dropped, 1)
        self.assertNotIn("a3", self._remaining_ids())

    def test_pid_is_alive_helper(self):
        self.assertTrue(spawn._pid_is_alive(os.getpid()))
        self.assertTrue(spawn._pid_is_alive(str(os.getpid())))
        self.assertFalse(spawn._pid_is_alive(self._dead_pid()))
        self.assertFalse(spawn._pid_is_alive(None))
        self.assertFalse(spawn._pid_is_alive(-1))
        self.assertFalse(spawn._pid_is_alive("not-an-int"))

    def test_string_encoded_live_pid_survives_past_retention(self):
        """Warrant-hunter finding (before-landing, stance 0): a pid
        serialized as a numeric string (ledger corruption/drift, cf.
        commit cea0f583) must still be probed via the OS, not assumed
        dead by the isinstance(pid, int) check alone — a live spawn must
        never be pruned just because its pid was stored as str."""
        now = time.time()
        old_ts = now - spawn.SPAWN_ATTEMPTS_RETENTION_SEC - 3600
        self._write([{"event": "spawn_attempt", "attempt_id": "a4",
                      "issue": 4, "role": "implementation",
                      "pid": str(os.getpid()), "ts": old_ts}])
        dropped = spawn._prune_spawn_attempts(now=now)
        self.assertEqual(dropped, 0)
        self.assertIn("a4", self._remaining_ids())


class SpawnAttemptSweepDedup(unittest.TestCase):
    """Issue #2413: many attempt_ids for the same (issue, role) subject
    (e.g. hundreds of orphaned pytest-fixture records) each independently
    pass the per-attempt_id ledger dedup gate and used to print one line
    apiece in a single watchdog tick — up to 5x repeats reported at filing
    time. Collapse to at most one printed line per subject per tick."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        td = Path(self._td.name)
        self.addCleanup(self._td.cleanup)
        self.path = td / "spawn-attempts.jsonl"
        patches = [
            mock.patch.object(spawn, "SPAWN_ATTEMPTS_PATH", self.path),
            mock.patch.object(spawn, "ledger_write", lambda e: None),
            mock.patch.object(spawn, "ledger_check_and_stamp",
                              lambda *a, **k: True),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def _write(self, records):
        with self.path.open("w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec) + "\n")

    def test_many_attempt_ids_same_subject_prints_once_per_tick(self):
        import io
        import contextlib
        now = time.time()
        old_ts = now - roster.SPAWN_ATTEMPT_GRACE_SEC - 10
        records = [{"event": "spawn_attempt",
                    "attempt_id": f"31:implementation:1:{i}",
                    "issue": 31, "role": "implementation", "pid": 1,
                    "ts": old_ts - i} for i in range(50)]
        self._write(records)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            count = roster.spawn_attempt_sweep(d_all={}, now=now)
        lines = [l for l in buf.getvalue().splitlines() if l.strip()]
        self.assertEqual(len(lines), 1)
        self.assertEqual(count, 1)
        self.assertIn("issue-31/implementation", lines[0])


if __name__ == "__main__":
    unittest.main()
