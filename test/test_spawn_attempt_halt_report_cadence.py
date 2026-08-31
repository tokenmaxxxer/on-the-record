"""issue #2916: an unresolved `"halted"` spawn-attempt used to be re-announced
every `RECONCILE_LEDGER_TTL_SEC` (15 min, shared by every other reconcile
dedup key) for the entire `SPAWN_ATTEMPTS_RETENTION_SEC` (7 days) that
`spawn._prune_spawn_attempts()` deliberately keeps it alive -- ~96
`spawn_attempt_halt_reported` ledger events per day, measured as 105 and 73
for the two unresolved (unknown-skill) attempts named in the issue.

The fix gives that one dedup key (`spawn-attempt-halt:{attempt_id}`, only on
the "still halted" branch of `roster.spawn_attempt_sweep`) a dedicated TTL
(`roster.SPAWN_ATTEMPT_HALT_REPORT_TTL_SEC`, derived from the retention
window: retention / this TTL = 7 reports max) instead of the shared
`RECONCILE_LEDGER_TTL_SEC`. The "no outcome recorded" branch (#2413) and the
resolved-halt path (#2511) are untouched.

  python3 -m pytest test/test_spawn_attempt_halt_report_cadence.py
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import spawn
import roster


def _write_unresolved_halt(path: Path, attempt_id: str, issue: int, skill: str,
                            ts: float, reason: str) -> None:
    """An unresolved halt with no `cwd` key -- `spawn._attempt_issue_closed()`
    returns False without a network call whenever `cwd` is absent, which is
    exactly what an "unknown skill" class halt needs here: no class-recheck,
    no supersession, no issue-closed check ever clears it, matching the two
    live repeaters named in issue #2916."""
    with path.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps({"event": "spawn_attempt", "attempt_id": attempt_id,
                              "issue": issue, "skill": skill, "pid": 4242,
                              "ts": ts}) + "\n")
        fh.write(json.dumps({"event": "spawn_attempt_outcome",
                              "attempt_id": attempt_id, "outcome": "halted",
                              "detail": reason, "ts": ts}) + "\n")


class UnresolvedHaltReportCadenceTest(unittest.TestCase):
    """Acceptance bullet 1: construct an unresolved halt in a throwaway
    STATE_ROOT, drive the sweep across simulated time spanning the full
    retention window, and count emissions for that one attempt_id."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.attempts_path = Path(self._td.name) / "spawn-attempts.jsonl"
        self.reconcile_ledger_path = Path(self._td.name) / "reconcile_ledger.json"
        self.reported: list[dict] = []
        patches = [
            mock.patch.object(spawn, "SPAWN_ATTEMPTS_PATH", self.attempts_path),
            mock.patch.object(spawn, "RECONCILE_LEDGER", self.reconcile_ledger_path),
            mock.patch.object(spawn, "ledger_write", self.reported.append),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        # Real `ledger_check_and_stamp` (plumbing.py, unmocked) does the
        # actual TTL-gated dedup this test exercises -- unlike
        # test_spawn_attempt_staleness.py's fixtures, which mock it away to
        # focus on the class-recheck logic instead.
        self.attempt_id = "2792:unknown-skill-halt-6aac2d26"
        self.issue = 2792
        self.skill = "unknown-skill-halt-6aac2d26"
        self.reason = "skill 'unknown-skill-halt' not found in skill registry"
        self.attempt_ts = 1_800_000_000.0
        _write_unresolved_halt(self.attempts_path, self.attempt_id, self.issue,
                                self.skill, self.attempt_ts, self.reason)

    def _reported_count_for_attempt(self) -> int:
        return sum(1 for ev in self.reported
                   if ev.get("event") == "spawn_attempt_halt_reported"
                   and ev.get("attempt_id") == self.attempt_id)

    def test_bounded_across_full_retention_window(self):
        old_cadence_step = spawn.RECONCILE_LEDGER_TTL_SEC  # 15 min -- worst case
        tick = self.attempt_ts
        end = self.attempt_ts + spawn.SPAWN_ATTEMPTS_RETENTION_SEC
        ticks = 0
        while tick <= end:
            roster.spawn_attempt_sweep(d_all={}, now=tick)
            tick += old_cadence_step
            ticks += 1

        count = self._reported_count_for_attempt()
        # Derived bound, stated in the record: retention // dedicated TTL + 1
        # (the +1 counts the always-due first report at tick 0).
        expected_bound = (spawn.SPAWN_ATTEMPTS_RETENTION_SEC
                           // roster.SPAWN_ATTEMPT_HALT_REPORT_TTL_SEC) + 1
        self.assertEqual(count, expected_bound)
        # The defect this issue fixes: naive per-tick replay at the old 15-min
        # cadence over the same window would have produced `ticks` reports
        # (one per tick, all "due" under the shared TTL) -- three orders of
        # magnitude more than the bounded count above.
        self.assertGreater(ticks, count * 10)

    def test_before_vs_after_derivation_no_longer_shows_the_9673_distribution(self):
        """Acceptance bullet 3, reproduced against a constructed ledger since
        this sandboxed checkout's own runs/ledger.jsonl never saw the
        production 105/73 incident (that history lives on the reporting
        orchestrator host, not in this git worktree) -- see the record's
        "population" note. Runs the identical constructed scenario twice,
        toggling only the dedup TTL used for the `spawn-attempt-halt:` key,
        to reproduce the ratio this issue measured and confirm the fix
        removes it."""
        def derive_counts(events):
            # The re-derivation command from this issue's body, as a
            # jq-equivalent Python reduction over runs/ledger.jsonl entries:
            #   jq -r 'select(.event=="spawn_attempt_halt_reported") |
            #           .attempt_id' runs/ledger.jsonl | sort | uniq -c
            counts: dict[str, int] = {}
            for ev in events:
                if ev.get("event") != "spawn_attempt_halt_reported":
                    continue
                counts[ev["attempt_id"]] = counts.get(ev["attempt_id"], 0) + 1
            return counts

        tick_step = spawn.RECONCILE_LEDGER_TTL_SEC
        end = self.attempt_ts + spawn.SPAWN_ATTEMPTS_RETENTION_SEC

        # "Before": the call site's dedup TTL is the shared
        # RECONCILE_LEDGER_TTL_SEC, reproducing the pre-#2916 code path.
        with mock.patch.object(roster, "SPAWN_ATTEMPT_HALT_REPORT_TTL_SEC",
                                spawn.RECONCILE_LEDGER_TTL_SEC):
            tick = self.attempt_ts
            while tick <= end:
                roster.spawn_attempt_sweep(d_all={}, now=tick)
                tick += tick_step
        before_counts = derive_counts(self.reported)
        self.reported.clear()
        _write_unresolved_halt(self.attempts_path, self.attempt_id, self.issue,
                                self.skill, self.attempt_ts, self.reason)
        # Reset the reconcile ledger so "after" starts from the same
        # never-reported state "before" did.
        self.reconcile_ledger_path.unlink(missing_ok=True)

        # "After": this issue's fix, dedicated TTL.
        tick = self.attempt_ts
        while tick <= end:
            roster.spawn_attempt_sweep(d_all={}, now=tick)
            tick += tick_step
        after_counts = derive_counts(self.reported)

        before = before_counts[self.attempt_id]
        after = after_counts[self.attempt_id]
        self.assertGreater(before, 600)  # matches the issue's ~96/day * 7d order
        self.assertLessEqual(after, 8)   # the derived bound from the other test
        self.assertLess(after, before / 50)


class EmptyStateTest(unittest.TestCase):
    """Acceptance bullet 1's empty-state clause: a STATE_ROOT whose
    spawn-attempts.jsonl is absent or empty emits nothing and does not
    create the file."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.attempts_path = Path(self._td.name) / "spawn-attempts.jsonl"
        patches = [
            mock.patch.object(spawn, "SPAWN_ATTEMPTS_PATH", self.attempts_path),
            mock.patch.object(spawn, "ledger_write", lambda ev: None),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def test_absent_file_emits_nothing_and_is_not_created(self):
        with mock.patch("builtins.print") as mocked_print:
            count = roster.spawn_attempt_sweep(d_all={})
        self.assertEqual(count, 0)
        self.assertEqual(mocked_print.call_args_list, [])
        self.assertFalse(self.attempts_path.exists())

    def test_empty_file_emits_nothing_and_stays_untouched(self):
        self.attempts_path.write_text("", encoding="utf-8")
        with mock.patch("builtins.print") as mocked_print:
            count = roster.spawn_attempt_sweep(d_all={})
        self.assertEqual(count, 0)
        self.assertEqual(mocked_print.call_args_list, [])
        self.assertEqual(self.attempts_path.read_text(encoding="utf-8"), "")


class FirstReportUnchangedTest(unittest.TestCase):
    """Acceptance bullet 2: the first announcement of a halt is unchanged --
    same text, same timing. This diffs the emitted line against a literal
    reconstruction of the pre-#2916 message-construction code (which this
    issue's diff never touches -- only the dedup TTL passed to
    `ledger_check_and_stamp` changed)."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.attempts_path = Path(self._td.name) / "spawn-attempts.jsonl"
        self.reconcile_ledger_path = Path(self._td.name) / "reconcile_ledger.json"
        patches = [
            mock.patch.object(spawn, "SPAWN_ATTEMPTS_PATH", self.attempts_path),
            mock.patch.object(spawn, "RECONCILE_LEDGER", self.reconcile_ledger_path),
            mock.patch.object(spawn, "ledger_write", lambda ev: None),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def test_single_tick_line_is_byte_identical_to_pre_change_format(self):
        attempt_id = "2326:unknown-skill-halt-ac4b8ed6"
        reason = "skill 'unknown-skill-halt' not found in skill registry"
        ts = 1_800_000_000.0
        _write_unresolved_halt(self.attempts_path, attempt_id, 2326,
                                "unknown-skill-halt-ac4b8ed6", ts, reason)

        with mock.patch("builtins.print") as mocked_print:
            count = roster.spawn_attempt_sweep(d_all={}, now=ts)

        self.assertEqual(count, 1)
        subject = roster.lease_key(2326, "unknown-skill-halt-ac4b8ed6")
        expected = (f"[spawn-attempt] {subject}: spawn halted pre-workspace "
                    f"(attempted at {roster._iso(ts)}): {reason}")
        printed = [str(c.args[0]) for c in mocked_print.call_args_list]
        self.assertEqual(printed, [expected])


if __name__ == "__main__":
    unittest.main()
