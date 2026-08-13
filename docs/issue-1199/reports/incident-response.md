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
comment body is exactly `APPROVE issue-1199/incident-response`). Worked
directly in the separate rulebook repo
(tokenmaxxxer/incident-response-rulebook, mounted at
/home/jwjung/tokenmaxxxer/rulebooks/incident-response-rulebook), on
branch issue-1199/tool-landscape:

- Added a bounded `playbook/tool-landscape.md` file (rule_count_floor
  4, five rule blocks including one REMOVAL entry) carrying four
  design-move learnings, each tagged with which of the five #1174
  axis files it upgrades — timeline-capture-at-record-time
  ([[timeline-construction]]), severity-tied-escalation
  ([[severity-classification-scoping]]), action-item-field-as-blocker
  ([[action-item-quality]]), and link-don't-duplicate-incident-record
  ([[timeline-construction]] + [[blameless-language-editing]]).
- Added a one-paragraph README Layout pointer to the new file, matching
  the existing `playbook/*.md` bullet style and citing the scout
  brief's location for adoption evidence rather than restating it.
- No existing playbook/*.md rule text changed or deleted; no gate
  logic touched, per the proposal's Out-of-scope list.
- Committed in the rulebook repo (commit
  3ab6e61da3c2623ccd7df6f288e34f008ef4667f, subject: issue-1199;
  canonical: `git -C
  /home/jwjung/tokenmaxxxer/rulebooks/incident-response-rulebook log -1
  --stat`, read this session), pushed to
  origin/issue-1199/tool-landscape, and opened a PR against
  tokenmaxxxer/incident-response-rulebook (canonical: `gh pr create`
  output this session).

## Why
Per issue-1199 (northpole req#1/req#5): the incident-response role's
rulebook encoded methodology (issue-1174's five axis files) but had
never surveyed the tool ecosystems incident-response practitioners
actually use, per the current-state survey's Gap finding (every
existing citation is written best-practice prose, never a tool's own
design move). The four adopted entries close that gap for the four
categories the scout brief actually surveyed (incident-management
platforms, on-call/paging, blameless-postmortem tool design,
status-page/incident-communication), each tied to a named existing
axis file per requirement 4.

## Upstream basis
docs/issue-1199/proposals/2026-08-13-incident-response-tool-landscape.md,
docs/issue-1199/reports/incident-response/current-state-survey.md,
docs/issue-1199/reports/incident-response/scout-brief.md

## Root cause of the gap this record closes
5-Whys causal chain (this record's subject is the survey's Gap finding,
not a service incident, so the "incident" analyzed here is the
methodology gap itself): the axis files cited only written
best-practice prose because issue-1174's build scoped source material
to named-practice literature, not tool-design analysis → because
issue-1174 ran before issue-1199 existed as a separate program → because
the two issues were deliberately split (issue-1199's own background:
"a SEPARATE program from #1174's rule-building"). Primary cause:
issue-1174's playbook build never had a tool-landscape survey in its
scope, by design. Contributing factors: the five axis files' own front
matter locks a layered citation convention (practitioner source, named
practice, comparison literature — canonical:
`playbook/rca-method-selection.md` front matter, read this session in
the rulebook repo) that does not distinguish a tool from a
practitioner's blog post about a tool, inviting exactly this gap; and
separately, no gate previously checked for tool-derived content, so the
gap was invisible until issue-1199's survey requirement made it
explicit.

## Action Items

- Jiwon Jung: check off the incident-response row in issue #1199's 43-item tracker by 2026-08-16.

## Open findings
None.

amendments-reconciled: issuecomment-5277555673 ("Judgment opened: PR
#? — candidate decision on branch `issue-1199/incident-response` (3
path(s) changed) entered delegated-judgment evaluation.") is an
automated delegated-judgment-evaluation notice about this session's own
phase-1 commit (the 3-file survey/scout-brief/proposal commit on this
branch) — canonical: `gh issue view 1199 --comments`, re-read this
session after the pr-preflight notice. It records that evaluation
opened; it carries no verdict, no requested change, and no content this
record needs to incorporate beyond acknowledging it here, so no content
amendment to this record is warranted.
