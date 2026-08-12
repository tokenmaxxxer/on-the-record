---
status: proposed
files:
  - spawn.py
  - tests/test_spawn.py
---

# Fix panel live-fire defects (#1045)

## Request

The first live `panel_cmd()` run (#973 measurement) found two defects:
(1) the two judge sessions never exchanged a `SendMessage` round-trip and
the run degraded to sequential consults every time; (2) the degrade path
itself crashes when the fallback `consult_cmd()` call fails (e.g. the model's
output has no parseable judgment JSON) — a panel run must never raise, only
record the failure.

## Constraints

- No new dependency, no new env var, no schema/migration.
- Write set stays inside `spawn.py` and `tests/test_spawn.py` — no touching
  `_run_panel_session()`'s transport shape (the `claude -p` invocation
  itself), only its prompt text and `_panel_degrade()`'s error handling.
- Existing `run_session` injection seam in `panel_cmd()` stays the test
  boundary — no real `claude -p` process in the regression tests.

## Rationale

For defect 1, the survey's bounded live reproduction
(docs/issue-1045/reports/implementation/survey.md) showed the
`ListAgents`/`SendMessage` primitive itself bridges two independently
`subprocess.run`-launched `claude -p` sessions successfully when the calling
session (a) polls `ListAgents` with retries instead of calling it once, and
(b) addresses the peer using the name `ListAgents` actually returns rather
than a role name. `_run_panel_session()`'s current prompt does neither.

Rejected alternative: fall back to an orchestrator-relayed "mailbox" file
exchange instead of live `SendMessage` (the option #973's product-discovery
scored as (c)). Rejected because the reproduction shows the live primitive
works once addressed correctly — downgrading to a file relay would give up
req#5's "live discussion" requirement to work around what the evidence shows
is a prompting defect, not a transport failure.

Rejected alternative for defect 2: only retry `consult_cmd()` once on
failure before giving up, instead of always catching and recording.
Rejected because a retry adds latency and complexity for no evidence it
helps transient failures (the observed failure — no judgment JSON in
output — is a parsing/prompt-adherence issue, not a flaky-network issue a
retry would fix); catching and recording is also what the mission statement
demands directly ("must never crash, it must record the failure and return
a degraded result").

## What will be done

1. `_run_panel_session()`'s judge prompt (spawn.py, lines 4479-4490) gets
   three additions: (a) instruct the model to call `ListAgents` first and
   retry a few times (sleep + re-check) if the peer session isn't visible
   yet — near-simultaneous `ThreadPoolExecutor` launch means the peer may
   not have registered its inbox on the first check; (b) instruct it to
   address `SendMessage` using the name `ListAgents` actually returned, not
   the literal `peer_role` string; (c) keep everything else (position →
   rebuttal → final JSON verdict shape) unchanged.
2. `_panel_degrade()` (spawn.py, lines 4517-4529) wraps each `consult_cmd()`
   call so a raised exception is caught, appended to the panel record as a
   `consult-error` turn, and turned into a `(verdict=None, error=<message>)`
   pair instead of propagating. The function's return dict gains `error_a`/
   `error_b` keys (both `None` on success) alongside the existing
   `verdict_a`/`verdict_b`.
3. Regression tests added to `tests/test_spawn.py` (new `PanelDegradeErrorSafety`
   class): a consult failure inside `_panel_degrade()` is recorded as a turn
   and returned as an error result without raising; one side failing still
   returns the other side's real verdict; `panel_cmd()`'s own
   no-round-trip-observed degrade trigger doesn't propagate a consult
   failure either.

## Out of scope

- Changing `_run_panel_session()`'s subprocess invocation shape, timeout, or
  settings construction.
- A live end-to-end `panel_cmd()` re-run against real `claude -p` judge
  sessions as part of this PR (expensive, non-deterministic wall-clock;
  the bounded primitive-level reproduction in the survey is the evidence
  this proposal builds on). A follow-up live re-run to confirm the prompt
  fix specifically is noted as a next step, not done here.
- Any change to `consult_cmd()` itself — its existing raise-on-failure
  contract is correct for its own callers (`_panel_degrade()` is the one
  caller that must not let it raise).

## Accumulation

Neither change adds a new inline `subprocess`/`gh` call site or a repeated
per-file edit shape. `_panel_degrade()` already calls `consult_cmd()` twice
(one per judge role) before this change; the fix wraps those same two
existing call sites in a helper (`_consult_or_record_error()`) rather than
adding new ones — a third judge role, if ever added, would call the same
helper a third time, not duplicate the try/except inline. The prompt-text
edit touches one string literal in one function; it does not repeat per role
or per file. Nothing here scales with N in a way that needs a shared helper
it doesn't already have.

## How you'll know it worked

- `python3 -m pytest tests/test_spawn.py -k panel` passes, including a case
  that seeds a `consult_cmd()` failure into `_panel_degrade()` and asserts
  no exception escapes and the failure is recorded.
- Reading `_run_panel_session()`'s prompt text confirms it now instructs
  `ListAgents`-based discovery with retry and peer addressing by the
  discovered name, not a hard-coded role string.
