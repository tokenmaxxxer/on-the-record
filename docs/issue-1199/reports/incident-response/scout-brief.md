---
subject: issue-1199
role: incident-response
kind: scout-brief
---

# Scout brief: incident-response Claude Code plugin landscape (issue-1199, re-scout)

Supersedes this file's prior version, which surveyed general domain
incident-management tools (Rootly, PagerDuty, Upptime) rather than the
Claude Code plugin ecosystem the 2026-08-14 survey-target amendment
requires. Mode: parallel WebSearch fan-out, 3 angles in one turn
(Claude Code plugin-marketplace incident-response/postmortem skills;
Claude Code SRE/on-call/runbook agents; Claude Code blameless-
postmortem/RCA skills), then one judge point, no further deepening.
1 sweep stage, 1 judge point, well under the 5-stage / 3-min budget.

## Category: incident-management orchestration (official)

- **Anthropic `claude-cookbooks` — `managed_agents/
  sre_incident_responder.ipynb`** — 51,517 GitHub stars on the parent
  repo (adoption evidence: `curl -s
  https://api.github.com/repos/anthropics/claude-cookbooks`, this
  session). First-party design: coordinates multiple specialized
  agents through detection → investigation → mitigation → postmortem
  phases, with severity (P0-P3) driving which phase-gate runs next and
  who/what gets invoked, and integrates PagerDuty/Prometheus/
  OpenTelemetry as inputs rather than as the thing being surveyed.

Must-be: severity is not a document-depth label alone — it is the
input that decides which phase runs next and who gets paged.

## Category: Claude Code plugin marketplace catalogs

- **`rohitg00/awesome-claude-code-toolkit`** — 2,509 GitHub stars
  (`curl -s
  https://api.github.com/repos/rohitg00/awesome-claude-code-toolkit`,
  this session), self-reported 176+ plugins, 368 skills. Bundles a
  runbook-generator skill that builds operational documentation by
  scanning actual infrastructure/source code (tech-stack detection,
  CI/CD, database, hosting) rather than free-hand authoring.
- Multiple independently-listed marketplace entries for incident-
  response/postmortem skills across mcpmarket.com, awesomeskill.ai,
  claudedirectory.org, claudemarketplaces.com — a four-tier severity
  system (P0-P3) and Incident Commander role recur across listings
  (multi-source convergence, adoption-evidence method).

Must-be: operational documentation and runbooks are generated FROM the
system's actual current state, not hand-typed from memory.

## Category: blameless-postmortem / RCA skill design (cross-cutting)

Independently listed across at least four separate marketplaces
(mcpmarket.com — three distinct listing pages, awesomeskill.ai,
getclaudeskills.com, claudeskills.info), converging on the same shape:
reconstruct a timestamped event timeline, quantify impact, run 5-Whys
to separate root cause from contributing factors, and — per several
listings' explicit framing — treat "what is still missing from this
timeline/analysis" as its own deliberate check, distinct from whether
the entries already drafted are worded correctly.

Must-be: a thoroughness check is a separate step from a
wording/format check — both are needed, and skipping the former
because the latter checked out cleanly is the common failure these
skills structure against.

## Judge point (saturation)

Three angles converged on two decision surfaces the current axis files
already own (severity → response-shape / escalation ~
severity-classification-scoping; timeline thoroughness ~
timeline-construction). No angle surfaced a decision surface the
existing five axis files don't already own, and no fourth angle would
change an adopt/skip call — stopped here.

## Adopt / skip

- **Adopt**: severity-drives-phase-gate-shape (Anthropic's own
  incident-responder cookbook) → upgrades
  `severity-classification-scoping.md` with a rule that severity pins
  the response's phase-gate shape, not only document depth.
- **Adopt**: system-record thoroughness check as its own step, separate
  from format/wording checks (the multi-source blameless-postmortem
  skill pattern, reinforced by the runbook-generator's
  generate-from-actual-state design) → upgrades
  `timeline-construction.md` with a rule that requires one explicit
  sweep against the actual system record before the timeline is
  treated as ready.
- **Skip**: any specific plugin's UI, its exact severity-tier
  vocabulary (P0-P3 vs. this rulebook's SEV1-5), its specific
  integration list (PagerDuty/Prometheus/OpenTelemetry), or its
  specific agent-orchestration primitives — cloning any one plugin's
  exact model would violate the scout directive's never-clone-the-
  exemplar rule; only the design MOVE is adopted, and per the 2026-08-13
  native-application amendment, neither the plugin name nor a
  tool-catalog section may appear in the rulebook's rule text — the
  adoption-evidence trail stays in this brief and the phase-2 record
  instead.

## Sources

```
https://platform.claude.com/cookbook/managed-agents-sre-incident-responder
https://github.com/anthropics/claude-cookbooks/blob/main/managed_agents/sre_incident_responder.ipynb
https://github.com/rohitg00/awesome-claude-code-toolkit
https://mcpmarket.com/tools/skills/incident-response-manager
https://mcpmarket.com/tools/skills/incident-response
https://mcpmarket.com/tools/skills/incident-response-sre-workflow-1
https://www.claudedirectory.org/plugins/incident-response
https://mcpmarket.com/tools/skills/postmortem-analysis
https://mcpmarket.com/tools/skills/operational-runbook-generator
https://mcpmarket.com/tools/skills/postmortem-analysis-1
https://mcpmarket.com/tools/skills/postmortem-writing-3
https://www.getclaudeskills.com/skills/incident-post-mortem-github
https://claudeskills.info/skills/github/awesome-copilot/incident-postmortem/
```
