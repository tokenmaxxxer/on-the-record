---
subject: issue-1199
role: release-engineering
kind: record
loop_state: landed
---

# Record: release-engineering tool-landscape fold-in (issue-1199)

## What was done
Executed the phase-2 fold-in unlocked by an `APPROVE
issue-1199/release-engineering` comment on this issue. canonical: `gh
issue view 1199 --repo tokenmaxxxer/on-the-record --json comments`, run
this session — comment body exactly `APPROVE
issue-1199/release-engineering`, posted by JiwonJung94 (listed in
`docs/specs/approvers.md`, read this session) at
2026-08-15T02:37:00Z, with an earlier identical comment at
2026-08-13T07:37:04Z.

Surveyed the Claude Code plugin/skill marketplace ecosystem for
release-engineering-relevant plugins/agents, per the tech-feasibility
adoption-evidence method. Sweep, deepening, and saturation judgment
detail live at
`docs/issue-1199/reports/release-engineering/scout-brief.md` (commit
`a5a85edc` on this branch).

Adoption evidence. canonical: `curl -s
https://api.github.com/repos/<org>/<repo>` for each repo below, run
this session:
- `wshobson/agents` — 38,817 stars, 4,135 forks
- `hesreallyhim/awesome-claude-code` — 52,314 stars, 4,577 forks
- `davila7/claude-code-templates` — 30,248 stars, 3,398 forks

Two release-relevant plugins live inside `wshobson/agents`. canonical:
`curl -s https://raw.githubusercontent.com/wshobson/agents/main/docs/plugins.md`,
run this session, listing both plugin rows.

1. **`deployment-engineer` agent** (`cloud-infrastructure` plugin).
   Problem it solves: ad hoc, judgment-call deployments lack a
   repeatable safety contract. How: prescribes progressive delivery
   (canary/blue-green over big-bang), automated rollback tied to
   health checks, and immutable versioned artifacts. canonical:
   WebFetch of
   `https://raw.githubusercontent.com/wshobson/agents/main/plugins/cloud-infrastructure/agents/deployment-engineer.md`,
   run this session, quoting "comprehensive health checks with
   automated rollback capabilities" and "immutable infrastructure
   principles with versioned deployments."
   Fold-in check. canonical:
   `/tmp/rb/release-engineering-rulebook/playbook/rollback-and-recovery.md`
   rules 2, 8, 12, read this session — the rulebook already encodes
   this design move (automated rollback on a pre-declared threshold,
   toil-driven automation of the rollback path, binary/config-pairing
   verification). No new rule added for this one; recorded as
   already-met.

2. **`deployment-validation` plugin, `config-validate` command**.
   Problem it solves: config-only changes (secrets, schema drift,
   prod/dev setting divergence) cause a class of incident a
   code-focused rollout gate misses entirely. How: an 8-stage
   pipeline — secret-exposure scan, JSON-Schema validation,
   environment-tiered required fields (e.g. HTTPS and
   encryption-at-rest required in production, optional in dev),
   config test suites, and semver-based config-format migration.
   canonical: WebFetch of
   `https://raw.githubusercontent.com/wshobson/agents/main/plugins/deployment-validation/commands/config-validate.md`,
   run this session.
   Fold-in check. canonical:
   `/tmp/rb/release-engineering-rulebook/playbook/deployment-rollout-strategy.md`
   and `rollback-and-recovery.md`, both read this session in full —
   neither file had a pre-rollout config/secret validation gate
   (existing coverage is binary/config pairing at rollback time, not a
   pre-rollout scan). This was the genuine gap.

Added that one learning to
`tokenmaxxxer/release-engineering-rulebook`'s
`playbook/deployment-rollout-strategy.md` as native rule 13
(environment-tiered pre-rollout config/secret validation), sourced to
`sre.google`'s "Release Engineering" hermetic-inputs framing — no
plugin/tool name, no tool-catalog section, per the native-application
requirement stated in this issue's own body. canonical:
`/tmp/rb/release-engineering-rulebook/playbook/deployment-rollout-strategy.md`
rule 13, this session's own edit. acceptance: `git -C
/tmp/rb/release-engineering-rulebook log --oneline -1` — result:
`64154bc release-engineering: add pre-rollout config validation rule
(issue-1199)`, on branch `issue-1199/release-engineering`, pushed to
origin. acceptance: `git -C /tmp/rb/release-engineering-rulebook
ls-remote origin issue-1199/release-engineering` — result: same sha
`64154bc` present on the remote. Opened as
`tokenmaxxxer/release-engineering-rulebook` PR #51
(https://github.com/tokenmaxxxer/release-engineering-rulebook/pull/51).

## Why
Issue #1199's body requires every role's rulebook to fold in learnings
from its domain's most-adopted Claude Code plugins/skills (2026-08-14
amendment quoted in the issue body), applied as native judgment rules
rather than a tool catalog (2026-08-13 amendment, same issue body), so
this role's deliverables reach practitioner-tool completeness per
northpole req#1 (docs/specs/northpole.md, cited in the issue body).

## Upstream basis
`docs/issue-1199/reports/release-engineering/scout-brief.md`, commit
`a5a85edc` on this branch.

## Open findings
canonical: the two `acceptance:` lines above (`git log`/`git
ls-remote` against `/tmp/rb/release-engineering-rulebook`, both run
this session). The rulebook commit is confirmed present on the pushed
remote branch. No open finding from this session's own survey or
fold-in.
