# knowledge-management — issue #1174 operational playbook: evidence trail

## What was done

Authored `playbook/` in the `knowledge-management-rulebook` checkout
(local path: `~/.tokenmaxxxer/work/knowledge-management-rulebook-issue-24-implementation/knowledge-management`,
remote: `tokenmaxxxer/knowledge-management-rulebook`, branch
`issue-1174/operational-playbook`) with 5 decision-axis files, each
condition→choice→source rules per the approved
docs/issue-1174/proposals/operational-playbook-program.md (c)/(d) spec:

- `playbook/pattern-extraction.md` — when a retrospective finding is
  pattern-shaped vs. stays a one-off issue note; 11 rules (2 REMOVAL).
- `playbook/taxonomy-tagging.md` — controlled-vocabulary/tagging rules for
  the pattern index; 11 rules (2 REMOVAL).
- `playbook/supersession-lifecycle.md` — status model
  (proposed/accepted/deprecated/superseded), never-delete rule, edit-vs-
  supersede test; 11 rules (2 REMOVAL).
- `playbook/structure-findability.md` — Diátaxis-informed filing/naming
  for retrieval (including RAG-retrieval implications); 11 rules
  (2 REMOVAL).
- `playbook/curation-pruning.md` — audit cadence, curation-not-deletion
  default, near-duplicate merge; 11 rules (2 REMOVAL).

Each file carries `rule_count_floor: 10` / `axis:` front matter (moderate
tier, 5 axes → N_min = max(8, 5*2) = 10, per proposal (a); files ship at
11 each, above floor). Cross-axis `[[axis-name]]` links follow the
proposal's own linking convention. Added `README.md` to the rulebook
checkout (none existed) with a Layout section pointing at `playbook/`,
mirroring the api-design-rulebook/technical-writing-rulebook convention
surveyed this session.

Pushed the branch and opened
`tokenmaxxxer/knowledge-management-rulebook` PR (rulebook repo, not this
repo) carrying README.md + playbook/*.md.

## Why

Issue #1174 requirement 1 + 6 (batch 6, per the approved proposal's
(b)/(b-revised) tiering — knowledge-management is listed moderate-tier,
parallel/streaming execution, not queued behind other roles). Requirement
2 (thorough web-verified research per rule, sources inline) and
requirement 4 (anti-shallowness / REMOVAL-category floor, amendment 4)
apply directly; this unit's dispatch prompt asked for the same shape
already landed for technical-writing (50 rules) and api-design (61
rules) as exemplars.

## Upstream basis

docs/issue-1174/proposals/operational-playbook-program.md (approved
design, sections (a)/(c)/(d)); consult-log 2026-08-13T04:36:27 entry
(rulebook is the landing location).

## Research trail (three-layer: practitioner / methodology-standard /
academic, per amendment-1 protocol)

All sources fetched via WebSearch this session, one parallel batch of 5
queries covering the axes above:

- ADR lifecycle (supersession-lifecycle axis): https://adr.github.io/ ,
  https://www.martinfowler.com/bliki/ArchitectureDecisionRecord.html ,
  https://www.techtarget.com/searchapparchitecture/tip/4-best-practices-for-creating-architecture-decision-records ,
  https://www.catio.tech/blog/architecture-decision-record ,
  https://docs.gitscrum.com/en/best-practices/documenting-architectural-decisions
- Controlled vocabulary / ISO 25964 / SKOS (taxonomy-tagging axis):
  https://www.niso.org/standards-committees/iso-25964 ,
  https://www.niso.org/schemas/iso25964 ,
  https://moderndata101.substack.com/p/demystifying-skos-for-practitioners ,
  https://en.wikipedia.org/wiki/Controlled_vocabulary ,
  https://arxiv.org/pdf/cs/0701072 ,
  https://www.hedden-information.com/category/taxonomy-standards/
- Diátaxis (structure-findability axis): https://diataxis.fr/ ,
  https://ubuntu.com/blog/diataxis-a-new-foundation-for-canonical-documentation ,
  https://idratherbewriting.com/blog/what-is-diataxis-documentation-framework ,
  https://bssw.io/items/diataxis-a-systematic-approach-to-technical-documentation-authoring
- Content pruning/curation (curation-pruning axis, SEO-literature origin,
  applied by analogy — flagged as such in the file's own research-trail
  header): https://www.g2.com/articles/content-pruning ,
  https://www.conductor.com/academy/content-pruning/ ,
  https://theinfluenceagency.com/blog/guide-to-content-pruning-and-its-benefits ,
  https://backlinkmanager.io/blog/content-curation-vs-content-pruning-understanding-difference/
- Pattern extraction from postmortems (academic layer, pattern-extraction
  axis): https://cacm.acm.org/research/knowledge-management-with-patterns/ ,
  https://en.wikipedia.org/wiki/Postmortem_documentation ,
  https://lsaglobal.com/project-management-postmortem-analysis-leveraging-insights/ ,
  https://arxiv.org/pdf/2601.22758

No pretrained-recall content: every rule's `source:` line traces to one
of the URLs above, fetched this turn via WebSearch (not asserted from
training-data memory).

## Acceptance check against issue #1174

- check "docs/playbook/ >= floor, condition+choice+source, one removal
  per axis": met — 5 files, 11 rules each (>= floor 10), 2 REMOVAL rules
  per axis (>= the required >=1/axis).
  derived: `grep -c '^[0-9]\+\.' playbook/*.md` and
  `grep -c '\*\*REMOVAL\*\*' playbook/*.md` in the rulebook checkout —
  reproduced below.
- check "one live role session's judgment record cites a specific
  playbook rule (executed-live)" — NOT satisfied by this unit; out of
  scope for a single-role fan-out dispatch, tracked at the issue level
  per requirement 5's own batch-level Acceptance check, not per-role.
- `gates/playbook_depth_gate.py` — per the proposal's Out-of-scope list,
  this script is not yet built; not run against this playbook.

```
$ cd ~/.tokenmaxxxer/work/knowledge-management-rulebook-issue-24-implementation/knowledge-management && grep -c '^[0-9]\+\.' playbook/*.md && grep -c '\*\*REMOVAL\*\*' playbook/*.md
```

## kind

report

## loop_state

phase1_delivered

## open findings

1. `gates/playbook_depth_gate.py` does not exist yet (proposal
   out-of-scope item), so this playbook's shape has not been machine-
   verified — only manually checked against the (c) spec's 6 criteria.
   resolution path: build the gate script (a separate, cross-role unit
   per the proposal) and re-run it against this playbook once it lands.
2. `roles/specs/knowledge-management.spec.json` has not been given a
   `playbook_refs` pointer (proposal item (e)) — out of scope for this
   fan-out dispatch per the proposal's own Out-of-scope list.
   resolution path: a follow-up unit adds `playbook_refs` once the spec-
   pointer wiring step of the program executes.
3. issuecomment-5276791251 (generic escalation-verdict template, no PR
   number filled in) landed mid-session — canonical:
   `gh api repos/tokenmaxxxer/on-the-record/issues/comments/5276791251`
   (read this turn; body: "Verdict: PR #? → escalate (depth or impact
   axis did not clear)", no PR number, no role name). Treated as
   not-actionable against this unit per the amendments-reconciled line
   in docs/issue-1174/reports/knowledge-management.md.
   resolution path: a maintainer review of this unit's rulebook PR
   should say plainly whether the escalation was meant for this unit; if
   so, revise the playbook content per the depth/impact gap named there.

## What did not work

None.
