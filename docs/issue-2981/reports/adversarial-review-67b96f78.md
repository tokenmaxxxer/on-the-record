---
issue: 2981
role: adversarial-review-67b96f78
author: adversarial-review-67b96f78
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #3002, the deliverable for issue #2981
loop_state: done
upstream:
  - path: https://github.com/tokenmaxxxer/on-the-record/pull/3002
    sha: b2ec4e1dd93a18b7062768bf9ceca218decf1d21
---

# issue-2981 — adversarial-review-67b96f78 record

## What was done

Independently verified PR #3002 ("issue-2981: check for an existing deliverable PR before respawning a crashed session") against issue #2981's acceptance criteria and must-not list.

canonical: `gh pr view 3002` output (baseRefName: main, headRefName: issue-2981/merge-gates+test-derivation-2f452df8, head oid b2ec4e1dd93a18b7062768bf9ceca218decf1d21)

Fetched the PR head into an isolated worktree (`git fetch origin pull/3002/head:pr-3002-review && git worktree add /tmp/pr-3002-review-4027469 pr-3002-review`, no edits made in it) and re-ran the issue's three acceptance checks there, independent of the PR's own claimed numbers:

- checked: `python3 -m pytest tests/ -k respawn_skips_existing_deliverable -q` — result: 4 passed in 0.93s
- checked: `python3 -m pytest tests/ -k respawn_proceeds_without_deliverable -q` — result: 6 passed in 0.95s
- checked: `python3 -m pytest tests/ -k respawn_skip_is_reported -q` — result: 2 passed in 0.88s
- checked: `python3 -m pytest test/test_reconcile_crash_verdict_race.py -q` — result: 9 passed in 0.88s (existing respawn regression suite, unmodified by this PR, still green)

Acceptance requirement met — checked: the three commands above together — result: 4 passed, 6 passed, 2 passed respectively, matching the PR's own claimed counts for the three checks issue #2981 names.

Audited the diff (`git diff main...HEAD -- lifecycle.py spawn.py gates/spawn_on_pr.py`) against the must-not list:

- must not disable automatic respawn — Present. `subject_has_deliverable()` fail-opens toward respawn on every negative/uncertain case: no PR found, `gh` lookup error (`ok=False`), and a record-only-only PR all return `None`, which falls through to the pre-existing respawn call unchanged (`lifecycle.py:523-556`, `gates/spawn_on_pr.py` `subject_has_deliverable()`). `b2ec4e1d:tests/test_respawn_deliverable_gate.py:186-198` (`test_respawn_proceeds_without_deliverable_when_gate_finds_none` and `test_respawn_proceeds_without_deliverable_still_respawns_genuine_crash`) exercises this against the real `spawn._auto_respawn_check()` entry point (a dead-pid roster entry with no `session-end`, the same fixture shape as `test/test_reconcile_crash_verdict_race.py`), asserting `_respawn_or_cap` is still called once. A subject whose deliverable is genuinely absent still respawns.
- must not treat a record-only PR as the suppressing deliverable — Present. `subject_has_deliverable()` is layered on the pre-existing (issue #2628) `_VERIFICATION_SLOT_RE` filter in `subject_deliverable_branch()` and the pre-existing `subject_deliverable_record()` resolver, neither modified by this PR. Verified independently, not just by reading the PR's claim: `b2ec4e1d:tests/test_respawn_deliverable_gate.py:96-110` (`test_respawn_proceeds_without_deliverable_when_only_record_only_pr_open` and `..._when_only_record_only_pr_merged`) constructs a PR/record named `independent-verification-1` (open, and separately landed with `verifies_subject: true`) and asserts `subject_has_deliverable()` returns `None` for both — confirmed by the passing `respawn_proceeds_without_deliverable` run above, which subsumes these cases.
- must not close/alter/force-push any existing PR — Present. The diff adds only read paths (`spawn.board()`, `closure_sweep._pr_index_all()`, `spawn._pr_open_or_merged_for_branch()`); no write/mutation call against an existing PR appears anywhere in the diff.
- must not be the fix for the unreliable verdict itself (issue #2969's scope) — Present. The diff does not touch `session_end_verdict()`, `reconcile()`, or watchdog HEALTHY-flip logic; the new gate sits after `verdict != "crashed"` already returned, so it fires unconditionally on every `crashed` verdict regardless of whether that verdict is correct — holds even when the verdict is right, per the issue's explicit requirement.

## Why

Rationale for the verification approach: the task explicitly warned not to trust the PR's claimed results, so every acceptance check was re-run from a freshly fetched worktree rather than cited from the PR body, and the must-not list was checked against the actual diff rather than the PR description's narrative.

## What did not work

None.

## Upstream basis

- PR #3002 (`issue-2981/merge-gates+test-derivation-2f452df8`), head `b2ec4e1dd93a18b7062768bf9ceca218decf1d21` — the deliverable under review.
- Issue #2981 body (`gh issue view 2981`) — acceptance checks and must-not list, quoted verbatim above.

## Open findings

**Finding: the deliverable-existence gate covers only one of the two call sites into `_respawn_or_cap()`, leaving the duplicate-PR failure mode this issue describes reachable through the other.**

canonical: direct read of `lifecycle.py` and `spawn.py` at PR #3002 head (`b2ec4e1dd93a18b7062768bf9ceca218decf1d21`, fetched into `/tmp/pr-3002-review-4027469`)

`_respawn_or_cap()` (`b2ec4e1d:lifecycle.py:359`) is reached from two independent call sites, not one:

1. `_auto_respawn_check()` (`b2ec4e1d:lifecycle.py:501`, called via `spawn._auto_respawn_check`) — the watchdog-polled path that computes a `crashed` verdict from a dead roster entry. This PR's gate is inserted here, immediately after `verdict != "crashed"` returns (`b2ec4e1d:lifecycle.py:523-556`), and the acceptance tests above confirm it works correctly for this path.
2. `_self_trigger_respawn()` (`b2ec4e1d:lifecycle.py:587-616`, called from `b2ec4e1d:spawn.py:5097` right after a session's own `_spawn_one()` ends with an abandoned-work outcome — `uncommitted-work`, `failed-no-commit`, or a causeless `silent-failure`) — calls `_sp._respawn_or_cap(...)` directly at `b2ec4e1d:lifecycle.py:615` with **no call to `_subject_has_deliverable()` anywhere in this function**.

```python
def _self_trigger_respawn(outcome: str, roster_key: str, work: str, issue: int,
                          skill: str, log: str, session_start_ts,
                          single_phase: bool) -> None:
    ...
    if outcome not in _sp._ABANDONED_WORK_OUTCOMES:
        return
    state = _sp._respawn_state_load()
    trigger = ("self-triggered-causeless" if outcome == "silent-failure"
               else "self-triggered-abandoned")
    _sp._respawn_or_cap(roster_key, work, issue, skill, log, session_start_ts, state,
                    trigger, single_phase)
```
(`b2ec4e1d:lifecycle.py:587,607-616`, verified by direct read of the fetched PR head, unchanged by this PR's diff)

derived: `grep -n "_self_trigger_respawn\|_respawn_or_cap\|_auto_respawn_check" lifecycle.py` (run inside `/tmp/pr-3002-review-4027469`) — shows the gate block (added lines, `b2ec4e1d:lifecycle.py:523-556`) sits only inside `_auto_respawn_check()`; `_self_trigger_respawn()` at `b2ec4e1d:lifecycle.py:587-616` has no matching gate call between its `_ABANDONED_WORK_OUTCOMES` check and its own `_respawn_or_cap()` call.

Confirmed this is not merely untested-but-covered: derived: `grep -n "^def test_\|_self_trigger_respawn\|_auto_respawn_check" tests/test_respawn_deliverable_gate.py` (run inside `/tmp/pr-3002-review-4027469`) — shows every test in the PR's new test file (`SubjectHasDeliverableTest`, `AutoRespawnConsultsDeliverableGateTest`) exercises `subject_has_deliverable()` directly or `spawn._auto_respawn_check()` — none construct or call `_self_trigger_respawn()`.

This second sink is live, not dead code — `b2ec4e1d:spawn.py:5097` calls it unconditionally on every bounded self-spawn whose outcome lands in `_ABANDONED_WORK_OUTCOMES`, immediately after the session's own `session-end` event is appended (`b2ec4e1d:spawn.py:5080-5098`). The scenario the issue's report describes (a duplicate PR opened over an issue a prior or sibling round already covers) is structurally reproducible through this path too: a session that ends with `uncommitted-work` or a causeless `silent-failure` self-triggers a respawn without ever checking whether another round (a sibling session, or an earlier round this one merely raced with) already produced a deliverable PR for the same subject.

This is a real gap in what the PR delivers, but it is arguably outside the issue's own literal framing: issue #2981's title, report, and acceptance checks are all scoped to a "crashed **verdict**" specifically (the watchdog path), and the PR's own description frames itself the same way throughout ("The crashed-verdict respawn path (`lifecycle.py::_auto_respawn_check`...)"). `_self_trigger_respawn()`'s trigger conditions (`uncommitted-work`/`failed-no-commit`/causeless `silent-failure`) are a different verdict shape than `crashed`, self-detected by the ending session rather than watchdog-polled. The 3 acceptance checks named in the issue verify clean above; the gap is a scope boundary the issue itself did not draw around this second call site, not a failure to satisfy what was asked. Recorded here as an open finding rather than a blocking defect, per the live context flagging this exact question (issue #2969's PR left the same second sink uncovered for the verdict-reliability fix) — a follow-up issue extending `subject_has_deliverable()`'s consult to `_self_trigger_respawn()` would close this gap without reopening #2981's own scope.

## Next steps

None.

## Skill verdicts

- skill-verdict: adversarial-review — applied: invoked; this session is itself the structurally-independent evaluator (fresh context, received only PR #3002 and issue #2981's text, no access to the builder session's reasoning) — followed Steps 1-3 by re-executing evidence rather than trusting the builder's claims, and produced located, cited findings per Step 3's gate.
- skill-verdict: work-in-english — applied: invoked; all repo-bound artifacts (this record, commit message, PR body) written in English; final user-facing summary written in Korean per the skill's routing rule.
- other mounted skills: not triggered (defect-verification-independence-from-upstream-verdicts, implementation-audit, conformance-review-finding-record, test-depth-audit, verify-finding-record — this record's shape and verification-independence practice already matched their intent without needing to load them; none of their specific triggers, e.g. a marked-Present requirement or an existing test suite to classify, applied here).
