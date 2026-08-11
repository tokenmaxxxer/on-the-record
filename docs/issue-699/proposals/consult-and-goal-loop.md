---
status: proposed
files:
  - spawn.py
  - test_spawn.py
  - on-the-record/hooks/directive.sh
  - on-the-record/hooks/hooks.json
  - on-the-record/commands/consult.md
  - docs/issue-699/reports/implementation/survey.md
  - docs/issue-699/proposals/consult-and-goal-loop.md
---

## Request

Issue #699 phase 1: survey the deployed directive surface, then propose as
one design the three requirements the operator stated:

- R1 — a role invocation can return its judgment directly to the asking
  session (a "consult") without the full issue -> spawn -> PR pipeline,
  while still leaving a trace on the record trail.
- R2 — every plain (non-orchestrator) session with on-the-record installed
  gets a standing norm to recognize judgment points and delegate them to
  the matching role instead of deciding inline.
- R3 — the session owns the goal loop: decompose the user's request into
  judgments and work, delegate each (consults for judgments, spawned roles
  for artifacts), integrate, drive to done or genuinely-blocked, report
  with the delegation trace — composing with, not duplicating, the
  existing `/orchestrate:run` flow.

## Constraints

- The survey (`docs/issue-699/reports/implementation/survey.md`) found: the
  only hook that already reaches every plain session unconditionally is
  `on-the-record/hooks/directive.sh` (UserPromptSubmit, gated solely on
  `CLAUDE_ROLE` being unset); the only code path that ever activates a
  role's rulebook is `spawn.py`'s `role_settings()` + `spawn_cmd()`, which
  always builds a full headless `claude -p --plugin-dir <role>` process;
  there is no in-process rulebook injection anywhere in the repo.
- Issues #695 and #700 already settled that enforcement for headless role
  sessions lives on hooks (PreToolUse `exit 2`), not on sandbox or
  permission-mode — `spawn_cmd()` runs headless sessions with
  `--permission-mode bypassPermissions` unconditionally (survey, Prior art
  section). Any new consult path that spawns a session must inherit this,
  not reopen the sandbox/permission debate.
- `deliverable-guard.sh` already denies a plain (orchestrator-shaped)
  session from writing `src`/`test`/`tests`/`docs` deliverables directly —
  a consult answer is a judgment returned as text, never a file write by
  the caller, so it must not need write access to those trees to work.
- "No traceless consults" (operator decision, issue text) — every consult,
  successful or not, must leave a durable record entry, not just an
  in-conversation string.
- Must not duplicate `/orchestrate:run`'s issue -> spawn -> PR flow; a
  consult is additive to it, not a replacement path for deliverable work.

## Rationale

**Chosen approach:** add a `consult` subcommand to `spawn.py` that reuses
the existing rulebook-loading path (`role_settings()`, `plugin_dirs()`)
but calls a new, smaller assembly than `spawn_cmd()` — a bounded, headless
`claude -p --plugin-dir <role>` run whose prompt is the caller's question
plus a "render your verdict as JSON `{answer, confidence, caveats}`, do
not create branches/commits/PRs" instruction, `--output-format
stream-json` captured directly by the calling process (no `_spawn_one()`
branch/watch/PR machinery), with the raw Q/A appended as one line to a new
per-repo trace file (`docs/consult-log.md`, or `docs/issue-<n>/reports/
consult-log.md` when an issue is in scope) before the answer is returned.
`directive.sh` gets an added paragraph (still gated on `CLAUDE_ROLE`
unset, i.e. every plain session) stating the delegation norm — recognize
a design/feasibility/risk/ambiguity judgment point, call `spawn.py
consult <role> "<question>"` before deciding it inline — and the
goal-loop norm (decompose -> delegate each judgment/artifact -> integrate
-> continue until done or user-blocked -> report the delegation trace),
explicitly framed as nesting inside the existing orchestrate loop: a
consult stays inside one exchange of `/orchestrate:run`'s "your loop"
section, only a deliverable still needs the full spawn -> PR path.

**Rejected alternative 1 — inject the role's rulebook text into the
asking session's own context (a "load, don't spawn" consult), instead of
spawning a new headless process.** This was the first design considered
because it would avoid a second process's latency/cost entirely. Rejected
because the survey found no code path anywhere that loads a role's
rulebook into an already-running session — the only realized mechanism is
build-settings-then-spawn-a-new-process with `CLAUDE_ROLE` set
(`role_settings()`'s own docstring: "turning the rulebook on doesn't
happen here — that's `--plugin-dir`'s job"). Building in-session injection
would mean maintaining two divergent rulebook-loading paths (the existing
spawn path and a new injection path) that must stay behaviorally
consistent — the same class of drift issue #695/#700 already had to clean
up once for the spawn path alone. Reusing `role_settings()`/
`plugin_dirs()` under a new bounded spawn keeps exactly one rulebook-
loading code path.

**Rejected alternative 2 — fold the delegation/goal-loop norm into
`on-the-record/commands/run.md` instead of `directive.sh`.** `run.md` is
prose reached only when a user or session explicitly invokes
`/orchestrate:run`; the survey found it is the sole file under
`on-the-record/commands/`, written as one continuous issue-to-PR
procedure. Putting R2/R3's norm there would satisfy R3's composition
requirement (it already is the orchestrate loop's home) but would fail
R2's actual acceptance check: "test renders the deployed directive surface
for a plain session and asserts the delegation norm and goal-loop wording
are present" — a plain session that never runs `/orchestrate:run` (or
runs it, then continues past its explicit scope) would not see the norm.
`directive.sh` is the one surface the survey confirmed reaches every
plain session unconditionally on every prompt; the goal-loop framing text
in it points to `run.md`/spawn's PR path for the deliverable half exactly
as `directive.sh` already does today for the existing orchestration
directive, so the norm still composes with rather than re-narrates
`run.md`.

## What will be done

- `spawn.py`: add `consult_cmd(role, question, issue=None, cwd=None)` next
  to (not replacing) `spawn_cmd()`/`_spawn_one()`. It calls
  `role_settings()` + `plugin_dirs()` for rulebook loading, assembles a
  bounded headless invocation (`--permission-mode bypassPermissions`, no
  branch/commit/PR steps, a question-answering prompt template appended
  with the caller's question, `--output-format stream-json`), runs it
  in-process (subprocess, captured, not backgrounded — the caller gets the
  answer before returning), and appends one trace line (`timestamp, role,
  issue (or "none"), question, answer-summary-or-error, trace-file`) to
  `docs/consult-log.md` (or `docs/issue-<n>/reports/consult-log.md` when
  `--issue` is given) **inside a `finally`/error-handling path that runs
  before the function returns or re-raises, on every exit — success,
  malformed/non-JSON verdict, or subprocess crash/timeout alike** — so a
  consult that fails before verdict-parse still leaves a trace entry
  (recorded as an error outcome, not silently dropped); only after the
  trace write does it return the parsed answer to the caller, or raise.
  Wire a CLI entry point (`spawn.py consult <role> "<question>" [--issue
  N]`) alongside the existing `spawn`/`watch`/`flows` subcommands.
- `test_spawn.py`: unit-test `consult_cmd` — asserts it returns an answer,
  asserts no branch/PR is created, asserts a trace-log entry is appended
  in both the issue and no-issue cases, **and asserts a trace-log entry is
  still appended when the invocation errors (subprocess failure or
  malformed verdict), not only on the success path** — the warrant-hunt
  dispatched against this proposal (`docs/issue-699/reports/
  hunt-consult-and-goal-loop.md`) found the success-only wording
  contradicted this proposal's own "no traceless consults" constraint.
  This is also the check the issue's acceptance section names for R1.
- `on-the-record/hooks/directive.sh`: add the R2 delegation-norm paragraph
  and the R3 goal-loop-norm paragraph to the text already injected on
  every plain-session prompt (same `CLAUDE_ROLE`-unset gate the file
  already uses) — decompose the request, delegate judgments to
  `spawn.py consult`, delegate artifacts to `spawn.py spawn`/
  `/orchestrate:run`, integrate results, continue to done or a
  genuinely-user-blocked stop, report naming which judgments went to which
  role and what each returned.
- `on-the-record/hooks/hooks.json`: no new hook is added (the norm rides
  the existing `directive.sh` registration) — this file is listed only in
  case adding the norm as a paragraph rather than a fresh hook script
  turns out, during the build, to need its own PreToolUse/Stop entry for
  trace-completeness enforcement; if it is not needed, phase 2 leaves it
  untouched and says so explicitly rather than editing it speculatively.
- `on-the-record/commands/consult.md`: a short reference command doc
  (mirroring `run.md`'s precedent as the only prior command file) that
  documents `spawn.py consult` for a human or session that wants the full
  syntax/behavior rather than just the injected directive-text summary.
- `docs/issue-699/reports/implementation/survey.md`,
  `docs/issue-699/proposals/consult-and-goal-loop.md`: this survey and
  this proposal, already written as phase-1 output.

## Accumulation

`consult_cmd`'s headless-invocation assembly (permission-mode flags,
plugin-dir loop, stream-json capture) is a second copy of a subprocess
shape already built once in `spawn_cmd()`. This proposal keeps that
duplication to one sibling function reusing `role_settings()`/
`plugin_dirs()` rather than inlining a third ad hoc subprocess/`gh` call
site — if a third distinct headless-invocation shape (beyond
`spawn_cmd()` and `consult_cmd()`) is ever proposed, it should factor the
shared argv/env assembly into one helper both call, instead of adding a
third inline copy. `roles/*.json` is not touched by this proposal (no new
per-role field), so the repeated-file-edit half of this gate's concern
does not apply here.

## Out of scope

- Changing `spawn_cmd()`/`_spawn_one()`'s existing deliverable-role
  pipeline (branch/PR/watch) — R1's consult path is additive, not a
  replacement.
- Changing `delegated-judgment-gate.sh`'s merge-time panel-consensus
  mechanism (issue #573) — it answers a different question (auto-approve
  a candidate PR) and is left untouched.
- Any change to `/orchestrate:run` (`run.md`)'s existing mission-board,
  execution-plan, or turn-budget sections.
- Enforcement of the R2 delegation norm beyond directive text (e.g. a
  gate that mechanically blocks an inline judgment) — the issue's
  acceptance section for R2 asks only that the directive text reach plain
  sessions, not that inline judgment become impossible; a follow-up issue
  can propose a mechanical gate once the norm's wording has been in use.
- The `docs/issue-699/reports/hunt-consult-and-goal-loop.md` warrant-hunt
  record — produced by the dispatched hunter, not authored here.

## How you'll know it worked

- R1: `test_spawn.py`'s new `consult_cmd` test invokes a role consult on a
  fixture question, asserts an answer returns to the caller, asserts no
  PR is opened (no `gh pr create` call made), and asserts a trace-log
  entry exists for the call — matching the issue's stated acceptance
  check verbatim — plus a second case asserting the trace-log entry still
  exists when the fixture invocation is made to error before verdict-parse
  (see the trace-write-on-every-exit fix in "What will be done").
- R2: a test that renders `directive.sh`'s injected text for a plain
  (`CLAUDE_ROLE` unset) session and asserts both the delegation-norm
  wording and the goal-loop wording are present, and — as a negative
  check — that a role session (`CLAUDE_ROLE` set) still does not receive
  either paragraph (the existing early-exit stays intact) — matching the
  issue's stated acceptance check for R2.
- Manual/CI: `spawn.py consult <role> "<question>"` run against a fixture
  role returns a parsed answer on stdout/return value within the phase-2
  build's own smoke run, and `docs/consult-log.md` (or the issue-scoped
  variant) shows the corresponding entry afterward.
