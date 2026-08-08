---
code_under_review: HEAD
loop_state: landed
---

Subject: issue-541

## What was done

Removed the `"path"` key from `roles/interaction-design.json`. That key
was added by commit `88baa3e` as an apparent omission-fix, but
`interaction-design` was one of three roles (`interaction-design`,
`defect-verification`, `issue-retrospective`) intentionally left without
a `path` so `test_gates.py::t_new_roles_resolve_without_a_local_checkout`
exercises `spawn.py`'s github-fallback `rulebook_source` branch. Adding
`path` silently pulled `interaction-design` back onto the local-checkout
path, breaking that test in clean worktrees (no local checkout present).

## Why

The test's docstring records a load-bearing reason for exactly three
github-only roles: the github-fallback code path needs at least one real
end-to-end exercise, not just be present in code. Nothing indicates that
requirement was deliberately retired; `88baa3e`'s message shows the
`path` addition was an accidental side-effect of a batch role-spec pass.
Restoring the no-`path` shape is a single-key revert to the previously
intended, still-documented behavior — see rationale in
docs/issue-541/proposals/2026-08-09-fix-interaction-design-path-regression.md.

## Upstream / basis

docs/issue-541/proposals/2026-08-09-fix-interaction-design-path-regression.md

## What did not work

None.

## Doc placement

- N/A — single-file behavior fix, no new env var/config key/dep/migration/
  setup step, no public-signature or wire-format change, no benchmark
  numbers to record.

## Open findings

None.
