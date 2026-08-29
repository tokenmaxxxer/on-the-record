---
issue: 2601
role: technical-writing-structure-comprehension+conformance-review-sampling-derivation-5178eb4a
author: technical-writing-structure-comprehension+conformance-review-sampling-derivation-5178eb4a
skills: technical-writing-structure-comprehension (skill-repository(297e350)), conformance-review-sampling-derivation (skill-repository(297e350))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: complete
upstream:
  - path: gh issue view 2601 --repo tokenmaxxxer/on-the-record
    sha: same-commit
code_under_review: skill-repository (git@github.com:tokenmaxxxer/skill-repository.git), base 5da544f3bc0ca89f65e1628f5480fb169d35e08a
type: docs-vocabulary-sweep
breaking: false
verdict: n/a
---

# issue-2601 — technical-writing-structure-comprehension+conformance-review-sampling-derivation-5178eb4a record

## What was done

Classified all 384 occurrences of `role`/`역할` (case-insensitive `\brole\b`
or `역할`) across skill-repository's 116 affected files, and edited only the
occurrences that describe tokenmaxxxer's retired spawn/identity axis.

canonical: `gh issue view 2601` (title, Ask, Acceptance, Non-goals sections quoted above)

derived: `cd ~/skill-registry/skills && git ls-files -z | xargs -0 grep -noiE '\brole\b|역할' | wc -l` — result: 384, across 116 files (`git ls-files -z | xargs -0 grep -lZi ...` file count) — matches the issue's own count exactly, confirming no drift on the branch (base commit `5da544f3bc0ca89f65e1628f5480fb169d35e08a`, pulled clean before starting).

Classification method: every one of the 384 occurrences was read in its
original-file context (full `grep -n -C1`/`-C2` context dumps, cross-checked
against the surrounding SKILL.md/references/rules.md prose) and assigned one
of three dispositions:

- **axis-reference** — self-referential language describing *this system's*
  spawn/identity model: "this role's own `produces` field", "role spec",
  "the role's record", "role directive", `role:` YAML frontmatter naming a
  spawned identity, "role intake", "contract v3 role: X", "another role's
  record" / "sibling role" (cross-role handoff), and compact compounds like
  "growth-role"/"discovery-role"/"ops-role" naming an in-repo skill variant.
  227 occurrences, across 81 files.
- **ordinary-English** — genuine subject-matter use of the word, unrelated to
  this system: ARIA `role` attribute (accessibility-aria-and-contrast-rules,
  design-artifact-html-demo, ux-engineering-control-selection,
  interaction-design-form-control-and-layout's WCAG/decorative-icon lines),
  RBAC/ABAC access-control role (secure-coding-authorization-access-control,
  secure-coding-session-authentication, release-engineering-release-cadence's
  role-based access control), organizational/job role (
  org-design-role-competency-definition, org-design-hiring-rubric,
  org-design-team-shape-selection, content-strategy RACI, customer-support
  escalation/five-whys tiering, marketing-segment-targeting, ux-engineering
  frontstage-backstage staff role, fmea/stride "person or role" acceptor),
  grammatical role (localization-string-externalization), technical/
  architecture role (code-architecture, architecture-module-boundary-
  definition, implementation-blueprint archetypes), character/game role
  (game-character-rendering-composition, game-ui-board-and-lane-layout),
  Agile user-story `<role>` template (requirements-quality), model-routing's
  own tier vocabulary (orchestrator/reasoner/executor), pricing's "anchor
  role" (decoy-pricing psychology term), and a handful of individually-read
  borderline calls (adversarial-review's "**Role**:" persona heading,
  ux-engineering-navigation-depth's UI-persona "multi-role nav",
  market-analysis-evidence-rigor's "restrict its role to" (a cited source's
  evidentiary function), implementation-audit's RBAC pseudocode example).
  145 occurrences, across 35 files (see the Open findings section below for
  the borderline calls' reasoning).
- **ordinary-English (historical citation, out of scope)** — literal
  citations, inside skill-repository's own prose, to dated research
  artifacts whose names contain `role-practice`/`role-interaction`
  (`docs/reports/research/2026-07-27-role-{practice,interaction}/...` —
  these paths are untracked in both skill-repository and the on-the-record
  checkout this session has access to; they were never verified to exist,
  only cited as-is by the skill files being read). The issue's own
  Non-goals list "Historical records in any repo — permanently out of
  scope"; rewriting the citing text's slug would either invent a fabricated
  renamed filename or silently break a working pointer to that unrenamed
  historical artifact. 12 occurrences, across 10 files.

Edit mechanism: for every axis-reference occurrence, the exact source line
was rewritten in place, replacing the word only (`role`→`skill`,
`Role`→`Skill`, case-preserving) while leaving the rest of the sentence
byte-identical — chosen because issue #2670 already renamed
`CLAUDE_ROLE`→`CLAUDE_SKILL` (write side + on-the-record read side), so
"skill" is the current, not invented, name for the same concept these
self-references were pointing at. Three occurrences citing literal external
file paths that still contain the substring `role` in their name
(`docs/specs/role-handoff-contract.md` ×2, `on-the-record/hooks/role-spec-
reference-guard.sh` ×1 — both untracked in the on-the-record checkout this
session has access to; renamed-or-not could not be confirmed, so no
`skill-`-prefixed replacement path was invented) were hand-reworded to
describe the artifact generically instead of asserting an unverified
renamed path.

derived: `cd ~/skill-registry/skills && git diff --stat | tail -1` — result: `81 files changed, 216 insertions(+), 216 deletions(-)`

## Acceptance checks (verbatim from the issue)

**Check 1 — table totalling 384, every occurrence classified:**
see the full 116-row table below. `derived: python3 /tmp/gen_table.py` (script
groups the 384 ground-truth occurrences from
`git ls-files -z | xargs -0 grep -noiE '\brole\b|역할'` by file, cross-
references each file/line against the classification map built while
reading every occurrence in context) — result: `TOTAL: 384`, 116 files, 0
unclassified.

**Check 2 — axis-reference subset re-grepped, must be 0:**
derived: `cd ~/skill-registry/skills && git ls-files -z | xargs -0 grep -noiE '\brole\b|역할' | wc -l` — result: 157 (= 145 ordinary + 12 historical-citation from the table; 0 from the 227-occurrence axis-reference subset, which is what the check requires). Cross-checked per-occurrence, not just by aggregate count: a verification script re-read the post-edit text at every one of the 384 original (file, line) locations and asserted (a) every occurrence classified axis-reference no longer matches `role`/`역할` on that line, and (b) every occurrence classified ordinary-English/historical still does — `derived: python3 -c "<verification script, printed in full further down this record's tooling trail>"` — result: `problems: 0` (0 mismatches out of 384).

**Check 3 — `git diff` limited to files classified ordinary-English must show nothing:**
derived: `comm -12 <(sort <pure-ordinary-and-historical-only file list>) <(git diff --name-only | sort)` — result: empty intersection. 35 files are classified 100% ordinary-English/historical (no axis-reference occurrence); none of the 35 appear in `git diff --name-only`. The other 81 files in the diff are exactly the 81 files that contain at least one axis-reference occurrence — derived: `diff <(sort <axis-files-from-table>) <(git diff --name-only | sed 's#^skills/##' | sort)` — result: `MATCH: diff files == axis files exactly`. For the mixed files among those 81, the classification table's per-line note lists exactly which lines are ordinary-English (unedited) versus axis-reference (edited); Check 2's per-occurrence verification confirms the ordinary-English lines inside mixed files are unchanged.

## Full classification table (116 files, 384 occurrences)

| file | count | disposition | note |
|---|---|---|---|
| `accessibility-aria-and-contrast-rules/SKILL.md` | 19 | ordinary-English |  |
| `accessibility-aria-and-contrast-rules/references/rules.md` | 21 | ordinary-English |  |
| `adversarial-review/SKILL.md` | 1 | ordinary-English |  |
| `api-design-tool-landscape/SKILL.md` | 2 | axis-reference | edited (lines 18,19) |
| `architecture-interface-contract-shape/SKILL.md` | 1 | axis-reference | edited (lines 18) |
| `architecture-module-boundary-definition/SKILL.md` | 2 | ordinary-English |  |
| `architecture-module-boundary-definition/references/rules.md` | 1 | ordinary-English |  |
| `blameless-postmortem/SKILL.md` | 2 | axis-reference | edited (lines 13) |
| `brand-design-brand-consistency-governance/SKILL.md` | 1 | axis-reference | edited (lines 19) |
| `brand-design-brand-identity-strategy/SKILL.md` | 2 | axis-reference | edited (lines 19,21) |
| `brand-design-color-visibility/SKILL.md` | 1 | ordinary-English |  |
| `code-architecture/references/rules.md` | 1 | ordinary-English |  |
| `conformance-review-finding-record/SKILL.md` | 1 | axis-reference | edited (lines 18) |
| `conformance-review-finding-record/references/rules.md` | 9 | mixed | 7 axis-reference, edited (lines 66,91,96,97,104,110,137); 2 ordinary-English (historical citation, out of scope), unedited (lines 12,51) |
| `conformance-review-requirement-extraction/references/rationalizations.md` | 1 | axis-reference | edited (lines 12) |
| `conformance-review-severity-classification/SKILL.md` | 3 | mixed | 1 axis-reference, edited (lines 22); 2 ordinary-English (historical citation, out of scope), unedited (lines 63,76) |
| `conformance-review-verdict-assignment/SKILL.md` | 4 | axis-reference | edited (lines 76,84,99,111) |
| `content-strategy-content-governance-ownership/SKILL.md` | 1 | ordinary-English |  |
| `customer-support-escalation-path/SKILL.md` | 3 | ordinary-English |  |
| `customer-support-five-whys-recurring-scope/SKILL.md` | 5 | ordinary-English |  |
| `customer-support-research-log/SKILL.md` | 1 | axis-reference | edited (lines 11) |
| `data-engineering-data-quality/SKILL.md` | 1 | ordinary-English |  |
| `defect-verification-evidence-artifact-completeness/SKILL.md` | 1 | axis-reference | edited (lines 103) |
| `defect-verification-independence-from-upstream-verdicts/SKILL.md` | 6 | axis-reference | edited (lines 38,59,65,67,73) |
| `design-artifact-html-demo/SKILL.md` | 2 | ordinary-English |  |
| `experiment-trust/SKILL.md` | 1 | axis-reference | edited (lines 14) |
| `finance-unit-economics-evidence-chain/SKILL.md` | 2 | axis-reference | edited (lines 107,108) |
| `finance-unit-economics-proposal-shape/SKILL.md` | 1 | axis-reference | edited (lines 87) |
| `fmea/SKILL.md` | 1 | ordinary-English |  |
| `game-character-rendering-composition/SKILL.md` | 6 | ordinary-English |  |
| `game-ui-board-and-lane-layout/SKILL.md` | 1 | ordinary-English |  |
| `hypothesis-testing/SKILL.md` | 1 | axis-reference | edited (lines 14) |
| `implementation-audit/references/surface-patterns.md` | 1 | ordinary-English |  |
| `implementation-blueprint/data/archetypes.csv` | 2 | ordinary-English |  |
| `incident-response-rca-method-selection/SKILL.md` | 1 | axis-reference | edited (lines 21) |
| `incident-response-severity-classification-scoping/SKILL.md` | 1 | axis-reference | edited (lines 22) |
| `incident-response-tool-landscape/SKILL.md` | 5 | axis-reference | edited (lines 6,21,22,34,88) |
| `interaction-design-form-control-and-layout/references/rules.md` | 4 | mixed | 2 axis-reference, edited (lines 53,115); 2 ordinary-English, unedited (lines 66,90) |
| `issue-retrospective-timeline-comprehensibility-and-subtraction-rules/SKILL.md` | 18 | axis-reference | edited (lines 4,26,32,35,38,52,56,70,88,89,91,92,94,95,101) |
| `issue-retrospective-timeline-comprehensibility-and-subtraction-rules/references/rules.md` | 11 | axis-reference | edited (lines 10,17,31,38,51,55,61,109,110,121) |
| `knowledge-management-taxonomy-tagging/SKILL.md` | 2 | axis-reference | edited (lines 84) |
| `localization-string-externalization/SKILL.md` | 3 | ordinary-English |  |
| `localization-text-expansion-and-layout/SKILL.md` | 1 | axis-reference | edited (lines 101) |
| `market-analysis-competitor-mapping/SKILL.md` | 1 | axis-reference | edited (lines 20) |
| `market-analysis-evidence-rigor/SKILL.md` | 4 | mixed | 2 axis-reference (2 occurrences on line 81), edited (lines 19,81); 1 ordinary-English, unedited (lines 82) |
| `market-analysis-five-forces/SKILL.md` | 1 | axis-reference | edited (lines 21) |
| `market-analysis-jtbd-fit/SKILL.md` | 2 | axis-reference | edited (lines 20,98) |
| `market-analysis-mece-proposal/SKILL.md` | 7 | axis-reference | edited (lines 6,29,57,67,83,123 — 2 occurrences on line 83) |
| `marketing-segment-targeting/SKILL.md` | 3 | ordinary-English |  |
| `ml-engineering-ml-test-score-scoring/SKILL.md` | 1 | axis-reference | edited (lines 20) |
| `model-routing/SKILL.md` | 2 | ordinary-English |  |
| `model-routing/references/rules.md` | 1 | ordinary-English |  |
| `observability-methodology-selection/SKILL.md` | 1 | axis-reference | edited (lines 19) |
| `org-design-hiring-rubric-structured-interview/SKILL.md` | 8 | ordinary-English |  |
| `org-design-role-competency-definition/SKILL.md` | 12 | ordinary-English | directory/skill name itself is untouched |
| `org-design-team-shape-selection/SKILL.md` | 5 | ordinary-English |  |
| `pr-communications-message-planning-and-evaluation-rules/SKILL.md` | 1 | axis-reference | edited (lines 15) |
| `pr-communications-message-planning-and-evaluation-rules/references/rules.md` | 1 | axis-reference | edited (lines 135) |
| `pricing-tier-structure/SKILL.md` | 4 | mixed | 2 axis-reference, edited (lines 19,90); 2 ordinary-English ("anchor role" — decoy-pricing term), unedited (lines 41,75) |
| `pricing-verdict-report/SKILL.md` | 1 | axis-reference | edited (lines 114) |
| `product-discovery-assumption-mapping/SKILL.md` | 3 | mixed | 2 axis-reference, edited (lines 43,57); 1 ordinary-English (historical citation, out of scope), unedited (lines 21) |
| `product-discovery-guardrail-metrics/SKILL.md` | 4 | mixed | 3 axis-reference, edited (lines 4,29,54); 1 ordinary-English (historical citation, out of scope), unedited (lines 22) |
| `product-discovery-hypothesis-preregistration/SKILL.md` | 1 | axis-reference | edited (lines 19) |
| `product-discovery-hypothesis-testing/SKILL.md` | 6 | axis-reference | edited (lines 4,15,26,36,116 — 2 occurrences on line 116) |
| `product-discovery-hypothesis-testing/references/rules.md` | 2 | axis-reference | edited (lines 47,49) |
| `product-discovery-jtbd-problem-framing/SKILL.md` | 1 | ordinary-English |  |
| `product-discovery-one-pager/SKILL.md` | 4 | mixed | 3 axis-reference, edited (lines 6,52,84); 1 ordinary-English (historical citation, out of scope), unedited (lines 21) |
| `product-discovery-opportunity-solution-tree/SKILL.md` | 1 | ordinary-English (historical citation, out of scope) | unedited |
| `product-discovery-rice-ice-prioritization/SKILL.md` | 3 | axis-reference | edited (lines 19,63,65) |
| `refactoring-legacy-seam-selection/SKILL.md` | 1 | axis-reference | edited (lines 18) |
| `refactoring-legacy-verification-cadence/SKILL.md` | 1 | axis-reference | edited (lines 19) |
| `release-engineering-deployment-rollout-strategy/SKILL.md` | 1 | axis-reference | edited (lines 8) |
| `release-engineering-error-budget-policy/SKILL.md` | 4 | mixed | 3 axis-reference, edited (lines 4,10,20); 1 ordinary-English (historical citation, out of scope), unedited (lines 64) |
| `release-engineering-postmortem/SKILL.md` | 2 | mixed | 1 axis-reference, edited (lines 4); 1 ordinary-English (historical citation, out of scope), unedited (lines 66) |
| `release-engineering-readiness-checklist/SKILL.md` | 6 | mixed | 5 axis-reference, edited (lines 4,15,50,51,88); 1 ordinary-English (historical citation, out of scope), unedited (lines 25) |
| `release-engineering-readiness-checklist/references/rules.md` | 3 | axis-reference | edited (lines 9,34,36) |
| `release-engineering-release-cadence-and-toil/SKILL.md` | 2 | ordinary-English |  |
| `release-engineering-rollout-plan/SKILL.md` | 2 | mixed | 1 axis-reference, edited (lines 4); 1 ordinary-English (historical citation, out of scope), unedited (lines 70) |
| `requirements-engineering-rules/SKILL.md` | 3 | axis-reference | edited (lines 8,23 — 2 occurrences on line 23) |
| `requirements-engineering-rules/references/rules.md` | 8 | axis-reference | edited (lines 73,76,86,109,112,149,212,213) |
| `requirements-quality/SKILL.md` | 8 | ordinary-English |  |
| `research-evidence-discipline/SKILL.md` | 2 | axis-reference | edited (lines 20,60) |
| `sales-pitch-scoping-and-messaging-handoff/SKILL.md` | 1 | axis-reference | edited (lines 83) |
| `secure-coding-authorization-access-control/SKILL.md` | 15 | ordinary-English |  |
| `secure-coding-session-authentication/SKILL.md` | 1 | ordinary-English |  |
| `security-threat-model-threat-modeling-decision-rules/SKILL.md` | 1 | axis-reference | edited (lines 27) |
| `security-threat-model-threat-modeling-decision-rules/references/rules.md` | 1 | axis-reference | edited (lines 117) |
| `stride/SKILL.md` | 1 | ordinary-English |  |
| `tech-feasibility/SKILL.md` | 1 | axis-reference | edited (lines 13) |
| `technical-feasibility-build-vs-buy-dependency-health/SKILL.md` | 1 | axis-reference | edited (lines 10) |
| `technical-feasibility-build-vs-buy-dependency-health/references/rules.md` | 7 | axis-reference | edited (lines 12,34,37,45,47,56,77) |
| `technical-feasibility-build-vs-buy/SKILL.md` | 2 | axis-reference | edited (lines 4,22) |
| `technical-feasibility-license-and-regulatory-risk/references/rules.md` | 11 | axis-reference | edited (lines 54,59,66,75,78,90,98,101,111,115,122) |
| `technical-feasibility-license-scan/SKILL.md` | 2 | axis-reference | edited (lines 4,20) |
| `technical-feasibility-reversibility-and-spike-scoping/references/rules.md` | 5 | axis-reference | edited (lines 71,72,80,99,101) |
| `technical-feasibility-reversibility-tag/SKILL.md` | 1 | axis-reference | edited (lines 83) |
| `technical-feasibility-spike-report/SKILL.md` | 4 | axis-reference | edited (lines 4,28,104,144) |
| `technical-feasibility-stride-table/SKILL.md` | 3 | axis-reference | edited (lines 4,21,24) |
| `technical-feasibility-threat-model-disposition/references/rules.md` | 9 | axis-reference | edited (lines 14,49,55,65,66,77,79,95,116) |
| `technical-feasibility-verdict-and-timebox-selection/references/rules.md` | 11 | axis-reference | edited (lines 15,26,38,49,59,60,72,83,92,104,117) |
| `technical-writing-doc-type-selection/SKILL.md` | 1 | axis-reference | edited (lines 20) |
| `technical-writing-minimalism-scoping/SKILL.md` | 2 | axis-reference | edited (lines 20,159) |
| `technical-writing-persuasion-trust/SKILL.md` | 1 | axis-reference | edited (lines 145) |
| `technical-writing-tool-landscape/SKILL.md` | 1 | axis-reference | edited (lines 88) |
| `test-authoring-isolation-and-fixture-strategy/SKILL.md` | 1 | axis-reference | edited (lines 14) |
| `upstream-defect-report-comprehensibility/SKILL.md` | 1 | axis-reference | edited (lines 15) — `role:` frontmatter |
| `upstream-defect-report-convention/SKILL.md` | 1 | axis-reference | edited (lines 15) — `role:` frontmatter |
| `upstream-defect-report-subtraction/SKILL.md` | 1 | axis-reference | edited (lines 14) — `role:` frontmatter |
| `user-discovery-verdict-prevalence-reporting/SKILL.md` | 1 | axis-reference | edited (lines 69) |
| `ux-engineering-control-selection/SKILL.md` | 2 | ordinary-English |  |
| `ux-engineering-control-selection/references/rules.md` | 1 | ordinary-English |  |
| `ux-engineering-navigation-depth/SKILL.md` | 2 | ordinary-English | UI-persona "user roles"/"multi-role nav", not self-referential |
| `ux-engineering-service-design-frontstage-backstage-separation/SKILL.md` | 4 | ordinary-English |  |
| `verify-finding-record/SKILL.md` | 2 | axis-reference | edited (lines 19,42) |
| `verify-finding-record/references/rules.md` | 5 | axis-reference | edited (lines 39,92,97,99,124) — line 39 hand-reworded (real-path citation) |
| `verify-severity-classification/SKILL.md` | 4 | axis-reference | edited (lines 22,23,68,104) — line 22 hand-reworded (real-path citation) |

TOTAL: 384 (227 axis-reference edited, 145 ordinary-English unedited, 12 ordinary-English historical-citation unedited)

## Why

The issue's own criterion for this repo (as opposed to #2600's flat zero in
the two enforcement repos) is "zero occurrences referring to tokenmaxxxer's
retired axis, leaving ordinary English alone" — judgment per site, not a
mechanical strip. Reading every occurrence in its original-file context
(rather than pattern-matching on the word alone) was the only way to
separate ~200 self-referential "this role's own X field" boilerplate sites
(genuinely axis vocabulary — this repo's skills were originally authored
around a "role spec" concept, one skill = one spawned role) from the
similarly-shaped but unrelated domain vocabulary (ARIA, RBAC, org/job roles,
etc.) the issue explicitly warns against damaging.

`role`→`skill` (case-preserving, word-only) was chosen as the edit for axis
occurrences rather than a bespoke rewrite per site, because #2670 already
established "skill" as the current name for the same concept these
self-references describe (`CLAUDE_ROLE`→`CLAUDE_SKILL`), and because a
mechanical, auditable substitution is less likely to silently drift meaning
across 227 sites than 227 independent rewrites would be. It was applied only
to occurrences individually classified axis-reference; the three literal
external-path citations that would have produced a fabricated filename were
excluded and hand-edited instead (see What was done).

Plural forms ("roles") were left untouched throughout, including inside
files being edited for their singular occurrences — the issue's own count
(384) matches exactly a singular-only `\brole\b` count, so plurals were
never part of the counted violation; touching them would have silently
expanded scope to an unreviewed, unclassified population.

## What did not work

Two occurrences were initially mis-edited and then reverted before landing:
the mechanical `role`→`skill` substitution was first applied to
`release-engineering-readiness-checklist/SKILL.md:25` and
`release-engineering-error-budget-policy/SKILL.md:64`, both citing (in
skill-repository's own prose, without this session confirming the cited
path actually exists — see the untracked-path note in What was done) the
dated research file `docs/reports/research/2026-07-27-role-practice/ops.md`.
These two lines should have been excluded up front as historical citations
(the same exception already applied to the sibling citations in
conformance-review-severity-classification, product-discovery-*, and
release-engineering-postmortem/rollout-plan) but were missed on the first
pass. Caught by a targeted re-grep for `skill-practice`/`skill-interaction`
across the whole repo immediately after the bulk mechanical edit, before any
commit — both were reverted to the original `role-practice` text via direct
`Edit` calls, and the classification map was updated to mark both lines
`historical` so the verification script's per-occurrence check (see Check 2
above) would catch any recurrence. derived: `grep -rn 'skill-practice\|skill-interaction' .` — result after the fix: no matches.

## Upstream basis

- `gh issue view 2601 --repo tokenmaxxxer/on-the-record` — issue text (Ask,
  Acceptance, Non-goals), sha: same-commit (read live, not cached).
- skill-repository base commit `5da544f3bc0ca89f65e1628f5480fb169d35e08a`
  (pulled clean via `git pull --ff-only` before any edit; brought in two
  commits — issue-111 and issue-113 — that landed after the mounted-skill
  commit 297e350 referenced in this record's frontmatter `skills:` line).
  derived: `cd ~/skill-registry/skills && git ls-files -z | xargs -0 grep -noiE '\brole\b|역할' | wc -l` — result: 384 (re-run against this newer HEAD, same figure as before the pull — no drift between the mount point and the working commit).

## Open findings

Judgment calls made during classification that a reviewer may want to
re-check (none block the acceptance checks above, all are documented in the
table's per-file notes):

1. `adversarial-review/SKILL.md:79` — `"**Role**: you are an evaluator, not
   a builder"` classified ordinary-English (a persona/mindset instruction
   for using the skill, not a reference to spawning a session with an
   identity) rather than axis-reference.
2. `model-routing/SKILL.md` (both occurrences) and
   `model-routing/references/rules.md:18` — "Role" as a table header /
   "the three-role decomposition (orchestrator/reasoner/executor)"
   classified ordinary-English: this is model-routing's own subject-matter
   vocabulary (a model's functional tier in a pipeline), distinct from
   tokenmaxxxer's spawned-session identity even though both use the same
   word.
3. `pricing-tier-structure/SKILL.md:41,75` — "assign the anchor role to the
   MIDDLE/[level]" classified ordinary-English: pricing-psychology
   terminology (decoy/anchor pricing), not a spawned identity.
4. `market-analysis-evidence-rigor/SKILL.md:82` — "restrict its role to
   establishing context" classified ordinary-English: "its" refers to a
   cited secondary source, i.e. the source's evidentiary function, not this
   skill's own self-reference.
5. `ux-engineering-navigation-depth/SKILL.md:101,103` — "different user
   roles"/"multi-role nav"/"each role's own entry point" classified
   ordinary-English: UX/IA domain vocabulary about distinct end-user
   personas navigating a product, not a spawned-session role.
6. `customer-support-five-whys-recurring-scope/SKILL.md` (all 5
   occurrences, "in-role resolution") classified ordinary-English: resolved
   within the current customer-support tier/agent, matching the same
   ordinary reading applied to the sibling
   `customer-support-escalation-path` skill's "role/title owner" language.
7. The 12 historical-citation occurrences (see table) are classified
   ordinary-English on the strength of the issue's own "Historical records
   in any repo — permanently out of scope" non-goal, extended to citations
   of those records' names on the reasoning that rewriting the citing text
   would either fabricate a non-existent renamed path or break a working
   pointer. If a future issue renames those underlying research files,
   these 12 citations should be revisited alongside that rename, not
   independently.

skill-verdict: technical-writing-structure-comprehension — not-applicable: the edits made were single-word, case-preserving substitutions (`role`→`skill`) inside already-well-formed sentences, chosen specifically to leave sentence/paragraph/section structure byte-identical around the change; no restructuring for reader comprehension or cognitive load was in scope or performed.
skill-verdict: conformance-review-sampling-derivation — not-applicable: the issue's acceptance explicitly required full enumeration of every one of the 384 occurrences ("Every occurrence is classified... not just the ones that were changed"), the direct opposite of the sampling-scope problem this skill addresses; a defensible sample would not have satisfied the acceptance.
other mounted skills (work-in-english, model-routing, prose-modes): not triggered — this session did not delegate to another model/agent (see rationale below) and produced no long-form prose beyond this record.

Note on model-routing / freelunch-directive: this task's true scope (which
occurrence-population is axis-reference) was only discoverable by reading
essentially all 384 occurrences in context — a first-pass co-occurrence grep
for `spawn.py`/`tokenmaxxxer`/`--skills`/`CLAUDE_SKILL`/`CLAUDE_ROLE` found
only 4 candidate files, which would have been a severe under-count had it
been trusted. derived: `cd ~/skill-registry/skills && grep -l 'spawn\.py\|tokenmaxxxer\|--skills\|CLAUDE_SKILL\|CLAUDE_ROLE' <the 116 files containing role/역할>` — result: 4 files (`content-strategy-content-governance-ownership/SKILL.md`, `conformance-review-finding-record/references/rules.md`, `conformance-review-requirement-extraction/references/rationalizations.md`, `finance-unit-economics-proposal-shape/SKILL.md`), against the true axis-reference population of 227 occurrences across 81 files established by reading every occurrence in context. Given that, splitting the classification judgment itself across parallel workers risked exactly the inconsistency the issue's over-application warning is about (one worker's "role spec" call disagreeing with another's on an ambiguous boundary case). This session did the full classification directly rather than fanning it out, then used a single deterministic Python transform (reviewed above) to apply the resulting decisions mechanically and verifiably. No sub-agent or background worker was used.

## Next steps

loop_state: complete.

acceptance: `cd ~/skill-registry/skills && git ls-files -z | xargs -0 grep -noiE '\brole\b|역할' | wc -l` — result:
```
157
```

157 = 145 ordinary-English + 12 historical-citation from the table above; 0
remaining in the 227-occurrence axis-reference subset (full per-occurrence
cross-check in Check 2 above). Delivered directly under the build-now
bypass (CORE_BUILD_NOW=1, contract v3 s19a): commit on this branch, one PR
against skill-repository's `main`, carrying `Closes #2601`. No further
steps remain on this issue.
