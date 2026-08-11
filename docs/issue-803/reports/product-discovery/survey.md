---
kind: current-state-survey
---

# Current-state survey — issue #803

## Background / context

code_under_review:
- on-the-record/hooks/directive.sh
- docs/issue-776/reports/execution-observation.md
- docs/issue-699/proposals/consult-and-goal-loop.md
- docs/issue-787/proposals/product-discovery.md

Read in full before this survey, per the issue's verify-before-claim
instruction (#793):

- on-the-record/hooks/directive.sh (171 lines, read whole file): the
  only UserPromptSubmit hook reaching every plain session, gated solely on
  `CLAUDE_ROLE` being unset. It already carries three standing norms —
  the issue→spawn→PR flow, the #699 R2 delegation norm ("recognize a
  judgment point, call `spawn.py consult`"), and the #699 R3 goal loop
  ("decompose → delegate each judgment/artifact → integrate → continue
  until done or genuinely user-blocked → report").
  canonical: on-the-record/hooks/directive.sh lines 150-163 (read in full
  this session, the "YOUR GOAL LOOP" paragraph). It contains no
  recognize-a-deviation-mid-task logic and no file-vs-inline decision
  rule — that paragraph describes decomposing the ORIGINAL request, not
  what to do when a NEW problem surfaces mid-execution.
- docs/issue-776/reports/execution-observation.md (full baseline
  transcript read this session): a plain session with on-the-record
  installed, given one representative requirement, made 17 tool calls —
  all direct Bash/Read/Edit/Write, zero delegation. It hit the seeded
  defect's non-obvious root cause and fixed it correctly (build/tests
  independently verified PASS) but left zero resolution trail — no record
  file, no filed issue, no consult, nothing beyond the working-tree diff.
  canonical: docs/issue-776/reports/execution-observation.md §5 row #1
  ("orchestration_to_completion: FAIL ... zero Task or any other
  delegation/spawn-shaped tool use across the entire 75-line log") and
  row #5 / open findings 1-2 (no resolution trail even though the seeded
  defect was correctly self-resolved). Verdict:
  `orchestration_to_completion=FAIL`, `problems_not_pushed_back=FAIL`
  (zero human stalls, but no resolution trail — the check requires both),
  `autonomous_completion_reporting=FAIL`. Open finding 1 of that record
  states plainly that the observed session never delegated at all despite
  the plugin being installed, root cause explicitly left undiagnosed by
  that role, routed forward as a new backlog item — #803 is that
  routed-forward item's design step.
- docs/issue-699/proposals/consult-and-goal-loop.md: defines the two
  primitives #803 must reuse, not reinvent — `spawn.py consult <role>
  "<question>"` (judgment only, no repo write, always one trace-log line,
  even on error) and the existing `spawn.py spawn <role> "<task>" --issue
  <n>` deliverable path (issue → branch → PR).
  canonical: on-the-record/hooks/directive.sh lines 150-163 (read in full
  this session). No existing code path decides WHEN to call which
  mid-task; that decision object does not exist anywhere in this repo yet
  — no such branch point appears in that text.
- docs/issue-787/proposals/product-discovery.md: #787 is the layer
  directly below #803 — it makes a plain session recognize a
  requirement-shaped prompt and enter orchestration mode at all.
  canonical: `find docs/issue-787 -name implementation.md` (run this
  session, during this survey) → no output, zero matches. #787's own
  status: proposal phase-1 written and merged; no implementation record
  exists yet under docs/issue-787/reports/. #803's design must be
  written to compose with #787's eventual output without depending on it
  being live to be *designed* — only to be *operational*.
- issue #801 (issue text only, read via `gh issue view 801` this session
  — no docs/issue-801 tree exists in this repo yet).
  canonical: `find . -path '*issue-801*'` (run this session, during this
  survey) → no output, zero matches. This is the quiet-gap self-wake
  problem. #803's resolution step, when the filed issue's fix takes
  longer than the current turn, needs #801's self-wake to re-attend
  without a human present; #803's design notes this dependency rather
  than solving it.

## The problem, stated without a solution attached (JTBD)

The issue text (#803) already names its own solution mechanism
("self-file as an issue, resolve via role, default-on via directive.sh").
Restated in the customer's terms, without that mechanism named:

- **Job performer**: a plain Claude Code session, with on-the-record
  installed, mid-way through a user's requirement, running with no human
  watching turn-by-turn (headless or unattended).
- **Job**: when something on the path to the requirement is not what was
  expected — an error whose cause is non-obvious, a scope boundary the
  current work would have to cross, a risk that could recur — keep moving
  toward the requirement without either (a) silently working around the
  deviation and leaving no trace of it, or (b) stopping to ask a human who
  is not there to answer.
- **Circumstance**: no explicit skill/command was invoked for this
  specific deviation (req #7: default-on, no CI, no manual steering); the
  deviation was not anticipated by the task's original scope.
- **Desired outcome**: the requirement is still reached, and every
  deviation from the expected path is accounted for afterward — a human
  reading the repo later can tell what deviated and how it was resolved,
  without having to have watched the session live.

**Gap between the issue's framing and this restatement**: the issue
already presumes "file it as a GitHub issue and resolve it through the
role/PR machinery" is the right mechanism. The #776 baseline evidence
actually only proves the NEGATIVE — today's plain session does neither
option well: it silently works around problems, leaving no filed issue
and no resolution trail (canonical citation above, open findings 1-2).
It does not by itself prove that issue-filing (versus, say, a lighter
in-repo note, or always-consult-first) is the right mechanism for every
deviation size — that is exactly why the file-vs-inline decision rule
(this proposal's core content) has to exist, rather than "always file."

## Where this sits in the opportunity-solution tree

- **Outcome** (northpole, pre-existing): requirement reached with
  bottlenecks recognized and resolved without human steering (req #1),
  and by spawning role-appropriate agents rather than pushing problems to
  the human (req #5).
- **Opportunity** (child of #787's opportunity "a plain session
  auto-enters orchestration on a requirement"): once a plain session is
  inside orchestration, it still has no defined behavior for a problem
  discovered *mid-task*.
  canonical: on-the-record/hooks/directive.sh lines 150-163 (same "YOUR
  GOAL LOOP" text cited above) — it covers decomposing the ORIGINAL
  request, not deviations found while executing it. This is the
  opportunity #803 targets: "the entered session's mid-task
  deviation-handling decision loop."
- **Candidate solutions** (this proposal picks one, see the proposal's
  Rationale): (a) always file as an issue; (b) always inline-fix and log;
  (c) a classifier that routes each deviation to (a) or (b) by
  scope/judgment criteria, reusing #699's consult primitive to render the
  routing judgment itself when it is not mechanically obvious.
- **Discriminating assumption test** (fixed by the issue's own
  Acceptance, not invented here): re-run the #776 harness after
  implementation; assert `orchestration_to_completion` and
  `problems_not_pushed_back` move from baseline FAIL toward PASS, with
  the seeded mid-run problem self-filed-and-resolved (not silently worked
  around), and assert the empty-state case (no genuine problem on the
  path) files zero spurious issues.
