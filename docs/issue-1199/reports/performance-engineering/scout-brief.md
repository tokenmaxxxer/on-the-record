---
subject: issue-1199
role: performance-engineering
kind: scout-brief
---

# Scout brief: performance-engineering tool landscape (issue-1199)

canonical: `gh api repos/grafana/k6 repos/wg/wrk repos/sharkdp/hyperfine
repos/locustio/locust repos/tsenart/vegeta repos/apache/jmeter
repos/gatling/gatling repos/brendangregg/FlameGraph repos/benfred/py-spy
repos/google/pprof --jq '.full_name+" "+(.stargazers_count|tostring)'`
(looped one repo per call), run this session.

Mode: batched-sequential `gh api` calls in one turn, one sweep stage plus
one deepen round reading each tool's own README/docs for design-move
detail (no parallel subagent fan-out — a star-count sweep is one search
angle, not several).

## Category coverage (adoption evidence, star counts per the canonical
`gh api` sweep above)

Load/traffic generation: grafana/k6 31,247; wg/wrk 40,388;
sharkdp/hyperfine 28,650 (micro-benchmarking, adjacent statistical-rigor
category); locustio/locust 28,068; tsenart/vegeta 25,143;
apache/jmeter 9,502; gatling/gatling 6,944.

Profiling/bottleneck-evidence: brendangregg/FlameGraph 19,664;
benfred/py-spy 15,431; google/pprof 9,260.

## Design moves (per tool family)

1. **k6/Locust/Gatling — load-as-code.** canonical: k6 docs "Thresholds"
   and "Ramping VUs executor," fetched this session
   (https://grafana.com/docs/k6/latest/using-k6/thresholds/,
   https://grafana.com/docs/k6/latest/using-k6/scenarios/executors/ramping-vus/).
   Both the load profile (staged ramp-up/sustain/ramp-down) and the SLO
   threshold are written as executable script content, evaluated
   automatically at run end — not a human reading a graph afterward.

2. **wrk/vegeta — open-loop generators.** canonical: vegeta README
   "constant request rate" section and Gil Tene, "How NOT to Measure
   Latency," fetched this session (https://github.com/tsenart/vegeta#readme,
   https://www.infoq.com/presentations/latency-pitfalls/). Both send load
   at a fixed target rate independent of response time (open-loop).
   canonical: same Tene talk cited above. A response-gated generator
   (next request issued only after the prior reply arrives) under-reports
   tail latency during a slowdown — the coordinated-omission effect
   Tene's talk names. Which model a given load run used changes what its
   reported p99 means.

3. **FlameGraph/py-spy/pprof — sampling profilers.** canonical: py-spy
   README "how it works" and Brendan Gregg's FlameGraph README, fetched
   this session (https://github.com/benfred/py-spy#readme,
   https://github.com/brendangregg/FlameGraph#readme). All three sample
   live call stacks — py-spy attaches to an unmodified running process,
   no code change required — and render a flamegraph whose bar width is
   time-in-stack, pointing at the hot path directly rather than through
   an aggregate timing number.

4. **hyperfine — statistical micro-benchmarking.** canonical: hyperfine
   README "Features" section, fetched this session
   (https://github.com/sharkdp/hyperfine#readme). Runs a benchmark
   repeatedly with warmup runs excluded, reports
   mean/stddev/min/max, and flags statistical outliers rather than
   reporting one run's number as the result.

## Gap line

canonical: `cat /home/jwjung/tokenmaxxxer/rulebooks/performance-engineering-rulebook/performance-engineering-checklist/checklist.md`,
read this session.

The checklist's phase-1 "Workload characterization" item text is
"concurrency level, request/transaction mix, and ramp-up profile" —
canonical: same checklist.md read above, that item's exact wording — no
staged-ramp structure and no open/response-gated generation-model field
in that text.

canonical: same checklist.md read above. The phase-2 "Bottleneck-evidence
linkage" item text asks only that a bottleneck point at
percentile/measurement data — no profiling-artifact field in that text.

canonical: same checklist.md read above. The phase-2 "Repro info" item
text asks for hardware/config/tool-version detail — no repeated-run-
variance field in that text.

Design moves 1-4 above supply each of these three missing fields.

## Adopt / skip

canonical: same checklist.md read above.

Adopt into checklist.md, as additive checklist items (the role's own
authoring norm, no tool name in the item text): a staged-ramp +
open/response-gated declaration field on the workload-characterization
item; a profiling-artifact field on the bottleneck-evidence-linkage
item; a repeated-run-variance field on the repro-info item.

Skip: any tool-name reference or tool catalog inside the public
checklist.md itself — the evidence trail (tool names, star counts,
fetched sources) stays only in this brief, the phase-1 proposal, and
this issue's phase-2 record.

## Sources
- https://github.com/grafana/k6
- https://github.com/wg/wrk
- https://github.com/sharkdp/hyperfine
- https://github.com/locustio/locust
- https://github.com/tsenart/vegeta
- https://github.com/apache/jmeter
- https://github.com/gatling/gatling
- https://github.com/brendangregg/FlameGraph
- https://github.com/benfred/py-spy
- https://github.com/google/pprof
- https://grafana.com/docs/k6/latest/using-k6/thresholds/
- https://grafana.com/docs/k6/latest/using-k6/scenarios/executors/ramping-vus/
- https://www.infoq.com/presentations/latency-pitfalls/
