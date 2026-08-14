---
status: proposed
files:
  - docs/issue-1112/reports/execution-observation.md
---

## Request

issue #1112 asks this role to judge whether the `implementation` role's
landed work on issue-1112/implementation (PR #1119, merged) was sound —
per northpole req#3 (real-wired verification) and this role's own
three-level verdict rulebook.

## Constraints

- Never edit `spawn.py`, `gates/test_consult_json_parse.py`, or any other
  path under the observed role's `src/`/`test/`/`docs/issue-1112/`
  ownership — this role's write set is `docs/issue-1112/reports/
  execution-observation.md` (and this proposal / the survey) only.
- Never re-run the observed role's task (i.e. never re-derive whether the
  consult hook-injection fix is correct by re-implementing or re-designing
  it) — only the PR diff, commits, and the observed role's own record are
  admissible evidence.
- Every verdict-bearing sentence in the phase-2 record must carry an
  adjacent citation (commit SHA, file:line, or PR comment URL).

## What will be checked and against what evidence

All three verdict levels will be rendered in the phase-2 record:

- **outcome** — recomputed as the worst case across the step-level results
  the observed record cites (its own `## Verification` section: the two
  `gates/test_consult_*.py` suites and the live consult smoke), checked
  against this session's own re-execution of those two suites at the
  commit the PR actually landed (`be8cf825`, via an isolated `git
  worktree`), plus a read of the live-smoke trace line's presence in the
  landed diff (`gh pr diff 1119`, the `docs/reports/consult-log.md` hunk).
- **trajectory** — the three named checks (scouted-when-required,
  surveyed-before-proposing, approved-by-human), each checked against:
  the observed role's own `docs/issue-1112/reports/implementation/
  survey.md` scout-skip statement; the ordering of that survey vs.
  `docs/issue-1112/proposals/2026-08-13-consult-self-hosted-hook-skip.md`
  (survey referenced by the proposal, not the reverse); and the issue
  comment thread (`gh issue view 1112 --json comments`) for a literal
  `APPROVE issue-1112/implementation` string from a
  `docs/specs/approvers.md`-listed account.
- **step** — any specific artifact found deficient, using the spec's
  per-claim vocabulary (subject/test/result/assertedBy), checked against
  `gh pr diff 1119`'s actual hunks only (diff-scope rule) — including
  the post-merge test-suite drift this session's survey already surfaced
  (current `main` fails two of the observed suite's assertions due to
  later, non-#1119 commits `14ec8d4f`/`74e40109`), which will be reported
  as a fact for the human's attention rather than as a step-level finding
  against #1119 itself, since it is not attributable to #1119's own diff
  hunks.

## Out of scope

- Judging or re-litigating #1123/#1313's own changes to
  `gates/test_consult_json_parse.py` — those are a different subject and
  not this issue's observation target.
- Filing an issue for the post-merge drift — under contract v3, issues
  are user-authored only; this role reports the fact in its record for
  the human to act on.

## How this will be verified as done

The phase-2 record `docs/issue-1112/reports/execution-observation.md`
exists, is committed on `issue-1112/execution-observation`, states all
three verdict levels (or "not applicable, because X"), and every
verdict-bearing sentence carries an adjacent citation per the rulebook
above.
