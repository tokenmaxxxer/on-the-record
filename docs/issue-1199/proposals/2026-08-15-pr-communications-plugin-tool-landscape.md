---
subject: issue-1199
role: pr-communications
loop_state: scope-proposed
status: proposed
files:
  - key-message-tiers/README.md
  - race-sequence/README.md
  - qa-preapproval/checklists/qa-preapproval.md
  - docs/issue-1199/reports/pr-communications.md
---

# Proposal: fold Claude Code plugin/skill landscape into pr-communications rulebook (issue-1199)

All file paths above except this repo's own record live in the separate
rulebook repo (tokenmaxxxer/pr-communications-rulebook, cloned locally
at /home/jwjung/tokenmaxxxer/rulebooks/pr-communications-rulebook,
branch `issue-1199/pr-communications-plugin-landscape`) — see
docs/issue-1199/reports/pr-communications/scout-brief.md.

## Request

Per issue-1199's 2026-08-14 amendment (survey target: the Claude Code
plugin/skill ecosystem, not general PR-domain practitioner tools), add
native judgment-guidance sections to this role's three existing
plugins — `key-message-tiers`, `race-sequence`, `qa-preapproval` — drawn
from two adoption-evidenced Claude Code skill repos surveyed this turn
(`jamditis/claude-skills-journalism`'s `crisis-communications` and
`story-pitch` skills; `dmend3z/tribo-skills`'s `public-relations-pr`
skill). No new plugin, no tool-catalog section — additive prose inside
each plugin's existing README/checklist, per the 2026-08-13
native-application amendment.

## Constraints

- No tool attribution or tool-catalog section in rulebook text — the
  learnings fold in as native judgment; only this repo's own record
  cites the surveyed sources.
- Additive only: none of the three plugins' existing gate rules,
  mechanical checks, or prior guidance change shape.
- Stay inside this role's stated `produces` scope (comms plan / key
  message / risk-Q&A prep) — skip anything from the surveyed skills that
  belongs to a broader campaign workflow (media-list building,
  influencer tiering).

## What will be done

- `key-message-tiers/README.md`: a "Judgment guidance" section —
  proof-point strength (timeliness/exclusivity, not just truth) and
  audience-specific message re-casting.
- `race-sequence/README.md`: a "Judgment guidance" section — trigger-
  driven channel selection for Communication, and settled-vs-unsettled
  fact separation for Evaluation.
- `qa-preapproval/checklists/qa-preapproval.md`: one added checklist
  item — a holding-position rewrite required before pre-approval when a
  Q&A answer states an unsettled fact as if it were settled.

## Out of scope

- Any change to the three plugins' gate scripts (`hooks/*.sh`) or their
  mechanical check logic.
- Surveying general PR-domain tools (media monitoring platforms, wire
  services) — the 2026-08-14 amendment restricts survey sources to
  Claude Code plugins/skills.

## How you will know it worked

- Each of the three target files carries a new, clearly separated
  guidance block with no tool name/attribution inside the rulebook
  prose itself.
- This repo's `docs/issue-1199/reports/pr-communications.md` names
  which deliverable/rule each learning upgrades, with adoption evidence
  and source citations, per the issue's acceptance check.
- The rulebook repo's existing test suite (`tests/*-gate-test.sh`)
  still passes — the change is additive prose, not gate logic.
