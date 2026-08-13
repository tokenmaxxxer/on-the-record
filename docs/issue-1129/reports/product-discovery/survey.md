# Current-state survey — issue #1129: unused-role diagnosis

subject: issue-1129
requirement: northpole req#1/#5 (docs/specs/northpole.md) — delegation to
specialized roles is the orchestration backbone; a role that can never
wake cannot receive delegation.

## Background / context

The role system defines 43 domains (`roles/specs/*.spec.json`). Each
domain accumulates a board record only when a session actually spawns
into that role and writes to `docs/issue-<n>/reports/<role>*`. Issue
#1129 asks for a MEASURED diagnosis of why 33 of those 43 have zero
such records across the repo's history, before any remedy is proposed
(remedy is explicitly out of scope, routed to a follow-up issue).

## Problem stated without any solution attached (JTBD tuple)

- **Job performer**: the repo's own routing/spawn layer (`spawn.py`,
  the orchestrating role in each session) and, downstream, whoever
  scopes the next remediation issue against this domain.
- **Job**: know, with recomputable evidence, WHY a given unused role
  never accumulates a board record — so a future decision to invest in
  waking a specific role is made against a named cause, not a guess.
- **Circumstance**: northpole req#1/#5 asserts delegation to
  specialized roles as the orchestration backbone; whether that holds
  in practice across all 43 domains is currently unverified by
  evidence (measured below).
- **Desired outcome**: a per-role cause classification, backed by
  counts recomputable from the same commands cited in this record, plus
  a discriminating IS/IS-NOT contrast between the roles that DO get
  used and the ones that don't — with no remedy attached (remedy is
  #1130's scope).

No solution is embedded in this framing — this issue produces a
diagnosis, not a fix.

## OST placement

Layer: **opportunity**, not yet a candidate solution and not yet a
discriminating-assumption test. The outcome this sits under is
northpole req#1/#5's delegation backbone; the opportunity this survey
resolves is "is 'roles can be delegated to' actually true in practice,
and if not, which mechanism explains each gap." No candidate solutions
are named here — this record's job is to produce the evidence a future
proposal (#1130) will branch candidate solutions from. No
discriminating-assumption test is registered at this layer because
there is no candidate solution yet to test between.

## Scout skip record

Skipped. Reason, one sentence: this is a measurement/diagnosis task
over the repo's own existing history and specs — there is no external
product surface to benchmark against and no design decision open (the
issue's acceptance criteria fully specify the deliverable shape: a
classification table with recomputable counts, plus an IS/IS-NOT
section), so neither scouting skip condition needs stretching — this
is closest to "spec literally leaves no design decision open."

## What the codebase currently has

`derived: find . -iname "runs" -o -iname "ledger.jsonl" 2>/dev/null`
```
(no output)
```

The issue's own acceptance text names `runs/ledger.jsonl` as a data
source. canonical: `find . -iname "runs" -o -iname "ledger.jsonl"`
(above) produced no matches; canonical: `ls ledger/` (this session) —
the only `ledger/` directory present holds `collect.py`,
`decisions.py`, `test_decisions.py` (aggregation scripts, no data
files). This is itself a finding: one of the issue's three named
evidence sources is absent, so the diagnosis below is built entirely
from `docs/issue-*/reports/` (board records) and
`docs/reports/consult-log.md` + per-issue `consult-log.md` files
(consult baselines), with the ledger gap called out explicitly rather
than silently substituted.

### Canonical role list (43)

`derived: ls roles/specs/ | sed 's/\.spec\.json$//' | sort | wc -l`
```
43
```

### Board records per canonical role (top-level `docs/issue-*/reports/<role>.md`)

`derived: find docs/issue-*/reports -maxdepth 1 -name "*.md" | sed -E 's#.*/reports/##; s#\.md$##' | sort | uniq -c | sort -rn`
```
    245 implementation
     44 coding          (non-canonical alias, not a roles/specs/*.spec.json name)
     26 execution-observation
      9 defect-verification
      6 conformance-review
      6 architecture
      3 requirements-engineering
      3 product-discovery
      2 verify           (non-canonical)
      2 qa               (non-canonical)
      2 feasibility       (non-canonical, distinct from technical-feasibility)
      1 ux-design         (non-canonical)
      1 technical-writing
      1 security-threat-model
      1 review            (non-canonical)
      1 reflect           (non-canonical)
      1 product           (non-canonical)
      1 hunt-implementation (warrant-hunt artifact, not a role record)
      1 consult-log       (log file, not a role record)
```

### Board activity per canonical role, including per-role subdirectories

`derived: python3 walk over docs/issue-*/reports/<role>/** (run in this session)`
```
392 implementation
73 execution-observation
69 product-discovery
51 coding            (non-canonical)
42 architecture
15 defect-verification
11 technical-feasibility
7 conformance-review
6 requirements-engineering
2 security-threat-model
2 feasibility          (non-canonical)
2 technical-writing
2 verify               (non-canonical)
2 qa                   (non-canonical)
1 review               (non-canonical)
1 product              (non-canonical)
1 reflect              (non-canonical)
```

Merging top-level + subdirectory activity and keeping only names that
match a canonical `roles/specs/*.spec.json` entry: exactly the
following canonical roles have any board activity at all —

`implementation, execution-observation, product-discovery, architecture,
defect-verification, technical-feasibility, conformance-review,
requirements-engineering, security-threat-model, technical-writing`

`derived: echo "implementation execution-observation product-discovery architecture defect-verification technical-feasibility conformance-review requirements-engineering security-threat-model technical-writing" | wc -w`
```
10
```
This matches the issue body's "10 used roles" claim, verified
independently here rather than assumed from the issue text. The
remaining roles have zero matching records anywhere under
`docs/issue-*/reports/`:

`accessibility, api-design, brand-design, capacity-planning,
content-design, customer-support, data-engineering, data-modeling,
devrel, finance-unit-economics, growth-analytics, incident-response,
interaction-design, issue-retrospective, knowledge-management,
legal-compliance, localization, market-analysis, marketing,
ml-engineering, observability, partnerships-bd,
performance-engineering, pr-communications, pricing,
refactoring-legacy, release-engineering, risk-management, sales,
secure-coding, test-authoring, user-discovery, ux-engineering`

`derived: comm -23 <sorted 43-role list> <sorted 10-name used list>` — 43
canonical roles minus the 10-name used list above yields 33 names,
matching that list's own word count (`echo "<list>" | wc -w` → 33).

### Consult-path baseline

`derived: cat docs/reports/consult-log.md; find . -name consult-log.md`

canonical: `docs/reports/consult-log.md`, read directly — 4 `- ` entries,
all `role=requirements-engineering`. canonical:
`docs/issue-1111/reports/consult-log.md`, read directly — 1 entry, also
`role=requirements-engineering` (`derived: grep -c "^-"
docs/issue-1111/reports/consult-log.md` → `1`, run in this session).
Total: **5** consult calls across the repo's history, all to the same
single role — matching the issue body's "consult path used 5 times
total, all requirements-engineering" claim.

### Role classification cross-reference (`docs/specs/role-invariant-coverage.md`)

canonical: `docs/specs/role-invariant-coverage.md`, read directly (landed
issue #960). It already classifies all 43 roles by whether a standing
hook enforces their invariant: `gate-now (landed)`, `gate-now`
(proposed, not yet landed), `directive-only` (stated as a role duty but
not mechanically checkable), or `spawn-only` (genuinely needs
situational judgment; the doc itself states "no repo-local signal" for
13 of these rows).

`derived: manual cross-tabulation of docs/specs/role-invariant-coverage.md's classification column against the 33-name unused-role list above`

| Coverage-doc class | Unused roles in this class | Count |
|---|---|---|
| gate-now, **landed**, hook fires on ~every relevant commit | secure-coding, test-authoring, issue-retrospective, release-engineering, interaction-design, ux-engineering | 6 |
| gate-now, **not yet landed** (proposed invariant, no hook exists) | accessibility, api-design, performance-engineering | 3 |
| spawn-only, coverage doc states "no repo-local signal" | brand-design, capacity-planning, customer-support, devrel, finance-unit-economics, incident-response, legal-compliance, market-analysis, marketing, partnerships-bd, pricing, risk-management, sales | 13 |
| directive-only, no mechanical hook | content-design, data-engineering, data-modeling, growth-analytics, knowledge-management, localization, ml-engineering, observability, pr-communications, refactoring-legacy, user-discovery | 11 |

`derived: 6+3+13+11 (arithmetic on the table above)` = 33, matches the
unused-role count exactly.

### `use_when` / `board_condition` shape (used vs unused roles)

canonical: `roles/specs/implementation.spec.json`, `use_when.board_condition`
field, read directly — *"a commit lands on the branch AND no
implementation record exists yet for that commit sha"* — unconditional
on every commit, no content/path filter.

canonical: `roles/specs/product-discovery.spec.json`, `use_when.board_condition`,
read directly — triggers on an issue's requirement being at
problem/hypothesis level, tied to issue-level state this repo's own
workload (feature/process issues) routinely produces.

canonical: `roles/specs/accessibility.spec.json`, `use_when`, read
directly — board_condition requires *"a new interaction pattern or
color-token set landed... AND no accessibility record exists yet"*,
gated by `trigger.path_patterns: **/*token*, **/*.css, **/*.tsx,
**/*.jsx, **/interaction*` and `content_patterns: aria-, color-token,
role="`.

`derived: find . -name "*.css" -o -name "*.tsx" -o -name "*.jsx"` (run in this session)
```
(no output)
```
This repo's own tree contains no `.css`/`.tsx`/`.jsx` files at all.
accessibility's trigger condition is structurally unsatisfiable by this
repo's own change population, independent of any routing or friction
question.

## IS/IS-NOT contrast: used vs unused roles

**IS** (the 10 used roles share):
1. `board_condition` is either unconditional on every commit
   (implementation), or keyed to issue/PR-level state this repo's own
   process necessarily produces on every issue (product-discovery,
   requirements-engineering, execution-observation, architecture,
   defect-verification, conformance-review) — never gated on a file
   pattern absent from this repo's own file population (see
   `use_when`/`board_condition` section above).
2. canonical: `docs/specs/role-invariant-coverage.md` rows for
   product-discovery, requirements-engineering, defect-verification,
   execution-observation, read directly — all list `gate-now (already
   landed)`, AND those same roles show real board activity in the
   "Board activity" section above: where a standing hook exists for the
   role's invariant, the role is ALSO still spawned as a distinct
   session that writes its own record — the hook and the role record
   are not substitutes for each other among the 10 used roles.
3. 8 of the 10 `derived: manual count against docs/specs/role-invariant-coverage.md's domain column (read above)`
   used roles' domains are about THIS repo's own artifacts
   (code, specs, requirements, architecture, defects) — self-referential
   to the tooling repo itself, not requiring external market/financial/
   customer context.

**IS-NOT** (what distinguishes the 33 unused roles, by sub-group —
counts sourced from the "Role classification cross-reference" table
above):

1. 13/33 `derived: "Role classification cross-reference" table above (docs/specs/role-invariant-coverage.md cross-tab)` are
   `spawn-only` roles the coverage doc itself already documents as
   needing context with "no repo-local signal" (market data, financial
   data, live incidents, sales/partner conversations) — this repo's own
   commit history structurally cannot produce a triggering workload for
   them (candidate cause **a**: workload never triggers domain).

2. 6/33 `derived: "Role classification cross-reference" table above (docs/specs/role-invariant-coverage.md cross-tab)` have
   a **landed** hook (secure-coding, test-authoring,
   issue-retrospective, release-engineering, interaction-design,
   ux-engineering) that fires on nearly every relevant commit, yet
   never produces a role record — the invariant is enforced INLINE by
   the hook blocking/passing the commit inside the implementation
   session, with no separate role session ever spawned to record it
   (candidate cause **b**: routing/enforcement absorbs the domain into
   implementation rather than delegating).

3. 11/33 `derived: "Role classification cross-reference" table above (docs/specs/role-invariant-coverage.md cross-tab)` are
   `directive-only` — stated as a duty in role docs but with no
   mechanical hook and no board_condition ever computed true by
   anything discoverable in this repo, so nothing in the pipeline can
   ever notice the duty fired (candidate cause **d**: no standing duty
   wired).

4. 3/33 `derived: "Role classification cross-reference" table above (docs/specs/role-invariant-coverage.md cross-tab)` are
   `gate-now` but explicitly **not yet landed** (accessibility,
   api-design, performance-engineering per the coverage doc's own
   landing-status note) — same cause **d**, plus for accessibility
   specifically the trigger's path patterns (`*.css`/`*.tsx`/`*.jsx`)
   match zero files in this repo's own tree, compounding with cause
   **a**.

That is 4 discriminating factors (board_condition scope,
hook-vs-role-session substitution, repo-self-referential vs
external-context domain, landed-vs-proposed gate status), exceeding
the required minimum of 3.

## Cause classification summary (33 unused roles)

`derived: sums from the "Role classification cross-reference" table above; cause (c) checked against the "Consult-path baseline" section above`

| Cause | Roles | Count |
|---|---|---|
| (a) workload never triggers domain | brand-design, capacity-planning, customer-support, devrel, finance-unit-economics, incident-response, legal-compliance, market-analysis, marketing, partnerships-bd, pricing, risk-management, sales | 13 |
| (b) routing/enforcement absorbs into implementation (landed hook, no role spawn) | secure-coding, test-authoring, issue-retrospective, release-engineering, interaction-design, ux-engineering | 6 |
| (c) consult-path friction | none of the 33 — the only consult activity observed (5 calls, see "Consult-path baseline" above) targeted a USED role (requirements-engineering); no unused role has any consult attempt to be blocked, so this cause has a measured zero share among the 33 | 0 |
| (d) no standing duty wired (directive-only, or gate-now not yet landed) | content-design, data-engineering, data-modeling, growth-analytics, knowledge-management, localization, ml-engineering, observability, pr-communications, refactoring-legacy, user-discovery, accessibility, api-design, performance-engineering | 14 |

`derived: 13+6+0+14 (arithmetic on the table above)` = 33, matches.

### Empty-state note (instrumentation gap)

canonical: `find . -iname "runs" -o -iname "ledger.jsonl"` (cited at the
top of this section) — `runs/ledger.jsonl`, named by the issue as a
primary data source, does not exist in this tree. Every count above is
instead recomputed from `docs/issue-*/reports/` and `consult-log.md`
files, which record only spawns/consults that already happened — they
cannot distinguish "orchestrator never even considered this role" from
"orchestrator considered it and routed elsewhere" for cause (b)'s 6
roles beyond what the landed-hook evidence already shows, nor can they
measure how often each `directive-only` role's board_condition silently
evaluates true with nothing built to notice it, for cause (d)'s 14
roles. What instrumentation would be needed: an orchestrator-side
routing log (which role was considered per issue, and why it was or
wasn't spawned) — a gap this survey documents rather than manufactures
from board output alone.

## Write-surface unknowns aimed at (no scout needed)

None outstanding for this diagnosis-only issue — all data sources
named by the issue's acceptance criteria have been read except the
non-existent `runs/ledger.jsonl`, called out above rather than silently
skipped.
