---
status: proposed
files:
  - spawn.py
  - gates/test_consult_gate_lib_env.py
---

## Request

Consult sessions are 100% broken: `terse.sh` (a UserPromptSubmit hook
loaded from the rulebook) fails to source its core dependency
`gate-lib.sh` and hard-blocks the prompt with a bash error; that error
text is captured as the "model output" and every downstream parse of
the judgment JSON fails. Fix the root cause in this repo's consult
generator; add a regression test; document the piece that cannot be
fixed here (a hard-block-vs-fail-open scope decision that lives in a
different repo).

## Constraints

- Skip-condition stated (survey-order-directive): pure bugfix, no
  design decision open — see `docs/issue-1141/reports/implementation/survey.md`
  (scout skipped accordingly).
- Requirement 2 of the issue (hooks must not hard-block on their own
  env breakage, scoped to non-PreToolUse hooks per the fail-closed
  scope decision) requires editing `terse.sh`'s own source guard in the
  `tokenmaxxxer-core` repo — outside this repo's write set. Out of
  scope here; documented as a cross-repo follow-up.
- No change to `spawn_cmd()` (the delivery-session path) — it already
  injects `CLAUDE_PLUGIN_ROOT_CORE` correctly (issue #182); this fix
  only closes the gap in `consult_cmd()`.

## Rationale

Considered widening `terse.sh`'s own bash fallback (in `tokenmaxxxer-core`)
to also probe a `core` sibling directory next to the rulebook checkout,
instead of touching `consult_cmd()`'s env at all. Rejected: that file
is outside this repo's write set (a separate GitHub repo, separate
issue tracker), and even if it were reachable, it would duplicate path-
resolution logic `consult_cmd()` already has correct machinery for via
`core_plugin_dirs()` — producing two competing resolution strategies
instead of reusing the one `spawn_cmd()` already proved correct for the
identical problem under issue #182.

Chosen approach: give `consult_cmd()` the exact one-line fix
`spawn_cmd()` already carries — inject `CLAUDE_PLUGIN_ROOT_CORE` from
`core_plugin_dirs()` into the subprocess env. Same mechanism, same
source of truth, zero new resolution logic.

## What will be done

- In `spawn.py`, inside `consult_cmd()`, resolve the `core` entry from
  `core_plugin_dirs()` (mirroring `spawn_cmd()`'s existing
  `core_dir = next(...)` lookup at spawn.py:4300) and inject it into
  the subprocess `env` dict as `CLAUDE_PLUGIN_ROOT_CORE`, so `terse.sh`
  and any other rulebook hook can locate `hooks/lib/gate-lib.sh`
  without falling back to the (broken) relative-path guess.
- Add `gates/test_consult_gate_lib_env.py`: a hermetic test using a
  fixture layout under `tests/fixtures/rulebooks/` (already present in
  this repo) that asserts the env `consult_cmd()` constructs for its
  subprocess resolves `hooks/lib/gate-lib.sh` under the injected
  `CLAUDE_PLUGIN_ROOT_CORE` path — reusing `gates/test_env_resolve.py`'s
  `resolve_core()` helper so this pins the exact same acceptance shape
  `spawn_cmd()` already has to meet, and cannot silently re-diverge.
  The test exercises `consult_cmd()`'s env-construction logic directly
  (no live network clone, no live `claude` process) — hermetic per the
  issue's acceptance criterion.

## Out of scope

- Editing `terse.sh` / `gate-lib.sh` in `tokenmaxxxer-core` (requirement
  2 of the issue) — different repo, different write set. Will be
  reported as a needed follow-up issue against `tokenmaxxxer-core` in
  this proposal's landing report, not filed from this session per the
  role-handoff contract (a role session does not spawn or file
  cross-scope work on its own initiative).
- The live re-run acceptance check (requirement 3, "live re-run of the
  exact failed question returns a verdict") is `provenance:
  executed-live` and runs at phase-2 delivery, not in this proposal.

## How you'll know it worked

- `python3 -m pytest gates/test_consult_gate_lib_env.py -v` passes,
  demonstrating the env `consult_cmd()` builds resolves
  `hooks/lib/gate-lib.sh` under a fixture rulebook layout, and fails
  (red) against the pre-fix code (env dict missing
  `CLAUDE_PLUGIN_ROOT_CORE`).
- At phase-2 delivery: a live consult re-run of the exact question from
  `docs/reports/consult-raw-failures/2026-08-13T022231.0588190000-1.txt`
  returns a parsed verdict JSON, with the consult trace line showing
  `ok` — quoted verbatim in the phase-2 record per the executed-live
  provenance requirement.

## Accumulation

This is a one-shot parity fix, not a repeated-shape accumulation: it
adds exactly one `CLAUDE_PLUGIN_ROOT_CORE` injection to the one other
subprocess-spawning function in `spawn.py` (`consult_cmd()`) that was
missing what `spawn_cmd()` already has. There is no list this grows —
`spawn.py` has exactly two functions that construct a `claude`
subprocess env (`spawn_cmd()`, `consult_cmd()`); after this change both
carry the same core-root injection and the drift class this issue
found cannot recur between them. If a third subprocess-spawning
function is added later needing the same env var, that is a new,
separate one-line change at that time, not an instance of a recurring
list this proposal is establishing.
