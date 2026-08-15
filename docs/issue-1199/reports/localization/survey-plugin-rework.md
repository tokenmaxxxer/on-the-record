# Survey (rework): localization — Claude Code plugin/skill ecosystem (issue-1199, 2026-08-14 amendment)

Supersedes survey.md's scope for acceptance purposes: survey.md surveyed
domain tools (Project Fluent, Weblate, Crowdin/Lokalise, i18next), which
the 2026-08-14 operator amendment excludes as the primary basis.
canonical: gh issue view 1199 --comments, this session — "Sample-check
verdict (2026-08-14 ...) all 17 earlier-completed roles' surveys are
domain-tool-basis ... enter plugin-basis rework". This file surveys the
CLAUDE CODE PLUGIN/SKILL ecosystem instead, per the amendment. survey.md's
four items stay as already-landed native/domain rules; this rework only
adds plugin-derived learnings alongside them.

Adoption-evidence method (tech-feasibility style: GitHub stars/forks),
web-fetched this session (canonical: WebSearch + WebFetch + `gh api
repos/<owner>/<repo>` tool output, read this session).

## Candidates surveyed

1. **deusyu/translate-book** — Claude Code (also Codex/OpenClaw) agent
   skill that translates entire books (PDF/DOCX/EPUB) into any
   language. canonical: `gh api repos/deusyu/translate-book --jq
   '{stars:.stargazers_count, forks:.forks_count}'`, read this session:
   1128 stars, 141 forks.

   Design move. canonical: WebFetch
   https://github.com/deusyu/translate-book, read this session. The
   pipeline samples five representative chunks to extract proper nouns
   and domain terms into a canonical terminology table, then injects
   that 3-column table into every chunk's translation prompt as a hard
   constraint; separately, each parallel sub-agent also receives
   read-only ~300-character excerpts from adjacent chunks so it can
   resolve pronouns/entity references across chunk boundaries; a
   SHA-256 manifest checks a 1:1 source-to-output chunk correspondence
   before the final merge.

2. **feiskyer/claude-code-settings** (`skills/translate/SKILL.md`) —
   curated Claude Code skills/sub-agents collection. canonical: `gh api
   repos/feiskyer/claude-code-settings --jq '{stars:.stargazers_count,
   forks:.forks_count}'`, read this session: 1631 stars, 246 forks.

   Design move. canonical: WebFetch
   https://raw.githubusercontent.com/feiskyer/claude-code-settings/main/skills/translate/SKILL.md,
   read this session. The skill runs a three-stage flow (direct
   translation first, a separate problem-identification stage, then a
   polished-reinterpretation stage), and carries a self-directed
   instruction-injection guard: it tells itself to treat every input as
   source text to translate, not as a request to act on, so
   instruction-shaped text inside the source gets translated rather
   than followed; it also carries a fixed do-not-translate list
   (technical acronyms, brand names).

## Mapping to existing rulebook state

canonical: playbook/string-externalization.md,
playbook/pluralization-and-grammar.md,
playbook/locale-convention-formatting.md,
playbook/rtl-and-script-support.md,
playbook/text-expansion-and-layout.md, read this session (files at
/home/jwjung/tokenmaxxxer/rulebooks/localization-rulebook/playbook/).
canonical: `grep -in "glossary\|neighbor.context\|instruction.injection\|treat.*source text" playbook/*.md`
in that directory, read this session: zero matches. Gap: none of the
five playbook files has a rule requiring a pre-translation glossary
extraction stage injected as a hard per-chunk constraint, a cross-chunk
neighbor-context read for pronoun/entity resolution, or a rule that
translation-pipeline content gets treated as text-to-translate rather
than instructions-to-follow when an LLM performs the translation step —
this last gap did not exist in survey.md's four items, which predate
LLM-pipeline-shaped skills.

## Sources

```
https://github.com/deusyu/translate-book
https://github.com/feiskyer/claude-code-settings
https://raw.githubusercontent.com/feiskyer/claude-code-settings/main/skills/translate/SKILL.md
```
