---
status: proposed
files:
  - docs/issue-2016/reports/performance-engineering/survey.md
  - docs/issue-2016/proposals/2026-08-22-single-session-profiling.md
---

# Single-session speed profiling (phase 1) — measurement-only, no fix landed this pass

## Request

Operator direction: "속도 더 최적화 가능하지 않나" (can we optimize speed
further). Architecture consult limited this to intra-session
optimization, no re-inflation of session count. Issue #2016 phase 1
scope: profile one representative single-phase role session end-to-end,
attribute real wall-clock to named buckets (boot, directive assembly,
per-tool-call gate/hook overhead, test tail, record/PR ceremony), name
the top-2 buckets, and write the profiling report. No optimization
edits in this phase — diagnose first.

## Constraints

- No session-count change (single-phase issues stay at one spawned
  session).
- No optimization edits this phase — measurement only.
- Numbers must be real, measured live where possible, or read from
  already-instrumented sources — no estimates presented as measurements.
- Scope limited to spawn.py, on-the-record/hooks/, scripts/, tests/,
  test/, docs/ per the issue.

## Rationale

Two measurement strategies were available: (a) instrument a brand-new
timing harness around spawn.py and the hook pipeline, or (b) use the
timing instrumentation and real session artifacts that already exist
(spawn.py's `_BOOTSTRAP_TIMING`/`_timed()` from issue #711, and this
repo's own session transcript logs) plus standalone live timing of the
actual hook scripts with representative payloads.

(a) was considered and rejected for this phase: building a new harness
would itself be an implementation change to spawn.py/hooks, which phase
1 explicitly forbids ("no optimization... diagnose-first"), and it would
duplicate instrumentation issue #711 already landed. It was also higher
risk of producing synthetic numbers that don't match what a real session
actually pays, defeating the point of gathering real numbers here.

(b) was chosen: it reuses landed instrumentation, reads real prior
session logs for the boot bucket (multiple independent respawns, same
result), and times the actual hook scripts standalone for the buckets
that have no built-in instrumentation (UserPromptSubmit, PreToolUse,
Stop). This is lower-risk (no code changes), directly measured (not
estimated), and its numbers are traceable to specific commands anyone
can re-run.

## What will be done

- Read the issue and its consult provenance (`gh issue view 2016`).
- Read `spawn.py`'s existing bootstrap timing instrumentation
  (`_BOOTSTRAP_TIMING`, `_timed()`, `_bootstrap_timing_line`) and pull
  real `bootstrap_timing` lines from existing session transcript logs.
- Read both hook layers' `hooks.json` (the `core` plugin and this
  repo's `on-the-record/hooks/`) to enumerate every script wired to
  `UserPromptSubmit`, `PreToolUse` (Bash-matched), and `Stop`; time
  each standalone against a representative event payload.
- Measure the fast test suite via this repo's own
  `.on-the-record/test-tiers.json` `fast` command and compare the
  total to the issue's own consult caveat figure.
- Write `docs/issue-2016/reports/performance-engineering/survey.md`
  attributing wall-clock to five named buckets, naming the top-2
  (test tail, per-tool-call gate/hook overhead), and flagging two open
  findings (Stop/UserPromptSubmit firing frequency across turns, and
  standalone-vs-harness timing floor).
- Write this proposal.

## Out of scope

- Any edit to spawn.py, hooks, or tests to reduce any bucket's cost —
  phase 1 is diagnose-only per the issue.
- Instrumenting a live multi-turn session to count actual
  UserPromptSubmit/Stop event frequency (flagged as an open finding for
  phase 2, not attempted here).
- Any change to session count or spawn cadence.

## How you'll know it worked

- `docs/issue-2016/reports/performance-engineering/survey.md` exists,
  attributes wall-clock to named buckets with real measured numbers
  (not estimates), and names the top-2 buckets, matching issue #2016's
  Acceptance check.
- No file outside the two listed in `files:` above is touched by this
  commit.
- If the top-2 buckets are judged worth fixing, that fix proposal is
  phase 2's job (after approval), not this commit's.
