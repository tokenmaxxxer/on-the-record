---
status: proposed
files:
  - roles/specs/content-design.spec.json
  - roles/specs/data-engineering.spec.json
  - roles/specs/data-modeling.spec.json
  - roles/specs/growth-analytics.spec.json
  - roles/specs/knowledge-management.spec.json
  - roles/specs/localization.spec.json
  - roles/specs/ml-engineering.spec.json
  - roles/specs/observability.spec.json
  - roles/specs/pr-communications.spec.json
  - roles/specs/refactoring-legacy.spec.json
  - roles/specs/user-discovery.spec.json
  - roles/specs/accessibility.spec.json
  - roles/specs/api-design.spec.json
  - roles/specs/performance-engineering.spec.json
  - roles/specs/secure-coding.spec.json
  - roles/specs/test-authoring.spec.json
  - roles/specs/issue-retrospective.spec.json
  - roles/specs/release-engineering.spec.json
  - roles/specs/interaction-design.spec.json
  - roles/specs/ux-engineering.spec.json
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/accessibility-guard.sh
  - on-the-record/hooks/api-version-guard.sh
  - on-the-record/hooks/perf-measurement-guard.sh
  - on-the-record/hooks/test_accessibility_guard.py
  - on-the-record/hooks/test_api_version_guard.py
  - on-the-record/hooks/test_perf_measurement_guard.py
  - on-the-record/hooks/merge-allow-gate.sh
  - on-the-record/hooks/test-authoring-spawn-check.sh
  - on-the-record/hooks/issue-retrospective-spawn-check.sh
  - on-the-record/hooks/interaction-design-spawn-check.sh
  - on-the-record/hooks/ux-engineering-spawn-check.sh
  - on-the-record/hooks/test_routing_fix_spawn_checks.py
  - gates/spec_schema_five_activities_test.py
  - docs/specs/role-invariant-coverage.md
  - docs/specs/reconciled-index.md
---

# issue-1130: role expertise realization (proposal)

kind: proposal
subject: issue-1130

Proposal: docs/issue-1130/proposals/role-expertise-realization.md

## Intent

Extend the 14 cause-d role specs (the roles issue #1129 diagnosed as
having no standing duty wired) so each names a canonical methodology,
artifact form, and degree-level knowledge source for judgment,
planning, deliverable production, feedback, and review — mirroring the
depth already present in roles/specs/product-discovery.spec.json's
`source_standard` and roles/specs/requirements-engineering.spec.json's
`finding_method`/`anti_pattern`. Wire the 3 of those 14 that are also
classified `gate-now` in docs/specs/role-invariant-coverage.md
(accessibility, api-design, performance-engineering) with real,
mechanically-checkable hooks, default-on. Propose routing fixes — not
expertise depth — for the 6 cause-b roles (secure-coding,
test-authoring, issue-retrospective, release-engineering,
interaction-design, ux-engineering), whose hooks already work but never
cause the role's own session to spawn. Add a spec-schema validation
test asserting the five-activity depth exists for every in-scope spec.
Read basis: docs/issue-1130/reports/requirements-engineering/current-state-survey.md
and docs/issue-1130/reports/requirements-engineering/scout-brief.md.

## Constraints stated so far

- Scope is exactly issue #1129's cause groupings — cause (a)'s 13 roles
  and cause (c)'s 0 roles get no #1130 action (issue body, `gh issue
  view 1130`, read directly this session).
- Sources must be real, cited, and verified by web research per this
  issue's requirement 2 (THOROUGH domain research, no templating from
  memory) — every methodology named below carries a `Sources:`-list
  entry in the scout-brief, gathered via WebSearch/WebFetch by the
  researching agents rather than typed from training-data recall.
- Wiring (requirement 3) is hooks-only, default-on, per the
  invariant-first principle already stated in
  docs/specs/role-invariant-coverage.md's legend — spawns stay reserved
  for judgment residue a gate cannot approximate.
- Enforcement must anchor to an arbitrary target-project root
  (requirement 4), not be hardcoded to this repo's own file layout —
  each new hook's file-pattern trigger resolves relative to the target
  project root the plugin is installed into.
- This is a phase-1 proposal only (role directive, contract v3 s19) —
  no spec/hook edits land in this PR; they land in phase 2, after an
  approvers.md Approve.

## What will be done

### 1. Five-activity extension, 14 cause-d specs

For each of the 14 in-scope specs, add a `source_standard` field (top
methodology) plus five new fields — `judgment_methodology`,
`planning_methodology`, `deliverable_form`, `feedback_methodology`,
`review_methodology` — each an object `{method: string, source: string}`
naming a real, cited, named framework, and a `degree_level_knowledge`
array of 2-3 `{concept: string, source: string}` entries. Content for
all 14 roles, with sources, is fully drafted in
docs/issue-1130/reports/requirements-engineering/scout-brief.md and the
five research-agent transcripts synthesized into it (data-engineering:
DAMA-DMBOK + Kimball; data-modeling: Codd normalization + IDEF1X;
growth-analytics: AARRR + Lean Analytics + HEART; content-design: NN/g
heuristics + Halvorson content strategy; pr-communications:
Conventional Commits + Keep a Changelog + SemVer; localization: ISO
17100 + MQM + XLIFF; knowledge-management: SECI model + ISO 30401;
ml-engineering: Google's Rules of ML + CRISP-DM + Model Cards;
observability: three pillars + SLO/error-budget + RED/USE;
refactoring-legacy: Fowler's Refactoring catalog + Feathers'
characterization tests + Strangler Fig; user-discovery: Mom Test +
Opportunity Solution Trees + JTBD + thematic-analysis saturation;
accessibility: WCAG 2.2 + VPAT/ACR; api-design: Google AIPs + Microsoft
REST Guidelines + OpenAPI; performance-engineering: USE/RED + SLO
capacity planning + Tail at Scale). Phase 2 copies this drafted content
into each spec.json verbatim, field-by-field, with no re-research.

### 2. Hook wiring, 3 gate-now roles

Add three new hooks mirroring the existing `design-rationale-guard.sh`
pattern (frontmatter/trailer-presence check, not a semantic audit):

- `accessibility-guard.sh` — fires on diffs to user-visible-surface
  files (`**/*.{html,jsx,tsx,vue,svelte}` plus any project-declared
  component directory); rejects an added image element with no `alt`,
  or an added interactive element with no discoverable accessible name.
- `api-version-guard.sh` — fires on diffs to a discovered API contract
  file (`**/openapi.{yaml,json}`, `**/swagger.{yaml,json}`, or a
  project-declared proto path); structurally diffs old vs. new spec and
  rejects a removed/renamed path or required field when the spec's own
  version field is unchanged.
- `perf-measurement-guard.sh` — fires on diffs to a project-declared or
  pattern-matched hot-path file; requires the commit/PR body to carry a
  `perf:` trailer citing a benchmark number or before/after latency.

Each hook is registered in `on-the-record/hooks/hooks.json` and ships
with a `test_*_guard.py` exercising one refusal case, matching the
acceptance criterion's own check clause. File-pattern discovery in all
three is anchored to the target project root passed at hook invocation,
never to this repo's own paths — satisfying requirement 4.

### 3. Routing-fix proposals, 6 cause-b roles

No spec depth changes for these six. Instead, phase 2 adds a `trigger`
object (mirroring `secure-coding.spec.json`'s existing shape) to each
of the specs that lacks one, naming a `record_absent_for: <role>`
check, and either extends the existing merge-time chokepoint
`on-the-record/hooks/merge-allow-gate.sh` (for release-engineering,
since it is already universal) or adds one of four new, narrowly-scoped
routing-check hooks — `test-authoring-spawn-check.sh`,
`issue-retrospective-spawn-check.sh`,
`interaction-design-spawn-check.sh`, `ux-engineering-spawn-check.sh`,
each with a shared `test_routing_fix_spawn_checks.py` covering one
refusal case per hook — that consults `record_absent_for` before
allowing the triggering event (merge, or — for issue-retrospective —
issue close) to finalize. `secure-coding`'s board_condition already
names the correct event; only its consumer (a merge-time check) is
missing, so it reuses `merge-allow-gate.sh` rather than a new file.
Full per-role diagnosis and routing_fix_proposal text is in the
research transcript synthesized into the scout-brief's "Must-bes"
section for this cluster.

### 4. Spec-schema depth test

`gates/spec_schema_five_activities_test.py` asserts, for the 14
in-scope specs, that `judgment_methodology`, `planning_methodology`,
`deliverable_form`, `feedback_methodology`, `review_methodology`, and
`degree_level_knowledge` are all present and each names a non-empty
`source` — run via `python3 -m pytest gates/ -q -k spec`, matching the
acceptance criterion's stated check command. The empty-state case (a
role diagnosed as workload-never-triggers, i.e. any cause-a role) is
asserted absent from the test's role list, not silently skipped.

## What is out of scope

- Cause (a)'s 13 roles and cause (c)'s 0 roles — no #1130 action, per
  issue body and the current-state survey's "Scope input" section.
- Any spec/hook file edit in this phase-1 PR — this proposal only; the
  files listed in frontmatter are the phase-2 write set.
- Substance grading of the cited methodologies beyond source-realness —
  the acceptance criterion itself states quality is human PR review,
  not a mechanical check.
- New standing hooks for the 11 cause-d roles that are NOT also
  gate-now (content-design, data-engineering, data-modeling,
  growth-analytics, knowledge-management, localization, ml-engineering,
  observability, pr-communications, refactoring-legacy,
  user-discovery) — role-invariant-coverage.md classifies these
  `directive-only`, and this issue's requirement 3 only wires roles
  already classified gate-now-but-unwired.

## How you will know it worked

`python3 -m pytest gates/ -q -k spec` exits 0 after phase 2, with the
new five-activity assertions included and passing for all 14 specs;
each of the three new hooks has a `test_*_guard.py` exercising one
refusal case; `on-the-record/hooks/hooks.json` lists the three new
hooks; `docs/specs/role-invariant-coverage.md`'s rows for accessibility,
api-design, and performance-engineering gain a `(landed)` marker and
`docs/specs/reconciled-index.md` is regenerated in the same commit
(spec-index-preflight.sh's own requirement).

## Accumulation

No accumulation-shaped change here — this proposal adds bounded,
enumerable content (14 specs' worth of five-activity fields, 3 hooks,
6 routing-fix spec edits) rather than an open-ended or per-item-growing
structure; nothing in phase 2 grows unboundedly with future issues.

## What did not work

- After-proposal warrant-hunt found the body's routing-fix section (§3)
  named files (`merge-allow-gate.sh`, four new routing-check hooks) that
  the frontmatter `files:` write set did not list — a write-set/body
  mismatch that would have given phase-2 textual cover to exceed the
  frozen write set. Fixed same-session: added the five missing paths
  plus their shared test file to frontmatter and named them explicitly
  in the body.
