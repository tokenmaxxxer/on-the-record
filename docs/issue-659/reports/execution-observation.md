---
code_under_review:
  - gates/risk_report.py
  - gates/flows.py
  - on-the-record/hooks/impact-guard.sh
  - on-the-record/hooks/plan-order-guard.sh
  - on-the-record/hooks/hooks.json
  - gates/test_batch_eligible_groups.py
  - gates/test_plan_order_blocked.py
  - docs/specs/generated-paths.md
  - docs/specs/enforcement-boundary.md
type: observation
breaking: false
verdict: pass-deferred
loop_state: handed-off
---

# Execution-observation report — issue #659 step 4

## Independence statement

This role did not author or edit the observed artifact this session. All
verdicts below judge PR #712 (`feat(issue-659): batch-eligibility + plan-order
gates (phase 2)`, merged `2026-08-11T02:26:44Z`,
https://github.com/tokenmaxxxer/on-the-record/pull/712) and
`docs/issue-659/reports/implementation.md` as read this session — no
`gates/`, `on-the-record/hooks/`, or implementation's own docs paths were
touched. No code was re-executed to produce this record; `gates/`,
`on-the-record/hooks/`, and implementation's `docs/issue-659/` subtree are
untouched by this session.

## What was done

Read PR #712's commits (`b2d913e`, `ade05a1`), its file diff, its own record
(`docs/issue-659/reports/implementation.md`, `loop_state: landed`, `verdict:
pass`), the issue's Acceptance clauses (`gh issue view 659`), the
pre-registered hypothesis package (`docs/issue-659/proposals/product-discovery.md`),
and `docs/issue-659/reports/execution-observation/survey.md` (this role's own
phase-1 current-state survey), then rendered a three-level verdict
(outcome/trajectory/step) against that evidence, per
`docs/issue-659/proposals/execution-observation.md`.

## Why

Basis: `docs/issue-659/proposals/execution-observation.md` (approved via the
issue-level comment `APPROVE issue-659/execution-observation`,
https://github.com/tokenmaxxxer/on-the-record/issues/659, posted by
`JiwonJung94`, a listed approver per `docs/specs/approvers.md`).

## Verdict — outcome

**effect-not-demonstrated / deferred-with-reason.** The pre-registered
primary metric `approvals_per_landed_pr` and guardrail
`wrongly_batched_or_spawned_rate` (`docs/issue-659/proposals/product-discovery.md`,
"Pre-registered hypothesis package" section) require (a) a rolling window of
the next 20 PRs landed after both gates shipped, and (b) at least one
gate-produced audit record to compute the guardrail against actual landed
traffic. Neither condition is met:

- derived: `gh pr list --state merged --search "merged:>=2026-08-11T02:26:44Z" --json number --jq length`
  ```
  10
  ```
  Fewer than the required 20-PR window have landed since PR #712's merge
  (`mergedAt: 2026-08-11T02:26:44Z`, from `gh pr view 712 --json mergedAt`).
- derived: `find docs -path "*/decisions/batch-*" -o -path "*/decisions/spawn-refusal-*"`
  ```
  (no output — no matching files)
  ```
  Neither `impact-guard.sh`'s `batch-<ts>.md` audit path nor
  `plan-order-guard.sh`'s `spawn-refusal-<ts>.md` audit path
  (`docs/issue-659/reports/implementation.md`, "What was done") has fired on
  real traffic — zero gate-produced audit records exist repo-wide.

Per the issue's own Acceptance clause ("deferred-with-reason if the window is
unfilled", `gh issue view 659` body) and this role's own proposal
(`docs/issue-659/proposals/execution-observation.md`, "outcome" bullet), the
correct outcome-level verdict at this window state is
effect-not-demonstrated / deferred-with-reason — recording a ratio from a
half-filled, gate-silent window would be a fabricated effect, which the
approved proposal and the issue's Acceptance clause both explicitly forbid.

Recomputed per the spec's rule (worst case among cited step-level results,
`roles/specs/execution-observation.spec.json`'s recomputation rule): the
step-level results below are all `present`, so outcome is bounded above by
pass, but is reported as deferred because the metric itself cannot yet be
computed from the two derived counts above, not because a step-level result
failed.

## Verdict — trajectory

**sound.** Implementation's phase-1→phase-2 path followed contract v3 s19:

- Proposal `docs/issue-659/proposals/implementation.md` was written and
  approved before code: the issue comment thread shows
  `APPROVE issue-659/architecture` preceding
  `APPROVE issue-659/implementation` (`gh issue view 659 --comments`, read
  this session), and PR #712's first commit trailer reads `Proposal:
  docs/issue-659/proposals/implementation.md` / `Subject: issue-659`
  (`gh pr view 712 --json commits`, commit `b2d913e`).
- A PR-review `FEEDBACK issue-659/implementation` comment (`gh issue view 659
  --comments`: "gates/test_generated_paths.py fails... register both scripts
  in this PR") preceded the second commit `ade05a1`, whose message body
  states it fixes exactly that feedback
  (`gh pr view 712 --json commits`, commit `ade05a1` messageBody) — the
  human-feedback loop was honored, not bypassed.
- A before-landing warrant hunt ran and found a real defect (dead-code
  `--step` regex against `spawn.py`'s actual CLI shape), fixed in the same
  session before landing (`docs/issue-659/reports/implementation.md`, "What
  did not work" section; commit `b2d913e` messageBody corroborates: "A
  before-landing warrant hunt found the first plan-order-guard.sh draft
  matched a non-existent --step flag... fixed to resolve role -> plan step
  instead, before landing").
- Implementation's own record frontmatter states `loop_state: landed`,
  `verdict: pass` (`docs/issue-659/reports/implementation.md`), a terminal
  state consistent with the PR having merged (`gh pr view 712 --json
  mergedAt`: `2026-08-11T02:26:44Z`).

## Verdict — step

Per-claim, in the spec's vocabulary (subject / test / result / assertedBy —
assertedBy: execution-observation, this role, citing itself):

- subject: `gates/risk_report.py` line 321 (`batch_eligible_groups`, Axis 1).
  test: Acceptance fixture coverage for overlap/non-overlap grouping.
  result: present. Evidence: `gates/test_batch_eligible_groups.py` added at
  PR #712 (`gh pr view 712 --json files`: 67 additions), and
  implementation's own record's "Test run" section
  (`docs/issue-659/reports/implementation.md`) quotes a passing run for this
  file under its own code fence, not re-derived by this session.
- subject: `gates/flows.py` line 134 (`plan_order_blocked`, Axis 2). test:
  Acceptance fixture coverage for premature-sequential-refused /
  parallel-allowed / no-dependency-empty-state. result: present. Evidence:
  `gates/test_plan_order_blocked.py` added at PR #712 (68 additions, `gh pr
  view 712 --json files`), with implementation's own record's "Test run"
  code fence (`docs/issue-659/reports/implementation.md`) as the count
  source.
- subject: `on-the-record/hooks/plan-order-guard.sh` (Axis 2 enforcement
  point). test: whether the hook's command-matching regex actually matches
  `spawn.py`'s real CLI shape. result: present, deficiency-then-fixed within
  the same PR (not an open deficiency at merge time). Evidence:
  `docs/issue-659/reports/implementation.md`, "What did not work" — impact,
  timeline, root cause, action item (blameless four-part shape, scaled to
  one finding), already present verbatim in implementation's own record and
  not repeated in full here to avoid duplicating admissible evidence; commit
  `b2d913e` messageBody confirms the fix landed before merge, not after.
- subject: `docs/specs/generated-paths.md`,
  `docs/specs/enforcement-boundary.md` (registration completeness gates
  #684/#441). test: whether `plan-order-guard.sh` and the unrelated
  pre-existing `session-role-bind.sh` (landed by #698, unregistered there)
  have completeness rows. result: present, via a post-merge-discovered,
  pre-merge-fixed correction — `gh pr view 712 --json files` shows both spec
  files modified in commit `ade05a1`, whose messageBody states the full
  suite passes, consistent with implementation's own closing "Test run"
  code fence (`docs/issue-659/reports/implementation.md`).
- subject: pre-registered effectiveness metric measurement (this issue's
  third Acceptance clause, `provenance: executed-live`). test: whether
  `approvals_per_landed_pr` / `wrongly_batched_or_spawned_rate` were
  measured over the required 20-PR post-ship window with a gate-fired audit
  trail. result: not-applicable, because the precondition data does not yet
  exist per the two `derived:` command outputs quoted above under "Verdict —
  outcome". This is not a deficiency in PR #712's artifacts; it is a
  state-of-the-world gap the issue's own Acceptance clause anticipated and
  named an explicit deferred branch for.

No deficiency finding is open against PR #712's landed artifacts: the one
defect this session's evidence surfaces (`plan-order-guard.sh`'s original
`--step` regex) was found and fixed by implementation's own before-landing
warrant hunt inside the same PR, not left open — so no new finding is filed
here per this role's own out-of-scope clause
(`docs/issue-659/proposals/execution-observation.md`, "Out of scope").

## Open findings

None. The outcome-level metric is deferred (not a finding against the
artifact) pending the 20-PR window and a gate-fired audit record, both
absent per the `derived:` outputs quoted above. Re-observation should re-run
the two `derived:` commands above once the window fills; no code or record
change is required of this role until then.

## Next steps

Re-run this observation once `gh pr list --state merged --search
"merged:>=2026-08-11T02:26:44Z" --json number --jq length` reaches 20 and at
least one `docs/issue-<n>/decisions/batch-*.md` or
`spawn-refusal-*.md` file exists, to compute the actual
`approvals_per_landed_pr` and `wrongly_batched_or_spawned_rate` values against
the pre-registered threshold (`≤0.7`, `0%` respectively).

## Resolution path

No open finding requires resolution. The outcome-level deferral resolves
itself once the pre-registered window and audit-record precondition are met;
no action item is owed by any role in the interim.
