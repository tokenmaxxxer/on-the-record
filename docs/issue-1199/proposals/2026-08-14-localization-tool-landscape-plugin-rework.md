---
subject: issue-1199
role: localization
loop_state: scope-proposed
status: proposed
files:
  - playbook/string-externalization.md
  - playbook/locale-convention-formatting.md
  - docs/issue-1199/reports/localization.md
---

# Proposal: rework localization's tool-landscape fold-in to the Claude Code plugin ecosystem (issue-1199, 2026-08-14 amendment)

Rework of docs/issue-1199/proposals/2026-08-13-localization-tool-landscape.md,
whose four already-landed items (PR #1272, merged) surveyed domain tools
(Project Fluent, Weblate, Crowdin/Lokalise, i18next) — per the 2026-08-14
operator amendment those fail the acceptance check because the survey
target is now the Claude Code plugin/skill ecosystem. Those four items
are NOT removed; this proposal adds plugin-derived learnings alongside
them, same rework pattern already accepted for
interaction-design/ml-engineering/observability (see the issue's
2026-08-14 comment thread). All file paths above (except the report)
live in the separate rulebook repo
("tokenmaxxxer/localization-rulebook", mounted at
/home/jwjung/tokenmaxxxer/rulebooks/localization-rulebook); phase 2
works and commits there directly.

## 조사 근거

docs/issue-1199/reports/localization/survey-plugin-rework.md and
docs/issue-1199/reports/localization/scout-brief-plugin-rework.md, this
session: two Claude Code skills surveyed with adoption evidence —
deusyu/translate-book (1128 stars, 141 forks — glossary-injection +
neighbor-context design) and feiskyer/claude-code-settings's
`skills/translate/SKILL.md` (1631 stars, 246 forks — three-stage
translation flow + translate-don't-execute instruction-injection
guard). Gap line in scout-brief-plugin-rework.md: none of the rulebook's
five playbook axis files required a pre-translation glossary injected
as a hard per-chunk constraint, a cross-chunk neighbor-context read, or
a translate-don't-execute guard for LLM-routed translation content.

## 채택 항목

1. Pre-translation glossary extraction, injected into every
   translation-batch prompt as a hard constraint before chunk-level
   translation work begins, upgrading
   `playbook/string-externalization.md`'s key-completeness/terminology
   handling — cites survey-plugin-rework.md item 1
   (deusyu/translate-book).
2. Cross-chunk neighbor-context read (adjacent-chunk excerpts) as a
   required step when translation work is split across multiple
   batches/agents, so pronoun/entity references stay resolvable across
   chunk boundaries — upgrading the same file's grammatical-role
   handling — cites survey-plugin-rework.md item 1
   (deusyu/translate-book).
3. Translate-don't-execute rule: any content routed through an
   LLM-based translation step must be treated as text to translate, not
   instructions to act on, upgrading
   `playbook/locale-convention-formatting.md` with a new
   content-integrity item — cites survey-plugin-rework.md item 2
   (feiskyer/claude-code-settings translate skill).

## 논리적 근거

Each item closes a gap scout-brief-plugin-rework.md's Gap line names
explicitly, and each traces to a specific surveyed Claude Code skill's
documented design move (adoption evidence: GitHub stars/forks, not a
pretrained-recall listing) — per issue-1199 requirement 2's research
depth and requirement 4's named-upgrade-target rule, and per the
2026-08-14 amendment's plugin-ecosystem survey-target requirement.
Item 3 is new relative to the original (2026-08-13) fold-in: it did not
surface from the domain-tool survey because none of Fluent/
Weblate/Crowdin/Lokalise/i18next are themselves LLM-driven translation
pipelines, so none of them carry a content-vs-instruction integrity
concern the way an LLM-based Claude Code translation skill does.

## 반영 계획

Add two numbered rules to `playbook/string-externalization.md` (items
8-9, continuing after the existing 7) and one numbered rule to
`playbook/locale-convention-formatting.md` (item 7, continuing after
the existing 6), in the same "when/choose/source" format already used
in those files, each citing the surveyed skill's adoption evidence and
the specific rule item it upgrades — never a tool-catalog section, no
verbatim copying beyond short quoted phrases already used for
attribution. docs/issue-1199/reports/localization.md is phase-2 output,
written only after approval opens phase 2, per contract v3 s19.

## Out of scope
- Any change to the localization plugins/hooks (verdict-axis,
  mqm-tagging, proposal-gate) — no surveyed skill maps to those gate
  mechanics.
- Installing or depending on deusyu/translate-book or
  feiskyer/claude-code-settings — the fold-in borrows the design move
  only.
- Removing or rewriting survey.md's four already-landed domain-tool
  items — this rework is additive.

## How you'll know it worked
Phase 2 diff, reviewed against this proposal, adds exactly the three
items above (each carrying tool name, adoption-evidence citation,
problem, how, and the rule it upgrades) with no deletion of existing
playbook text, no "learned from repo X" attribution language, and no
tool-catalog section anywhere in the rulebook repo.
