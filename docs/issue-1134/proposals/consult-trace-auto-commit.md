---
status: proposed
files:
  - spawn.py
  - tests/test_gates.py
  - docs/issue-1134/reports/implementation.md
---

## Request

Consult traces (`docs/reports/consult-log.md` / `docs/issue-<n>/reports/consult-log.md`
and the `consult-raw-failures/` side files) are written by
`consult_cmd()` into the tracked tree with no landing path: nothing
commits them, so every orchestrator-side consult leaves the checkout
dirty and fails `t_rulebook_version_is_recorded`. Give these writes a
defined landing path — auto-commit or relocation, phase-1's call — while
keeping the "every consult traces exactly one line" invariant exactly as
it is today.

## Constraints

- The trace invariant (one line per consult attempt, success or failure,
  written unconditionally in `consult_cmd()`'s `finally`) must not
  weaken (issue requirement 2).
- northpole req#2 (docs/specs/northpole.md §2) requires deliverables to
  be "documented in the repo" — a trace visible only as local
  uncommitted state, or invisible because it's gitignored, does not
  satisfy that.
- A commit staging `docs/issue-<n>/reports/consult-log.md` or
  `docs/issue-<n>/reports/consult-raw-failures/*` must carry a `Subject:
  issue-<n>` trailer (role-handoff contract v3 s13) or the commit-time
  hook rejects it.
- Sequenced after #1123 (merged, PR #1136) — satisfied, per survey.

## Rationale

Chosen: auto-commit the trace file (and any raw-failure side file
written in the same call) from inside `consult_cmd()`'s `finally` block,
using a fixed message shape, mirroring the existing `approve-scope`
precedent (spawn.py:1367-1387: write, `git add`, `git commit -m
<fixed-shape message>`, revert the write on `CalledProcessError`).

Rejected alternative: relocate the trace files outside the tracked tree
(e.g. under a gitignored `.consult/` directory, matching #1110's fix for
`.orchestrate-monitor-alive/`). Rejected because northpole req#2 defines
a "record" as something documented *in the repo* so a new session or
person can pick up the work with zero onboarding — an untracked file
satisfies neither "in the repo" nor survives a fresh clone. #1110's
marker directory had no record value to begin with (a liveness flag);
consult-log.md and consult-raw-failures/ are exactly the record req#2
is talking about. Relocating them out of git would resolve the dirty-tree
symptom by deleting the requirement the issue itself cites.

Rejected alternative: commit only at spawn.py's top-level CLI entry point
(batch the trace commit alongside whatever else that invocation does),
rather than inside `consult_cmd()` itself. Rejected because `consult_cmd()`
is called from multiple sites (`_consult_or_record_error()`, the panel
degrade path, the direct CLI subcommand — spawn.py:4744, 4757+, 5086) and
pushing the commit responsibility out to each caller reintroduces the
exact drift class `_append_consult_trace()`'s own docstring already
warns against (one shared trace helper so writers can't diverge) — a
caller that forgets to commit reproduces this issue silently at a new
call site.

## What will be done

1. Add a `_commit_consult_trace(paths: list[Path], issue: int | None,
   role: str, outcome: str, cwd: str | None) -> None` helper in
   spawn.py, next to `_append_consult_trace()`. It `git add`s the
   trace-log path (and the raw-failure side file path, when one was
   written this call) and `git commit -m <message>`, where the message
   is `f"issue-{issue}: consult-trace ({outcome_word})"` when `issue` is
   not `None` (satisfying the `Subject: issue-<n>` trailer requirement),
   else `f"consult-trace ({outcome_word})"`; `outcome_word` is `"ok"` or
   `"error"`, derived from the same `outcome` string already passed to
   `_append_consult_trace()`.
2. Call `_commit_consult_trace()` from `consult_cmd()`'s `finally` block
   (spawn.py:4600-4604), immediately after `_append_consult_trace()`
   returns, passing the same `trace_path`, the `raw_path` local when the
   parse-failure branch set one this call, `issue`, `role`, and
   `outcome`. `cwd` is passed through from `consult_cmd()`'s own `cwd`
   parameter so the commit lands in the orchestrator's actual checkout,
   not always `ROOT`.
3. On `subprocess.CalledProcessError` from the `git add`/`git commit`
   step, do not raise past the `finally` block (a commit failure must
   not turn a trace-write success into a raised exception that shadows
   the consult's real outcome) — print a loud stderr warning naming the
   dirty path and the git error, and leave the write in place (unlike
   `approve-scope`, there is no matching "prior text" to revert to: the
   trace line is an append, not a full-file overwrite, so reverting it
   would either lose the just-appended line or require re-reading and
   truncating the file, both riskier than leaving one committable dirty
   line for the next call to pick up together with its own).
4. Extend `tests/test_gates.py` with a new gate function that runs
   `consult_cmd()` against a scratch git clone (mocked `claude` binary
   returning a canned success or failure JSON, matching the mocking
   pattern in gates/test_consult_json_parse.py) and asserts `git status
   --porcelain` is empty afterward while the trace file's last line
   matches the trace-line shape `_append_consult_trace()` writes today —
   covering both the acceptance criteria's first check and the
   already-existing `t_rulebook_version_is_recorded` (no code change
   needed there; it starts passing once the checkout stays clean).
5. Write `docs/issue-1134/reports/implementation.md` (phase-2 record) once
   phase 2 opens.

## Out of scope

- Changing `CONSULT_TIMEOUT`, the retry count, or anything else about
  consult's parse-failure handling — #1123 already covers that ground.
- Adding a commit step to `_append_panel_turn()` / the panel record path
  (spawn.py:4619-4634) — the issue and its acceptance criteria are
  scoped to `consult_cmd()`'s trace-log and raw-failure writes only; the
  panel path is a separate, pre-existing surface not named by this
  issue's requirements.
- Retrying a failed commit — the `finally` block already runs once per
  consult attempt (two attempts per `consult_cmd()` call before it
  gives up); adding commit-level retry logic is unrequested complexity
  for a failure mode (git identity/lock/disk) the approve-scope
  precedent already treats as a loud-failure, not a retry, case.

## Accumulation

This adds one more inline `subprocess.run(["git", ...])` call site to
spawn.py, joining the ones already at spawn.py:1374-1379 (approve-scope),
:5365, :5393, :5496-5507 and others surfaced in the survey's grep. It
does **not** add a bare new call site: `_commit_consult_trace()` is
itself the shared helper for this one — every future writer that needs
"write a tracked doc, then commit it with a fixed message" (trace logs,
raw-failure side files, and any future consult-adjacent record) calls
this one function rather than repeating `git add`/`git commit` inline.
If a third unrelated call site (outside consult) needs the same
write-then-commit shape later, that is the trigger to lift this into a
shared `_commit_tracked_write()` used by both `approve-scope` and
`consult_cmd()` — not done here because the two current occurrences
(spawn.py:1374-1379 and this proposal's new helper) differ enough in
their message-shape and rollback semantics (approve-scope reverts a
full-file overwrite; consult-trace cannot revert an append) that forcing
one signature now would be premature abstraction over a two-item set.

## How you'll know it worked

- `python3 -m pytest tests/test_gates.py::t_rulebook_version_is_recorded -q`
  passes on a checkout after a consult failure (acceptance criterion 2).
- The new scratch-clone gate test passes: a mocked consult (success and
  failure variants) leaves `git status --porcelain` empty while the
  trace line is present (acceptance criterion 1).
- `git log` on the scratch clone shows one commit per consult attempt,
  each carrying the fixed message shape and, when issue-scoped, the
  `Subject: issue-<n>` trailer.
