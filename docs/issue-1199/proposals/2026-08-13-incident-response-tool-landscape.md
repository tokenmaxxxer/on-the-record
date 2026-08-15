---
status: proposed
files:
  - docs/issue-1199/proposals/2026-08-13-incident-response-tool-landscape.md
---

# issue-1199 (incident-response): tool-landscape fold-in

kind: proposal
subject: issue-1199

Proposal: docs/issue-1199/proposals/2026-08-13-incident-response-tool-landscape.md

## Background

Issue #1199 (northpole req#1/req#5) asks every role to survey the
plugins/tools practitioners in its domain actually use, with adoption
evidence, and fold distilled learnings into a bounded rulebook section
naming which deliverable/rule/judgment each learning upgrades — separate
from #1174's playbook build. Read basis:
`docs/issue-1199/reports/incident-response/current-state-survey.md` and
`docs/issue-1199/reports/incident-response/scout-brief.md` (both written
this session). The rulebook already carries #1174's five `playbook/*.md`
axis files (severity-classification-scoping, rca-method-selection,
action-item-quality, blameless-language-editing, timeline-construction)
— canonical: `find /home/jwjung/tokenmaxxxer/rulebooks/incident-response-rulebook/playbook
-maxdepth 1` output this session — but none names a tool or a
tool-derived design move; every citation is written best-practice prose,
never the product's own automation/UI move (survey's Gap section). This
proposal is the missing fold-in.

## Target reader

A phase-2 implementing session (this role) adding a new
`playbook/tool-landscape.md` file to
tokenmaxxxer/incident-response-rulebook, following the existing
axis-file shape (front matter + condition→choice→source rule blocks),
with no further scouting needed — the scout brief already carries the
sourced findings.

## Proposed structure

New file `playbook/tool-landscape.md`, `rule_count_floor: 4` (below the
existing axis files' floor of 4-per-axis-at-20-total design intent,
sized to the scout brief's four adopted findings — a fold-in bounded by
requirement 3's "not a tool catalog," not a sixth full decision axis).
Content, per the scout brief's Adopt list:

1. **timeline_capture_at_record_time** — when: building the `timeline`
   field. choice: capture events into the timeline AS they happen
   (paste/export from the live incident channel at record time) rather
   than reconstructing from memory after the incident closes. source:
   Rootly/incident.io auto-timeline-capture-from-chat design, scout
   brief §incident-management platforms. Upgrades:
   `timeline-construction.md` rule 1 (currently states the falsifiable-
   event standard but not the *capture-timing* discipline that makes it
   achievable).
2. **severity_tied_escalation** — when: an incident is classified SEV1
   or SEV2. choice: name the escalation-chain shape (who gets paged,
   in what order) as part of the severity classification itself, not a
   separate concern left to whatever paging tool is in use. source:
   PagerDuty/Opsgenie's severity-driven escalation-chain routing, scout
   brief §on-call/paging. Upgrades: `severity-classification-scoping.md`,
   currently silent on who-gets-paged, only on document depth.
3. **action_item_field_as_blocker** — when: drafting an action item.
   choice: treat a missing owner, verb, outcome, or deadline as a
   blocking gap that stops the item from entering the tracked list at
   all — mirror how the surveyed postmortem tools structurally refuse
   to create an action item without those fields, rather than writing
   the fields as an advisory shape check applied after the fact. source:
   Rootly/incident.io action-item creation flow, scout brief §blameless-
   postmortem tool design. Upgrades: `action-item-quality.md` rule 1
   (already lists the four fields; this reframes the check from advisory
   to blocking, matching `incident-response-action-item-gate`'s own
   mechanical enforcement).
4. **link_dont_duplicate_incident_record** — when: the org already
   tracks the live incident somewhere (an issue, a channel, a paging
   event). choice: link the postmortem's timeline/impact sections to
   that live record instead of re-typing its content — Upptime's
   design collapses the incident record and the public communication
   artifact into the same GitHub Issue rather than hand-copying between
   them. source: Upptime (17.1k stars), scout brief §status-page /
   incident-communication. Upgrades: `timeline-construction.md` and
   `blameless-language-editing.md`, both of which currently assume the
   postmortem doc is authored from scratch.

Each entry keeps the axis files' shape: condition → choice → source,
tagged with which existing playbook file's judgment it upgrades (issue
requirement 4). Adoption-evidence citations (stars, customer counts,
acquisition/market signal, multi-source comparison mentions) live in the
scout brief, referenced by name here rather than restated, to keep this
file bounded per requirement 3.

## Rationale

- Bounded fold-in (issue requirement 3, consult finding): four entries,
  each tracing to one scout-brief Adopt-list finding and one named
  upgrade target, per requirement 4's "each learning traces to the
  surveyed tool" bar. The scout brief's four Skip items (vendor-specific
  UI/taxonomy/schema) are deliberately excluded, per the scout
  directive's never-clone-the-exemplar rule.
- Adoption evidence routed through the scout's WebSearch trail (issue
  requirement 1: stars, reported customer counts, acquisition signal,
  multi-source comparison mentions), never pretrained-recall —
  `docs/issue-1199/reports/incident-response/scout-brief.md`'s Sources
  list carries every citation.
- This role's own decision boundary (contract v3's proposal-evidence-
  gate requirement): entry 3 ties directly back to this role's existing
  mechanical gate (`incident-response-action-item-gate`) rather than
  introducing a new judgment surface — the fold-in makes an existing
  gate's intent explicit in the playbook prose, it does not add scope
  the gate does not already enforce.
- `rule_count_floor: 4` mirrors each existing axis file's own per-axis
  floor while staying a single bounded file rather than a sixth full
  axis, sized to what the scout brief actually supports.

## Plan for phase 2

1. Add `playbook/tool-landscape.md` to
   tokenmaxxxer/incident-response-rulebook, branch
   `issue-1199/tool-landscape`, with the four entries above in the
   existing playbook/*.md rule-block shape.
2. Add a README Layout line pointing to the new file, mirroring the
   existing playbook/*.md bullet.
3. Open a PR against tokenmaxxxer/incident-response-rulebook; land the
   PR URL and diff summary in `docs/issue-1199/reports/incident-response.md`
   (this repo's phase-2 record, gated behind the `APPROVE
   issue-1199/incident-response` comment per contract v3 s19 — already
   posted, canonical: `gh issue view 1199 --comments`, read this
   session).
4. Check off the incident-response row in issue #1199's 43-item tracker
   once the rulebook PR is opened.

## Out of scope

- Adding tool-landscape sections for any role other than
  incident-response — each role's fan-out unit is separate per issue
  requirement 6 (distinct branches, never shared).
- Building the shape-check gate extending `gates/playbook_depth_gate.py`
  for entry-completeness (issue Acceptance check 1) — that is the
  issue's step-1 infra unit, not a per-role fan-out unit.
- Cloning any surveyed vendor's specific UI, workflow-primitive
  taxonomy, or escalation-policy schema — scout brief's explicit
  adopt/skip call, per scout-directive's "never clone the exemplar"
  rule.
- Touching the 43-item tracker for any row but incident-response's own.
- Rewriting any existing rule text in the five #1174 axis files — the
  fold-in is additive only, per the brand-design/technical-writing
  precedent this proposal follows.

## Approval

`APPROVE issue-1199/incident-response` was already posted to this issue
as an issue-level comment (single-account mode; canonical: `gh issue
view 1199 --comments`, read this session — trailing comment body is
exactly that string) before this proposal was written, so phase 2 (the
rulebook PR and this repo's phase-2 record) may proceed directly
following this proposal's commit.
