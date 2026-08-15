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

amendments-reconciled: issuecomment-5288372590 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)"). canonical: gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5288372590 — body is
exactly that text, posted by JiwonJung94 with the PR number left as an
unfilled `#?` placeholder; it names no PR, no role, and no
ux-engineering artifact, same templated shape as the prior entry above.
Out of scope for the 2026-08-14 plugin/skill rework phase-1 unit
(docs/issue-1199/proposals/2026-08-14-ux-engineering-plugin-tool-landscape-rework.md);
no reconciliation action needed beyond this citation.

amendments-reconciled: issuecomment-5288383520, and by the same
templated shape issuecomment-5288384... series through
IC_kwDOTiVhs88AAAABOzZgJw (2026-08-14T01:33:56Z, "Judgment opened: PR
#? — candidate decision on branch `issue-1199/defect-verification`").
canonical: gh issue view 1199 --json comments -q '.comments[-8:]' — all
are auto-posted "Judgment opened"/"Verdict: PR #?" pairs from
delegated-judgment watchdog machinery, firing every ~30-90s against
various roles' branches (localization, ux-engineering,
defect-verification), none naming a resolved PR number or citing
ux-engineering content. Out of scope for this phase-1 unit; no
reconciliation action needed beyond this citation.

amendments-reconciled: issuecomment-5288389172. canonical: gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5288389172 — same
templated watchdog "Verdict: PR #? → escalate" body as the prior
entries above; out of scope for this phase-1 unit, no reconciliation
action needed beyond this citation.

amendments-reconciled: issuecomment-5288392464. canonical: gh issue
view 1199 --json comments -q '.comments[-1]' — same templated watchdog
"Verdict: PR #? → escalate" body as the prior entries above; out of
scope for this phase-1 unit, no reconciliation action needed beyond
this citation.

gh pr create for this unit's branch hit pr-preflight's
amendments-reconciled gate four consecutive times in this session (ids
5288372590, 5288383520, 5288389172, 5288392464 — see entries above),
each retry racing a new watchdog "Judgment opened"/"Verdict: PR #? →
escalate" comment pair that lands roughly every 30-90s. canonical:
on-the-record/hooks/pr-preflight.sh:259-267 — the hook's own
machine-comment-cursor section (issue #1310) states this exact comment
shape should not count as a blocking "newest comment", but
`_MACHINE_BODY_RE` (pr-preflight.sh:266-270) does not match the
"Judgment opened: PR #? —"/"Verdict: PR #? → escalate" body shape, so
these watchdog comments keep racing `gh pr create`. Filing this as a
deviation rather than editing the hook myself (out of this unit's
write scope). Commits for this rework are pushed to origin
(issue-1199/ux-engineering) but no PR is open — treating this the same
as a network-blocked push per session instructions: the commit lands,
PR creation is the open item.

## 2026-08-14 plugin-ecosystem rework (phase 2 executed)

Redo of the tool-landscape fold-in above under issue-1199's 2026-08-14
operator amendment (supersedes the broad reading the section above was
authored under). canonical: this file's own upstream-work section
above (search "five named upgrade targets"), read this session — the
five entries there (Tokens Studio, Stark, Radix UI, Storybook, Optimal
Workshop) are general practitioner design-tooling platforms; none
names a Claude Code plugin repo. Per the amendment, a fold-in whose
surveyed sources are domain tools alone fails issue-1199's Acceptance
criterion 1.

Approved via the phase-1 proposal
(docs/issue-1199/proposals/2026-08-14-ux-engineering-plugin-tool-landscape-rework.md,
committed cf798408) and the issue-level `APPROVE
issue-1199/ux-engineering` comment. canonical: `gh issue view 1199
--json comments -q '.comments[] | select(.body=="APPROVE
issue-1199/ux-engineering")'`, run this session — two matches, author
JiwonJung94 (an approvers.md account) both times: 2026-08-13T07:02:22Z
(predates this amendment, already consumed by the section above) and
2026-08-15T00:44:43Z — the second postdates the phase-1 proposal
commit (2026-08-14T10:31:20+09:00 = 2026-08-14T01:31:20Z), so it is
valid fresh authorization for this rework's phase-2 delivery per
contract v3 s19.

Surveyed the Claude Code plugin/skill ecosystem for tools relevant to
this role's domain (component/token/design-system specification),
adoption evidence via the tech-feasibility method (stars/forks/
multi-source mentions). Full scouting trail: canonical:
docs/issue-1199/reports/ux-engineering/scout-brief-plugins.md (this
repo, written this session).

- **storybookjs/mcp** (`@storybook/claude-code-plugin`) — an official,
  Storybook-org-published plugin, backed by an MCP server, that lets
  Claude query a live component library's existing stories/docs/build
  instructions from inside a session before generating new UI.
  Adoption: canonical: scout-brief-plugins.md's Category-must-bes
  section (this repo, written this session), quoting
  storybook.js.org/docs/ai/mcp/overview and the plugin's own
  first-party-published status. Design move: source-of-truth lookup
  runs before authoring, not after. Learning → `layout-grouping.md`
  rule 8: before specifying a new component to fill a grouped layout's
  slot, check the live component library rather than a stale mental
  snapshot.

- **wilwaldon/Claude-Code-Frontend-Design-Toolkit** — a curated
  collection layering design-token (OKLCH wide-gamut color space, a
  single derived-hue variable driving a full palette), theming, and
  accessibility-tree-based testing tools on top of Anthropic's
  first-party `frontend-design` skill. Adoption: canonical:
  scout-brief-plugins.md's Sources-cited WebFetch result quoted in that
  file (this repo, written this session) — "This repository has 636
  stars and 79 forks." Design move: a concrete, named color-space
  default instead of a bare "define tokens" instruction. Learning →
  `color-visibility.md` rule 8: default new color tokens to a
  perceptually-uniform wide-gamut space (e.g. OKLCH) with a single
  derived-hue variable driving the ramp.

- **anthropics/claude-plugins-official — `frontend-design` skill** —
  Anthropic's own first-party, auto-invoked frontend skill. Adoption:
  canonical: scout-brief-plugins.md's Category-must-bes section (this
  repo, written this session), quoting a WebSearch result — "The
  claude-plugins-official repository has 30.4k stars." Design move:
  accessibility named as a co-equal technical-requirement constraint
  alongside framework and performance, ahead of a later separate audit
  step. Learning → `control-selection.md` rule 9: name accessibility
  as a co-equal constraint at spec time.

A fourth candidate, darasoba/design-engineer-plugin, was scouted but
not carried forward — canonical: scout-brief-plugins.md's Skip record
(this repo, written this session), quoting a WebFetch result: "The
plugin currently has 1 star and 1 watcher on GitHub, indicating
early-stage adoption" — below the adoption-evidence bar this round
applied.

Applied (not referenced) three native rules directly into the mounted
rulebook repo (tokenmaxxxer/ux-engineering-rulebook,
/home/jwjung/tokenmaxxxer/rulebooks/ux-engineering-rulebook), branch
`issue-1199/plugin-tool-landscape` — `color-visibility.md` rule 8,
`layout-grouping.md` rule 8, `control-selection.md` rule 9. canonical:
`git -C /home/jwjung/tokenmaxxxer/rulebooks/ux-engineering-rulebook
show dd569f8 --stat`, run this session, output:
```
 playbook/color-visibility.md  | 15 +++++++++++++++
 playbook/control-selection.md | 14 ++++++++++++++
 playbook/layout-grouping.md   | 15 +++++++++++++++
 3 files changed, 44 insertions(+)
```

Per the operator's native-application amendment (2026-08-13T06:36:54Z):
no rule text names `storybookjs`, `wilwaldon`, `Claude-Code-Frontend-
Design-Toolkit`, `anthropics/claude-plugins-official`, `frontend-
design`, or a `source:` line pointing at any of them. canonical: `git
-C /home/jwjung/tokenmaxxxer/rulebooks/ux-engineering-rulebook show
dd569f8 -- playbook/color-visibility.md playbook/layout-grouping.md
playbook/control-selection.md | grep -i "storybook\|wilwaldon\|toolkit\|claude-plugins\|frontend-design\|source:"`,
run this session — no output (no match). The tool names, adoption
evidence, and per-insight mapping live only in this record and the
scout brief. No verbatim text was copied from any surveyed repo; all
three rules are paraphrased insight.

Committed in the rulebook repo (commit dd569f8, subject line
"issue-1199: fold Claude Code plugin-ecosystem judgments into three
axes"), pushed to origin/issue-1199/plugin-tool-landscape. PR link
recorded in a follow-up entry to this section once `gh pr create`
succeeds after this reconciliation commit is on the branch.

amendments-reconciled: issuecomment-5299606020, issuecomment-5299606090,
and issuecomment-5299606170 (posted 2026-08-15T00:48:33Z-00:48:35Z by
JiwonJung94) — same templated auto-posted "Judgment opened: PR #? —
candidate decision on branch `issue-1199/ux-engineering` (4 path(s)
changed) entered delegated-judgment evaluation." / "Verdict: PR #? →
escalate (depth or impact axis did not clear)" watchdog shape recorded
as the same unresolved pr-preflight `_MACHINE_BODY_RE` gap named in
this file's Open findings section below; none names a resolved PR
number or cites ux-engineering content beyond the branch name. No
reconciliation action needed beyond this citation.

## Open findings

- gh pr create is blocked by an apparent gap in pr-preflight.sh's
  machine-comment regex (issue #1310's fix) against the
  "Judgment opened"/"Verdict: PR #? → escalate" watchdog comment
  shape, which races indefinitely on this busy issue thread. Needs
  either a hook fix (extend `_MACHINE_BODY_RE`) or a manual PR-open by
  someone with a wider retry/backoff window.
