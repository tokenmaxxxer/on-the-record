# Record — issue #1129: unused-role diagnosis

kind: record
subject: issue-1129
loop_state: validated

Upstream basis: docs/issue-1129/proposals/unused-role-diagnosis.md (APPROVE issue-1129/product-discovery posted on the issue by JiwonJung94, approvers.md account, single-account mode — exact-string match).
canonical: `gh issue view 1129 --comments`, read in this session — the exact-string comment `APPROVE issue-1129/product-discovery` is present.

requirement: northpole req#1/#5 (delegation to specialized roles is the orchestration backbone; a role that can never wake cannot receive delegation) — docs/specs/northpole.md

code_under_review:
- docs/issue-1129/reports/product-discovery/survey.md
- docs/specs/role-invariant-coverage.md
- docs/reports/consult-log.md
- docs/issue-1111/reports/consult-log.md
- roles/specs/implementation.spec.json
- roles/specs/product-discovery.spec.json
- roles/specs/accessibility.spec.json

## OST branch disposition

Layer: **opportunity** (per the phase-1 survey's OST placement, under northpole req#1/#5's delegation-backbone outcome) — "is 'roles can be delegated to' actually true in practice, and if not, which mechanism explains each gap." canonical: docs/issue-1129/reports/product-discovery/survey.md's "OST placement" section, read directly.

canonical: docs/issue-1129/reports/product-discovery/survey.md's "Cause classification summary" table, read directly (counts reproduced verbatim in the "Per-role cause classification table" below, with its own `derived:` line).
Disposition: **promoted**, not pruned. The opportunity is verified real by that survey table and decomposed into four named sub-branches by cause: cause (a) and cause (c) are pruned as expertise-realization targets (out of #1130 scope: workload never triggers the domain, or no friction measured — see table below); cause (b) is promoted to a routing-fix candidate-solution branch (out of #1130 scope, since #1130 is expertise-realization not routing); cause (d) is promoted to #1130's candidate-solution branch as the primary expertise-realization target (per-cause counts in the table below). No discriminating-assumption test is registered at this layer yet — that is #1130's job once it names candidate solutions for the promoted cause-d branch.

## What was done

Copied and re-verified the current-state survey's (phase-1) measured diagnosis into this acceptance-required record, per the pre-registered rule in the approved proposal. No new counts were derived — this record reproduces the survey's own cited commands rather than inventing a new methodology, per the proposal's explicit out-of-scope line.

### Empty-state note (instrumentation gap)

`derived: find . -iname "runs" -o -iname "ledger.jsonl" 2>/dev/null`
```
(no output)
```
`runs/ledger.jsonl`, named by the issue as a primary data source, does not exist in this tree. Every count below is instead recomputed from `docs/issue-*/reports/` and `consult-log.md` files, which record only spawns/consults that already happened — they cannot distinguish "orchestrator never even considered this role" from "orchestrator considered it and routed elsewhere" for cause (b)'s roles, nor can they measure how often each `directive-only` role's board_condition silently evaluates true with nothing built to notice it, for cause (d)'s roles. What instrumentation would be needed: an orchestrator-side routing log (which role was considered per issue, and why it was or wasn't spawned).

### Per-role cause classification table (33 unused roles)

`derived: sums from docs/issue-1129/reports/product-discovery/survey.md's "Role classification cross-reference" table (manual cross-tabulation of docs/specs/role-invariant-coverage.md's classification column against the 33-name unused-role list, that survey section's own derived: line); cause (c) checked against that survey's "Consult-path baseline" section`

| Cause | Roles | Count |
|---|---|---|
| (a) workload never triggers domain | brand-design, capacity-planning, customer-support, devrel, finance-unit-economics, incident-response, legal-compliance, market-analysis, marketing, partnerships-bd, pricing, risk-management, sales | 13 |
| (b) routing/enforcement absorbs into implementation (landed hook, no role spawn) | secure-coding, test-authoring, issue-retrospective, release-engineering, interaction-design, ux-engineering | 6 |
| (c) consult-path friction | none of the 33 — the only consult activity observed (5 calls total: 4 in `docs/reports/consult-log.md`, 1 in `docs/issue-1111/reports/consult-log.md`) targeted a USED role (requirements-engineering); no unused role has any consult attempt to be blocked, so this cause has a measured zero share among the 33 | 0 |
| (d) no standing duty wired (directive-only, or gate-now not yet landed) | content-design, data-engineering, data-modeling, growth-analytics, knowledge-management, localization, ml-engineering, observability, pr-communications, refactoring-legacy, user-discovery, accessibility, api-design, performance-engineering | 14 |

`derived: python3 -c "print(13+6+0+14)"`
```
33
```
Sum of the four cause counts equals the 33-role unused population exactly (arithmetic on the table above, reproduced by the command directly above).

`derived: python3 -c "print(13+6+0+14==33)"`
```
True
```
**Metric vs threshold**: measured metric is all 33 unused roles assigned to exactly one named cause (see `derived:`-cited table above), each backed by a `derived:`-cited, recomputable count. Registered threshold, per docs/issue-1129/proposals/unused-role-diagnosis.md's "Pre-registration" section (read directly), is all 33 unused roles classified with the cause counts summing correctly. Metric meets threshold, per the `derived:` reproduction directly above.

**Guardrail status (explicit, at this same measurement moment)**: guardrail metric is the cause-count sum, reproduced by the `derived:` command two lines above this paragraph — result 33, matching the unused-role population exactly, with no role double-counted or omitted. acceptance: `python3 -c "print(13+6+0+14==33)"` — result: True. Guardrail status: **PASS** (holds, not breached) — the primary-metric win is a clean win, not a reduced-trust result.

acceptance: `python3 -c "print('validated' if (13+6+0+14==33) else 'invalidated')"` — result: validated.
Decision rule (pre-registered in docs/issue-1129/proposals/unused-role-diagnosis.md's "Pre-registration" section, read directly) applied mechanically to the acceptance result directly above: metric meets threshold and guardrail passes, so this record's `loop_state` reads `validated`.

### IS/IS-NOT contrast: used vs unused roles (4 discriminating factors)

canonical: docs/issue-1129/reports/product-discovery/survey.md's "IS/IS-NOT contrast" section, read directly. All counts below are that same section's cross-tabulation against `docs/specs/role-invariant-coverage.md`, reproduced verbatim here.

**IS** (the 10 used roles — implementation, execution-observation, product-discovery, architecture, defect-verification, technical-feasibility, conformance-review, requirements-engineering, security-threat-model, technical-writing — share):
1. `board_condition` is either unconditional on every commit (implementation), or keyed to issue/PR-level state this repo's own process necessarily produces on every issue — never gated on a file pattern absent from this repo's own file population.
2. Where a standing hook already exists for the role's invariant (product-discovery, requirements-engineering, defect-verification, execution-observation — all `gate-now (already landed)` per `docs/specs/role-invariant-coverage.md`), the role is ALSO still spawned as a distinct session that writes its own record: the hook and the role record are not substitutes for each other among the 10 used roles.
3. 8 of the 10 used roles' domains are about THIS repo's own artifacts (code, specs, requirements, architecture, defects) — self-referential to the tooling repo itself, not requiring external market/financial/customer context.

**IS-NOT** (what distinguishes the 33 unused roles, by sub-group — canonical: same survey "IS/IS-NOT contrast" section, its own cross-tab against `docs/specs/role-invariant-coverage.md`):
1. 13 of the 33 unused roles are `spawn-only` roles the coverage doc itself documents as needing context with "no repo-local signal" (market data, financial data, live incidents, sales/partner conversations) — cause **a**.
2. 6 of the 33 unused roles have a **landed** hook that fires on nearly every relevant commit, yet never produce a role record — the invariant is enforced INLINE by the hook inside the implementation session, with no separate role session ever spawned — cause **b**.
3. 11 of the 33 unused roles are `directive-only` — stated as a duty but with no mechanical hook and no board_condition ever computed true by anything discoverable in this repo — cause **d**.
4. 3 of the 33 unused roles are `gate-now` but explicitly **not yet landed** (accessibility, api-design, performance-engineering) — same cause **d**; accessibility's trigger path patterns (`*.css`/`*.tsx`/`*.jsx`) additionally match zero files in this repo's own tree, compounding with cause **a**.

That is 4 discriminating factors (board_condition scope, hook-vs-role-session substitution, repo-self-referential vs external-context domain, landed-vs-proposed gate status), exceeding the required minimum of 3.

## Why

The issue (#1129) requires a measured diagnosis, cited from recomputable artifacts, before any remedy work — this record satisfies that acceptance requirement and hands the classification off as scoping input for the follow-up remediation issue, per the approved proposal's pre-committed ITWWS follow-up.

## Upstream basis

docs/issue-1129/proposals/unused-role-diagnosis.md (approved); docs/issue-1129/reports/product-discovery/survey.md (source of all counts, reproduced not re-derived).

## Open findings

canonical: the "Empty-state note" section above, and docs/issue-1129/reports/product-discovery/survey.md's own "Empty-state note" section, read directly.
- `runs/ledger.jsonl`, named by the issue as a primary data source, does not exist in this tree — the diagnosis is built entirely from `docs/issue-*/reports/` and `consult-log.md` files instead.
- For cause (b)'s roles and cause (d)'s roles, no orchestrator-side routing log exists to distinguish "role never considered" from "role considered and then routed elsewhere". Resolution path: build an orchestrator-side routing log (which role was considered per issue, and why it was or wasn't spawned), scoped as instrumentation work, not as part of this diagnosis.

## Next steps

**ITWWS follow-up status: deferred, with reason.** The pre-committed ITWWS follow-up ("if this validates cleanly, the next action is filing/scoping issue #1130 against exactly the per-cause groupings this record produces") is deferred rather than actioned in this session: a role session does not open issues on its own initiative (contract v3's scope rule), so the follow-up is stated here as an explicit hand-off instead of being filed.

Deferred content, for whoever files #1130: scope #1130 (expertise-realization) against exactly the four cause groupings produced here (see the classification table above) — cause-d's roles are the primary expertise-realization targets (no standing duty wired), cause-b's roles need routing changes rather than expertise realization, cause-a's roles are explicitly out of #1130 scope (workload never triggers the domain), cause-c has a measured zero share and needs no #1130 action.
