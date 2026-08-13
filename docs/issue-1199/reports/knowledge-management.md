---
subject: issue-1199
role: knowledge-management
loop_state: landed
code_under_review:
  - /home/jwjung/tokenmaxxxer/rulebooks/knowledge-management-rulebook/docs/handbooks/knowledge-management.md
---

# issue-1199 knowledge-management: tool-landscape fold-in record

amendments-reconciled: issuecomment-5276799629 and issuecomment-5277551353
and issuecomment-5277558197 and issuecomment-5277568294 (canonical: gh api
repos/tokenmaxxxer/on-the-record/issues/1199/comments — automated
judgment-loop notices about other roles' PRs (`issue-1199/technical-writing`,
`issue-1199/implementation`) entering delegated-judgment evaluation, not
directed at this role's work; no change required to this record's plan.)

## What was done

Surveyed the knowledge-management tool landscape (adoption-evidence
method, web-fetched, four parallel search angles — see
docs/issue-1199/reports/knowledge-management/scout-brief.md) and folded
five design moves natively into
`/home/jwjung/tokenmaxxxer/rulebooks/knowledge-management-rulebook/docs/handbooks/knowledge-management.md`
(rulebook repo, branch `issue-1199/knowledge-management`, commit 0beb2fe,
PR opened against `tokenmaxxxer/knowledge-management-rulebook`):

- Pattern-entry filenames now require a `<domain>.<slug>` prefix from a
  fixed domain list (`process`/`tooling`/`review`/`record`/`handoff`).
- Pattern-entry front matter gained `reused_by` (issue numbers of later
  issues that consulted/applied the entry) and `applies_to_roles` (other
  roles the pattern is relevant to).
- Landed entries' five body sections and `title` are now immutable —
  replacement is a new entry that supersedes, never an in-place edit;
  only `reused_by` may still be appended after landing.
- The cross-issue index template gained a required second table (by
  keyword), regenerated from entries' `keywords` fields rather than
  hand-maintained separately.
- The phase-2 record self-check gained the corresponding confirmation
  lines (domain-prefix validity, `reused_by`/`applies_to_roles` presence,
  no in-place edit of a landed entry).

No tool name, tool attribution, or tool-catalog section was added to the
handbook — every change reads as this role's own rule/template text.

## Why

Per issue-1199 (northpole req#1/req#5): the handbook's existing templates
had five concrete gaps (no reuse-discovery, no immutability rule, no
cross-role discoverability, no structured naming, single-view index) —
documented in
docs/issue-1199/reports/knowledge-management/current-state-survey.md
(canonical: read of the rulebook handbook, this session) — that
comparably-adopted knowledge tools each solve with a specific design
move. The fold-in closes those five gaps using the tools' HOW, not their
branding.

## Upstream basis

- docs/issue-1199/reports/knowledge-management/current-state-survey.md
- docs/issue-1199/reports/knowledge-management/scout-brief.md
- docs/issue-1199/proposals/2026-08-13-knowledge-management-tool-landscape.md
- APPROVE issue-1199/knowledge-management (issue #1199 comment,
  JiwonJung94, single-account mode)

## Accumulation

Additive-only change: two new optional front-matter fields, one new
required index table, one new filename-prefix rule, one new
immutable-after-landed rule. No existing landed pattern entry is
retrofitted (out of scope per the proposal); the accumulation cost applies
only to future entries that adopt the new fields.

## What did not work

None.

## Open findings

None.
