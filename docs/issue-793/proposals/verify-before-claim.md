---
status: proposed
files:
  - docs/issue-793/proposals/verify-before-claim.md
  - docs/issue-793/reports/product-discovery/survey.md
  - docs/issue-793/reports/product-discovery.md
---

# Proposal — verify-before-claim (issue #793, phase 1: design)

## Intent

Design a default-on, hooks/directives-only mechanism so an agent
confirms a consequential claim (role output, session/PR/board state, or
a defect) against the canonical source before acting on it, instead of
against a summary or partial signal.

## Constraints (from the issue + directives)

- Default-on via plugin hooks/directives only — no CI, no explicit
  invocation (req #7).
- Must not block low-stakes reads (empty-state).
- #791 is the code-slice instance (defect claims); this issue is the
  general rule and anchors #791, not a replacement for it.
- Composes with `record-claim-guard.sh` / `gates/record_lint.py`
  (existing citation-shape checks) rather than duplicating them.

## OST placement

outcome: false-premise consequential actions (bad halts, wrong
issue-closes, defect "fixes" on false premises) drop toward zero.
opportunity: the gap between "a claim carries *some* citation" (already
gated) and "the citation names a canonical, not summary, source" (not
gated).
candidate solutions: (A) directive-only — instruct verify-before-claim,
no mechanical check; (B) directive + a `canonical:`-tag mechanical gate
extending `record_lint.py`; (C) full automated re-verification (the gate
itself re-runs `gh pr view`/reads the file to confirm the claim).
discriminating assumption test: can a hook mechanically distinguish "the
agent read the canonical source" from "the agent typed a citation that
looks like one" without executing arbitrary re-verification? — answered
in Feasibility below; this determines A/B/C.

## Evidence cited

- interview/observation count: 1 self-report, 2026-08-11, paraphrase:
  consumer session traced 5 wrong judgments to one shared cause
  (asserting on role-summary/partial-observation without canonical
  confirmation).
- interview/observation count: 1 in-session recurrence, 2026-08-11,
  paraphrase: this same orchestration session mistook a phase-1 plan PR
  for a baseline result and misread a filtered `ps` grep as sessions
  gone.
- code observation, 2026-08-11, paraphrase: `record_lint.py`'s existing
  count/path/unverifiable checks (derived:
  gates/record_lint.py:60-140) validate citation SHAPE, not citation
  SOURCE KIND — a `derived: role's own summary` line passes identically
  to a `derived: gh pr view` line today.

No stated-preference or hypothetical evidence used (Mom Test rule) —
all three items are direct incident/code observations.

## RICE scoring (candidates A/B/C)

Reach (fraction of consequential-claim writes affected per period),
Impact (1-3 scale: false-premise action prevented), Confidence, Effort
(person-weeks equivalent, hook/gate authoring):

| Candidate | Reach | Impact | Confidence | Effort | RICE |
|---|---|---|---|---|---|
| A — directive-only | 1.0 (all role sessions read the directive) | 1 (relies on discipline; #793's own root cause is agents ignoring exactly this kind of instruction under pressure) | 0.3 | 0.5 | 1.0×1×0.3/0.5 = 0.6 |
| B — directive + `canonical:` tag gate | 0.6 (only claims the gate's regex can classify: state/defect claims in a record; role-output claims inside a PR body are not gated the same way) | 3 (mechanically blocks the exact failure shape: a claim with no canonical-source tag) | 0.7 | 1 | 0.6×3×0.7/1 = 1.26 |
| C — full automated re-verification | 0.6 | 3 | 0.15 (a hook cannot safely re-run `gh pr view`/read arbitrary files against network/auth inside a PreToolUse hook without becoming its own unreliable dependency, and cannot judge SEMANTIC correctness of a claim, only tag presence) | 4 | 0.6×3×0.15/4 = 0.0675 |

B wins on RICE. Reach data is real (derived from existing gate's
per-write firing pattern), so RICE applies directly — no ICE fallback
needed.

## Taxonomy of canonical source per claim type

| Claim type | Summary/partial signal (insufficient) | Canonical source (required) |
|---|---|---|
| role-output claim ("role X did/found Y") | the role's own self-summary sentence, a chat-relayed paraphrase, a task-notification's headline | the role's actual board record (`docs/issue-<n>/reports/<role>.md` on `main`) or the PR's real diff (`gh pr diff <n>` / `gh pr view <n> --json files`) |
| session/PR/board state claim ("session halted", "N sessions running", "PR is mergeable") | a grep/filter over a log or `ps` output, a watcher event, a truncated tool result | the raw ground-truth command output in full (`spawn.py ps` unfiltered, `gh pr view <n>` raw JSON, the actual file read in full) |
| defect/root-cause claim ("file:line causes Z") | a keyword grep hit, a filename match | actual source + design read at file:line with surrounding context (#791's slice — unchanged, this issue anchors it, does not re-specify it) |

## What will be done (design output of this phase)

1. **Directive** (`on-the-record` plugin, SessionStart or existing
   core-protocol injection point): instructs that before a
   role/orchestrating session takes a consequential action — file/close
   an issue, halt/merge a session or PR, or write a record CLAIMING a
   state or defect — it must have confirmed the claim against the
   canonical source per the taxonomy above, and any such claim it
   writes into a record must carry an explicit `canonical: <what was
   read>` tag naming the source consulted (e.g. `canonical: gh pr view
   790 --json files`, `canonical: docs/issue-785/reports/implementation.md
   (main)`, `canonical: spawn.py ps (raw, unfiltered)`). This composes
   with, does not replace, #791's file:line-context requirement for
   defect claims specifically.

2. **Gate extension** (`gates/record_lint.py`, new function
   `canonical_source_claim_check`, wired the same way the four existing
   `record_lint` checks are — added to `lint_record()`'s check list and
   mirrored into `record-claim-guard.sh`'s write-time PreToolUse path):
   mechanically checkable surface, deliberately narrow —
   - Detect a STATE/DEFECT-CLAIM sentence via a small marker vocabulary
     already implicit in existing usage: a line asserting one of
     `halted|merged|closed|found|confirms?|is (running|gone|stale)` about
     a role/session/PR/issue/file, OR any line already caught by
     `bare_count_claim_check`'s count-of-something pattern (a superset
     signal: a state claim is very often also a count claim).
   - If such a line exists in the record text and NO `canonical:` tag
     appears anywhere in the same paragraph/bullet (or within N=3 lines
     above it), flag it — same shape as the existing `derived:`
     requirement, added as a sibling tag, not a replacement.
   - The gate CANNOT verify the claim is TRUE, and does not try to — it
     checks only that a canonical-source citation is PRESENT and
     minimally well-formed (non-empty, matches one of: a `gh` command
     string, a bare file path that exists in the tree, or a
     `spawn.py`/raw-command string). This is the same shape the existing
     `derived:`/`unverifiable:` checks already use — presence and
     well-formedness, not semantic truth.
   - This is intentionally weaker than "the gate re-verifies the claim"
     (candidate C, ruled out below) — it forces the agent to NAME what
     it checked, which is what makes the false-premise pattern
     (asserting from a self-summary with nothing to name) visible and
     refusable, and is exactly the same trust model
     `record-claim-guard.sh` already uses for `derived:`.

3. **Empty-state**: a write with no state/defect-claim marker sentence —
   a pure log line, a plan/next-steps line, a low-stakes read-only
   note, a doc/spec edit — is untouched; the check only fires on the
   narrow claim-marker vocabulary above, the same scoping
   `bare_count_claim_check` already uses (fires per-line, not per-file).

## Feasibility with hooks alone

Confirmed feasible for candidate B, at the scope stated above:
`record-claim-guard.sh` already runs as a synchronous PreToolUse hook
against `Write|Edit|MultiEdit` payloads scoped to
`docs/issue-*/reports/**`, calling into `record_lint.py` functions
(derived: on-the-record/hooks/record-claim-guard.sh:1-80,
gates/record_lint.py:1-60) — no CI, no explicit invocation, exactly
req #7's constraint. Candidate C (semantic re-verification) is NOT
feasible inside this hook shape: it would need network calls
(`gh pr view`) and filesystem reads of arbitrary paths synchronously
inside a tool-call gate, with no reliable way to judge whether the
returned content actually SUPPORTS the claim (that is a judgment call,
not a mechanical check) — ruled out on Effort/Confidence in the RICE
table above, not on raw impossibility of the tool calls themselves.

## Relationship to #791

#791 is the code-defect slice of this general rule, already covering
row 3 of the taxonomy in more detail (read source+design at file:line
with context, distinguishable from a grep hit). This proposal's
directive explicitly says "compose with, do not replace" #791's
existing/future gate for that row; rows 1 and 2 (role-output claims,
state claims) are the new ground this issue adds. If #791 lands a
`context:`-style tag first, row 3's `canonical:` tag in this design
should alias to it rather than introduce a second tag for the same
claim type — noted as an open integration point for phase 2, not
resolved here.

## Out of scope

- Implementing the gate/directive (phase 2, pending approval).
- Re-specifying #791's own file:line-context check.
- Any CI-based enforcement (explicitly excluded by req #7).
- Verifying claim TRUTH, only citation presence/shape (candidate C,
  ruled out above).

## How you will know it worked

Phase 2's Acceptance (per the issue): a unit test where a record claims
a role output / session-PR-board state / defect, and asserts the
deployed directive/gate requires the corresponding `canonical:` source
tag, refusing or flagging a claim backed only by a summary/grep/watcher
signal with no such tag; a record making no consequential assertion
passes unaffected.

## Accumulation

Not accumulation-cost-shaped — this is a new, narrowly-scoped gate
function added once, not a per-instance recurring cost.

## What did not work

None.
