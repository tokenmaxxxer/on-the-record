# Deviation log — issue-1597/implementation

- 2026-08-15T00:00:00Z | inline | design-rationale-guard.sh required a
  non-empty `design-rationale:` frontmatter field on
  on-the-record/commands/run.md (pre-existing gap on this file,
  unrelated to issue #1597) before any edit to it could be written;
  added the field alongside the merge-step edit. Location:
  on-the-record/commands/run.md frontmatter.
- 2026-08-15T00:00:00Z | inline | gate-registration-guard.sh refused the
  commit adding gates/patrol_wiring.py without a matching row in
  docs/specs/enforcement-boundary.md; added the row and regenerated
  docs/specs/reconciled-index.md via `python3 gates/spec_index.py
  --update` in the same commit. Location: docs/specs/enforcement-boundary.md,
  docs/specs/reconciled-index.md.
