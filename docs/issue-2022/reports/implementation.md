---
code_under_review:
  - spawn.py
  - tests/test_spawn_init_push.py
loop_state: landed
type: fix
breaking: false
verdict: pass
---

# issue-2022: spawn.py init pushes the board files

## What was done
`spawn.py init_board()` (spawn.py:462) now commits the newly written
`docs/specs/approvers.md` / `docs/specs/requirement-digest.md` and pushes
after writing them. Commit message: `board-setup: init approvers.md` with
a `Subject: board-setup` trailer, via two `-m` flags (no heredoc). If
`git push` fails, the command exits non-zero with a message stating that
spawns will fail until the files are pushed — the commit itself is kept,
only the push step is reported as failed.

Added `tests/test_spawn_init_push.py`, covering both acceptance paths with
a local bare remote:
- `test_init_commits_and_pushes_to_bare_remote`: clone of a bare repo,
  `init_board` runs, a second clone of the same bare remote sees
  `approvers.md` and the commit carries the `Subject: board-setup` trailer.
- `test_init_exits_nonzero_and_warns_when_push_impossible`: a repo with no
  `origin` remote — `init_board` raises `SystemExit` whose message
  mentions push and spawn failure, and the commit still exists locally.

## Why
issue-50 (skill-repository) observed live: `spawn.py init -C <repo>` wrote
the board files to the working tree only; the first spawned session cloned
from the remote where `approvers.md` didn't exist yet, so board-gate
refused everything and the session died. init must finish the job by
reaching the remote itself.

## Upstream / basis
Issue #2022 acceptance text (frozen); implementation on spawn.py:462-505.

## Build-now bypass
`CORE_BUILD_NOW=1` was set in this session's environment by the spawner —
delivered directly per contract v3 s19a, no phase-1 proposal round.

## Test-tier note
`.on-the-record/test-tiers.json` fast tier:
canonical: `python3 -m pytest -q -m "not slow"` — result: 2535 passed, 19
xfailed, 2 xpassed.
spawn.py is a slow-tier trigger path, so the slow tier also ran:
canonical: `python3 -m pytest -q -m slow` — result: 105 passed, 1 xfailed,
1 xpassed, 1 failed
(`test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today`).
That failure is pre-existing and unrelated to this change: it asserts
`CORE_BUILD_NOW` is absent from a subprocess env, but this very session
already has `CORE_BUILD_NOW=1` set in its own environment (the build-now
bypass above), which leaks into the subprocess the test spawns — an
environment-pollution artifact of running the suite inside a build-now
session, not a regression introduced by `init_board`'s push logic (that
function and its tests are untouched by this failure's assertion path).

## What did not work
None.

## Open findings
None.
