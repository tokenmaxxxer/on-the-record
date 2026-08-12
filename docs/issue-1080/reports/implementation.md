---
code_under_review:
  - spawn.py
  - gates/test_requirement_drift.py
type: fix
breaking: false
# canonical: acceptance: python3 -m pytest gates/test_requirement_drift.py -v — result: pass
verdict: pass
loop_state: landed
---

## What was done

Implemented `requirement_drift`'s infra-tag exception per the approved
phase-1 proposal (docs/issue-1080/proposals/2026-08-12-requirement-drift-infra-tag.md).
canonical: docs/issue-1080/proposals/2026-08-12-requirement-drift-infra-tag.md (read this turn)
In `spawn.py::requirement_drift`'s open-issue/PR loop (spawn.py:2519-2530),
an item whose title/body contains `_INFRA_TAG` (imported from
`gates/requirement_linkage.py`, not duplicated as a literal) is now
skipped before appending to `unreferenced_open` — mirroring the
existing exception in `gates/requirement_linkage.py` at line 49
(function `check_issue_body`).
Added `gates/test_requirement_drift.py` with three unit tests:
tagged item excluded, untagged item still flagged, and the empty-tagged
case leaving drift output unchanged.

## Why

`requirement_drift` previously flagged every open issue/PR lacking a
requirement ID, including ones carrying the sanctioned
`infrastructure/no-direct-requirement` tag (issue #745), producing a
permanent false positive per issue #1080.

## Upstream / basis

docs/issue-1080/proposals/2026-08-12-requirement-drift-infra-tag.md
(merged via PR #1094 — canonical: PR #1094 body, read this turn via `gh pr view 1094`).

## Acceptance verification

canonical: acceptance: python3 -m pytest gates/test_requirement_drift.py -v — result: pass
checked: `python3 -m pytest gates/test_requirement_drift.py -v` — result: pass

```
gates/test_requirement_drift.py::test_infra_tagged_item_excluded_from_unreferenced_open PASSED
gates/test_requirement_drift.py::test_untagged_item_still_flagged PASSED
gates/test_requirement_drift.py::test_empty_tagged_items_leaves_drift_output_unchanged PASSED
3 passed in 0.05s
```

canonical: acceptance: python3 -c "import ast; ast.parse(open('spawn.py').read())" — result: SYNTAX_OK
Also confirmed `python3 -c "import ast; ast.parse(open('spawn.py').read())"`
parses cleanly after the edit.

## What did not work

None.

## Doc placement

- No new env var, dependency, migration, or config key introduced —
  nothing routes to a handbook.
- No new public signature or wire format changed — nothing routes to
  docs/issue-1080/decisions/.
- No benchmark/investigation numbers produced — nothing routes to
  docs/issue-1080/reports/ beyond this record itself.

## Open findings

canonical: docs/issue-1080/reports/implementation/2026-08-12-hunt-requirement-drift-infra-tag.md (warrant-hunter agent aca901b6afa016bda output, this turn)
Pre-landing warrant hunt (stance 0) found: the new `import requirement_linkage`
was unguarded and would crash the whole advisory `_board_wide_sweep` tick
(aborting the subsequent spawn_coverage check too) on ImportError,
contradicting the function's own advisory/non-blocking contract.
Resolved inline this turn: wrapped the import in try/except, falling
back to `infra_tag = None` (skip check disabled, prior behavior
preserved) on ImportError — spawn.py:2518-2525.
canonical: acceptance: python3 -m pytest gates/test_requirement_drift.py -v — result: pass
Re-ran the test suite after the fix — 3 passed.

canonical: docs/issue-1080/reports/implementation/hunt-2026-08-12-requirement-drift-infra-tag.md (prior phase-1 after-proposal hunt, read this turn)
A separate, earlier (phase-1 after-proposal) hunt finding remains
unresolved: `_INFRA_TAG` is only enforced/maintained as a meaningful
marker on issue bodies by `require_requirement_linkage` (which
short-circuits when `issue is None`), so applying the same exemption to
PR text in the approved uniform `issues + prs` loop extends the
exemption onto state nothing maintains. The approved phase-1 proposal
explicitly designed the exemption to apply uniformly across the shared
`issues + prs` loop and gave no PR-specific carve-out, so this was
built exactly as approved; widening or narrowing the PR-body scope of
the exemption is a design judgment outside spawn.py's frozen write set
for this proposal (docs/issue-1080/proposals/2026-08-12-requirement-drift-infra-tag.md)
and is left for verify/a follow-up issue to weigh.
