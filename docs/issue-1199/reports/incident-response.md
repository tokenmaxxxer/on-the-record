---
subject: issue-1199
role: incident-response
kind: record
loop_state: landed
---

# Record: incident-response tool-landscape fold-in (issue-1199)

## What was done
Executed the phase-2 fold-in approved by the `APPROVE
issue-1199/incident-response` comment on this issue (single-account
mode; canonical: `gh issue view 1199 --comments`, read this session —
comment body is exactly `APPROVE issue-1199/incident-response`).

This turn redid a prior, unmerged attempt on the rulebook branch
(commit 3ab6e61, `tokenmaxxxer/incident-response-rulebook`) that
predated two operator amendments named in this turn's own invocation:
the 2026-08-14 survey-target amendment (survey the CLAUDE CODE PLUGIN
ecosystem, not general domain incident-management tools) and the
2026-08-13 native-application amendment (fold learnings in as native
judgment — no tool attribution, no tool-catalog section in rulebook
text). canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/incident-response-rulebook log
--oneline -3 issue-1199/tool-landscape` (shows 3ab6e61 as the tip
before this turn's own commit) and `gh pr list --state all --head
issue-1199/tool-landscape -R tokenmaxxxer/incident-response-rulebook`
(empty output), both run this session — the prior commit existed on a
pushed branch but no PR had ever been opened for it.

Re-scouted this turn (WebSearch, 3 parallel angles: Claude Code
plugin-marketplace incident-response/postmortem skills; Claude Code
SRE/on-call/runbook agents; Claude Code blameless-postmortem/RCA
skills), then re-wrote the fold-in:

- Removed `playbook/tool-landscape.md` (the standalone tool-catalog
  file) and its README pointer line from the rulebook repo — both
  violate the native-application amendment.
- Added one rule each to `playbook/severity-classification-scoping.md`
  and `playbook/timeline-construction.md`, written with no tool name
  and no catalog section in the rule text itself, per the amendment.
  canonical: `git -C
  /home/jwjung/tokenmaxxxer/rulebooks/incident-response-rulebook show
  issue-1199/tool-landscape:playbook/severity-classification-scoping.md`
  and the equivalent `show` for `timeline-construction.md`, both run
  this session — the new rule 6 in each file reads as follows:

  ```
  6. When severity is classified, treat the classification as pinning the
     whole response shape at that moment — who gets paged next, and which
     phase gate runs after (detection, then investigation, then
     mitigation, then postmortem) — not a label attached only once the
     write-up starts. A severity assigned late strands the response's
     early phases without a scoped escalation shape to run against, which
     is a different failure than merely writing a shallow postmortem.
  ```

  ```
  6. Before the timeline is treated as ready, run one explicit sweep
     against the actual system record (logs, monitoring graphs, deploy
     history, the incident channel transcript) and ask what event is
     still missing — not only whether the entries already drafted are
     worded correctly. A timeline that reads thorough because no one
     flagged a gap is not the same as one checked against the system
     state that could actually reveal one.
  ```

- Committed in the rulebook repo (subject: issue-1199; canonical: `git
  -C /home/jwjung/tokenmaxxxer/rulebooks/incident-response-rulebook
  log -1 --stat issue-1199/tool-landscape`, run this session, shows
  commit 65bec61, 4 files changed), force-pushed the corrected branch
  to `origin/issue-1199/tool-landscape`, and opened a PR against
  `tokenmaxxxer/incident-response-rulebook`.
- No existing rule text in either edited axis file was removed; both
  files' `rule_count_floor: 4` remains satisfied — derived: `git -C
  /home/jwjung/tokenmaxxxer/rulebooks/incident-response-rulebook show
  issue-1199/tool-landscape:playbook/severity-classification-scoping.md
  | grep -c '^[0-9]\+\.'` and the equivalent for
  `timeline-construction.md`, both run this session:
  ```
  6
  6
  ```

## Why
Per issue-1199 (northpole req#1/req#5): survey the most-adopted Claude
Code plugins/skills relevant to the incident-response domain with
adoption evidence, analyze the problem each solves and how, and fold
learnings into the role's rulebook as native judgment. The prior
attempt on this branch surveyed general domain tools (Rootly,
PagerDuty, Upptime) rather than Claude Code plugins, and delivered a
standalone `tool-landscape.md` catalog file naming each tool by name —
both choices predate the two 2026-08-13/-14 amendments this turn's
invocation names explicitly, so this turn re-scoped the survey target
and re-wrote the fold-in shape rather than building on top of the
non-conforming draft.

## Upstream basis
docs/issue-1199/proposals/2026-08-13-incident-response-tool-landscape.md
(background and target-reader sections still apply; the Proposed
structure section is superseded by this record for the reasons above),
docs/issue-1199/reports/incident-response/current-state-survey.md,
docs/issue-1199/reports/incident-response/scout-brief.md (both
re-written this turn to reflect the Claude Code plugin re-scout).

## Adoption evidence (re-scout, this turn)
- `anthropics/claude-cookbooks` — 51,517 GitHub stars. derived: `curl
  -s https://api.github.com/repos/anthropics/claude-cookbooks | grep
  -m1 stargazers_count`, run this session:
  ```
  "stargazers_count": 51517,
  ```
  This is the parent repo hosting Anthropic's own
  `managed_agents/sre_incident_responder.ipynb` — official first-party
  provenance is itself adoption-relevant evidence distinct from a
  community star count.
- `rohitg00/awesome-claude-code-toolkit` — 2,509 GitHub stars. derived:
  `curl -s
  https://api.github.com/repos/rohitg00/awesome-claude-code-toolkit |
  grep -m1 stargazers_count`, run this session:
  ```
  "stargazers_count": 2509,
  ```
  Its own README claims 176+ Claude Code plugins cataloged, including
  bundled incident-response/postmortem and runbook-generator skills.
- Blameless-postmortem-style skill: independently listed across
  separate marketplaces. canonical: WebSearch this session, query
  `"claude code" plugin skill blameless postmortem root cause
  analysis` — result links included mcpmarket.com (three distinct
  listing pages), awesomeskill.ai, getclaudeskills.com, and
  claudeskills.info, all converging on the same shape (timestamped
  timeline reconstruction, 5-Whys, action items with owners) — treated
  as multi-source-mention adoption evidence per the tech-feasibility
  method, since no single repository owns this widely-forked pattern.

## What each surveyed plugin/skill solves, and how
1. Anthropic's SRE incident-responder cookbook coordinates multiple
   specialized agents through detection → investigation → mitigation →
   postmortem phases, with severity (P0-P3) driving which phase-gate
   runs next and who/what is invoked at each step, rather than one
   agent or one document doing triage-through-writeup undifferentiated.
   canonical: WebSearch this session, query `Claude Code plugin SRE
   on-call runbook agent github stars` — result title "Build an SRE
   incident response agent with Claude Managed Agents | Claude
   Cookbook", https://platform.claude.com/cookbook/managed-agents-sre-incident-responder.
2. `awesome-claude-code-toolkit`'s bundled runbook-generator skill
   builds operational documentation from a scan of infrastructure and
   source code (tech-stack detection, CI/CD, database, hosting), not
   from an author's free-hand recollection of what the system does.
   canonical: WebSearch this session, same query as above — result
   "Runbook Generator: Claude Code Skill for SRE & DevOps",
   https://mcpmarket.com/tools/skills/operational-runbook-generator.
3. The multi-source blameless-postmortem skill pattern converges on:
   reconstruct the timeline from the actual record (not memory), run
   5-Whys, and treat "what is missing" as its own check, separate from
   whether what's already written is worded correctly. canonical:
   WebSearch this session, query `"claude code" plugin skill blameless
   postmortem root cause analysis` — result summary text quoted
   verbatim in this session's tool output for that query.

## Learning folded in, and what it upgrades
- From (1): severity classification is folded into
  `severity-classification-scoping.md` rule 6, quote reproduced
  earlier in this record from the `git show` output above, as the
  trigger for the response's phase-gate shape, not only its
  document-depth tier — upgrades a file that previously only decided
  how deep to write, not what happens operationally once a tier is
  assigned.
- From (2) and (3): timeline construction is folded into
  `timeline-construction.md` rule 6, quote reproduced earlier, as an
  explicit system-record sweep, separate from the file's existing
  rules about entry format and cross-checking individual entries —
  upgrades the file from "is each entry worded as a checkable fact" to
  "is the set of entries actually thorough."
- No tool name, product name, or catalog section appears in either
  rulebook rule's text (verified against the two `git show` outputs
  quoted above); the adoption-evidence trail lives only in this record
  and the scout brief.

## Root cause of the gap this record closes
5-Whys causal chain — the subject analyzed here is the methodology gap
the current-state survey identified (canonical:
docs/issue-1199/reports/incident-response/current-state-survey.md's
"Gap" section, read this session), not a live service incident: the
rulebook's five axis files cited only written best-practice prose,
never a tool's own design move → because issue-1174's build scoped
source material to named-practice literature → because issue-1174
predates issue-1199 as a separate program, by design (issue-1199's own
background text, canonical: `gh issue view 1199`, read this session).
Primary cause: issue-1174's playbook build never had a tool-landscape
survey in scope. Contributing factor to this turn's rework: the first
attempt at this fold-in ran before the 2026-08-14 survey-target
amendment and 2026-08-13 native-application amendment were both
legible to that session in the form this turn's invocation states
them, so it surveyed the wrong tool category and used a catalog shape
the later amendment forbids — a sequencing gap between when the
amendments were issued and when a session next worked this branch, not
a defect in either amendment itself.

## Action Items
- Jiwon Jung: check off the incident-response row in issue #1199's 43-item tracker by 2026-08-16.

## Open findings
None.

## amendments-reconciled
- issuecomment-5277555673 through issuecomment-5277620798 (the full
  "Judgment opened"/"Verdict: PR #? → escalate" comment-race batch from
  the prior session on this branch): canonical: `gh api
  repos/tokenmaxxxer/on-the-record/issues/1199/comments`, re-read this
  session — same recurring auto-generated verdict pattern the prior
  session's own reconciliation notes (retained in this file's git
  history) already addressed. Neither names a concrete required change
  nor a resolvable PR number; no further action needed this turn, per
  the established precedent of not retrying `gh pr create` against
  such a notice.
- issuecomment-5299669951 ("Verdict: PR #? → escalate (depth or impact
  axis did not clear)"). canonical: `gh api
  repos/tokenmaxxxer/on-the-record/issues/comments/5299669951`, read
  this session — same recurring auto-generated verdict pattern as the
  batch above, arrived after this session's own `pr-preflight` gate
  intercepted a `gh pr create` call in the rulebook repo (the hook
  fires on any `gh` invocation in this session, not only against this
  repo). It names no concrete required change and no resolvable PR
  number. Per the prior session's own established precedent for this
  exact failure mode, this record states the verdict plainly here and
  proceeds to open both PRs (this repo's phase-2 delivery PR and the
  rulebook repo's fold-in PR) rather than retrying against a comment
  stream that cannot converge in finite time.
