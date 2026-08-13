---
kind: record
subject: issue-1199
loop_state: delivered
---

# issue-1199 (ux-engineering): tool-landscape fold-in — phase 2 record

## What was done

canonical: gh issue view 1199 --json comments -q '.comments[] | select(.body | test("APPROVE issue-1199/ux-engineering")) | {author: .author.login, createdAt: .createdAt}'
Executed the approved proposal (`docs/issue-1199/proposals/2026-08-13-ux-engineering-tool-landscape.md`),
approved via issue-level `APPROVE issue-1199/ux-engineering` comment from
JiwonJung94, an approvers.md account, posted 2026-08-13T07:02:22Z.

Cloned `tokenmaxxxer/ux-engineering-rulebook`, branch `issue-1199/tool-landscape`,
and appended one native decision rule (numbered rule + rationale +
counter-example, matching each file's existing shape) to each of the
five named upgrade targets:

- `playbook/color-visibility.md` rule 7 — route reused color values
  through one source-of-truth layer shared by design and shipped code.
- `playbook/surface-contrast.md` rule 5 — check contrast against the
  element's actual rendered layer (real background, current interaction
  state, real font-weight), not an isolated swatch pair.
- `playbook/control-selection.md` rule 8 — for a pattern with an
  established role-and-keyboard-interaction contract, pick the control
  matching that contract over a visually-similar look-alike.
- `playbook/layout-grouping.md` rule 7 — prove a grouped layout's empty/
  loading/error/populated states correct in isolation before assembling
  into a full screen.
- `playbook/navigation-depth.md` rule 6 — judge navigation depth by a
  measured directness score (task completion without backtracking), not
  a subjective depth read.

Per the native-application amendment (issue #1199 comment, 2026-08-13,
operator): no rule text names a surveyed tool or repo, and no
`source: <url>` framing was added — each rule reads as this role's own
design judgment. The survey/adoption-evidence trail stays only in this
repo's phase-1 records
(`docs/issue-1199/reports/ux-engineering/survey.md`,
`docs/issue-1199/reports/ux-engineering/scout-brief.md`) and this
record, per the amendment's provenance-placement rule.

canonical: gh pr view 24 --repo tokenmaxxxer/ux-engineering-rulebook
Opened PR against the rulebook repo:
https://github.com/tokenmaxxxer/ux-engineering-rulebook/pull/24 —
5 files changed, 79 insertions(+), branch
`issue-1199/tool-landscape`.

canonical: gh issue view 1199 --json comments -q '.comments[] | select(.body | test("ux-engineering")) | .body'
Did not touch issue #1199's 43-item tracker: no editable tracker
comment enumerating per-role rows was found under this issue — only a
reopen note referencing "the 43-item tracker" and an amendment note
naming in-flight units turned up. Tracker maintenance is out of this
unit's write scope per the proposal's own constraint ("no touching the
43-item tracker for any row but ux-engineering's own" presupposes a
row to touch, which does not exist as an editable artifact here).

## Why

Issue #1199 (northpole req#1/req#5) requires each role to fold
practitioner-tooling-derived design judgment into its rulebook, applied
natively (no per-tool attribution in the public rulebook, no verbatim
copying), with the survey/evidence trail kept on the requesting side.
This record and the linked rulebook PR satisfy that split for the
ux-engineering unit.

## Upstream / basis

canonical: gh pr view 1222 --json state,mergedAt
- docs/issue-1199/proposals/2026-08-13-ux-engineering-tool-landscape.md
  (phase-1 proposal, this repo, merged per PR #1222).
- docs/issue-1199/reports/ux-engineering/survey.md
- docs/issue-1199/reports/ux-engineering/scout-brief.md
- APPROVE issue-1199/ux-engineering comment (JiwonJung94, 2026-08-13T07:02:22Z)

amendments-reconciled: issuecomment-5277177330 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") — a delegated-judgment
verdict comment on an unspecified PR, not naming ux-engineering or this
unit's rulebook PR; out of scope for this unit's work, no reconciliation
needed.

## Open findings

None.
