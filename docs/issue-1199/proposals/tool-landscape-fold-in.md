---
status: approved
files:
  - /home/jwjung/tokenmaxxxer/rulebooks/partnerships-bd-rulebook/partnerships-bd/reference/deliverable-shapes.md
---

Strategic-fit/ICP-overlap statement: this fold-in is ICP-neutral for
partnerships-bd itself — the "partner" here is this role's own tooling
maturity, so the fit test is whether the upgrade sharpens the role's own
deliverable shape, not whether an external counterpart fits an ICP.
Compounding-value statement: each upgrade attaches to a rule the role
already re-derives on every deal, so the gain (sharper partner-tiering,
named approval routing, explicit cure-period/data-IP split) compounds
across every future record rather than being a one-time fix.

Stage: binding-terms-ready (issue's own APPROVE token already posted:
`APPROVE issue-1199/partnerships-bd`, issue comment, `JiwonJung94`,
approvers.md account).

## Six-axis scoring (applied to this proposal's own fold-in work)

- strategic/ICP fit: weight 2, score 5 — directly sharpens this role's
  own fit-scoring rule; self-referential but load-bearing.
- financial health: weight 1, score 5 — zero external cost, doc-only
  change in an internal-tooling repo.
- legal/compliance posture: weight 1, score 5 — no attribution/licensing
  exposure; tool names stay out of the public rulebook per this issue's
  explicit constraint.
- operational capability: weight 2, score 5 — three bounded clause
  additions to one already-existing file, no new gate, no new section.
- cultural fit: weight 1, score 5 — matches this role's existing
  BATNA/ZOPA and evidence-discipline conventions already in the repo.
- compounding-value: weight 3, score 5 — every future partnerships-bd
  record re-derives these three fields; the sharpening compounds instead
  of being a one-off fix.

Intent: fold three practitioner tool-landscape learnings — (1) PRM
partner tiering, (2) deal-desk approval-routing-as-a-design-decision,
(3) CLM termination-clause granularity — natively into the role's own
deliverable-shapes.md, upgrading three existing sub-fields rather than
adding a tool catalog. Full evidence trail (per this issue's rule that
the public rulebook carries no tool attributions) is in
`docs/issue-1199/reports/partnerships-bd/scout-brief.md` and
`docs/issue-1199/reports/partnerships-bd.md`.

Sources:
- [PRM partner-tiering claim (1)](https://www.introw.io/blog/best-partner-relationship-management-software)
- [Deal-desk approval-routing claim (2)](https://www.heyiris.ai/blog/top-9-deal-desk-software-solutions-to-boost-revenue)
- [CLM/deal-desk vendor-overlap claim (3)](https://dealhub.io/glossary/deal-desk/)

Constraints: no tool name appears in the rulebook repo; no new gate
script (the three axis/section names are fixed elsewhere and out of
scope); bounded — three added sentences/clauses, not a new section.

What will be done: edit
`partnerships-bd/reference/deliverable-shapes.md` in the
`partnerships-bd-rulebook` repo — (1) deal-structure-verdict's
strategic/ICP-fit axis gains a partner-tier-naming requirement; (2)
term-sheet-outline section 4 (governance) gains a named-approval-
routing-surface requirement; (3) section 7 (exit/termination) gains an
explicit cure-period + data/IP-handling-split requirement. Commit on
`issue-1199/partnerships-bd` in that repo, push, open PR.

Out of scope: `multi-axis-scoring/reference/axes.md`'s six fixed axis
names (gate-script-bound, not this issue's surface); any gate-script
change; any tool-attribution content in the rulebook.

How you will know it worked: `deliverable-shapes.md` diff shows the
three additions; `tests/run-gate-tests.sh` in the rulebook repo still
passes 20/20 (unaffected — doc-only change, no gate logic touched); the
rulebook branch is pushed to origin and a PR is open.
