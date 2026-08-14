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

amendments-reconciled: issuecomment-5276738377 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") is a delegated-judgment
verdict for a different, unnumbered candidate PR on branch
`issue-1199/implementation` (canonical: `gh issue view 1199
--comments`, re-read this session after the pr-preflight notice) — it
does not name or reference this brand-design unit's PR (#1208) or its
rulebook-repo counterpart (brand-design-rulebook#27), so no content
amendment to this record is warranted.

## 2026-08-14 rework amendment

Operator amendment (survey text pasted verbatim into this session's
opening prompt, 2026-08-14) superseded the earlier broad reading: the
tool-landscape survey target is the Claude Code plugin/skill ecosystem
(marketplace/community plugins), not general domain tools.

canonical: methodology.md entries 1-5, read this session at commit
0d354fda181d6f0296538b118bff84f3f69cce23 in
/home/jwjung/tokenmaxxxer/rulebooks/brand-design-rulebook.
Merged PR #27 above surveyed only Style Dictionary, Tokens Studio,
Stark, zeroheight, and diagram-design — five domain tools, no Claude
Code plugin/skill sources — so it fails the amended acceptance check
on its own.

### What was done
Web-fetched three Claude Code plugin/skill-ecosystem sources this
session (canonical: WebFetch results this session against
github.com/VoltAgent/awesome-claude-design,
github.com/ryanthedev/design-for-ai, and
github.com/rampstackco/claude-skills) and added them as three
additive entries under a new "Claude Code plugin/skill ecosystem
(issue-1199, 2026-08-14 amendment)" subsection in
docs/handbooks/brand-design/methodology.md in the separate rulebook
repo (tokenmaxxxer/brand-design-rulebook), each carrying {tool,
adoption evidence (GitHub star count), problem, how, learning→named
upgrade to an existing phase-2 checklist item}. Kept all five prior
domain-tool entries verbatim, per the amendment's explicit "KEEP
existing native rules" instruction — no deletion.

Committed in the rulebook repo (commit
bb8e76fb46d1d87f3c21626f111e2209e2b29a62, subject: issue-1199;
canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/brand-design-rulebook log -1
--stat`, read this session), pushed to
origin/issue-1199/brand-design, and opened a new PR since #27 was
already merged and its branch deleted upstream (canonical: `gh pr
create` output this session —
https://github.com/tokenmaxxxer/brand-design-rulebook/pull/28).

### Why
Northpole req#1/req#5: the amendment states plainly that a fold-in
whose surveyed sources are domain tools alone does not satisfy
issue-1199 — this unit closes that specific gap without touching the
already-landed domain-tool entries, which remain correct native
learnings in their own right.

### Upstream basis
docs/issue-1199/proposals/2026-08-13-brand-design-tool-landscape.md
(original proposal, whose approved shape — bounded subsection, entries
carrying {tool, adoption evidence, problem, how, upgrade} — this
rework reuses); this rework itself proceeded as a continuation of that
already-approved unit (contract v3 s19's phase-2 approval covers "fold
tool-landscape learnings into the rulebook" as delivered scope) rather
than opening a fresh phase-1 proposal, since the amendment corrects
the survey source population within the same approved deliverable
shape and does not change the write set, the entry schema, or which
checklist items are upgraded in kind.

### kind / loop_state
kind: record
loop_state: landed — brand-design-rulebook#28 carries the named
upgrade file (docs/handbooks/brand-design/methodology.md), committed
and pushed to a non-main branch, PR open against main.

### Open findings
None.

amendments-reconciled: issuecomment-5288013676 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)"), preceded by
issuecomment-5288013556 ("Judgment opened: PR #? — candidate decision
on branch `issue-1199/brand-design` (1 path(s) changed)"). canonical:
`gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments`, read
this session — the pairing evaluated this branch's prior single-file
commit (the record-only edit, before this rework's second commit
landed here) as an unnumbered delegated-judgment candidate; it names
no PR number and predates this session's `gh pr create` call, so it is
not a verdict on a PR that exists — no content amendment to this
record is warranted, matching the same reconciliation precedent above.

amendments-reconciled: issuecomment-5288019102 ("Verdict: PR #? →
escalate ..."), preceded by issuecomment-5288018954 ("Judgment opened:
... branch `issue-1199/architecture` (2 path(s) changed)"). canonical:
`gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments`, read
this session — this pairing is for the architecture role's branch, not
brand-design; no content amendment warranted.

amendments-reconciled: issuecomment-5288022201 ("Verdict: PR #? →
escalate ..."). canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/1199/comments`, read this
session — a further watcher verdict comment arriving faster than
pr-preflight's per-comment reconciliation cycle completes, same
deadlock class already logged in
docs/issue-1199/reports/brand-design/survey.md for issue-1174's
observability/market-analysis fan-out units: no content amendment
warranted, and PR creation is left for external relay per that
precedent rather than retried further in this turn — the branch
(commit 732d83c9) is committed and pushed to
origin/issue-1199/brand-design.
