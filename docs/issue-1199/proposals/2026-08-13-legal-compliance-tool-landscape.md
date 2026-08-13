---
subject: issue-1199
role: legal-compliance
loop_state: scope-proposed
status: proposed
files:
  - playbook/consent-ux.md
  - playbook/license-compatibility.md
  - playbook/vendor-dpa.md
  - playbook/retention-minimization.md
  - docs/issue-1199/reports/legal-compliance.md
---

# Proposal: fold legal-compliance's tool landscape into the rulebook (issue-1199)

All four playbook file paths below live in the separate rulebook repo
("tokenmaxxxer/legal-compliance-rulebook", mounted at
/home/jwjung/tokenmaxxxer/rulebooks/legal-compliance-rulebook — see
docs/issue-1199/reports/legal-compliance/survey.md), not in this
working tree; phase 2 branches and commits there directly.

## Request
Per issue-1199 (northpole req#1/req#5) and this session's specific
task instruction: research the tools legal-compliance practitioners
actually use (adoption-evidence method), then apply the resulting
design-move learnings NATIVELY as new decision rules inside the
existing playbook axis files — no tool-catalog section, no "learned
from X" attribution in the public rulebook, no verbatim copying. The
full evidence trail (tools, adoption evidence, insight mapping) lands
only in docs/issue-1199/reports/legal-compliance.md in this repo.

## Scope / boundary
This proposal's scope boundary: in scope are the four numbered rule
additions named below; out of scope is everything else in the
rulebook repo — see "Out of scope" for the full list.

## Regulations engaged
GDPR Recital 32 (affirmative-act consent standard — consent-ux rule
5); GDPR Art. 28(3)(a) (documented-instructions requirement flowing to
sub-processors — vendor-dpa rule 5); GDPR Art. 5(2) (accountability /
ability to demonstrate compliance — retention-minimization rule 5);
license-compatibility rule 5 is sourced to a compliance-practice
pattern (no single statute governs license compatibility), consistent
with the existing license-compatibility.md rules' own practice-guide
citations. No exclusions from the regulations named above — GDPR is
the only regime this round's four rules engage; other regimes (CCPA,
sector-specific rules) are not implicated by this fold-in.

## Necessity / proportionality
Each new rule is added only where the field-vs-checklist gap analysis
(docs/issue-1199/reports/legal-compliance/scout-brief.md) found the
existing four rules per axis silent on a specific, named failure mode
a real-world tool was built to close (pre-consent tracker firing;
unchecked vendored-license drift; DPA flow-down with no runtime
verification; a retention period with no enforcement mechanism) —
proportionate to that one gap, not a general rewrite of the axis, and
requiring no mitigation beyond the rule addition itself (no risk
introduced that needs a separate mitigation). No existing rule is
deleted, reworded, or renumbered.

## Evidence / rationale
- consent-ux rule 5 design move (github.com/kiprotect/klaro), sourced to GDPR Recital 32, Art. 4(11).
- license-compatibility rule 5 design move (reuse.software; github.com/nexB/scancode-toolkit) — assumption, unsourced as to statute (practice-pattern sourced instead, matching this file's existing rules).
- vendor-dpa rule 5 design move (iabeurope.eu/tcf), sourced to GDPR Art. 28(3)(a).
- retention-minimization rule 5 design move (onetrust.com/solutions/third-party-management), sourced to GDPR Art. 5(2).

Full evidence trail (adoption numbers, problem/how per tool): docs/
issue-1199/reports/legal-compliance/scout-brief.md.

## Sources
- https://github.com/kiprotect/klaro
- https://reuse.software/
- https://github.com/nexB/scancode-toolkit
- https://iabeurope.eu/tcf/
- https://www.onetrust.com/solutions/third-party-management/
- https://gdpr-info.eu/recitals/no-32/
- https://gdpr-info.eu/art-5-gdpr/
- https://gdpr-info.eu/art-28-gdpr/

## What will be done
Add one new numbered rule (rule 5) to each of four playbook axis
files, per the scout brief's field-vs-checklist gap:

1. **consent-ux.md** — technical gating verification: a consent review
   must check that non-essential trackers are actually prevented from
   executing pre-consent, not only that the banner's visible copy/
   friction is compliant. Sourced to GDPR Recital 32's affirmative-act
   standard.
2. **license-compatibility.md** — per-component license check: a
   license review of a repo bundling vendored/embedded third-party
   code must check each bundled component individually, not assume
   the top-level LICENSE file is exhaustive. Sourced to the REUSE
   per-file-tagging model (cited as a specification pattern, not a
   tool endorsement).
3. **vendor-dpa.md** — runtime per-vendor consent signal for multi-hop
   chains: a DPA review of a data flow through more than one
   sub-processor must require a verifiable, current per-vendor legal-
   basis signal at processing time, in addition to the existing
   contractual flow-down clause (rule 3). Sourced to Art. 28(3)(a)'s
   documented-instructions requirement.
4. **retention-minimization.md** — named enforcement mechanism: a
   retention rule must name the actual deletion/anonymization
   mechanism (scheduled job or a named manual owner+cadence), not just
   state a period. Sourced to Art. 5(2)'s accountability/demonstrate-
   compliance requirement.

Each new rule carries its own `counter-example:` scoping when the new
check does not apply, matching the existing rules' structure.

docs/issue-1199/reports/legal-compliance.md is phase-2 output, written
only after approval opens phase 2, per contract v3 s19.

## Out of scope
- cross-border-transfer.md, lawful-basis-selection.md, research-log.md
  — no tool this round mapped a clear design-move gap onto these three
  axes; not touched.
- Any change to the three gate plugins (phase1-proposal-gate,
  phase2-record-gate, fanout-completeness-gate) or the handbook's gate-
  test-harness doc — no tool maps to gate mechanics.
- Installing or depending on any of the surveyed tools — the fold-in
  borrows the design move only.
- A public "Tool learnings" section or any tool-name attribution in the
  rulebook — explicitly excluded by this session's task instruction.

## How you'll know it worked
Phase 2 diff, reviewed against this proposal, adds exactly one rule 5
to each of the four named playbook files (each carrying a numbered
rule, a `source:` citation to a legal provision — never a tool name —
and a `counter-example:`), with no deletion or renumbering of existing
rules, and no tool-catalog or attribution text anywhere in the
rulebook repo.
