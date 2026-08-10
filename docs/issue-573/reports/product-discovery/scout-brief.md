# Scout brief — issue #573 product-discovery

## Skip record

Scouting (external sweep for best-in-class exemplars) is skipped for the mechanism-design
decisions this proposal makes. Reason, one sentence: the current-state survey's gaps are already
covered by Step 1's merged four-angle sweep (`docs/issue-573/reports/technical-feasibility/survey.md`)
— ITIL/CAB, code-review auto-merge/policy-as-code, aviation/medical delegation, RFC/ADR
governance — which is exactly the "best of the deliverable's own kind" sweep this role would
otherwise run for a delegated-judgment/tiered-approval mechanism, was fanned out as four genuinely
concurrent background agents with primary-source citations, and the operator's own sequencing
directive on the issue ("RESEARCH FIRST ... and only then converge") assigns that sweep to Step 1
precisely so later steps consume it rather than re-running it. Re-scouting the same methodology
space here would duplicate Step 1's sources, not add a new angle; this role's decisions (below)
apply that already-scouted field to this repo's own existing precedents (#511 impact axes, #566
capture surface, #476 anti-theater line), which is current-state-survey territory, not scout
territory.

No new product-facing decision has surfaced mid-build past what Step 1 covers, so no
re-scout trigger has fired. If one does during architecture/implementation (e.g. a new UI/flow
for surfacing the audit record), that role runs its own micro-round per the re-scout trigger rule.
