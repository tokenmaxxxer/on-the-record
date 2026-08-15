---
subject: issue-1199
role: finance-unit-economics
kind: survey
---

# issue-1199 (finance-unit-economics): current-state survey

canonical: `find /home/jwjung/tokenmaxxxer/rulebooks/finance-unit-economics-rulebook -type f`, read this session.

`tokenmaxxxer/finance-unit-economics-rulebook` (mounted locally at
`/home/jwjung/tokenmaxxxer/rulebooks/finance-unit-economics-rulebook`)
carries five decision-axis files under `playbook/`, built during issue
#1174's research pass (2026-08-13):

- `playbook/ltv-cac-band.md` (6 rules) — LTV:CAC ratio to band verdict.
- `playbook/cac-payback.md` (6 rules) — payback months to threshold
  verdict.
- `playbook/churn-assumption.md` (5 rules) — which churn/retention
  figure feeds LTV.
- `playbook/sensitivity-scenario.md` (5 rules) — sensitivity/scenario
  section construction.
- `playbook/evidence-chain.md` (5 rules) — citation vs. assumption-label
  discipline.

Each rule already carries source citations from #1174's own
practitioner/methodology/academic research layers — none of that
research touched practitioner *tooling* (what SaaS-metrics, FP&A, or
cohort-analytics software actually does and why), which is the gap
issue #1199 targets. `docs/handbooks/finance-unit-economics/
methodology.md` in that repo covers the role's overall operating
procedure but likewise carries no tool-derived judgment.

canonical: `find /home/jwjung/tokenmaxxxer/rulebooks/finance-unit-economics-rulebook -path '*issue-1199*'`, run this session, zero results.
No `docs/issue-1199/**` tree exists yet in the rulebook repo — this is
the first issue-1199 delivery landing there for this role.
