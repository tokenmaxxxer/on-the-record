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
SKILL = "independent-verification-1"  # issue #2628: the slot spawned when attempts starts at 0
KEY = SUBJECT  # issue #2628: park state is keyed by subject alone, not "subject/role"


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
                         lambda root, subject, pr_index: f"{subject}/impl")
    monkeypatch.setattr(spawn_on_pr, "_pr_number_for_branch",
                         lambda root, branch, pr_index: pr_number)
    monkeypatch.setattr(spawn_on_pr, "resolve_live_base", lambda root: "deadbeef")

    def _is_approval_blocked(root, issue, skill):
        if approval_calls is not None:
            approval_calls.append((issue, skill))
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
        monkeypatch, tmp_path, missing={SUBJECT: 1}, pr_number=111,
        blocked=True, approval_calls=approval_calls)

    pairs = _run(tmp_path)

    assert pairs == [(SUBJECT, SKILL)]
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
        monkeypatch, tmp_path, missing={SUBJECT: 1},
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
    assert approval_calls == [(99001, spawn_on_pr.VERIFICATION_APPROVAL_TARGET)]

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
        monkeypatch, tmp_path, missing={SUBJECT: 1}, pr_number=600,
        blocked=False)
    _seed_park_state(park_path, {
        KEY: {"blocked": True, "pr_number": 500, "parked": False, "attempts": 1},
    })

    pairs = _run(tmp_path)

    # issue #2628: the slot number is drawn from the subject's own
    # cumulative attempts (1 already recorded), never renumbered back to 1
    # -- that stability is exactly what the warrant hunt on this issue's
    # delivery required after finding the positional-renumbering defect.
    assert pairs == [(SUBJECT, "independent-verification-2")]
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
        monkeypatch, tmp_path, missing={SUBJECT: 1}, pr_number=700,
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
        monkeypatch, tmp_path, missing={SUBJECT: 1}, pr_number=700,
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


def test_sibling_slot_resolving_does_not_reset_ceiling_progress(monkeypatch, tmp_path):
    # issue #2628 warrant hunt (before-landing, stance 0, 2026-08-27):
    # reproduced regression. Slot numbers used to be recomputed fresh each
    # tick from the CURRENT deficit (`range(1, deficit+1)`) -- when a
    # subject needed 2 verifications and the lower-numbered one resolved
    # first, the still-stuck higher-numbered slot's own park/ceiling
    # history got silently discarded and replaced by a fresh, low-attempt
    # identity under the now-renumbered key. Tracking park/ceiling state
    # per subject (not per slot) closes that path: the subject's
    # cumulative `attempts` counter must climb monotonically to the real
    # ceiling regardless of how many of its individual slots resolve
    # along the way, and slot numbers must never repeat.
    #
    # Tick 1: subject needs 2 verifications, nothing spawned yet -- both
    # slots go out in one batch.
    recorder, park_path = _wire(
        monkeypatch, tmp_path, missing={SUBJECT: 2}, pr_number=100, blocked=True)
    pairs1 = _run(tmp_path)
    assert pairs1 == [(SUBJECT, "independent-verification-1"),
                       (SUBJECT, "independent-verification-2")]
    assert json.loads(park_path.read_text())[KEY]["attempts"] == 2

    # Tick 2: one of the two landed a verifying record -- the subject's
    # deficit drops to 1 -- but the auto-spawn tick must still treat this
    # as "still blocked, retry" (a real approval re-arm signal, blocked=
    # False) so it spawns exactly one more session, numbered from the
    # subject's own attempts (2), never renumbered back to 1.
    recorder, park_path = _wire(
        monkeypatch, tmp_path, missing={SUBJECT: 1}, pr_number=100, blocked=False)
    pairs2 = _run(tmp_path, max_respawn_attempts=3)
    assert pairs2 == [(SUBJECT, "independent-verification-3")]
    state2 = json.loads(park_path.read_text())
    assert state2[KEY]["attempts"] == 3

    # Tick 3: still 1 short, still blocked -- with max_respawn_attempts=3
    # the subject's cumulative attempts (3) has now reached the ceiling.
    # A defect that reset the counter when slot 1 resolved on tick 2 would
    # never reach this ceiling at all.
    recorder, park_path = _wire(
        monkeypatch, tmp_path, missing={SUBJECT: 1}, pr_number=100, blocked=False)
    pairs3 = _run(tmp_path, max_respawn_attempts=3)
    assert pairs3 == []
    assert recorder.spawn_calls == []
    state3 = json.loads(park_path.read_text())
    assert state3[KEY]["ceiling_hit"] is True
    assert state3[KEY]["attempts"] == 3
    assert len(recorder.ledger_events) == 1
    assert recorder.ledger_events[0]["event"] == "spawn_on_pr_respawn_ceiling_hit"
    assert recorder.ledger_events[0]["attempts"] == 3


# ---------------------------------------------------------------------
# clear_ceiling(): issue #2607 — the CEILING HIT message's named recovery
# command. Must clear only ceiling_hit/attempts, never blocked/parked, so
# the next tick still gates on a real approval signal, not on this
# command's mere invocation.
# ---------------------------------------------------------------------

def test_clear_ceiling_empty_state_reports_nothing_and_does_not_error(tmp_path, monkeypatch):
    park_path = tmp_path / "spawn_on_pr_parked.json"
    monkeypatch.setattr(spawn_on_pr, "_park_state_path", lambda root: park_path)

    cleared = spawn_on_pr.clear_ceiling(tmp_path)

    assert cleared == []
    assert not park_path.exists()


def test_clear_ceiling_no_args_clears_all_currently_reported_subjects(tmp_path, monkeypatch):
    park_path = tmp_path / "spawn_on_pr_parked.json"
    monkeypatch.setattr(spawn_on_pr, "_park_state_path", lambda root: park_path)
    OTHER_KEY = "issue-99002"
    _seed_park_state(park_path, {
        KEY: {"blocked": True, "pr_number": 700, "parked": True,
              "ceiling_hit": True, "attempts": 4},
        OTHER_KEY: {"blocked": True, "pr_number": 900, "parked": True,
                    "ceiling_hit": True, "attempts": 4},
        # A plain waiting-for-approval park entry, never ceiling_hit --
        # out of scope for this command and must survive untouched.
        "issue-99003": {
            "blocked": True, "pr_number": 800, "parked": True, "attempts": 1,
        },
    })

    cleared = spawn_on_pr.clear_ceiling(tmp_path)

    assert sorted(cleared) == sorted([KEY, OTHER_KEY])
    state = json.loads(park_path.read_text())
    assert state[KEY]["ceiling_hit"] is False
    assert state[KEY]["attempts"] == 0
    assert state[KEY]["blocked"] is True  # untouched -- still gated on real signal
    assert state[KEY]["parked"] is True
    assert state[OTHER_KEY]["ceiling_hit"] is False
    assert state[OTHER_KEY]["attempts"] == 0
    untouched = state["issue-99003"]
    assert untouched == {"blocked": True, "pr_number": 800, "parked": True, "attempts": 1}


def test_clear_ceiling_named_subject_leaves_other_ceiling_hits_alone(tmp_path, monkeypatch):
    park_path = tmp_path / "spawn_on_pr_parked.json"
    monkeypatch.setattr(spawn_on_pr, "_park_state_path", lambda root: park_path)
    OTHER_KEY = "issue-99002"
    _seed_park_state(park_path, {
        KEY: {"blocked": True, "pr_number": 700, "parked": True,
              "ceiling_hit": True, "attempts": 4},
        OTHER_KEY: {"blocked": True, "pr_number": 900, "parked": True,
                    "ceiling_hit": True, "attempts": 4},
    })

    cleared = spawn_on_pr.clear_ceiling(tmp_path, subject=SUBJECT)

    assert cleared == [KEY]
    state = json.loads(park_path.read_text())
    assert state[KEY]["attempts"] == 0
    assert state[OTHER_KEY]["ceiling_hit"] is True  # not named -- untouched
    assert state[OTHER_KEY]["attempts"] == 4


def test_clear_ceiling_then_next_tick_spawns_once_approval_is_real(monkeypatch, tmp_path):
    # The full recovery path the issue asks for: a pair hit the ceiling,
    # the operator runs clear-ceiling, and — because a real external
    # approval signal is already present (blocked=False here stands in
    # for that) — the very next tick spawns it again. clear_ceiling()
    # never had to touch `blocked`/`parked` for this to work: the ceiling
    # was the only thing still in the way.
    recorder, park_path = _wire(
        monkeypatch, tmp_path, missing={SUBJECT: 1}, pr_number=700,
        blocked=False)
    _seed_park_state(park_path, {
        KEY: {"blocked": True, "pr_number": 700, "parked": True,
              "ceiling_hit": True, "attempts": 4},
    })

    cleared = spawn_on_pr.clear_ceiling(tmp_path)
    assert cleared == [KEY]

    pairs = _run(tmp_path)

    assert pairs == [(SUBJECT, SKILL)]
    assert len(recorder.spawn_calls) == 1
    state = json.loads(park_path.read_text())
    assert state[KEY]["parked"] is False
    assert state[KEY]["attempts"] == 1


def test_clear_ceiling_does_not_unblock_without_a_real_approval_signal(monkeypatch, tmp_path):
    # The must-not case: clear-ceiling alone is not a bypass. If no real
    # external signal exists yet (still blocked=True), the pair stays
    # parked on the next tick exactly like any other waiting-for-human
    # pair -- clearing the ceiling did not spoof an approval.
    recorder, park_path = _wire(
        monkeypatch, tmp_path, missing={SUBJECT: 1}, pr_number=700,
        blocked=True)
    _seed_park_state(park_path, {
        KEY: {"blocked": True, "pr_number": 700, "parked": True,
              "ceiling_hit": True, "attempts": 4},
    })

    spawn_on_pr.clear_ceiling(tmp_path)
    pairs = _run(tmp_path)

    assert pairs == []
    assert recorder.spawn_calls == []


# ---------------------------------------------------------------------
# missing_verification(): issue #2652 -- the is-open check must run
# before the pr_index-membership check, so a closed subject whose
# deliverable branch is unmappable (the ordinary state for a long-closed
# issue) never reaches the branch-missing print/one-shot-marker at all.
# ---------------------------------------------------------------------

def _deliverable_board(author="alice"):
    # A single non-verifying record -> subject_deliverable_record()
    # resolves it as the deliverable, and verifying_record_count() is 0
    # (no `verifies_subject: true` record), so verification_deficit() is
    # REQUIRED_INDEPENDENT_VERIFICATIONS (> 0) -- this subject is always a
    # deficit candidate for missing_verification() to evaluate.
    return {"implementation": {"author": author}}


def test_closed_issue_with_unmappable_branch_prints_nothing(monkeypatch, tmp_path, capsys):
    # issue #2652 acceptance 1: a closed issue whose deliverable branch is
    # not in pr_index must produce NO per-tick spawn-on-pr output -- the
    # is-open check must short-circuit before the branch-missing check
    # even gets a chance to fire (with the one-shot marker forced to
    # "first time seen" below, so the old ordering would deterministically
    # print here if it regressed).
    subject = "issue-99101"
    monkeypatch.setattr(spawn_on_pr.spawn, "board", lambda root: {subject: _deliverable_board()})
    monkeypatch.setattr(spawn_on_pr.spawn, "_watchdog_note_unmappable_subject_branch",
                         lambda root, s: True)

    out = spawn_on_pr.missing_verification(
        tmp_path, issue_states={99101: "CLOSED"}, pr_index={})

    assert subject not in out
    captured = capsys.readouterr()
    assert captured.out == ""


def test_open_subject_with_unmappable_branch_still_reports_missing_branch(
        monkeypatch, tmp_path, capsys):
    # issue #2652 acceptance 2: an OPEN subject whose branch genuinely is
    # missing from pr_index must still print the branch-missing line --
    # the fix must not silence this case generally, only reorder past it
    # for closed subjects.
    subject = "issue-99102"
    monkeypatch.setattr(spawn_on_pr.spawn, "board", lambda root: {subject: _deliverable_board()})
    monkeypatch.setattr(spawn_on_pr.spawn, "_watchdog_note_unmappable_subject_branch",
                         lambda root, s: True)

    out = spawn_on_pr.missing_verification(
        tmp_path, issue_states={99102: "OPEN"}, pr_index={})

    assert subject not in out
    captured = capsys.readouterr()
    assert (f"[spawn-on-pr] {subject}: deliverable 브랜치를 pr_index 에서 "
            "찾지 못했다") in captured.out


def test_closed_and_open_subjects_mixed_only_open_unmappable_branch_reported(
        monkeypatch, tmp_path, capsys):
    # issue #2652: a mixed board (many closed subjects with unmappable
    # branches, one open subject with an unmappable branch, one open
    # subject whose branch IS in pr_index) -- only the open+unmappable
    # subject prints, the open+mapped subject spawns normally (deficit
    # surfaces in the result), and no spawning-eligible set changes.
    closed_subjects = [f"issue-{93000 + i}" for i in range(30)]
    board = {s: _deliverable_board() for s in closed_subjects}
    board["issue-93100"] = _deliverable_board()  # open, branch unmappable
    board["issue-93200"] = _deliverable_board()  # open, branch mapped

    issue_states = {int(s.split("-", 1)[1]): "CLOSED" for s in closed_subjects}
    issue_states[93100] = "OPEN"
    issue_states[93200] = "OPEN"
    pr_index = {"issue-93200/implementation": {"number": 1, "state": "OPEN"}}

    monkeypatch.setattr(spawn_on_pr.spawn, "board", lambda root: board)
    monkeypatch.setattr(spawn_on_pr.spawn, "_watchdog_note_unmappable_subject_branch",
                         lambda root, s: True)
    monkeypatch.setattr(spawn_on_pr.check_runner, "pr_diff_paths",
                         lambda root, pr: ["gates/spawn_on_pr.py"])

    out = spawn_on_pr.missing_verification(
        tmp_path, issue_states=issue_states, pr_index=pr_index)

    assert out == {"issue-93200": spawn_on_pr.REQUIRED_INDEPENDENT_VERIFICATIONS}
    captured = capsys.readouterr()
    printed_subjects = [line.split(":", 1)[0].removeprefix("[spawn-on-pr] ")
                         for line in captured.out.splitlines() if "찾지 못했다" in line]
    assert printed_subjects == ["issue-93100"]


# ---------------------------------------------------------------------
# missing_verification(): issue #2777/#2792 -- a degraded issue-state
# lookup (issue_states stays None because closure_sweep.issue_state_
# index_all() did not return a usable index) must report its own
# distinct state, not silently produce the same empty output as a
# healthy quiet tick. #2652's reorder is not touched: `_issue_is_open()`
# still fail-closes the spawn decision (`out` stays unaffected either
# way) -- only the diagnostic print is new.
#
# issue #2792: the degraded case is now two DISTINCT states sharing the
# same `issue_states=None` fallout -- ISSUE_INDEX_FAILED (the gh call
# itself failed) and ISSUE_INDEX_TRUNCATED (the gh call succeeded but
# the index was too large to trust). Pre-#2792, `issue_state_index_all()`
# returned `(None, True)` for truncation -- indistinguishable, at this
# call site, from `(index, True)` healthy success once `not ok` was the
# only check -- so a truncated board never accumulated a failure streak
# and never printed anything: silent withholding while looking healthy.
# The two states below must now print two DIFFERENT lines under two
# DIFFERENT streak signals ("spawn-on-pr" / "spawn-on-pr:truncated"),
# never the same "gh 실패" line for both.
# ---------------------------------------------------------------------

def _degraded_lookup(monkeypatch, tmp_path, *, status):
    subject = "issue-99301"
    index = {} if status == spawn_on_pr.closure_sweep.ISSUE_INDEX_OK else None
    monkeypatch.setattr(spawn_on_pr.spawn, "board", lambda root: {subject: _deliverable_board()})
    monkeypatch.setattr(spawn_on_pr.spawn, "_watchdog_note_unmappable_subject_branch",
                         lambda root, s: True)
    monkeypatch.setattr(spawn_on_pr.closure_sweep, "issue_state_index_all",
                         lambda root: (index, status))
    monkeypatch.setattr(spawn_on_pr.state_paths, "STATE_ROOT", tmp_path / "state")
    return subject


def test_degraded_lookup_stays_quiet_below_the_failure_streak_threshold(monkeypatch, tmp_path, capsys):
    _degraded_lookup(monkeypatch, tmp_path, status=spawn_on_pr.closure_sweep.ISSUE_INDEX_FAILED)
    threshold = spawn_on_pr.spawn.WATCHDOG_TRANSIENT_GH_FAILURE_THRESHOLD
    for _ in range(threshold - 1):
        out = spawn_on_pr.missing_verification(tmp_path, pr_index={})
        assert out == {}
    captured = capsys.readouterr()
    assert captured.out == ""  # single/short blips stay quiet, same convention as watchdog.py


def test_degraded_lookup_reports_its_own_state_once_streak_hits_threshold(monkeypatch, tmp_path, capsys):
    _degraded_lookup(monkeypatch, tmp_path, status=spawn_on_pr.closure_sweep.ISSUE_INDEX_FAILED)
    threshold = spawn_on_pr.spawn.WATCHDOG_TRANSIENT_GH_FAILURE_THRESHOLD
    for _ in range(threshold):
        out = spawn_on_pr.missing_verification(tmp_path, pr_index={})

    assert out == {}  # no spawn-eligibility change -- _issue_is_open() still fail-closes
    captured = capsys.readouterr()
    assert "gh 실패" in captured.out
    # distinct from the old unlabeled branch-missing noise:
    assert "찾지 못했다" not in captured.out
    # distinct from the truncated-state line (issue #2792):
    assert "절단" not in captured.out


def test_healthy_lookup_after_this_functions_own_fetch_stays_quiet(monkeypatch, tmp_path, capsys):
    # Regression guard: a *successful* internal fetch must not start
    # printing either -- the diagnostic prints are gated on a non-OK
    # status alone.
    subject = _degraded_lookup(monkeypatch, tmp_path, status=spawn_on_pr.closure_sweep.ISSUE_INDEX_OK)

    out = spawn_on_pr.missing_verification(tmp_path, pr_index={})

    assert subject not in out  # empty issue_states index -> issue treated as not-OPEN
    captured = capsys.readouterr()
    assert captured.out == ""


# ---------------------------------------------------------------------
# missing_verification(): issue #2792 acceptance -- a truncated index is
# reported as its own state, distinct from both a healthy quiet tick
# (test above) and a gh-failure tick (tests above). It shares
# `issue_states=None` fallout with a real failure (`out == {}`, same
# spawn eligibility either way -- acceptance bullet 3) but must never be
# silently folded into, or mistaken for, the "gh 실패" failure streak.
# ---------------------------------------------------------------------

def test_truncated_lookup_stays_quiet_below_its_own_streak_threshold(monkeypatch, tmp_path, capsys):
    _degraded_lookup(monkeypatch, tmp_path, status=spawn_on_pr.closure_sweep.ISSUE_INDEX_TRUNCATED)
    threshold = spawn_on_pr.spawn.WATCHDOG_TRANSIENT_GH_FAILURE_THRESHOLD
    for _ in range(threshold - 1):
        out = spawn_on_pr.missing_verification(tmp_path, pr_index={})
        assert out == {}
    captured = capsys.readouterr()
    assert captured.out == ""


def test_truncated_lookup_reports_its_own_state_once_streak_hits_threshold(monkeypatch, tmp_path, capsys):
    _degraded_lookup(monkeypatch, tmp_path, status=spawn_on_pr.closure_sweep.ISSUE_INDEX_TRUNCATED)
    threshold = spawn_on_pr.spawn.WATCHDOG_TRANSIENT_GH_FAILURE_THRESHOLD
    for _ in range(threshold):
        out = spawn_on_pr.missing_verification(tmp_path, pr_index={})

    assert out == {}  # spawn eligibility unaffected -- same fail-closed result as a real failure
    captured = capsys.readouterr()
    assert "절단" in captured.out
    # never mislabeled as a real gh failure -- this is the exact defect
    # #2792 reports: truncation used to be indistinguishable from health
    # because both left `not ok` False.
    assert "gh 실패" not in captured.out


def test_truncated_and_failed_streaks_accumulate_independently(monkeypatch, tmp_path, capsys):
    # A run of truncated ticks must not feed the "spawn-on-pr" gh-failure
    # streak (that streak means something actionable-differently: the gh
    # call itself is broken, not "the board grew past the safety limit").
    _degraded_lookup(monkeypatch, tmp_path, status=spawn_on_pr.closure_sweep.ISSUE_INDEX_TRUNCATED)
    threshold = spawn_on_pr.spawn.WATCHDOG_TRANSIENT_GH_FAILURE_THRESHOLD

    def streaks():
        path = spawn_on_pr.spawn._watchdog_noise_state_path(tmp_path)
        state = spawn_on_pr.spawn._load_watchdog_noise_state(path)
        return state.get("gh_failure_streaks", {})

    for _ in range(threshold):
        spawn_on_pr.missing_verification(tmp_path, pr_index={})

    s = streaks()
    assert s.get("spawn-on-pr:truncated", 0) == threshold
    assert s.get("spawn-on-pr", 0) == 0


def test_gh_failure_streak_resets_on_recovery_via_production_caller_shape(monkeypatch, tmp_path, capsys):
    # issue #2777 verification finding: watchdog.py (the sole production
    # caller of spawn_missing_for_pr()) fetches issue_states ONCE per tick
    # and always forwards it explicitly -- a real dict on success, None on
    # failure -- it never omits the argument the way every other test in
    # this file does. That means the "issue_states is None" branch (the
    # only place the pre-fix streak reset lived) never runs on a healthy
    # production tick, so the streak could climb on a sustained outage and
    # then never come back down once the caller recovered. This test
    # drives missing_verification() through that exact calling shape --
    # explicit issue_states=None on failing ticks, explicit real dict on
    # the recovery tick -- rather than letting missing_verification() do
    # its own internal fetch every tick.
    subject = "issue-99302"
    monkeypatch.setattr(spawn_on_pr.spawn, "board", lambda root: {subject: _deliverable_board()})
    monkeypatch.setattr(spawn_on_pr.spawn, "_watchdog_note_unmappable_subject_branch",
                         lambda root, s: True)
    monkeypatch.setattr(spawn_on_pr.state_paths, "STATE_ROOT", tmp_path / "state")
    threshold = spawn_on_pr.spawn.WATCHDOG_TRANSIENT_GH_FAILURE_THRESHOLD

    def streak():
        path = spawn_on_pr.spawn._watchdog_noise_state_path(tmp_path)
        state = spawn_on_pr.spawn._load_watchdog_noise_state(path)
        return state.get("gh_failure_streaks", {}).get("spawn-on-pr", 0)

    monkeypatch.setattr(spawn_on_pr.closure_sweep, "issue_state_index_all",
                         lambda root: (None, spawn_on_pr.closure_sweep.ISSUE_INDEX_FAILED))
    lines = []
    for _ in range(threshold):
        # mirrors watchdog.py: the caller's own top-level fetch failed,
        # so it forwards issue_states=None explicitly (not omitted).
        spawn_on_pr.missing_verification(tmp_path, issue_states=None, pr_index={})
        lines.append(capsys.readouterr().out)

    assert lines[:-1] == [""] * (threshold - 1)
    assert "gh 실패" in lines[-1]
    assert streak() == threshold

    # recovery tick: the caller's own fetch now succeeds and forwards a
    # real (non-None) issue_states dict -- exactly what watchdog.py does,
    # and exactly the shape the pre-fix code never called the reset from.
    out = spawn_on_pr.missing_verification(tmp_path, issue_states={}, pr_index={})
    recovery_line = capsys.readouterr().out

    assert recovery_line == ""  # a reset never itself prints
    assert streak() == 0
    assert out == {}  # empty issue_states index -> issue treated as not-OPEN, unaffected

    # a single isolated blip right after recovery must NOT immediately
    # re-warn -- if it did, the streak would not have actually reset.
    monkeypatch.setattr(spawn_on_pr.closure_sweep, "issue_state_index_all",
                         lambda root: (None, spawn_on_pr.closure_sweep.ISSUE_INDEX_FAILED))
    spawn_on_pr.missing_verification(tmp_path, issue_states=None, pr_index={})
    assert capsys.readouterr().out == ""
    assert streak() == 1


def test_truncated_streak_resets_on_recovery_via_production_caller_shape(monkeypatch, tmp_path, capsys):
    # issue #2792: the "spawn-on-pr:truncated" streak (separate signal
    # name from "spawn-on-pr", see test_truncated_and_failed_streaks_
    # accumulate_independently above) must reset on recovery the same
    # way the pre-existing failure streak does -- same production caller
    # shape as test_gh_failure_streak_resets_on_recovery_via_production_
    # caller_shape above, mirrored for the truncated signal.
    subject = "issue-99303"
    monkeypatch.setattr(spawn_on_pr.spawn, "board", lambda root: {subject: _deliverable_board()})
    monkeypatch.setattr(spawn_on_pr.spawn, "_watchdog_note_unmappable_subject_branch",
                         lambda root, s: True)
    monkeypatch.setattr(spawn_on_pr.state_paths, "STATE_ROOT", tmp_path / "state")
    threshold = spawn_on_pr.spawn.WATCHDOG_TRANSIENT_GH_FAILURE_THRESHOLD

    def streak():
        path = spawn_on_pr.spawn._watchdog_noise_state_path(tmp_path)
        state = spawn_on_pr.spawn._load_watchdog_noise_state(path)
        return state.get("gh_failure_streaks", {}).get("spawn-on-pr:truncated", 0)

    monkeypatch.setattr(spawn_on_pr.closure_sweep, "issue_state_index_all",
                         lambda root: (None, spawn_on_pr.closure_sweep.ISSUE_INDEX_TRUNCATED))
    for _ in range(threshold):
        spawn_on_pr.missing_verification(tmp_path, issue_states=None, pr_index={})
        capsys.readouterr()
    assert streak() == threshold

    out = spawn_on_pr.missing_verification(tmp_path, issue_states={}, pr_index={})
    recovery_line = capsys.readouterr().out

    assert recovery_line == ""
    assert streak() == 0
    assert out == {}
