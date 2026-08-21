---
code_under_review:
  - docs/specs/role-source-allowlist.json
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# Phase-2 delivery: skill-axis phase-3 batch wave 3 (#1772)

## Summary of work

Delivered the two PRs named in the approved proposal
(docs/issue-1772/proposals/skill-axis-phase-3-wave-3.md, approved via
`APPROVE issue-1772/implementation`):

1. **skill-repository content PR**: adds 50 `SKILL.md` files across
   all 10 wave-3 roles (market-analysis, marketing, ml-engineering,
   observability, partnerships-bd, performance-engineering,
   pr-communications, pricing, product-discovery, refactoring-legacy),
   one directory per skill under `skills/<role>-<axis>/`, each
   byte-equal to its rulebook source, no `hooks/` dir anywhere. Branch
   tip: `b01825e`. No role is excluded this wave — all 10 have a
   migratable Markdown source (see the proposal's Rationale).

   canonical: `gh pr view 4 --repo tokenmaxxxer/skill-repository --json state,number,url` (skill-repository, executed live this turn)
   ```
   {"number":4,"state":"OPEN","url":"https://github.com/tokenmaxxxer/skill-repository/pull/4"}
   ```
   canonical: the `gh pr view 4` JSON output directly above (skill-repository, executed live this turn). State is `OPEN`, not merged — same fail-closed-ordering posture the earlier waves hit; see Rationale for deviations below.

2. **on-the-record allowlist PR** (this branch): adds 10 entries to
   `docs/specs/role-source-allowlist.json` mapping all 10 wave-3 roles
   to their migrated skill names.

   canonical: `git diff main -- spawn.py` (this branch, executed live
   this turn), empty output — no `spawn.py` hunk in this branch's diff
   against `main`.

## Check 1 — per-rulebook recursive diff (byte-equal evidence)

canonical: `diff <rulebook source> <skill-repository SKILL.md>` run
live this turn, once per file, across all 10 roles' 50 migrated files
(9 playbook-derived roles plus product-discovery's playbook files and
its pre-shaped `skills/*/SKILL.md` direct copies). Every diff returned
empty output.

```
=== market-analysis ===
  competitor-mapping: empty diff
  evidence-rigor: empty diff
  five-forces: empty diff
  jtbd-fit: empty diff
  mece-proposal: empty diff
=== marketing ===
  channel-selection: empty diff
  message-persuasion: empty diff
  positioning-differentiation: empty diff
  scope-pruning: empty diff
  segment-targeting: empty diff
=== ml-engineering ===
  evaluation-discipline: empty diff
  ml-test-score-scoring: empty diff
  model-provenance-versioning: empty diff
  rollout-promotion-rollback: empty diff
  serving-pattern-selection: empty diff
  slo-definition-tradeoffs: empty diff
=== observability ===
  cardinality-budget: empty diff
  explorability: empty diff
  methodology-selection: empty diff
  phase-trace: empty diff
  signal-golden: empty diff
  signal-red: empty diff
  signal-use: empty diff
=== partnerships-bd ===
  deal-structure-selection: empty diff
  exclusivity-and-scope-terms: empty diff
  governance-cadence-and-kpi: empty diff
  negotiation-positioning: empty diff
  term-sheet-comprehensibility-and-convention: empty diff
=== pricing ===
  design-rigor: empty diff
  method-family: empty diff
  scope-gate: empty diff
  tier-structure: empty diff
  verdict-report: empty diff
=== refactoring-legacy ===
  characterization-test-scope: empty diff
  refactoring-step-decomposition: empty diff
  seam-selection: empty diff
  strangler-fig-migration: empty diff
  verification-cadence: empty diff
=== performance-engineering (single combined file) ===
  operational-playbook: empty diff
=== pr-communications (single combined file) ===
  message-planning-and-evaluation-rules: empty diff
=== product-discovery playbook axis ===
  guardrail-metric-status: empty diff
  hypothesis-preregistration: empty diff
  jtbd-problem-framing: empty diff
  opportunity-solution-tree-branching: empty diff
  rice-ice-prioritization: empty diff
=== product-discovery pre-shaped skills (direct copy) ===
  hypothesis-testing: empty diff
  guardrail-metrics: empty diff
  opportunity-solution-tree: empty diff
  one-pager: empty diff
  assumption-mapping: empty diff
```

canonical: `find skills/product-discovery-one-pager -type f` (local
skill-repository clone, executed live this turn)
```
skills/product-discovery-one-pager/SKILL.md
```
canonical: the `find` output directly above. It lists only `SKILL.md` under `skills/product-discovery-one-pager/` — confirms `product-one-pager`'s `templates/one-pager-template.md` sibling was not migrated (defect-verification precedent, same as the proposal's Constraints).

No demoted-guidance appendices were added this wave. Checked every
wave-3 role's hook plugins for domain-substantive checks not already
present in the corresponding playbook axis text (same method the
earlier waves used):

canonical: `grep -rlE "re\.compile\(r'[^']{20,}" /tmp/onr-<role>-rulebook --include='*.py' --include='*.sh'`, executed live this turn across all 10 clones — every hit inspected inline is a target-path regex (`docs/issue-.../reports/<role>\.md`), a required-heading regex (e.g. pr-communications' `**Core message**:`/`**Proof point**:`, the `**Research|Action|Communication|Evaluation**:` label check), or a required-field/proximity regex (e.g. pricing's `Q_RE`/`A_RE`/`APPROVED_RE`) — all structural record-shape checks, not new domain guidance the playbook text is silent on. No band-word/formula-style domain check appears in any wave-3 role's hooks.

## Check 2 — `resolve_role_source()` live output, post-allowlist-merge

canonical: `python3 /tmp/wave3_work/check2_resolve.py` (this branch,
`spawn.resolve_role_source()` called directly with `repo_root` pointed
at the local skill-repository clone's `skills/` dir), executed live
this turn
```
market-analysis -> {'source': 'skill-repo', 'skills': ['market-analysis-competitor-mapping', 'market-analysis-evidence-rigor', 'market-analysis-five-forces', 'market-analysis-jtbd-fit', 'market-analysis-mece-proposal'], 'skill_sha': 'b01825e'}
marketing -> {'source': 'skill-repo', 'skills': ['marketing-channel-selection', 'marketing-message-persuasion', 'marketing-positioning-differentiation', 'marketing-scope-pruning', 'marketing-segment-targeting'], 'skill_sha': 'b01825e'}
ml-engineering -> {'source': 'skill-repo', 'skills': ['ml-engineering-evaluation-discipline', 'ml-engineering-ml-test-score-scoring', 'ml-engineering-model-provenance-versioning', 'ml-engineering-rollout-promotion-rollback', 'ml-engineering-serving-pattern-selection', 'ml-engineering-slo-definition-tradeoffs'], 'skill_sha': 'b01825e'}
observability -> {'source': 'skill-repo', 'skills': ['observability-cardinality-budget', 'observability-explorability', 'observability-methodology-selection', 'observability-phase-trace', 'observability-signal-golden', 'observability-signal-red', 'observability-signal-use'], 'skill_sha': 'b01825e'}
partnerships-bd -> {'source': 'skill-repo', 'skills': ['partnerships-bd-deal-structure-selection', 'partnerships-bd-exclusivity-and-scope-terms', 'partnerships-bd-governance-cadence-and-kpi', 'partnerships-bd-negotiation-positioning', 'partnerships-bd-term-sheet-comprehensibility-and-convention'], 'skill_sha': 'b01825e'}
performance-engineering -> {'source': 'skill-repo', 'skills': ['performance-engineering-operational-playbook'], 'skill_sha': 'b01825e'}
pr-communications -> {'source': 'skill-repo', 'skills': ['pr-communications-message-planning-and-evaluation-rules'], 'skill_sha': 'b01825e'}
pricing -> {'source': 'skill-repo', 'skills': ['pricing-design-rigor', 'pricing-method-family', 'pricing-scope-gate', 'pricing-tier-structure', 'pricing-verdict-report'], 'skill_sha': 'b01825e'}
product-discovery -> {'source': 'skill-repo', 'skills': ['product-discovery-guardrail-metric-status', 'product-discovery-hypothesis-preregistration', 'product-discovery-jtbd-problem-framing', 'product-discovery-opportunity-solution-tree-branching', 'product-discovery-rice-ice-prioritization', 'product-discovery-assumption-mapping', 'product-discovery-guardrail-metrics', 'product-discovery-hypothesis-testing', 'product-discovery-one-pager', 'product-discovery-opportunity-solution-tree'], 'skill_sha': 'b01825e'}
refactoring-legacy -> {'source': 'skill-repo', 'skills': ['refactoring-legacy-characterization-test-scope', 'refactoring-legacy-refactoring-step-decomposition', 'refactoring-legacy-seam-selection', 'refactoring-legacy-strangler-fig-migration', 'refactoring-legacy-verification-cadence'], 'skill_sha': 'b01825e'}
```
canonical: the `check2_resolve.py` output directly above. `skill_sha` (`b01825e`) matches the content PR branch's own tip commit recorded in Summary item 1 above — captured against the content PR branch's own tip, not skill-repository's merged `main`, same method the earlier waves used (see Rationale for deviations below).

## Check 3 — control unmapped role

canonical: same `python3 /tmp/wave3_work/check2_resolve.py` run
directly above, executed live this turn
```
risk-management -> {'source': 'rulebook', 'skill_dirs': [], 'skills': [], 'skill_sha': None}
```
canonical: the output line directly above. `risk-management` is an as-yet-unmigrated later-wave role (not touched by this wave's allowlist entries); it still resolves to `"rulebook"` with no `skill_dirs`/`skills`/`skill_sha` — the same value it would have returned before this wave's 10 allowlist additions, demonstrating the addition is additive and does not perturb resolution for roles outside the wave.

## Why

Batches the earlier pilot and wave patterns (#1761, #1766, #1769)
across the next 10 wave-3 rulebooks per the issue's "Batch mechanics"
instruction (one content PR for the wave's content-bearing roles, one
allowlist PR after). See the proposal's Rationale for why all 10 roles
migrate this wave (unlike the prior wave's `execution-observation`
exclusion) and why `product-discovery`'s pre-shaped `skills/*/SKILL.md`
files migrate as direct copies alongside its playbook-derived skills.

## Upstream / basis

docs/issue-1772/proposals/skill-axis-phase-3-wave-3.md (approved),
docs/issue-1772/reports/implementation/survey.md

## Rationale for deviations

canonical: docs/issue-1772/proposals/skill-axis-phase-3-wave-3.md:96-99
(this repo, read this turn) — step 2 reads "After that PR merges: ...
add 10 entries to ... allowlist.json", assuming the content PR is
merged before the allowlist PR is opened.

canonical: docs/issue-1766/reports/implementation.md:97-105 (this
repo, read this turn) — the wave-1 record already established that a
role session's `gh pr merge` against a PR it opened is refused by
`gh-guard.sh` (two-account model, contract v3 s8); this session did not
re-attempt the refused call and instead opened both PRs, leaving the
content PR for the human to merge first, matching the prior waves'
precedent.

canonical: `gh pr view 4 --repo tokenmaxxxer/skill-repository --json state` (skill-repository, executed live this turn) — the JSON output returned by this call reports state `OPEN`, i.e. unmerged, at the time this record was written.

The allowlist PR body (this branch's PR, opened after this record) is
written to name `skill-repository#4` as a merge-order prerequisite —
that PR-body text is the artifact a human reviewer sees before
merging, standing in for the merge step this session cannot perform.

The Check 2 equivalence evidence above is captured against the content
PR branch's own tip commit (`b01825e`), not against skill-repository's
`main` — same method the earlier waves' Check 2 evidence used.

canonical: docs/issue-1769/reports/implementation.md:254-256 (this
repo, read this turn) — the prior wave's own Check 2 evidence was
likewise captured via a local skill-repository clone pointed at
`<clone>/skills`, not by fetching skill-repository's merged `main`
branch — same method, applied here and re-executed live this turn (see
Check 2 above).

## What did not work

canonical: shell output from the first `python3 /tmp/wave3_work/check2_resolve.py` run this turn (this session's own transcript):
```
--skills: 모르는 스킬 market-analysis-competitor-mapping, market-analysis-evidence-rigor, market-analysis-five-forces, market-analysis-jtbd-fit, market-analysis-mece-proposal — 쓸 수 있는 이름: docs, skills
```
canonical: the error text quoted directly above. `spawn.resolved_skill_dirs()` fails closed on that error when `repo_root` is pointed at the skill-repository clone's top level instead of its `skills/` subdirectory — the first attempt used `/tmp/skill-repository` and expected the resolved skill names to be found, but the quoted error lists only `docs` and `skills` as available names. Corrected `repo_root` to `/tmp/skill-repository/skills` per `resolved_skill_dirs()`'s own docstring shape (`<repo_root>/<name>`), matching the earlier waves' method; re-running produced the expected `skill-repo` resolutions shown in Check 2 above.

canonical: `git diff --stat docs/specs/role-source-allowlist.json`
output from the first update attempt this turn (this session's own
transcript) — the first attempt to update
`docs/specs/role-source-allowlist.json` re-sorted the whole file
alphabetically: expected a minimal append-only diff matching the
earlier waves' diff shape, but the re-sort produced a much larger diff
touching every pre-existing entry's position, because the original
file was not already alphabetically ordered. Reverted via `git
checkout --` and redone as a plain dict-update-and-append, producing
the expected append-only diff (`git diff --stat` reported 70
insertions, 0 deletions after the fix).

## Open findings

None.
