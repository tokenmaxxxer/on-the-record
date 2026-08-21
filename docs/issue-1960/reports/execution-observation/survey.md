---
name: skill-invocation-log-survey
subject: issue-1960
---

# Survey: session-log joinability for skill-invocation measurement (issue-1960)

Subject: issue-1960
Basis: gh issue view 1960; docs/reports/consult-log.md 2026-08-22 requirements-engineering consult cited on the issue.

## What was surveyed

Session logs under `~/.tokenmaxxxer/work/*.session*.log`.

```
canonical: this session, live command
derived: ls ~/.tokenmaxxxer/work/*.session*.log | wc -l
660
```

Each role-session's log is JSONL (one JSON object per line, `type` field
discriminates: `system`, `assistant`, `user`, etc.).

## Join point found

A `type:"system", subtype:"init"` line, emitted once near the top of each
log, carries a `plugins` array. Each entry is `{"name", "path", "source"}`.
Entries whose `path` contains `/skill-registry/skills/` are the
role-mapped skill-repository skills mounted for that session — this is
the "mounted skills" half of the join.

```
canonical: on-the-record-issue-1955-implementation.session.20260822T072848.1258847.log line 14 (subtype:"init")
"plugins":[{"name":"core","path":"/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core/core", ...},
{"name":"terse", ...}, {"name":"freelunch", ...}, {"name":"scout", ...}, {"name":"warrant", ...},
{"name":"implementation-complexity-coupling-management","path":"/home/jwjung/skill-registry/skills/implementation-complexity-coupling-management", ...},
{"name":"implementation-design-pattern-selection", ...},
{"name":"implementation-performance-data-structure-choice", ...},
{"name":"implementation-blueprint", ...}]
```

Distinct from this is the session-wide `skills` array in the same init
line — this lists the entire skill catalog reachable via the Skill tool
(every skill in the marketplace), not the role-mapped subset. Using
`skills` instead of `plugins`-filtered-by-path would count every session
as having every skill "mounted," destroying the relevance-gated
denominator the issue's consult requires. The correct join key is
`plugins[].path` containing `/skill-registry/skills/`, not the `skills`
array.

The other half of the join — Skill tool invocations — is any line matching
`"type":"tool_use"` with `"name":"Skill"` anywhere in the log body (the
Skill tool call appears as a normal assistant tool_use entry, same as
Bash/Edit/Read/Write).

## Non-joinable cases (empty state)

Some logs are unmeasurable by this join. Zero-byte logs (session crashed
or was killed before any `init` line was written):

```
canonical: this session, live command
derived: find ~/.tokenmaxxxer/work -maxdepth 1 -name '*.session*.log' -size -1k
./on-the-record-issue-473-conformance-review.session.20260814T150333.71405.log
```

```
canonical: on-the-record-issue-473-conformance-review.session.20260814T150333.71405.log
derived: cat on-the-record-issue-473-conformance-review.session.20260814T150333.71405.log
(empty output — 0 bytes, i.e. that file is empty)
```

Pre-JSONL / plain-text session logs, if any exist outside the sampled
window, would also fail the `init`-line parse and must be listed
unmeasurable, not dropped, per the issue's empty-state requirement.

Sessions from before the skill-repository role mapping existed (issue-1955)
are joinable but legitimately show `mounted_count: 0` — this is not an
unmeasurable case, it's a true negative: no skill-repository skill was
mapped to that role at that time, so it is excluded by the relevance gate
below, not marked unmeasurable.

## Relevance-gating heuristic

The issue's consult requires "only sessions whose task plausibly warrants a
mounted skill" in the denominator. Heuristic adopted:

A session is relevance-gated in (counted in the denominator) iff its
`plugins` array contains at least one entry whose `path` matches
`/skill-registry/skills/<skill-name>` — i.e., the role-to-skill-repository
mapping (issue-1955/#1758) actively mounted at least one skill for that
session's role.

Rationale: the role mapping step already encodes the relevance judgment —
a role is mapped to a skill-repository skill only when that skill's domain
plausibly applies to the role's task class (e.g. `implementation` role maps
to `implementation-blueprint`, `implementation-design-pattern-selection`,
etc. — canonical: the `plugins` join point shown above). Re-deriving
relevance from free-text task descriptions would duplicate that judgment
with a weaker signal and risks disagreeing with the mapping that produced
the mount in the first place. A session with `mounted_count: 0` is
excluded from the denominator (no mapped skill existed to invoke, so its
invocation rate is undefined, not zero).

This is a coarser gate than a per-skill relevance match (e.g. "was
`implementation-blueprint` specifically relevant to this task's actual
work") — it is stated as the adopted heuristic, not the only possible one;
a finer heuristic is out of scope for phase A given the consult's own
caveat that "relevance criterion needs an explicit heuristic," which this
satisfies at the role-mapping granularity.

## What did not work

canonical: this session's own tool-call sequence — the `plugins`-path join
point was found on the first log inspected; nothing to report here.

## What was done

Read the issue and its consult, inspected the
`on-the-record-issue-1955-implementation` session log to find the
mount/invocation join point (above), and wrote/ran an analysis script
(`/tmp/measure_skill_invocation.py`) against a sample spanning role
diversity and recency.

canonical: docs/issue-1960/reports/execution-observation/baseline-measurement.md
That same file lists the role types the join was checked against
(implementation, test-authoring, execution-observation, conformance-review,
observability, market-analysis, architecture, product-discovery,
technical-feasibility) and holds the resulting measurement.

## Why

Per contract v3 s19, current-state survey precedes the proposal. The
measurement artifact itself (acceptance check 1) needs the join point and
relevance heuristic established here before it can be produced honestly.

## Upstream

Basis: gh issue view 1960; consult cited on the issue
(docs/reports/consult-log.md 2026-08-22 requirements-engineering).

## Open findings

canonical: docs/issue-1960/reports/execution-observation/baseline-measurement.md (the sampled-session table, dated 2026-08-14 through 2026-08-22)
- The `plugins`-path join point works for every log in that sampled window
  but was not verified against logs older than 2026-08-14; older logs may
  predate the `plugins` field entirely and would need to fall into the
  unmeasurable bucket rather than being misread as `mounted_count: 0`.
- The role-mapping-implies-relevance heuristic inherits any error in the
  role-to-skill mapping itself (issue-1955/#1758) — if a role is mismapped
  to an irrelevant skill, this heuristic would count that session as
  relevance-gated-in when it plausibly isn't. Out of scope for phase A.

kind: report
loop_state: reported
