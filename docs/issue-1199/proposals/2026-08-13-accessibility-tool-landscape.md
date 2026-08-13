---
status: proposed
files:
  - playbook/aria-and-contrast-rules.md
  - wcag-em-checklist/checklists/wcag-em.md
---

# Proposal: fold accessibility tool-landscape learnings into accessibility-rulebook

## Intent

Issue #1199 (northpole req#1): survey the tools accessibility
practitioners most use, extract the design moves each embodies, and
fold distilled learnings natively into `tokenmaxxxer/accessibility-
rulebook`'s own operational content — no tool-catalog section, no
"learned from X" attribution in the public rulebook.

## Constraints stated so far

- Adoption-evidence method only (stars/downloads/multi-source), no
  pretrained-recall tool listing — satisfied by
  `docs/issue-1199/reports/accessibility/scout-brief.md`.
- Bounded fold-in, no bloat: distilled rules/checklist items, not a
  tool catalog.
- Each learning must trace to which deliverable/rule it upgrades.
- No verbatim copying of any tool's own text.

## What will be done

Apply the four adopted learnings from the scout brief as this role's
own native rules, in the two files already governing this content:

1. `playbook/aria-and-contrast-rules.md` — add a new numbered section
   ("5. Evidence-field specificity and provenance") carrying two
   condition→choice→source rule blocks:
   - AT-testing evidence must name the specific tool (+version where
     known) used, never the generic phrase "screen reader tested" —
     upgrades the `evidence` field's reproducibility on every
     interaction-heavy criterion entry.
   - A machine/AI-suggested accessible-name or alt-text candidate is a
     draft; it may not be recorded `assertedBy` a person, nor carry an
     affirmative verdict, until a human has reviewed and accepted it —
     upgrades the naming rules (2.1–2.3) to cover suggestion-tool
     provenance, a case they do not currently address.
   Sources cited per rulebook convention: the WebAIM Screen Reader
   User Survey #10 finding (regional AT split) and the axe-core/
   Lighthouse/Pa11y ~57% automated ceiling, both already publicly
   documented WCAG-adjacent facts independent of any single vendor's
   marketing claim, cited the same way existing rules 3.1–3.3 cite
   the W3C understanding-doc thresholds.
2. `wcag-em-checklist/checklists/wcag-em.md` — add two checklist
   bullets mirroring the two new playbook rules (AT tool+version named;
   machine-suggested content held as unreviewed until confirmed), plus
   one bullet naming the standing minimum manual-check pair (keyboard
   tab-stop walk + focus-visible walk) as the default when the
   `wcag-em-directive`'s "interaction-heavy" branch fires — upgrades
   the session-start static aid to point at a concrete starting set
   instead of a bare "add AT/functional testing" instruction.
3. Token-stage timing (design-move 3, color-token contrast/CVD check
   due at token-definition time) is already covered by this role's
   existing `USE_WHEN` ("신규 인터랙션 패턴·색상 토큰 도입 시") — no
   file edit needed; the current-state survey records this as already
   met rather than claiming a phantom gap.

## Out of scope

- No new plugin/hook file.
- No change to `wcag-em-gate/hooks/methodology-gate.sh`'s mechanical
  enforcement — the two new checklist bullets are static-aid guidance,
  not machine-gated fields, matching the checklist's own stated scope
  ("static aid only... `wcag-em-gate` does [the enforcing]").
- No tool-catalog section or tool-name reference anywhere in the
  rulebook body.

## How you will know it worked

- `playbook/aria-and-contrast-rules.md` gains a fifth numbered section
  with two sourced condition→choice rule blocks, reviewable against
  `gates/playbook_depth_gate.py`'s rule-block shape.
- `wcag-em-checklist/checklists/wcag-em.md` gains three new bullets.
- `docs/issue-1199/reports/accessibility.md` (this role's phase-2
  record) states the applied diff and traces each rule to its
  scout-brief source angle.
