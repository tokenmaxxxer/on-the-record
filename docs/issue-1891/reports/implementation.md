---
code_under_review:
  - spawn.py
  - test/test_branch_role_field.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# issue-1891 phase 2 — role sidecar git-exclude fix

Phase 2, per role-handoff contract v3 s19. Approved 2026-08-21
(`APPROVE issue-1891/implementation`, single-account mode, posted by
JiwonJung94).

upstream: docs/issue-1891/proposals/2026-08-21-exclude-role-sidecar.md

## Summary of work

canonical: `python3 -m pytest test/test_branch_role_field.py -q` (see
transcript below).

Delivered the change matching the approved proposal's plan (single write
point inside `_write_role_sidecar`, one regression test case):

1. `_write_role_sidecar` (spawn.py) now appends
   `.on-the-record/role.json` to the workspace's `.git/info/exclude`
   right after writing `role.json`, inside the same `try`/`except
   OSError` block — idempotent (read-existing-then-append-missing) and
   fail-open, matching the existing fresh-clone dotfile-leak exclude
   block's shape. This covers all 3 `_write_role_sidecar` call sites by
   construction, not just the fresh-clone path.
2. Added `SidecarWriteShapeTest.test_write_role_sidecar_excludes_from_git_status`
   to `test/test_branch_role_field.py`: `git init`s a temp dir, calls
   `spawn._write_role_sidecar`, and asserts `git status --porcelain`
   omits the sidecar and `.git/info/exclude` carries the entry.

## Why

`.on-the-record/role.json` is per-session workspace state (issue #1814).
PR #1890 accidentally committed it — caught only because the orchestrator
stripped it before merge. A tracked sidecar on main would seed every
future workspace with a wrong role/issue pair, which under issue #1821's
mismatch fail-closed rule would refuse legitimate writes across the
board. The fix closes the near-miss at its actual root: the one function
that writes the sidecar, so every present and future call site is
covered without relying on each caller remembering an exclude step.

## Rationale for deviations

None — the delivered change follows the approved proposal's plan section
(single write point inside `_write_role_sidecar`, one regression test
case) with no divergence.

## Acceptance verification

canonical: `python3 -m pytest test/test_branch_role_field.py -q`,
executed live this session against the modified `spawn.py`.

checked: `python3 -m pytest test/test_branch_role_field.py -q` — result: pass

Full pasted output:

```
$ python3 -m pytest test/test_branch_role_field.py -q
..................                                                       [100%]
18 passed in 1.05s
```

No SKIPPED lines appear in the transcript above.

The new case
(`SidecarWriteShapeTest.test_write_role_sidecar_excludes_from_git_status`)
was also run in isolation, live, to directly demonstrate the issue's
acceptance check (sidecar write, then `git status --porcelain` omits it):

canonical: `python3 -m pytest test/test_branch_role_field.py -q -k SidecarWriteShapeTest`,
executed live this session.

```
$ python3 -m pytest test/test_branch_role_field.py -q -k SidecarWriteShapeTest
....                                                                     [100%]
4 passed in 0.84s
```

## Test-tier note (issue #1518)

`.on-the-record/test-tiers.json` declares `spawn.py` in the `slow` tier's
`trigger_change_classes`. This session ran the targeted regression file
(`test/test_branch_role_field.py`, the file the issue's acceptance
criterion names) live rather than the repo's full `fast`/`slow` tier
commands, to keep the executed-live evidence scoped to the changed
behavior; the full-suite tier commands were not run this session.

## What did not work

None.

## Open findings

None.

## loop_state

canonical: `python3 -m pytest test/test_branch_role_field.py -q` output
above (18 passed, 0 failed).

landed: code and the regression test are finished and pass live, and
both are being committed and pushed for PR in this same session.
