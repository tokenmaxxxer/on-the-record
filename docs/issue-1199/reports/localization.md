---
subject: issue-1199
role: localization
kind: record
loop_state: landed
---

# Record: localization tool-landscape fold-in (issue-1199)

## What was done

Executed the phase-2 fold-in approved by the `APPROVE
issue-1199/localization` comment on this issue (single-account mode;
canonical: `gh issue view 1199 --comments`, read this session — trailing
comment body is exactly `APPROVE issue-1199/localization`). Ran the
phase-1 survey/scout/proposal in this working tree
(docs/issue-1199/reports/localization/survey.md,
docs/issue-1199/reports/localization/scout-brief.md,
docs/issue-1199/proposals/2026-08-13-localization-tool-landscape.md)
and the phase-2 edit directly in the separate rulebook repo
(tokenmaxxxer/localization-rulebook, mounted at
/home/jwjung/tokenmaxxxer/rulebooks/localization-rulebook), same
session:

- `playbook/string-externalization.md`: added rule 6 (automated
  base-vs-target key diffing as the key-completeness mechanism, citing
  Crowdin/Lokalise adoption evidence) and rule 7 (structure-free target
  messages, citing Project Fluent's asymmetric localization) —
  canonical: file read this session,
  /home/jwjung/tokenmaxxxer/rulebooks/localization-rulebook/playbook/string-externalization.md.
- `playbook/pluralization-and-grammar.md`: added rule 6 (CLDR-versioned
  plural runtime requirement, citing the i18next ecosystem and
  i18next/i18next#1202) — canonical: file read this session, same repo
  path.
- `playbook/locale-convention-formatting.md`: added rule 6 (project-wide
  terminology-consistency check, citing Weblate's cross-translation
  check and glossary terminology flag) — canonical: file read this
  session, same repo path.
- No existing playbook text deleted; no gate/plugin logic touched
  (verdict-axis, mqm-tagging, proposal-gate out of scope per the
  proposal); no tool-catalog section added anywhere — each entry is a
  rule in the existing when/choose/source format, not a listing.

code_under_review:
- playbook/string-externalization.md
- playbook/pluralization-and-grammar.md
- playbook/locale-convention-formatting.md

## Target locale

- xx: checklist=N/A(no locale-specific string content this round; rulebook-methodology fold-in only), style=N/A(no locale-facing copy was produced or reviewed this round)

## MQM tags

N/A(this unit surveys tools and edits playbook rule text; it does not
review any translated surface for string-external defects, so no MQM
tag applies).

pattern_type/pattern_value: N/A(no date/time/number/currency/name
formatting pattern was reviewed on any surface this session — this
unit edits playbook rule prose, not a rendered surface).

## Why

Per issue-1199 (northpole req#1/req#5): the localization role's
rulebook encoded checklist/style-guide methodology but had not learned
from the tool ecosystems localization practitioners actually use. The
four entries close the gap the phase-1 scout brief identified —
automated key-diffing, maintained/versioned CLDR data, cross-key
terminology consistency, and structure-free target messages — none of
which the prior checklist wording required.

## Upstream basis

docs/issue-1199/proposals/2026-08-13-localization-tool-landscape.md

## Open findings

None.

amendments-reconciled: issuecomment-5277607380 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") is a delegated-judgment
verdict for a different, unnumbered candidate PR on branch
`issue-1199/incident-response` (canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5277607380`, read this
session) — it does not name or reference this localization unit's
rulebook-repo PR, so no content amendment to this record is warranted.
