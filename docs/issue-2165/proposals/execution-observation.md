---
status: proposed
files:
  - docs/issue-2165/reports/execution-observation/survey.md
  - docs/issue-2165/proposals/execution-observation.md
  - docs/issue-2165/reports/execution-observation.md
---

# Proposal — issue #2165: execution-observation

Phase 1 only, per role-handoff contract v3 s19. No verdict language below —
outcome/result is named here as what phase 2 will check, not decided.

Skip condition stated per scout-directive / survey-order-directive: scouting
is skipped because the spec leaves no design decision open. canonical:
roles/specs/execution-observation.spec.json's own gate_c_status field,
quoted in docs/issue-2165/reports/execution-observation/survey.md's "Scout
skip record" section — the verdict method (worst-case recomputation over
cited results) and the record's own field shape (EARL 1.0
subject/test/result/assertedBy) are both fixed by that spec file, leaving
this round nothing to scout a comparable-system pattern against.

## Request

Fill the pre-existing skeleton at
docs/issue-2165/reports/execution-observation.md (issue #2135's
convention) with a verdict on the four commits landed on branch
issue-2165/implementation, against the acceptance criterion issue #2165's
own body states.

## Constraints

- Write only docs/issue-2165/reports/execution-observation.md (no
  backticks — an out-of-scope, not-yet-committed scaffold path per issue
  #2135's convention) — this role's sole write_scope entry per
  roles/specs/execution-observation.spec.json.
- Never edit gates/spawn_on_pr.py, tests/test_spawn_on_pr.py,
  tests/test_spawn_on_pr_park.py, or the implementation role's own
  docs/issue-2165/ subtree — those are read-only inputs, read via a
  separate git worktree checked out from issue-2165/implementation, kept
  out of this branch's own tree entirely.
- No fabricated result: the frontmatter result field is the worst case
  across every cited test entry (the spec's own recomputation rule), never
  a standalone summary asserted independently of what was actually run.

## Rationale

**Chosen approach: independently re-execute the issue's own
Acceptance-named commands** (`tests/test_spawn_on_pr.py`,
`tests/test_spawn_on_pr_park.py`) in a separate read-only worktree, rather
than only reading the phase-2 record's own pasted test-output transcript.
This matches the role spec's own framing of what makes this role's verdict
non-discretionary: roles/specs/execution-observation.spec.json's
gate_c_status states the check holds because "two independent observers
re-running the same test set against the same commit sha produce the same
worst-case verdict" — re-running, not merely re-reading, is the reason the
spec gives for why this role's judgment reduces to mechanical aggregation
rather than an investigative finding.

**Rejected alternative: trust the phase-2 record's own pasted test-output
transcript without independent re-execution** (the shape
docs/issue-659/proposals/execution-observation.md's own Constraints section
chose for a prior issue — "never re-execute the observed role's code").
Rejected here because the spec's own hollow-instance gate requires at least
one non-untested, non-cantTell entry tied to a command actually run, and a
pasted transcript inside a record authored by the same session that wrote
the code under review is not independently verifiable by a reader as
genuine — re-running the exact named commands this session, in a worktree
this role never wrote to, produces a citation this role can stand behind as
its own, not a second-hand quote of the implementing role's own claim about
itself.

## What will be done

1. In a separate `git worktree` checked out from `issue-2165/implementation`
   (kept out of this branch's own tree), re-run
   `python3 -m pytest tests/test_spawn_on_pr.py tests/test_spawn_on_pr_park.py -q`
   — the exact command issue #2165's own Acceptance clause names — and the
   phase-2 record's stated neighbor sanity check
   (`tests/test_watchdog_local_signals.py`, `tests/test_watchdog_freshness.py`).
2. Fill docs/issue-2165/reports/execution-observation.md (no backticks —
   an out-of-scope, not-yet-committed scaffold path) per the
   pre-existing skeleton's own five headings (delivered-work summary, why,
   upstream basis, open findings, next steps), with frontmatter
   `subject`/`test`/`result`/`assertedBy` resolving to the commit sha and
   commands actually re-run in step 1, `result` set to the worst case
   across every cited entry, and `loop_state: handed-off` (this role's own
   terminal state per `roles/specs/execution-observation.spec.json`).
3. Disclose, as open findings with their own resolution path (not as
   blocking defects), anything this round observes outside the artifact's
   own correctness — e.g. PR #2170's own merge state at observation time.

## Out of scope

- Editing `gates/spawn_on_pr.py`, any test file, or the implementation
  role's own `docs/issue-2165/` paths.
- Filing a follow-up issue for any open finding — issues are user-authored
  only (contract v3); this role's record is the disclosure mechanism, not
  the filing mechanism.
- Judging whether PR #2170 should land on main — a human merge/close
  decision, outside this role's own write_scope and judgment.

## How you'll know it worked

The target record (docs/issue-2165/reports/execution-observation.md, no
backticks — an out-of-scope, not-yet-committed scaffold path) is committed
on this branch with `subject`/`test`/`result`/`assertedBy` frontmatter each
resolving to a real repo path, commit sha, or command actually run this
round; `loop_state: handed-off`; at least one non-untested, non-cantTell
test entry backed by a command re-executed in step 1 above (not merely
read); and every open finding carrying its own resolution path.
