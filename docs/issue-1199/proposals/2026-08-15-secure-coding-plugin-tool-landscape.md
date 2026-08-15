---
subject: issue-1199
role: secure-coding
loop_state: scope-proposed
status: proposed
files:
  - docs/issue-1199/proposals/2026-08-15-secure-coding-plugin-tool-landscape.md
---

# Proposal: fold Claude Code plugin/skill landscape into secure-coding-rulebook (issue-1199, 2026-08-14 amendment)

kind: proposal
subject: issue-1199

## Verification level

Verification Level: L1. This proposal targets ASVS L1 (baseline) depth
for the two rules delivered — ASVS V14 dependency-component
requirements and V5 input-validation requirements, both L1-scoped
controls per the OWASP ASVS 5.0 chapter. Requirement ID cited: ASVS
V14.2.1 (component inventory/vetting before use) for rule 1, ASVS
V5.1.3 (input validated against a defined structure) as the existing
anchor rule 10 extends.

## Problem / goal framing

canonical: docs/issue-1199/reports/secure-coding/current-state-survey.md
and docs/issue-1199/reports/secure-coding/scout-brief-plugins.md (this
repo, written this session), and the current-state survey of
`playbook/dependency-supply-chain-security.md` and
`playbook/input-validation-injection-defense.md` in
`/home/jwjung/tokenmaxxxer/rulebooks/secure-coding-rulebook`, read this
session. Secure-coding's rulebook has not yet been surveyed for this
issue. The 2026-08-14 amendment requires the surveyed sources to be
Claude Code plugins/skills, not general practitioner security tools
(OWASP cheat sheets, which the existing playbook already cites, do not
satisfy it).

## Comparison set / exemplars

Per the scout brief: anthropics/claude-code-security-review (5,861
stars), trailofbits/skills (6,589 stars) as top-tier adoption-evidence
exemplars; ghostsecurity/skills (398 stars) and snyk/claude-plugin-snyk
(0 stars, too new) as secondary confirmation of a convergent design
move (pre-acceptance/exploitability-first triage) rather than primary
adoption evidence.

## Methodology cited

This role's existing governing methodology (ASVS L1-L3, CWE/CVSS
finding format) is not replaced. This round adds two additive,
plugin-ecosystem-sourced judgments the OWASP-cheat-sheet-sourced
playbook does not yet cover.

## What will be delivered

Two native rule additions, phrased as this role's own judgment with no
tool-repo name or `source:` framing in the rulebook body (native-
application convention — provenance stays only in this on-the-record
trail):

1. **Pre-acceptance dependency health check rule** — before a new
   dependency is added (not only after it lands in the manifest),
   check its maintenance/security posture and exploitability of any
   known open issues, so an already-risky dependency does not enter
   the manifest and rely on the post-acceptance scan/patch ladder
   (rules 1-8) to catch it later. Upgrades:
   `dependency-supply-chain-security.md`, new rule 9.
2. **Diff/trust-boundary-scoped, false-positive-aware review rule** —
   when conducting a security review pass, scope it to the changed
   lines and the trust boundaries they cross rather than re-scanning
   the whole codebase each time, and explicitly triage out low-signal/
   non-reachable findings before they reach the finding list, rather
   than reporting every pattern match. Upgrades:
   `input-validation-injection-defense.md`, new rule 10.

Delivery target: `tokenmaxxxer/secure-coding-rulebook`, branch
`issue-1199/plugin-tool-landscape`, editing
`playbook/dependency-supply-chain-security.md` and
`playbook/input-validation-injection-defense.md`.

## Adopt / skip rationale

Adopt: the two rules above, each closing a gap the scout brief's gap
line names (no existing rule requires a pre-acceptance check; no
existing rule scopes how a review pass itself is bounded).

Skip: trailofbits/skills' full structured-detector-catalog architecture
and ghostsecurity's hook-based live-scanning automation — this role
delivers an ASVS checklist plus a finding list per scope, not a running
scanning pipeline; the judgment is adopted, the tool's automation
surface is not.

## How it will be judged

Judged done when: (a) both rules land as edits to the named target
files in `tokenmaxxxer/secure-coding-rulebook`; (b) this repo's phase-2
record (`docs/issue-1199/reports/secure-coding.md`) documents the
rulebook branch/commit and cites the scout-brief evidence trail for
each rule, without duplicating tool names/URLs into the rulebook body,
and sets `loop_state: landed` only once the edits are pushed; (c) the
secure-coding row in issue #1199's 43-item tracker stays/becomes
checked.

## Plan for phase 2

1. On `tokenmaxxxer/secure-coding-rulebook`, branch
   `issue-1199/plugin-tool-landscape`: add rule 9 to
   `playbook/dependency-supply-chain-security.md` and rule 10 to
   `playbook/input-validation-injection-defense.md`.
2. Commit and push the branch.
3. Update this repo's phase-2 record
   `docs/issue-1199/reports/secure-coding.md` documenting the
   branch/commit and the evidence trail, and set `loop_state: landed`.

## Out of scope

- Tool-landscape rework for any other role.
- Re-opening any existing rule in either target file.
- Building a live scanning/hook pipeline in the rulebook itself.
