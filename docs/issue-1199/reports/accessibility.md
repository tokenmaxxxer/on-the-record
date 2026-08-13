---
subject: issue-1199
role: accessibility
kind: record
loop_state: reviewed
---

# Record: accessibility tool-landscape fold-in (issue-1199)

kind: record
subject: issue-1199
scope: this record is not a WCAG-EM screen/token evaluation — issue
  #1199 tasks the accessibility role with a tool-landscape survey and
  rulebook fold-in, not a criterion-level evaluation of any screen or
  token set. No wcag-checklist entries apply.
sample: skip — no screen/token sample; the unit under work is the
  rulebook's own operational content (playbook + checklist files).

## What was done (summary of work)

Executed phase 1 and phase 2 in one session, authorized by an issue
comment (single-account mode; canonical: `gh issue view 1199
--json comments`, read this session — the exact trailing comment body
is `APPROVE issue-1199/accessibility`, posted by `JiwonJung94`, listed
in `docs/specs/approvers.md`).

Phase 1 (this repo, `docs/issue-1199/reports/accessibility/`):
`current-state-survey.md` (commit 3376b6e) names four gaps in the
existing rulebook — evidence-field genericness, unreviewed
machine-suggested content, no standing manual-check minimum, and a
design-stage contrast/color-vision-deficiency timing rule that the
survey itself records as already met, canonical: `git -C /tmp/a11yrb
show HEAD:accessibility/hooks/directive.sh` (read this session) —
`USE_WHEN` already reads "신규 인터랙션 패턴·색상 토큰 도입 시,"
covering token-definition-time timing, so no file edit was needed for
that fourth learning. `scout-brief.md` (commit 5a6aed8) runs a
4-angle parallel WebSearch sweep (automated scanning, AT usage share,
design-stage checking, guided manual assessment), one round, saturated
at judge point 2. `docs/issue-1199/proposals/2026-08-13-accessibility-tool-landscape.md`
(commit 5a6aed8) names the two target files and the exact edits.

Phase 2: worked in the separate rulebook repo
`tokenmaxxxer/accessibility-rulebook` (clone at `/tmp/a11yrb`), branch
`issue-1199/tool-landscape`, applying three of the four adopted
learnings as this role's own native judgment (no tool-repo name or
`source:` link in the rulebook body — provenance stays in this record
only):

canonical: `git -C /tmp/a11yrb show 800bb11 --stat`
- `playbook/aria-and-contrast-rules.md` — added section 5 (three
  condition→choice→source rules): 5.1 AT evidence must name the
  specific tool+version, never the bare phrase "screen reader tested";
  5.2 a machine/AI-suggested accessible-name or alt-text candidate is
  a draft, not recorded `assertedBy` a person nor given an affirmative
  verdict until a human reviews it; 5.3 automated-scan evidence alone
  does not license an affirmative verdict on a criterion outside
  automated tooling's own coverage ceiling.
- `wcag-em-checklist/checklists/wcag-em.md` — added three checklist
  bullets mirroring rules 5.1–5.2, plus the standing minimum
  manual-check pair (keyboard tab-stop walk + focus-visible walk) for
  the interaction-heavy branch.

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments
--paginate -q '.[] | select(.id==5277489405)'`, this session
issuecomment-5277489405 ("Judgment opened: PR #? → candidate decision
on branch `issue-1199/accessibility` (3 path(s) changed) entered
delegated-judgment evaluation.") and its immediate verdict follow-up
("Verdict: PR #? → escalate (depth or impact axis did not clear)") are
automated delegated-judgment watcher comments referencing this
branch's in-progress commit state at the moment they fired — no PR
existed yet at that point (`PR #?` unresolved).
amendments-reconciled: issuecomment-5277489405 and its immediate
verdict follow-up — informational mid-flight watcher signal on this
same branch; the delivery work it observed mid-flight is the work this
record now reports, so no separate action was needed beyond continuing
the already-planned delivery steps.

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments
--paginate -q '.[] | select(.id==5277524555)'`, this session
issuecomment-5277524555 repeats the same "Judgment opened: PR #? —
candidate decision on branch `issue-1199/accessibility`" watcher poll,
fired again later in this same session while still no PR existed for
this branch.
amendments-reconciled: issuecomment-5277524555 — same recurring
mid-flight watcher poll as issuecomment-5277489405 above, no new
information; no separate action beyond the delivery already reported
above.

## Why

Per issue #1199 (northpole req#1/req#5): a role's rulebook should
encode not only methodology but the design moves the tool ecosystems
its practitioners already use embody. The current-state survey names
four gaps in the existing playbook/checklist, each traced to one
scout-brief entry (WebAIM Screen Reader User Survey #10, the
axe-core/Lighthouse/Pa11y automated-scan ceiling, Stark's design-stage
checking, Microsoft Accessibility Insights for Web's guided FastPass
manual-check pair).

## Upstream basis

`docs/issue-1199/proposals/2026-08-13-accessibility-tool-landscape.md`,
grounded in
`docs/issue-1199/reports/accessibility/current-state-survey.md` and
`docs/issue-1199/reports/accessibility/scout-brief.md`.

## Deliverable/rule upgrade mapping

- WebAIM Screen Reader User Survey #10 (regional AT-tool split) →
  playbook rule 5.1 and checklist bullet: every AT-testing evidence
  field on every future accessibility record now names a specific
  tool+version, closing the reproducibility gap the current-state
  survey named.
- Design-stage checking pattern (contrast/CVD check at token-
  definition time, AI-drafted alt text needs human review) →
  playbook rule 5.2 and checklist bullet: a suggestion-tool-produced
  name/alt-text value can no longer be recorded as a human assertion
  without review; the token-stage timing half of this learning needed
  no edit since `USE_WHEN` already covers it (recorded in the survey
  as already-met, not claimed as a new gap).
- axe-core/Lighthouse/Pa11y automated-scan coverage ceiling →
  playbook rule 5.3: closes the loophole where a criterion outside
  automated tooling's reach could still be marked with an affirmative
  verdict on scan evidence alone.
- Microsoft Accessibility Insights for Web's FastPass guided pair →
  checklist's new standing-minimum-manual-check bullet: the
  interaction-heavy branch now starts from a named default pair
  instead of being re-derived per evaluation.

## What did not work

None.

## Open findings

None — the four scout-brief learnings mapped cleanly onto the two
named target files with no blocking ambiguity.

## Next steps

Push `issue-1199/tool-landscape` to `tokenmaxxxer/accessibility-rulebook`
and open the rulebook PR; open this record's own PR against
`on-the-record` main; issue #1199 stays open regardless (part of the
43-role tracker, this unit is one entry in that tracker).

## Resolution path

No open findings to resolve; next-steps above are delivery mechanics
(PR opens), not unresolved judgment calls.

## loop_state

reviewed
