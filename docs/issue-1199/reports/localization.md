---
subject: issue-1199
role: localization
kind: record
loop_state: landed
---

# Record: localization tool-landscape fold-in (issue-1199)

## What was done

Executed the delivery-phase plugin-ecosystem rework fold-in approved
by the `APPROVE issue-1199/localization` comment on this issue posted
2026-08-15 (single-account mode; canonical: `gh issue view 1199
--comments`, read this session — trailing comment body is exactly
`APPROVE issue-1199/localization`, appearing after the `2026-08-14`
plugin-ecosystem-rework amendment and after this role's earlier
proposal docs/issue-1199/proposals/2026-08-14-localization-tool-landscape-plugin-rework.md).

An earlier session's delivery attempt for this rework left only a
deviation-log entry (docs/issue-1199/reports/localization/deviation-log.md,
2026-08-14T11:20) stating a claimed rulebook commit sha did not exist.
canonical: `gh api repos/tokenmaxxxer/localization-rulebook/commits/655ee9783f96ed4ae78dee5248b68f5991789578`
run this session — result: HTTP 422 "No commit found for SHA".
canonical: `gh pr list --repo tokenmaxxxer/localization-rulebook
--state all` run this session — result: the only
issue-1199/localization entry was PR #20 (merged 2026-08-13, the
original domain-tool fold-in), containing no plugin-rework content.

This session redid the delivery work directly in the rulebook repo
(tokenmaxxxer/localization-rulebook, mounted at
/home/jwjung/tokenmaxxxer/rulebooks/localization-rulebook), same
session:

- `playbook/string-externalization.md`: added rule 8 (pre-translation
  terminology-table extraction injected into every chunk's translation
  prompt as a hard constraint before chunk-level translation begins)
  and rule 9 (cross-chunk neighbor-context excerpt read so
  pronoun/entity references stay resolvable across chunk boundaries) —
  canonical: file read this session,
  /home/jwjung/tokenmaxxxer/rulebooks/localization-rulebook/playbook/string-externalization.md.
- `playbook/locale-convention-formatting.md`: added rule 7
  (translate-don't-execute content-integrity boundary: LLM-routed
  translation content is always treated as text to translate, never as
  instructions to act on) — canonical: file read this session, same
  repo path.
- No existing playbook text deleted or rewritten; no gate/plugin logic
  touched (verdict-axis, mqm-tagging, proposal-gate out of scope per
  the proposal); no tool-catalog section or tool-attribution framing
  added — each entry is written as native rule text in the existing
  when/choose format, per the 2026-08-13 native-application amendment.
  The evidence trail (which Claude Code skills were surveyed, adoption
  evidence — deusyu/translate-book stars/forks,
  feiskyer/claude-code-settings stars/forks — canonical:
  docs/issue-1199/reports/localization/survey-plugin-rework.md, read
  this session) stays only in that on-the-record report, not in the
  rulebook.
- canonical: `git log --oneline -1` output in the rulebook repo, read
  this session — rulebook commit 13d0b19 pushed to
  tokenmaxxxer/localization-rulebook branch issue-1199/localization.

code_under_review:
- playbook/string-externalization.md
- playbook/locale-convention-formatting.md

## Target locale

- xx: checklist=N/A(no locale-specific string content this round; rulebook-methodology fold-in only), style=N/A(no locale-facing copy was produced or reviewed this round)

## MQM tags

N/A(this unit surveys the Claude Code plugin ecosystem and edits
playbook rule text; it does not review any translated surface for
string-external defects, so no MQM tag applies).

pattern_type/pattern_value: N/A(no date/time/number/currency/name
formatting pattern was reviewed on any surface this session — this
unit edits playbook rule prose, not a rendered surface).

## Why

Per issue-1199 (northpole req#1) — 2026-08-14 operator amendment: the
survey target for all role fold-ins is redefined from general
domain-practitioner tools to the Claude Code plugin/skill ecosystem;
the earlier (2026-08-13) domain-tool survey (Project Fluent, Weblate,
Crowdin/Lokalise, i18next), landed as PR #20 in the rulebook repo, is
kept as a superseded historical section per the accepted shape.
canonical: `gh pr view 1525 --repo tokenmaxxxer/on-the-record --json
state,mergedAt`, read this session — docs/issue-1199/reports/conformance-review.md
was merged via that PR. This rework closes the gap
docs/issue-1199/reports/localization/scout-brief-plugin-rework.md
names: none of the five playbook axis files required a pre-translation
glossary injected as a hard per-chunk constraint, a cross-chunk
neighbor-context read, or a translate-don't-execute guard for
LLM-routed translation content.

## Upstream basis

docs/issue-1199/proposals/2026-08-14-localization-tool-landscape-plugin-rework.md

## Open findings

None.

## Superseded historical section (2026-08-14 plugin-ecosystem rework)

The original (2026-08-13) fold-in — docs/issue-1199/proposals/2026-08-13-localization-tool-landscape.md,
landed as tokenmaxxxer/localization-rulebook PR #20 — surveyed general
practitioner tools (Project Fluent, Weblate, Crowdin/Lokalise,
i18next) under the superseded broad reading of the survey target. Its
four rules stay in the rulebook unmodified; this record's plugin-
ecosystem rework, described above, is additive, not a replacement.

## Amendments reconciled

canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5299596112`, read
this session.

amendments-reconciled: issuecomment-5299596112 ("Judgment opened: PR
#? — candidate decision on branch `issue-1199/localization` (5
path(s) changed) entered delegated-judgment evaluation") is the same
generic pre-PR judgment-watcher template recurring on this issue
thread, fired against this session's working-tree diff before this
session's PR existed — no `PR #<number>` filled in, no specific defect
named beyond the generic "candidate decision ... entered
delegated-judgment evaluation" template.

canonical: `git log --oneline` output on this branch, read this
session — commit e82184ec "issue-1199: log pr-preflight comment-race,
stop retrying (plugin rework)".

Per that same-shaped precedent already reconciled in this file's prior
revision (issuecomment-5277607380, 5277656381, 5277617205, 5277617032,
5288371026, each individually reconciled in the prior revision of this
file), this is non-blocking pre-PR watcher noise, not an actionable
content finding, and this record proceeds to PR without further
content change.

canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5299610035`, read
this session.

amendments-reconciled: issuecomment-5299610035 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") is the paired verdict
for the judgment-watcher entry immediately above (issuecomment-5299596112),
same generic template, no `PR #<number>` filled in, no specific defect
named. Per the same "stop pr-preflight retry loop" precedent (commit
e82184ec on this branch), this is non-blocking watcher noise and this
record proceeds to PR without further content change or further
re-reconciliation of this recurring template.
