---
status: approved
files:
  - docs/issue-1199/reports/finance-unit-economics.md
---

# issue-1199 (finance-unit-economics): tool-landscape fold-in

kind: proposal
subject: issue-1199

## Request

Issue #1199 (northpole req#1) asks every role to survey the tools its
domain's practitioners actually use, distill each tool's design move
with adoption evidence, and fold that judgment natively into the
rulebook. Two binding amendments apply: (a) apply-not-reference — the
same delivery must edit the named upgrade target files, not only point
at them; (b) native application — absorbed rules read as this role's
own judgment, no tool/repo names or `source: <url>` framing inside the
public rulebook; the survey/adoption-evidence trail stays only in this
on-the-record record. This proposal covers the finance-unit-economics
unit.

## Survey summary

canonical: docs/issue-1199/reports/finance-unit-economics/survey.md
`tokenmaxxxer/finance-unit-economics-rulebook` carries five
`playbook/*.md` decision-axis files, each sourced from #1174's
practitioner/methodology/academic research layers only — none reflects
practitioner tooling. That is the gap this fold-in targets.

## Scout summary

canonical: docs/issue-1199/reports/finance-unit-economics/scout-brief.md
One research agent ran four search angles (SaaS metrics/subscription
platforms, FP&A modeling tools, cohort-LTV analytics tooling, SaaS
benchmark/valuation sources), one sweep stage, saturation at judge point
1. Findings mapped to six gaps in the existing five axes: margin-
adjusted/time-window-normalized LTV input; joint payback+margin+burn-
multiple health check; economic-substance churn/acquisition-event
definitions; shared single-definition variables across dependent
outputs; benchmark citations carrying distribution position and period.

## Mandate chain

Each of the five new rules is sourced from the scout brief's fetched
tooling-practice evidence (e.g. https://baremetrics.com/academy/saas-calculating-ltv
and the other URLs listed in docs/issue-1199/reports/finance-unit-economics/scout-brief.md)
and is therefore necessary to this role's own mandate, 단위경제상
성립하는가 (does the unit economics hold up): a CAC payback verdict
checked jointly against margin/burn multiple, an LTV input that is
margin-adjusted and cohort/channel-segmented, and a benchmark citation
that states its distribution position are each a more accurate test of
whether the unit economics genuinely holds → each rule tightens, rather
than loosens, this role's own sustainability judgment.

## Adopted norms

One new native rule appended to each of the five existing axis files
(no new sixth file — a standalone tool-landscape file is ruled out by
the native-application amendment), matching each file's existing rule
shape (numbered rule + rationale + counter-example), phrased with no
tool/repo attribution:

1. `playbook/cac-payback.md` rule 7 — judge payback jointly with gross
   margin and burn multiple before calling unit economics healthy.
2. `playbook/churn-assumption.md` rule 6 — define churn/acquisition
   events by economic substance (paid-period end, true first
   acquisition), not user-initiated action.
3. `playbook/ltv-cac-band.md` rule 7 — require the LTV input itself to
   be margin-adjusted and normalized to a fixed time-window since
   acquisition, computed per cohort/channel before blending.
4. `playbook/sensitivity-scenario.md` rule 6 — define a variable feeding
   more than one output once, named, and reference that single
   definition everywhere it is used.
5. `playbook/evidence-chain.md` rule 6 — require a cited benchmark to
   state its distribution position and measurement period, and flag a
   carried-forward input as stale once actuals diverge materially from
   the plan it came from.

## Rationale

- Apply-not-reference (issue amendment, 2026-08-13): all five named
  upgrade targets are edited in the same phase-2 delivery.
- Native application, no attribution (issue amendment, 2026-08-13): no
  rule text names a tool or carries a `source:` URL; each rule is
  phrased as this role's own decision judgment, matching the shape of
  the five files' existing rules (rule + rationale + counter-example)
  minus the source line — the surveyed-tool evidence trail lives only
  in this on-the-record record, never in the rulebook.
- No verbatim copying: every rule is paraphrased synthesis, not quoted
  tool documentation.

## Phase-2 reflection plan

`produces`: "five native playbook-rule additions (one per axis file) +
this on-the-record phase-2 record, no new marketplace-spec fields."
`REQUIRED_FIELDS`: unchanged from the existing spec (`metric_name`,
`value`, `period`) — this fold-in adds decision-rule prose to
`playbook/*.md`, not a new record-producing field, so no
`finance-unit-economics.spec.json` field is added or removed. Gate
logic phase 2 executes: none of the five `finance-*` gates change; only
`playbook/*.md` prose is edited in the rulebook repo, verified by eye
against each file's existing rule shape (numbered rule + rationale +
counter-example), the same review mode brand-design's landed fold-in
used for its methodology-handbook edits.

## Decision requested

Approve this proposal so phase 2 can add the five native rules listed
under "Adopted norms" to the rulebook repo and land this record.

## Out of scope

- No gate-logic changes (the five `finance-*` plugin hooks/gates are
  untouched).
- No new sixth playbook file or standalone tool-catalog section.
- No changes to `docs/handbooks/finance-unit-economics/methodology.md`
  — the fold-in targets the five playbook axis files, which are this
  role's own operating-content home for decision judgment (parallel to
  brand-design's methodology.md target, since that role's tool-derived
  judgment lives in its methodology handbook rather than per-axis
  playbook files).

## Acceptance

- Each of the five `playbook/*.md` files carries exactly one new
  numbered rule, in the existing shape, with no tool/repo attribution.
- This record and the linked rulebook-repo PR are both submitted.
