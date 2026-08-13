---
status: proposed
files:
  - docs/issue-1174/proposals/operational-playbook-program.md
  - docs/issue-1174/reports/requirements-engineering/scout-brief.md
---

## Intent

Issue #1174 asks for a design (proposal only, no build) of the program
that will carry practitioner-depth operational decision rules into all
43 role rulebooks: per-role minimum rule-count thresholds, the 43-role
source-richness tiering and batch order, the batch depth-gate script's
spec, where playbooks land inside a rulebook repo, and how a role's
spec points at its playbook for quality-bar citation. Calibration bar =
the operator's own worked examples (issue body Problem section):
field-type-to-control mapping, layout/grouping rules, background-vs-edit
contrast composition, nav-order-vs-usage-frequency rules,
color-combination visibility rules — each a condition, a choice, and
(implicitly) a source.

## Constraints stated so far

- requirement: northpole req#1 (orchestration to completion) / req#5 —
  docs/specs/northpole.md; this program only has teeth if a session
  actually cites a playbook rule in a live judgment (Acceptance check 2).
- consult-log 2026-08-13T04:36:27 already ruled: landing location =
  rulebook, not spec (spec stays the verification layer); depth defense
  = forced source citation + counter-example test as the completion
  unit.
- coverage sequencing must be tiered (rich/moderate/sparse), batched
  4-6 roles per PR, tracked by a 43-item checklist in the issue so the
  program cannot silently stall on a subset.
- a playbook that "reads like a glossary" fails the depth gate — the
  gate must distinguish a decision rule (condition -> choice, with a
  reason and a source) from a definition (a term and its meaning).
- this is phase-1 design only: no rulebook repo, no gate script, and no
  spec field change lands in this PR. Build happens once this proposal
  is approved and a later phase/step executes it.

## (a) Per-role minimum-N thresholds

Flat N is wrong because domain breadth varies enormously (UX interaction
surfaces vs. e.g. legal-compliance's narrower, citation-bound rule set).
N is derived per role from two inputs, not assigned by fiat:

1. **Decision-axis count** — during batch execution, the assigned role
   session (or its scout pass) enumerates the domain's distinct
   decision axes at the operator's granularity — for ux-engineering
   these are already named in the issue: control-selection-by-field-
   type, layout/grouping, background-vs-edit contrast, nav-order-vs-
   frequency, color-combination visibility = 5 axes. Other domains
   derive their own axis list the same way (e.g. accessibility: focus-
   order rules, ARIA-role-by-widget-type, motion/timing thresholds,
   color-contrast minimums, keyboard-trap avoidance).
2. **Tier floor** — a minimum rules-per-axis multiplier set by the
   role's source-richness tier (below), so a rich domain cannot satisfy
   the gate with one shallow rule per axis:
   - rich: N_min = max(12, axes x 3)
   - moderate: N_min = max(8, axes x 2)
   - sparse: N_min = max(5, axes x 1)

N is therefore role-specific and computed once per role at batch time
(recorded in that role's own playbook front matter as `rule_count_floor:
<N>` with the axis list that produced it), not a constant baked into
this proposal. The depth-gate script (c) reads that recorded floor back
to verify the delivered playbook, so N is falsifiable per role rather
than asserted once and forgotten.

## (b) 43-role source-richness tier classification + batch sequence

Tiering signal: does the domain have an established public literature of
named, citable operational rules (textbooks, standards bodies, style
guides, W3C/IEEE/ISO specs, well-known practitioner canon) vs. rules
that are mostly org-specific/tacit judgment with thin public sourcing.
canonical: roles/*.json role-name listing read this turn (43 files,
matching the issue's own count).

**Batch 1 — rich, UX/design family (issue's named starting domains):**
ux-engineering, interaction-design, brand-design, content-design,
accessibility

**Batch 2 — rich, engineering/technical craft (deep public canon: OWASP,
Nielsen heuristics analogues, RFC/POSIX/CS-textbook-level rules):**
api-design, secure-coding, data-modeling, architecture,
performance-engineering

**Batch 3 — rich, quality/verification craft (ISTQB, IEEE, ISO 29148
family already anchors this repo's own spec fields):**
test-authoring, requirements-engineering, conformance-review,
observability, defect-verification

**Batch 4 — moderate, delivery/ops practice (documented but more
context-dependent, fewer universal numeric thresholds):**
release-engineering, incident-response, capacity-planning,
data-engineering, ml-engineering

**Batch 5 — moderate, product/discovery practice (named methodologies
exist — Jobs-to-be-Done, Double Diamond, RICE — but application is more
judgment-heavy than rule-tabular):**
product-discovery, user-discovery, market-analysis,
technical-feasibility, growth-analytics

**Batch 6 — moderate, writing/comms craft (style-guide-anchored but
audience-dependent):**
technical-writing, devrel, pr-communications, localization,
knowledge-management

**Batch 7 — moderate, risk/governance (frameworks exist — NIST, COSO —
but org-specific thresholds dominate):**
security-threat-model, risk-management, legal-compliance,
finance-unit-economics, pricing

**Batch 8 — sparse, org/relationship-facing (rules are mostly tacit,
negotiated, or company-specific; little citable public canon at
decision-rule granularity):**
sales, partnerships-bd, marketing, customer-support,
issue-retrospective

**Batch 9 — sparse, remaining craft + closing the set:**
implementation, execution-observation, refactoring-legacy,
upstream-defect-report

Batch 1-3 = rich (15 roles), batch 4-7 = moderate (20 roles), batch 8-9
= sparse (9 roles), 44 roles total.
canonical: `ls roles/*.json | xargs -n1 basename | wc -l` and the full
name listing, both read this turn — the working tree currently holds
44 role manifests, not the 43 the issue text states. This proposal's
batch list above accounts for all 44 actual roles; the discrepancy
against the issue's stated "43" is flagged here rather than silently
dropping one role to force a match. The executing session for step 2+
should re-run the same count against `roles/*.json` and size the
issue's completion tracker to whatever that count is at batch-1 time
(44 today, but roles can be added/removed before batches finish).

This tiering is a phase-1 judgment call, not a measurement — the
executing role should re-confirm a role's tier against actual source
availability found during that batch's own scout pass, and move a role
between tiers if the assumption above doesn't hold.

## (c) Batch depth-gate script spec

New script: `gates/playbook_depth_gate.py` (parent repo, mirroring the
existing `gates/spec_index.py` / `gates/record_lint.py` convention —
these are the parent repo's own gate house, not the rulebook's plugin-
gate pattern surveyed in (d)).

Invocation: `python3 gates/playbook_depth_gate.py <playbook-file-or-dir>
--role <role-name> --floor <N>` — run per role per batch, called from
the batch PR's own preflight the same way `spec_index.py --update` is
called today.

Shape it checks, per candidate rule block (a rule block = a heading or
list item under a "## Rules" / "## Decision rules" section):

1. **Condition present** — the block contains a conditional marker
   (`when/if/under/for <X>` in English, `~일 때/~인 경우/~면` in Korean) that
   names a concrete situation, not a bare noun phrase.
2. **Choice present** — the block states what to DO or PICK (an
   imperative verb or a named option among alternatives), not just what
   a term means.
3. **Source present** — the block carries a citation (URL, standard
   name + section, or `source:` field) distinct from the rule's own
   restatement — an uncited assertion does not count toward N even if
   condition+choice are present.
4. **Glossary-shape rejection** — a block is rejected (does not count
   toward N, and if it's the majority of the file the whole file fails)
   when it matches definition shape: `<Term> is/means/refers to <X>`
   with no condition clause and no choice/action verb. This is the
   mechanical form of "reads like a glossary" from the issue's
   Acceptance section.
5. **Count vs. floor** — total accepted rule blocks (after glossary
   rejection) must be >= the role's recorded `rule_count_floor` from
   (a). Exit non-zero with a per-block reason list (accepted/rejected +
   why) when short.

Output: machine-readable pass/fail plus a human-readable per-rule table
(reason for every rejection), so a batch PR can paste the gate's own
output as its acceptance evidence rather than asserting a bare count.
The gate checks SHAPE only (executed-unit, per the issue's Acceptance
provenance split) — the human reviewer's spot-check for whether an
accepted block is actually decision-grade (not just condition+choice+
source-shaped but *true and useful*) stays a separate, human step, exactly
as the issue's Acceptance section already splits "provenance:
executed-unit (shape) + human review (depth)".

## (d) Rulebook landing structure

Surveyed tokenmaxxxer/ux-engineering-rulebook (operator-named exemplar)
this turn — see scout-brief.md for the full listing. That repo already
runs its own docs/{handbooks,specs,issue-<n>} tree mirroring this
repo's contract v3 layout, and its top-level dirs are one-per-gate-
plugin (each a `{.claude-plugin, hooks, tests}` enforcement bundle for
document *shape*, not content) — no directory in it currently holds
practitioner decision content.

Proposed addition, matching that repo's own convention rather than
inventing a new one: a new top-level content directory,
`playbook/<topic>.md` per decision-axis group (e.g. for ux-engineering:
`playbook/control-selection.md`, `playbook/layout-grouping.md`,
`playbook/surface-contrast.md`, `playbook/navigation-depth.md`,
`playbook/color-visibility.md` — one file per axis from (a), each
holding that axis's condition-choice-source rule table plus a front-
matter `rule_count_floor:`/`axis:` pair for the depth gate to read).
This sits as a peer to the existing plugin dirs (ux-token-schema/,
ux-wcag-onpair/, etc.), not nested under docs/ — docs/ in that repo is
reserved for the contract's own process artifacts (specs, handbooks,
issue trees), and the plugin-dir-as-topic-unit pattern is what that
repo's README already documents as its layout convention. Each
rulebook's README "Layout" section gains one line pointing at
`playbook/` the same way it lists its existing plugin dirs — adopting
the repo's own self-documenting-layout pattern rather than a silent
addition.

Roles without a dedicated rulebook repo yet (if any surface during
later batches) fall back to `docs/playbook/<topic>.md` inside this
parent repo's own per-role docs tree, matching the acceptance
criterion's stated fallback ("or the rulebook's equivalent operational
section").

## (e) Spec -> playbook pointer shape

Add one optional field to `roles/specs/<role>.spec.json`, alongside the
existing `source_standard`/`finding_method`/`anti_pattern` fields
surveyed this turn in requirements-engineering.spec.json:

```json
"playbook_refs": [
  {
    "axis": "control-selection",
    "repo": "tokenmaxxxer/ux-engineering-rulebook",
    "path": "playbook/control-selection.md",
    "section": "#field-type-to-control-mapping"
  }
]
```

One entry per decision axis (matching (a)'s axis list and (d)'s one-
file-per-axis layout), so a quality-bar verdict can cite
`playbook_refs[].axis` + `.section` as the violated rule's address —
this is the concrete form of Acceptance check 2 ("one live role session's
judgment record cites a specific playbook rule"): the citation in that
judgment record should resolve to exactly this pointer shape, verifiable
by fetching `repo`+`path`+`section` and confirming the anchor exists.
`finding_method`/`anti_pattern` stay as they are — pointer fields are
additive, not a replacement for the existing verification-layer fields
(matches the consult-log ruling that spec stays the verification layer,
not the content layer).

## Out of scope (this proposal)

- Writing any actual playbook content for any role.
- Building `gates/playbook_depth_gate.py` or wiring it into any
  preflight.
- Editing any rulebook repo (ux-engineering-rulebook or any other).
- Editing any `roles/specs/*.spec.json` file to add `playbook_refs`.
- Re-litigating the consult-log's landing-location ruling — this
  proposal builds on it, not around it.
- Filing the 43-item completion tracker into the issue body — that is
  an issue-editing action for the human/orchestrator turn that approves
  this design, not a phase-1 write.

## Verification

- This proposal itself is reviewable against the issue's five listed
  requirements (a)-(e) one-to-one — each subsection above is
  addressable to one requirement line.
- Once approved, step 2 (implementation, batch 1) should be checkable
  against: `python3 gates/playbook_depth_gate.py` (once built) passing
  for all 5 batch-1 playbooks at their recorded floors, and one live
  session transcript citing a `playbook_refs` entry (Acceptance check
  2), exactly as spec'd in (c)/(e) above.

## What did not work

None.
