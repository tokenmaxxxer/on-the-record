---
status: proposed
files:
  - docs/issue-914/reports/product-discovery/survey.md
  - docs/issue-914/reports/product-discovery/scout-brief.md
  - docs/issue-914/proposals/2026-08-12-standing-real-build-and-use-verification.md
---

# Proposal — standing real-build-and-use verification, default-on (issue #914, phase 1: design)

## Intent

Design, plugin-only and default-on, a standing requirement that closes
the shared root cause behind orphaned capabilities (#909) and silent
failures (#910): an implementation lands after satisfying static/unit
checks, but whether it actually works when really built and used is
never verified by default. Generalize this across three artifact types
— target-repo deliverable, plugin gate/hook, general outcome claim —
and specify how the #776 harness proves the requirement holds.
Supersedes #870 candidate-b as the design vehicle for that mechanism.

## Constraints (from the issue + directives)

- Default-on via plugin hooks only — no forced CI, no explicit
  invocation (north-pole req #7, same bar #870/#892 already met).
- Never a false positive result: an unmeasurable artifact degrades to
  `UNMEASURED-with-reason`, the standing escape shape already
  established by #310's `unverifiable:` and reused by #870/#892.
- Must compose with, not duplicate: #892 (write-time citation-kind
  check for outcome claims), #906 (standing test-authoring invariant —
  "no untested code path lands").
- Must specify how #776's harness (spec'd, unbuilt) proves the
  requirement — a change that satisfies static checks but does not
  actually work when built and used must be caught by default.

## Evidence cited

- canonical: docs/issue-909/reports/conformance-review/survey.md (read
  this session, "Finding" section) — one confirmed orphan
  (`on-the-record/hooks/absorbed-branch-recut-guard.sh`): implemented,
  its own test file present, doc rows asserting it ships live, but no
  `hooks.json` row — never fired in any installed session. A test
  existing did not catch this; wiring verification would have.
- canonical: docs/issue-910/reports/defect-verification/silent-failure-inventory.md
  (read this session, findings 5-8) — four deny-capable gates fail open
  on a missing tool with no log line distinguishing "checked, clean"
  from "the check itself never ran." None of these sites' unit tests
  exercise the fail-open branch against a crafted "tool missing"
  condition as a live-fired lifecycle event.
- canonical: docs/issue-870/proposals/2026-08-11-generalized-fake-success-detection.md
  (read this session, "Evidence cited" section) — four independent
  incidents (PRs #845, #855, #867, #787's rerun) where a prior PASS/
  finished-implementation verdict did not survive fresh re-execution;
  the RICE table there already ranks (b) — real execution — highest
  Impact of the three candidates, but it was never built.
- canonical: https://code.claude.com/docs/en/hooks (re-consulted this
  session per docs/issue-914/reports/product-discovery/scout-brief.md)
  — confirms `PreToolUse` can refuse a write before it lands and
  `Stop`/`SubagentStop` can block a turn/subagent from ending; no event
  type can itself synthesize a lifecycle invocation of another hook, so
  live-firing a hook under test is an executable-check convention
  (crafted stdin JSON piped into the target script), not a new hook
  type — same shape `gates/test_boundary.py` and
  `gates/test_acceptance_gate.py` already use.

No stated-preference or hypothetical evidence used (Mom Test rule) —
all four items are direct code/incident/documentation observations.

## Candidates — RICE scoring

Reach (fraction of relevant writes/turns/artifacts this mechanism
covers per session), Impact (1-3: a real orphan/silent-failure/false
claim prevented vs. cosmetic), Confidence, Effort (person-weeks
equivalent):

| Candidate | Reach | Impact | Confidence | Effort | RICE |
|---|---|---|---|---|---|
| (a) target-deliverable acceptance-command re-run (generalizes #870 candidate-b) | 0.5 (fires only where a target has a recorded acceptance command; degrade path covers the rest) | 3 (the only candidate that runs a REAL execution against the REAL current target — directly matches the #845/#855/#867/#787 incident shape) | 0.6 (design and enforcement point already scoped in #870's own proposal, not yet built — plumbing risk, not design risk) | 2 | 0.5×3×0.6/2 = 0.45 |
| (b) plugin gate/hook mandatory live-fire test | 0.4 (fires on every newly-staged `on-the-record/hooks/*.sh`/`gates/*.py` commit, the exact surface #909's orphan slipped through) | 3 (directly closes the #909 orphan class: a live-fire assertion for `absorbed-branch-recut-guard.sh` would have failed the moment it landed with no `hooks.json` row, since there would be nothing to pipe the crafted payload into) | 0.6 (executable-check convention already exists in this codebase for gate unit tests; new part is requiring it specifically for new gate/hook files and asserting the allow/deny path, not just that code runs) | 1.5 | 0.4×3×0.6/1.5 = 0.48 |
| (c) general outcome-claim gate tightened to require (a)/(b)-shaped citations only | 0.9 (fires on every outcome-claim marker already covered by #892's shipped check — highest reach, since it rides an existing enforcement point) | 2 (closes the citation-kind loophole between #892's shape check and an actual re-run — but is a write-time citation check, not itself a re-execution, same limit #892 already accepts) | 0.8 (small, additive change to an already-shipped, already-tested check function) | 0.5 | 0.9×2×0.8/0.5 = 2.88 |

Reach data above is derived from each candidate's own trigger surface:
(a) from target-acceptance-command configuration state (mirrors #870's
own reach derivation for its candidate-b); (b) from new-gate/hook-file
commit frequency (#909's sweep found one orphan across the current
34-row set — a small but nonzero rate); (c) from #892's already-
measured firing rate on the existing outcome-claim marker vocabulary.

(c) wins on RICE by a wide margin because it is cheap and rides an
existing enforcement point, but it cannot alone close the gap: (c) can
only demand that a citation LOOK like a live-fire/acceptance-run
reference, never confirm the referenced run actually happened this
turn or actually passed — that confirmation is exactly what (a) and (b)
supply. This mirrors #870's own reasoning for shipping candidate-a and
candidate-b together rather than picking the single highest-RICE
candidate in isolation: they close different halves of the same gap.
Recommendation: ship all three, in dependency order (b) before (a)
before (c) is meaningful, since (c)'s tightened citation vocabulary
should recognize the specific citation shapes (a) and (b) produce.

## What will be done (design output of this phase)

### Design, per artifact type

**Artifact type 1 — target-repo deliverable.** Generalizes #870
candidate-b, unbuilt until now.

- Setup: mirrors #831's `ensure_target_remote` shape — first outcome-
  claim write in a target repo with no recorded acceptance command
  prompts once (attended sessions only, gated by the `unattended` flag
  the same way #831 gates its own prompt): "what command proves this
  target's deliverable actually works?" Recorded via `ledger_write`
  (`{"event": "acceptance_command_confirmed", "command": ..., "ts":
  ...}`), asked once per target, not re-asked unless the recorded
  command stops executing at all (a syntax/missing-binary failure,
  distinct from the command running and reporting a genuine failure).
- Enforcement point: `Stop`/`SubagentStop` — per the scout brief, the
  only event types able to block a turn/subagent from ending. When this
  turn's transcript carries an outcome-claim marker and an acceptance
  command is on record for this target, the hook runs it (bounded
  timeout) and requires the claim's citation to match the run's actual
  exit status. A claim backed by a non-zero exit, or by no run at all
  when a command IS on record, is refused (`decision: "block"`).
- Degrade path: no acceptance command on record (setup declined, or
  genuinely none exists yet) → the claim is not blocked, but the citing
  line must read `UNMEASURED-with-reason: no acceptance command on
  record for this target` — reusing #310's `unverifiable:` escape
  shape rather than inventing a new one.

**Artifact type 2 — plugin gate/hook.** New mechanism; this is the
piece #870 never scoped, because #870 was about outcome claims in
general, not specifically about a gate/hook's own liveness.

- Enforcement point: `PreToolUse` on `git commit`, sibling to
  `test-authoring-invariant-guard.sh` (#906) — same interception shape,
  one layer stricter: for a staged new or changed file under
  `on-the-record/hooks/*.sh` or a `gates/*.py` module registered as a
  gate/hook, the commit must also stage (a) a matching `hooks.json` row
  (or an explicit CLI-only design note, the same exemption
  `poll-rearm.sh`/`record-scaffold.sh` already carry per #909's
  survey), AND (b) a live-fire test — an executable check that pipes a
  crafted lifecycle-event-shaped JSON payload into the hook script via
  stdin and asserts its stdout/exit code against the allow/deny/log
  outcome the script's own header comment declares, not merely that
  the script imports or runs without a Python exception.
- This is a live-fire-test-EXISTS check, mechanically identical in
  enforcement shape to #906's existing "a test exists" check — but
  additionally requires that test to invoke the hook script as a real
  lifecycle event with a synthetic payload (matching the stdin-JSON
  contract every `on-the-record/hooks/*.sh` script already implements),
  not merely import the module or call an inner function directly.
  #909's orphan is the direct counter-example this closes: a commit
  landing a new hook file with a `hooks.json` row present, but no
  live-fire test asserting the row's matcher actually catches the
  crafted input, would still pass #906's existing check (a test file
  exists) while failing this new one (the test never pipes a crafted
  payload through the actual script).
- Fail-open conditions mirror the existing gate family (no python3/git,
  not a git-repo, unparseable payload) — same escape hatch shape as
  `test-authoring-invariant-guard.sh`'s own documented fail-open list,
  plus a `Live-fire-N/A: <reason>` commit-trailer escape for a gate/hook
  with no lifecycle-event surface to live-fire (e.g. a pure library
  module like `gates.py` itself, sourced but never itself a `hooks.json`
  row).

**Artifact type 3 — general outcome-claim gate.** Tightens #892
(shipped), does not replace it.

- Extends `outcome_claim_citation_check`'s `_EXECUTED_LIVE_CANONICAL`
  acceptance set: currently any citation starting with `gh `, `git `,
  `pytest`, `python3`, etc. qualifies. Add recognition for the two new
  citation shapes artifact types 1 and 2 above will actually produce —
  `acceptance: <command> — result: PASS|FAIL|UNMEASURED` (already
  recognized) and a new `live-fire: <hook path> — result:
  allow|deny|log` line shape for artifact type 2 — so a citation
  produced by a genuine live-fire or acceptance run is recognized as
  such, and a citation that merely names a command without having run
  it this turn is not privileged over one that did.
- This is additive to #892's existing regex set, same append-only
  widening policy #870/#892/#906 already use for their own marker
  vocabularies — no removal or narrowing of what #892 already accepts.

## How this subsumes #909 and #910 at the root

If artifact type 2's live-fire requirement had been standing when
`absorbed-branch-recut-guard.sh` was committed, the commit gate would
have required a test piping a crafted `PreToolUse`/`Bash` payload
(a `git commit`/`gh pr create` command string) into the script and
asserting a matching `hooks.json` row exists for the matcher that test
depends on — with no such row, the live-fire test has nothing to
invoke as a real lifecycle event and the commit is refused, closing
#909's orphan class at the point it would have been introduced, not
after a separate sweep discovers it later.

If the same requirement had been standing for the four fail-open gates
#910 lists (findings 5-8), each gate's live-fire test would need to
assert the deny-capable branch actually fires under a crafted
tool-missing condition, not just that the happy-path (tool present, no
violation) returns allow — a fail-open branch with a live-fire test
asserting a specific log line (per this proposal's #910-composition
note below) would surface exactly the silent-vs-clean ambiguity #910's
findings identify, at commit time rather than via a manual audit.

Both classes share the same structural gap this proposal targets: a
test existing was treated as equivalent to the capability having been
proven to actually fire, when built and used for real.

## How this composes with #892 and #906

- #892 (candidate-a, shipped) checks citation PRESENCE and SHAPE at
  write time — cheap, mechanical, catches a claim with no citation or
  an obviously non-executed one. This proposal's artifact-type-3 change
  extends #892's accepted-shape vocabulary; it does not alter #892's
  enforcement point or its existing checks.
- #906 (test-authoring invariant) checks that a test EXISTS for new
  code. This proposal's artifact-type-2 change narrows that requirement
  specifically for gate/hook files: existing is necessary but not
  sufficient — the test must be a live-fire, not any test. #906's
  general "test exists" requirement is untouched for all other code
  paths; only the gate/hook subset gains the stricter bar, since that
  subset is exactly where #909's orphan and #910's silent-failure sites
  live.
- Composition order: #906 fires first (does a test exist at all), this
  proposal's artifact-type-2 check fires as an additional, narrower
  condition on the same commit boundary (is that test a live-fire, for
  gate/hook files specifically) — sibling checks on the same
  interception point, not a replacement chain.

## How the #776 harness proves this

Per `docs/specs/northpole-harness.md`'s existing signal table, this
proposal's requirement is provable against the same fixture target and
signal shape already spec'd, extending signal #3 rather than adding a
new one:

- Signal #3 ("real-wired verification") already specifies the harness
  independently checks out the resulting repo state and runs the
  target's own build+run commands. This proposal's artifact-type-1
  mechanism is what makes that independent re-run happen by default
  INSIDE the session too, not only by the harness after the fact — so
  signal #3 becomes a redundant double-check (harness confirms what the
  session's own `Stop`-hook re-run should have already confirmed) rather
  than the only real-execution check in the loop.
- A seeded-defect run (the harness's existing `--version` crash
  fixture) with artifact-type-1's mechanism installed and NO acceptance
  command yet confirmed for the fixture target must show the degrade
  path firing (`UNMEASURED-with-reason`), never a silent pass — this is
  a new assertion this proposal adds to signal #3's existing pass
  condition, checkable once the harness itself is built (#776 step 2).
- For artifact-type-2, the harness (once built) can seed a second
  fixture: a plugin gate/hook file staged with a `hooks.json` row but
  with its live-fire test stubbed to a no-op, and assert the commit
  gate refuses the commit — proving a would-be #909-shaped orphan
  cannot land under this requirement. This is a new fixture case, not
  covered by the harness's existing single fixture-target design
  (`docs/specs/northpole-harness.md` section 1) — the implementation
  phase should add it as a second, narrower fixture rather than folding
  it into the CLI fixture already spec'd for signal #3.

## Plugin-only / no-forced-CI feasibility

Confirmed feasible for all three artifact types using only plugin
`hooks.json` entries: artifact type 1 is a `Stop`/`SubagentStop`
`command` hook plus a one-time setup prompt mirroring #831's precedent.
Artifact type 2 is a `PreToolUse` `command` hook on `git commit`,
identical registration shape to `test-authoring-invariant-guard.sh`.
Artifact type 3 is a pure extension of `gates/record_lint.py`'s
existing regex set, called from the same already-registered
`record-claim-guard.sh` `PreToolUse` hook #892 already uses. No CI
workflow, no explicit skill invocation, no new install step beyond the
plugin itself.

## Out of scope

- Implementing the three mechanisms (phase 2, pending approval).
- Widening the outcome-claim or state-claim marker vocabularies beyond
  the additive citation-shape recognition described for artifact type
  3 (append-only follow-up, same limitation #870/#892/#906 already
  note for their own vocabularies).
- Verifying an acceptance command's or a live-fire test's SEMANTIC
  correctness beyond exit-status/outcome match — an executed-live
  command or live-fire assertion that itself checks the wrong thing is
  out of scope, same boundary #870/#892/#776 already draw.
- Building the #776 harness itself (already a separate, in-progress
  issue at step 1 of 3) or its two new fixture cases named above —
  those are implementation-phase and #776-step-2 work respectively.
- Retroactively wiring or retiring `absorbed-branch-recut-guard.sh`
  (that is #909's own step 2, tracked on that issue, not duplicated
  here).

## How you will know it worked

Per the composed signal above: in a fresh installed target session, a
deliverable claim with no executed-live citation is refused or
downgraded to `UNMEASURED-with-reason` by default (artifact type 1); a
new gate/hook file landing with no live-fire test asserting its
allow/deny/log behavior against a crafted input is refused at commit
time (artifact type 2); a general outcome claim citing a non-executed
source is refused, unchanged from #892's existing behavior, now
additionally recognizing genuine live-fire/acceptance citations as
qualifying (artifact type 3). A genuinely built-and-exercised change,
and a genuinely live-fired gate/hook, both pass without added friction.
Where no acceptance command is on record, the outcome reads
`UNMEASURED-with-reason`, never a silent pass. Empty state: a session
that makes no outcome/liveness claim and stages no new gate/hook file
is unaffected by all three mechanisms.

## Accumulation

This is accumulation-cost-shaped: artifact type 1 adds one bounded-
timeout command execution per turn that contains an outcome claim in a
target with a recorded acceptance command (scoped to outcome-claim
turns only, not every turn — same scoping #870's own candidate-b
already specified). Artifact type 2 adds one live-fire-test authorship
cost per new gate/hook file, paid once at authoring time, checked
mechanically thereafter at zero marginal cost per commit (the check
itself is a cheap script-presence/shape check, not a re-run of the
live-fire test on every commit — only on commits that stage a new or
changed gate/hook file). Artifact type 3 adds no recurring cost beyond
the one-time regex-set extension, since it rides #892's already-paid
enforcement point. None of the three introduces a per-turn cost on
turns that make no relevant claim or staging change — the accumulation
is bounded by claim/staging frequency, not by session length.

## What did not work

None.
