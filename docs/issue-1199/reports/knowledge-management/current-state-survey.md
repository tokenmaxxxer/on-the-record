# Current-state survey: knowledge-management rulebook (issue-1199)

derived: cat /home/jwjung/tokenmaxxxer/rulebooks/knowledge-management-rulebook/docs/handbooks/knowledge-management.md
canonical: /home/jwjung/tokenmaxxxer/rulebooks/knowledge-management-rulebook/docs/handbooks/knowledge-management.md (read in full this session)

The rulebook (`tokenmaxxxer/knowledge-management-rulebook`, mounted at
`/home/jwjung/tokenmaxxxer/rulebooks/knowledge-management-rulebook`) has one
handbook file (path above) covering: phase-1 ADR-shaped proposal norm;
phase-2 templates for a pattern-library entry (`<rulebook>/docs/patterns/
<slug>.md`, five body sections — Context/Problem/Why/Solution/Consequences
— plus front matter `title`/`keywords`/`source_issues`/`supersedes`/
`superseded_by`/`article_id`/`capture_point`/`reuse_status`); a cross-issue
index (`<rulebook>/docs/patterns/index.md`, one table row per entry); a
supersession-note pairing rule; a fixed `loop_state` vocabulary; and a
phase-2 self-check.

Gaps found below (canonical: the handbook text at the path above, same
source already cited).

- **No backlink/reuse-discovery mechanism.** `source_issues` records where a
  pattern came from, but nothing records which later issues consulted or
  applied it — reuse is invisible until a human greps.
- **No immutability rule for a landed pattern's body.** Supersession links
  both directions in front matter, but nothing stops silently editing a
  landed entry's Context/Problem/Solution text in place instead of
  superseding it — drift is possible with no signal.
- **No ownership/cross-role applicability field.** A pattern entry has no
  field naming which OTHER roles' work it is relevant to, so a role
  starting phase-1 elsewhere has no way to discover an applicable KM
  pattern without a manual search.
- **No structured slug/naming discipline.** The slug is freeform; no
  hierarchy or prefix convention exists, so the index can only be scanned
  linearly, not filtered by domain prefix.
- **Index is single-view.** One table, one grouping — no second retrieval
  axis (e.g. by keyword/theme) despite `keywords` already being collected
  in front matter.

These five gaps are the aim points for the tool-landscape scout sweep below.
