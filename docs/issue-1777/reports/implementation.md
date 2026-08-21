---
code_under_review:
  - docs/specs/role-source-allowlist.json
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# Phase-2 delivery: skill-axis phase-3 batch wave 4 (final) (#1777)

## Summary of work

Delivered the two PRs named in the approved proposal
(docs/issue-1777/proposals/skill-axis-phase-3-wave-4.md, approved via
`APPROVE issue-1777/implementation`):

1. **skill-repository content PR**: adds `SKILL.md`-shaped files
   (including `implementation-blueprint`'s `data/`+`scripts/` siblings)
   across all 13 wave-4 roles (release-engineering,
   requirements-engineering, risk-management, sales, secure-coding,
   security-threat-model, technical-feasibility, technical-writing,
   test-authoring, user-discovery, ux-engineering, implementation,
   conformance-review), one directory per skill under
   `skills/<role>-<axis>/`, each byte-equal to its rulebook source, no
   `hooks/` dir anywhere. `implementation` and `conformance-review` land
   last within this repo's allowlist commit per the issue's ordering
   requirement (commit-internal ordering; the content PR itself is one
   PR covering all 13 roles, per the proposal's Rationale).

   canonical: `gh pr view 5 --repo tokenmaxxxer/skill-repository --json state,number,url,headRefOid` (skill-repository, executed live this turn)
   ```
   {"headRefOid":"71fe2dee13bfe4028aa85f28de0bd6753d4231d9","number":5,"state":"OPEN","url":"https://github.com/tokenmaxxxer/skill-repository/pull/5"}
   ```
   canonical: the JSON output directly above (skill-repository, executed live this turn). State is `OPEN`, not merged — same fail-closed-ordering posture as every earlier wave; see Rationale for deviations below.

2. **on-the-record allowlist PR** (this branch): adds 13 entries to
   `docs/specs/role-source-allowlist.json` mapping all 13 wave-4 roles
   to their migrated skill names, `implementation` and
   `conformance-review` added last within the commit.

   canonical: `git diff main -- spawn.py` (this branch, executed live
   this turn), empty output — no `spawn.py` hunk in this branch's diff
   against `main`.

   canonical: `git diff --stat main -- docs/specs/role-source-allowlist.json` (this branch, executed live this turn)
   ```
   docs/specs/role-source-allowlist.json | 91 +++++++++++++++++++++++++++++++++++
   1 file changed, 91 insertions(+)
   ```

## Check 1 — per-rulebook recursive diff (byte-equal evidence)

canonical: `diff <rulebook source> <skill-repository SKILL.md>` run
live this turn, once per file, across all 13 roles' migrated files
(11 playbook-derived/single-file roles, `technical-feasibility` and
`conformance-review`'s pre-shaped `skills/*/SKILL.md` direct copies,
and `implementation`'s `blueprint` full-directory copy). Every diff
returned empty output.

```
=== release-engineering ===
  branching-release-strategy: empty diff
  changelog-entry-categorization: empty diff
  deployment-rollout-strategy: empty diff
  release-cadence-and-toil: empty diff
  rollback-and-recovery: empty diff
  semver-bump-selection: empty diff
  error-budget-policy (pre-shaped): empty diff
  postmortem (pre-shaped): empty diff
  readiness-checklist (pre-shaped): empty diff
  rollout-plan (pre-shaped): empty diff
=== requirements-engineering (single combined playbook/rules.md) ===
  rules: empty diff
=== risk-management ===
  aggregation-consolidation: empty diff
  appetite-tolerance-threshold: empty diff
  likelihood-impact-scale: empty diff
  monitoring-review-cadence: empty diff
  response-strategy-selection: empty diff
=== sales (sales-playbook/README.md excluded — plugin README, not a
     guidance source) ===
  objection-handling: empty diff
  pitch-scoping-and-messaging-handoff: empty diff
  qualification-and-discovery: empty diff
=== secure-coding ===
  authorization-access-control: empty diff
  cryptography-secrets-management: empty diff
  dependency-supply-chain-security: empty diff
  input-validation-injection-defense: empty diff
  session-authentication: empty diff
=== security-threat-model (single combined playbook file) ===
  threat-modeling-decision-rules: empty diff
=== technical-feasibility ===
  build-vs-buy-dependency-health: empty diff
  license-and-regulatory-risk: empty diff
  reversibility-and-spike-scoping: empty diff
  threat-model-disposition: empty diff
  verdict-and-timebox-selection: empty diff
  build-vs-buy (pre-shaped): empty diff
  license-scan (pre-shaped): empty diff
  reversibility-tag (pre-shaped): empty diff
  spike-report (pre-shaped): empty diff
  stride-table (pre-shaped): empty diff
=== technical-writing ===
  doc-type-selection: empty diff
  minimalism-scoping: empty diff
  persuasion-trust: empty diff
  structure-comprehension: empty diff
  style-guide-compliance: empty diff
  tool-landscape: empty diff
=== test-authoring (source at non-standard docs/specs/playbook/ path) ===
  isolation-and-fixture-strategy: empty diff
=== user-discovery ===
  evidence-strength-tagging: empty diff
  follow-up-ladder-depth: empty diff
  question-design-past-behavior: empty diff
  saturation-stopping-rule: empty diff
  switch-timeline-causal-forces: empty diff
  verdict-prevalence-reporting: empty diff
=== ux-engineering ===
  color-visibility: empty diff
  control-selection: empty diff
  layout-grouping: empty diff
  navigation-depth: empty diff
  research-log: empty diff
  surface-contrast: empty diff
=== implementation ===
  complexity-coupling-management: empty diff
  design-pattern-selection: empty diff
  performance-data-structure-choice: empty diff
  blueprint SKILL.md: empty diff
  blueprint data/antipatterns.csv: empty diff
  blueprint data/archetypes.csv: empty diff
  blueprint data/rules.csv: empty diff
  blueprint scripts/prep.py: empty diff
=== conformance-review ===
  requirement-extraction: empty diff
  sampling-derivation: empty diff
  traceability-and-evidence: empty diff
  verdict-assignment: empty diff
  verification-method-selection: empty diff
  finding-record (pre-shaped): empty diff
  severity-classification (pre-shaped): empty diff
```

canonical: `find skills/technical-feasibility-spike-report -type f` and
`find skills/conformance-review-finding-record -type f` (local
skill-repository clone, executed live this turn)
```
skills/technical-feasibility-spike-report/SKILL.md
skills/conformance-review-finding-record/SKILL.md
```
canonical: the two `find` outputs directly above. Each lists only
`SKILL.md` — confirms `spike-report`'s
`templates/spike-report-template.md` sibling and `finding-record`'s
`templates/finding-record-template.md` sibling were not migrated
(defect-verification precedent, same as prior waves).

canonical: `find skills/implementation-blueprint -type f` (local
skill-repository clone, executed live this turn)
```
skills/implementation-blueprint/SKILL.md
skills/implementation-blueprint/data/antipatterns.csv
skills/implementation-blueprint/data/archetypes.csv
skills/implementation-blueprint/data/rules.csv
skills/implementation-blueprint/scripts/prep.py
```
canonical: the `find` output directly above. `blueprint` migrated as a
full directory (`SKILL.md` + `data/` + `scripts/`), not `SKILL.md`
alone — per the proposal's Rationale (its own `SKILL.md` instructs the
reader to query the CSVs rather than paste them).

canonical: `grep -rlE "re\.compile\(r'[^']{20,}" <clone> --include='*.py' --include='*.sh'`, executed live this turn across all 13 clones — every hit inspected is a target-path regex, a required-heading/label regex, a required-field/proximity regex, or a proposal/record-shape structural check (e.g. release-engineering's `proposal-fields-gate.sh`, requirements-engineering's `traceability-matrix-gate.sh`/`req-id-gate.sh`, sales's `qualification-gate.sh`/`stage-definitions-gate.sh`, security-threat-model's per-phase `methodology-gate.sh` + `sequence-gate.sh`, implementation's own `survey-order-gate.sh`/`coding-progress-gate.sh`/`record-shape-gate.sh`/`proposal-shape-gate.sh`, conformance-review's `traceability-gate.sh`/`severity-gate.sh`/`closed-checks-gate.sh`). No demoted-guidance appendices were added this wave: every matched hook file is a structural record-shape check, not new domain guidance absent from the playbook text, and no band-word/formula-style domain check appears in any wave-4 role's hooks.

## Check 2 — `resolve_role_source()` live output, post-allowlist-merge

canonical: `python3 /tmp/wave4_work/check2_resolve.py` (this branch,
`spawn.resolve_role_source()` called directly with `repo_root` pointed
at the local skill-repository clone's `skills/` dir), executed live
this turn
```
release-engineering -> {'source': 'skill-repo', 'skills': ['release-engineering-branching-release-strategy', 'release-engineering-changelog-entry-categorization', 'release-engineering-deployment-rollout-strategy', 'release-engineering-release-cadence-and-toil', 'release-engineering-rollback-and-recovery', 'release-engineering-semver-bump-selection', 'release-engineering-error-budget-policy', 'release-engineering-postmortem', 'release-engineering-readiness-checklist', 'release-engineering-rollout-plan'], 'skill_sha': '71fe2de'}
requirements-engineering -> {'source': 'skill-repo', 'skills': ['requirements-engineering-rules'], 'skill_sha': '71fe2de'}
risk-management -> {'source': 'skill-repo', 'skills': ['risk-management-aggregation-consolidation', 'risk-management-appetite-tolerance-threshold', 'risk-management-likelihood-impact-scale', 'risk-management-monitoring-review-cadence', 'risk-management-response-strategy-selection'], 'skill_sha': '71fe2de'}
sales -> {'source': 'skill-repo', 'skills': ['sales-objection-handling', 'sales-pitch-scoping-and-messaging-handoff', 'sales-qualification-and-discovery'], 'skill_sha': '71fe2de'}
secure-coding -> {'source': 'skill-repo', 'skills': ['secure-coding-authorization-access-control', 'secure-coding-cryptography-secrets-management', 'secure-coding-dependency-supply-chain-security', 'secure-coding-input-validation-injection-defense', 'secure-coding-session-authentication'], 'skill_sha': '71fe2de'}
security-threat-model -> {'source': 'skill-repo', 'skills': ['security-threat-model-threat-modeling-decision-rules'], 'skill_sha': '71fe2de'}
technical-feasibility -> {'source': 'skill-repo', 'skills': ['technical-feasibility-build-vs-buy-dependency-health', 'technical-feasibility-license-and-regulatory-risk', 'technical-feasibility-reversibility-and-spike-scoping', 'technical-feasibility-threat-model-disposition', 'technical-feasibility-verdict-and-timebox-selection', 'technical-feasibility-build-vs-buy', 'technical-feasibility-license-scan', 'technical-feasibility-reversibility-tag', 'technical-feasibility-spike-report', 'technical-feasibility-stride-table'], 'skill_sha': '71fe2de'}
technical-writing -> {'source': 'skill-repo', 'skills': ['technical-writing-doc-type-selection', 'technical-writing-minimalism-scoping', 'technical-writing-persuasion-trust', 'technical-writing-structure-comprehension', 'technical-writing-style-guide-compliance', 'technical-writing-tool-landscape'], 'skill_sha': '71fe2de'}
test-authoring -> {'source': 'skill-repo', 'skills': ['test-authoring-isolation-and-fixture-strategy'], 'skill_sha': '71fe2de'}
user-discovery -> {'source': 'skill-repo', 'skills': ['user-discovery-evidence-strength-tagging', 'user-discovery-follow-up-ladder-depth', 'user-discovery-question-design-past-behavior', 'user-discovery-saturation-stopping-rule', 'user-discovery-switch-timeline-causal-forces', 'user-discovery-verdict-prevalence-reporting'], 'skill_sha': '71fe2de'}
ux-engineering -> {'source': 'skill-repo', 'skills': ['ux-engineering-color-visibility', 'ux-engineering-control-selection', 'ux-engineering-layout-grouping', 'ux-engineering-navigation-depth', 'ux-engineering-research-log', 'ux-engineering-surface-contrast'], 'skill_sha': '71fe2de'}
implementation -> {'source': 'skill-repo', 'skills': ['implementation-complexity-coupling-management', 'implementation-design-pattern-selection', 'implementation-performance-data-structure-choice', 'implementation-blueprint'], 'skill_sha': '71fe2de'}
conformance-review -> {'source': 'skill-repo', 'skills': ['conformance-review-requirement-extraction', 'conformance-review-sampling-derivation', 'conformance-review-traceability-and-evidence', 'conformance-review-verdict-assignment', 'conformance-review-verification-method-selection', 'conformance-review-finding-record', 'conformance-review-severity-classification'], 'skill_sha': '71fe2de'}
```
canonical: the `check2_resolve.py` output directly above, together with
the `headRefOid` (`71fe2dee1...`) cited in Summary item 1 above. The
`skill_sha` reported here (`71fe2de`) is the short form of that same
commit — the content PR branch's own tip, not a post-merge sha (see
Rationale for deviations below for why).

### `implementation` / `conformance-review` — dedicated smoke (issue-mandated)

canonical: the `check2_resolve.py` output above, `implementation` and
`conformance-review` lines. Both resolve `source: skill-repo` with
`skill_sha: 71fe2de`, confirming both highest-traffic roles map
correctly before the dry-run smoke below.

canonical: `MUSTER_SKILL_REPO=/tmp/skill-repository/skills python3 spawn.py implementation "smoke: dry-run assembly check for skill-repo-mapped implementation role (issue-1777 wave-4)" --dry-run` (this branch, executed live this turn)
```
{
  "sandbox": {
    "enabled": false,
    "network": {
      "allowedDomains": [
        "api.anthropic.com",
        "*.github.com",
        "github.com"
      ]
    }
  },
  "decides": "승인된 범위 → 동작 코드 (신규 구현)",
  "use_when": "스펙/제안이 승인됐고 신규 구현이 필요할 때. 검증은 안 한다 — 자기 주장 확인(빌드·자기 테스트 1회)까지만",
  "produces": "src/·test/ 코드, build proposal, what-did-not-work log, closed_checks entries, coding record",
  "write_scope": [
    "src/**",
    "test/**",
    "tests/**"
  ],
  "record_fields": {
    "loop_state": [
      "scope-proposed",
      "scope-approved",
      "in-progress",
      "refused",
      "not-needed",
      "cannot-verify",
      "landed"
    ]
  },
  "enabledPlugins": {
    "on-the-record@tokenmaxxxer": false
  },
  "permissions": { "...": "unchanged sandbox/tooling allowlist, elided for brevity" },
  "hooks": { "...": "role hook wiring unchanged from role_settings(), elided for brevity" },
  "model": "sonnet"
}
--model sonnet
```
canonical: the `--dry-run` output directly above (this branch, executed
live this turn) — this is the exact command named in issue #1777's
acceptance item 2. Full JSON preserved at
`/tmp/wave4_work/dryrun_output.txt`; the `permissions`/`hooks` blocks
are elided here only for record length, not truncated in the actual
run.

canonical: `spawn.py:7224` (this branch, read this turn), own comment
in the `--dry-run` branch of `main()`: "`--dry-run` 은 세션을 안
태운다... `spawn_cmd` 는 이 dry-run 경로를 안 타므로" — `role_settings()`
(what `--dry-run` calls) assembles sandbox/model/permission settings
only; `spawn_cmd()`, which appends the `--plugin-dir` argv mounting
`role_source`'s resolved skill dirs, is not invoked on the `--dry-run`
path. The Check 2 `resolve_role_source()` call above is what actually
proves the skill-repo plugin-mount resolution — this `--dry-run`
invocation is the literal command the issue names, confirming the
settings layer (model, sandbox, hooks) assembles without error for the
now-mapped `implementation` role.

## Check 3 — control unmapped role

canonical: the `check2_resolve.py` output above, final block
```
execution-observation -> {'source': 'rulebook', 'skill_dirs': [], 'skills': [], 'skill_sha': None}
```
canonical: the output line directly above, together with
docs/issue-1769/proposals/skill-axis-phase-3-wave-2.md (this repo, read
this turn), which names `execution-observation` as that wave's
excluded, still-unmapped role. `execution-observation` still resolves
to `"rulebook"` with no `skill_dirs`/`skills`/`skill_sha` — the same
value it would have returned before this wave's 13 allowlist additions
— demonstrating the addition is additive and does not perturb
resolution for roles outside the wave.

## Why

canonical: issue #1777 body, read via `gh issue view 1777` this turn:
```
Same per-rulebook 3 checks and batch mechanics.
```

Batches the earlier pilot and wave patterns (#1761, #1766, #1769,
#1772) across the final 13 wave-4 rulebooks per that instruction, plus
the issue-mandated extra smoke on `implementation`/`conformance-review`
as this wave's own reviewer role. See the proposal's Rationale for why
`blueprint`'s `data/`+`scripts/` siblings migrate (unlike every prior
wave's excludable `templates/` sibling) and why `implementation`/
`conformance-review` land last within one allowlist commit rather than
a second PR.

## Upstream / basis

docs/issue-1777/proposals/skill-axis-phase-3-wave-4.md (approved),
docs/issue-1777/reports/implementation/survey.md

## Rationale for deviations

canonical: docs/issue-1777/proposals/skill-axis-phase-3-wave-4.md:97-99
(this repo, read this turn) — step 2 reads "After that PR merges: ...
add 13 entries to ... allowlist.json", assuming the content PR is
merged before the allowlist PR is opened.

canonical: docs/issue-1766/reports/implementation.md:97-105 (this
repo, read this turn) — the wave-1 record already established that a
role session's `gh pr merge` against a PR it opened is refused by
`gh-guard.sh` (two-account model, contract v3 s8); this session did not
re-attempt the refused call and instead opened both PRs, leaving the
content PR for the human to merge first, matching every prior wave's
precedent.

canonical: `gh pr view 5 --repo tokenmaxxxer/skill-repository --json state` (skill-repository, executed live this turn) — reports state `OPEN`, i.e. unmerged, at the time this record was written.

canonical: this branch's own allowlist PR body (opened after this
record) — written to name `skill-repository#5` as a merge-order
prerequisite, the artifact a human reviewer sees before merging,
standing in for the merge step this session cannot perform.

canonical: docs/issue-1772/reports/implementation.md:187-190 (this
repo, read this turn) — the wave-3 record's Check 2 evidence was
likewise captured via a local skill-repository clone pointed at
`<clone>/skills`, not by fetching a merged branch of the remote.

canonical: the Check 2 `check2_resolve.py` output above (`skill_sha:
'71fe2de'`, matching the `headRefOid` cited in Summary item 1) — this
session applied the same local-clone method, re-executed live this
turn, capturing the Check 2 equivalence evidence against the content
PR branch's own tip commit rather than a post-merge sha.

canonical: `spawn.py:7224` (this branch, read this turn), same citation
as under the `--dry-run` output in Check 2 above — this session's
`--dry-run` smoke is narrower than "confirms plugin-mount assembly"
might suggest: `--dry-run` exercises `role_settings()` only, not
`spawn_cmd()`'s `--plugin-dir` argv construction. This session ran the
exact command the issue's acceptance item 2 names
(`spawn --dry-run` of `implementation`, output pasted in Check 2 above)
and paired it with a direct `resolve_role_source()` call (also pasted
in Check 2 above — the function that actually determines the
plugin-mount source) to cover what the CLI flag itself does not
exercise.

## What did not work

canonical: this session's own transcript — the first candidate tried
for the Check 3 control role, `customer-support`, was expected to be
unmapped (matching this session's initial read of the allowlist file,
which listed 30 role keys with no `customer-support` entry visible at
a glance) but resolved `source: skill-repo` because it was mapped by an
earlier wave — the working file on disk in fact carried 43 keys
including `customer-support` at the time Check 3 ran. Re-checked via
`jq -r 'keys[]' docs/specs/role-source-allowlist.json` against
docs/issue-1769/proposals/skill-axis-phase-3-wave-2.md, which names
`execution-observation` as that wave's excluded (still-unmapped) role;
switched the control-role check to `execution-observation`, which
correctly resolved `source: rulebook` (see Check 3 above).

## Open findings

None.
