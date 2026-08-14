---
subject: issue-1130
role: execution-observation
phase: 1
kind: current-state-survey
---

# Current-state survey — issue-1130, PRs #1147/#1148/#1150

## Scope statement

canonical: `gh pr list --state all --search "head:issue-1130" --json
number,title,headRefName,state,url`, run this session — output showed
`"state":"MERGED"` for all three PRs below.

Observed target: the `implementation` role's session for issue #1130
("role expertise realization: 20-year-practitioner judgment/planning/
deliverables/feedback/review, scoped by #1129 diagnosis"), delivered on
branch `issue-1130/implementation` as three PRs:

- PR #1147 (https://github.com/tokenmaxxxer/on-the-record/pull/1147,
  merge commit `dbe8d532d3c9d32f122968f2574a36ab260bc84c`) — the
  five-activity spec depth + gate-now hooks + cause-b routing fix
  delivery.
- PR #1148 (https://github.com/tokenmaxxxer/on-the-record/pull/1148,
  merge commit `103130b58f6179818ae380581f8693131645db1f`) — a
  same-session warrant-hunt fix (`$()`-substitution bypass in 5 new
  deny gates), commit `50b7ca71649bf267b0c787c2f4eeb132413c009f`.
- PR #1150 (https://github.com/tokenmaxxxer/on-the-record/pull/1150,
  merge commit `94b698a8fa886a1c2aef7df3c73114e4e75f827e`) — the
  record-only phase-2 delivery, commit `197f526604310e87572cf585acc453b52ec78729`,
  adding `docs/issue-1130/reports/implementation.md`.

## What was read this session (fresh-eyes ordering: diff/commits before the observed role's own record narrative)

1. canonical: `gh issue view 1130`, run this session — full issue
   body, requirements 1-4, acceptance criteria, northpole req#1/#5
   citation.
2. canonical: `gh pr diff 1147`, run this session, full diff read; file
   count derived:
   ```
   gh pr diff 1147 | grep -c '^diff --git'
   35
   ```
   35 files: 14 `roles/specs/*.spec.json` five-activity additions, 3
   new gate-now hooks (`accessibility-guard.sh`, `api-version-guard.sh`,
   `perf-measurement-guard.sh`) + 3 matching test files, 4 new cause-b
   spawn-check hooks (`test-authoring-spawn-check.sh`,
   `issue-retrospective-spawn-check.sh`,
   `interaction-design-spawn-check.sh`, `ux-engineering-spawn-check.sh`)
   + shared test file, `merge-allow-gate.sh` extension, `hooks.json`
   wiring, `gates/spec_schema_five_activities_test.py`, and
   registration-row edits to `docs/specs/enforcement-boundary.md` /
   `generated-paths.md` / `role-invariant-coverage.md`.
3. canonical: `gh pr view 1147 --json body,commits`, run this session —
   PR body's own stated test-plan line reads `python3 -m pytest gates/
   -q -k spec` with a pasted result the body itself asserts (not yet
   independently re-run at this point in the survey — see item 8 below
   for this session's own re-run). The same body's "Approval gap"
   section asserts that at #1147's own merge time no `APPROVE
   issue-1130/implementation` comment existed yet (asserted by the PR
   body; item 6 below checks this independently).
4. canonical: `gh pr view 1148 --json commits`, run this session —
   commit message `50b7ca7` states a warrant-hunt finding: 5 new deny
   gates copied `merge-allow-gate.sh`'s "bail out on any backtick/
   `$()`" line, correct for an ALLOW gate but wrong for a DENY gate
   (lets a harmless substitution buy a bypass); the commit message
   states a fix and a new regression test were added in the same
   commit.
5. canonical: `gh pr diff 1150`, run this session — the entire diff is
   one new file, `docs/issue-1130/reports/implementation.md` (68
   lines); no code changes in this PR.
6. canonical: `gh issue view 1130 --json comments -q '... test
   ("APPROVE") ...'`, run this session — four approval-related comments
   by `JiwonJung94`: `APPROVE issue-1130/requirements-engineering`
   (2026-08-13T02:19:21Z), a clarifying comment scoping phase-1
   acceptance, `APPROVE issue-1130/implementation`
   (2026-08-13T02:36:21Z), and a clarifying comment stating the earlier
   requirements-engineering APPROVE was intended to cover the whole
   proposal and this token formalizes it for `implementation`, citing
   PR #1147's write set and its own test counts. This independent read
   of the issue's own comment thread resolves item 3's second claim: an
   `APPROVE issue-1130/implementation` token exists, timestamped after
   #1147's merge commit.
7. canonical: `docs/issue-1130/reports/implementation.md` (added by PR
   #1150), read in full this session, last, per fresh-eyes ordering.
   Its narrative sections were checked against items 1-6's independent
   reads; every claim found in it had upstream diff/commit support
   already established by those items. A full step-level check of
   every sentence in it is deferred to phase 2.
8. canonical: command run this session on a fresh worktree of
   `origin/main` (`git worktree add /tmp/otr-main-check origin/main`,
   run this session), compared inline against
   `docs/issue-1130/reports/implementation.md`'s own pasted figure for
   the identical command (same file, item 7 above) —
   ```
   cd /tmp/otr-main-check && python3 -m pytest gates/spec_schema_five_activities_test.py on-the-record/hooks/test_routing_fix_spawn_checks.py -q
   this session's run: 16 passed in 0.43s
   implementation.md's own pasted figure for the same command: 13 passed
   ```
   canonical: same command output block above — logged as an observed
   number gap only, deferred to phase-2 judgment (main growth vs. other
   explanation); no verdict rendered in this phase-1 survey.
9. canonical: command run this session, same worktree, compared inline
   against PR #1147's own pasted figure (`gh pr view 1147 --json body`,
   item 3 above, same body read this session) —
   ```
   cd /tmp/otr-main-check && python3 -m pytest gates/ -q -k spec
   this session's run: 79 passed, 509 deselected in 0.50s
   PR #1147 body's own pasted figure at its merge time: 68 passed, 375 deselected
   ```
   canonical: same command output block above — same caveat as item 8,
   logged as an observed number gap, no verdict rendered here.

## Diff hunks read (admissible for step-level citation)

- PR #1147 diff, all 35 files' hunks (item 2 above, full `gh pr diff
  1147` output read this session) — the five-activity spec additions,
  the 3 gate-now hooks + tests, the 4 cause-b spawn-check hooks +
  shared test, `merge-allow-gate.sh`'s extension hunk, `hooks.json`'s
  wiring hunk, `gates/spec_schema_five_activities_test.py` in full
  (new file), and the three `docs/specs/*.md` registration-row hunks.
- PR #1148: commit message and `git show 103130b58 --stat` read this
  session (item 4 above), listing the 7 changed files and their
  line-change counts — sufficient for trajectory/outcome-level citation
  that a fix landed; the actual hunks are not yet read hunk-by-hunk as
  of this survey, so a step-level finding about the fix's own
  correctness requires reading them in phase 2 before citing.
- PR #1150 diff, full (single new file, all 68 lines, item 5 above).

## Process-state facts (no evaluation)

canonical: `gh issue view 1130` (item 1), top-level `state` field read
this session: `CLOSED`.

- canonical: `gh pr view 1150 --json commits`, run this session (item
  5's underlying call) — commit `197f526`'s body contains `Closes
  #1130`. PR #1147's and #1148's commit bodies, fetched the same way,
  carry no closing keyword.
- The approval-sequencing fact stated in PR #1147's own body (item 3:
  no `APPROVE issue-1130/implementation` at #1147's merge time) sits
  alongside item 6's independent read: that token exists, timestamped
  2026-08-13T02:36:21Z. This sequencing is left as a trajectory-level
  fact for phase-2 judgment under `approved-by-human`, not evaluated
  here.
- canonical: `find docs/issue-1130 -type f`, run this session against
  the branch checked out at session start — returned only paths under
  `docs/issue-1130/reports/*.md` and `docs/issue-1130/proposals/*.md`
  authored by other roles (`implementation`,
  `requirements-engineering`); none under any execution-observation
  path. No prior execution-observation proposal, survey, or record for
  this issue existed before this session.

## Scout-directive skip record

canonical: this role's own directive text (system context, this
session) — the phase-2 verdict procedure (outcome/trajectory/step,
citation-adjacency, evidence-mode discipline) is fully specified there;
this survey found no product-facing or design surface open for this
observation task to scout. Skip condition invoked: "the spec literally
leaves no design decision open." Scouting is skipped for this reason.
