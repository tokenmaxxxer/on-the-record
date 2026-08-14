---
subject: issue-1199
role: performance-engineering
kind: scout-brief
---

# Scout brief (rework): Claude Code plugin ecosystem for performance work (issue-1199)

Per the 2026-08-14 operator amendment: the survey target for this
rework is the Claude Code plugin/skill ecosystem, not general
performance-domain tools. This addendum sits alongside, not replaces,
the prior scout-brief.md (that domain-tool survey's fold-in already
landed and stays).

Mode: batched-sequential `WebSearch` calls (4 angles: marketplace
listings, awesome-lists, official marketplace, skill/agent-file
content) run in one turn, followed by one deepening round fetching
SKILL.md / agent .md content directly. No parallel subagent fan-out
was used — a plugin-landscape sweep is text search, not independently
producible build units.

## Category coverage (adoption evidence)

canonical: `gh api repos/rohitg00/awesome-claude-code-toolkit
repos/composio-community/awesome-claude-plugins
repos/hesreallyhim/awesome-claude-code
repos/anthropics/claude-plugins-official repos/borghei/Claude-Skills
--jq '.full_name+" "+(.stargazers_count|tostring)'`, run this session:
```
rohitg00/awesome-claude-code-toolkit 2499
composio-community/awesome-claude-plugins 1882
hesreallyhim/awesome-claude-code 52240
anthropics/claude-plugins-official 33491
borghei/Claude-Skills 478
```
canonical: `gh api search/repositories -X GET -f
q="perf-profiler rohitg00" --jq '.items[] | .full_name+" "+(.stargazers_count|tostring)'`,
run this session:
```
jeremylongshore/claude-code-plugins-plus-skills 2630
ccplugins/awesome-claude-code-plugins 910
```
Multi-source mention corroboration (WebSearch, this session): a
perf-profiler plugin was independently reported at 1,716 stars/535
forks by lobehub.com and claudepluginhub.com; awesome-claude-code
(52.2k stars) and awesome-claude-skills (13k stars) both list
performance/profiling entries as a named category.

## Design moves extracted, per source fetched this session

1. **perf skill, composio-community/awesome-claude-plugins
   (1,882★)** — canonical: fetched
   https://raw.githubusercontent.com/ComposioHQ/awesome-claude-plugins/master/perf/skills/profile/SKILL.md
   this session. Gate: profiling is blocked until debug symbols are
   confirmed present and a specific performance scenario is stated —
   "profiling without justification is blocked." Evidence rule:
   bottleneck claims require file:line hotspot location plus a
   flamegraph/equivalent artifact; output is kept "minimal and
   evidence-backed," no speculative bottleneck naming.

2. **performance-engineer agent, rohitg00/awesome-claude-code-toolkit
   (2,499★)** — canonical: fetched
   https://raw.githubusercontent.com/rohitg00/awesome-claude-code-toolkit/main/agents/quality-assurance/performance-engineer.md
   this session. Five-step gated workflow: measure (reproducible
   benchmark) -> profile (never guess) -> hypothesize (data-driven) ->
   implement (minimal change) -> verify (same benchmark; **revert if
   numbers don't improve**). Post-fix gate requires before/after
   measurement under the *same* benchmark methodology, percentile
   values (p50/p95/p99, not averages), and statistical-significance
   confirmation (t-test recommended) before an improvement is claimed
   as real.

## Gap line

The existing checklist (from the prior domain-tool fold-in) already
covers: numeric SLO, staged workload ramp profile,
open-loop-vs-response-gated declaration, percentile evidence, and
profiling-artifact linkage for bottleneck claims. It did NOT cover: a
precondition gate on profiling readiness (symbols + named scenario)
before a profiling run is even scheduled, an explicit
revert-if-no-improvement discipline tied to the fix-verification step,
or a statistical-significance requirement distinguishing a real
improvement from noise. These three gaps map directly to the two
plugin sources above and are what this rework's checklist edit closes.

## Sources

- https://raw.githubusercontent.com/ComposioHQ/awesome-claude-plugins/master/perf/skills/profile/SKILL.md
- https://raw.githubusercontent.com/rohitg00/awesome-claude-code-toolkit/main/agents/quality-assurance/performance-engineer.md
- https://github.com/rohitg00/awesome-claude-code-toolkit
- https://github.com/composio-community/awesome-claude-plugins
- https://github.com/hesreallyhim/awesome-claude-code
- https://github.com/anthropics/claude-plugins-official
- https://lobehub.com/skills/jeremylongshore-claude-code-plugins-plus-skills-application-profiler
- https://www.claudepluginhub.com/plugins/rohitg00-perf-profiler-plugins-perf-profiler
