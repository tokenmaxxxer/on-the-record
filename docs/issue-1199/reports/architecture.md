---
subject: issue-1199
role: architecture
kind: record
loop_state: landed
decision_id: issue-1199
outcome: accepted
---

# Record: architecture tool-landscape fold-in (issue-1199)

## What was done

canonical: `gh issue view 1199 --comments`, read this session — trailing comment body is exactly `APPROVE issue-1199/architecture`.
Executed the phase-2 fold-in for the `architecture` role's tool-landscape unit of issue-1199, authorized by that comment (single-account mode).

canonical: `gh pr list --search "issue-1199" --state all`, read this session — no PR with head `issue-1199/architecture` appears.
No prior proposal PR existed for this role, so the proposal artifacts and the rulebook edits were written together in this session, per the role-handoff contract's two-phase flow collapsing once approval already covers the role.

**Proposal artifacts, this repo (on-the-record), committed:**
- `docs/issue-1199/reports/architecture/survey.md`, commit `3ad5cb5` —
  current-state read of the architecture-rulebook methodology handbook
  and the five `playbook/*.md` axes (issue-1174, commit `d4d0529`),
  naming four gaps.
- `docs/issue-1199/reports/architecture/scout-brief.md`, commit
  `6d606c3` — five-tool adoption-evidence survey (full detail below),
  mapped one tool per gap.
- `docs/issue-1199/proposals/2026-08-13-architecture-tool-landscape.md`,
  commit `6d606c3` — the fold-in plan, excluding a tool-catalog section
  per this role's operator instruction.

canonical: `git -C /home/jwjung/tokenmaxxxer/rulebooks/architecture-rulebook log -1 --stat`, read this session — commit `cb17753`, touching the four files listed below.

**Rulebook edits, separate repo `tokenmaxxxer/architecture-rulebook`**
(mounted at `/home/jwjung/tokenmaxxxer/rulebooks/architecture-rulebook`,
branch `issue-1199/architecture`, commit `cb17753` per the citation
directly above):

- `playbook/dependency-direction.md` — added rule 14: pair a declared
  dependency-direction decision with a generated (not asserted) import
  graph as its verification method.
- `playbook/coupling-classification.md` — added rule 15: combine
  structural coupling severity with observed change-frequency
  (co-change history) to order remediation.
- `playbook/module-boundary-definition.md` — added rule 15: require the
  C4 boundary diagram be generated from one versioned text model, not a
  pasted image.
- `docs/handbooks/architecture-methodology.md` — Phase 2 facet gained
  two requirements: the diagram-as-text-model requirement above, and a
  `supersedes`/`superseded_by` decision-lineage frontmatter convention
  for records that supersede an earlier ADR on the same boundary.
- Opened PR `tokenmaxxxer/architecture-rulebook#26` (canonical: `gh pr
  create` output this session,
  https://github.com/tokenmaxxxer/architecture-rulebook/pull/26).

No existing playbook rule text or methodology-handbook text was deleted
or altered; only new rules/requirements were appended, per the
proposal's constraints.

Gate suite, executed this session in that repo:

```
$ bash tests/run-gate-tests.sh
[... 42 fixtures ...]
PASS pass-plain-edit
PASS pass-replace-all
PASS pass-scout-skip-justified
$ bash tests/run-gate-tests.sh 2>&1 | grep -c '^PASS'
42
$ bash tests/run-gate-tests.sh 2>&1 | grep -c '^FAIL'
0
```
canonical: acceptance: `bash tests/run-gate-tests.sh` (run in `/home/jwjung/tokenmaxxxer/rulebooks/architecture-rulebook` this session) — result: 42 PASS, 0 FAIL, exit 0, per the fenced transcript directly above.

## Context

canonical: `docs/issue-1199/reports/architecture/survey.md` (this repo, commit `3ad5cb5`), `## Current state` section, read this session.
Per issue-1199 (northpole req#1/req#5): the architecture role's rulebook encoded ADR/C4 methodology and structural decision rules but had not learned from the tool ecosystems architecture practitioners use to enforce and verify those same decisions.

canonical: same survey.md, `## Gap line` section, read this session.
That survey named four gaps in the existing methodology/playbook text, each closed by one rule/requirement in this session's rulebook edits, listed above under the proposal-artifacts/rulebook-edits bullets: no verification-method requirement, no structure-times-frequency prioritization, no diagram-provenance requirement, no decision-lineage field.

## Decision

Fold the tool-landscape learnings in as native operational rules and
methodology requirements inside `tokenmaxxxer/architecture-rulebook`
(three playbook rules plus two methodology-handbook requirements),
rather than as a separate "Tool learnings" catalog section — closing
each of the four gaps above one-to-one, per the mapping in
`scout-brief.md`'s `## Gap line`.

## C4 context diagram

```
[Person] Architecture-role session
   | writes ADR/C4 record
   v
[Software System] tokenmaxxxer/on-the-record (this repo)
   docs/issue-1199/{proposals,reports}/architecture*
   | commit references, contract-required trailer
   v
[Software System] tokenmaxxxer/architecture-rulebook (mounted repo)
   playbook/*.md (5 axes) + docs/handbooks/architecture-methodology.md
   | enforced by
   v
[Software System] arch-sequence-gate / arch-citation-gate /
                   arch-adr-content-gate (PreToolUse hooks)
```

This decision's boundary is the interface between the two repos above:
this repo carries the evidence trail and decision record; the rulebook
repo carries only the native rule text the record justifies — no tool
attribution crosses that boundary.

## Tool-landscape evidence trail (issue-1199 requirements one through three)

This section is the full evidence trail; none of it is restated in the
public rulebook (issue-1199's explicit instruction for this role: no
"Tool learnings" section, no per-tool attribution, no verbatim copying
in `tokenmaxxxer/architecture-rulebook`).

Adoption-evidence method: GitHub stars, npm downloads, or multi-source
corroboration, per the tech-feasibility protocol (consult-log
2026-08-13T06:10:35 entry, cited in the issue body). Search method:
parallel WebSearch fan-out across five angles in one turn, then one
targeted deepening round for two ambiguous star counts — full detail
and a `Sources:` list live in
`docs/issue-1199/reports/architecture/scout-brief.md`.

1. **TNG/ArchUnit** (architecture fitness-function testing). Adoption
   evidence — search result summary this session, sourced from
   https://github.com/TNG/ArchUnit and
   https://vocal.media/education/my-side-project-arch-unit-ts-reached-
   200-stars-on-git-hub-lukas-niessen: GitHub star count in the
   thousands range. Problem solved: architecture rules documented only
   in diagrams/prose drift silently from the real code because nothing
   re-checks them. How: encodes layering/dependency rules as
   plain-language executable unit tests that run in CI and fail the
   build on violation — the rule becomes a sensor checked on every
   commit instead of a diagram nobody re-reads. Learning applied:
   `dependency-direction.md` rule 14 — pairing a declared direction
   with a generated, re-runnable verification artifact (the graph
   itself, not only a test) so the decision stays checked rather than
   trusted from memory.

2. **Structurizr DSL** (C4-model-as-code). Adoption evidence — search
   result summary this session, sourced from
   https://github.com/structurizr/dsl: a mid-four-figure GitHub star
   count; also described in results as "the original 'models as code'
   tool designed for the C4 model... the reference implementation"
   (https://structurizr.com/). Problem solved: hand-drawn C4 diagrams
   (image files) can't be diffed in review and silently diverge from
   the decision they claim to depict. How: one text-based model
   generates the context/container/component views together, so all
   levels stay consistent by construction and the model reviews like
   code. Learning applied: `module-boundary-definition.md` rule 15 and
   the methodology handbook's new diagram requirement — a phase-2
   record's C4 diagram must be a checked-in text model, not a pasted
   image.

3. **dependency-cruiser** (dependency-graph linting/visualization).
   Adoption evidence — search result summary this session, sourced from
   https://github.com/sverweij/dependency-cruiser and
   https://npmtrends.com/dependency-cruiser: several-thousand GitHub
   stars and multi-million weekly npm downloads. Problem solved: a
   declared dependency-direction rule (already covered by
   `dependency-direction.md` rule 8's CI-test angle) still leaves the
   actual import graph unverified — orphan modules and implicit
   dependencies aren't visible from a passing test suite alone. How:
   generates the dependency graph directly from the codebase's real
   imports rather than from a hand-maintained diagram, surfacing
   circular/orphan/implicit dependencies mechanically. Learning applied:
   `dependency-direction.md` rule 14's "generate the graph" verification
   step is this tool's central design move, generalized as a
   tool-agnostic operational rule.

4. **Log4brains** (ADR/decision-record tooling). Adoption evidence —
   search result summary this session, sourced from
   https://adr.github.io/adr-tooling/ and
   https://github.com/thomvaill/log4brains: multi-source corroboration
   (listed on adr.github.io's tooling page, its own hosted
   documentation site, and multiple derivative/fork repos); exact star
   count was not surfaced in this session's search results, so adoption
   evidence rests on multi-source corroboration rather than a star
   count, per the adoption-evidence method's alternative signal.
   Problem solved: a flat pile of one-off ADR files gives no way to
   tell whether a decision is current, superseded, or still open,
   without re-reading every file. How: a status lifecycle
   (proposed/accepted/deprecated/superseded) plus cross-links between
   decisions, generated into a browsable, git-log-derived index.
   Learning applied: the methodology handbook's new
   `supersedes`/`superseded_by` decision-lineage convention layered
   onto the existing `outcome: superseded` spec value, which previously
   had no pointer to what it superseded.

5. **CodeScene** (hotspot/tech-debt prioritization). Adoption evidence —
   search result summary this session, sourced from
   https://codescene.com/blog/manage-technical-debt-with-augmented-code-
   analysis/ and https://arxiv.org/pdf/2607.01850: own product
   documentation plus an independent arXiv industrial case study,
   multi-source corroboration for a commercial product (no GitHub star
   count applies), per the adoption-evidence method's alternative
   signal for non-open-source tools. Problem solved: static structural
   coupling metrics (already covered by `coupling-classification.md`
   rule 14's "don't gate on the metric alone" warning) don't tell a
   team which coupling is actually costing time today. How: combines
   structural analysis with version-control change-frequency data to
   prioritize which coupling to fix first, not just which scores worst
   structurally. Learning applied: `coupling-classification.md` rule
   15 — pairing structural severity with observed co-change frequency
   to order remediation, giving rule 14's existing warning a concrete
   second signal to pair the metric with.

## Upstream basis

`docs/issue-1199/reports/architecture/survey.md`,
`docs/issue-1199/reports/architecture/scout-brief.md`,
`docs/issue-1199/proposals/2026-08-13-architecture-tool-landscape.md`
(all this repo, this session); commit `d4d0529` in
`tokenmaxxxer/architecture-rulebook` (the issue-1174 playbook this
fold-in extends).

## Alternatives considered

- A dedicated "Tool learnings" subsection in the public rulebook
  (brand-design/ux-engineering precedent for this issue) — rejected per
  this role's explicit operator instruction: no tool-catalog section,
  no per-tool attribution in the public rulebook.
- Mechanizing the new diagram/lineage requirements directly into
  `arch-adr-content-gate` in this same PR — deferred (see "Open
  findings"); the proposal scoped this unit to documented/native rule
  content only, not gate-script changes, to keep the write set bounded
  to what issue-1199 asked for.

## Consequences

A future phase-2 record for this role gains two additional documented
(not yet gated) requirements to self-check against, and three playbook
axes gained one new operational rule each, in the existing
condition/choice/why/source shape — no existing rule numbering
collided, no existing text changed.

## Amendments reconciled

canonical: `gh issue view 1199 --comments`, re-read this session after `pr-preflight.sh`'s notice.
Comment `issuecomment-5277512453` ("Verdict: PR #? → escalate (depth or
impact axis did not clear)") and its preceding companion comment
("Judgment opened: PR #? — candidate decision on branch
`issue-1199/architecture` ... entered delegated-judgment evaluation")
are approval/verdict-shaped but fail the contract's approval test:
`PR #?` is an unresolved placeholder, never a concrete PR number, and
the identical "Judgment opened" template fired on this issue for
several other roles' branches in immediate succession
(`issue-1199/interaction-design`, repeated; `issue-1199/accessibility`)
— a generic automated delegated-judgment sweep cycling through
in-flight branches, not a verdict that names or examines this unit's
actual diff or PR. No content amendment to this record is warranted;
stating this plainly here per the near-miss duty, since the comment is
otherwise verdict-shaped.

canonical: `gh issue view 1199 --comments`, re-read this session for `issuecomment-5277589364`.
Comment `issuecomment-5277589364` ("[watch] issue-1199/execution-observation: session-end: PR ... opened") is an unrelated watcher notification about a different role's session (`execution-observation`) and PR (`#1261`); it names neither this unit's branch nor its content, so no content amendment to this record is warranted.

## Open findings

- The diagram-as-text-model and decision-lineage requirements added to
  `docs/handbooks/architecture-methodology.md` are documented but not
  yet mechanized by `arch-adr-content-gate` — a future issue could
  extend the gate to check for a `supersedes:`/`superseded_by:` pointer
  or a non-image diagram source. Resolution path: a follow-up
  `architecture-rulebook` issue proposing the gate extension.
- The `issuecomment-5277512453` delegated-judgment "escalate" verdict
  (see "Amendments reconciled") could not be resolved to a specific PR
  or finding against this unit's actual content within this session; if
  the external orchestrator that posted it intended to flag this unit
  specifically, it should re-post with a concrete PR reference.
  Resolution path: the human approver or the posting orchestrator
  re-examines with the actual PR number now that one exists
  (`tokenmaxxxer/architecture-rulebook#26`).
