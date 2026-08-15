# Scout brief (rework): localization — Claude Code plugin ecosystem (issue-1199)

Mode: parallel WebSearch fan-out (4 queries in one turn), then two
deepening WebFetch/gh-api calls in the next turn. canonical: tool-call
transcript, this session. derived: 1 sweep stage + 1 deepening stage;
budget was 5 stages / 3min, well under.

## Must-bes (what the strong Claude Code translation skills assume)
- Cross-chunk terminology consistency needs a shared glossary built
  BEFORE translation starts and injected into every chunk's prompt as a
  hard constraint, not left to each chunk's own judgment
  (deusyu/translate-book).
- A translation-pipeline skill must not treat source content as
  instructions — the skill text itself states a translate-don't-execute
  rule (feiskyer/claude-code-settings translate skill).

## Performance axes tools compete on
- Consistency-preservation mechanism when translation work is chunked
  across parallel agents: glossary injection + neighbor-context reads
  (deusyu/translate-book) vs. no stated mechanism surfaced in the
  sweep's other candidates. canonical: `gh api
  repos/senshinji/claude-translation-skill --jq
  '{stars:.stargazers_count}'`, read this session: 21 stars — too small
  an adoption signal to use as the primary example, so it is context
  only, not a surveyed candidate.
- Depth of source-integrity handling: an explicit instruction-injection
  guard (feiskyer) vs. skills that only state translation quality goals
  with no content-integrity guard mentioned.

## Adopt / skip
- Adopt: pre-translation glossary extraction injected as a hard
  per-chunk constraint (rule added, string-externalization.md new item);
  cross-chunk neighbor-context read for pronoun/entity resolution (rule
  added, string-externalization.md new item); translate-don't-execute
  rule for any content routed through LLM-based translation (rule
  added, locale-convention-formatting.md new item).
- Skip: installing/depending on deusyu/translate-book or
  feiskyer/claude-code-settings themselves — only the design move is
  borrowed, per issue-1199's no-catalog constraint. Skip also: the
  chunk-manifest SHA-256 mechanism itself (an implementation detail of
  one skill's file-merge step, not a rule the rulebook's checklist axis
  can state as a locale-fitness judgment).

## Gap line
canonical: survey-plugin-rework.md's "Mapping to existing rulebook
state" section, written this session. None of the five playbook axis
files had a rule for pre-translation glossary injection, cross-chunk
neighbor-context resolution, or a translate-don't-execute guard for
LLM-routed content — all three gaps line up with what the two surveyed
Claude Code skills' designs are built around, and none were present
even after survey.md's earlier (domain-tool-basis) fold-in.

## Segment fit
This is a docs/methodology role (not a UI/product build): the fit check
is whether each design move translates into a checklist/rule
instruction rather than a tool integration. All three adopted items do
— they read as "when a translation workflow is chunked/LLM-routed,
choose X."

## Sources

```
https://github.com/deusyu/translate-book
https://github.com/feiskyer/claude-code-settings
https://raw.githubusercontent.com/feiskyer/claude-code-settings/main/skills/translate/SKILL.md
https://github.com/senshinji/claude-translation-skill
https://github.com/jeremylongshore/claude-code-plugins-plus-skills
```
