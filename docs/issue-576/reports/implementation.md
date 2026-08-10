---
code_under_review: HEAD
type: fix
breaking: false
verdict: landed
loop_state: landed
---

Subject: issue-576

# Implementation record

## Summary of work

Adds `_open_pr_for_branch(root, branch) -> int | None` (spawn.py, near
`_pr_for_branch`), using `gh pr list --head <branch> --state open`.
Swaps the `_watch` pipeline's `pr-opened` resolution call site
(spawn.py:4372-4378) from `_pr_for_branch` to `_open_pr_for_branch` so a
reused head branch whose earlier PR already merged resolves to the new
OPEN PR, not the stale merged one. Updates `test_spawn.py`'s `_run`
helper to patch `_open_pr_for_branch` instead, keeping its
`pr_for_branch=` parameter name. Adds one regression test: merged PR +
new PR on same head branch -> reported `pr-opened` URL is the new one.

## Why

Root cause per docs/issue-576/reports/implementation/survey.md:
`_pr_for_branch`'s `--state all` filter with `.[0].number` can resolve
to an already-merged PR when a head branch is reused across rounds.
`_pr_for_branch` itself cannot be narrowed to `--state open` because
`approve_scope` (spawn.py:1225) depends on `--state all` matching a
merged PR (approval can live in comments on an already-merged phase-1
PR). A new `--state open`-only helper isolates the fix to the one call
site (`_watch`'s `pr-opened` resolution) that actually wants open-only
semantics, matching the file's existing per-`--state` wrapper
convention (`_merged_pr_for_branch`, `_pr_open_or_merged_for_branch`)
and the analogous prior fix at `ensure_pushed` (spawn.py:3994, issue
#60).

## Upstream basis

docs/issue-576/proposals/2026-08-10-pr-opened-open-state-filter.md

## What did not work

None.

## Open findings

Reported (not fixed), per proposal's Out of scope:
- Stall report on an already-completed session — no concrete repro in
  issue #576, needs its own issue with repro evidence.
- DEAD watcher — same: no concrete repro captured, out of scope here.

## Doctrine ladder

No env var / config key / new dependency / migration / setup step, no
library-or-format choice over a named alternative changing a public
signature or wire format beyond the new internal helper's own
signature (which the proposal already froze), and no benchmark/
investigation numbers produced. No `docs/decisions/` or
`docs/reports/` entry required.

## Next steps

None — scope is fully delivered per the approved proposal.

## Resolution path

N/A — no open blocking finding against this record.
