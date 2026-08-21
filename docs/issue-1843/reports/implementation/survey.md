---
subject: issue-1843
role: implementation
kind: survey
loop_state: coding
---

# Current-state survey: user-discovery family (wave 2h)

Skip-condition note (scout-directive): scouting was skipped for this
survey. This wave is pure mechanical reuse of the recipe frozen in
docs/issue-1790/reports/implementation.md ("WAVE RECIPE" section) and
already applied verbatim across waves 2a-2d in the skill-repository
checkout's own commit history (below) — the spec (the frozen recipe
itself) leaves no design decision open for this wave; the only work is
applying the same steps to a new family's file set.

## Checkout and branch state

acceptance: `cd /tmp/skill-repository && git status && git log --oneline -5` — result:

```
현재 브랜치 issue-1830-wave2d-observability
브랜치가 'origin/issue-1830-wave2d-observability'에 맞게 업데이트된 상태입니다.
커밋할 사항 없음, 작업 폴더 깨끗함
b94ec38 Author procedural bodies for wave 2d: observability family (issue-1830) (#11)
d0bde0e Author procedural bodies for wave 2c: product-discovery family (issue-1812) (#10)
7279ec9 Author procedural bodies for wave 2b: release-engineering family (issue-1809) (#9)
a1701b5 Author procedural bodies for wave 2a: technical-feasibility family (issue-1802) (#8)
bb89bdc Author procedural bodies for pilot wave: upstream-defect-report + api-design (issue-1790) (#7)
```

canonical: `git status` output directly above — checked-out branch is
`issue-1830-wave2d-observability`, stale relative to this issue; phase 2
will branch fresh from the checkout's default branch after fetching, not
from this stale local branch.

acceptance: `cat scripts/procedure_authored_skills.txt` (run in
/tmp/skill-repository) — result: 44 lines, spanning the pilot + waves
2a-2d (technical-feasibility, release-engineering, product-discovery,
observability):

```
upstream-defect-report-comprehensibility
upstream-defect-report-convention
upstream-defect-report-subtraction
api-design-error-design
api-design-http-semantics
api-design-payload-design
api-design-resource-modeling
api-design-tool-landscape
api-design-versioning-evolution
technical-feasibility-build-vs-buy
technical-feasibility-build-vs-buy-dependency-health
technical-feasibility-license-and-regulatory-risk
technical-feasibility-license-scan
technical-feasibility-reversibility-and-spike-scoping
technical-feasibility-reversibility-tag
technical-feasibility-spike-report
technical-feasibility-stride-table
technical-feasibility-threat-model-disposition
technical-feasibility-verdict-and-timebox-selection
release-engineering-branching-release-strategy
release-engineering-changelog-entry-categorization
release-engineering-deployment-rollout-strategy
release-engineering-error-budget-policy
release-engineering-postmortem
release-engineering-readiness-checklist
release-engineering-release-cadence-and-toil
release-engineering-rollback-and-recovery
release-engineering-rollout-plan
release-engineering-semver-bump-selection
product-discovery-assumption-mapping
product-discovery-guardrail-metric-status
product-discovery-guardrail-metrics
product-discovery-hypothesis-preregistration
product-discovery-hypothesis-testing
product-discovery-jtbd-problem-framing
product-discovery-one-pager
product-discovery-opportunity-solution-tree
product-discovery-opportunity-solution-tree-branching
product-discovery-rice-ice-prioritization
observability-cardinality-budget
observability-explorability
observability-methodology-selection
observability-phase-trace
observability-signal-golden
observability-signal-use
```

Waves 2e (legal-compliance)/2f (conformance-review)/2g (ux-engineering)
per issues #1834/#1835/#1838 are recorded elsewhere in this repo's docs
tree — canonical: this conversation's `gitStatus` recent-commits list
(07a36fec, 2d1a2fbe, 9ed6cdfe) — but their landing state in the
skill-repository checkout is not this wave's concern; this survey only
needs the manifest file as it exists in the checkout right now, which
this wave extends incrementally per the recipe's step 4.

## Family membership

acceptance: `ls skills | grep -i user-discovery` (run in
/tmp/skill-repository) — result:

```
user-discovery
user-discovery-evidence-strength-tagging
user-discovery-follow-up-ladder-depth
user-discovery-question-design-past-behavior
user-discovery-saturation-stopping-rule
user-discovery-switch-timeline-causal-forces
user-discovery-verdict-prevalence-reporting
```

The issue's Acceptance criterion names exactly 6 family skills (the
`user-discovery-*` axis skills); `user-discovery` itself (no suffix) is
the family's overview/harness skill, not one of the 6 axis skills the
issue scopes in, and is excluded from this wave's write set — matches
precedent (each prior wave's manifest additions, listed above, touched
only a family's dash-suffixed axis skills, not any overview skill).

## Per-skill frontmatter/body shape (Shape A/B classification)

acceptance: for each of the 6 files, `grep -n "^## " skills/<dir>/SKILL.md`
plus `grep -c "^[0-9]\+\." skills/<dir>/SKILL.md` plus `wc -l
skills/<dir>/SKILL.md`, run in /tmp/skill-repository — result:

```
=== user-discovery-evidence-strength-tagging ===
12:## Rules
rules count: 9
wc: 30
=== user-discovery-follow-up-ladder-depth ===
12:## Rules
rules count: 9
wc: 30
=== user-discovery-question-design-past-behavior ===
12:## Rules
rules count: 10
wc: 32
=== user-discovery-saturation-stopping-rule ===
12:## Rules
rules count: 9
wc: 30
=== user-discovery-switch-timeline-causal-forces ===
12:## Rules
rules count: 9
wc: 30
=== user-discovery-verdict-prevalence-reporting ===
12:## Rules
rules count: 9
wc: 30
```

All 6 are **Shape A** (pilot/prior-wave terminology: no existing
`## Trigger`/`## Procedure`/`## Output shape` heading — only frontmatter,
a title, a "Research trail" paragraph, and `## Rules`). None is Shape B
(already procedure-shaped): canonical: the `grep -n "^## "` result
directly above lists exactly one `##`-level heading (`## Rules`) per
file, with no `## Trigger`/`## Procedure`/`## Output shape` line in any
of the 6. This matches every prior wave's finding (#1790's pilot survey,
and waves 2a-2d per the manifest above): the no-op/empty-state
acceptance clause has not fired in any wave to date, and does not fire
here either — all 6 skills require live authoring.

acceptance: `cat skills/user-discovery-evidence-strength-tagging/SKILL.md`
(run in /tmp/skill-repository) — result (excerpted; rules 2-9's full text
is unchanged in the working tree, quoted in full in the actual file):

```
---
name: user-discovery-evidence-strength-tagging
description: Use when you need guidance on Evidence-strength tagging: behavioral / recounted / opinion. Applies to the evidence-strength-tagging axis.
axis: evidence-strength-tagging
rule_count_floor: 8
---

# Evidence-strength tagging: behavioral / recounted / opinion

Research trail: behavioral vs. attitudinal interview evidence distinction (ventureforall.com, structured-interview bias literature on ScienceDirect); the Mom Test's evidence-quality framing. All searched this session.

## Rules

1. When a claim in the interview log is grounded in something the interviewee did and can point to ... source: https://www.ventureforall.com/p/from-assumptions-to-evidence-are
```

This is structurally identical to the pilot's `upstream-defect-report-*`
and `api-design-*` files the frozen recipe was authored against
(canonical: docs/issue-1790/reports/implementation.md, body excerpts
quoted in that record) — no family-specific structural divergence found.

## Rule-line inventory (pre-change, for the retention sweep)

derived: sum of the per-file `rules count:` values quoted in the shape
block above — 9 + 9 + 10 + 9 + 9 + 9 = 55 rule lines total across the 6
skills (`grep -c "^[0-9]\+\."`, which also counts
`**REMOVAL**:`-prefixed lines, consistent with how prior waves' own
retention sweeps counted rule lines — canonical:
docs/issue-1790/reports/implementation.md's Requirement-1 sweep block).

## Manifest and checker state

`scripts/check_skill_conformance.py` already carries the `--manifest`
opt-in check added in the pilot (#1790, canonical:
docs/issue-1790/reports/implementation.md "Extended
`scripts/check_skill_conformance.py`..." paragraph); no checker logic
change is in scope or needed for this wave (issue's own non-goals list
this explicitly). `scripts/procedure_authored_skills.txt` is append-only
across waves (canonical: the 44-line listing quoted above, spanning 5
prior commits with no removed lines); this wave adds exactly 6 lines to
it.

## Conclusion driving the proposal

No design decision is open: the frozen recipe steps (quoted verbatim in
docs/issue-1790/reports/implementation.md's "WAVE RECIPE" section —
insert Trigger/Procedure/Output-shape citing rule numbers, rewrite
`description:` from Trigger, append manifest, then run that same
section's checks) apply as-is to all 6 files, none of which are no-op
cases per the shape classification above.
