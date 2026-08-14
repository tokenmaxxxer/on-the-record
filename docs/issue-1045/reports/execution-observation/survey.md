---
code_under_review:
  - spawn.py
  - tests/test_spawn.py
  - docs/issue-1045/proposals/panel-defect-fixes.md
  - docs/issue-1045/reports/implementation/survey.md
  - docs/issue-1045/reports/implementation.md
type: survey
loop_state: running
---

# Current-state survey — execution-observation of #1045

## Scope statement

Observed: role `issue-1045/implementation`, subject issue #1045 ("panel
live-fire: SendMessage round-trip degrades every run + degrade path
crashes on consult error"), requirement R001. Two PRs:

canonical: `gh pr view 1052`, run this session.
- PR #1052 — phase-1 proposal: MERGED.

canonical: `gh pr view 1060 --json number,title,commits,mergeCommit,mergedAt,reviews,body`, run this session.
- PR #1060 — phase-2 delivery: MERGED 2026-08-12T05:35:53Z, commit
  `6cbf19d5e4a4c266a6f7791d92ff34ed54d0e9db`, carries `Closes #1045` in
  its body.

`gh pr diff 1060` was read this session before
`docs/issue-1045/reports/implementation.md`'s own narrative (fresh-eyes
ordering). Diff hunks read: the new `docs/issue-1045/reports/implementation.md`
file in full; `spawn.py`'s `_run_panel_session()` judge-prompt hunk
(around line 4479) and the `_panel_degrade()`/new
`_consult_or_record_error()` hunk (around line 4517); the new
`PanelDegradeErrorSafety` test class hunk in `tests/test_spawn.py`.

Also read this session: `docs/issue-1045/proposals/panel-defect-fixes.md`
in full; `docs/issue-1045/reports/implementation/survey.md` in full; the
issue #1045 comment thread via `gh issue view 1045 --comments`;
`docs/specs/approvers.md`.

## What the issue asked

canonical: `gh issue view 1045`, run this session (issue body).

Two defects, requirement R001:
1. Concurrent judge sessions degrade every run — no `SendMessage`
   round-trip observed. Acceptance: "a live re-run showing at least one
   SendMessage round-trip, or a grounded record of why it cannot work
   under `claude -p`."
2. `_panel_degrade()` calls `consult_cmd()` unguarded; a consult failure
   raises out of `panel_cmd()`. Acceptance: "consult error inside degrade
   → recorded turn + error result, no exception."
Check: `python3 -m pytest tests/test_spawn.py -k panel`.

## What the observed role's artifacts show

canonical: `gh pr diff 1060`, run this session (the diff hunks named in
the Scope statement above).

- Defect 2: PR #1060's diff adds `_consult_or_record_error()` (spawn.py,
  hunk around line 4517) wrapping each `consult_cmd()` call inside
  `_panel_degrade()`; it catches `Exception`, appends a `consult-error`
  turn via `_append_panel_turn()`, and returns `(None, str(e))` instead
  of propagating. The `PanelDegradeErrorSafety` test class (3 methods,
  `tests/test_spawn.py` hunk) exercises: a failing `consult_cmd`
  producing a recorded `consult-error` turn with no raise; one side
  failing while the other returns a real verdict; `panel_cmd()`'s own
  no-round-trip trigger not propagating a consult failure.

canonical: `docs/issue-1045/reports/implementation/survey.md`, read in
full this session.
- Defect 1 diagnosis: that survey's "Defect 1" section runs a bounded
  live reproduction — two `claude -p` sessions launched via backgrounded
  subshells from that session's own Bash tool, with a bespoke minimal
  prompt instructing `ListAgents`-based discovery/retry and addressing by
  the discovered name — and reports a successful `SendMessage`
  round-trip. That survey's own text states the reproduction is "minimal
  and outside the panel prompt's wording," i.e. not
  `_run_panel_session()` or `panel_cmd()` itself, and closes by saying its
  own effect should be judged against a subsequent live `panel_cmd()`
  run rather than assumed from the survey alone.

canonical: `docs/issue-1045/proposals/panel-defect-fixes.md`, read in
full this session, line 85 area ("Out of scope" section).
- The proposal's "Out of scope" section states the same thing from the
  delivery side: a live end-to-end `panel_cmd()` re-run as part of this
  PR is explicitly excluded from scope; the text at line 85 describes a
  follow-up live re-run confirming the prompt fix specifically as a
  next step, separate from this PR's own delivery.

canonical: `gh pr diff 1060`, run this session (the `_run_panel_session()`
judge-prompt hunk).
- PR #1060's diff applies that fix to `_run_panel_session()`'s actual
  judge prompt (the `ListAgents`-with-retry / address-by-discovered-name
  instructions), the same hunk cited above.

canonical: `ls docs/issue-1045/reports/implementation/`, run this
session.
- That directory lists only `survey.md` — no separate re-run report file.

canonical: `gh issue view 1045 --comments`, run this session.
- The comment thread contains no re-run report, before or after #1045's
  merge/close.

## Approval

canonical: `gh issue view 1045 --comments`, run this session.
The comment thread contains a comment whose entire body is exactly
`APPROVE issue-1045/implementation`, posted by `JiwonJung94`.

canonical: `docs/specs/approvers.md`, read this session.
`JiwonJung94` and `jjongkwann` are the two listed accounts, so
`JiwonJung94` qualifies as an approver.

This is the observed role's own single-account-mode approval (PR
#1052/#1060 author is also `JiwonJung94`) — a real Approve, not
inferred, and it names the observed role
(`issue-1045/implementation`), not this observation role.
