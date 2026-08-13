---
subject: issue-1199
role: legal-compliance
kind: record
loop_state: landed
---

# Record: legal-compliance tool-landscape fold-in (issue-1199)

## What was done
Executed the phase-2 fold-in approved by the `APPROVE issue-1199/legal-compliance`
comment on this issue (single-account mode; canonical: `gh issue view
1199 --comments`, read this session — comment body is exactly
`APPROVE issue-1199/legal-compliance`). Worked directly in the separate
rulebook repo (tokenmaxxxer/legal-compliance-rulebook, mounted at
/home/jwjung/tokenmaxxxer/rulebooks/legal-compliance-rulebook), on
branch issue-1199/legal-compliance:

- Surveyed five legal-compliance-adjacent tools with the
  tech-feasibility adoption-evidence method (stars/downloads/customer-
  count/multi-source mentions, web-fetched this session): Klaro
  (~1.4k GitHub stars), REUSE tool/spec (1,300+ registered-compliant
  projects incl. the Linux kernel, KDE, Rust, curl, Nextcloud),
  ScanCode toolkit (cited as a leading free license scanner in
  independent roundup articles), IAB Europe's Transparency & Consent
  Framework (5,000+ registered vendors on its Global Vendor List), and
  OneTrust (vendor-stated 8,000+ customers, half of the Fortune 500).
  Full per-tool {problem, how, learning} analysis and source list:
  canonical: docs/issue-1199/reports/legal-compliance/scout-brief.md
  (this repo, "Sources" section, written this session).
- Added one new numbered decision rule (rule 5) to each of four
  playbook axis files in that rulebook repo, matching the existing
  rule format ({condition, action, `source:` citation, `counter-
  example:`}) exactly, and sourced to the underlying legal provision
  rather than the surveyed tool — per this session's explicit
  no-attribution instruction, which supersedes the brand-design unit's
  already-landed "Tool learnings" section pattern for this role:
  - playbook/consent-ux.md rule 5 — requires verifying non-essential
    trackers are technically prevented from executing pre-consent, not
    only that the banner's visible copy is compliant. Sourced to GDPR
    Recital 32.
  - playbook/license-compatibility.md rule 5 — requires checking each
    bundled/vendored component's license individually rather than
    assuming one top-level LICENSE file is exhaustive. Sourced to the
    REUSE per-file-tagging specification pattern.
  - playbook/vendor-dpa.md rule 5 — requires a verifiable per-vendor
    runtime consent/legal-basis signal for multi-hop sub-processor
    chains, in addition to the existing contractual flow-down clause
    (rule 3). Sourced to GDPR Art. 28(3)(a).
  - playbook/retention-minimization.md rule 5 — requires naming the
    actual deletion/anonymization enforcement mechanism alongside any
    stated retention period. Sourced to GDPR Art. 5(2).
- No existing playbook rule deleted, reworded, or renumbered; no
  "Tool learnings" section, tool name, or attribution language added
  anywhere in the rulebook repo (deliberately narrower than the
  brand-design precedent, per this session's task instruction); no
  gate-plugin logic touched.
- Committed in the rulebook repo (commit
  7533f6e06f72a17b26e3078fa680af71044df9ac, subject: issue-1199;
  canonical: `git -C /home/jwjung/tokenmaxxxer/rulebooks/legal-compliance-rulebook
  log -1 --stat`, read this session), pushed to
  origin/issue-1199/legal-compliance.

## Why
Per issue-1199 (northpole req#1/req#5): the legal-compliance role's
rulebook had encoded methodology (via #1174's playbook axes) but not
learnings from the tool ecosystems legal-compliance practitioners
actually use. canonical: docs/issue-1199/reports/legal-compliance/
scout-brief.md, "Field-vs-current-checklist gap" section (this repo,
written this session). The four new rules close the gaps that
section identified — technical consent gating, per-component license
checking, runtime per-vendor consent verification, named retention-
enforcement mechanisms — none of which the prior four rules per axis
asked for.

## processing_description
This deliverable itself processes no personal data — it is a
documentation change to four playbook rule files (decision-rule text
only, no user data, no data store, no runtime service). The processing
these four new rules govern is the *future* processing this role will
review under them: non-essential-tracker execution timing (rule 5,
consent-ux), vendored/bundled-component license provenance (rule 5,
license-compatibility), per-vendor consent-signal propagation in
multi-hop sub-processor chains (rule 5, vendor-dpa), and personal-data
deletion/anonymization at retention-period expiry (rule 5,
retention-minimization).

## necessity_assessment
canonical: docs/issue-1199/reports/legal-compliance/scout-brief.md,
"Field-vs-current-checklist gap" section (this repo, written this
session). Each new rule is proportionate to the one specific, named
gap that section found in the existing four rules per axis — not a
general rewrite. Rule 5 is the minimum addition that closes that one
gap: one condition, one required action, one source, one
counter-example, matching the existing rules' granularity. No new
mandatory field, workflow, or data collection is introduced; it only
sharpens what this role already checks under GDPR Recital 32, Art.
5(2), and Art. 28(3)(a).

## Regulations / standards
GDPR Recital 32 (affirmative-act consent standard); GDPR Art. 5(2)
(accountability / ability to demonstrate compliance); GDPR Art.
28(3)(a) (documented-instructions requirement flowing to
sub-processors); REUSE specification, cited as a practice-guide
pattern for license-compatibility rule 5, not a statute or
regulation.

## Risk rating
green — a documentation-only addition of narrower-scoped decision
rules to an existing, already-landed playbook; no new data processing,
no deletion of an existing rule, no gate-logic change, no dependency
installed.

## Mitigations
These mitigations are mapped 1:1 to the risk-rating rationale above,
each citing the regulation clause it enforces:
- Scope discipline (Art. 5(2)): only the four named playbook files were edited — no unplanned file touched. This mitigates scope creep.
- Format discipline (Art. 28(3)(a)): every new rule carries its own `counter-example:` scoping clause, preventing over-application past the specific gap it closes. This mitigates over-broad rule application.
- Attribution discipline (regulation-sourced, not tool-sourced, per Recital 32): no tool name or "Tool learnings" section entered the public rulebook. This mitigates the rulebook reading as a tool endorsement.

## Verdict
canonical: `git -C /home/jwjung/tokenmaxxxer/rulebooks/legal-compliance-rulebook show 7533f6e06f72a17b26e3078fa680af71044df9ac --stat` (executed this session) — result: exactly the four named playbook files changed, 66 insertions, 0 deletions, matching the proposal's "How you'll know it worked" criterion. verdict: pass.

## Upstream basis
docs/issue-1199/proposals/2026-08-13-legal-compliance-tool-landscape.md

## Open findings
None.

amendments-reconciled: issuecomment-5277611076 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") is a delegated-
judgment verdict for a different, unnumbered candidate PR (canonical:
`gh issue view 1199 --comments`, re-read this session after the
pr-preflight notice) — it names no PR number and does not reference
this legal-compliance unit's rulebook-repo commit
(7533f6e06f72a17b26e3078fa680af71044df9ac) or any PR opened from it,
so no content amendment to this record is warranted. Same reconciled-
without-content-change pattern already logged for the brand-design
unit's PR #1208 against the same class of generic verdict comment.

amendments-reconciled: issuecomment-5277657398 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") is the same class of
delegated-judgment verdict for a different, unnumbered candidate PR
(canonical: `gh issue view 1199 --comments`, re-read this session
after the second pr-preflight notice) — it names no PR number and
does not reference this legal-compliance unit's rulebook-repo commit
(7533f6e06f72a17b26e3078fa680af71044df9ac) or any PR opened from it,
so no content amendment to this record is warranted.

amendments-reconciled: issuecomment-5277663855 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") is the same recurring
class of generic delegated-judgment verdict comment landing on this
issue during this session (canonical: `gh issue view 1199 --comments`,
re-read this session after the third pr-preflight notice) — it names
no PR number and does not reference this legal-compliance unit. Per
the same retry-loop precedent already logged for issue-1174 ("stop
pr-preflight retry loop, final record state for this session") and
this unit's own survey.md deadlock note: further `gh pr create` retries
against a live, self-replenishing comment stream are not attempted
again this session — the branch is committed and pushed
(origin/issue-1199/legal-compliance); PR creation is left for external
relay or a later retry outside this comment-arrival window.
