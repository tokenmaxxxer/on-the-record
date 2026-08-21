---
subject: issue-1942
role: implementation
kind: record
code_under_review:
  - skill-repository/skills/pr-communications-message-planning-and-evaluation-rules/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
loop_state: landed
type: feature
breaking: false
verdict: pass
---

# Implementation record: pr-communications-message-planning-and-evaluation-rules procedural body

## What was done

Authored the procedural body for the single skill
`pr-communications-message-planning-and-evaluation-rules` in
`tokenmaxxxer/skill-repository` per the approved proposal
(docs/issue-1942/proposals/procedural-body-pr-communications-message-planning-and-evaluation-rules.md)
and the frozen wave recipe (docs/issue-1790/reports/implementation.md,
WAVE RECIPE section):

1. Inserted `## Trigger` / `## Procedure` / `## Output shape` between
   the framing paragraph and `## Rules`, following the flat-list pattern
   from `upstream-defect-report-comprehensibility` (#1790 pilot): one
   Procedure step per rule (rules 2-3 grouped, as proposed), each step
   citing its rule number(s), preserving existing rule order.
2. Rewrote `description:` as a single sentence derived from the
   authored Trigger section's opening clauses, keeping "use when".
3. Appended `pr-communications-message-planning-and-evaluation-rules`
   to `scripts/procedure_authored_skills.txt`.
4. Ran the four live checks from the skill-repository checkout
   (`/tmp/skill-repository`), committed the change on branch
   `issue-1942-pr-communications-procedural-body`
   (commit `8ba1517eab4c1f8dd52e456ce5214c0bb916cc0e`), pushed, and
   opened skill-repository PR
   https://github.com/tokenmaxxxer/skill-repository/pull/45.

canonical: git diff skills/requirements-engineering-rules/SKILL.md (run
in /tmp/skill-repository, executed live) — result: a one-line
`description:` change unrelated to this issue's write set, found while
preparing the diff (leftover from issue #1943's prior session in the
same shared checkout), plus a stray `requirements-engineering-rules`
line already appended to `scripts/procedure_authored_skills.txt`. Both
were outside this issue's frozen write set, so they were stashed out
(`git stash push -- skills/requirements-engineering-rules/SKILL.md`) and
the stray manifest line was removed before committing, keeping this PR
scoped to exactly the two files below.

canonical: gh pr diff 45 --repo tokenmaxxxer/skill-repository
--name-only (executed live) — result:
`scripts/procedure_authored_skills.txt` and
`skills/pr-communications-message-planning-and-evaluation-rules/SKILL.md`,
confirming the resulting PR touches only those two paths.

## Why

Requirements-engineering procedural-body wave 2a (issue #1942), per the
recipe frozen in the #1790 pilot record. Phase 2 opened on
single-account-mode approval: issue comment `APPROVE issue-1942/implementation`
from `JiwonJung94` (listed in docs/specs/approvers.md), same account as
the phase-1 PR #1946 author.

## Upstream/basis

- docs/issue-1942/proposals/procedural-body-pr-communications-message-planning-and-evaluation-rules.md
  (approved phase-1 proposal)
- docs/issue-1790/reports/implementation.md (WAVE RECIPE, frozen)
- skill-repository commit 589c55e5835735e017743cf399b3288c6726e1d
  (pre-change baseline, per the survey)

## The four checks (executed live from the skill-repository checkout, post-change)

acceptance: python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt (run in /tmp/skill-repository) — result: exit 0, 234 skills checked.

```
$ cd /tmp/skill-repository && python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt
234 skills checked
$ echo "exit: $?"
exit: 0
```

acceptance: grep -nE "^[0-9]+\." skills/pr-communications-message-planning-and-evaluation-rules/SKILL.md (run in /tmp/skill-repository) — result: all 13 pre-change rule lines present verbatim.

```
$ grep -nE "^[0-9]+\." skills/pr-communications-message-planning-and-evaluation-rules/SKILL.md
45:1. Before choosing a channel, name the objective's target audience;
48:2. If more than one audience segment exists for the activity, split
52:3. If a key message has no proof point attached, attach one (data,
54:4. Match the lead persuasive appeal to the audience's actual objection —
58:5. If a message states a change as a gain-or-loss trade-off, frame the
61:6. If the activity touches a live incident or negative news, prepare
64:7. Route each drafted Q&A answer through an explicit approval workflow
68:8. If more than one spokesperson may face the same question, give them
71:9. Delete Q&A entries that stopped being plausible (feature shipped,
74:10. Before the activity is sent, define success criteria across all
77:11. If an outcome claim has no outtake-level evidence under it, report
80:12. If a supporting message restates the core message in different
96:1. When the audience for a message is not yet named, choose the
105:2. When more than one audience segment exists for the same activity
113:3. **REMOVAL**: when a communications plan lists more than one core
122:4. When a key message has no proof point attached, either attach a
130:5. When choosing which of ethos, pathos, or logos to lead with, match it
140:6. When a message states a change as a gain-or-loss trade-off (e.g. a
150:7. When a communications activity touches a live incident or negative
158:8. When a Q&A entry has a drafted answer, route it through an explicit
167:9. When more than one spokesperson may face the same question, use one
175:10. **REMOVAL**: when a risk/Q&A document accumulates answers for
184:11. When defining success criteria for a communications activity,
193:12. When an outcome claim ("this changed perception/behavior") has no
203:13. **REMOVAL**: when a supporting message restates the core message in
```

Cross-check against the survey's pre-change baseline (13 rule lines at
pre-change lines 29-136) shows all 13 rule texts (lines 96-203 above)
retained byte-identical post-change; the 12 lines at 45-80 above are the
newly authored Procedure steps, not the retained rules.

acceptance: git diff --stat (run in /tmp/skill-repository) — result: only the two intended paths, matching the proposal's frozen write set.

```
$ git diff --stat
 scripts/procedure_authored_skills.txt              |  1 +
 .../SKILL.md                                       | 69 +++++++++++++++++++++-
 2 files changed, 69 insertions(+), 1 deletion(-)
```

acceptance: python3 scripts/check_skill_conformance.py (run in /tmp/skill-repository, full-tree, no --manifest flag) — result: exit 0, 234 skills checked.

```
$ python3 scripts/check_skill_conformance.py
234 skills checked
$ echo "exit: $?"
exit: 0
```

## Skill-repository PR

https://github.com/tokenmaxxxer/skill-repository/pull/45 (branch
`issue-1942-pr-communications-procedural-body`, commit
`8ba1517eab4c1f8dd52e456ce5214c0bb916cc0e`, pushed successfully — no
SSH push failure encountered this run).

## Acceptance verification

- checked: manifest checker — acceptance: python3
  scripts/check_skill_conformance.py --manifest
  scripts/procedure_authored_skills.txt — result: exit 0 (see fenced
  output above).
- checked: rule-retention sweep — acceptance: grep -nE "^[0-9]+\."
  skills/pr-communications-message-planning-and-evaluation-rules/SKILL.md
  — result: all 13 pre-change rule lines retained (see fenced output
  and cross-check above).
- checked: scoped diff — acceptance: git diff --stat — result: only
  the skill's `SKILL.md` and the manifest file (see fenced output
  above).
- checked: full-tree checker — acceptance: python3
  scripts/check_skill_conformance.py — result: exit 0 (see fenced
  output above).
- checked: PR path scope — acceptance: gh pr diff 45 --repo
  tokenmaxxxer/skill-repository --name-only — result: only the two
  intended paths.

## What did not work

None.

## Open findings

None. canonical: git diff skills/requirements-engineering-rules/SKILL.md
(cited above) — the unrelated stray change from issue #1943, found in
the shared checkout, was stashed out rather than modified or resolved
on this issue's behalf; that issue's own session owns resolving it.

## Next steps

None — this record is terminal (`landed`).
