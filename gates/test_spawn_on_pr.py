#!/usr/bin/env python3
"""issue #2238 — `gates/spawn_on_pr.py`'s park/re-arm guard and respawn
ceiling.

Background: `spawn-on-pr` respawned issue-2208's observers 9x each
because `should_park()` treated an unchanged `pr_number` as the re-arm
signal — but a PR number changing because THIS mechanism's own respawn
opened a fresh PR is not evidence of human progress, so the guard never
actually armed. The fix removes `pr_number` from the park/re-arm decision
entirely (the only re-arm signal is now `is_approval_blocked()`, a real
external signal — an approver-allowlist comment) and adds an independent
respawn ceiling as a second line of defense.

These tests exercise the real entrypoint `spawn_missing_for_pr()` (the
same function `watchdog.py`'s board-sweep calls every tick) with the
gh/git/spawn boundaries monkeypatched out — no real `gh`, `git fetch`, or
Claude session is ever touched — so the park/ceiling logic under test is
the actual production code path, not a reimplementation of it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gates"))
import spawn_on_pr  # noqa: E402


# ---------------------------------------------------------------------
# should_park(): pure function, no monkeypatching needed.
# ---------------------------------------------------------------------

def test_should_park_first_time_candidate_never_parks():
    # issue #2238 acceptance: a (subject, role) pair seen for the very
    # first time (no prior park record) must never park, regardless of
    # `blocked`.
    assert spawn_on_pr.should_park(None, True) is False
    assert spawn_on_pr.should_park(None, False) is False


def test_should_park_still_blocked_parks():
    prior = {"blocked": True, "pr_number": 111}
    assert spawn_on_pr.should_park(prior, True) is True


def test_should_park_cleared_by_real_signal_does_not_park():
    # `blocked=False` here stands in for "is_approval_blocked() found an
    # approval comment" — a real external signal, not a PR-number diff.
    prior = {"blocked": True, "pr_number": 111}
    assert spawn_on_pr.should_park(prior, False) is False


def test_should_park_prior_not_previously_blocked_does_not_park():
    prior = {"blocked": False, "pr_number": 111}
    assert spawn_on_pr.should_park(prior, True) is False


def test_should_park_signature_has_no_pr_number_parameter():
    # issue #2238: pr_number must not be part of the decision surface at
    # all -- a regression that reintroduces it as a required positional
    # arg would silently resurrect the self-created-PR re-arm bug.
    import inspect
    params = list(inspect.signature(spawn_on_pr.should_park).parameters)
    assert params == ["prior", "blocked"]


# ---------------------------------------------------------------------
# spawn_missing_for_pr(): integration through the real tick entrypoint.
# ---------------------------------------------------------------------

SUBJECT = "issue-99001"
ROLE = "generic-role"
KEY = f"{SUBJECT}/{ROLE}"


class _Recorder:
    def __init__(self):
        self.spawn_calls = []
        self.ledger_events = []

    def spawn_one(self, *args, **kwargs):
        self.spawn_calls.append((args, kwargs))

    def ledger_write(self, entry):
        self.ledger_events.append(entry)


def _wire(monkeypatch, tmp_path, *, missing, pr_number, blocked,
          approval_calls=None):
    """Monkeypatch every gh/git/spawn boundary spawn_missing_for_pr()
    touches, while leaving the park/ceiling logic itself real. Returns a
    `_Recorder` capturing what would have been spawned/ledgered, and the
    tmp park-state path so tests can pre-seed or inspect it directly."""
    park_path = tmp_path / "spawn_on_pr_parked.json"
    monkeypatch.setattr(spawn_on_pr, "_park_state_path", lambda root: park_path)
    monkeypatch.setattr(spawn_on_pr, "missing_verification",
                         lambda root, issue_states=None, pr_index=None: dict(missing))
    monkeypatch.setattr(spawn_on_pr, "subject_deliverable_branch",
                         lambda subject, pr_index: f"{subject}/impl")
    monkeypatch.setattr(spawn_on_pr, "_pr_number_for_branch",
                         lambda root, branch, pr_index: pr_number)
    monkeypatch.setattr(spawn_on_pr, "resolve_live_base", lambda root: "deadbeef")

    def _is_approval_blocked(root, issue, role):
        if approval_calls is not None:
            approval_calls.append((issue, role))
        return blocked

    monkeypatch.setattr(spawn_on_pr, "is_approval_blocked", _is_approval_blocked)

    recorder = _Recorder()
    monkeypatch.setattr(spawn_on_pr.spawn, "roster_register", lambda *a, **k: None)
    monkeypatch.setattr(spawn_on_pr.spawn, "_spawn_one", recorder.spawn_one)
    monkeypatch.setattr(spawn_on_pr.spawn, "ledger_write", recorder.ledger_write)
    return recorder, park_path


def _seed_park_state(park_path: Path, state: dict) -> None:
    park_path.parent.mkdir(parents=True, exist_ok=True)
    park_path.write_text(json.dumps(state))


def _run(tmp_path, **kwargs):
    return spawn_on_pr.spawn_missing_for_pr(
        tmp_path, str(tmp_path), dry_run=False, issue_states=None,
        backoff_state={}, pr_index={}, **kwargs)


def test_empty_state_spawns_once_and_never_parks_on_first_tick(monkeypatch, tmp_path):
    # issue #2238 acceptance: a (subject, role) pair seen for the first
    # time ever (no park file, no prior entry) spawns exactly once and
    # is not treated as a retry.
    approval_calls = []
    recorder, park_path = _wire(
        monkeypatch, tmp_path, missing={SUBJECT: [ROLE]}, pr_number=111,
        blocked=True, approval_calls=approval_calls)

    pairs = _run(tmp_path)

    assert pairs == [(SUBJECT, ROLE)]
    assert len(recorder.spawn_calls) == 1
    # is_approval_blocked() must never be consulted for a brand-new
    # candidate -- only pairs with a prior "blocked" record touch gh here.
    assert approval_calls == []

    state = json.loads(park_path.read_text())
    entry = state[KEY]
    assert entry["parked"] is False
    assert entry["attempts"] == 1


def test_self_created_pr_number_change_no_longer_defeats_parking(monkeypatch, tmp_path):
    # issue #2238 core regression: the respawned observer's own session
    # opens a fresh PR each tick, so `pr_number` differs from the prior
    # tick's value even though nothing external changed. Before the fix,
    # that bare diff bypassed the approval recheck entirely and
    # respawned again; now it must still park because is_approval_blocked
    # still reports blocked=True (no real external signal was observed).
    approval_calls = []
    recorder, park_path = _wire(
        monkeypatch, tmp_path, missing={SUBJECT: [ROLE]},
        pr_number=600,  # different from the prior tick's 500 -- self-created PR
        blocked=True, approval_calls=approval_calls)
    _seed_park_state(park_path, {
        KEY: {"blocked": True, "pr_number": 500, "parked": False, "attempts": 1},
    })

    pairs = _run(tmp_path)

    assert pairs == []
    assert recorder.spawn_calls == []
    # The recheck DID happen (a prior blocked record exists) -- it just
    # correctly parked instead of being bypassed by the pr_number diff.
    assert approval_calls == [(99001, ROLE)]

    state = json.loads(park_path.read_text())
    entry = state[KEY]
    assert entry["parked"] is True
    assert entry["pr_number"] == 600  # recorded for visibility, not for gating


def test_real_external_signal_clears_park_and_allows_respawn(monkeypatch, tmp_path):
    # The positive counterpart: an approval comment (is_approval_blocked
    # returning False) is a real external signal and DOES re-arm, even
    # though the PR number also changed -- proving the fix distinguishes
    # a genuine external signal from a bare PR-number diff, rather than
    # just refusing to ever re-arm.
    recorder, park_path = _wire(
        monkeypatch, tmp_path, missing={SUBJECT: [ROLE]}, pr_number=600,
        blocked=False)
    _seed_park_state(park_path, {
        KEY: {"blocked": True, "pr_number": 500, "parked": False, "attempts": 1},
    })

    pairs = _run(tmp_path)

    assert pairs == [(SUBJECT, ROLE)]
    assert len(recorder.spawn_calls) == 1
    state = json.loads(park_path.read_text())
    entry = state[KEY]
    assert entry["parked"] is False
    assert entry["attempts"] == 2  # carried forward and incremented, not reset


def test_respawn_ceiling_hits_and_reports_loudly(monkeypatch, tmp_path, capsys):
    # issue #2238 item 2: independent backstop. Even though
    # is_approval_blocked() reports a real external signal this tick
    # (blocked=False, i.e. item 1's park rule would allow a respawn), the
    # ceiling must still stop it once max_respawn_attempts is reached --
    # and must say so loudly (print + ledger), not silently no-op.
    recorder, park_path = _wire(
        monkeypatch, tmp_path, missing={SUBJECT: [ROLE]}, pr_number=700,
        blocked=False)
    _seed_park_state(park_path, {
        KEY: {"blocked": True, "pr_number": 600, "parked": False, "attempts": 2},
    })

    pairs = _run(tmp_path, max_respawn_attempts=2)

    assert pairs == []
    assert recorder.spawn_calls == []

    assert len(recorder.ledger_events) == 1
    event = recorder.ledger_events[0]
    assert event["event"] == "spawn_on_pr_respawn_ceiling_hit"
    assert event["subject"] == SUBJECT
    assert event["role"] == ROLE
    assert event["attempts"] == 2

    out = capsys.readouterr().out
    assert "CEILING HIT" in out

    state = json.loads(park_path.read_text())
    entry = state[KEY]
    assert entry["ceiling_hit"] is True
    assert entry["parked"] is True


def test_ceiling_hit_entry_stays_parked_on_a_later_tick(monkeypatch, tmp_path):
    # Once a pair has been marked ceiling_hit, a later tick must not spawn
    # it again just because it re-enters the ordinary blocked-recheck
    # path -- `attempts` (and `ceiling_hit`) survive the
    # `{**prior, ...}` merges in every park-state write along that path,
    # so should_park() alone (still blocked, no new external signal)
    # keeps it parked without needing to re-derive the ceiling verdict
    # every tick.
    recorder, park_path = _wire(
        monkeypatch, tmp_path, missing={SUBJECT: [ROLE]}, pr_number=700,
        blocked=True)
    _seed_park_state(park_path, {
        KEY: {"blocked": True, "pr_number": 700, "parked": True,
              "ceiling_hit": True, "attempts": 4},
    })

    pairs = _run(tmp_path)

    assert pairs == []
    assert recorder.spawn_calls == []
    state = json.loads(park_path.read_text())
    assert state[KEY]["ceiling_hit"] is True
    assert state[KEY]["attempts"] == 4
