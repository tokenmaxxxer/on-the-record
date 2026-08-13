# Survey: localization tool landscape (issue-1199)

Adoption-evidence method (tech-feasibility style: stars/customers/multi-source),
web-fetched this session (canonical: WebSearch tool output, read this
session), per issue-1199 requirement 1 and northpole req#1.

## Candidates surveyed

1. **Project Fluent** (Mozilla). canonical: WebSearch "Mozilla Fluent
   localization project github stars asymmetric localization", read
   this session. Design move: "asymmetric localization" — the developer
   exposes an ID plus raw data (count, etc.); the translator's message
   owns its own grammatical structure instead of being forced into the
   source string's 1:1 shape. Source: Mozilla Hacks blog post
   introducing Fluent (see Sources block below).

2. **Weblate** — WeblateOrg/weblate. canonical: WebSearch "Weblate open
   source translation platform github stars glossary consistency
   check", read this session. Design move: project-wide
   cross-translation consistency check (same source string, different
   translations, flagged) plus a glossary component with a
   "terminology" flag applied project-wide. Source: Weblate docs
   "Checks and fixups" and "Glossary" (see Sources block below).

3. **Crowdin vs. Lokalise (TMS category, adoption comparison)** —
   canonical: WebSearch "Crowdin vs Lokalise translation management
   platform adoption customers 2026", read this session; figures
   sourced from 6sense's category comparison page (see Sources block
   below). Design move both center: automated base-locale-vs-target-
   locale key diffing as the operative workflow, not a manual file
   read-through.

4. **i18next ecosystem (CLDR-backed plural runtime)** — canonical:
   WebSearch `"i18next" github repository stars count`, read this
   session; GitHub Topics pages for react-i18next and next-i18next (see
   Sources block below). Design move: plural-category selection
   delegated to a maintained, versioned CLDR data source at runtime
   rather than a hand-copied static table; i18next's own issue tracker
   documents a live CLDR rule revision (Hebrew) landing in the library
   (see Sources block below).

## Method note

derived: 4 WebSearch calls issued in one parallel tool-call batch this
session (canonical: tool-call transcript, this session), plus one
deepening WebSearch call in a follow-up turn after the first round's
i18next result lacked a citable star count.

## Mapping to existing rulebook state

canonical: playbook/string-externalization.md,
playbook/pluralization-and-grammar.md,
playbook/locale-convention-formatting.md, read this session (files at
/home/jwjung/tokenmaxxxer/rulebooks/localization-rulebook/playbook/).
The existing playbook axis files already cite Crowdin, Lokalise, Phrase,
locize, and MQM as rule *sources*, but as prose citations for isolated
rules — none of the four candidates above were present as a surveyed
tool with adoption evidence recorded, and none of the four design moves
(asymmetric localization, cross-translation consistency, automated key
diffing, CLDR-versioned plural runtime) were represented as a rule.

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
