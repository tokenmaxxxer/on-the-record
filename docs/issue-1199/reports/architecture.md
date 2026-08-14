---
subject: issue-1199
role: architecture
kind: record
loop_state: landed
decision_id: issue-1199
outcome: accepted
---

# Record: architecture tool-landscape fold-in (issue-1199)

## 2026-08-14 rework amendment (Claude Code plugin ecosystem)

canonical: issue-1199 body, "issue-1199 tool-landscape REWORK (2026-08-14 amendment)" section, read this session.
The operator's 2026-08-14 amendment supersedes this record's original
survey target: the required survey basis is the Claude Code plugin/skill
ecosystem, not general domain architecture tools (ArchUnit, Structurizr,
dependency-cruiser, log4brains) — the prior survey below is
domain-tool-basis and fails the amended acceptance on its own.

**What changed this session:** reworked the evidence trail only —
`playbook/dependency-direction.md` rule 14, `playbook/coupling-
classification.md` rule 15, and `playbook/module-boundary-definition.md`
rule 15 keep the same native design moves (generated import graph over
asserted rule; structural severity paired with an observed-impact
signal; C4 diagram as one versioned text model), each now sourced to a
Claude Code plugin/skill instead of a general domain tool. No rule text,
numbering, or "why" reasoning changed beyond the citation swap; the
methodology handbook's two Phase 2 requirements (diagram-as-text-model,
decision-lineage) are unchanged.
canonical: `docs/issue-1199/reports/architecture/scout-brief.md`,
"Category-level check" paragraph in its "## 2026-08-14 rework addendum"
section, read/written this session — their design moves already match
what the newly surveyed plugins independently confirm.

derived: git -C /home/jwjung/tokenmaxxxer/rulebooks/architecture-rulebook log --oneline -1 issue-1199/plugin-landscape-rework
```
91b6e0b issue-1199: rework tool-landscape evidence to Claude Code plugin ecosystem
```
canonical: git -C /home/jwjung/tokenmaxxxer/rulebooks/architecture-rulebook diff --stat main issue-1199/plugin-landscape-rework — read this session, confirms 3 files changed (the same three playbook rule files from the original fold-in), 7 insertions(+), 6 deletions(-), no other paths touched.

Opened `tokenmaxxxer/architecture-rulebook#27`
(https://github.com/tokenmaxxxer/architecture-rulebook/pull/27) against
that repo's `main`, per contract v3 s8 (session opens, does not merge).

Full rework survey: `docs/issue-1199/reports/architecture/scout-brief.md`,
"## 2026-08-14 rework addendum" section (this repo, this session).

code_under_review (rework):
- playbook/dependency-direction.md (tokenmaxxxer/architecture-rulebook)
- playbook/coupling-classification.md (tokenmaxxxer/architecture-rulebook)
- playbook/module-boundary-definition.md (tokenmaxxxer/architecture-rulebook)
- docs/issue-1199/reports/architecture/scout-brief.md (this repo)

## Rework evidence trail (Claude Code plugin ecosystem, 2026-08-14 amendment)

1. **blueraai `claude-code-graph`** — adoption evidence: marketplace
   listing plus multi-source cross-listing (WebSearch this session,
   https://lobehub.com/skills/blueraai-bluera-base-claude-code-graph);
   exact star count not surfaced, so evidence rests on the
   adoption-evidence method's alternative multi-source signal. Problem
   solved: same as the earlier dependency-cruiser entry below —
   a declared dependency-direction rule stays unverified without a
   generated view of the real import graph. How: parses a plugin's
   manifest/source into a directed dependency graph (DOT/Mermaid/JSON)
   with cycle detection and orphan/unused-module identification.
   Learning applied: unchanged design move, `dependency-direction.md`
   rule 14 — now sourced to this Claude Code-native skill instead of
   the general-purpose npm CLI tool.
2. **`Egonex-AI/Understand-Anything`** — 79.2k GitHub stars (WebFetch
   this session, https://github.com/Egonex-AI/Understand-Anything).
   Problem solved: same as the earlier CodeScene entry below —
   static structural coupling severity doesn't say which coupling is
   actually costing the team time today. How: builds an interactive
   knowledge graph across major coding agents and includes a "Diff
   Impact Analysis" feature showing which parts of the system a change
   ripples into before commit. Learning applied: unchanged design move,
   `coupling-classification.md` rule 15 — pairing structural severity
   with an observed-impact/ripple signal, now sourced to this
   Claude Code-native, high-adoption plugin.
3. **`cheriftj/c4-model-skill`** — 34 GitHub stars (WebFetch this
   session, https://github.com/cheriftj/c4-model-skill), corroborated
   by a second independently-maintained C4 skill
   (`bitsmuggler/c4-skill`) and a dedicated architecture-skills blog
   listing (https://skills.thicket.sh/blog/best-claude-code-skills-for-architects).
   Problem solved: same as the earlier Structurizr entry below —
   a hand-drawn C4 diagram (image file) can't be diffed in review.
   How: interactive Claude Code skill generating C4 diagrams
   (Mermaid/Structurizr DSL/PlantUML) from one text model. Learning
   applied: unchanged design move, `module-boundary-definition.md` rule
   15 and the methodology handbook's diagram requirement — now sourced
   to this Claude Code-native skill.
4. **`gauravs19/enterprise-architecture-skill`** — 7 GitHub stars
   (WebFetch this session,
   https://github.com/gauravs19/enterprise-architecture-skill),
   corroborated by the same architecture-skills blog listing as #3.
   Problem solved: same as the earlier Log4brains entry below — a
   flat set of decision records gives no way to tell which supersedes
   which. How: unifies C4/ArchiMate/TOGAF/arc42+ADR with a built-in
   linter that flags "accepted ADRs not linked from any doc." Learning
   applied: secondary confirming context for the methodology handbook's
   existing `supersedes`/`superseded_by` decision-lineage requirement —
   no rule change, since a Claude Code-native skill independently
   assumes the same lineage-tracking need.

canonical: `docs/issue-1199/reports/architecture/scout-brief.md`,
"## Superseded survey" heading (this repo, this session). The original
five-tool domain-basis evidence trail below is kept for record
continuity (which gap each originally closed); the trail immediately
above this line is the acceptance-qualifying basis per the 2026-08-14
amendment.

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

## Superseded evidence trail (pre-2026-08-14, domain-tool basis)

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

canonical: `gh issue view 1199 --comments`, re-read this session for `issuecomment-5277592420`.
Comment `issuecomment-5277592420` ("Verdict: PR #? → escalate (depth or impact axis did not clear)") is another instance of the same generic, unresolved-placeholder "Verdict: PR #?" template already addressed above — it carries no PR number or branch name distinguishing it from the earlier instance already reconciled, so it is treated the same way: approval/verdict-shaped but not a verdict on this unit's actual diff; no content amendment warranted.

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/comments/5277596197`, read this session.
Comment `issuecomment-5277596197` ("Verdict: PR #? → escalate (depth or impact axis did not clear)") is a fourth automated delegated-judgment verdict from the same pre-PR watcher run, posted after this session started, with no amendment content of its own — no action taken on this record or the rulebook PR. This matches the pr-preflight comment-race already logged against this same watcher pattern in prior issue-1199/issue-1174 records (e.g. commit `005e2c6`, `9b6a346`): each commit reconciling one watcher comment races a fresh comment from that same watcher run. Per that precedent, this session stops retrying `gh pr create` after this reconciliation and relies on on-the-record's outside relay to open the PR from the pushed branch (`issue-1199/architecture`, commit `d9e3386` and this commit).

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
