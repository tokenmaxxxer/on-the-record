---
subject: issue-1199
role: brand-design
kind: record
loop_state: landed
---

# Record: brand-design tool-landscape fold-in (issue-1199)

## What was done
Executed the phase-2 fold-in approved by the `APPROVE issue-1199/brand-design`
comment on this issue (single-account mode; canonical: `gh issue view
1199 --comments`, read this session — trailing comment body is exactly
`APPROVE issue-1199/brand-design`). Worked directly in the separate
rulebook repo (tokenmaxxxer/brand-design-rulebook, mounted at
/home/jwjung/tokenmaxxxer/rulebooks/brand-design-rulebook), on branch
issue-1199/brand-design:

- Added a bounded "Tool learnings (issue-1199)" section to the
  rulebook repo's methodology handbook, at path
  docs/handbooks/brand-design/methodology.md relative to that repo's
  root (not this working tree — the path does not resolve here by
  design): five surveyed tools (diagram-design, Style Dictionary,
  Tokens Studio for Figma, Stark, zeroheight), each carrying {tool,
  adoption evidence, problem, how, learning→named upgrade to an
  existing phase-2 checklist item}, per the proposal.
- Added a one-sentence pointer to that section in each of the three
  affected plugin READMEs in that same rulebook repo
  (brand-design-guide-and-spec, brand-design-wcag-consistency,
  brand-design-system-handoff), mirroring the issue-20
  README-mirrors-handbook precedent.
- No existing handbook or README text deleted; no gate logic touched
  (brand-design-kapferer-scope-guard and the shape-gate question are
  out of scope per the proposal).
- Committed in the rulebook repo (commit
  0d354fda181d6f0296538b118bff84f3f69cce23, subject: issue-1199;
  canonical: `git -C /home/jwjung/tokenmaxxxer/rulebooks/brand-design-rulebook
  log -1 --stat`, read this session), pushed to
  origin/issue-1199/brand-design, and opened a PR (canonical: `gh pr
  create` output this session — https://github.com/tokenmaxxxer/brand-design-rulebook/pull/27).

## Why
Per issue-1199 (northpole req#1/req#5): the brand-design role's
rulebook had encoded methodology but not learnings from the tool
ecosystems brand-design practitioners actually use. The five entries
close the gap the phase-1 scout brief identified — fixed type enum,
per-pairing granularity, named downstream consumer, distinct
source-of-truth path — none of which the prior checklist wording
asked for.

## Upstream basis
docs/issue-1199/proposals/2026-08-13-brand-design-tool-landscape.md

## Open findings
None.
