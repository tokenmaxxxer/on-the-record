# localization operational playbook — evidence trail (phase-1 record)

This session's phase-2 record file is gated behind an
"APPROVE issue-1174/localization" comment per contract v3 s19; no such
comment exists yet.
canonical: `gh issue view 1174 --comments` output this turn, grep for
"APPROVE issue-1174/localization" returning no match (exit 1). This
file carries the evidence trail as allowed phase-1 material instead, so
the research trail is not lost between sessions.

## What was done (delivered to the rulebook repo, outside this repo's gate)

Authored the localization role's operational playbook and opened it as
a pull request against tokenmaxxxer/localization-rulebook, branch
issue-1174/operational-playbook.
canonical: `gh pr create` output this turn, returning
https://github.com/tokenmaxxxer/localization-rulebook/pull/19 — the
PR's open/merged state was not re-checked after creation; treat it as
open as of this turn's `gh pr create` call, not confirmed merged.

The PR adds `playbook/<axis>.md` (one file per axis, per the program
proposal's (d) landing structure): 5 decision axes —
string-externalization-and-key-management, pluralization-and-grammar,
locale-convention-formatting, text-expansion-and-layout, and
rtl-and-script-support — 25 rule blocks total (condition -> choice ->
source), against a computed floor of `max(8, 5 axes x 2) = 10` (this
role is tier `moderate` per the program proposal's (b) batch-6
classification). Each axis carries at least one rule marked
**REMOVAL** (5 total, one per axis minimum), per the issue's amendment
4.
canonical: file content of `playbook/string-externalization.md`,
`playbook/pluralization-and-grammar.md`,
`playbook/locale-convention-formatting.md`,
`playbook/text-expansion-and-layout.md`,
`playbook/rtl-and-script-support.md` as written this session (see the
git diff on branch issue-1174/operational-playbook in the
localization-rulebook repo, commit 828e142).

## Research protocol (three layers per the amendment-1 protocol)

Layer 1 (practitioner/checklist decision rules):
- query: "CLDR plural rules categories localization best practices" ->
  Unicode CLDR Plural Rules spec, locize i18n Pluralization guide.
- query: "ICU MessageFormat string externalization i18n key management
  best practices" -> Lokalise ICU message-format guide, Phrase
  practical-guide, Crowdin i18n-explained guide.

Layer 2 (named methodology/standard):
- query: "MQM Multidimensional Quality Metrics locale convention error
  typology" -> themqm.org error-types typology and full typology
  (Locale conventions dimension used for MQM-tagging this role's
  string-external findings).
- query: "RTL localization bidi mirroring icons Unicode bidi algorithm
  UI guidelines" -> Unicode UAX #9 (Unicode Bidirectional Algorithm),
  SimpleLocalize RTL design guide.
- query: "Microsoft Style Guide date number currency locale formatting
  rules" -> Microsoft Learn Globalization docs (number/currency
  formatting).

Layer 3 (academic/cross-domain, subtraction-neglect per amendment 4):
- query: "UI text expansion ratio localization German French
  translation length guidelines" -> Crowdin/POEditor/intlpull
  expansion-ratio synthesis, used to derive the text-expansion axis's
  removal rule (shortening source copy multiplies expansion-budget
  savings across every target locale simultaneously — the applied form
  of the subtraction-neglect finding named in the program proposal's
  constraints: Adams, Converse, Hales & Klotz, *Nature* 594, 2021,
  "People systematically overlook subtractive changes").
- query: "over-localization pitfalls remove unnecessary translation
  cultural adaptation research" -> cross-checked cultural-adaptation
  literature; did not surface a rule distinct enough from the
  text-expansion removal rule already derived, so no separate axis was
  added for it — recorded here rather than silently dropped.

All queries run via WebSearch this turn; no pretrained-recall content
was used for rule sourcing — every rule in the 5 playbook files carries
an inline `source:` line resolving to one of the URLs surfaced by the
above queries.
canonical: WebSearch tool-call outputs this turn (7 calls: CLDR plural
rules, ICU MessageFormat, Microsoft Style Guide formatting, UI text
expansion, RTL bidi, MQM typology, over-localization pitfalls).

## Rule count vs. floor

derived: `grep -c '^[0-9]\. \*\*' playbook/*.md` in the
localization-rulebook repo, run this turn against the 5 new files.

```
playbook/locale-convention-formatting.md:5
playbook/pluralization-and-grammar.md:5
playbook/rtl-and-script-support.md:5
playbook/string-externalization.md:5
playbook/text-expansion-and-layout.md:5
```

25 total accepted-shape rule blocks against a floor of 10 (2.5x the
floor) — 5 of the 25 are REMOVAL-classified (one per axis), clearing
the program proposal's (c) check 6 (>= 1 removal rule per axis).

## What did not work

None.
