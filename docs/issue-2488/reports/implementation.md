---
issue: 2488
role: implementation
author: implementation
loop_state: in-progress
upstream:
  - path: <docs/issue-2488/... or code path this record builds on>
    sha:
code_under_review:
  - PLACEHOLDER: path/to/file
type: # one of: feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert
breaking: # string
verdict: # one of: pass|fail
---

# issue-2488 — implementation record

## What was done

<!-- fill: the delivered work, concretely -->

## Why

<!-- fill: rationale for the approach taken -->

## What did not work

None.

## Upstream basis

<!-- fill: the concrete upstream inputs (docs/issue-2488/ paths or commit
shas); per contract §1, frontmatter `sha:` is `same-commit` when the cited
path lands in this same commit, else the real 40-char sha -->

## Open findings

<!-- fill: each open finding with its resolution path, or "none" -->

## Rationale for deviations
canonical: docs/issue-2488/reports/implementation/2026-08-26-hunt-skills-resolver-fix.md

This delivery ran under the build-now bypass (contract v3 s19a,
`CORE_BUILD_NOW=1`), so there is no approved phase-1 proposal to
diverge from. The one divergence worth naming: the before-landing
warrant-hunter dispatch (mandatory at that transition per
warrant-protocol) surfaced a real, reproduced defect (the `hooks/`-guard
bypass) that this delivery's own scope — fix the stale `--skills` help
text and document #1774's already-frozen collision/trust decision — did
not anticipate and does not cover. Per the warrant protocol's
scope-exceeded rule, the fix for that defect was not folded into this
delivery's write set; instead the finding was recorded in the hunt file
cited above, narrowed the new decision doc's own claim to stop
overclaiming past what the code guarantees, and left as an "Open
findings" item for the user to route (role sessions cannot file issues,
contract v3 s9).

## Next steps

<!-- fill while loop_state is non-terminal; set loop_state to the terminal
value for this record kind when done -->
