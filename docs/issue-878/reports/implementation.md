---
code_under_review:
  - on-the-record/hooks/directive.sh
  - spawn.py
  - harness/driver.py
  - harness/test_driver.py
  - tests/test_spawn.py
  - docs/handbooks/async-completion-drive.md
type: feature
breaking: false
verdict: pending
loop_state: landed
---

## What was done

canonical: docs/issue-878/proposals/2026-08-11-async-completion-drive.md (read in full this session)

Implemented the merged phase-1 proposal
(`docs/issue-878/proposals/2026-08-11-async-completion-drive.md`), split by
process lifecycle as designed:

1. **Interactive self-drive** (`on-the-record/hooks/directive.sh`): a new
   paragraph, gated by the same `CLAUDE_ROLE`-unset check as the existing
   four, tells the orchestrator that the moment a `watch --follow`
   notification (or a resumed-turn nudge) reports a delegated PR
   opened/mergeable/checks-passed, its next action is verify → `gh pr
   merge` → rebuild/re-check → emit the 4-part `final_report` — same turn,
   never deferred. No new poll/scheduler; only the post-notification
   instruction is new.

2. **Headless resume mechanism** (`spawn.py`):
   - `ORCHESTRATOR_SESSION_ID_ENV` ("`ORCHESTRATOR_SESSION_ID`") is read at
     roster-registration time in `_spawn_one` and stored on the roster
     entry's new `session_id` field — `None` when unset, never fabricated.
   - `_session_resume_claim` (a `ledger_check_and_stamp`-backed atomic
     claim, TTL `SESSION_RESUME_CLAIM_TTL_SEC`) keyed on `session_id`
     itself, not on the roster entry — addresses the after-proposal hunt
     finding that `session_id` is process-scoped, so two roster entries
     spawned by the same orchestrator session must resume it at most once.
   - `_resume_orchestrator_session` runs `claude -p "<nudge>" --resume
     "<session_id>"` in the background (non-blocking, same observe-only
     tick discipline `roster_watchdog` already holds).
   - `_maybe_resume_for_ready_pr` is the call site, wired into
     `roster_watchdog`'s existing dead-and-completed branch: when a role
     session has ended with a PR and the entry carries a `session_id`, it
     claims and resumes exactly once per session_id per readiness window.

3. **Harness measurement** (`harness/driver.py`):
   - `extract_session_id`, `poll_for_pr_ready` (bounded `gh pr list`
     polling), `resume_orchestrator_session` (`claude -p --resume
     --output-format json`), and `drive_multiturn_completion` which
     composes the three and returns exactly one of `final_report` /
     `unmeasured_reason` non-None on every path — a break anywhere in the
     chain (no session_id, poll timeout, `--resume` unavailable/failing)
     yields an explicit `unmeasured_reason`, never a fabricated report.
     `harness/signals.py` is unchanged — its checks already only PASS on a
     genuine 4-part `final_report`; the fix is entirely in what the driver
     feeds it.

4. **Handbook** (`docs/handbooks/async-completion-drive.md`): the
   interactive-vs-headless split, the `session_id` capture point, and the
   hard boundary that a `-p` process's own `end_turn` is unrecoverable
   in-process, stated plainly per the proposal's constraint.

Tests added: `harness/test_driver.py` (12 new tests covering
`extract_session_id`/`poll_for_pr_ready`/`resume_orchestrator_session`/
`drive_multiturn_completion`, including the never-fabricate-a-report path)
and `tests/test_spawn.py` (`SessionResumeClaim`,
`OrchestratorSessionIdCapture` — 7 new tests covering the shared-session_id
double-fire prevention, no-session_id no-op, and env-var capture contract).

derived: `python3 -m pytest tests/test_spawn.py -q`
```
446 passed in 35.13s
```
derived: `cd harness && python3 -m pytest test_driver.py test_signals.py -q`
```
27 passed in 0.14s
```
`bash -n on-the-record/hooks/directive.sh` — syntax OK.

## Why

canonical: GitHub issue #878 body (`gh issue view 878`, read this session)

Issue #878 step 2: the survey/proposal (phase 1, PR #880) found that every
upstream step of async delegation already works (issue creation, role
delegation, PR-open) but the orchestrator closes its turn awaiting the
delegated PR and never self-drives to merge + `final_report` — so #1/#4 of
the #776 harness signal table never reach a real PASS without a human. This
implements the approved design: reuse the landed poll/Monitor machinery
(#829/#835/#782) verbatim, add only the post-notification behavior
(interactive) and the resume-invoke primitive (headless), and make the
harness drive the real multi-turn shape instead of observing the gap.

## Upstream

docs/issue-878/proposals/2026-08-11-async-completion-drive.md (approved via
`APPROVE issue-878/implementation`, issue #878 comment)

## What did not work

None.

## Open findings

None — the after-proposal hunt finding (session_id is process-scoped, not
entry-scoped) is addressed directly in this implementation via
`_session_resume_claim`'s session_id-keyed claim.

## Doc placement

- [x] `docs/handbooks/async-completion-drive.md` — the `session_id`
  capture point, the interactive/headless split, and the unrecoverable
  `end_turn` boundary (per doctrine: this is exactly the "future proposals
  should not re-attempt case-1's mechanism for case 2" ladder item the
  proposal named).

## Out of scope (per the approved proposal, unchanged)

- Re-running the #776 harness live (issue #878 step 3,
  execution-observation) — this record covers step 2 (implementation)
  only.
- Redesigning `/orchestrate:run` step 6's verify/relay-action criteria —
  reused as-is.
- The `directive.sh` accumulation consolidation the proposal's
  Accumulation section flagged as a should-do alongside this paragraph —
  not part of the frozen "What will be done" bullets; left as the
  already-flagged follow-up for a future proposal rather than silently
  folded into this one's scope.
