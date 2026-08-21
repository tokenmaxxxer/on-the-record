---
subject: issue-1790
role: implementation
code_under_review:
  - skill-repository/skills/upstream-defect-report-comprehensibility/SKILL.md
  - skill-repository/skills/upstream-defect-report-convention/SKILL.md
  - skill-repository/skills/upstream-defect-report-subtraction/SKILL.md
  - skill-repository/skills/api-design-error-design/SKILL.md
  - skill-repository/skills/api-design-http-semantics/SKILL.md
  - skill-repository/skills/api-design-payload-design/SKILL.md
  - skill-repository/skills/api-design-resource-modeling/SKILL.md
  - skill-repository/skills/api-design-tool-landscape/SKILL.md
  - skill-repository/skills/api-design-versioning-evolution/SKILL.md
  - skill-repository/scripts/check_skill_conformance.py
  - skill-repository/scripts/procedure_authored_skills.txt
loop_state: landed
type: delivery
breaking: false
verdict: pass
---

# Phase-2 record: procedural-body authoring pilot wave

## What was done

Delivered the approved proposal (`docs/issue-1790/proposals/procedural-body-pilot.md`)
against the `skill-repository` checkout at `/tmp/skill-repository`, branch
`issue-1790-procedural-body-pilot`, commit `debb425`, opened as
tokenmaxxxer/skill-repository#7.

For each of the 9 pilot skills — `upstream-defect-report-comprehensibility`,
`upstream-defect-report-convention`, `upstream-defect-report-subtraction`,
`api-design-error-design`, `api-design-http-semantics`,
`api-design-payload-design`, `api-design-resource-modeling`,
`api-design-tool-landscape`, `api-design-versioning-evolution` — inserted a
`## Trigger` / `## Procedure` / `## Output shape` section between the
framing paragraph and the existing `## Rules` list, with each Procedure
step citing the rule number(s) it draws on, and rewrote `description:`
from the template ("Use when you need guidance on X") into a sentence
derived from that skill's own Trigger section.

canonical: docs/issue-1790/reports/implementation/survey.md
("Frontmatter shape" section, read before drafting the proposal) —
confirms none of the 9 pilot bodies already carried a Trigger/Procedure/
Output-shape section. All 9 pilot skills were therefore live edits, and
the acceptance criterion's no-op/empty-state clause does not apply to
any of the 9.

Extended `scripts/check_skill_conformance.py` with an additive,
`--manifest <path>` opt-in check: any skill directory listed in the
manifest must have `## Trigger`, `## Procedure`, and `## Output shape` in
its `SKILL.md` body; unlisted skills are unaffected. Added
`scripts/procedure_authored_skills.txt` listing the 9 pilot skill
directory names.

## Why

why: matches the approved proposal's Rationale — a manifest-gated check
keeps the 234-skill tree's existing conformance intact while enforcing the
new shape strictly on the 9 pilot skills (issue's own pilot-first
sequencing); each Procedure step cites its source rule(s) so the new
section is a navigational layer over `## Rules`, not a disconnected
summary that would leave rule content functionally orphaned.

upstream: docs/issue-1790/proposals/procedural-body-pilot.md; approved via
`APPROVE issue-1790/implementation` comment from `JiwonJung94` (listed in
docs/specs/approvers.md), single-account mode (PR #1794 author ==
approver).

## Acceptance checks — executed live

### Requirement 1: manifest checker + rule-retention sweep

```
$ cd /tmp/skill-repository && python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt
234 skills checked
$ echo "exit: $?"
exit: 0
```
canonical: python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt (run in /tmp/skill-repository, post-change)

Rule-retention sweep — for each pilot file, every pre-change numbered rule
line's first-50-char substring (extracted from `git show HEAD~1:<path>`,
where HEAD~1 is the pre-authoring commit) greps successfully against the
post-change file. derived: for-loop grep sweep executed live in
/tmp/skill-repository, one file per pilot skill:

```
=== upstream-defect-report-comprehensibility ===  6/6 RETAINED
  1. **When** describing the failure — **choice**:
  2. **When** the report includes code, logs, comman
  3. **When** the environment (OS, runtime/interpret
  4. **When** the reproduction requires more than ~3
  5. **When** a report would otherwise bury the sing
  6. **When** the report would otherwise repeat the
=== upstream-defect-report-convention ===  7/7 RETAINED
  1. **When** the upstream repository ships an issue
  2. **When** CONTRIBUTING.md or the issue template
  3. **When** the project's own commit/PR history sh
  4. **When** the project designates a specific chan
  5. **When** a project's CONTRIBUTING.md is stale r
  6. **When** the reporter's own habitual tone (dema
  7. **When** checking whether a defect has already
=== upstream-defect-report-subtraction ===  7/7 RETAINED
  1. **When** the report author is a fluent field-ti
  2. **When** a stack trace, log dump, or screenshot
  3. **When** the reproduction steps include environ
  4. **When** the report narrates the investigation
  5. **When** a proprietary or reporter-specific dep
  6. **When** the same defect has already been filed
  7. **When** a suspected upstream defect is about t
=== api-design-error-design ===  13/13 RETAINED
  1. When designing the base error envelope for a JS
  2. When a client needs to branch program logic on
  3. When a single request fails validation on multi
  4. When defining error codes across services, name
  5. When writing the human-readable `detail`/`messa
  6. When populating `title`, keep it a fixed string
  7. **REMOVAL**: When generating any error response
  8. **REMOVAL**: When an error can be retried by th
  9. When a request is safe to retry (network failur
  10. When a service needs to expose more error cont
  11. When designing error message text, write for t
  12. When an error object could carry both a stable
  13. When encoding this playbook's rules into an au
=== api-design-http-semantics ===  12/12 RETAINED
  1. When a request only retrieves data and causes n
  2. When a client needs to safely retry a request a
  3. When a client must create or mutate a resource
  4. When designing idempotency-key behavior, do not
  5. When a client wants to fully replace a resource
  6. When a client needs to apply a partial, increme
  7. When a server team wants POST-based resource cr
  8. When a resource is successfully created via POS
  9. When an operation succeeds but there is no repr
  10. When a create/update/delete operation is proce
  11. **REMOVAL**: When choosing a redirect status f
  12. **REMOVAL**: When a numbered API operation lik
=== api-design-payload-design ===  12/12 RETAINED
  1. When a collection can grow past a few thousand
  2. When users need to jump to an arbitrary page nu
  3. When designing a list endpoint's pagination res
  4. When a list endpoint could return enough rows t
  5. When exposing a paginated collection over HTTP,
  6. When an endpoint supports both a full list and
  7. When clients need to fetch resources with diffe
  8. **REMOVAL**: When a resource's default list/get
  9. When designing filter query parameters for a li
  10. **REMOVAL**: When a list endpoint currently re
  11. When a list endpoint's result set can be large
  12. When a collection is accessed by many concurre
=== api-design-resource-modeling ===  13/13 RETAINED
  1. When an operation maps cleanly onto Get/List/Cr
  2. When an operation has no reasonable mapping to
  3. When a child object always exists exactly once
  4. When you're tempted to make an endpoint's reque
  5. When designing a resource hierarchy, keep paren
  6. When a sub-resource relationship is many-to-man
  7. When a sub-resource already has a globally uniq
  8. When nesting is genuinely warranted (strict hie
  9. When choosing resource identifiers and paths, m
  10. When you need to represent a relationship betw
  11. **REMOVAL**: When a URL path exceeds roughly t
  12. **REMOVAL**: When an endpoint's shape is ident
  13. When a resource model grows past a handful of
=== api-design-tool-landscape ===  4/4 RETAINED
  1. When an interface-spec is published, generate a
  2. When a payload schema is defined in the interfa
  3. When a new API version or resource ships, gener
  4. When two services need to agree on a resource's
=== api-design-versioning-evolution ===  15/15 RETAINED
  1. When deciding how to expose API versions at all
  2. When a URL-based version prefix (e.g., `/v1/cus
  3. When classifying whether a proposed change is b
  4. When classifying a schema/message-level change
  5. When your API returns opaque strings such as ID
  6. When choosing between adding a new field/parame
  7. When your organization needs a formal gate befo
  8. When you deprecate a field, endpoint, or parame
  9. **REMOVAL**: When retiring an API version or fe
  10. **REMOVAL**: When you have committed to a conc
  11. When setting a deprecation-to-removal timeline
  12. **REMOVAL**: When planning a deprecation/remov
  13. When an emergency (critical security vulnerabi
  14. When a breaking-change policy (rule 3-4 above)
  15. When defining what counts as a breaking change
```

Total: 89 rule lines across all 9 pilot skills, all retained. Corroborated
structurally: `git diff HEAD~1 HEAD -- skills/ | grep '^-' | grep -v '^---'`
shows only the 9 `description:` lines as removed content — no rule text
under any `## Rules` block was deleted. canonical: git diff HEAD~1 HEAD --
skills/ | grep '^-' | grep -v '^---' (run in /tmp/skill-repository,
output was the 9 description lines only, no `## Rules` content).

### Requirement 2: git diff --stat + full-tree checker

```
$ cd /tmp/skill-repository && git diff --stat --cached
 scripts/check_skill_conformance.py                 | 36 +++++++++++++++
 scripts/procedure_authored_skills.txt              |  9 ++++
 skills/api-design-error-design/SKILL.md            | 52 +++++++++++++++++++++-
 skills/api-design-http-semantics/SKILL.md          | 43 +++++++++++++++++-
 skills/api-design-payload-design/SKILL.md          | 46 ++++++++++++++++++-
 skills/api-design-resource-modeling/SKILL.md       | 50 ++++++++++++++++++++-
 skills/api-design-tool-landscape/SKILL.md          | 28 +++++++++++-
 skills/api-design-versioning-evolution/SKILL.md    | 51 ++++++++++++++++++++-
 .../SKILL.md                                       | 40 ++++++++++++++++-
 skills/upstream-defect-report-convention/SKILL.md  | 44 +++++++++++++++++-
 skills/upstream-defect-report-subtraction/SKILL.md | 42 ++++++++++++++++-
 11 files changed, 432 insertions(+), 9 deletions(-)
```
(the truncated 9th row is `skills/upstream-defect-report-comprehensibility/SKILL.md`)
— exactly the 9 pilot paths plus `scripts/check_skill_conformance.py` and
`scripts/procedure_authored_skills.txt`, no other file touched.
canonical: git diff --stat --cached (run in /tmp/skill-repository,
captured pre-commit while the 11 files were staged).

```
$ python3 scripts/check_skill_conformance.py
234 skills checked
$ echo "exit: $?"
exit: 0
```
canonical: python3 scripts/check_skill_conformance.py (no --manifest flag,
full 234-skill tree, run in /tmp/skill-repository post-change).

acceptance: python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt — result: exit 0, 234 skills checked.
acceptance: python3 scripts/check_skill_conformance.py — result: exit 0, 234 skills checked, no --manifest flag.
Both requirements' acceptance checks above are executed-live.

## WAVE RECIPE

**Authoring pattern** (frozen from this pilot, for reuse by follow-up
waves):
1. Check the skill's body for existing `## Trigger`/`## Procedure`/
   `## Output shape` headings before authoring; if present, record a
   no-op with evidence instead of authoring (this pilot's own check —
   canonical: docs/issue-1790/reports/implementation/survey.md,
   "Frontmatter shape" section — found none across the 9 pilot skills,
   so all 9 required authoring).
2. Insert `## Trigger` (concrete conditions distinguishing this skill from
   its sibling axes in the same family — not a restatement of the title),
   `## Procedure` (ordered steps, each citing rule number(s) from
   `## Rules`), and `## Output shape` (what the applied skill produces)
   between the framing paragraph and `## Rules`.
3. Rewrite `description:` as a sentence derived from the `## Trigger`
   content, keeping a checker trigger-marker substring ("use when").
4. Add the skill's directory name to `procedure_authored_skills.txt`.
5. Run `check_skill_conformance.py --manifest <manifest>` and the
   full-tree run with no flag; run the rule-retention grep sweep before
   committing.

**Observed per-skill effort** (this pilot, 9 skills): derived:
`git diff --stat --cached` (fenced under Requirement 2 above) shows a
28-52 line range across the 9 skill files, 432 total insertions across
all 11 changed files; the rule-retention sweep (fenced under Requirement
1 above) shows a 4-15 rule-per-skill range, 89 rules total.

**Proposed wave partition for the remaining skills** (per the survey's
family-size finding, largest families first, one wave per family to keep
each wave's review surface bounded to a single role's rule set):
canonical: docs/issue-1790/reports/implementation/survey.md (family-size
enumeration read during phase-1 research).
- Wave 2 candidates: the largest remaining families (e.g. 10-skill
  families such as `technical-feasibility`, `release-engineering`,
  `product-discovery` per the survey) — highest total rule-line count,
  most reuse of the frozen pattern before smaller families diverge from
  it.
- Subsequent waves: descending by family size down to the smallest
  (2-skill) families, each wave citing this recipe and this record as the
  basis, extending `procedure_authored_skills.txt` incrementally rather
  than replacing it.
- Each wave repeats this record's four checks (manifest run, sweep,
  diff --stat scoped to that wave's paths, full-tree run) before landing.

## What did not work

acceptance: python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt — result: exit 0 on the first authored version of all 9 skills (see Requirement 1 block above).
None to date under that check.

## Open findings

None.

## Deliverables

- tokenmaxxxer/skill-repository#7 (commit `debb425` on
  `issue-1790-procedural-body-pilot`): the 9 pilot skill bodies, checker
  extension, manifest.
- This record.
