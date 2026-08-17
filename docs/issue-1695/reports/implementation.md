---
code_under_review:
  - spawn.py
  - tests/test_spawn.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #1695

## What was done

Added `spawn.py::init_requirement_digest(cwd)` and wired it into
`init_board` (both the fresh-init path and the already-a-board path) so
that `spawn.py init` scaffolds `docs/specs/requirement-digest.md` in the
target repo whenever it's absent — a header comment, a documented
`## R-entry format` block, and an empty `## Entries` section. It never
overwrites an existing digest file (`dest.exists()` guard, same shape as
the pre-existing `approvers.md` guard).
canonical: spawn.py:902-940

## Why

Issue #1695: the requirement-linkage gate (#1017,
`gates/requirement_linkage.py`) refuses a freshly drafted issue on a new
target repo unless its body cites an `R\d+` ID, but a fresh `init` left
no ledger to cite from — every new consumer repo hit this wall on its
first spawn.

## Upstream basis

docs/issue-1695/proposals/requirement-digest-stub.md

## What did not work

None.

## Open findings

None.

## Acceptance verification

canonical: acceptance: python3 -m pytest tests/test_spawn.py -k RequirementDigestScaffold -q — result: pass
checked: `spawn.py init` on a repo without the digest creates it with a
documented R-entry format stub; running init twice does not overwrite an
existing ledger — result: pass (cases `test_creates_stub_when_absent`,
`test_init_board_scaffolds_digest_alongside_approvers`)

canonical: acceptance: python3 -m pytest tests/test_spawn.py -k RequirementDigestScaffold -q — result: pass
checked: repos that already have a ledger are untouched (empty-state
acceptance line) — result: pass (cases `test_second_run_does_not_overwrite`,
`test_init_board_leaves_existing_digest_untouched_on_second_call`)

derived: python3 -m pytest tests/test_spawn.py -k RequirementDigestScaffold -q
```
$ python3 -m pytest tests/test_spawn.py -k RequirementDigestScaffold -q
....                                                                     [100%]
4 passed in 1.02s
```

## Doc placement ladder

No env var, config key, new dependency, migration, or setup-step in this
change. Public-surface addition is `init_requirement_digest`, recorded in
docs/issue-1695/proposals/requirement-digest-stub.md's `## What will be
built` section. No benchmark/investigation numbers to place.

## Test-tier directive

canonical: `ls .on-the-record/test-tiers.json` (not found)
```
$ ls .on-the-record/test-tiers.json
ls: cannot access '.on-the-record/test-tiers.json': No such file or directory
```
No test-tiers config in this repo root. Full-suite wall-clock not
separately measured this session — only the targeted
`-k RequirementDigestScaffold` subset ran, scoped to this change's new
isolated test class (see derived fence above, 1.02s).
