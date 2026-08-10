# issue-685 — current-state survey

## What exists today

- `gates/acceptance_gate.py` already enforces a `provenance:
  executed-live|executed-unit|read` line on an **issue's** `## Acceptance`
  section when that section references an executable artifact
  (`_PROVENANCE` regex, `_EMPTY_STATE` regex). This is issue-body
  provenance, not delivery-record provenance — a different document, same
  vocabulary (`executed-live`/`executed-unit`/`read`), decided at
  `docs/issue-474/decisions/416-provenance-and-empty-state.md`.
- `roles/specs/implementation.spec.json` (target-repo role spec, consumed
  by `role-spec-reference-guard.sh`) declares the delivery record's four
  required fields: `commit_sha`, `type` (Conventional Commits enum),
  `breaking`, `verdict` (`pass`/`fail`). It carries no `provenance` field
  and no notion of a UI-facing surface today — this is exactly the gap
  issue #685 asks phase 1 to close.
- `gates/gates.py` has no diff-content classifier (no "does this diff
  touch path-class X" helper). The closest existing diff-scoped primitives
  are `changed_files(root)` (git diff path list, used throughout
  `record_enums`/`record_wellformed_in`/etc.) and per-role `write_scope`
  globs in `roles/*.json` (e.g. `roles/implementation.json`'s
  `write_scope: ["src/**", "test/**"]`) — globs already exist as a
  convention for path-set declaration, just never used for diff
  classification, only for write-permission checks (`writeset` gate,
  `gates.py:871` `overrides.get(role, ...)`).
- `docs/specs/` is the standing home for target-repo-declared config that
  gates read (`platform-capabilities.md`, `role-spec-template.schema.json`,
  `enforcement-boundary.md`, etc.) — no file there today declares UI/screen
  path globs. This is the natural home for the target-repo-declared glob
  the issue asks for, following the same declare-in-`docs/specs/`,
  read-by-a-gate shape `schema_field_orphans` already uses for
  `docs/specs/*.md` schema tables.
- No existing gate reads a target repo's diff and cross-references it
  against `docs/specs/`-declared globs today. `schema_field_orphans` reads
  `docs/specs/*.md` tables but for field-name cross-reference, not path
  globs.

## Write set this touches (paths do not exist yet — this is the new-file plan)

- new module under gates/ for the UI-facing detection + provenance
  refusal check (module name settled in the proposal), following the
  `acceptance_gate.py` module shape (pure function over already-read
  text/paths, no network, unit-testable).
- a paired test_*.py under gates/ for the three acceptance-criteria cases
  (UI+unit-only pass → refused; UI+executed-live → allowed; non-UI+unit
  pass → allowed) plus the undeclared-glob empty-state case.
- a new file under docs/specs/ where a target repo declares its
  screen-glob list; documents the fail-closed default when absent.
- `gates/gates.py` — register the new check in `ALL` (one-line addition,
  same pattern as every other entry in the `ALL` dict at line ~1229).

No existing file's runtime behavior changes; this is additive. No new
dependency, no new env var, no migration.

## Prior decisions this must stay consistent with

- `docs/issue-474/decisions/416-provenance-and-empty-state.md`: provenance
  values are `executed-live`/`executed-unit`/`read`, existence-checked only
  (not content-verified) — issue #685's provenance check should reuse this
  exact vocabulary and the same existence-only rigor, not invent a new one.
- Role-spec fields are declared per role in a `roles/specs/<role>.spec.json`
  file (`required_fields`), read by `role-spec-reference-guard.sh` — adding
  `provenance` there is an extension point the proposal must weigh
  explicitly, since it is a schema change to a file other tooling reads,
  and issue #685 is scoped to the record-gate refusal, not a schema
  rewrite across every role spec.

## Skip-condition check

Scouting does not skip here: the issue text explicitly leaves the
detection rule and the undeclared-glob default open ("detection rule
decided in phase 1", "behavior per the phase-1 fail-open/closed decision")
— this is a live design decision, not a pure bugfix and not a spec with no
open decision.
