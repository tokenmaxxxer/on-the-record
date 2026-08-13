---
role: performance-engineering
subject: issue-1174
---

# Scout brief — performance-engineering operational playbook

Mode: parallel WebSearch sweep, 4 angles in one turn (practitioner
methodology / SRE latency-SLO practice / queueing-theory capacity math /
removal-shaped optimization patterns). 1 stage, well under the 5-stage /
3min budget — signal converged immediately on canonical, uncontested
sources; no deepening round changed a build decision (saturation reached
after stage 1).

## Must-bes (what a top practitioner's judgment assumes)
- Diagnose via utilization+saturation+errors per resource before changing
  anything (USE method) — never "optimize" the first metric that looks off.
- Report latency as percentiles (p50/p95/p99), never mean — mean hides the
  tail that SLOs are actually written against.
- Capacity/queueing decisions run through L = λW; utilization approaching
  1.0 is treated as a wait-time cliff, not a linear cost.
- Removal-shaped fixes (kill redundant queries, drop unbounded pools,
  delete dead cache layers) outrank addition-shaped fixes (add cache, add
  replica) when both close the same gap — addition compounds operational
  cost, removal doesn't.

## Performance axes practitioners compete on
1. Diagnosis rigor (methodical vs guess-and-check)
2. Percentile discipline in SLOs
3. Capacity math literacy (queueing, not gut-feel headroom)
4. Bias toward removal/simplification over bolt-on scaling

## Adopt / skip
- Adopt: condition→choice→source rule shape, three layers (practitioner
  rule / named methodology / theory), REMOVAL rules as first-class, not
  an afterthought.
- Skip: vendor-specific APM tool tutorials (not portable, not a decision
  rule) and generic "monitor everything" advice with no threshold.

## Gap line
Current spec/rulebook state (performance-engineering-rulebook repo) has
gate scripts and a checklist but no docs/playbook/ — 0 of the required
condition→choice→source rules exist yet. This playbook is a net-new
addition, not a revision.

## Stages/mode
1 stage, parallel WebSearch fan-out (native parallel tool calls, not
subagents — appropriate at this width).

Sources:
- https://www.brendangregg.com/USEmethod/use-linux.html
- https://www.brendangregg.com/methodology.html
- https://sre.google/sre-book/service-level-objectives/
- https://sre.google/workbook/error-budget-policy/
- https://sixsigmadsi.com/glossary/littles-law/
- https://www.clearpeaks.com/database-connection-pooling-a-guide-to-tuning-performance-optimisation/
