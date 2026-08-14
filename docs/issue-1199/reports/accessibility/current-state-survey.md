kind: report
subject: issue-1199
doc-type: reference

# accessibility — issue #1199 current-state survey

## Governing basis

Issue #1199 (northpole req#1/req#5): survey the plugins/tools
practitioners in this role's domain most use, extract the design moves
each embodies, and fold distilled learnings into the rulebook as this
role's own native rules — no per-tool attribution in public rulebook
content, provenance kept only in this on-the-record trail.

## Rulebook write surface

canonical: `git -C /tmp/a11yrb log -1 --format=%H` (this turn's tool
transcript, clone of `tokenmaxxxer/accessibility-rulebook`)

`tokenmaxxxer/accessibility-rulebook` carries four machine-enforced
plugins (`accessibility`, `wcag-em-directive`, `wcag-em-checklist`,
`wcag-em-gate`) plus one substantive playbook file:
`playbook/aria-and-contrast-rules.md` (issue-1174 batch, four
sections — ARIA role selection, accessible naming, contrast (WCAG
1.4.3), focus order/visibility — each a condition→choice→source rule
block with fetched citations, one open gap recorded on roving-tabindex).
`wcag-em-checklist/checklists/wcag-em.md` is the static session-start
aid; `wcag-em-gate/hooks/methodology-gate.sh` is the mechanical
enforcement of the seven-field entry shape.

## Methodology already named

The WCAG-EM 5-step evaluation is already the governing methodology
(issue-1's approved `methodology-norms.md`), and the SessionStart
`wcag-em-directive` hook already requires "automated + manual
inspection at minimum" per in-scope criterion, plus AT/functional
testing when the pattern is interaction-heavy. This fold-in extends
that existing methodology rather than introducing a new one.

## Gap this fold-in targets

1. **Evidence-field genericness.** The checklist requires an
   `evidence` field naming "technique used," but neither the checklist
   nor the playbook requires that an assistive-technology evidence
   entry name a specific tool+version rather than the generic phrase
   "screen reader tested." A generic entry cannot be reproduced or
   checked for AT diversity.
2. **Unreviewed machine-suggested content treated as verified.**
   Nothing in the current rules addresses the case where an
   accessible-name or alt-text candidate was produced by a suggestion
   tool (spell/AI-assisted) rather than authored/verified by a human —
   the playbook's naming rules (2.1–2.3) govern where the name comes
   from, not whether a machine-suggested value may be marked verified
   before human confirmation.
3. **No design-stage (pre-code) contrast/color-vision-deficiency check
   named**, despite `USE_WHEN` explicitly covering "신규 색상 토큰
   도입 시" (new color token introduction) — a token-stage event that
   precedes any rendered page an automated page-scanner could reach.
   Rule 3.1–3.3 state the numeric thresholds but not when in the
   pipeline (token definition vs. rendered page) the check is due.
4. **No structured per-criterion manual-check discipline** beyond the
   checklist's generic "automated + manual inspection" line — no rule
   requires naming which few manual checks recur across most
   interaction-heavy patterns (keyboard tab-stop walk, focus-visible
   walk) as a standing minimum set, rather than re-deriving the set
   from scratch each evaluation.

These four gaps are the scout's targets.
