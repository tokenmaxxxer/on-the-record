---
status: proposed
files:
  - on-the-record/hooks/pr-preflight.sh
  - on-the-record/hooks/test_pr_preflight.py
---

# Proposal — issue #1310: pr-preflight machine-comment cursor auto-advance

## Request

Fix `pr-preflight.sh` so machine-generated issue comments (watchdog
judgment pairs, poll-reports, consult traces, reconcile lines) never block
`gh pr create` by themselves and auto-advance the session's acked-comment
cursor, while an operator (human) comment keeps the current blocking
behavior until the session re-reads the thread and advances its cursor by
citing the comment in its record. #1310

## Constraints

- Operator-comment blocking must stay byte-identical to today's behavior:
  same `amendments-reconciled: issuecomment-<id>` citation mechanism, same
  fail-open policy on any lookup/parse failure.
- Detection must be author-based first, falling back to stable text
  patterns — per the issue's own requirement 1 and the phase-1
  conformance-review consult it cites (`docs/issue-1199/reports/
  consult-log.md`, 2026-08-14T00:40:29Z entry).
- No new persistent cursor file: the existing `amendments-reconciled` line
  in the role's own record already serves as the cursor position for
  operator comments (requirement 3's "pure cursor-push without a read is
  not a bypass" — the re-read-and-cite step stays mandatory for operator
  comments only).
- Empty state (no comments at all, or no comments newer than spawn) keeps
  passing exactly as today (issue's Acceptance "empty state" line).

## Rationale

**Chosen approach:** classify every comment newer than spawn time as
machine or operator via `_is_machine_comment()` (author login pattern OR
one of the bracket-prefix/heading text patterns the survey found actually
in use: `[on-the-record]`, `[watch]`, `## Framing snapshot —`, the
consult-trace line shape, and the wider watchdog tag family
`[poll-report]`/`[watchdog]`/`[reconcile]`/etc.), then run the existing
issue #1177 "newest comment after spawn" block only against the filtered
operator subset. Machine comments are simply excluded from the block
computation — no separate advance step needed, which is what "auto-advance
the cursor" cashes out to given the existing single-newest-comment cursor
model.

**Rejected alternative — an explicit persisted cursor file per session**
(e.g. `runs/pr_preflight_cursor/<key>.json` written on every hook run):
this would let a session "advance the cursor" over machine comments
without touching its record at all. Rejected because it duplicates the
`amendments-reconciled` mechanism issue #1177 already built and adds a new
piece of on-disk session state the record-shape/record-claim directives
don't expect — the issue's own requirement 3 explicitly frames the cursor
as advanced "after re-reading" via the record, not via a side file, and
the acceptance bar only asks for pass/refuse behavior, not a new
persistence format.

**Rejected alternative — pattern-only detection, no author check**:
faster to write, but the issue explicitly orders "identified by author
account when possible, by stable text patterns otherwise" and the
conformance-review consult explicitly flags pattern-only as a spoofable
weakening of the gate's purpose (an operator could accidentally or
deliberately phrase a comment starting with a machine marker and slip
past). Author-based detection is checked first and wins whenever a
distinct bot-shaped login is present; pattern matching is the fallback for
this repo's common single-account mode, not the sole check.

## What will be done

1. In `on-the-record/hooks/pr-preflight.sh`'s embedded Python (issue #1177
   block), add:
   - `_MACHINE_LOGIN_RE` — matches a login ending in `[bot]`, or equal to
     a small set of known service-account shapes (`github-actions`,
     `github-actions[bot]`, `dependabot[bot]`).
   - `_MACHINE_BODY_RE` — matches a comment body that starts with (after
     stripping leading whitespace) one of: `[on-the-record]`, `[watch]`,
     `[poll-report]`, `[watchdog]`, `[watchdog-crash]`, `[reconcile]`,
     `[orphaned]`, `[resume]`, `[returned-pr]`, `[health]`, `## Framing
     snapshot —`, or the consult-trace line shape `- <ISO8601> | role=`.
   - `_is_machine_comment(c)` returning True if the login matches
     `_MACHINE_LOGIN_RE` OR the body matches `_MACHINE_BODY_RE`.
2. Change the "find the newest comment overall" scan
   (spawn_ts/newest-comment loop) to skip any comment where
   `_is_machine_comment(c)` is True, so the block only ever considers the
   newest *operator* comment newer than spawn time. Everything downstream
   (the `amendments-reconciled` deny/citation logic) is untouched.
3. Add unit tests to `on-the-record/hooks/test_pr_preflight.py` mirroring
   the acceptance bar's three named cases, in the same end-to-end
   (stubbed-`gh`) style the existing issue #1177 tests use:
   - a stream of machine comments (mixed marker shapes) landing after
     session start → `gh pr create` passes with no record citation needed.
   - one operator comment landing after session start (alongside machine
     comments) → refused until the record's `amendments-reconciled` line
     cites that operator comment's id; passes once cited.
   - empty state (no comments at all) → passes, matching the existing
     `test_hook_allows_pr_when_no_comments_at_all` case.

## Out of scope

- No new cursor-persistence file/format (see Rationale).
- No change to the two-account/single-account approval mechanism, the
  `check_body`/plan-parsing logic, or the phase-1 closing-keyword refusal
  — none of those are touched by this fix.
- No attempt to make pattern detection unspoofable — an operator who
  deliberately opens a comment with a machine marker string can still
  slip past pattern-only detection; this is the same acknowledged
  trade-off the conformance-review consult already named, not newly
  introduced here.

## Accumulation

`_MACHINE_BODY_RE` is one regex alternation, not a per-marker inline
`gh`/subprocess call — adding a new machine-comment shape in future is a
one-line alternation edit to that single regex, not a new call site, so
this does not accumulate the "inline subprocess call per shape" pattern
`accumulation-claim-guard.sh` flags. If a future issue adds another
machine-comment producer with its own marker text, the fix is the same
one-line regex extension; no growth in call sites, no repeated per-file
edits across `roles/*.json`-style lists.

## How you'll know it worked

`python3 -m pytest on-the-record/hooks/test_pr_preflight.py -v` passes,
including the three new cases, and the existing issue #1177/#741/#854
cases in the same file stay green (pasted output in the phase-2 record).
