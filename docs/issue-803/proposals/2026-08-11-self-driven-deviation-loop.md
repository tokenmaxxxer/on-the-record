---
status: proposed
files:
  - on-the-record/hooks/directive.sh
  - on-the-record/hooks/deviation-log-guard.sh
  - docs/handbooks/deviation-loop.md
  - docs/issue-803/reports/product-discovery/survey.md
  - docs/issue-803/reports/product-discovery/scout-brief.md
  - docs/issue-803/proposals/2026-08-11-self-driven-deviation-loop.md
---

## Request

Issue #803 step 1 (product-discovery): design the default-on, self-driven
find→file-as-issue-or-inline→resolve-via-role→continue loop for a PLAIN
session (not the human-directed orchestrator) — the layer above #787
(entering orchestration) and depending on #801 (quiet-gap self-wake) for
full operation. Output the spec, or state a kill rationale. This proposal
is the spec; no code lands in this phase (contract v3 s19 phase-1 scope).

## Constraints

- Reuse #699's primitives only (`spawn.py consult`, `spawn.py spawn`) —
  no new spawn/consult mechanism (survey: the primitives already exist
  and are sufficient; what's missing is the decision object that calls
  them mid-task).
- Default-on via plugin hooks/directives alone (req #7) — no CI, no
  explicit skill invocation required for this behavior to fire.
- Must not over-file: an empty-state guard is required by the issue's own
  Acceptance ("a run with no genuine problem/risk on the path does not
  spuriously file issues").
- Must compose with, not duplicate, #699's existing goal-loop text in
  `directive.sh` and the warrant-directive's own SCOPE EXCEEDED clause
  (survey: this repo already has a write-set-boundary convention; reuse
  it as the scope test rather than inventing a second one).
- Depends on #787 to be *operational* (a plain session must already be
  inside orchestration mode for any of this to have anywhere to run) and
  on #801 to be *fully* autonomous (resolution that outlives the current
  turn needs quiet-gap self-wake) — this proposal's design must state
  both dependencies explicitly rather than silently assume either is
  live.

## Rationale

**Go, not kill.** The gap is measured, not speculative (survey's baseline
citation): a plain session today either silently works around a problem
or never notices one — the routed-forward finding from #776 that this
issue exists to close. The resolution mechanism already exists (#699);
what's missing is a small, well-scoped decision object, not a new
subsystem.

**Chosen approach — a three-step decision object, injected as one more
`directive.sh` paragraph, gated the same way the existing three norms
already are (`CLAUDE_ROLE` unset):**

1. **RECOGNIZE**: a deviation is anything mid-task that is NOT normal task
   friction. Concretely: an error/ambiguity/risk counts as a deviation
   only if resolving it requires the session to do something the current
   task's own scope did not already call for (an edit outside the
   task's own write set, a judgment a role would normally render, a risk
   that would recur beyond this one task). A test failure the task itself
   exists to fix, a routine lint/type error inside the file already being
   edited, or an expected retry is NOT a deviation — it is the task. This
   is the empty-state guard's first half: most sessions recognize zero
   deviations, by design, because most work is exactly what was asked.
2. **CLASSIFY (file-vs-inline)**, only once step 1 fires:
   - **INLINE-FIX** iff ALL hold: (a) the fix stays inside the current
     task's already-frozen write set (the same write-set boundary the
     warrant directive's proposal frontmatter already declares — reuse,
     not reinvent); (b) the fix is mechanical — no design/architecture/
     security/product judgment call a reviewer would need to weigh
     alternatives on; (c) the fix does not change what the deliverable
     claims to do; (d) the fix is a one-off, not a recognizable systemic
     pattern.
   - **FILE-AS-ISSUE** otherwise: the deviation needs a role's judgment,
     crosses the write-set boundary, is systemic/recurring, or the fix
     itself is a scope-changing decision. This mirrors the warrant
     directive's own "SCOPE EXCEEDED" clause (finish what's in scope,
     stop, report, the remainder becomes the next proposal) — #803's
     contribution is turning that stop-and-report into a stop-and-file
     step that keeps the session moving instead of ending the turn.
   - When the classification itself is not obvious from (a)-(d) alone,
     the session renders it via ONE `spawn.py consult <role>
     "<question>"` call (the matching role, or a generalist role if none
     obviously matches) BEFORE acting — the classification is itself a
     judgment point per #699 R2, so it goes through consult rather than
     being decided inline by the session's own guess.
3. **RESOLVE AND CONTINUE**:
   - Inline case: apply the fix, append one line to a new deviation log
     (`docs/issue-<n>/reports/deviation-log.md`, or
     `docs/reports/deviation-log.md` with no issue in scope — same
     issue-keyed-vs-not split `consult-log.md` already uses) — timestamp,
     `inline`, one-line description, the diff's location. Resume the
     original task in the same turn.
   - File case: draft the issue (the session is now acting as the
     orchestrator, per #787's entry — issues are still user-confirmed per
     contract v3 s19 UNLESS #787's design already grants a
     bootstrap-drafted issue an explicit self-file allowance for exactly
     this deviation class; #803 does not resolve that permission
     question — it is #787's to answer, noted as an open dependency
     below), then `spawn.py spawn <role> "<task>" --issue <n>
     --background`. Append one line to the same deviation log — timestamp,
     `filed`, issue number, role, one-line description. The original
     session either continues its own unaffected work in parallel, or, if
     the resolution blocks the original task, waits on the spawn per the
     existing watch/re-arm pattern `directive.sh` already documents for
     the orchestrator flow (`spawn.py watch --issue <n>`) — no new
     waiting mechanism. When the fix lands (PR merged), the session
     appends a `resolved` line to the same deviation-log entry (issue
     number, PR, one line on what changed) and resumes the original task
     referencing the resolution.
   - Both cases: the deviation log is the resolution trail #776 finding 2
     found entirely absent — every deviation, inline or filed, leaves
     exactly one traceable entry; the RECOGNIZE step is what keeps this
     from becoming noise (no entry for non-deviations).

**Rejected alternative A — always file as an issue, never inline-fix.**
Rejected: would turn every routine one-line fix a session already makes
correctly (per #776, the session DID fix the seeded defect correctly) into
issue-and-PR overhead for zero-judgment changes, working against req #7's
own default-on-and-lightweight framing and directly violating the issue's
own empty-state acceptance line (a run with a trivial deviation must not
spuriously file).

**Rejected alternative B — always inline-fix, only log, never file.**
Rejected: this is close to what the #776 baseline already does today
(minus even the logging) and would leave req #5 ("problems solved by
spawning role-appropriate agents, not pushed to the human") permanently
unmet for anything that actually needs a role's judgment — a security or
architecture-shaped deviation would get silently patched by a session with
no such expertise, which is a worse outcome than #776's baseline, not a
better one.

**Rejected alternative C — a numeric/statistical noise threshold (e.g.
score each deviation, file above a cutoff).** Rejected per the scout
brief's gap line: SOC-style ML alert scoring assumes volume this loop
never has (at most one or two deviations per session); a scored threshold
would be un-tunable with no data and adds a knob with no empirical basis.
The mechanical (a)-(d) test is deliberately not a score.

## What will be done

- `on-the-record/hooks/directive.sh`: add one new paragraph (same
  `CLAUDE_ROLE`-unset gate as the existing three norms) stating the
  RECOGNIZE → CLASSIFY → RESOLVE-AND-CONTINUE steps above, explicitly
  framed as nesting inside the existing #699 R3 goal loop the same way
  the delegation norm already does — a deviation is a new judgment/
  artifact discovered mid-loop, not a separate loop.
- `on-the-record/hooks/deviation-log-guard.sh`: a new PreToolUse/Stop-
  shaped guard (mirroring `record-claim-guard.sh`'s existing pattern) that
  refuses a session-end when the transcript shows a recognized deviation
  (per its own logged marker) with no corresponding deviation-log entry —
  the mechanical backstop for "no traceless deviations," matching how
  `consult-log.md` traceability is enforced today.
- `docs/handbooks/deviation-loop.md`: the human-facing explanation of the
  RECOGNIZE/CLASSIFY/RESOLVE steps, the deviation-log format, and the
  explicit statement of the #787/#801 dependency (this design is
  write-able now; it is only fully operational once #787 lands the
  orchestration-entry behavior and #801 lands quiet-gap self-wake for
  filed deviations that outlive the current turn).
- This survey and this proposal (already phase-1 output).

## Out of scope

- Implementing any of the above (`directive.sh` paragraph,
  `deviation-log-guard.sh`, the handbook) — that is #803 step 2, gated on
  human approval of this proposal per contract v3 s19.
- Resolving whether a self-filed issue under this loop needs a different
  user-confirmation rule than #787's own bootstrap issue-drafting design
  — noted above as an explicit open dependency on #787, not answered
  here.
- #801's self-wake mechanism itself — this design assumes it exists for
  full autonomy and states the dependency; it does not design #801.
- Re-running the #776 harness — that is #803 step 3
  (execution-observation), after step 2 lands.

## Accumulation

`directive.sh` already accumulates one standing paragraph per landed
issue (the base flow, then #699 R2, then #699 R3) — this proposal's one
paragraph is the fourth such addition to a file re-injected on every
single prompt of every plain session. That is an accumulating read-cost,
not a one-time addition: each new norm makes every future prompt's
context slightly heavier, forever, regardless of whether that norm is
relevant to the current task. This proposal does not add a fifth
mechanism (a second file, a second hook) to avoid compounding that cost
further, and flags for whoever proposes the NEXT `directive.sh` addition
that a consolidation pass (folding the now-four norms into one
tighter block, or moving less-frequently-relevant norms to a
lazily-loaded reference like `/consult`'s own command doc) is due once a
fifth is proposed — not before, since three prior additions plus this one
is not yet a maintenance problem on its own, but a fifth would be.

## How you'll know it worked

- This proposal, once approved, gates #803 step 2 (implementation).
- Step 2's own success check (not this proposal's): a re-run of the #776
  harness (step 3, execution-observation) shows
  `orchestration_to_completion` and `problems_not_pushed_back` moving from
  baseline FAIL toward PASS, with the seeded mid-run problem
  self-filed-and-resolved and logged, per the issue's own Acceptance
  text — this proposal registers that as the pre-committed hypothesis
  below, to be applied mechanically at step 3, not re-judged then.

## Pre-registration (for step 3's future measurement)

We believe the RECOGNIZE→CLASSIFY→RESOLVE loop above, once implemented,
makes a plain session self-file-and-resolve the #776 fixture's seeded
mid-run problem instead of silently working around it.

- **Primary metric**: `harness/signals.py::check_problems_not_pushed_back`
  on a #776 harness re-run (zero human stalls AND a resolution trail
  present).
- **Guardrail metric**: `harness/signals.py`'s empty-state case — a
  harness re-run seeded with NO genuine problem must file zero issues
  (checked by asserting the deviation log for that run is empty, not
  merely that no new GitHub issue exists — an empty log is the stronger,
  directly-inspectable claim).
- **Threshold**: primary metric moves from the #776 baseline's FAIL to
  PASS; guardrail must show zero spurious deviation-log entries on the
  no-problem run — a primary PASS with a guardrail breach (spurious
  filing) is a reduced-trust result, not a win, per the guardrail-metrics
  obligation.
- **Decision rule**: both PASS at step 3 → validated, proceed. Primary
  PASS but guardrail breach → invalidated, the CLASSIFY step's mechanical
  test needs tightening before this loop ships as default-on. Primary
  still FAIL → invalidated, re-open this design.
- **ITWWS follow-up** (if this works we should ...): extend the same
  deviation log's `filed`/`resolved` shape to the orchestrator's own
  existing issue→spawn→PR flow, so a human-directed run and a self-driven
  run leave the same trail shape and both are readable by the same future
  tooling.
