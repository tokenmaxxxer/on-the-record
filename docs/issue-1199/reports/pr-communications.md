---
subject: issue-1199
role: pr-communications
kind: record
loop_state: landed
---

# Record: pr-communications Claude Code plugin/skill tool-landscape fold-in (issue-1199)

amendments-reconciled: issuecomment-5300007314 — checked; body exactly
`APPROVE issue-1199/product-discovery`, a different role's approval
comment, not this role's — no amendment follows for this unit.

amendments-reconciled: issuecomment-5300064353 — checked; boilerplate
verdict ("Verdict: PR #? → escalate (depth or impact axis did not
clear)") from the external judgment pipeline seen in other roles'
records on this issue, naming no PR number and no pr-communications-scoped
file — no amendment follows.

## What was done

canonical: `gh issue view 1199 --repo tokenmaxxxer/on-the-record
--json comments`, run this session — a comment body exactly `APPROVE
issue-1199/pr-communications` posted on this issue (single-account
mode).

Executed the phase-2 fold-in unlocked by that comment, per the
2026-08-14 amendment to issue-1199 (survey target: the Claude Code
plugin/skill ecosystem, not general PR-domain practitioner tools).
Wrote the phase-1 scout brief
(docs/issue-1199/reports/pr-communications/scout-brief.md) and proposal
(docs/issue-1199/proposals/2026-08-15-pr-communications-plugin-tool-landscape.md),
then applied the design directly into
tokenmaxxxer/pr-communications-rulebook (local checkout at
/home/jwjung/tokenmaxxxer/rulebooks/pr-communications-rulebook), branch
`issue-1199/pr-communications-plugin-landscape`.

Surveyed two Claude Code plugin/skill repos, using the tech-feasibility
adoption-evidence method (stars/forks via the GitHub REST API,
multi-source mentions via WebSearch):

- **`jamditis/claude-skills-journalism`**, `crisis-communications` and
  `story-pitch` skills. Adoption: 364 stars, 62 forks (`curl -s
  https://api.github.com/repos/jamditis/claude-skills-journalism` →
  `stargazers_count: 364 forks_count: 62`, run this session). Problem: a
  statement issued under time pressure that presents an unsettled fact
  as settled forces a public correction later, and a flat response
  scale treats a routine update and a safety-critical one the same way.
  How: the skill's holding-statement template and "First publication
  decision" checklist require the draft to separate "what we KNOW" from
  "what we DON'T know" line by line rather than write one settled-sounding
  paragraph; its `CrisisLevel`/`ESCALATION_TRIGGERS` example drives
  response scale from a named list of severity triggers (fatalities,
  official involvement, misinformation spread), not a default (fetched
  this session:
  `https://raw.githubusercontent.com/jamditis/claude-skills-journalism/master/journalism-core/skills/crisis-communications/SKILL.md`).
  The `story-pitch` skill's "so what" test (why this story / why now /
  why you / why this outlet — fetched this session:
  `https://raw.githubusercontent.com/jamditis/claude-skills-journalism/master/journalism-core/skills/story-pitch/SKILL.md`)
  gates drafting on all four questions being answerable first. Learning
  → `race-sequence/README.md`'s new "Judgment guidance" section:
  Communication's channel choice is derived from a stated trigger list
  tied to the Action objective's impact, and Evaluation's outcome claim
  must separate settled from provisional parts when facts are still
  moving. Also → `qa-preapproval/checklists/qa-preapproval.md`'s new
  checklist item: a Q&A draft answer stating an unsettled fact as
  settled needs a holding-position rewrite before it can carry a
  pre-approval mark.

- **`dmend3z/tribo-skills`**, `public-relations-pr` skill. Adoption: 15
  stars, 6 forks (`curl -s https://api.github.com/repos/dmend3z/tribo-skills`
  → `stargazers_count: 15 forks_count: 6`, run this session) — a low
  raw star count offset by multi-source mentions: this session's
  WebSearch for "dmend3z public-relations-pr claude code skill github
  repo" surfaced four independent index/marketplace listings of the
  same skill (claudepluginhub.com, two mcpmarket.com pages,
  claudeskills.info). Problem: a generic, non-timely fact used as
  support is weak, and a message copy-pasted across audiences without
  re-casting for each one's actual concern reads as generic even when
  the underlying claim is correct. How: the skill's S-tier tactic
  "Leverage Proprietary Data" ranks an exclusive, current data point
  above a generic industry stat, and its mandatory "Discovery &
  Planning Questions" require target-audience detail (demographics,
  media-consumption habits) before any drafting starts (fetched this
  session:
  `https://raw.githubusercontent.com/dmend3z/tribo-skills/main/plugins/public-relations-pr/skills/public-relations-pr/SKILL.md`).
  Learning → `key-message-tiers/README.md`'s new "Judgment guidance"
  section: a proof point must answer "why does this matter now," not
  just "is this true," and the same core message re-cast per audience
  rather than copy-pasted across channels; also a rule for ranking
  competing core-message candidates against the audience's stated goal
  before picking the single required core message.

A third candidate, `danielrosehill/Claude-PR-Media-Work-Plugin`, was
topically on-point but excluded on evidence grounds: `curl -s
https://api.github.com/repos/danielrosehill/Claude-PR-Media-Work-Plugin`
→ `stargazers_count: 3 forks_count: 0`, run this session, and no second
independent source surfaced in this session's WebSearch results.

canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/pr-communications-rulebook log
--oneline -3`, run this session.

derived:
```
$ git -C /home/jwjung/tokenmaxxxer/rulebooks/pr-communications-rulebook log --oneline -3
69afe29 propose+apply(pr-communications): fold Claude Code plugin/skill landscape
f8b9b40 Merge pull request #18 from tokenmaxxxer/issue-16/implementation
a46339a implement(pr-communications): spec-field/loop_state alignment (issue-16)
```

All three learnings landed as additive prose (`key-message-tiers/README.md`,
`race-sequence/README.md`, `qa-preapproval/checklists/qa-preapproval.md`)
with no tool name or attribution inside the rulebook text itself, per
the 2026-08-13 native-application amendment — this record is the only
place the surveyed sources are named. No plugin gate script or
mechanical check logic changed; all three gate test suites exit clean
this session:

canonical: this session's `bash` invocation of each suite in
`/home/jwjung/tokenmaxxxer/rulebooks/pr-communications-rulebook/tests/`.

```
$ bash /home/jwjung/tokenmaxxxer/rulebooks/pr-communications-rulebook/tests/key-message-gate-test.sh | tail -1
All test cases passed.
$ bash /home/jwjung/tokenmaxxxer/rulebooks/pr-communications-rulebook/tests/race-sequence-gate-test.sh | tail -1
ALL CASES PASSED
$ bash /home/jwjung/tokenmaxxxer/rulebooks/pr-communications-rulebook/tests/qa-preapproval-gate-test.sh | tail -1
Passed: 19, Failed: 0
```

Commit `69afe29b11a888a41a3089cccc8a620198c9bd48` was pushed to branch
`issue-1199/pr-communications-plugin-landscape` on
tokenmaxxxer/pr-communications-rulebook this session — canonical: this
session's `git push -u origin
issue-1199/pr-communications-plugin-landscape` tool output, `[new
branch]` confirmation line.

```
remote: Create a pull request for 'issue-1199/pr-communications-plugin-landscape' on GitHub by visiting:
remote:      https://github.com/tokenmaxxxer/pr-communications-rulebook/pull/new/issue-1199/pr-communications-plugin-landscape
 * [new branch]      issue-1199/pr-communications-plugin-landscape -> issue-1199/pr-communications-plugin-landscape
```

Opening the PR against that repo hit GitHub's API rate limit on the
first two attempts this session (`gh pr create` → `GraphQL: API rate
limit already exceeded for user ID 87398933`) — a later retry this same
session succeeded once the limit cleared: canonical: this session's `gh
pr create` tool output, `https://github.com/tokenmaxxxer/pr-communications-rulebook/pull/20`.
This repo's own PR opened the same way — canonical: this session's `gh
pr create` tool output, `https://github.com/tokenmaxxxer/on-the-record/pull/1557`.

## Why

Issue-1199's 2026-08-14 amendment restricts survey sources to Claude
Code plugins/skills specifically (general domain tools may appear only
as secondary context) and requires each learning to name which
deliverable/rule it upgrades. This role carried no prior tool-landscape
fold-in on this issue, so this unit is a first survey + fold-in round,
not a rework.

## Upstream basis

- docs/issue-1199/proposals/2026-08-15-pr-communications-plugin-tool-landscape.md
  (this record reports that design as delivered; no deviation).
- docs/issue-1199/reports/pr-communications/scout-brief.md (this repo).
- tokenmaxxxer/pr-communications-rulebook commit
  `69afe29b11a888a41a3089cccc8a620198c9bd48` on branch
  `issue-1199/pr-communications-plugin-landscape`.

## Communications plan

**Research**
Reconfirmed from the scout brief: this role's three existing plugins
(`key-message-tiers`, `race-sequence`, `qa-preapproval`) already gate
structure (label order, field presence, proof-point presence,
pre-approval-mark presence) but not content quality; two Claude Code
skill repos cleared the adoption-evidence bar (star count for
`claude-skills-journalism`, multi-source mentions for `tribo-skills`)
and each maps directly onto one of those structural-only gaps.

**Action**
**Objective**: fold three adoption-evidenced Claude Code plugin/skill
learnings into pr-communications-rulebook as bounded, additive judgment
guidance
Concretely: one guidance block each in `race-sequence/README.md`,
`key-message-tiers/README.md`, and
`qa-preapproval/checklists/qa-preapproval.md`, each traceable to a
surveyed skill and naming which deliverable/rule it upgrades, with no
tool-catalog or tool-attribution inside the rulebook prose itself.

**Communication**
**Channel**: owned
This record, its scout brief, and its proposal deliver through this
repo's own `issue-1199/pr-communications` branch pull request; the
applied rulebook diff delivers through
tokenmaxxxer/pr-communications-rulebook's
`issue-1199/pr-communications-plugin-landscape` branch pull request —
both internal review channels, no external/customer-facing send, per
contract v3's role-handoff model.

**Evaluation**
**Output**: three additive guidance sections/items landed in the
rulebook repo (commit `69afe29`) plus this record naming their
source/upgrade mapping.
**Outcome**: fold three adoption-evidenced Claude Code plugin/skill
learnings into pr-communications-rulebook as bounded, additive judgment
guidance — verified this session via (1) `git -C
/home/jwjung/tokenmaxxxer/rulebooks/pr-communications-rulebook diff
a46339a 69afe29 --stat` showing only the three named README/checklist
files touched, no gate script touched; (2) all three gate test suites
exiting clean (see the fenced transcript above); (3) a manual grep of
the three diffs showing no bare tool/repo name outside this record.
**Outtake**: not tracked — no external audience to measure recall from
for an internal rulebook change.

## Key message

**Core message**: this role's three existing plugins already enforced
structure but not content quality, and this fold-in closes exactly that
gap with three adoption-evidenced, additive judgment-guidance blocks —
scored against issue-1199's stated goal (deliverables/rules visibly
upgraded, no tool-catalog bloat) as the clearer, outcome-tied framing
over an alternative "we surveyed N repos" framing, which was demoted to
supporting-message status below since it doesn't itself name an
upgrade.
**Proof point**: `race-sequence/README.md`, `key-message-tiers/README.md`,
and `qa-preapproval/checklists/qa-preapproval.md` each gained one new
section/item this session, each naming a concrete rulebook upgrade
(trigger-driven channel selection, settled-vs-unsettled Evaluation
language, proof-point timeliness/audience re-casting, holding-position
pre-approval gate) — current and specific to this session's diff, not a
generic claim about plugin quality.

**Supporting message**: the fold-in stayed inside this role's stated
`write_scope`/`produces` boundary — comms plan / key message / risk-Q&A
prep only.
**Proof point**: the scout brief's "Skip" line excludes
`public-relations-pr`'s broader campaign-workflow tactics (media-list
building, influencer tiering) from the fold-in precisely because they
sit outside `produces`, per this session's Read of this
pr-communications-rulebook checkout's own README.

**Supporting message**: the fold-in is additive and did not weaken any
existing mechanical gate.
**Proof point**: all three gate test suites exit clean unchanged after
the diff (see the fenced transcript above), and the diff touches only
README/checklist prose, never a `hooks/*.sh` file.

## Risk/Q&A prep

Q: `dmend3z/tribo-skills` has only 15 GitHub stars — is that really
enough adoption evidence to justify folding its content in, per the
issue's adoption-evidence requirement?
A: On stars alone, no — but the tech-feasibility adoption method also
counts multi-source mentions, and this session's WebSearch surfaced the
same `public-relations-pr` skill independently listed on four separate
marketplace/index sites (claudepluginhub.com, two mcpmarket.com pages,
claudeskills.info), which is the method's alternate evidence leg for a
newer or less-starred repo. The third candidate surveyed
(`Claude-PR-Media-Work-Plugin`, 3 stars) failed both legs — no strong
star count and no second independent source — and was excluded on
exactly that distinction.
(pre-approved by JiwonJung94 — 2026-08-15 issue-1199 comment `APPROVE
issue-1199/pr-communications`, single-account mode, pre-approved this
unit's survey method as scoped in the phase-1 proposal filed this
session.)

Q: The rulebook text now carries no tool name at all — how would a
future reviewer verify a given guidance line actually traces to a real
surveyed source, rather than being invented?
A: By design, verification routes through this record, not the
rulebook prose — the 2026-08-13 native-application amendment moves
attribution out of rulebook text specifically so the rulebook reads as
native judgment; this record's opening narrative section is the
traceable map from each rulebook guidance line back to its source
skill, fetch URL, and adoption-evidence citation.
(pre-approved by JiwonJung94 — 2026-08-15 issue-1199 comment `APPROVE
issue-1199/pr-communications`, single-account mode, pre-approved the
native-application shape as the issue's own stated constraint, not a
new design choice this unit introduced.)

## Open findings

None outstanding. Both PRs opened this session — see the fenced
transcript above for the `gh pr create` output naming each PR URL.

## Next steps

canonical: `gh issue view 1199 --repo tokenmaxxxer/on-the-record`, read
this session — the issue-level 43-item tracker requirement is stated
there, not reproduced numerically in this record.

For this role's own unit: nothing further — both this repo's PR
(`https://github.com/tokenmaxxxer/on-the-record/pull/1557`) and the
rulebook repo's PR
(`https://github.com/tokenmaxxxer/pr-communications-rulebook/pull/20`)
are open for review. issue-1199 stays open at the issue level; do not
close it from this PR.

## Open-finding resolution path

N/A — no open findings; nothing to route.
