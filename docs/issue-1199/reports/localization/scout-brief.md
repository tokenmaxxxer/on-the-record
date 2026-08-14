# Scout brief: localization tool landscape (issue-1199)

Mode: batched-sequential WebSearch (parallel tool calls within one
turn), no subagent fan-out. derived: 1 sweep stage + 1 deepening stage
run this session (canonical: tool-call transcript, this session);
budget was 5 stages / 3min, well under.

## Must-bes (what the strong tools assume)
- Key completeness is enforced by an automated base-vs-target diff, not
  manual review (Crowdin/Lokalise category norm).
- Plural-category logic is sourced from a maintained CLDR data table,
  not hand-copied (i18next ecosystem).
- Terminology/consistency is checked project-wide across all keys
  sharing a source term, not per-key only (Weblate).

## Performance axes tools compete on
- Translator structural freedom vs. forced source-shape mirroring
  (Fluent's differentiator).
- Automation depth of key-diff/consistency checking (Crowdin/Lokalise/
  Weblate compete here).
- CLDR-data freshness (i18next ecosystem's differentiator over
  hand-rolled plural logic).

## Adopt / skip
- Adopt: automated key-diff as the key-completeness mechanism (rule
  added, string-externalization.md item 6); asymmetric/structure-free
  target messages (rule added, string-externalization.md item 7);
  CLDR-versioned plural runtime requirement (rule added,
  pluralization-and-grammar.md item 6); project-wide terminology
  consistency check (rule added, locale-convention-formatting.md item
  6).
- Skip: installing/depending on any of the four tools themselves — only
  the design move is borrowed, per issue-1199's no-catalog constraint.

## Gap line
canonical: survey.md's "Mapping to existing rulebook state" section,
written this session. The current rulebook state already had per-key
checklist rules for key completeness, plural branching, and
locale-convention formatting, but none of them required (a) automation
over manual review, (b) a maintained/versioned data source over a
static table, or (c) a cross-key consistency check — all three gaps
line up with what the four surveyed tools' adoption is built around.

## Segment fit
This is a docs/methodology role (not a UI/product build), so the fit
check is: does the design move translate into a checklist/rule
instruction rather than a tool integration? All four do.

## Sources

```
https://github.com/projectfluent/fluent
https://github.com/mozilla-l10n
https://hacks.mozilla.org/2019/04/fluent-1-0-a-localization-system-for-natural-sounding-translations/
https://metalglot.com/blog/mozilla-fluent/
https://github.com/WeblateOrg/weblate
https://docs.weblate.org/en/latest/user/checks.html
https://docs.weblate.org/en/latest/user/glossary.html
https://6sense.com/tech/translation-and-localization/crowdin-vs-lokalise
https://github.com/topics/react-i18next
https://github.com/topics/next-i18next
https://github.com/i18next/i18next/issues/1202
```
