---
status: proposed
files:
  - docs/issue-476/reports/product-discovery/survey-round2.md
  - docs/issue-476/reports/product-discovery/scout-brief-round2.md
  - docs/issue-476/proposals/discovery-round2.md
---

# Proposal — issue #476 round 2: wiring the H1 mechanism to an actual trigger

Phase 1 only. Scope is narrow, per the operator's assignment: the 2026-
08-10 execution-observation measurement found `fabrication_survival_rate`
= 100% not because `claim_scan.py`/`reexecution_gate.py` are wrong (they
are correct, commit `49a6154`) but because nothing on the deployed,
zero-install hook surface ever calls either. This proposal pre-registers
which wiring candidate to build, a metric, a threshold, and a decision
rule, before any hook file is touched.

## Candidates scored (RICE), against the JTBD in survey-round2.md

Reach/Impact scored against "PRs opened by role sessions, per week," same
basis round one used. Effort in relative days. Confidence reflects
whether the candidate survived the scout brief's must-be check (no second
copy of check logic; fail posture matches blast radius; kill switch
present).

| # | Candidate | Reach | Impact | Confidence | Effort | RICE | Verdict |
|---|---|---|---|---|---|---|---|
| A | PreToolUse `Bash` chokepoint on `gh pr create`/`gh pr edit`, calling `claim_scan.scan_text()` inline (mirrors `pr-preflight.sh`'s shape) | 5 | 5 | 0.8 | 1 | 20.0 | **Keep — primary, ships first** |
| B | Same chokepoint additionally invoking `reexecution_gate.run_reexecution()` synchronously (blocking) | 4 | 5 | 0.5 | 3 | 3.3 | Keep, staged after A — see rollout-friction hypothesis |
| C | `PostToolUse` hook on the same `Bash` match, invoking re-execution asynchronously (non-blocking, writes `.reexecution/<issue>-<role>.json` after the PR already exists) | 4 | 4 | 0.6 | 3 | 2.1 | Keep as B's fallback if B's latency guardrail fails |
| D | `Stop`-event hook (mirrors `role-test-claim-guard.sh`) scanning the session's own record content, independent of the `gh pr create` call | 3 | 2 | 0.4 | 2 | 1.2 | **Reject for this round** |

### Why each non-primary candidate is scored the way it is

- **A (primary)**: reach and impact match `pr-preflight.sh`'s own reach
  (every `gh pr create`/`gh pr edit`, the exact chokepoint the current
  gap sits at) at the lowest effort of any candidate — the check itself
  (`claim_scan.scan_text()`) is a pure-Python regex scan, no subprocess,
  no worktree, so wiring it costs one new hook file mirroring an existing
  shape, not new infrastructure. Confidence is capped below round one's
  own scoring (0.8, not higher) because the scout brief's gap line
  already names a real open design tension this proposal must register,
  not silently resolve: most existing records would hard-fail the
  evidence-marker check on day one (survey-round2.md's "Initial-friction
  constraint").
- **B**: kept, not rejected — `reexecution_gate` is the stronger check
  (round one's own sandbox pilot showed it catches what `claim_scan`
  alone misses, e.g. a claim citing a real-but-unrelated file). But
  running a SHA-pinned worktree re-execution synchronously inside a
  `PreToolUse` hook blocks every `gh pr create` call for however long the
  cited command takes to re-run — an operator-visible latency cost this
  round's assignment did not ask to be silently accepted. Scored below A
  and staged after it, gated on A's own rollout data (see H1b below).
- **C**: exists specifically as B's fallback, not scored independently
  high, because an async write to `.reexecution/` after the PR already
  exists changes `landing_readiness.py`'s `reexecution_blocking_cause()`
  from "blocks creation" to "blocks a later merge attempt" — a real
  design difference, not a minor variant, which is why it is not folded
  into B's row.
- **D — reject for this round**: a Stop-event hook fires at the end of
  *every* session, not only sessions that end in a claim-bearing `gh pr
  create`. It would need its own claim-detection pass independent of
  `pr-preflight.sh`'s chokepoint, duplicating detection logic the scout
  brief's must-be #1 explicitly warns against (no second copy of check
  logic — here the risk is two *chokepoints* each deciding independently
  whether a claim needs re-execution, which is a coordination problem
  A/B/C don't have). Revisit only if A's post-rollout data shows sessions
  routing around `gh pr create` entirely (e.g. pushing without ever
  calling `gh pr create` in a way `pr-preflight.sh` observes) — not
  ruled out as impossible, ruled out as this round's build target absent
  evidence that gap is real.

## Pre-registered hypothesis package

**H1-wiring (primary, this round).** If `claim_scan.scan_text()` is
invoked synchronously inside a new `PreToolUse` `Bash`-matcher hook that
fires on `gh pr create`/`gh pr edit` (candidate A), then the fraction of
qualifying claim-bearing PR bodies that reach `gh pr create` with zero
mechanized verdict ever attempted against them will fall from its current
measured value, because the chokepoint that already exists for a
structurally identical check (`pr-preflight.sh`) proves session-side
`Bash`-matcher hooks reliably intercept this exact call.

- **Metric**: `wiring_coverage_rate` = (qualifying `gh pr create`/`gh pr
  edit` invocations for which `claim_scan.scan_text()` was actually
  invoked, regardless of verdict) / (total qualifying invocations,
  "qualifying" = PR body matches `CLAIM_RE`), measured over the next 30
  qualifying invocations after the hook ships. This is deliberately a
  different metric from round one's `fabrication_survival_rate` — this
  round measures whether the trigger fires at all (the round's actual
  named gap), not whether the fired check's verdict is correct (round
  one's already-closed question per Findings 1-2). `fabrication_survival_
  rate` remains the round-one metric this round's fix is a precondition
  for, re-measured downstream once `wiring_coverage_rate` clears its own
  threshold.
- **Threshold**: `wiring_coverage_rate` ≥ 95% (round one's own H1
  threshold used 10%/90%-class bands; this round mirrors that scale — a
  wiring mechanism that fires on fewer than 95 of every 100 qualifying
  invocations has the same practical effect as round one's finding, a
  trigger nobody can rely on).
- **Guardrail metric**: `false_reject_rate` on the SAME chokepoint,
  carried forward unchanged from round one's registration (≤5%) — this
  round adds a trigger, it must not also silently tighten what counts as
  a violation beyond what `claim_scan` already decides.
- **Decision rule**: `wiring_coverage_rate` ≥ 95% AND `false_reject_rate`
  ≤5% → **go**, proceed to stage B (re-execution) on the same
  chokepoint. `wiring_coverage_rate` < 95% → **pivot**: the chokepoint
  itself is leaky (sessions bypass `gh pr create`/`gh pr edit` some other
  way — e.g. direct `git push` plus a manually-opened PR from outside the
  session) — widen the matcher or add a second chokepoint (candidate D
  becomes live evidence, not a guess) before declaring wiring
  insufficient. `false_reject_rate` > 5% → **kill-and-redesign**: same
  guardrail failure mode round one already named, punishing honest work.
- **Gaming-resistance argument**: the trigger fires on the `Bash` tool
  call itself (`gh pr create`/`gh pr edit` as typed), intercepted by the
  hook layer outside the session's own control — a session cannot skip
  the hook by choosing not to self-report, the same way it could skip a
  self-reported field. The check's *logic* (`claim_scan.scan_text()`)
  already has its own gaming-resistance argument from round one
  (independent of self-report); this hypothesis only adds "and it is
  guaranteed to run," not a new claim about the check's own strength.
- **Failure signature**: fails quietly if a session routes the claim
  through a call shape `pr-preflight.sh`'s existing matcher (and this
  hook's identical matcher) does not cover — e.g. `gh pr create` invoked
  via a wrapper script, or the PR body set through `gh api` directly
  instead of `--body`/`--body-file`. Named here so the architecture role
  is on notice: the matcher's coverage of call *shapes*, not just the
  `gh` subcommand name, is the thing that must be verified, not assumed.
  `pr-preflight.sh`'s own header already documents this exact gap for its
  own scope (fails open on non-matching command) — this hook inherits the
  same blind spot unless the architecture phase explicitly widens it.

**H1b (rollout-friction, gates B/staging).** Given survey-round2.md's
finding that most existing qualifying records would currently hard-fail
the evidence-marker check, immediate-enforce (deny on first violation)
risks the guardrail's own failure mode at scale — not fabrication being
punished, but the existing honest-but-differently-formatted record style
being punished, which reads to an operator as the tool breaking, not the
tool working.

- **Metric**: `warn_period_correction_rate` = (qualifying PRs during a
  fixed warn-only period that self-correct to include a passing evidence
  marker before landing, without ever being blocked) / (total qualifying
  PRs during the warn period).
- **Threshold**: ≥60% self-correct during a two-week warn-only period
  (hook emits `additionalContext`/stderr guidance, exit code stays
  non-blocking) before flipping to deny-mode.
- **Decision rule**: ≥60% self-correction → **go**, flip to deny-mode
  (candidate A's blocking form) after the warn period. <60% → **pivot**:
  the evidence-marker format itself may be under-documented, not just
  under-enforced — check `run.md`'s own record-format guidance before
  tightening enforcement further. This hypothesis is explicitly
  subordinate to H1-wiring: it governs *when* A becomes blocking, not
  *whether* A ships (A ships in warn-mode immediately regardless of this
  hypothesis's outcome — the wiring gap itself is unconditionally the
  target; only the fail-posture's timing is conditional).
- **Gaming-resistance argument**: a warn-only period cannot be "gamed"
  into permanent leniency by construction — the decision rule above fixes
  the flip-to-deny trigger as a date plus a measured rate, not a
  renewable extension a session or operator could keep deferring; this is
  the same no-moved-finish-line constraint role-handoff contract already
  imposes on this role's own pre-registrations, applied to the hook's own
  rollout.
- **Failure signature**: fails quietly if the warn period is extended
  informally (a hook config edit that keeps `deny=false` past the
  registered two-week mark with no corresponding record explaining why) —
  named here so the architecture/implementation phase's own record must
  cite this hypothesis's decision rule explicitly if it deviates from it.

## ITWWS (if this works we should ...)

If H1-wiring's `wiring_coverage_rate` clears threshold, extend candidate
A's chokepoint to also cover candidate B (synchronous re-execution) on
the SAME hook, rather than building B as a separate file — deferred to
the architecture phase (which chokepoint owns re-execution invocation is
an implementation-surface decision needing the actual hook runtime in
hand), not actioned here.

If H1b's warn period does not clear its threshold, the ITWWS is a
documentation fix to `run.md`'s evidence-marker guidance before any
further enforcement change — explicitly deferred, not actioned, because
it depends on H1b's own measured outcome.

## Out of scope

- Building candidate D (Stop-event chokepoint) this round — reject
  reasoning stated above; revisit only on A's own coverage-gap evidence.
- Editing `gates/claim_scan.py` or `gates/reexecution_gate.py`'s internal
  logic — round one's Findings 1-2 already closed that; this round is
  wiring only.
- Declaring round one's `fabrication_survival_rate` window closed or
  reset — this round's `wiring_coverage_rate` is a precondition metric,
  not a replacement; round one's window continues once wiring exists.

## How you'll know it worked

`docs/issue-476/proposals/discovery-round2.md` exists, is committed,
carries `status: proposed`; the sibling survey and scout brief exist and
are committed; both hypothesis packages (H1-wiring, H1b) state a named
metric, numeric threshold, and go/pivot/kill decision rule per this
role's own contract; every candidate (A-D) states a gaming-resistance
argument and a failure signature or an explicit reject reason citing one.
