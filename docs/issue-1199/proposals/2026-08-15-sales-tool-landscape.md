Status: phase-1 proposal, executed under phase-2 authorization — see
Adoption rationale. Subject: issue-1199. Part of #1199.

## Scope

Built against `docs/issue-1199/reports/sales/survey.md` and
`docs/issue-1199/reports/sales/scout-brief.md`.

## Guiding principle

Fold the design moves the surveyed Claude Code sales-skill repos ship
— evidence-tied field values, buying-committee-scoped named contacts,
cross-deal objection-pattern tracking — natively into the sales
rulebook's existing methodology docs as this role's own judgment, per
the operator's 2026-08-13 native-application amendment: no tool
attribution or catalog section in the rulebook text itself.

## Per-item breakdown

1. **Evidence-tied qualification values** — `sales-qualification-
   meddpicc/README.md` gains a rule: a field's captured value should
   name the observable signal it rests on (a filing, a public pricing
   page, a stated timeline) rather than stand as a bare label, mirroring
   how "TBD"/"unknown" already requires an explicit marker instead of
   a silent blank.
2. **Buying-committee-scoped named contacts** — same README: the
   existing "Economic Buyer and Champion must be named individuals"
   rule gains a clause that the named individual is placed in the
   context of the deal's other identified buying-committee members
   (who else has influence/access), not recorded as an isolated name.
3. **Cross-deal objection-pattern tracking** — `sales-playbook/
   README.md`'s objection-handling section description gains a rule
   that recurring objections are tracked as a named pattern across
   deals (frequency, which stage they recur at) rather than restated
   fresh per deal.

Target shape (non-final, phase-2 wording TBD): one added paragraph per
README under the existing "Semantic check" or methodology-description
prose, no new heading structure, no gate-code change (these are
judgment/methodology additions, not new mechanically-enforced checks).

## Adoption rationale

Sourced from `docs/issue-1199/reports/sales/scout-brief.md`'s two
surveyed repos (`zubair-trabzada/ai-sales-team-claude`, 1039 stars;
`louisblythe/Sales-Skills`, 116 stars) — see that file for per-item
source citations.

Per the `APPROVE issue-1199/sales` comment already posted on this issue
(canonical: `gh issue view 1199 --json comments`, read this session —
author `JiwonJung94`, an approvers.md account per `docs/specs/
approvers.md`, posted before this session started), phase 2 is already
authorized in single-account mode; this session executes phase 1 and
phase 2 together in one delivery, following the `conformance-review`
role's precedent for this issue (`docs/issue-1199/reports/
conformance-review.md`, its "2026-08-14 plugin-ecosystem rework"
section, read this session).

## Plugin-reflection plan

Applied directly in the same delivery (see `docs/issue-1199/reports/
sales.md`): the two named README.md files in
`tokenmaxxxer/sales-rulebook` are edited on branch `issue-1199/sales`
in that separate repo, no other file touched.
