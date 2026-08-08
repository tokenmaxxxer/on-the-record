# Survey — issue-535 (turn-budget rules)

Scope: locate the orchestration contract surfaces named by the issue —
`/orchestrate:run` and the UserPromptSubmit hook text — and find what they
currently say about foreground vs background execution.

## Files found

- `on-the-record/commands/run.md` (526 lines) — the `/orchestrate:run`
  slash command body, the full orchestration contract.
- `on-the-record/hooks/directive.sh` (118 lines) — the UserPromptSubmit
  hook; prints a condensed reminder of the same contract into every prompt.

## What already exists (bounded patterns to extend, not invent)

- `run.md` step 4 already mandates background spawn for role sessions
  ("반드시 백그라운드로", line 83-87) and `directive.sh` restates it
  (line 69-70, `run_in_background: true`, "a role session runs for
  minutes and the conversation must not block on it").
- `directive.sh` lines 74-90 already define a bounded-wait primitive:
  `spawn.py watch --issue <n>` returns early at the first material event
  or after `--stall-timeout` minutes (default 5), and mandates re-arming
  after every non-terminal event — this is the turn-budget pattern the
  issue wants generalized, already proven for the single case of watching
  one role session.
- `run.md` line 375-378 (streaming landing) says fan-out results are
  processed as they arrive, "라운드 단위로 모았다가 한꺼번에 처리하는 것이
  아니라" — an existing anti-batch-barrier norm for role-session fan-out,
  but it is scoped to role-session reconcile/watchdog signals, not to the
  orchestrator's own foreground tool-call chains.

## What is thin / missing (the gap the issue names)

1. **No explicit foreground-duration budget.** Nothing in either file says
   "if an operation is expected to take >~30s, background it." The
   existing background mandate (step 4) is scoped to *role sessions*
   only — it says nothing about the orchestrator's own multi-step
   sequences (e.g. `gh pr checks` + `gh pr merge` + board re-read across
   several issues, or `gates/landing_readiness.py` runs, or `gates/*.py`
   local verification runs mentioned in run.md lines 416-423).
2. **Watchdog cadence is framed as "직접 돌아라" without a background
   framing.** `run.md` lines 513-522: "세션이 살아있는 동안 10-15분
   간격으로 ... watchdog 을 스스로 돌려" — this reads as the orchestrator
   polling in-band on its own initiative, with no statement that this
   polling must not occupy a blocking foreground turn. This is the
   clearest instance of language that *permits* (without requiring) a
   long/blocking pattern.
3. **Step 6 (merge acceptance) sequences multiple `gh` calls
   (`gh pr checks`, `gh pr merge`) per queued decision item, and the
   decision queue itself can hold N items** (line 234-245) processed in
   one reply — no statement that a batch of N mechanical merges should be
   scripted into one background command rather than N sequential
   foreground `gh` calls.
4. **No closing statement that a reply should end the turn once
   remaining work is armed in background** — the "turn ends, notification
   drives the next turn" shape is implicit in the watch/re-arm loop
   (directive.sh 74-90) but never stated as a general default for *all*
   multi-step foreground work, only for watching spawned role sessions.

## Write set (frozen for the proposal)

- `on-the-record/commands/run.md` — add a turn-budget section covering
  the three fix-direction items from the issue, cross-referencing the
  existing watch/re-arm and streaming-landing patterns rather than
  duplicating them.
- `on-the-record/hooks/directive.sh` — extend the injected reminder with
  a short turn-budget line so the rule is refreshed every prompt (per the
  hook's own stated design rationale, hooks.sh:2-6: "steering must be
  freshly read to steer").
- the phase-2 implementation record, written only after approval, per
  contract v3 s19 (phase-1 only in this pass).

No dependency, schema, or migration surface is touched — this is a
contract-text-only change.

## Scout-directive skip record

Skip condition applied: **the spec leaves no meaningful design decision
open for external benchmarking.** This is an internal AI-orchestration
harness's own operating contract, not a product-facing surface with a
comparable category of "best-in-class" external products to scout. The
one directly relevant reference point — how bounded/early-return waiting
should look — already exists inside this same codebase
(`directive.sh` 74-90's `spawn.py watch --stall-timeout`), and the
proposal's approach is to generalize that existing, already-adopted
pattern rather than import an external one. No web scouting was run.
