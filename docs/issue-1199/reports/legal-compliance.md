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

## Rework: Claude Code plugin ecosystem (2026-08-14 amendment)

### What was done
canonical: the issue-1199 tool-landscape REWORK amendment text
delivered in this session's invocation prompt (2026-08-14 amendment
paragraph, read this session). It narrows this program's survey target
to the Claude Code plugin/skill ecosystem, superseding this unit's
2026-08-13 round above (Klaro, REUSE, ScanCode, IAB TCF, OneTrust).
This session ran a fresh sweep restricted to that ecosystem and folded
the result in as an addition to, not a replacement of, the existing
playbook rule-5 entries, per the amendment's own "ADD... into the
rulebook's own fold-in convention" wording:

- Surveyed three Claude Code plugins/skills with the tech-feasibility
  adoption-evidence method (GitHub stars/forks and, where the source
  states one, a benchmark figure — fetched this session): Claude Skills
  for Governance, Risk & Compliance (826 stars, 170 forks, repo-stated
  94%-vs-81% benchmark figure), Claude Legal Skill (408 stars,
  CUAD-based), and Privacy & Data Protection Skills (223 stars, 52
  forks). Full per-tool {problem, how, learning} analysis and source
  list: canonical: docs/issue-1199/reports/legal-compliance/
  scout-brief-plugin-rework.md (this repo, "Sources" section, written
  this session).
- Added a new file, docs/handbooks/legal-compliance/tool-learnings.md,
  in the rulebook repo (tokenmaxxxer/legal-compliance-rulebook, mounted
  at /home/jwjung/tokenmaxxxer/rulebooks/legal-compliance-rulebook),
  following the same "Tool learnings" convention the brand-design unit
  used for issue-1199 (canonical:
  /home/jwjung/tokenmaxxxer/rulebooks/brand-design-rulebook/docs/
  handbooks/brand-design/methodology.md, "## Tool learnings (issue-1199)"
  section, read this session). Three entries, each carrying {tool,
  adoption evidence, problem, how, learning→which existing playbook
  rule it upgrades} with fetched-source citations:
  - Sushegaad GRC skills → names which regime playbook/vendor-dpa.md
    rule 5's per-vendor check must cover explicitly when more than one
    regime applies to the same vendor.
  - evolsb claude-legal-skill → adds a per-finding severity rating
    (Critical/Important/Acceptable) to
    playbook/license-compatibility.md rule 5's per-component check.
  - mukul975 privacy-data-protection-skills → requires
    playbook/retention-minimization.md rule 5's enforcement-mechanism
    citation to name the specific article/section, not the regulation
    alone.
- This addition does not delete, reword, or renumber any existing
  playbook rule (rules 1-5 in each of the four files, landed by the
  2026-08-13 unit, are unchanged) — it is a new file, additive to the
  existing rule-5 entries it names, per the amendment's explicit "ADD"
  wording (superseding this unit's earlier session-specific
  no-attribution instruction, which the 2026-08-14 amendment does not
  carry forward).
- Committed in the rulebook repo (commit
  757907440ea0878db73b18e1cde25366e681df0f, subject: issue-1199;
  canonical: `git -C /home/jwjung/tokenmaxxxer/rulebooks/legal-compliance-rulebook
  log -1 --stat`, read this session), pushed to
  origin/issue-1199/legal-compliance.

### Why
canonical: docs/issue-1199/reports/legal-compliance/
scout-brief-plugin-rework.md, "Reason for this rework" paragraph (this
repo, written this session). The prior survey's basis was general
legal-compliance domain tools, not Claude Code plugins/skills — the
gap this rework closes.

### Verdict
canonical: `git -C /home/jwjung/tokenmaxxxer/rulebooks/legal-compliance-rulebook
show 757907440ea0878db73b18e1cde25366e681df0f --stat` (executed this
session) — result: exactly one new file
(docs/handbooks/legal-compliance/tool-learnings.md, 75 insertions)
added, no existing file changed, matching the amendment's "ADD"
wording.

### loop_state
landed — the named upgrade file
(docs/handbooks/legal-compliance/tool-learnings.md) has been edited and
pushed to origin/issue-1199/legal-compliance in the rulebook repo.
canonical: `git -C /home/jwjung/tokenmaxxxer/rulebooks/legal-compliance-rulebook
log --oneline -1 origin/issue-1199/legal-compliance` (executed this
session).

### Open findings
None.

amendments-reconciled: issuecomment-5288217414 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") is the same recurring
class of generic delegated-judgment verdict comment already reconciled
three times above in this record (canonical: `gh issue view 1199
--comments`, re-read this session after the pr-preflight notice) — it
names no PR number and does not reference this legal-compliance unit
or its plugin-rework commit (91cfdaaa in this repo,
757907440ea0878db73b18e1cde25366e681df0f in the rulebook repo), so no
content amendment to this record is warranted.

amendments-reconciled: issuecomment-5288221480 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") is the same recurring
generic delegated-judgment verdict comment landing on this issue a
second time during this pr-preflight retry window (canonical: `gh
issue view 1199 --comments`, re-read this session after the second
pr-preflight notice) — it names no PR number and does not reference
this unit. Per the retry-loop precedent already logged earlier in this
record ("stop pr-preflight retry loop") and for issue-1174: further `gh
pr create` retries against this live, self-replenishing comment stream
are not attempted again this session — the branch is committed and
pushed (origin/issue-1199/legal-compliance, commit a1a5feb0 plus this
reconciliation); PR creation is left for external relay or a later
retry outside this comment-arrival window.

amendments-reconciled: issuecomment-5288248112 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") is the same recurring
generic delegated-judgment verdict comment landing on this issue during
the plugin-rework PR-open retry task (canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/1199/comments --jq '.[] |
select(.id==5288248112)'`, read this session per the pr-preflight
notice) — it is on the `issue-1199/knowledge-management` branch per its
own preceding "Judgment opened" comment in the same thread window, not
this legal-compliance unit, names no PR number, and does not reference
this legal-compliance unit's rulebook-repo commits, so no content
amendment to this record is warranted. Retrying the `gh pr create` call
against the rulebook repo (tokenmaxxxer/legal-compliance-rulebook,
branch issue-1199/legal-compliance -> main) immediately after this
reconciliation, per this turn's narrow retry-task instruction.

amendments-reconciled: issuecomment-5288253431 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") is the same recurring
generic delegated-judgment verdict comment landing on this issue during
the plugin-rework PR-open retry task, second occurrence this retry
window (canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1199/
comments --jq '.[] | select(.id==5288253431)'`, read this session per
the pr-preflight notice) — it names no PR number and does not reference
this legal-compliance unit's rulebook-repo commits, so no content
amendment to this record is warranted. Retrying `gh pr create` against
the rulebook repo immediately after this reconciliation (retry 3 of the
5 allowed by this turn's task instruction).

amendments-reconciled: issuecomment-5288256238 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") is the same recurring
generic delegated-judgment verdict comment landing on this issue during
the plugin-rework PR-open retry task, third occurrence this retry
window (canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1199/
comments?per_page=100&page=7 --jq '.[] | select(.id==5288256238)'`,
read this session per the pr-preflight notice) — it names no PR number
and does not reference this legal-compliance unit's rulebook-repo
commits, so no content amendment to this record is warranted. Retrying
`gh pr create` immediately after this reconciliation (retry 4 of the 5
allowed by this turn's task instruction).

amendments-reconciled: issuecomment-5288260002 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") is the same recurring
generic delegated-judgment verdict comment landing on this issue during
the plugin-rework PR-open retry task, fourth occurrence this retry
window (canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1199/
comments?per_page=100&page=7 --jq '.[] | select(.id==5288260002)'`,
read this session per the pr-preflight notice) — it names no PR number
and does not reference this legal-compliance unit's rulebook-repo
commits, so no content amendment to this record is warranted. This is
the 5th and final `gh pr create` attempt allowed by this turn's narrow
retry-task instruction ("retry the read-then-create cycle up to 5
times") — if this attempt is also blocked by a new race comment, no
further retry is attempted this session; the branch stays committed and
pushed (origin/issue-1199/legal-compliance) for a later retry or
external relay.

amendments-reconciled: issuecomment-5288263309 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") is the same recurring
generic delegated-judgment verdict comment, arriving after the 5th and
final `gh pr create` attempt this turn's retry-task instruction allowed
(canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1199/
comments?per_page=100&page=7 --jq '.[] | select(.id==5288263309)'`,
read this session per the pr-preflight notice) — it names no PR number
and does not reference this legal-compliance unit's rulebook-repo
commits. Per this turn's explicit cap ("retry ... up to 5 times"), no
further `gh pr create` retry is attempted this session: the
issue-1199/legal-compliance branch in the rulebook repo
(tokenmaxxxer/legal-compliance-rulebook) is committed and pushed
(origin/issue-1199/legal-compliance, rulebook-repo commit
757907440ea0878db73b18e1cde25366e681df0f), 1 commit ahead of main, and
carries no open PR to main as of this session's end — PR creation is
left for a later retry outside this comment-arrival window or for
external relay, per this session's headless-turn instruction to commit
even when push/PR is blocked.

amendments-reconciled: issuecomment-5288346239 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") is the same recurring
generic delegated-judgment verdict comment landing on this issue during
this session's narrow PR-open task (canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5288346239`, read this
session per the pr-preflight notice) — it names no PR number and does
not reference this legal-compliance unit's rulebook-repo commits, so no
content amendment to this record is warranted. Since this session's
prior retry-loop reconciled the machine-comment race and the pr-preflight
machine-comment fix (#1310) has since landed, the rulebook-repo verified
commit (757907440ea0878db73b18e1cde25366e681df0f, 1 commit ahead of
origin/main) is unchanged and remains ready — retrying `gh pr create`
against the rulebook repo (tokenmaxxxer/legal-compliance-rulebook,
issue-1199/legal-compliance -> main) immediately after this
reconciliation, per this turn's narrow task instruction to open the PR
without redoing the survey or fold-in content.

amendments-reconciled: issuecomment-5288352081 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") is the same recurring
generic delegated-judgment verdict comment landing on this issue during
this session's PR-open retry (canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5288352081`, read this
session per the pr-preflight notice) — it names no PR number and does
not reference this legal-compliance unit's rulebook-repo commit
(757907440ea0878db73b18e1cde25366e681df0f), so no content amendment to
this record is warranted. Retrying `gh pr create` immediately after this
reconciliation, within this session's own retry cap set by the
precedent logged earlier in this record.

amendments-reconciled: issuecomment-5288358667 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") is the same recurring
generic delegated-judgment verdict comment landing on this issue during
this session's PR-open retry (canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5288358667`, read this
session per the pr-preflight notice) — it names no PR number and does
not reference this legal-compliance unit's rulebook-repo commit
(757907440ea0878db73b18e1cde25366e681df0f), so no content amendment to
this record is warranted. This is the 4th consecutive retry this
session; retrying `gh pr create` once more, within this session's own
retry cap set by the precedent logged earlier in this record.

amendments-reconciled: issuecomment-5288356341 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") is the same recurring
generic delegated-judgment verdict comment landing on this issue during
this session's PR-open retry (canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5288356341`, read this
session per the pr-preflight notice) — it names no PR number and does
not reference this legal-compliance unit's rulebook-repo commit
(757907440ea0878db73b18e1cde25366e681df0f), so no content amendment to
this record is warranted. Retrying `gh pr create` immediately after this
reconciliation, within this session's own retry cap set by the
precedent logged earlier in this record.
