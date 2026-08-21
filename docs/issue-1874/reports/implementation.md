---
subject: issue-1874
role: implementation
code_under_review:
  - skill-repository/skills/partnerships-bd-deal-structure-selection/SKILL.md
  - skill-repository/skills/partnerships-bd-exclusivity-and-scope-terms/SKILL.md
  - skill-repository/skills/partnerships-bd-governance-cadence-and-kpi/SKILL.md
  - skill-repository/skills/partnerships-bd-negotiation-positioning/SKILL.md
  - skill-repository/skills/partnerships-bd-term-sheet-comprehensibility-and-convention/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
loop_state: landed
type: delivery
breaking: false
verdict: pass
---

# Phase-2 record: procedural-body wave 2a — partnerships-bd family

## What was done

Delivered the approved proposal
(`docs/issue-1874/proposals/partnerships-bd-wave2a.md`) against the
`skill-repository` checkout, base commit `4b2a372`, worktree at
`/tmp/skill-repository-1874`, commit `e56f3ee` on branch
`issue-1874-procedural-body-partnerships-bd`, opened as
tokenmaxxxer/skill-repository#25.

For each of the 5 `partnerships-bd-*` skills —
`partnerships-bd-deal-structure-selection`,
`partnerships-bd-exclusivity-and-scope-terms`,
`partnerships-bd-governance-cadence-and-kpi`,
`partnerships-bd-negotiation-positioning`,
`partnerships-bd-term-sheet-comprehensibility-and-convention` —
inserted a `## Trigger` / `## Procedure` / `## Output shape` section
between the framing paragraph and the existing `## Decision rules`
section, with each Procedure step citing the rule number(s) (`### N.`)
it draws on, and rewrote `description:` from the template ("Use when
you need guidance on X") into a sentence derived from that skill's own
Trigger section.

canonical: docs/issue-1874/reports/implementation/survey.md ("Body
shape" section, read before drafting the proposal) — confirms none of
the 5 family bodies already carried a Trigger/Procedure/Output-shape
section (all one `## Decision rules` heading each). All 5 skills were
therefore live edits; the acceptance criterion's no-op/empty-state
clause does not apply to any of the 5.

Appended the 5 skill directory names to
`scripts/procedure_authored_skills.txt`, after the file's tail as it
stood at the branch base commit `4b2a372` (through
`risk-management-response-strategy-selection`) — no checker-logic
change, matching the issue's non-goals.

## Why

why: matches the approved proposal's Rationale — cite rules by their
printed `### N.` heading number (this family prints each rule as its
own numbered level-3 heading, distinct in markup from other families
but citable the same way); each Procedure step cites its source
rule(s) so the new section is a navigational layer over `## Decision
rules`, not a disconnected summary, matching the #1790 pilot's
navigational-layer framing.

upstream: docs/issue-1874/proposals/partnerships-bd-wave2a.md; approved
via `APPROVE issue-1874/implementation` comment from `JiwonJung94`
(listed in docs/specs/approvers.md), single-account mode (PR #1878
author == approver).

## Rationale for deviations

Shared skill-repository checkout collision: `/tmp/skill-repository` is
a shared, uncoordinated checkout. Mid-task its working tree turned out
to already carry another in-flight session's uncommitted WIP
(issue-1873, `refactoring-legacy` family, on branch
`issue-1873-procedural-body-refactoring-legacy`).
canonical: git status --short / git diff scripts/procedure_authored_skills.txt,
run live in /tmp/skill-repository mid-session — showed a `UU` unmerged
manifest with conflict markers after an initial `git checkout
-b`/`git stash` sequence briefly intermixed this task's edits with
that other session's WIP.

Recognized as a deviation per the role-deviation directive (not
routine task friction: it risked another session's uncommitted work,
outside this task's own frozen write set). Classified INLINE-FIX:
resolving it stayed inside this task's data (no design/security/product
judgment, no scope change to the deliverable, one-off collision) —
restored the shared checkout's working tree to exactly that other
session's pre-collision state (manifest conflict resolved to just its
5 `refactoring-legacy-*` lines, its 5 skill files left untouched, no
partnerships-bd content left behind), then did all of this task's
actual work in an isolated `git worktree`
(`/tmp/skill-repository-1874`) branched from the same base commit
(`4b2a372`) so no further collision was possible.

The approved proposal's step-by-step plan did not anticipate a
shared-checkout collision, so isolating the work into a separate
worktree is the one procedural addition beyond the proposal's literal
steps. canonical: git diff --stat=200 4b2a372 e56f3ee (fenced under
Requirement 2 below) — the write set touched is exactly the 5 SKILL.md
files + manifest, the proposal's frozen `files:` list, unaffected by
the collision or its resolution. Logged per the deviation-loop
directive: `docs/reports/deviation-log.md` — timestamp 2026-08-21,
`inline`, "shared /tmp/skill-repository checkout collision with
concurrent issue-1873 session, resolved by isolating this task's work
into /tmp/skill-repository-1874 worktree", diff location: manifest
conflict resolution + worktree creation, this session.

## Acceptance checks — executed live

### Requirement 1: manifest checker + rule-retention sweep

```
$ cd /tmp/skill-repository-1874 && python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt
234 skills checked
$ echo "exit: $?"
exit: 0
```
canonical: python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt (run in /tmp/skill-repository-1874, post-change)

Rule-retention sweep, comparing each of the 5 family files' pre-change
`### N.` headings (from `git show 4b2a372:<path>`, the branch base
commit) against the post-change file.
canonical: for-loop grep sweep (git show 4b2a372:<path> | grep -c
'^### [0-9]' vs. grep -c '^### [0-9]' <path>, plus per-heading grep -qF
containment check) executed live in /tmp/skill-repository-1874 — raw
output below, every pre-change heading retained verbatim:

```
=== partnerships-bd-deal-structure-selection === pre=3 post_headings=3
  headings retained: 3/3
=== partnerships-bd-exclusivity-and-scope-terms === pre=3 post_headings=3
  headings retained: 3/3
=== partnerships-bd-governance-cadence-and-kpi === pre=3 post_headings=3
  headings retained: 3/3
=== partnerships-bd-negotiation-positioning === pre=3 post_headings=3
  headings retained: 3/3
=== partnerships-bd-term-sheet-comprehensibility-and-convention === pre=3 post_headings=3
  headings retained: 3/3
```

Total: 15 rule headings across all 5 family skills, all retained.
canonical: git diff HEAD -- skills/ | grep '^-' | grep -v '^---' (run
in /tmp/skill-repository-1874) — output was the 5 description lines
only, no `## Decision rules` content, corroborating structurally that
no rule text under any `## Decision rules` block was deleted.

### Requirement 2: git diff --stat + full-tree checker

```
$ cd /tmp/skill-repository-1874 && git diff --stat=200 4b2a372 e56f3ee
 scripts/procedure_authored_skills.txt                                       |  5 +++++
 skills/partnerships-bd-deal-structure-selection/SKILL.md                    | 31 ++++++++++++++++++++++++++++++-
 skills/partnerships-bd-exclusivity-and-scope-terms/SKILL.md                 | 30 +++++++++++++++++++++++++++++-
 skills/partnerships-bd-governance-cadence-and-kpi/SKILL.md                  | 30 +++++++++++++++++++++++++++++-
 skills/partnerships-bd-negotiation-positioning/SKILL.md                     | 30 +++++++++++++++++++++++++++++-
 skills/partnerships-bd-term-sheet-comprehensibility-and-convention/SKILL.md | 31 ++++++++++++++++++++++++++++++-
 6 files changed, 152 insertions(+), 5 deletions(-)
```
canonical: git diff --stat=200 4b2a372 e56f3ee (run in
/tmp/skill-repository-1874, base commit 4b2a372 vs. this wave's commit
e56f3ee) — lists exactly the 5 `partnerships-bd-*/SKILL.md` paths plus
`scripts/procedure_authored_skills.txt`, no other file touched.

```
$ python3 scripts/check_skill_conformance.py
234 skills checked
$ echo "exit: $?"
exit: 0
```
canonical: python3 scripts/check_skill_conformance.py (no --manifest
flag, full 234-skill tree, run in /tmp/skill-repository-1874
post-change).

acceptance: python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt — result: exit 0, 234 skills checked.
acceptance: python3 scripts/check_skill_conformance.py — result: exit 0, 234 skills checked, no --manifest flag.
Both requirements' acceptance checks above are executed-live.

## What did not work

canonical: acceptance run above (Requirement 1 block) — exit 0 on the
first authored version of all 5 skills. None to date under that check.
The only failure encountered this session was the shared-checkout
collision covered in the Rationale for deviations section above, which
was a working-tree/process hazard, not a check failure — no check ever
returned non-zero or a missing rule line.

## Open findings

None.

## Deliverables

- tokenmaxxxer/skill-repository#25 (commit `e56f3ee` on
  `issue-1874-procedural-body-partnerships-bd`): the 5 partnerships-bd
  skill bodies, manifest extension.
- This record.
