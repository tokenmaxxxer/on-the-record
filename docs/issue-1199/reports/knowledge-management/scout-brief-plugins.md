kind: report
subject: issue-1199
doc-type: reference

# knowledge-management — Claude Code plugin/skill scout brief (2026-08-14 amendment)

canonical: WebSearch results this turn (queries: "most popular Claude Code
plugin marketplace skills 2026 knowledge management notes obsidian";
"\"claude code\" plugin skill github stars memory knowledge base ADR
decision record"; "claudeskills.info ADR lifecycle plugin superseding
linking documentation 65.4k stars") — pages listed under Sources below.

## Skip record

canonical: this WebSearch sweep and one deepening round, this turn.
Scouting ran — 2 sweep angles (general KM/PKM plugin landscape; memory/
ADR-specific plugin landscape), plus 1 deepening round on the
ADR-lifecycle plugin's name and star count. 3 stages total, within the
5-stage/3min budget.

## Category must-bes (from sweep)

canonical: WebSearch results this turn — github.com/coleam00/claude-memory-compiler,
github.com/Korni22/claude-adr, github.com/terrylica/cc-skills (see
Sources).

- A Claude Code plugin/skill sub-ecosystem for knowledge-capture exists,
  separate from general PKM apps: session-memory compilers, ADR-lifecycle
  plugins, and multi-domain skill bundles that carry KM/ADR skills.
- ADR-lifecycle management appears as its own plugin category, with
  several independent publishers (Korni22, zircote, madappgang) each
  shipping one.
- Among these, the strongest adoption signal points at one plugin that
  bundles create/index/supersede/link into a single invocation, rather
  than three separate author steps.

## Candidates (adoption evidence, problem, how)

1. **coleam00/claude-memory-compiler** — GitHub repo, its own README
   traces to a named public architecture write-up (Karpathy's LLM
   knowledge-base design), listed alongside other memory-plugin entries
   in the same sweep result set (see Sources). Problem: a session's
   decisions/lessons get written down only when a human remembers to do
   it afterward. How: hooks fire at session boundaries and a compilation
   step turns raw session content into structured, cross-referenced
   knowledge articles ahead of any manual authoring step.

2. **Korni22/claude-adr** (listed as `ruflo-adr` on claudeskills.info
   with a 65.4K star count on that listing page; mirrored at
   zircote/adr) — an ADR-lifecycle plugin spanning create, index,
   supersede, and link-to-code, per the claudeskills.info
   documentation-plugin directory page cited above (see Sources).
   Problem: index update and supersession linking sit as separate manual
   steps beyond writing the ADR body, and skipping either leaves the
   record set out of sync. How: one plugin action carries out create +
   index-update + supersede-link together, so the index and the
   reciprocal link move alongside the new/superseding entry in the same
   action.

3. **terrylica/cc-skills** — a skills marketplace whose category list
   names "ADR-driven development" as a distinct skill group, alongside
   DevOps/data/productivity groups, appearing in the same result set as
   the broader toolkit/awesome-list pages (see Sources). Problem: a
   marketplace mixing capture-time skills (draft an ADR) with audit-time
   skills (check ADR compliance) in one undifferentiated list leaves the
   applicable phase unclear. How: skills carry an explicit lifecycle-
   phase tag/grouping, so an author or a gate can pick the phase-
   appropriate skill instead of scanning the whole list.

## Gap line

canonical: docs/issue-1199/proposals/2026-08-13-knowledge-management-tool-landscape.md
(this repo, read this turn) — that proposal's five surveyed entries
(Obsidian, Joel Parker Henderson's ADR repo, Backstage TechDocs, Dendron,
Notion) are general PKM/IDP/docs products, not Claude Code plugins or
skills. Per the 2026-08-14 amendment, a fold-in whose surveyed sources
are domain tools alone does not satisfy the amended acceptance check.
This round adds 3 plugin/skill entries to the handbook, additive to the
prior 5, not a replacement of them.

- claude-memory-compiler's automatic session-boundary capture lines up
  with a gap the prior round left open: today `reused_by` is appended
  only when a later phase-1 research round happens to cite an entry as
  upstream basis by hand — nothing prompts that citation at the point it
  applies.
- claude-adr's single-action create+index+supersede-link lines up with a
  residual risk in the existing "link both directions in the same
  change" supersession rule: the rule states the requirement in prose but
  nothing pairs the two edits (old entry's `superseded_by`, new entry's
  `supersedes`) into one checked line.
- cc-skills' phase-tagged skill grouping reinforces the existing
  phase-1/phase-2 plugin composition table with a matching self-check
  label, giving the phase separation the same visibility cc-skills'
  tagging gives it.

## Adopt / skip

Adopt: a phase-2 self-check line prompting `reused_by` citation at the
point a later record names an entry as upstream basis; a single
self-check line pairing the two supersession-link edits instead of
treating them as independently satisfiable; an explicit phase label on
the existing self-check items. Skip: the three plugins' actual runtime
(hooks, a compilation step, marketplace tagging UI) — this rulebook
borrows the design moves, not the tools.

## Sources

```
https://github.com/coleam00/claude-memory-compiler
https://github.com/Korni22/claude-adr
https://github.com/zircote/adr
https://claudeskills.info/plugins/
https://claudeskills.info/plugins/category/documentation/page/4/
https://github.com/terrylica/cc-skills
```

## kind / loop_state

kind: report
loop_state: phase-1-scouted
