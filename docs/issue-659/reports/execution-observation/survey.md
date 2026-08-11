# Current-state survey — issue #659 step 4 (execution-observation)

## Scope

Named target: role `implementation`, issue #659, PR #712
(`feat(issue-659): batch-eligibility + plan-order gates (phase 2)`), merged
`2026-08-11T02:26:44Z` (`gh pr view 712 --json mergedAt`, read this session).
Commits `b2d913e9cb0e6f83bf7ddae6d4d19e6f3f1e9ab1` and
`ade05a1f314b40ab724284b784f89b5184b57de2` (`gh pr view 712 --json commits`, read
this session). Implementation's own record,
`docs/issue-659/reports/implementation.md` (loop_state: landed, verdict: pass),
read this session.

## What was read

- `gh issue view 659` — issue body, Acceptance clauses, execution plan, prior
  comments (including the `APPROVE issue-659/architecture` and
  `APPROVE issue-659/implementation` comments already posted; no
  `APPROVE issue-659/execution-observation` comment exists yet).
- `gh pr view 712 --json commits,files,mergedAt,url` — full commit list, file diff
  stat, merge timestamp.
- `docs/issue-659/reports/implementation.md` — implementation's own account of
  what shipped.
- `docs/issue-659/proposals/product-discovery.md` — the pre-registered hypothesis
  package (metric, threshold, decision rule) this step must measure against.
- `docs/specs/approvers.md` — confirms `JiwonJung94` and `jjongkwann` are the
  listed approvers; the phase-2 approval gate (`approval-gate.sh`) blocks writing
  this role's phase-2 record until one of them posts
  `APPROVE issue-659/execution-observation` on the issue.

derived: `find docs -path "*/decisions/batch-*" -o -path "*/decisions/spawn-refusal-*"`
```
(no output — no matching files)
```
No gate-produced audit record exists repo-wide, meaning neither gate has fired on
real traffic since PR #712 landed.

derived: `gh pr list --state merged --search "merged:>=2026-08-11T02:26:44Z" --json number --jq length`
```
9
```
This includes PR #712 itself at the boundary, so at most 8 PRs have landed
strictly after gate-ship.

## What this means for phase 2

The pre-registered metric (`docs/issue-659/proposals/product-discovery.md`,
"Pre-registered hypothesis package") requires a rolling window of the next 20
landed PRs after both gates ship, plus at least one gate-produced audit record
to compute `wrongly_batched_or_spawned_rate`. Neither condition is met per the
counts derived above. Per the issue's own Acceptance clause
("deferred-with-reason if the window is unfilled"), phase 2's outcome-level
verdict will be effect-not-demonstrated / deferred-with-reason — not a
fabricated ratio.
