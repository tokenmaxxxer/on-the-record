# Scout brief: release-engineering Claude Code plugin-ecosystem survey (issue-1199)

Mode: batched-sequential (WebSearch + WebFetch + `gh`/`curl` API calls,
one turn per round; no concurrent Agent fan-out used). Stages used: 2
(one sweep round via WebSearch, one deepening round fetching specific
agent/plugin files) — within the 5-stage / 3min budget.

## Sweep

Searched the Claude Code plugin/skill marketplace ecosystem for
release-engineering-relevant plugins (deployment, CI/CD, rollback,
config validation, versioning/changelog). Highest-adoption hits, by
GitHub stars — canonical: `curl -s https://api.github.com/repos/<org>/<repo>`,
run this session:

- `wshobson/agents` — 38,817 stars, 4,135 forks
- `hesreallyhim/awesome-claude-code` — 52,314 stars, 4,577 forks
- `davila7/claude-code-templates` — 30,248 stars, 3,398 forks
- `terrylica/cc-skills` — 62 stars, 10 forks (too low-adoption to use
  as a primary source; noted only as a rejected candidate)

## Deepening

`wshobson/agents` carries a `cloud-infrastructure` plugin with a
`deployment-engineer` agent and two purpose-built plugins:
`deployment-strategies` (rollback automation) and
`deployment-validation` (pre-deployment config checks). canonical:
`curl -s https://raw.githubusercontent.com/wshobson/agents/main/docs/plugins.md`,
run this session, output listing both plugin rows.

- **`deployment-engineer` agent** (`plugins/cloud-infrastructure/agents/deployment-engineer.md`).
  Problem: ad hoc deployments lack a repeatable safety contract. How:
  prescribes progressive delivery (canary/blue-green) over big-bang
  releases, "comprehensive health checks with automated rollback
  capabilities," and "immutable infrastructure principles with
  versioned deployments." canonical: WebFetch of that raw file URL,
  run this session, quoting those phrases.
  Gap check against current rulebook state: canonical:
  `/tmp/rb/release-engineering-rulebook/playbook/rollback-and-recovery.md`
  rules 2, 8, 12, read this session — already cover automated-
  rollback-on-threshold, toil-driven automation, and binary/config
  pairing, so this learning is already met, not missing.

- **`deployment-validation` plugin, `config-validate` command**
  (`plugins/deployment-validation/commands/config-validate.md`).
  Problem: config-only changes (not code) cause a second class of
  incident that a code-focused rollout gate misses — exposed secrets,
  schema drift, and prod/dev setting inconsistency. How: an 8-stage
  pipeline (config scan for secrets, JSON-Schema validation,
  environment-tiered rules — e.g. `require_https: True` and
  `require_encryption: True` in production but not dev — config test
  suites, runtime watch, semver-based config-format migration,
  encryption of sensitive values, auto-generated docs). canonical:
  WebFetch of that raw file URL, run this session, quoting those
  phrases.
  Gap check: canonical:
  `/tmp/rb/release-engineering-rulebook/playbook/deployment-rollout-strategy.md`
  and `rollback-and-recovery.md`, read this session in full — neither
  file carried a config/secret validation gate *before* rollout starts
  (they cover binary/config pairing *at* rollback time, not a
  pre-rollout scan) — this is the genuine gap the fold-in targets.

Judge point (saturation). canonical: the two gap-check citations in
the Deepening section directly above (the two rulebook file reads,
this session). Those reads show the two `wshobson/agents` plugins
above already supplied one confirmed-missing must-be (pre-rollout
config validation, tiered by environment) and one already-covered one
(automated rollback trigger). A second deepening round on
`davila7/claude-code-templates` or `awesome-claude-code` was checked
(canonical: WebFetch of both repos' root README pages, run this
session) and returned no additional release-specific agent/command
content, only a generic pointer toward documentation this session
could not resolve to a real path. Stopped at 2 stages: another round
would not change the fold-in decision.

## Fold-in decision

One rule added: `playbook/deployment-rollout-strategy.md` rule 13 —
pre-rollout config/secret validation, environment-tiered strictness.
Written natively (no tool name, no catalog section), per the
2026-08-13 operator amendment. canonical:
`/tmp/rb/release-engineering-rulebook/playbook/deployment-rollout-strategy.md`
rule 13, this session's own edit.

Sources:
- https://raw.githubusercontent.com/wshobson/agents/main/docs/plugins.md
- https://raw.githubusercontent.com/wshobson/agents/main/plugins/cloud-infrastructure/agents/deployment-engineer.md
- https://raw.githubusercontent.com/wshobson/agents/main/plugins/deployment-validation/commands/config-validate.md
- https://api.github.com/repos/wshobson/agents
- https://api.github.com/repos/hesreallyhim/awesome-claude-code
- https://api.github.com/repos/davila7/claude-code-templates
- https://api.github.com/repos/terrylica/cc-skills
