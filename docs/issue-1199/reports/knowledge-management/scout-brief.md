# Scout brief: knowledge-management tool landscape (issue-1199)

Mode: parallel WebSearch fan-out, 4 angles in one turn (PKM apps head-to-
head; ADR tooling; internal-developer-portal docs platforms; hierarchical/
Zettelkasten note tools). One deepening round skipped — the sweep already
produced concrete adoption evidence and clear design moves per candidate,
and a second round would not change which five tools get picked or what
they teach (saturation reached at stage 1; total 1 stage, well under the
5-stage/3min budget).

## Candidates (adoption evidence, problem, how)

1. **Obsidian** — PKM market: about 8 percent share, but the top choice
   among power users/developers/researchers, with a large community
   plugin ecosystem (multi-source: tech-insider.org, guptadeepak.com 2026
   comparisons — see Sources). Problem: a knowledge base locked in a
   vendor's database becomes unsearchable/unlinkable once the tool is
   abandoned. How: plain local Markdown files as the source of truth,
   bidirectional links resolved at read-time (not stored per-note), graph
   view built from link scan, not manual index maintenance.

2. **Joel Parker Henderson's `architecture-decision-record`** — the
   most-starred ADR resource on GitHub (source: adr.github.io tooling
   page / scribelet.app ADR-examples writeup, cross-checked — see
   Sources). Problem: architectural rationale gets lost or silently
   rewritten after the fact. How: Nygard-format ADRs are numbered,
   sequential, and effectively immutable once accepted — a later change
   is a NEW numbered record that supersedes the old one, never an edit to
   it.

3. **Backstage TechDocs** — widely adopted at large engineering orgs;
   named adopters include Netflix, LinkedIn, American Airlines, Spotify
   (source: javacodegeeks Backstage-IDP piece, dev.to/roadie Backstage-
   adoption piece — see Sources). Problem: docs drift from the code/
   service they describe because nothing ties a doc to its owning
   service. How: catalog metadata co-located with the doc binds it to a
   registered service/owner in the catalog, so the catalog UI can group
   and surface docs by owner, not just by folder.

4. **Dendron** — an actively-starred VSCode note-taking extension (source:
   stackshare.io Dendron comparison pages — see Sources). Problem: a flat
   or freeform note collection stops being navigable past a few hundred
   entries. How: dot-hierarchy note IDs (`domain.subdomain.note`) double
   as both a filing scheme and a lookup-by-prefix query, plus per-
   hierarchy-level schema templates.

5. **Notion** — the largest team-docs product by market share, powering a
   majority of Fortune 500 teams' team docs per Capterra 2026 data
   (source: tech-insider.org, guptadeepak.com — see Sources). Problem:
   the same underlying data (e.g. a set of entries) needs different
   groupings for different readers (chronological vs. by-owner vs. by-
   status) and hand-maintaining separate lists drifts. How: one database
   of typed properties, multiple saved views (table/board/timeline)
   filtered/grouped from the same rows — never a second copy of the data.

## Gap line (survey gaps this maps against)

- Obsidian's link-scan-not-maintained-index closes the survey's "no
  backlink/reuse-discovery mechanism" gap.
- ADR immutability-by-supersession closes "no immutability rule for a
  landed pattern's body" gap.
- Backstage catalog-info ownership binding closes "no ownership/
  cross-role applicability field" gap.
- Dendron dot-hierarchy closes "no structured slug/naming discipline"
  gap.
- Notion multi-view-over-one-source closes "index is single-view" gap.

All five gaps from the current-state survey have a matching tool; nothing
surveyed is adopted for a gap the handbook doesn't actually have.

## Adopt / skip

Adopt: link-scan discovery, supersession-only immutability, ownership
metadata field, hierarchical slug prefix, second index view. Skip:
full graph-view UI, vendor database/proprietary storage, and adopting any
tool's full plugin/product surface — this rulebook borrows design moves,
not the products.

## Sources

```
https://tech-insider.org/notion-vs-obsidian-2026/
https://guptadeepak.com/tools/top-10-note-taking-pkm-apps-2026/
https://adr.github.io/adr-tooling/
https://scribelet.app/blog/architecture-decision-record-examples
https://www.javacodegeeks.com/2025/06/building-internal-developer-platforms-with-backstage-io.html
https://dev.to/roadie/adopting-backstage-documentation-and-support-5gei
https://stackshare.io/dendron/vs/vim-plug
```
