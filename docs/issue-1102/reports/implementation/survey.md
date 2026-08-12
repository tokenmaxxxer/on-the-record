# issue-1102 current-state survey

Scope: wire a roles/specs/*.spec.json trigger so gates/roles_due.py
surfaces a specialist role when a landing obligation is failing.

## What exists today

- `gates/roles_due.py` already implements a generic `use_when.trigger`
  predicate per role spec: `path_patterns` (fnmatch over the diff's
  changed files) and/or `content_patterns` (regex over those files'
  current content), gated by `record_absent_for` (a board record path
  under `docs/issue-<n>/reports/<role>.md`) and a commit-ancestry "does
  the record cover this diff" check. `_trigger_matches` is the single
  predicate-evaluation function; it only reads `changed` (the diff'd
  file list) — nothing today reads filesystem state outside the diff.

  canonical: gates/roles_due.py:39-56,86-111,148-197 (read this turn)

- `gates/test_roles_due.py` builds a scratch git repo plus scratch
  roles/specs/*.spec.json fixtures per case (`_write_spec` helper), so
  the evaluator's tests are independent of this repo's real specs —
  the existing convention this issue's new cases extend.

  canonical: gates/test_roles_due.py:27-63 (read this turn)

- `roles/specs/security-threat-model.spec.json` is the one live example
  of a spec carrying a non-empty `trigger` (path/content patterns plus
  `record_absent_for`) — the closest precedent for the shape of the
  new trigger this issue adds.

  canonical: roles/specs/security-threat-model.spec.json, use_when.trigger block (read this turn)

- A module for landing obligations was proposed by a prior PR but was
  not built — that PR's own write set item for it landed as text only,
  and its Out of scope section names the roles/specs trigger wiring
  (this issue) as a deferred follow-up.

  canonical: docs/issue-1098/proposals/2026-08-12-post-landing-verify-refile-loop.md, section "Out of scope", item 1 (read this turn)
  derived: find . -iname "landing_obligation*py" -not -path "*/node_modules/*"

```
(no output)
```

  derived: grep -rl "landing_obligation" roles/ docs/handbooks

```
(no output)
```

## The gap this issue closes

The trigger predicate is diff-shaped only — it reads the changed file
list from the branch's diff. A landing obligation's failing status
would live in a per-issue obligation record file that is filesystem
state, not necessarily part of the current branch's diff against
origin/main. Wiring the trigger needs one more predicate kind, beside
path/content patterns: one that reads obligation records directly,
independent of the diff, so it degrades to the acceptance's required
empty state (no obligations -> no role surfaced) until obligation
records start getting written by whatever later builds that writer.

## Write set for this issue

- `gates/roles_due.py` — add the new predicate.
- `gates/test_roles_due.py` — cases per the issue's acceptance list.
- `roles/specs/defect-verification.spec.json` — the mapped specialist
  role's `use_when.trigger` gains the new predicate.
  `defect-verification`'s existing board_condition ("an
  execution-observation or conformance-review record's result is
  disputed by another comment on the same commit sha AND no
  defect-verification record exists yet for that dispute") is the
  closest match among the existing role specs surveyed by reading each
  spec's use_when.board_condition line: a landing whose
  re-verification came back failing is a disputed result needing
  independent reproduction.

  canonical: roles/specs/defect-verification.spec.json, use_when.board_condition (read this turn)

- one new ADR file under this issue's decisions tree, for the new
  trigger-predicate shape (a wire-format addition to the spec JSON
  schema) — path frozen in the proposal, not yet created on disk.

## Design decision this survey surfaces (feeds the proposal's Rationale)

Which role gets the trigger, and whether the obligation predicate
depends on the not-yet-built obligation-writer module or reads
obligation record files directly. Both are decided in the proposal,
not here.
