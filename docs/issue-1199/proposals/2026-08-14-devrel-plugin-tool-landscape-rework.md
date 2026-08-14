---
subject: issue-1199
role: devrel
loop_state: scope-proposed
status: proposed
files:
  - docs/handbooks/devrel-plugins.md
  - docs/issue-1199/reports/devrel.md
---

# Proposal: fold Claude Code plugin/skill landscape into devrel rulebook (issue-1199, 2026-08-14 amendment rework)

All file paths below except this repo's own record/proposal live in the
separate rulebook repo (tokenmaxxxer/devrel-rulebook, cloned this turn
at /tmp/devrel-rulebook-1199, branch `issue-1199/devrel-plugin-rework`)
— see docs/issue-1199/reports/devrel/scout-brief-plugins.md.

## Request

The 2026-08-14 amendment to issue-1199 supersedes the prior survey
target: the CLAUDE CODE PLUGIN/SKILL ecosystem (marketplace/community
plugins) relevant to devrel, not general devrel-domain practitioner
tools. Add a second, additive tool-learnings block to
docs/handbooks/devrel-plugins.md in tokenmaxxxer/devrel-rulebook: three
surveyed Claude Code plugins/skills, each with adoption evidence,
problem/how, and a named upgrade to existing gate-required field
content guidance.

## Problem/Motivation

canonical: docs/issue-1199/reports/devrel.md (this repo, read this
turn), commit e28ac55/c9ef5d2 in tokenmaxxxer/devrel-rulebook — the
2026-08-13 fold-in surveyed Docusaurus, Scalar, Stainless, ReadMe,
Orbit: general API-docs/SDK-gen/community-analytics platforms, none of
them a Claude Code plugin or skill. The issue's 2026-08-14 amendment
states explicitly that a fold-in whose surveyed sources are domain
tools alone does not satisfy the acceptance check, so devrel's tracker
line needs this additive rework before it can count toward the
issue-level 43/43.

## Proposed surface decision

Add one "Claude Code plugin/skill tool learnings (issue-1199, 2026-08-14
amendment)" section to docs/handbooks/devrel-plugins.md, placed after
the existing "Tool learnings (issue-1199)" section (kept, not removed —
the amendment adds a plugin/skill-sourced set, it does not retract the
prior domain-tool one). Three entries, each naming which existing
gate-required field/section it upgrades:

1. **anthropics/claude-plugins-official** (20.2k GitHub stars, 30+
   first-party + 15 partner plugins). `commit-commands`'
   `/commit-push-pr` chains commit-message generation, push, and PR
   creation into one step. Upgrades: guidance to generate the commit
   body and PR body from the same pass that wrote the record fields,
   reducing record/commit-trailer disagreement.
2. **mintlify/mintlify-claude-plugin** (official plugin, listed on
   Anthropic's own plugin directory). Converts non-Markdown source into
   MDX at generation time rather than post-hoc labeling. Upgrades:
   `doc-type:` guidance — pick doc-type before drafting when a
   generation tool is in the loop.
3. **changelog-generator plugin** (awesome-claude-plugins list;
   independently documented Trigger.dev worked example). Separates
   engineer-facing commits from customer-facing changelog entries.
   Upgrades: "Adoption-friction list" guidance — each entry states
   which audience (internal engineer vs. external adopter) it is
   written for.

docs/issue-1199/reports/devrel.md is phase-2 output, updated only after
this rework is applied, per contract v3 s19.

## Adoption-friction evidence

canonical: docs/issue-1199/reports/devrel/scout-brief-plugins.md (this
repo, written this turn) — the prior fold-in's friction guidance
(Stainless entry) already covers "sample code needs a version anchor";
this rework's friction-relevant addition is narrower: the
commit-commands entry specifically targets the record-to-commit-trailer
handoff point, a friction source the prior 5 entries did not name.

## Alternatives

- Replace the prior 5-entry domain-tool section outright — rejected:
  the amendment adds a survey-target correction, it does not instruct
  deleting prior work; domain tools remain valid secondary context per
  requirement 1's own wording ("may appear only as secondary context").
- A new standalone file for the plugin-sourced entries — rejected: same
  reasoning as the 2026-08-13 proposal's alternatives section — the one
  handbook file is where an author already reads guidance.

## User impact

Authors get 3 additional concrete content checks tied to the actual
Claude Code plugin/skill tooling they run inside their own authoring
sessions, on top of the 5 domain-tool checks already present; no gate
becomes stricter, no previously-passing proposal/record starts failing.

## Sources

See docs/issue-1199/reports/devrel/scout-brief-plugins.md for the full
source list (6 URLs consulted this turn).
