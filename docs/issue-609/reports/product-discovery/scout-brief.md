# Scout brief — issue #609 product-discovery

## Skip record

Scouting (external sweep for best-in-class exemplars) is skipped. Reason, one sentence: this
issue is an explicit EXTENSION of #573's already-scouted delegated-judgment mechanism ("Same
two-axis AND rule, same audit-record/citation discipline, same brokered routing as #573/#587") to
a new artifact type (spec-stage open decisions instead of approval acts), not a new mechanism-design
space — #573's product-discovery phase already ran the external sweep this role would otherwise run
(ITIL/CAB, code-review auto-merge/policy-as-code, aviation/medical delegation, RFC/ADR governance,
`docs/issue-573/reports/technical-feasibility/survey.md`) for exactly this class of decision
(who gets to decide, how narrow the auto-tier is, what the audit record must contain), and that
survey's findings (asymmetric conservatism, contradiction-only auto-reject bar, mechanized
re-derivable audit records, catalog-drift-from-loosening as the universal failure mode) apply
identically to an open-decision item as they did to an approval-act item — the only thing that
differs is which artifact triggers the routing (a proposal's stated ambiguity vs. a candidate
decision awaiting approve/reject), which is current-state-survey territory (what exists in this
repo to route through), not scout territory (what the field does elsewhere). Re-scouting the same
methodology space would duplicate #573's sources, not add a new angle.

This role's proposal applies the already-scouted field (via #573's registered hypothesis package
and #586's completed axis matrix) to this issue's specific extension question: does an open-decision
item reuse the existing `axis_evaluation` shape as-is, or does it need its own upstream record shape.
That is a routing/schema decision grounded in this repo's current state, not a "what does the
industry do" question.

No new product-facing decision has surfaced past what #573's Step 1 sweep and this repo's current
state already cover. If one surfaces during architecture/implementation (e.g. a new UI/flow for
surfacing the open-decision audit trail at spec review), that role runs its own micro-round per the
re-scout trigger rule.
