---
code_under_review:
  - skill-repository/skills/brand-design-brand-consistency-governance/SKILL.md
  - skill-repository/skills/brand-design-brand-identity-strategy/SKILL.md
  - skill-repository/skills/brand-design-color-visibility/SKILL.md
  - skill-repository/skills/brand-design-logo-clear-space-size/SKILL.md
  - skill-repository/skills/brand-design-typography-pairing/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
loop_state: landed
type: feature
breaking: false
verdict: pass
---

# Implementation record — issue-1896, brand-design procedural-body wave

subject: issue-1896

## What was done

Applied the frozen procedural-body recipe (#1790 pilot,
`docs/issue-1790/reports/implementation.md`) to all 5 `brand-design-*`
skills in `tokenmaxxxer/skill-repository`, per the approved phase-1
proposal (`docs/issue-1896/proposals/brand-design-wave2a.md`):

1. Inserted `## Trigger` / `## Procedure` / `## Output shape` sections
   between each skill's framing paragraph and its existing
   `## Decision rules` heading, with each Procedure step citing the
   `### N.` rule number(s) it draws on.
2. Rewrote each skill's frontmatter `description:` as a sentence
   derived from that skill's own new `## Trigger` section.
3. Appended the 5 skill names (alphabetical) to
   `scripts/procedure_authored_skills.txt`.
4. Ran both checker modes and the rule-retention sweep (all four
   required checks — outputs below).
5. Committed and pushed branch `issue-1896-wave2a-brand-design` to
   `tokenmaxxxer/skill-repository`, opened PR
   canonical: `gh pr create` executed live,
   https://github.com/tokenmaxxxer/skill-repository/pull/31.

## Why

basis: `docs/issue-1896/proposals/brand-design-wave2a.md` (approved via
issue comment `APPROVE issue-1896/implementation`).

The proposal's Rationale reuses the recipe verbatim, citing rules by
their existing `### N.` heading number — the same citation convention
already proven for `legal-compliance-*`/`finance-unit-economics-*`
(both Shape A, `## Decision rules` + `### N.` headings, same as this
family per the phase-1 survey). Two alternatives were considered and
rejected in the proposal: citing rules by paragraph position instead of
the printed heading number, and normalizing the `## Decision rules`
heading to `## Rules` — both rejected as diverging from precedent and
outside the issue's non-goals.

## Upstream basis

basis: `docs/issue-1790/reports/implementation.md` (WAVE RECIPE
section) and `docs/issue-1896/proposals/brand-design-wave2a.md`.

## The four required checks — executed live from the skill-repository checkout

canonical: all four commands run live in `/tmp/skill-repository` on
branch `issue-1896-wave2a-brand-design`, checked out from
`origin/main` = commit `4ec5882`, this session, after the edits below.

### 1. Manifest checker

```
$ python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt
234 skills checked
EXIT: 0
```

### 2. Rule-retention sweep

For each of the 5 files, every pre-change `### N.` rule block (heading
line) under `## Decision rules` was checked present verbatim in the
post-change file, and the full `## Decision rules`-onward block was
diffed pre- vs. post-change:

```
=== brand-design-brand-consistency-governance ===
OK: ### 1. Lock core identity elements (logo, primary color, primary type) in the template layer; leave only content zones editable
OK: ### 2. Route review effort by risk, not uniformly — low-risk internal assets skip sign-off, high-risk public/campaign assets require brand-manager approval
OK: ### 3. Expire and remove outdated/unapproved assets from the shared library instead of leaving them alongside current ones
Decision rules block identical pre/post
=== brand-design-brand-identity-strategy ===
OK: ### 1. Require every new visual asset to trace to a stated Physique or Personality facet before shipping
OK: ### 2. Check the "sender" facets (Physique, Personality, Culture) and the "receiver" facets (Reflection, Self-image, Relationship) separately when auditing consistency
OK: ### 3. Drop identity facets the brand no longer actually delivers on, rather than keeping them in the guide as aspirational
Decision rules block identical pre/post
=== brand-design-color-visibility ===
OK: ### 1. Body/UI text pairs must clear WCAG contrast; brand-mark text is exempt but should still clear it when feasible
OK: ### 2. Reserve a single dominant brand hue for the primary recognition trigger; do not let a secondary/accent palette compete for that role
OK: ### 3. Remove low-familiarity accent colors from a mature guide rather than adding new ones to chase trend cycles
Decision rules block identical pre/post
=== brand-design-logo-clear-space-size ===
OK: ### 1. Define clear space as a ratio of the logo's own height/letterform, not a fixed absolute unit
OK: ### 2. Set separate minimum-size floors for print and for digital, and for wordmark vs. logomark-alone
OK: ### 3. Cut logo variants that exist only for a single obsolete campaign/medium rather than keeping every historical version "just in case"
Decision rules block identical pre/post
=== brand-design-typography-pairing ===
OK: ### 1. Pair for contrast, not similarity — serif+sans over near-identical sans+sans
OK: ### 2. Match contrast level between the two chosen faces; don't pair a fragile high-contrast serif with a heavy low-contrast display sans
OK: ### 3. Cap the brand system at two-to-three typefaces total; retire an unused third/fourth face rather than let it accumulate from campaign-specific additions
Decision rules block identical pre/post
```

All 15 pre-change rule blocks (heading + `**Condition**`/`**Choice**`/
`**Why**`/`**Source**`/`**Counter-example test**` sub-bullets) present
verbatim post-change. 0 rule lines lost.

### 3. Full-tree checker

```
$ python3 scripts/check_skill_conformance.py
234 skills checked
EXIT: 0
```

### 4. Scoped `git diff --stat`

```
$ git diff --stat
 scripts/procedure_authored_skills.txt              |  5 ++++
 .../SKILL.md                                       | 29 +++++++++++++++++++++-
 .../brand-design-brand-identity-strategy/SKILL.md  | 29 +++++++++++++++++++++-
 skills/brand-design-color-visibility/SKILL.md      | 29 +++++++++++++++++++++-
 skills/brand-design-logo-clear-space-size/SKILL.md | 29 +++++++++++++++++++++-
 skills/brand-design-typography-pairing/SKILL.md    | 28 ++++++++++++++++++++-
 6 files changed, 144 insertions(+), 5 deletions(-)
```

Exactly the 5 `brand-design-*` SKILL.md paths plus
`scripts/procedure_authored_skills.txt` — nothing else. Matches the
proposal's frozen write set.

## Empty state

No no-op applies: the phase-1 survey classified all 5 skills Shape A
(no pre-existing Trigger/Procedure/Output-shape headings); all 5
required authoring.

## What did not work

None.

## Open findings

None.

## loop_state

`landed` — skill-repository PR #31 opened. canonical: `gh pr create`
executed live, plus the four check outputs pasted above
(`python3 scripts/check_skill_conformance.py --manifest ...` exit 0,
the rule-retention sweep, `python3 scripts/check_skill_conformance.py`
exit 0, and the scoped `git diff --stat` output) — all executed live
this session in "## The four required checks" above, all passing, diff
scoped to the frozen write set. This on-the-record repo's own PR
carries this record.
