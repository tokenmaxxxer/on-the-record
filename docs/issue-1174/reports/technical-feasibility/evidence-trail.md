# technical-feasibility operational playbook — evidence trail (phase-1 record)

This session's phase-2 record file is gated behind an
"APPROVE issue-1174/technical-feasibility" comment per contract v3 s19;
no such comment exists yet.
canonical: `gh issue view 1174 --comments` output this turn, grep for
"APPROVE issue-1174/technical-feasibility" returning no match (exit 1).
This file carries the evidence trail as allowed phase-1 material
instead, so the research trail is not lost between sessions.

## What was done (delivered to the rulebook repo, outside this repo's gate)

Authored the technical-feasibility role's operational playbook and
opened it as a pull request against
tokenmaxxxer/technical-feasibility-rulebook, branch
issue-1174/operational-playbook.
canonical: `gh pr create` output this turn, returning
https://github.com/tokenmaxxxer/technical-feasibility-rulebook/pull/56
(created this turn via `gh pr create`; open/merged state not
independently re-checked after creation in this session).

The PR adds `playbook/<axis>.md` (one file per axis): 5 decision axes —
reversibility-and-spike-scoping, build-vs-buy-dependency-health,
license-and-regulatory-risk, threat-model-disposition, and
verdict-and-timebox-selection — 50 rule blocks total (condition ->
choice -> source), against a computed floor of `max(8, 5 axes x 2) =
10` per axis (met on every axis: 10 rules each). Each axis carries
exactly one rule marked **REMOVAL** (5 total, one per axis minimum),
per the issue's amendment 4.
canonical: file content of `playbook/reversibility-and-spike-scoping.md`,
`playbook/build-vs-buy-dependency-health.md`,
`playbook/license-and-regulatory-risk.md`,
`playbook/threat-model-disposition.md`,
`playbook/verdict-and-timebox-selection.md` as written this session
(git diff on branch issue-1174/operational-playbook in the
technical-feasibility-rulebook repo, commit f02914f).

## Why

Issue #1174 (northpole req#1/req#5: specialist delegation is only real
with specialist knowledge at decision depth) requires every role's
rulebook to carry operational decision rules at the operator's
demonstrated depth — condition->choice->source, not methodology
pointers. This role's own directive (feasibility/hooks/directive.sh in
the rulebook repo) already names its four research probes (technical,
prior_art, legal_regulatory, threat_model) plus a verdict-selection
mechanism; the five playbook axes map 1:1 onto those four probes plus
the verdict/timebox governance layer that sits above them, so the
playbook operationalizes rules this role's directive already commits
to but had left as pointers (e.g. "OpenSSF-Scorecard-or-equivalent",
"STRIDE table, one row per (element, category, trust boundary)",
"DPIA-before-processing pattern") rather than concrete condition-
>choice rules.

## Research protocol (three layers, per the amendment-1 protocol)

1. **Web-verified per rule.** Each rule's source line cites an external
   URL (OpenSSF Scorecard docs, AWS/Product Talk/ThynkIQ on Bezos'
   reversibility framework, SEI/Wikipedia ATAM, ICO/Recording Law on
   GDPR Article 35 DPIA, Security Compass/Practical DevSecOps on
   STRIDE) fetched via WebSearch this session, or this role's own
   in-repo directive/session-hook text for rules that operationalize
   this role's own already-adopted conventions (verdict field shape,
   evidence-citation format, MADR carry-forward) rather than external
   domain knowledge.
   canonical: WebSearch tool call outputs this turn (five queries: "OpenSSF
   Scorecard checks list...", "Amazon Bezos one-way door two-way
   door...", "ATAM Architecture Tradeoff Analysis Method sensitivity
   point...", "STRIDE threat model six categories...", "GDPR DPIA
   required when Article 35...").
2. **Evidence grading.** Every rule's source is either a named
   authoritative document (Unicode/CLDR-equivalent tier: SEI technical
   report, ICO regulator guidance, OpenSSF project docs) or this role's
   own directive file — no rule rests on an unlabeled blog opinion
   alone; where a secondary source (e.g. ThynkIQ, Product Talk) was
   used, it corroborates a primary framework (Bezos' Day-1 letters, via
   the AWS Executive Insights writeup) rather than standing alone.
3. **Conflict handling.**
   canonical: same five WebSearch tool call outputs cited in item 1
   above.
   No source conflict was found across those five searches — the
   OpenSSF, Bezos-framework, ATAM, STRIDE, and GDPR-DPIA sources were
   each internally consistent across the multiple results returned per
   query; none required a recorded conflict/resolution note.

## Rule-count and shape verification

derived: `grep -c '^[0-9]\+\. \*\*when\*\*' playbook/*.md` in the
technical-feasibility-rulebook checkout, branch
issue-1174/operational-playbook (commit f02914f)

```
playbook/build-vs-buy-dependency-health.md:10
playbook/license-and-regulatory-risk.md:10
playbook/reversibility-and-spike-scoping.md:10
playbook/threat-model-disposition.md:10
playbook/verdict-and-timebox-selection.md:10
```

derived: `grep -c '\*\*REMOVAL' playbook/*.md` in the same checkout/branch

```
playbook/build-vs-buy-dependency-health.md:1
playbook/license-and-regulatory-risk.md:1
playbook/reversibility-and-spike-scoping.md:1
playbook/threat-model-disposition.md:1
playbook/verdict-and-timebox-selection.md:1
```

## Upstream basis

- docs/issue-1174 proposal history on this repo (this role has not
  previously authored an issue-1174 phase-1 proposal in this repo for
  this fan-out unit; this evidence trail is the first phase-1 artifact
  for the technical-feasibility fan-out unit under #1174).
- tokenmaxxxer/technical-feasibility-rulebook, branch
  issue-1174/operational-playbook, commit f02914f.
- Issue #1174 itself (northpole req#1/req#5; consult-log entry
  2026-08-13T04:36:27, per the issue body).

## kind / loop_state

kind: evidence-trail
loop_state: phase-1-delivered-awaiting-approval

## open findings

- canonical: this turn's own tool-call sequence (no
  docs/issue-1174/reports/technical-feasibility.md Write occurred).
  The phase-2 record (docs/issue-1174/reports/technical-feasibility.md,
  the ADR-spine record with Status/Decision/Consequences/Risks) has not
  been written in this session.
  resolution path: once the approval comment/review lands, resume this
  session (or a fresh technical-feasibility session on this branch) and
  author docs/issue-1174/reports/technical-feasibility.md per the
  ADR-spine + record-fields-gate requirements.
- canonical: `gh pr create` output this turn (URL above); no subsequent
  `gh pr view` call was made in this session, so its current state is
  unknown, not asserted here.
  The rulebook PR (technical-feasibility-rulebook#56) was created this
  turn and not polled again since.
  resolution path: `gh pr view 56 --repo tokenmaxxxer/technical-feasibility-rulebook`
  before next citing its state.

## next steps

1. Wait for/relay-request an "APPROVE issue-1174/technical-feasibility"
   comment (or a two-account PR Approve) to open phase 2.
2. On approval, author the phase-2 ADR-spine record and open (or update)
   this repo's PR against main, with Closes #1174 only if this fan-out
   unit is understood to close the whole 43-role tracker (it is not —
   this is one of 43 rows; do not add a Closes trailer to a single-role
   PR).
3. Update the issue's 43-item completion tracker checkbox for
   technical-feasibility once this repo's own PR lands on main, per
   whatever board-state check the tracker maintainer runs at that time.
