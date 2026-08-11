---
code_under_review:
  - spawn.py
  - test_spawn.py
  - on-the-record/hooks/directive.sh
  - on-the-record/commands/consult.md
type: feature
breaking: false
verdict: pending
loop_state: landed
---

# Issue #699 — implementation record (phase 2)

## What was done

Delivered the approved phase-1 proposal
(`docs/issue-699/proposals/consult-and-goal-loop.md`, approved via issue
comment `APPROVE issue-699/implementation`) as one change:

1. `spawn.py`: added `consult_cmd(role, question, issue=None, cwd=None)`
   next to (not replacing) `spawn_cmd()`/`_spawn_one()`. It reuses
   `role_settings()` + `plugin_dirs()` for rulebook loading, assembles a
   bounded headless `claude -p --plugin-dir <role> --output-format json`
   run (`--permission-mode bypassPermissions`, `CONSULT_TIMEOUT=180s`,
   no branch/workspace/commit/PR/watcher/roster machinery), appends a
   prompt instructing the role to render its verdict as
   `{"answer", "confidence", "caveats"}` JSON, and parses that JSON out of
   the session's `result` text via `_parse_consult_verdict` (scans for the
   last `{...}` object that parses and carries an `answer` key, so prose
   before the JSON doesn't break extraction). A `finally` block calls
   `_append_consult_trace()` on every exit — success, malformed verdict,
   non-zero session return code, or `subprocess.TimeoutExpired` — before
   returning or re-raising, so a failed consult still leaves a trace line
   (`docs/issue-<n>/reports/consult-log.md` when `--issue` is given, else
   `docs/reports/consult-log.md`). Wired a `spawn.py consult <role>
   "<question>" [--issue N]` CLI entry point (added a third positional
   `consult_question` argparse argument, since `role`/`task` are already
   used as the subcommand-name/first-argument pair by `kill`/`watch`).
2. `test_spawn.py`: `ConsultCmd` — asserts an answer returns to the
   caller, asserts no `gh`/PR-shaped subprocess call happens, asserts a
   trace entry lands for both the issue-scoped and no-issue cases, and
   asserts a trace entry still lands when the invocation errors
   (malformed verdict, non-zero session exit, timeout) — mirroring the
   proposal's explicit success-and-failure trace requirement.
   `ConsultVerdictParsing` covers `_parse_consult_verdict` directly
   (prose-then-JSON, no object present, empty text). `PlainSessionDirectiveNorms`
   drives the shipped `on-the-record/hooks/directive.sh` as a subprocess
   with `CLAUDE_ROLE` unset and asserts the delegation-norm and
   goal-loop-norm wording is present; a second case with `CLAUDE_ROLE` set
   and a third with `ORCHESTRATE_OFF=1` assert the norms are absent —
   confirming the same `CLAUDE_ROLE`-unset gate the file already used for
   the orchestration directive now also gates the new norms.
3. `on-the-record/hooks/directive.sh`: added a "DELEGATION IS THE
   DEFAULT" paragraph (R2 — recognize a design/feasibility/risk/ambiguity
   judgment point, delegate it to `spawn.py consult <role> "<question>"`
   rather than deciding inline) and a "YOUR GOAL LOOP" paragraph (R3 —
   decompose the user's request into judgments and work, delegate each
   (consult for judgments, spawn for artifacts), integrate, continue to
   done or genuinely-user-blocked, report the delegation trace),
   appended inside the same heredoc the existing orchestration directive
   already emits — same `CLAUDE_ROLE`-unset / `ORCHESTRATE_OFF` gate, no
   new hook registration.
4. `on-the-record/commands/consult.md`: reference doc for `spawn.py
   consult`, mirroring `run.md`'s precedent as the plugin's other command
   file — syntax, what it does/does not do, and the trace guarantee.
5. `on-the-record/hooks/hooks.json`: left untouched, as the proposal's
   "What will be done" section allowed — the norm rides the existing
   `directive.sh` registration; no trace-completeness enforcement hook
   turned out to be needed for this delivery.
6. `docs/reports/consult-log.md`: created (see Rationale for deviations
   #2) so the no-issue trace path referenced by `directive.sh` and
   `commands/consult.md` is a reachable file, not a dangling reference.

## Why

Per the proposal's Rationale: reusing `role_settings()`/`plugin_dirs()`
under one new sibling function (rather than a second rulebook-loading
path, or injecting rulebook text into the caller's own context) keeps
exactly one rulebook-loading code path — the survey found no code path
anywhere that loads a role's rulebook into an already-running session,
and building one would reopen the same drift class issue #695/#700 had
to clean up once already for the spawn path. The delegation/goal-loop
norm went into `directive.sh` rather than `run.md` because the survey
confirmed `directive.sh` is the only surface that reaches every plain
session unconditionally on every prompt — `run.md` is reached only by an
explicit `/orchestrate:run` invocation and would miss a plain session
that never runs it, which is exactly what R2's acceptance check
("plain session … carries the delegation norm") requires.

## Upstream

Based on: `docs/issue-699/proposals/consult-and-goal-loop.md` (merged
proposal, PR #704), approved via issue-699 comment
`APPROVE issue-699/implementation`.

## What did not work

- Writing the no-issue consult trace to the exact path the proposal
  names for it (a bare file directly under `docs/`) — `board-gate.sh`
  refused the write: `docs/` under contract v3 s10 holds only
  `README.md`, the six standing buckets, and per-issue
  `docs/issue-<n>/` trees, and a bare filename directly under `docs/` is
  none of those. Moved the no-issue trace path into the `reports/`
  standing bucket instead — `docs/reports/consult-log.md` — see
  Rationale for deviations.

## Rationale for deviations

Two deviations from the proposal's exact wording, neither changing the
delivered mechanism's substance:

1. The proposal's "What will be done" describes `--output-format
   stream-json` for `consult_cmd`; this delivery uses `--output-format
   json` instead, matching the existing `session_result()` helper
   (`spawn.py`) which already parses the non-streaming JSON result object
   used by `_spawn_one()`'s post-processing — `stream-json` is a
   line-per-event log format meant for live tee'ing to a run log, which a
   consult (no live log, single bounded call, answer extracted from the
   final result text) has no use for. The proposal's own Constraints
   section states the goal as "captured directly by the calling process
   (no `_spawn_one()` branch/watch/PR machinery)"; `json` reaches that
   goal with less code than parsing a stream of JSON lines for the one
   final `result` event would.
2. The proposal names the no-issue trace path as a bare filename directly
   under `docs/`. Writing to that path during this delivery was refused
   by `board-gate.sh` (contract v3 s10, see "What did not work" above).
   `_consult_trace_path()` instead resolves the no-issue case to
   `docs/reports/consult-log.md` (the `reports/` standing bucket), which
   satisfies the proposal's own "no traceless consults" constraint while
   fitting the layout rule the proposal did not check against
   `board-gate.sh` at proposal time.

## Open findings

None known at delivery time.

## Next steps

None — R1/R2/R3 acceptance criteria are covered by the tests in this
delivery (`ConsultCmd`, `ConsultVerdictParsing`, `PlainSessionDirectiveNorms`).
Any follow-up (e.g. a mechanical gate enforcing the R2 norm, per the
proposal's Out of scope) is a new issue, not open work here.
