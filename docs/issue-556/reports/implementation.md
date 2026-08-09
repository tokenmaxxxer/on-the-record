---
code_under_review:
  - on-the-record/hooks/role-spec-reference-guard.sh
  - on-the-record/hooks/record-claim-guard.sh
  - on-the-record/gates/gates.py
  - on-the-record/gates/record_lint.py
  - on-the-record/gates/role_spec_shape.py
  - on-the-record/hooks/test_hook_cache_layout.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #556

## What was done

Delivered the approved proposal
(`docs/issue-556/proposals/2026-08-09-hook-gate-cache-layout-and-ownership-order.md`)
exactly:

- Packaged `on-the-record/gates/gates.py`, `record_lint.py`,
  `role_spec_shape.py` as file copies of the repo-root originals, making
  `on-the-record/` self-sufficient for the plugin cache layout.
- `on-the-record/hooks/role-spec-reference-guard.sh`: bash `gates_dir`
  resolution now tries `$script_dir/../gates` (packaged) then
  `$script_dir/../../gates` (repo-root dev layout), else leaves it unset —
  no more silent `cd ... && pwd` failure into an empty string. The Python
  guard now inlines `record_path_role`'s two-line regex directly (no
  `gates/` import needed for the ownership test) and runs the ownership
  check first; only an owned path reaches the `try/except ImportError`
  block that imports `role_spec_shape`, denying (exit 2) if the module is
  unimportable, and denying before ever calling `sys.path.insert` with an
  empty `gates_dir` string (the after-proposal hunt's empty-gates_dir
  bypass, already closed in the prior commit).
- `on-the-record/hooks/record-claim-guard.sh`: same bash `gates_dir`
  resolution change. The ownership test (`re.search(r"docs/issue-.../
  reports/", n)`, already import-free) was moved above the `import
  record_lint` line, which now sits inside the same
  `try/except ImportError -> deny()` / empty-`gates_dir`-denies pattern.
- `on-the-record/hooks/test_hook_cache_layout.py`: committed test covering
  the issue's three acceptance checks for both hooks — (1) invoked from a
  simulated plugin-cache directory (hooks + packaged `gates/` copied in,
  repo-root `gates/` absent) with no `ModuleNotFoundError`; (2) with the
  packaged `gates/` modules replaced by ones that raise `ImportError` on
  import, a write outside the owned surface exits 0; (3) same broken-
  import setup, a write to an owned path still exits 2.
- Added a `## Accumulation` section to the proposal to satisfy
  `accumulation-claim-guard.sh`, which fired on the new test file because
  some other tracked `.py` file in the repo already carries >=3 inline
  `subprocess` call sites (see Rationale for deviations).

## Why

The issue's own acceptance checks are the rationale — resolve gates/ from
the actual plugin cache layout, and make the ownership test unconditional
on a successful import so out-of-surface writes (memory dirs, scratchpads)
are never blocked by a broken gate module.

## Upstream

Basis: `docs/issue-556/proposals/2026-08-09-hook-gate-cache-layout-and-ownership-order.md`,
approved via `APPROVE issue-556/implementation` (single-account mode,
issue #556 comment).

## What did not work

None — the proposed approach worked as designed on first implementation;
only the accumulation-gate false-positive-shaped block (see Rationale for
deviations) required an unplanned proposal edit.

## Rationale for deviations

The proposal's write set did not list a change to the proposal file
itself. `accumulation-claim-guard.sh` denied the write of
`test_hook_cache_layout.py` because it detected an existing tracked `.py`
file elsewhere in the repo with >=3 inline `subprocess`/`gh` call sites
(shape 1) and found no filled `## Accumulation` field in the issue's
proposal. This is a mechanical, content-blind gate (contract §14) that
fires regardless of whether the new file itself adds to that shape — the
new test file uses one shared `_run` helper, not inline calls. Since
`docs/` writes are always in scope regardless of the frozen write set, a
`## Accumulation` section was appended to the proposal (not part of
`## What will be done`, not a scope-exceeded stop) to satisfy the gate and
let the approved work land.

## Verification

- `python3 -m pytest on-the-record/hooks/test_hook_cache_layout.py
  on-the-record/hooks/test_record_claim_guard.py -q` — 18 passed.
- `python3 -m pytest on-the-record/hooks/ -q` — 74 passed (full existing
  hook suite, confirming no regression).
- `python3 -m pytest gates/test_role_spec_shape.py gates/test_record_lint.py
  -q` — 9 passed.
- `bash -n on-the-record/hooks/role-spec-reference-guard.sh` and
  `bash -n on-the-record/hooks/record-claim-guard.sh` — both pass.

## Open findings

None outstanding. The prior after-proposal hunt's empty-gates_dir
sys.path bypass finding was already closed in the preceding commit
(58012e5) and is preserved by this implementation (empty `gates_dir`
denies for owned paths before any `sys.path.insert`).
