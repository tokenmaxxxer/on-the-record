# Current-state survey — issue #659: batch-eligibility + sequential-dependency gating

## Background / context

Confirmed by inspection, not assumed:

- `gates/risk_report.py` (function `_role_write_scopes`) already reads every `roles/*.json`'s
  `write_scope` glob list keyed by role name; `_glob_matches` (fnmatch, with a `**`-prefix segment
  fallback) is the one overlap-detection primitive this repo already uses for write-set comparison
  (`blast_radius_grade`, `propagation_grade`). This is the "#573/#587 write_scope resolution" the
  issue names — it is real, deployed code, not a proposal. It currently answers "which roles' write
  scopes does this path-set touch" for a single proposal's own `files:` list plus `other_proposals`
  passed in by the caller; nothing today calls it pairwise across a set of *pending delivering
  PRs* to produce a batch grouping.
- `docs/issue-609/reports/product-discovery/current-state.md` (merged, its Background section)
  confirms #573 (two-axis AND gate, axis-owning role approval authority, four-field audit record)
  and #587 (execution-observation/remediation on the same routing) are both merged and in deployed
  use for **approval acts** — decisions already proposed for approve/reject. Neither touches
  batching a *set* of pending PRs, and neither touches ordering/dependency between steps.
- `gates/flows.py` (function `_plan_from_body`, issue #189, fixed by #197) is the real, deployed
  parser for an issue body's `## 실행 계획` block. It returns `[{step: int, roles: [...], done:
  bool}, ...]`, splitting roles within one step line on `‖` (parallel roles, same step). Step
  numbers are positional/sequential in the list but **nothing today reads `done` across steps to
  refuse spawning step N+1 while step N is `done: false`** — grep of `gates/flows.py` for callers
  of `_plan_from_body` shows it feeds PR/step/role tracking logic only, not a spawn/merge gate.
- No hits anywhere in `docs/`, `gates/`, `roles/`, `on-the-record/` for "batch-approv", "batch
  eligib", or "delivering PR" as a defined term — this is genuinely new ground, not a rename of an
  existing mechanism.
- `docs/issue-573/proposals/product-discovery.md` (merged, phase 1) already establishes the
  precedent this issue explicitly asks to extend: axis-owning role authority, contradiction-only
  auto-reject, four-field re-derivable audit record, guardrail metric distinct from the primary
  metric. Issue #659 names #573 reaching real operation as the deeper structural fix and frames
  itself as the throughput-side complement — batching raises the ceiling on how much a single
  approver clears per unit time; it does not remove the single-approver bottleneck #573 targets.
- Issue #476 (open, "anti-theater"): forbids an orchestrator's own unrecorded reasoning standing in
  for a mechanically re-derivable judgment. The issue's own framing of Axis 1 ("orchestrator
  eyeballing 'no file overlap'") is explicitly this failure mode, one level up from #573's original
  approval-act framing (there: approve/reject; here: batch/no-batch).

## Problem, stated without the proposed solution (JTBD)

- **Job performer**: the human operator who is the sole approver across all pending delivering PRs
  and phase-decisions, and the orchestrator session that currently decides — by unrecorded eyeball
  judgment — which of those PRs it presents together as a batch and which step it lets itself
  spawn next.
- **Job**: know, for a queue of pending delivering PRs and an issue's declared execution-plan order,
  exactly which subset is safe to approve/merge together and exactly which next step is safe to
  spawn — without either party inventing that judgment fresh each time from memory of past
  conflicts (e.g. the #178 rebase conflict) or hand-eyeballing file lists.
- **Circumstance**: 20+ issues/day × 2 phase-decisions each = 40+ approvals/day funnel through one
  human, with 12 PRs queued at the point of self-diagnosis. The orchestrator already has two
  correct instincts — batch what doesn't overlap, refuse to parallelize what has a real prerequisite
  — but both instincts live only in orchestrator working memory: unrecorded, not re-derivable, and
  exactly the shape #476 already named as a failure mode when applied to approval acts. The
  machinery to make both instincts mechanical already exists in adjacent form (`_role_write_scopes`/
  `_glob_matches` for write-set overlap; `_plan_from_body`'s parsed step/role/done structure for
  declared order) but nothing wires either one to a batch/spawn decision today.
- **Desired outcome**: a batch-approvable set over pending delivering PRs is computed mechanically
  from write-set non-overlap and surfaced with a recorded, re-derivable basis (which PRs, which
  overlapping paths or roles ruled others out), so the orchestrator relays a computed answer instead
  of asserting one; and a step whose declared prerequisite step has not landed (`done: false`)
  is refused for concurrent spawn/merge, read directly from the issue body's already-existing
  `## 실행 계획` syntax, never from the orchestrator's memory of which issues conflicted before.

## Where this sits on the opportunity-solution tree

- **Outcome**: operator approval throughput rises (fewer round-trips, more decisions batched per
  approval act) without an increase in wrongly-batched or wrongly-parallelized outcomes — the same
  shape #573's own guardrail (`auto_decision_reversal_rate`) already established for approval-act
  auto-decisions, moved one level up to batching/spawn decisions.
- **Opportunity**: #573/#587/#586 built axis-ownership routing and the approval-act gate, but
  scoped it to a single decision's approve/reject; nothing in that machinery groups *multiple*
  pending decisions into a batch or reads an issue's *own declared step order* to gate concurrent
  spawn. Both gaps are currently filled by orchestrator eyeballing — the same unrecorded-reasoning
  failure mode #573 closed for approval acts, now open at the batch/spawn layer instead.
- **Candidate solutions**: scored in the proposal — (a) reuse `_role_write_scopes`/`_glob_matches`
  directly on each pending PR's own changed-file set (not role write_scope) to compute pairwise
  non-overlap and produce connected-component batches; (b) a new gate reading `_plan_from_body`'s
  parsed step list to refuse spawn/merge of any step whose prerequisite step is not `done: true`,
  treating `‖`-joined roles within one step as the only concurrency the plan itself licenses; (c)
  whether these are one gate or two independent ones (mirrors #573's own rejected "single combined
  judge" candidate — kept independent here for the same reason: two orthogonal mechanical signals,
  neither should paper over the other's refusal).
- **Discriminating assumption test**: whether a pending PR's own write-set (the files it actually
  changed, e.g. via `gh pr diff --name-only`) can be compared for overlap using the exact same
  `_glob_matches` primitive already validated for role write_scope comparison, without inventing a
  second overlap-detection routine — this is what the proposal's pre-registered hypothesis targets,
  and it is the discriminating test because a "yes" means Axis 1 is pure reuse (matches the issue's
  explicit instruction to extend, never parallel-invent) while a "no" would mean a genuinely new
  comparison primitive is needed, which the issue does not ask for.

## Degradation, stated explicitly

Today, batch grouping and spawn/merge ordering across pending delivering PRs happen exclusively by
orchestrator judgment, with no mechanical check and no audit record of the basis. Until Axis 1's
gate ships, every batch decision is orchestrator-asserted, unrecorded, and unverifiable after the
fact. Until Axis 2's gate ships, every spawn/merge concurrency decision depends on the orchestrator
correctly recalling which prior issues had real prerequisites (e.g. #178/#181, #14/#12, #290) —
correct so far by observed diligence, not by any mechanism that would catch a future miss. Both
gaps degrade to the current, fully-manual state; neither axis's absence blocks any decision from
being made, only from being made mechanically and re-derivably.
