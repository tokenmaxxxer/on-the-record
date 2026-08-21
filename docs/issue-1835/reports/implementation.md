---
subject: issue-1835
code_under_review:
  - skills/conformance-review-finding-record/SKILL.md
  - skills/conformance-review-requirement-extraction/SKILL.md
  - skills/conformance-review-sampling-derivation/SKILL.md
  - skills/conformance-review-severity-classification/SKILL.md
  - skills/conformance-review-traceability-and-evidence/SKILL.md
  - skills/conformance-review-verdict-assignment/SKILL.md
  - skills/conformance-review-verification-method-selection/SKILL.md
  - scripts/procedure_authored_skills.txt
loop_state: landed
type: record
breaking: false
verdict: pass
---

# Implementation record: wave 2f conformance-review family (issue-1835)

## What was done

Delivered the phase-2 build approved by `APPROVE issue-1835/implementation`
(issue #1835 comment, this account, single-account mode): applied the
frozen wave recipe (docs/issue-1790/reports/implementation.md WAVE
RECIPE) to all 7 `conformance-review-*` skills in
`tokenmaxxxer/skill-repository`, per the phase-1 proposal
(docs/issue-1835/proposals/2026-08-21-wave-2f-conformance-review.md).

- Inserted `## Trigger` / `## Procedure` / `## Output shape` into each of
  the 7 skill bodies, between the framing paragraph and the skill's
  existing first substantive heading.
- 5 Shape-A skills (`requirement-extraction`, `sampling-derivation`,
  `traceability-and-evidence`, `verdict-assignment`,
  `verification-method-selection`): Procedure steps cite `## Rules`
  numbers.
- 2 Shape-B skills (`finding-record`, `severity-classification`):
  Procedure steps cite named section headings in parentheses, per the
  wave-2b `release-engineering-postmortem` precedent.
- Rewrote each `description:` from the authored Trigger, keeping the
  checker's trigger-marker substring ("use when"/"use while").
- Appended the 7 directory names to
  `scripts/procedure_authored_skills.txt` (39 -> 46 entries,
  incremental).
- Delivered as skill-repository PR
  https://github.com/tokenmaxxxer/skill-repository/pull/12 (branch
  `issue-1835-wave2f-conformance-review`, commit `9dc1f7e`). canonical:
  `gh pr create` output and `git log -1 --format=%H` on
  `/tmp/skill-repository-1835`, both read live in this session, are the
  source for the PR URL and commit sha. Built on a fresh checkout at
  `/tmp/skill-repository-1835`.

## Why

Contract v3 s19 phase-2 delivery: builds the phase-1 proposal exactly as
approved.

## Upstream

`upstream: docs/issue-1835/proposals/2026-08-21-wave-2f-conformance-review.md`
and `docs/issue-1835/reports/implementation/survey.md` (phase-1, this
role). canonical: `git log --oneline origin/main` (read live in this
session) shows `99a5584e issue-1835 phase 1: survey + proposal for wave
2f conformance-review family (#1837)` on `main` — the phase-1 PR #1837
is merged.

## The four checks (executed live from the skill-repository checkout, `/tmp/skill-repository-1835`, commit `9dc1f7e`)

canonical: commands executed live in this session's shell, output pasted
verbatim below.

### Check A — manifest checker

```
$ python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt
234 skills checked
exit=0
```

### Check B — rule-retention sweep

Per-skill numbered-rule counts under `## Rules`, post-change, for the 5
Shape-A skills:

```
requirement-extraction: 6 numbered rules under ## Rules
sampling-derivation: 5 numbered rules under ## Rules
traceability-and-evidence: 5 numbered rules under ## Rules
verdict-assignment: 6 numbered rules under ## Rules
verification-method-selection: 5 numbered rules under ## Rules
sum: 27 (matches the survey's pre-change baseline of 27 across these 5 skills — zero rule lines lost)
```

`git diff -- skills/conformance-review-<shape-A-name>/SKILL.md | grep -E
'^-[0-9]|^-\*\*'` returned empty for all 5 Shape-A files — no rule text
line was removed, only additions.

For the 2 Shape-B skills, line counts grew rather than shrank
(`finding-record` 164 -> 197 lines, `severity-classification` 80 -> 108
lines), and `git diff -- skills/conformance-review-<shape-B-name>/SKILL.md
| grep '^-' | grep -v '^--- '` showed exactly one removed line per file —
the pre-change `description:` line, replaced by the rewritten one per the
proposal's step 2 — with no other content line removed.

### Check C — `git diff --stat`, scoped to the 7 family paths + manifest

```
$ git diff --stat
 scripts/procedure_authored_skills.txt              |  7 +++++
 skills/conformance-review-finding-record/SKILL.md  | 35 +++++++++++++++++++++-
 skills/conformance-review-requirement-extraction/SKILL.md | 34 ++++++++++++++++++++-
 skills/conformance-review-sampling-derivation/SKILL.md | 33 +++++++++++++++++-
 skills/conformance-review-severity-classification/SKILL.md | 30 ++++++++++++++++++-
 skills/conformance-review-traceability-and-evidence/SKILL.md | 31 ++++++++++++++++++-
 skills/conformance-review-verdict-assignment/SKILL.md | 35 +++++++++++++++++++++-
 skills/conformance-review-verification-method-selection/SKILL.md | 31 ++++++++++++++++++-
 8 files changed, 229 insertions(+), 7 deletions(-)
exit=0
```

No path outside the 7 family `SKILL.md` files + the manifest is touched
(Requirement 2, Acceptance check 2).

### Check D — full-tree checker

```
$ python3 scripts/check_skill_conformance.py
234 skills checked
exit=0
```

## What did not work

None. All 7 skills required the full insert. canonical:
docs/issue-1835/reports/implementation/survey.md, section "Shape A/B
split", states "None of the 7 files carry `## Trigger`/`## Procedure`/
`## Output shape` yet, so none qualifies for the recipe's no-op/empty-state
clause" — so the recipe's no-op/empty-state clause did not apply to any
family member.

## Open findings

None.
