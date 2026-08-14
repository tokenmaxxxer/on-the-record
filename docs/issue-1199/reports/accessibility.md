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

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments
--paginate -q '.[] | select(.id==5277529070)'`, this session
issuecomment-5277529070 repeats the same watcher poll a third time.
This session then hit the reconcile-then-retry-`gh pr create` deadlock
already logged by the interaction-design and technical-writing units
for issue #1199: the poll re-fires faster than each reconcile-and-
retry cycle can clear. Logged to
`docs/issue-1199/reports/accessibility/deviation-log.md` (commit
a445a50).
amendments-reconciled: issuecomment-5277529070 — same recurring
mid-flight watcher poll, no new information; retries on `gh pr create`
stop here per the deviation log above. Both branches
(`tokenmaxxxer/accessibility-rulebook`'s `issue-1199/tool-landscape`,
commit `800bb11`, and this repo's `issue-1199/accessibility`) are
pushed to origin for external relay to open the PRs.

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

Both branches are pushed to origin (rulebook: `issue-1199/tool-landscape`
commit `800bb11`; this repo: `issue-1199/accessibility`) but this
session's `gh pr create` retries stopped after hitting the recurring
watcher-comment-race deadlock recorded in
`docs/issue-1199/reports/accessibility/deviation-log.md`. External
relay opens both PRs (rulebook PR against
`tokenmaxxxer/accessibility-rulebook`, and this record's PR against
`on-the-record` main). Issue #1199 stays open regardless (part of the
43-role tracker, this unit is one entry in that tracker).

## Resolution path

No open findings to resolve; the one filed deviation (PR-open deadlock)
resolves by external relay opening the two already-pushed branches as
PRs — no unresolved judgment calls remain on this unit's content.

## 2026-08-14 plugin-ecosystem rework (phase 1 only)

canonical: `docs/issue-1199/proposals/2026-08-14-accessibility-plugin-tool-landscape-rework.md`
(read this session) — the issue's 2026-08-14 amendment narrows the
survey target to Claude Code plugins/skills; the 2026-08-13 round above
surveyed domain tools (axe-core, Lighthouse, Pa11y, Stark, Accessibility
Insights for Web) only, so it does not by itself satisfy the amended
acceptance check.

canonical: `docs/issue-1199/reports/accessibility/scout-brief-plugins.md`
(read this session) — a 4-way parallel WebSearch/WebFetch sweep names
two adoption-evidenced exemplars, Community-Access/accessibility-agents
(390 GitHub stars) and Owl-Listener/inclusive-design-skills (93 stars),
plus three lower-adoption plugins as secondary confirmation, each entry
carrying its own `canonical:`/star-count citation inside that file.

canonical: `git show 1d40ca42 --stat` (read this session) — this
session's own git-show output lists exactly two files changed,
`docs/issue-1199/proposals/2026-08-14-accessibility-plugin-tool-landscape-rework.md`
and `docs/issue-1199/reports/accessibility/scout-brief-plugins.md`,
305 insertions, committed as `1d40ca42` with the `Subject: issue-1199`
trailer, on branch `issue-1199/accessibility`.

canonical: `gh pr view 1248 --json number,title,state,url,headRefName`
(read this session) — PR #1248, state OPEN, `headRefName:
issue-1199/accessibility`, carries the above commit.

canonical: `gh issue view 1199 --json comments -q '.comments[] |
select(.body=="APPROVE issue-1199/accessibility")'` (read this
session) returns exactly one matching comment, timestamped before the
2026-08-14 proposal file above was written; no comment matching that
exact string, posted after the proposal file's own commit, appears in
that same query output. Per the rework proposal's own "Approval"
section, canonical: `docs/issue-1199/proposals/2026-08-14-accessibility-plugin-tool-landscape-rework.md`
(read this session, "Approval" section), this session stops after
phase 1, holding for a new `APPROVE issue-1199/accessibility` comment
posted after the proposal file's commit. This section is a proposal
status note, not an outcome claim: the two additive rules named in
the proposal's "What will be delivered" section (named-pattern manual-
check for focus-trap/live-region; tradeoff-rationale scope notes)
remain proposal text in this session; no edit to
`tokenmaxxxer/accessibility-rulebook` was made or pushed this session.

## Accumulation

This fold-in pattern (per-role survey file + proposal file, two small
additive files, no shared helper) repeats across all 43 roles tracked
by issue #1199, and now a second time per role under the 2026-08-14
plugin-ecosystem amendment. If N more rounds land this way, `docs/
issue-1199/reports/<role>/` and `docs/issue-1199/proposals/` accumulate
two more small files per role per round with no cross-role index or
dedup — the per-role tracker in issue #1199 is the only place coverage
is summarized, and nothing in this repository regenerates it
automatically. That growth shape stays workable for this issue's own
bounded, one-time-per-amendment survey work (each file is small,
independently reviewable, and the issue's 43-item checklist already
serves as the accumulation's index); it stops being workable only if a
third or later amendment reopens the same 43 roles again without first
folding the accumulated proposals into one per-role canonical file.

## loop_state

reviewed
