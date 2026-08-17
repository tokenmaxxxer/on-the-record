---
code_under_review:
  - gates/requirement_met.py
  - gates/test_requirement_met.py
  - on-the-record/hooks/directive.sh
  - gates/acceptance_gate.py
loop_state: handed-off
type: observation
---

## Scope

Observing the `implementation` role's session for issue #1696
("executed-live checks must require command-identity"), branch
issue-1696/implementation, delivered as PR
https://github.com/tokenmaxxxer/on-the-record/pull/1699 (author
JiwonJung94, two commits: 85189493f6050ae9a44851351fb58af1756c56d6 and
7c6253396ac4840baa11ae154b41c1057de8c515).

canonical: gh pr diff 1699 (saved to /tmp/pr1699.diff, 663 lines)
Read this session, before reading the implementation role's own record
narrative (FRESH-EYES ORDERING): PR #1699's full diff via `gh pr diff
1699`; issue #1696 body and its four comments via `gh issue view 1696
--json comments`; PR #1699's reviews via `gh pr view 1699 --json
reviews` (empty array); PR #1699's per-commit file lists via `gh api
repos/tokenmaxxxer/on-the-record/commits/<sha>`; and, after the diff,
the implementation role's own record at
docs/issue-1696/reports/implementation.md (path exists on branch
issue-1696/implementation, not on this branch — read via the PR diff's
added-file hunk, not a local file open).

## What was done

Read PR #1699 (issue-1696/implementation, JiwonJung94) end to end —
diff, both commits, issue thread, review list — and rendered a
three-level execution-judgment verdict against it: outcome
met-with-a-known-gap, trajectory sound, and one step-level finding
(gates/requirement_met.py's `_command_identity_mismatch` multi-citation
branch does not catch the same leading-token mismatch class its
single-citation branch was fixed for). No code was written or edited;
this record is the sole deliverable.

## Independence statement

This session did not author or edit gates/requirement_met.py,
gates/test_requirement_met.py, on-the-record/hooks/directive.sh,
gates/acceptance_gate.py, or any docs/issue-1696/** file produced by
the implementation role. All findings below are read from PR #1699's
diff and commits, never from re-executing the observed role's task.

## Outcome

canonical: gh issue view 1696 --json comments (body, "## Acceptance" section)
The issue's single check requires two things: (1) the orchestrate/role
directive text and the acceptance-format documentation both state a
command-identity rule, and (2) `requirement_met`'s deterministic layer
flags an executed-live check whose recorded command differs from the
check's named command surface, unit-tested with a mismatched-command
fixture.

canonical: gh pr diff 1699, hunk `@@ -304,6 +304,21 @@` in on-the-record/hooks/directive.sh and hunk `@@ -8,6 +8,21 @@` in gates/acceptance_gate.py
(1) confirmed, mode: read — the directive.sh hunk adds a
COMMAND-IDENTITY paragraph inside the ACCEPTANCE FORMAT block
(on-the-record/hooks/directive.sh, post-merge line ~307-320); the
acceptance_gate.py hunk adds the same rule to the module docstring
(post-merge line ~11-26), cross-referencing requirement_met.py as the
enforcement point.

canonical: gh pr diff 1699, hunks `@@ -37,6 +37,95 @@` and `@@ -121,6 +210,9 @@` through `@@ -138,9 +240,16 @@` in gates/requirement_met.py, and hunk `@@ -224,6 +224,81 @@` in gates/test_requirement_met.py
(2) confirmed, mode: read — the requirement_met.py hunks add
`_command_identity_mismatch()` and wire it into `grade()` as a blocking
reason independent of the semantic verdict. The test_requirement_met.py
hunk adds `t_command_identity_mismatch_blocks_even_without_yes_verdict`,
whose fixture body (naming installed `python3 -m devdigest` vs. a
recorded `PYTHONPATH=src python3 -m devdigest.cli`) mirrors the
pilot-devdigest PR #6 shape the issue cites, plus three negative
fixtures and one regression fixture for the warrant-hunt finding (see
Step, below).

canonical: this record's own Step section below, citing gh pr diff 1699's gates/requirement_met.py hunk
Per the spec's recomputation rule, the outcome verdict is the worst case
among the step-level results this record cites: one CONFIRMED gap
survives (see Step section, `_command_identity_mismatch`'s
multi-citation branch), so the outcome verdict is met-with-a-known-gap
rather than unconditionally met — the deterministic check genuinely
blocks the issue's own motivating fixture shape, but a diff-touched
branch of the same function has an unfixed instance of the identical
bug class the issue was filed to close.

canonical: gh pr diff 1699, added lines in docs/issue-1696/reports/implementation.md ("## Confirmation run" section)
Test-run outcome claims in the implementation role's own record
("19 passed", "13 passed", "2198 passed, 19 xfailed, 2 xpassed, 1 failed
[pre-existing, confirmed via git stash]", "100 passed, 2 xfailed") are
mode: asserted — this session did not re-run them (the role directive
prohibits re-executing the observed role's task); they are the observed
role's own citation, unverified independently by this session, and
this record's outcome verdict above does not rely on them beyond what
this session verified directly from the diff.

## Trajectory

canonical: gh pr diff 1699, added lines in docs/issue-1696/reports/implementation/survey.md
- scouted-when-required: not applicable, because the implementation
  role's survey file records an explicit scout-directive skip under
  that directive's own skip condition ("the spec leaves no design
  decision open" — the change is a mechanical extension of an
  already-shaped deterministic sub-check in the same function, reusing
  an already-defined citation regex from gates/record_lint.py), mode:
  read.

canonical: gh pr diff 1699, added lines in docs/issue-1696/reports/implementation/survey.md ("## Write set found by reading the codebase" section)
RESEARCH holds independently of the skip: the same survey file names
the specific write surfaces read (requirement_met.py's existing
`_artifact_in_diff_hunk` pattern, record_lint.py's
`_EXECUTED_LIVE_CANONICAL`, check_runner.py's command heuristic) before
any proposal-shaped language appears in it.

- surveyed-before-proposing, mode: read.
  canonical: gh api repos/tokenmaxxxer/on-the-record/commits/85189493f6050ae9a44851351fb58af1756c56d6 (file list); gh pr diff 1699 (ordering of the two files' content inside that commit's diff)
  Commit 85189493f6050ae9a44851351fb58af1756c56d6 lands the survey file
  and the proposal file
  (docs/issue-1696/proposals/2026-08-17-command-identity.md) together;
  the diff orders the survey's write-set section ahead of the
  proposal's build-plan section, and the proposal's Rationale section
  references decisions the survey already scoped (e.g. not
  piggybacking on acceptance-command-real-run-guard.sh). This PR used
  the contract v3 s19a build-now bypass (proposal, code, and record all
  in one commit, not a separate phase-1 PR); the survey-before-proposal
  ordering still holds inside that single commit's diff. Verdict for
  this check: holds.

canonical: gh issue view 1696 --json comments (comment 1, exact body "APPROVE issue-1696/implementation")
- approved-by-human, mode: read — the issue #1696 comment thread
  carries a comment whose entire body is exactly
  "APPROVE issue-1696/implementation", posted by JiwonJung94, an account
  listed in docs/specs/approvers.md. PR #1699's author is also
  JiwonJung94 (gh pr view 1699 --json author), so this is single-account
  mode per contract v3 s19 — string-exact match, valid. `gh pr view 1699
  --json reviews` returned an empty array, consistent with
  single-account mode using the issue-comment path instead of a
  two-account PR review. Verdict for this check: holds.

canonical: the three checks directly above (scouted-when-required, surveyed-before-proposing, approved-by-human), each already individually cited
Trajectory verdict, combining the three checks above: sound.

## Step

canonical: docs/reports/2026-08-17-hunt-command-identity-rule.md (read via gh pr diff 1699's added-file hunk) — recorded the single-citation instance of this bug class, fixed in commit 85189493f6050ae9a44851351fb58af1756c56d6
- subject: gates/requirement_met.py, `_command_identity_mismatch`'s
  `len(recorded_commands) > 1` branch (diff hunk `@@ -37,6 +37,95 @@`
  in PR #1699)
  test: does the deterministic layer catch a leading-token mismatch
  (e.g. `python` named vs. `python3` recorded) when more than one
  `acceptance:` citation exists in the diff — the same bug class the
  warrant-hunt finding cited above already flagged for the
  single-citation case
  result: failed
  assertedBy: execution-observation (this role)
  mode: read
  canonical: gh pr diff 1699, gates/requirement_met.py added lines (the `candidates = [...]` line inside `_command_identity_mismatch`)
  evidence: the added `candidates = [c for c in recorded_commands if
  _strip_env_prefix(c).split()[:1] == artifact_tokens[:1]]` line still
  filters by first-token match whenever more than one recorded command
  exists in the diff; only the `len(recorded_commands) == 1` branch
  (the two lines immediately above it) was special-cased to compare
  directly. A second recorded `acceptance:` citation elsewhere in the
  same diff (e.g. an unrelated check's proof, or a second attempt
  logged before the passing one) reintroduces the same failure mode:
  a `python3 ...` citation proving a check that names `python ...` is
  excluded from `candidates` before the exact-match comparison runs, so
  `grade()` reports `command_identity_mismatch: False` and does not
  block — silently missing the interpreter-substitution class the issue
  was filed to catch, whenever a second executed-live citation happens
  to co-exist in the same PR diff.
  - Impact: an executed-live check proven by an equivalent-but-not-
    identical command (the issue's own motivating failure mode) can
    still slip past the new grader undetected, in any PR whose diff
    carries two or more `acceptance:` citations — a realistic shape for
    a PR covering more than one check.
  - Timeline: introduced in commit
    85189493f6050ae9a44851351fb58af1756c56d6 (2026-08-17T03:42:11Z); the
    single-citation instance of the same bug was caught by the role's
    own warrant-hunt and fixed in the same commit; this multi-citation
    instance was not caught (the hunt's dispatched fixture used a
    single-citation diff) and remains present in PR #1699 as of this
    session.
  - Root cause: the fix for the single-citation case special-cased only
    `len(recorded_commands) == 1`; the first-token filter used to
    disambiguate the multi-citation case was left unchanged, so it
    still excludes a legitimate mismatch candidate whenever the leading
    token differs, regardless of citation count.
  - Action item: extend `_command_identity_mismatch`'s multi-citation
    branch to also compare the artifact against every recorded command
    directly (not only same-first-token ones) before concluding
    no-mismatch, or add a regression fixture with two `acceptance:`
    citations (one same-first-token non-match, one different-first-token
    exact match) to make the gap fail loudly instead of silently. This
    role does not file issues under contract v3; the human approver
    routes this finding.

## Open findings

canonical: this record's own Step section above
- gates/requirement_met.py's `_command_identity_mismatch` multi-citation
  branch does not catch a leading-token mismatch when a second
  `acceptance:` citation exists in the diff (Step finding above).
  Resolution path: human approver decides whether to open a follow-up
  issue against the multi-citation branch; this role does not file
  issues under contract v3.

## Next steps

canonical: this record's own phase-2 sections above (Outcome, Trajectory, Step)
Nothing further from this role beyond what is recorded above. The open
finding above awaits human routing.
