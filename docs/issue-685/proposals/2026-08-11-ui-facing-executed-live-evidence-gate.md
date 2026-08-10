files:
  - gates/ui_evidence_gate.py
  - gates/test_ui_evidence_gate.py
  - gates/gates.py
  - docs/specs/ui-surfaces.md

## Request

An operator incident showed a delivery record claiming `verdict: pass`
with only unit-test provenance while the actual screen was dead. Issue
#685 asks: when a delivery's diff touches a UI/screen surface, refuse a
record's `verdict: pass` unless its provenance includes an
`executed-live` entry with evidence (run log, screenshot path, or
healthcheck output). Phase 1 decides the UI-surface detection rule and
what happens when a target repo has declared no UI globs at all.

## Constraints

- Reuse the existing `executed-live`/`executed-unit`/`read` provenance
  vocabulary from `docs/issue-474/decisions/416-provenance-and-empty-
  state.md` — no new vocabulary.
- Existence-only checking, matching every other record gate's rigor
  (`record_enums`, `acceptance_gate.py`): the gate confirms an
  `executed-live` provenance line with an evidence reference exists, not
  that the evidence is truthful.
- No new dependency, no new env var, no migration — this is additive
  gate logic plus one new docs/specs/ declaration file.
- Detection must be diff-scoped (`changed_files`), matching how every
  other gate in `gates/gates.py` already reads a change set.

## Rationale

Two designs were considered for where a target repo declares its UI
globs:

1. **Extend `roles/specs/implementation.spec.json`'s `required_fields`**
   with a repo-level UI-glob list. Rejected: that file is a per-role
   deliverable-field schema (`commit_sha`/`type`/`breaking`/`verdict`),
   consumed by `role-spec-reference-guard.sh` for reference resolution —
   folding an unrelated path-classification concept into it conflates two
   different schema purposes and would require every consumer of that
   spec file to learn to ignore a field that has nothing to do with
   record-field validation.
2. **A new `docs/specs/ui-surfaces.md` declaration file**, read directly
   by the new gate — chosen. `docs/specs/` is already the established
   home for target-repo-declared config gates read
   (`platform-capabilities.md`, `enforcement-boundary.md`,
   `role-spec-template.schema.json`), and `schema_field_orphans` already
   establishes the pattern of a gate parsing a `docs/specs/*.md` table.
   This keeps UI-surface declaration orthogonal to record-field schema,
   so a repo can adopt or ignore it independently of `implementation.spec.json`.

For the undeclared-glob default, the field's own tooling (dorny/paths-
filter, tj-actions/changed-files — see scout-brief.md) defaults
*permissive*: no matching filter simply means the gated job doesn't run.
That default was considered and rejected here, because it is exactly the
failure mode issue #685 reports: a repo that never got around to
declaring its UI globs would silently never trigger the check, which
reproduces the original incident (unit-only pass, dead screen, nobody
warned). Issue #685's body explicitly asks for fail-closed instead, and
this repo's existing gates already use fail-closed as house style for
missing declarations (`acceptance_gate.py`: "검사 불가는 통과가 아니다";
`record_enums`: unreadable role def → block, don't skip). So: **when
`docs/specs/ui-surfaces.md` is absent or declares no globs, any changed
path matching a small fixed fallback list of screen-like extensions/dirs
(`.tsx`, `.jsx`, `.vue`, `.svelte`, `.html`, and paths containing
`/components/`, `/pages/`, `/views/`, `/screens/`, `/ui/`) is treated as
UI-facing.** A repo opts fully out of the fallback only by writing a
literal `none` line under `## Globs` (not merely an empty section) —
`## Globs` present but empty, or the file absent entirely, both mean "no
declaration was made" and the fallback fires; `## Globs\nnone` is the one
spelling that means "this repo has no UI surface, do not fall back."
These are three distinct, mechanically distinguishable states, not two.

## What will be done

1. `docs/specs/ui-surfaces.md` — documents the declaration format: a
   fenced list of glob patterns under a `## Globs` heading (one per
   line), plus the fail-closed fallback list, and the three-state
   convention from Rationale: absent file or empty `## Globs` → fallback
   applies; `## Globs` containing only the literal line `none` → fallback
   suppressed (repo declares it has no UI surface); `## Globs` with one
   or more glob lines → those globs are used instead of the fallback.
2. `gates/ui_evidence_gate.py` — new module, `acceptance_gate.py`-shaped
   (pure functions over already-read text, unit-testable, no network):
   - `is_ui_facing(root, changed_paths) -> bool`: reads
     `docs/specs/ui-surfaces.md` if present and matches declared globs;
     falls back to the fixed screen-like pattern list per the Rationale
     above when the file is absent or declares no globs and isn't
     explicitly opted out.
   - `check_record(root, record_path, record_text) -> list[str]`: if
     `is_ui_facing` is true for the record's diff-scoped changed paths and
     the record's frontmatter/body has `verdict: pass`, requires a
     `provenance: executed-live` line with a non-empty evidence reference
     (run log path, screenshot path, or healthcheck output description) —
     same existence-only rigor as `acceptance_gate.py`'s `_PROVENANCE`
     check. Violation messages state what is missing (`provenance:
     executed-live` line) and how to add it (example line shown in the
     message).
3. `gates/gates.py` — register `ui_evidence_gate.check_record` in the
   `ALL` dict (one entry, same shape as every existing entry).
4. `gates/test_ui_evidence_gate.py` — the three acceptance-criteria
   cases plus the empty-state case:
   - UI-touching diff + `executed-unit`-only pass → refused.
   - UI-touching diff + `executed-live` evidence → allowed.
   - non-UI diff + `executed-unit` pass → allowed.
   - no `docs/specs/ui-surfaces.md` declared, but a screen-like path
     changed → treated as UI-facing (fail-closed), refused without
     `executed-live` evidence.

## Out of scope

- Verifying that the `executed-live` evidence is truthful (screenshot
  actually shows the screen, log actually corresponds to the run) — this
  repo's existing provenance checks are existence-only by established
  decision (416), and #685's own scope note says "whether the human
  actually looks at the screen remains the human's seat."
- Wiring this gate into `gates/ci.py`'s default full-suite run or any
  CI-invocation surface — issue #685's acceptance criteria only ask for
  the gate + its tests; enabling it repo-wide is a separate rollout
  decision left to a follow-up.
- Extending `roles/specs/implementation.spec.json`'s `required_fields`
  with a `provenance` field — considered in Rationale, rejected as
  out of scope for this issue (the gate can read an unstructured
  `provenance:` line from the record body without a schema change).

## Accumulation

This touches `gates/gates.py`'s `ALL` dict, a repeated-registration-shaped
file: each new gate adds one `"name": function` entry, same as every prior
gate (`schema_field_orphans`, `record_checked_claims`, etc.). At N more
gates this stays a flat dict of one-line entries — no growth pattern
changes, since `ALL` is already the accepted single registration point
every gate uses (`check(names, d, cfg)` looks names up in it). The new
`docs/specs/ui-surfaces.md` declaration file is per-repo, not per-gate, so
it does not accumulate with future gates the way `ALL` does.

## How you'll know it worked

`python3 -m pytest gates/test_ui_evidence_gate.py -q` exits 0, covering
all four cases above; `derived: python3 -m pytest gates/test_ui_evidence_gate.py -q`.
