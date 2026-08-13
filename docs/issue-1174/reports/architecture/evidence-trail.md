# architecture operational playbook — evidence trail (phase-1 record)

This session's phase-2 record file (docs/issue-1174/reports/architecture.md,
a path that does not yet exist in this working tree) is gated behind an
"APPROVE issue-1174/architecture" comment per contract v3 s19. canonical:
PreToolUse:Write hook output this turn from
on-the-record/hooks/approval-gate.sh, refusing the write with "no matching
'APPROVE issue-1174/architecture' issue comment ... was found." This file
carries the evidence trail as allowed phase-1 material instead, matching the
api-design/technical-writing/brand-design precedent for this same issue.

amendments-reconciled: issuecomment-5276975028 — canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/1174/comments --paginate` output
this turn. Body is a `[watch]` bot notification ("issue-1174/pr-communications:
session-end: PR ... opened"), posted by JiwonJung94, about a different
role's session ending — not an amendment to this unit's scope or the
approved operational-playbook-program.md design. No amendment needed.

## What was done (delivered to the rulebook repo, outside this repo's gate)

Authored the architecture role's operational playbook (5 axes, 71 rules),
committed and pushed to tokenmaxxxer/architecture-rulebook, branch
issue-1174/operational-playbook.
canonical: `git push -u origin issue-1174/operational-playbook` output this
turn against tokenmaxxxer/architecture-rulebook (commit d4d0529).

Opening the rulebook PR itself (`gh pr create`) hit the same
pr-preflight/approval-gate deadlock documented for several sibling
fan-out units on this issue (market-analysis, data-engineering,
data-modeling, secure-coding, observability, ml-engineering,
refactoring-legacy, test-authoring): pr-preflight.sh requires an
`amendments-reconciled` line inside
docs/issue-1174/reports/architecture.md citing issuecomment-5276975028
(a comment that landed after this session started) before allowing ANY
`gh pr create` call in this session.
canonical: `gh pr create` output this turn from
on-the-record/hooks/pr-preflight.sh, refusing PR creation ("이슈 #1174에
세션 시작 이후 새 코멘트(issuecomment-5276975028)가 달렸다").

That exact path is this role's phase-2 record, which approval-gate.sh
refuses to let this session write before an "APPROVE issue-1174/architecture"
comment lands, so no phase-1-legal write can satisfy pr-preflight's
requirement.
canonical: PreToolUse:Write hook output this turn from
on-the-record/hooks/approval-gate.sh ("no matching 'APPROVE
issue-1174/architecture' issue comment ... was found").

Per this issue's own instructions ("push, open the rulebook PR (or
branch+relay note)"), the branch is pushed and this evidence trail is the
relay note: the architecture-rulebook PR still needs to be opened by a
later session (once the amendments-reconciled line can legally be written,
or once a maintainer opens it directly from the pushed branch).

Per the approved proposal design
(docs/issue-1174/proposals/operational-playbook-program.md sections (a)
axis-derived N floor, (b-revised) fan-out unit, (c) depth-gate shape, (d)
playbook/topic.md landing, amendment 4 removal-category requirement), the
PR adds:

- playbook/module-boundary-definition.md (14 rules, 4 REMOVAL, rule_count_floor: 12)
- playbook/dependency-direction.md (13 rules, 3 REMOVAL, rule_count_floor: 12)
- playbook/coupling-classification.md (14 rules, 6 REMOVAL, rule_count_floor: 12)
- playbook/interface-contract-shape.md (17 rules, 4 REMOVAL, rule_count_floor: 12)
- playbook/decomposition-strategy.md (13 rules, 6 REMOVAL, rule_count_floor: 12)
- README.md (Layout section pointer added)

71 rule blocks total, each condition -> choice -> source, every axis file
carrying at least 3 rules marked **REMOVAL** (amendment 4).
canonical: `grep -cE '^### [0-9]+' ` and `grep -c '\*\*REMOVAL\*\*'` run
against each playbook/*.md file this turn in the architecture-rulebook
checkout (/home/jwjung/tokenmaxxxer/rulebooks/architecture-rulebook),
counts as listed above.

## Research protocol (amendment 1, three layers)

Delegated to 5 parallel research subagents (Agent tool, one per decision
axis, background-dispatched then polled to completion and consumed this
same turn per contract v3 s22), each independently running WebSearch/
WebFetch this session — no pretrained-recall content, every rule cites a
URL the agent actually visited or read via search this turn.

Axes and their layer-2 (named standard/methodology) anchor sources, as
cited inline in each playbook file:

- module-boundary-definition: layer 1 (Sam Newman monolith-to-microservices
  notes, Shopify modular-monolith engineering post, InVision's
  microservices-back-into-monolith writeup) + layer 2 (Parnas information
  hiding, DDD bounded contexts (Fowler), Conway's Law, C4 model) + layer 3
  (Parnas 1972 CACM primary source; Springer peer-reviewed critique of
  coupling/cohesion as quality indicators).
  canonical: module-boundary-definition subagent's final message this turn
  (11 source URLs listed, including
  https://wstomv.win.tue.nl/edu/2ip30/references/criteria_for_modularization.pdf
  and https://link.springer.com/article/10.1007/BF00590439).
- dependency-direction: layer 1 (Uncle Bob Clean Architecture blog,
  ThoughtWorks Radar on architectural fitness functions/dependency-drift
  fitness functions) + layer 2 (Dependency Inversion Principle, Stable
  Dependencies/Acyclic Dependencies Principles, Hexagonal Architecture
  (Cockburn), Onion Architecture (Palermo), ArchUnit-style rules) + layer 3
  (OOPSLA'05 design structure matrix paper; arXiv architecture-erosion
  practitioner study).
  canonical: dependency-direction subagent's final message this turn (13
  source URLs listed, including https://groups.csail.mit.edu/sdg/pubs/2005/oopsla05-dsm.pdf
  and https://arxiv.org/pdf/2103.11392).
- coupling-classification: layer 1 (shared-database anti-pattern writeups,
  vFunction/Gremlin distributed-monolith posts, mrpicky.dev coupling
  essays) + layer 2 (afferent/efferent coupling and instability metric
  (Robert Martin), connascence (Page-Jones/Weirich)) + layer 3 (Stevens,
  Myers & Constantine 1974, IBM Systems Journal, "Structured Design";
  Springer empirical critique of coupling/cohesion metrics).
  canonical: coupling-classification subagent's final message this turn (11
  source URLs listed, including
  https://gist.github.com/Momus/4e42f6e5ca3e4658cb5033145c5a80e1 and
  https://link.springer.com/article/10.1007/BF00590439).
- interface-contract-shape: layer 1 (sync-vs-async microservice
  communication writeups, Temporal saga orchestration-vs-choreography
  posts) + layer 2 (DDD context-mapping patterns — Shared Kernel,
  Conformist, Anticorruption Layer, Open Host Service/Published Language;
  Interface Segregation Principle; Sam Newman's Backends for Frontends) +
  layer 3 (Parnas information hiding primary source; CAP/PACELC
  latency-consistency tradeoff literature).
  canonical: interface-contract-shape subagent's final message this turn (7
  source URLs listed, including
  https://john.cs.olemiss.edu/~hcc/researchMethods/notes/ClassicParnas/ACMannotated/ClassicParnasRevisionAnnotated.pdf).
- decomposition-strategy: layer 1 (Segment "Goodbye Microservices", Amazon
  Prime Video 90%-cost-cut writeup, Shopify Packwerk modular-monolith post)
  + layer 2 (Fowler MonolithFirst, Sam Newman Strangler Fig/Branch by
  Abstraction, Inverse Conway Maneuver/Team Topologies) + layer 3 (Adams,
  Converse, Hales & Klotz, *Nature* 592, 2021, "People systematically
  overlook subtractive changes", cited on the primary REMOVAL rule; VAE-GNN
  microservice decomposition case study; DDD systematic literature review
  (arXiv)).
  canonical: decomposition-strategy subagent's final message this turn,
  listing https://www.nature.com/articles/s41586-021-03380-y among the
  source URLs it fetched/searched.

canonical: each subagent's own WebSearch/WebFetch tool calls this turn
(reported per-axis source URL lists in each agent's final message this
turn, cited above), and the per-rule `source:` lines in each playbook file
resolving to those calls' results.

## Open findings

- The parent repo's playbook-depth-gate script (proposal section (c),
  `gates/playbook_depth_gate.py`) does not exist yet — out of scope for
  this proposal per its own "Out of scope" section — so the shape counts
  above were verified manually (`grep -cE`), not by running the gate.
  canonical: `find gates -name playbook_depth_gate.py` this turn, no match.
- No live role-session citation of a specific playbook rule has been
  produced for this batch yet (Acceptance check 2, "executed-live") —
  that check is scoped to a later step once `playbook_refs` wiring (proposal
  section (e)) lands in `roles/specs/architecture.spec.json`, which is also
  out of scope for this unit.
  canonical: `grep -n playbook_refs roles/specs/architecture.spec.json`
  this turn, no match.
- docs/issue-1174/reports/architecture.md (phase-2 record) remains gated
  behind an "APPROVE issue-1174/architecture" comment; no such comment
  exists as of this session.
  canonical: `gh issue view 1174 --comments` output this turn, grepped for
  "APPROVE issue-1174/architecture", no match.

## Why

Issue #1174 requires practitioner-decision-depth playbooks in every role's
rulebook repo, not methodology pointers in the parent spec. Landing
location and depth-gate shape were already ruled by the approved
docs/issue-1174/proposals/operational-playbook-program.md; this unit
executes that design for the `architecture` fan-out unit only (amendment 3:
one role = one independent, non-blocking work unit).

## Upstream / basis

- docs/issue-1174/proposals/operational-playbook-program.md (approved
  program design, sections (a)-(e))
- northpole req#1/req#5 — docs/specs/northpole.md

## kind / loop_state

kind: report
loop_state: awaiting-review (terminal for `report`: this phase-1 evidence
trail is itself finished; open follow-on work is tracked below, not this
record's own completion)
canonical: this file's own content, written this turn (self-referential —
no external outcome is being asserted by the loop_state line itself).

## Next steps

- Open the tokenmaxxxer/architecture-rulebook PR from the pushed
  issue-1174/operational-playbook branch once the pr-preflight/
  approval-gate deadlock above is resolved, then get human review/merge.
- Post "APPROVE issue-1174/architecture" (from a docs/specs/approvers.md
  account) to unlock docs/issue-1174/reports/architecture.md phase-2
  writes, if a phase-2 build step is later required for this unit.
- Resolution path for the two open findings above: build
  `gates/playbook_depth_gate.py` in a later step (per proposal section (c),
  explicitly out of scope here) and wire `playbook_refs` into
  `roles/specs/architecture.spec.json` (per proposal section (e)) before
  attempting the Acceptance-check-2 executed-live citation test.
