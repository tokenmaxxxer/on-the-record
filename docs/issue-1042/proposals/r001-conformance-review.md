---
status: proposed
files:
  - docs/issue-1042/reports/conformance-review.md
---

## Request

issue #1042 cites requirement R001 (multi-session/multi-machine
correctness family): `spawn.py::require_requirement_linkage`'s
branch-existence check must detect a remote-only `issue-N/...`
branch as already-spawned, using an exact-ref check rather than
`git branch -a --list` glob matching against `-a`'s display prefix.
This review checks the delivered commit on
`origin/issue-1042/implementation` against that requirement.

## Constraints

- Per the conformance-review role directive: per-requirement verdict
  only (Present/Surface/Absent/Incorrect/Unverifiable), never a
  holistic code-quality judgment, never a fix.
- Phase 2 (rendering the verdict and writing the record) works from
  the artifact and the spec only, deliberately without the building
  agent's stated intent, per the same directive.

## What will be done

Requirement list (single item, no sampling needed):

- R001 — the branch-existence check in
  `require_requirement_linkage` must detect a remote-only
  `issue-N/...` branch as already-spawned (not misread as
  never-spawned), per issue #1042's fix direction (exact-ref check
  via `git for-each-ref`) and acceptance criterion
  (`python3 -m pytest tests/test_spawn.py -k remote_branch`).

Phase 2 will render the R001 verdict against `spawn.py` and
`tests/test_spawn.py` on `origin/issue-1042/implementation`
(commit fb505bd7) and write it to
docs/issue-1042/reports/conformance-review.md.

## Out of scope

Any requirement not cited by issue #1042. Any fix to findings —
findings hand off to the owning role, never fixed here.

## How you will know it worked

docs/issue-1042/reports/conformance-review.md exists with an R001
verdict, citing spawn.py:1058-1061 and the acceptance test run as
evidence.
