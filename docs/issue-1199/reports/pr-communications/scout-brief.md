---
subject: issue-1199
role: pr-communications
doc-type: scout-brief
---

# Scout brief: pr-communications Claude Code plugin/skill landscape (issue-1199, 2026-08-14 amendment)

canonical: this turn's Bash/WebSearch/WebFetch tool transcript.

Mode: batched-sequential (curl/WebSearch/WebFetch calls run one after
another in this turn, not via parallel Agent dispatch) — stated
explicitly per the scout directive's fallback-mode requirement, since
this unit's scope (a bounded 3-entry fold-in) did not warrant a
multi-agent sweep. One sweep round plus one deepening round (fetching
each shortlisted skill's SKILL.md).

## Candidates and adoption evidence

canonical: `curl -s https://api.github.com/repos/jamditis/claude-skills-journalism`

```
stargazers_count: 364
forks_count: 62
```
`jamditis/claude-skills-journalism` — carries a `crisis-communications`
skill directly in scope for this role.

canonical: `curl -s https://api.github.com/repos/dmend3z/tribo-skills`

```
stargazers_count: 15
forks_count: 6
```
`dmend3z/tribo-skills` — its `public-relations-pr` skill sits inside an
84-skill marketing plugin set.

canonical: this turn's WebSearch for "dmend3z public-relations-pr claude
code skill github repo" — result titles included "public-relations-pr -
Claude Code Plugin" (claudepluginhub.com), "Public Relations Specialist
Claude Code Skill" (mcpmarket.com), "PR & Communications Skill for
Claude Code" (mcpmarket.com), "public-relations Skill by kostja94"
(claudeskills.info) — four independent index/marketplace sites listing
the same skill, the multi-source-mentions leg of the tech-feasibility
adoption method, weighed here against the repo's own low star count
above.

canonical: `curl -s https://api.github.com/repos/danielrosehill/Claude-PR-Media-Work-Plugin`

```
stargazers_count: 3
forks_count: 0
```
`danielrosehill/Claude-PR-Media-Work-Plugin` — topically on-point (PR and
media monitoring workflow) but with neither a strong star count nor a
second independent source in this turn's WebSearch results; left out of
the fold-in on evidence grounds.

canonical: `curl -s https://api.github.com/repos/jeremylongshore/claude-code-plugins-plus-skills`

```
stargazers_count: 2636
forks_count: 387
```
`jeremylongshore/claude-code-plugins-plus-skills` — a general marketplace
aggregator, used only as scale context for the ecosystem, not itself a
source for a design move.

## Judge point

canonical: this turn's WebFetch of the crisis-communications, story-pitch,
and public-relations-pr `SKILL.md` files, and this session's Read of
`race-sequence/README.md`, `key-message-tiers/README.md`, and
`qa-preapproval/checklists/qa-preapproval.md` in the
pr-communications-rulebook checkout.

The two adoption-evidenced repos each carry a skill whose content maps
onto a gap those three existing plugin files leave open: race-sequence's
Evaluation guidance had nothing on partially-settled facts, key-message-
tiers' gate accepts any proof point without weighing its strength, and
qa-preapproval's checklist had no check for a firm-sounding answer to an
unsettled question. `Claude-PR-Media-Work-Plugin`'s content was not
pulled further given the adoption gap noted above.

## Must-bes, performance axes, adopt/skip

canonical: the crisis-communications `SKILL.md` fetched this turn
(holding-statement template; "First publication decision" checklist
listing "What we KNOW" vs. "What we DON'T know"; the `CrisisLevel`/
`ESCALATION_TRIGGERS` example).

- Must-be: separate a settled fact from an unsettled claim explicitly in
  any statement issued under time pressure. **Adopt** → race-sequence
  Evaluation guidance + qa-preapproval holding-position check.
- Must-be: channel/response scale tracks a named severity-trigger list
  rather than a flat default. **Adopt** → race-sequence Communication
  channel-selection guidance.

canonical: the public-relations-pr `SKILL.md` fetched this turn (S-tier
tactic "Leverage Proprietary Data"; "Discovery & Planning Questions"
requiring target-audience detail before drafting) and the story-pitch
`SKILL.md` fetched this turn (the "so what" test: why this story / why
now / why you / why this outlet).

- Performance axis: proof-point strength turns on timeliness/exclusivity
  of the supporting fact, not truth alone. **Adopt** → key-message-tiers
  proof-point guidance.
- Performance axis: audience-specific message re-casting beats one
  generic message copy-pasted across channels. **Adopt** →
  key-message-tiers core-message framing guidance.

canonical: this session's Read of this pr-communications-rulebook
checkout's `README.md` (`write_scope: []`, `produces`: comms plan / key
message / risk-Q&A prep only).

- Skip: public-relations-pr's broader campaign-workflow steps (media-list
  building, influencer tiering) sit outside this role's stated
  `produces` scope; left out of the fold-in.

## Gap line

The three existing plugins already gate structure (label order, field
presence, proof-point presence, pre-approval-mark presence); none of
them weigh content quality within an already-valid structure — the gap
the three adopted learnings above close.

Sources:
- https://api.github.com/repos/jamditis/claude-skills-journalism
- https://raw.githubusercontent.com/jamditis/claude-skills-journalism/master/journalism-core/skills/crisis-communications/SKILL.md
- https://raw.githubusercontent.com/jamditis/claude-skills-journalism/master/journalism-core/skills/story-pitch/SKILL.md
- https://api.github.com/repos/dmend3z/tribo-skills
- https://raw.githubusercontent.com/dmend3z/tribo-skills/main/plugins/public-relations-pr/skills/public-relations-pr/SKILL.md
- https://www.claudepluginhub.com/plugins/dmend3z-public-relations-pr-plugins-public-relations-pr
- https://api.github.com/repos/danielrosehill/Claude-PR-Media-Work-Plugin
- https://api.github.com/repos/jeremylongshore/claude-code-plugins-plus-skills
