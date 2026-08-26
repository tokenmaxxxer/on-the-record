---
issue: 2451
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: gh issue view 2451
    sha: same-commit
code_under_review:
  - on-the-record/directive/merge-gates.md
  - docs/issue-2451/reports/implementation.md
type: docs
breaking: "none — additive directive guidance only, no behavior/API changed by this commit itself"
verdict: pass
---

# issue-2451 — implementation record

## What was done

Two-part fix for GitHub issue #2451 (stray branches survive `gh pr merge`
because it never passes `--delete-branch`, and the repo's
`deleteBranchOnMerge` setting does not reliably cover API/CLI-driven
merges):

### Part 1 — directive fix

acceptance: `git diff on-the-record/directive/merge-gates.md` — result:
```diff
@@ -98,6 +98,12 @@
    every other outcome is HOLD — never merge on the LLM verdict alone. A
    correct MERGE blocked by a flaky deterministic gate surfaces to the
    human as a HOLD, not an auto-reject.
+- DELETE-BRANCH ON MERGE (issue #2451): every `gh pr merge` call MUST pass
+  `--delete-branch`. The repo's `deleteBranchOnMerge` setting does not
+  reliably cover API/CLI-driven merges — this session directly observed
+  merged PRs (e.g. #2439, #2413) whose head branch survived without it.
+  Omitting the flag leaves stray `issue-<n>/<role>` branches on the
+  remote after merge.
 - STALE-REVERT AT MERGE (issue #1664): the same pre-merge step also runs
   `gates/stale_revert_guard.py` `classify()`/`check_pr()` — a PR whose
   merge would delete content base HEAD already has that was added after
```

Bullet placed immediately before the existing `STALE-REVERT AT MERGE
(issue #1664)` bullet, in the same pre-merge-steps section as
`VERDICT-ASYMMETRY AT MERGE`, following the existing bullet
voice/citation style.

### Part 2 — backfill cleanup

acceptance: `gh pr list --repo tokenmaxxxer/on-the-record --state merged --json headRefName,number --limit 2000` (1504 rows) cross-referenced against `git ls-remote --heads origin` (BEFORE snapshot, 40 heads), excluding any branch also present in `gh pr list --state open --json headRefName,number` (14 rows) and this session's own `issue-2451/implementation` — result:
```
BEFORE stray count: 11
issue-1978/implementation           (PR #1979)
issue-2001/implementation           (PR #2002)
issue-2156/conformance-review       (PR #2162)
issue-2186/implementation           (PR #2192)
issue-2187/implementation           (PR #2191)
issue-2227/execution-observation    (PR #2346)
issue-2274/conformance-review       (PR #2316)
issue-2293/execution-observation    (PR #2374)
issue-2413/conformance-review       (PR #2423)
issue-2413/execution-observation    (PR #2424)
issue-2414/conformance-review       (PR #2426)
```

None of the 11 appeared in the open-PR list, so none were recut-branch
cases (issue #2402) — all cleared for deletion.

acceptance: `git push origin --delete <branch>` run once per branch in the list above — result:
```
issue-1978/implementation           - [deleted]
issue-2001/implementation           - [deleted]
issue-2156/conformance-review       - [deleted]
issue-2186/implementation           - [deleted]
issue-2187/implementation           - [deleted]
issue-2227/execution-observation    - [deleted]
issue-2274/conformance-review       - [deleted]
issue-2293/execution-observation    - [deleted]
issue-2413/conformance-review       - [deleted]
issue-2413/execution-observation    - [deleted]
issue-2414/conformance-review       - [deleted]
```

acceptance: same cross-reference re-run after deletion (fresh `git ls-remote --heads origin`, `gh pr list --state merged`, `gh pr list --state open` pulls) — result:
```
AFTER stray count: 0
```

`git ls-remote --heads origin` head-total went 40 → 30, not 40 minus 11 =
29, because a `diff` of the two raw `git ls-remote` captures shows a
concurrent unrelated session pushed `issue-2467/implementation` between
the before/after snapshots; it has no associated merged PR yet, so the
cross-reference logic correctly excludes it from the stray count.

## Why

canonical: `gh issue view 2451 --repo tokenmaxxxer/on-the-record` (read this session)

The gap was a missing instruction, not a code defect: `pipeline.py`'s own
comments already assumed orchestrator-driven merges carry
`--delete-branch` (per the issue body, which quotes that comment), but
`merge-gates.md` — the directive file orchestrator sessions actually
read — never said so, and the repo's `deleteBranchOnMerge` setting does
not reliably cover API/CLI-driven merges (the issue's own before-state:
PR #2439 and PR #2413's branches survived without deletion despite that
setting). Adding one bullet in the existing pre-merge-steps section, in
the neighboring bullets' voice/citation convention, is the cheapest fix
and keeps future merges from re-accumulating the same clutter. The
backfill is a one-time cleanup of already-existing leakage; it
deliberately excludes any branch a still-open PR points at (verified
empty overlap above), since that overlap is the recut-branch case tracked
separately by issue #2402 and is out of scope here.

## What did not work

None.

## Upstream basis

canonical: `gh issue view 2451 --repo tokenmaxxxer/on-the-record` (read
this session). No prior phase-1 proposal record exists for this issue in
this repo — this is a direct build-now delivery (`CORE_BUILD_NOW=1`, no
proposal round). The issue body is the only upstream input, specifying
both the directive-bullet requirement and the backfill acceptance check
verbatim; both are addressed in this same commit, so `sha: same-commit`.

## Open findings

none

## Next steps

Both acceptance checks (the directive diff and the before/after branch
counts, both shown above) were executed live in this session; loop_state
is terminal and no next steps remain for this record.

skill-verdict: work-in-english — applied: invoked; did the doc edit, commit messages, PR body, and record body in English per this skill's routing rule
skill-verdict: implementation-blueprint — not-applicable: single-file directive-text edit plus CLI cleanup, no multi-module code architecture decision
skill-verdict: implementation-complexity-coupling-management — not-applicable: no class/coupling metric or check-pipeline ordering decision involved
skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-pattern indirection decision involved
skill-verdict: implementation-performance-data-structure-choice — not-applicable: no data-structure/algorithm/communication-scheme choice involved
