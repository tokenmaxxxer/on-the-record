---
subject: issue-1199
role: localization
loop_state: scope-proposed
status: proposed
files:
  - playbook/string-externalization.md
  - playbook/pluralization-and-grammar.md
  - playbook/locale-convention-formatting.md
  - docs/issue-1199/reports/localization.md
---

# Proposal: fold localization's surveyed tool landscape into the rulebook (issue-1199)

All file paths above (except the report) live in the separate rulebook
repo ("tokenmaxxxer/localization-rulebook", mounted at
/home/jwjung/tokenmaxxxer/rulebooks/localization-rulebook — see
docs/issue-1199/reports/localization/survey.md), not in this working
tree; phase 2 works and commits there directly, mirroring the
brand-design precedent (docs/issue-1199/proposals/2026-08-13-brand-design-tool-landscape.md).

## 조사 근거

docs/issue-1199/reports/localization/survey.md and
docs/issue-1199/reports/localization/scout-brief.md, this session:
four tools surveyed with adoption evidence — Project Fluent (spec +
fluent.js star counts), Weblate (WeblateOrg/weblate star/fork counts),
Crowdin vs. Lokalise (6sense customer-count/market-share comparison),
and the i18next ecosystem (react-i18next/next-i18next star counts,
i18next/i18next#1202 CLDR-revision issue). Gap line in scout-brief.md:
the existing three playbook axis files already had per-key checklist
rules but none required automation-over-manual-review, a
maintained/versioned data source over a static table, or a cross-key
consistency check.

## 채택 항목

1. Automated base-locale-vs-target-locale key diffing as the
   key-completeness mechanism, upgrading
   `playbook/string-externalization.md`'s key-management axis — cites
   survey.md item 3 (Crowdin/Lokalise adoption comparison).
2. Structure-free target messages (not just split keys) for
   grammatically divergent locales, upgrading the same file's
   grammatical-role rule — cites survey.md item 1 (Project Fluent
   asymmetric localization).
3. CLDR-versioned plural runtime requirement, upgrading
   `playbook/pluralization-and-grammar.md`'s plural-branching rule —
   cites survey.md item 4 (i18next ecosystem).
4. Project-wide terminology-consistency check, upgrading
   `playbook/locale-convention-formatting.md`'s locale-convention axis
   — cites survey.md item 2 (Weblate).

## 논리적 근거

Each item closes a gap the scout-brief's Gap line names explicitly, and
each traces to a specific surveyed tool's documented design move (not a
pretrained-recall listing) — per issue-1199 requirement 2's research
depth and requirement 4's named-upgrade-target rule.

## 반영 계획

Add one numbered rule (or two, for string-externalization.md) to each
of the three playbook axis files, in the same "when/choose/source"
format already used in those files, each citing the surveyed tool's
adoption evidence and the specific rule item it upgrades — never a
tool-catalog section, no verbatim copying from the tools' own docs.
docs/issue-1199/reports/localization.md is phase-2 output, written only
after approval opens phase 2, per contract v3 s19.

## Out of scope
- Any change to the localization plugins/hooks (verdict-axis,
  mqm-tagging, proposal-gate) — no surveyed tool maps to those gate
  mechanics.
- Installing or depending on any of the four surveyed tools — the
  fold-in borrows the design move only.

## How you'll know it worked
Phase 2 diff, reviewed against this proposal, adds exactly the four
items above (each carrying tool name, adoption-evidence citation,
problem, how, and the rule it upgrades) with no deletion of existing
playbook text, no "learned from repo X" attribution language, and no
tool-catalog section anywhere in the rulebook repo.
