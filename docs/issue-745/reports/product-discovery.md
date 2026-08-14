---
kind: hypothesis-testing
loop_state: inconclusive
---

# issue #745 — phase 2 record: precondition check on the operator's deferral decision

## Summary of work

This record checks whether the operator's 2026-08-11 decision — hold Item 1 (thinking budget) and Item 3 (`execution-observation` conditioning) until Item 2's (record-section tiering) pre-registered measurement window has run once — can now be evaluated, on APPROVE re-entry into phase 2.

It cannot. Item 2's execution issue (#760) landed only its phase-1 proposal (PR #778, merged) and was then closed without ever landing a phase-2 hook implementation:

```
$ gh issue view 760 --json state -q .state
CLOSED
$ find . -iname "*record-tiering*"
(no output)
```

No `record-tiering-directive.sh` or `record-tiering-guard.sh` exists anywhere in the working tree. The mechanism the pre-registered `boilerplate_output_token_share` metric depends on was never built, so the measurement window the operator's decision named as the gate for Items 1 and 3 (derived: `docs/issue-745/proposals/product-discovery.md`'s own Item 2 pre-registered package states the window as "the next 20 records written under the tiered format" — quoted verbatim from that already-landed proposal, not recomputed here) has zero records to measure against. `#760`'s own closure looks like the same premature-`Closes`-on-phase-1-merge defect the operator's own decision comment already named for this issue's history (`#741`'s fix, PR #756) — a phase-1-only PR merged and closed the issue before phase 2 opened.

No candidate is promoted, killed, or re-scored here. This record exists to state the precondition failure plainly rather than silently letting Items 1 and 3 stay held against a window that isn't running.

## Why

The role-handoff contract requires this record to check, mechanically, whether a pre-registered decision rule's inputs are actually available before applying it. The operator's held-items decision was itself conditional on Item 2's measurement window running; checking that condition before either re-opening Items 1 and 3 or reporting the issue quiet is this phase-2 turn's job.

## Upstream basis

- `docs/issue-745/proposals/product-discovery.md` (this issue's own phase-1 proposal, landed 2026-08-11)
- `docs/issue-745/reports/product-discovery/current-state.md`
- issue #745's own comment thread (operator decision comment, 2026-08-11) and priority-record close-out comment (2026-08-12)
- issue #760 / PR #778 (Item 2's execution issue, phase-1-only, closed)
- `docs/issue-476/decisions/2026-08-08-h1-h2-mechanism-adr.md` (cited precedent for the premature-closure failure mode)

## Where this sits on the opportunity-solution tree

- **Outcome**: unchanged from the phase-1 proposal — spend on judgment quality, auditability, and self-report trust priced and auditable rather than cut blindly.
- **Opportunity**: unchanged — no mechanism yet separates spend that bought the named good from spend that didn't, for any of the three items.
- **Candidate solutions**: none pruned or promoted this turn. Item 2's candidate (citation-informed section tiering) is neither validated nor invalidated — its trial never started running. Items 1 and 3 remain exactly where the operator left them: held.
- **Discriminating assumption test**: still open, and now blocked on a prerequisite the tree did not previously know was missing — Item 2's mechanism has to actually ship and accumulate its pre-registered sample of tiered records before its own test, let alone the deferred Items 1 and 3 decision, can run.

## Problem statement

The operator needs to know whether the precondition it set for reconsidering Items 1 and 3 — "after Item 2's measurement window has run once" — has been met, before either item can be picked up.

## Target market / market size rationale / competitive alternatives / differentiator / timing rationale / go-to-market plan / critical success factors

Not applicable in the literal go-to-market sense this role-spec's field set assumes: the "market" here is this repo's own set of role-session branches, priced in $/session rather than sold. Restated in that frame — target market: this repo's own future issue×role sessions across all product-discovery-gated issues; market size rationale: bounded by this repo's own session cadence (no external cadence log exists, per the phase-1 proposal's own noted limit); competitive alternatives: the status-quo (no tiering, no budget conditioning, unconditioned `execution-observation`) already scored against each candidate in the phase-1 proposal's RICE tables; differentiator: a pre-registered, guardrail-backed metric per candidate instead of an ungrounded cut; timing rationale: Item 2 was chosen first because it doesn't touch judgment quality; go-to-market plan: whichever role and issue the operator assigns each held item to next, per the phase-1 proposal's ITWWS section; critical success factors: Item 2's mechanism actually shipping and accumulating a real post-tiering sample — the one factor this record finds unmet.

## Hypothesis statement

If Item 2's tiering mechanism ships and accumulates its pre-registered post-tiering sample, `boilerplate_output_token_share` will fall relative to baseline by the margin already fixed in `docs/issue-745/proposals/product-discovery.md` while `cross_issue_citation_rate` stays within its guardrail tolerance per category — and only then should the operator revisit Items 1 and 3, per its own 2026-08-11 decision.

## Fail condition / time box / decision rule

- **Fail condition**: at re-entry, the post-tiering window has not accumulated (because the mechanism never shipped) — met this turn.
- **Time box**: none was set on when the precondition check itself must resolve; this record closes that gap by checking now, on the first phase-2 re-entry after the operator's decision.
- **Decision rule**: if the precondition is met (mechanism shipped, sample accumulated per the proposal's own pre-registered size) → proceed to actually measure `boilerplate_output_token_share` and `cross_issue_citation_rate` against the pre-registered thresholds. If the precondition is unmet (this turn's finding) → **inconclusive** on the held-items question; do not evaluate Items 1 and 3, and flag the broken precondition instead of silently re-holding.

## Success metric

Not directly measurable this turn — the metric this record was checking for (`boilerplate_output_token_share`, `cross_issue_citation_rate`) has no post-tiering data to compute against, because the tiering mechanism was never built.

## Guardrail status at measurement

Not applicable this turn: no measurement window ran, so no guardrail reading exists to state. This is itself the finding — a guardrail with nothing to measure is not evidence the guardrail passed.

## Evidence log

- `docs/issue-745/proposals/product-discovery.md`
- `docs/issue-745/reports/product-discovery/current-state.md`
- issue #745 comment thread (operator decision, 2026-08-11; priority-record close-out, 2026-08-12)
- issue #760 (`gh issue view 760 --json state -q .state` → `CLOSED`)
- PR #778 (`gh pr view 778` → phase-1-only body, `mergedAt` set, `Closes #760` in a phase-1-only PR body — same defect shape as `#741`)
- working-tree search for the tiering mechanism (`find . -iname "*record-tiering*"` → no output)

## Recommendation

no-go on evaluating Items 1 and 3 this turn — not on any of the three candidates themselves. The operator's own precondition is unmet. The actionable next step is not a candidate pick; it is getting Item 2's phase-2 hook implementation actually landed.

## Verdict

**inconclusive** — the pre-registered decision rule for reconsidering Items 1 and 3 cannot yet be applied, because its input (Item 2's post-tiering measurement window) never started: the mechanism it depends on was never built before its execution issue was closed.

## Confidence level

High confidence in the finding itself (directly checked: issue state, PR body, working-tree search for the mechanism file). No confidence claim is made about what Item 2's eventual measurement would show, since it hasn't run.

## Open findings

- Item 2's execution issue (#760) was closed with only its phase-1 proposal landed — the same premature-closure shape `#741` fixed for this issue's own history, recurring on a different issue. Whether `#741`'s fix (PR #756, on `main`) should have prevented this, or whether `#760`'s session predates that fix reaching its plugin clone (the same clone-lag caveat the operator's own 2026-08-11 decision comment names), is unresolved here — it needs a targeted check of `#760`'s session timestamp against `#756`'s landing timestamp, which this turn does not do.
- Items 1 and 3 remain held with no active blocker being worked — until #760 (or a re-filed successor issue) actually lands the tiering hook and accumulates the measurement window, this issue has no path to its own resolution.

## Next steps

1. Operator or an assigned session re-files or reopens #760's phase-2 (hook implementation) so Item 2's mechanism actually ships.
2. Once the pre-registered post-tiering sample exists, re-run this precondition check: compute `boilerplate_output_token_share` and `cross_issue_citation_rate` against the pre-registered thresholds in `docs/issue-745/proposals/product-discovery.md`.
3. Only after that measurement resolves (persist/pivot/kill for Item 2) does this issue's own held-items question (Items 1 and 3) become answerable.

## Resolution path

Re-entry into this same phase-2 record on the next APPROVE, once #760's phase-2 has landed and the measurement window has accumulated — at that point the loop_state moves from `inconclusive` to `measuring` (Item 2's own trial) and, downstream, back to a fresh decision point for Items 1 and 3.

## ITWWS carried forward

Unchanged from the phase-1 proposal's own ITWWS section — none of the three items' follow-ups are actioned this turn; all remain deferred to whichever role and issue the operator assigns next, now additionally gated on #760's phase-2 actually landing.
