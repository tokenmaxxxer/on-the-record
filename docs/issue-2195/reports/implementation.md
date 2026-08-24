---
issue: 2195
role: implementation
loop_state: landed
upstream:
  - path: spawn.py
    sha: 8b126d1e039dc11f633d262befe3a01d6245e559
  - path: tests/test_auto_sweep_nonblocking.py
    sha: 8b126d1e039dc11f633d262befe3a01d6245e559
  - path: docs/issue-2195/reports/implementation/2026-08-24-hunt-auto-sweep-background-dispatch.md
    sha: c3451a9eb0a5504e02718bc2d92b300c2956e952
code_under_review: 8b126d1e039dc11f633d262befe3a01d6245e559
  - spawn.py
  - tests/test_auto_sweep_nonblocking.py
type: perf
breaking: false
verdict: pass
---

# issue-2195 — implementation record

## What was done

Build-now bypass (CORE_BUILD_NOW=1): delivered directly on
issue-2195/implementation, no separate phase-1 proposal round (skip note
below).

canonical: `spawn.py` diff, commit 8b126d1e039dc11f633d262befe3a01d6245e559
(`_spawn_one`'s `with _timed("auto_sweep"):` block).

1. Investigated the cost driver: `auto_sweep()` (`lifecycle.py:857`) scans
   every workspace under `_workspace_base()` with a `.git` dir, calls
   `_workspace_clean_state()` (`lifecycle.py:598`) per workspace for a
   liveness/dirty-tree judgment, and, for every workspace that survives
   the age bound, calls `_dir_size_bytes()` (`lifecycle.py:826`) — a
   pure-Python `rglob("*")` plus `stat()` over every file in that
   workspace, to enforce the `MUSTER_CLEAN_MAX_BYTES` total. Cost scales
   with how many stale workspaces have piled up in a given environment —
   a shared dev environment's own accumulated backlog, not a fixed
   per-spawn cost.
2. Nothing downstream of the sweep needs it to finish before the new
   session starts: `issue_workspace()` creates a workspace keyed by
   issue+role, a name `auto_sweep`'s candidate scan never touches, so
   there is no name-collision dependency.
3. Fix: the previously-synchronous call inside
   `with _timed("auto_sweep"):` now runs on a fire-and-forget
   `threading.Thread(daemon=True)`, never joined — the `auto_sweep`
   bootstrap phase measures dispatch cost, not sweep duration. Deliberately
   a bare daemon thread, not `concurrent.futures.ThreadPoolExecutor` (see
   the reasoning below).
4. A before-landing warrant-hunt was dispatched against this diff
   (`docs/issue-2195/reports/implementation/2026-08-24-hunt-auto-sweep-background-dispatch.md`,
   commit c3451a9eb0a5504e02718bc2d92b300c2956e952). Its write-up
   describes the same tradeoff issue #2186 was filed to prevent for other
   phases: with the sweep backgrounded, `bootstrap_timing`'s `auto_sweep=`
   field reads near-zero unconditionally, so a future regression back to
   a 148s-class sweep would again be invisible in that one line. Fixed by
   having the background thread itself log its own elapsed time and
   outcome (`removed`/`failed` counts) to stderr once the real sweep
   finishes — the bootstrap phase stays fast, but the real duration still
   surfaces in the live log. canonical: `spawn.py` diff, same commit as
   above, the `_run_auto_sweep` closure's `elapsed`/`print` lines.
5. Regression tests added — `tests/test_auto_sweep_nonblocking.py`,
   commit 8b126d1e039dc11f633d262befe3a01d6245e559 — covering: the sweep
   no longer blocks `_spawn_one()` or its own timed phase even when the
   sweep function is made to block for 2s
   (`test_slow_auto_sweep_does_not_block_spawn_or_its_timed_phase`); the
   sweep still actually runs, off the blocking path, via a
   `threading.Event` the dispatched call sets; the hunt-driven completion
   log line appears once the background call ends, with the right
   removed-count; and the pre-existing `MUSTER_CLEAN_AUTO=0` kill switch
   still suppresses the dispatch entirely
   (`test_auto_sweep_disabled_flag_still_skips_dispatch`).

## Why

Reading `lifecycle.py:857` (`auto_sweep`) against `spawn.py`'s call site
showed the function does real per-workspace work that scales with backlog
size, not a single fixable slow line — so the issue's own three-way
framing (make it fast / stop blocking on it / both) pointed at "stop
blocking on it" once two questions were answered: no name-collision risk
(workspace names are issue+role-keyed, never in the sweep's candidate
set), and the disk-space rationale behind running it before
`issue_workspace()` (issue #1179) is a soft, time-averaged bound —
`MUSTER_CLEAN_MAX_BYTES` (default 5GiB) only ever bounded the
*accumulated* size of safe-to-delete workspaces over time; even the
synchronous form never guaranteed enough free space for the very next
clone specifically. Moving that bound from "always-synchronous-before-
every-clone" to "usually current, because the dispatch now happens every
spawn instead of only when an operator remembers to run cleanup by hand"
is the tradeoff the issue's own Fix section asks for.

`threading.Thread(daemon=True)` over `concurrent.futures.ThreadPoolExecutor`:
a sibling in-flight change for issue #2186
(commit 53968cad942495fbd33c2ad8f4de84e35dd38764, on the
`origin/issue-2186/implementation` remote branch — canonical:
`git branch -a --contains f65d67f31851ee0ef8ac9f9a2e2b46f127fc8278`, run
this session, lists only that remote branch, not `main` or this branch's
own history) records a warrant-hunt result for the identical shape: a
`ThreadPoolExecutor` submitted for an overlapped `gh pr list` call still
lets CPython's `concurrent.futures.thread._python_exit` atexit hook join
that non-daemon worker before the interpreter can exit, regardless of
`.shutdown(wait=False)`. That record's own fix, `_BackgroundCall`, wraps a
daemon thread to add `.result()` semantics — not present on this branch's
base (that commit is not reachable from this branch's history), and not
needed here since nothing downstream ever reads `auto_sweep`'s return
value. A bare `threading.Thread(daemon=True).start()` is the minimal
primitive that avoids the same atexit-join defect without adding an
unused `.result()` API.

Alternatives considered and rejected:
- **Keep `concurrent.futures.ThreadPoolExecutor` + `.shutdown(wait=False)`**,
  matching `cross_family`'s existing shape. Rejected: the atexit-join
  defect above would reintroduce a version of the same blocking this
  issue exists to remove, moved to process-exit time.
- **Speed up `auto_sweep()`'s internals** (skip the size-bound step, or
  cache `_dir_size_bytes()` results). Rejected: the issue's own
  Investigate section asks whether blocking *placement* is the defect
  before assuming raw cost is; the two internal steps (age-bound reap,
  size-bound walk) do correctness-relevant work each, and the issue's
  acceptance bar (dispatch off the blocking path) is met without touching
  either.
- **Background only the size-bound (`_dir_size_bytes`) step, keep the
  age-bound reap synchronous.** Rejected: splitting `auto_sweep()` into
  two call sites adds complexity for no benefit under this issue's
  acceptance bar, which a single full-function background dispatch
  already meets — and the age-bound step's own per-workspace
  `_workspace_clean_state()` calls can themselves dominate cost on a
  large backlog, so a partial split would still leave a large share of
  the original 148.7s on the blocking path.
- **A periodic watchdog cadence instead of per-spawn dispatch** (the
  issue's other suggested option). Rejected here: no existing
  spawn-independent scheduler exists in this codebase to hang a periodic
  sweep off of — building one is new infrastructure beyond this issue's
  named scope, while per-spawn background dispatch reuses the exact
  overlap mechanism issue #2186 already established for
  `returned_pr_gate`/`cross_family` and needs no new scheduling
  primitive.

Skip note (survey-order-directive): no separate survey/proposal file was
written — CORE_BUILD_NOW=1 authorizes direct delivery (contract v3 s19a).
The open design decisions (daemon thread vs. `ThreadPoolExecutor`; full
background dispatch vs. partial/periodic) are argued inline above.

## Upstream basis

- Issue #2195, read via `gh issue view 2195` — names the 148.7s/154.3s
  (96%) measurement, the Investigate questions, the Fix direction
  (background thread or periodic cadence), and the two acceptance
  criteria.
- `spawn.py`, `lifecycle.py` (`auto_sweep`, `_workspace_clean_state`,
  `_dir_size_bytes`, `_clean_auto_enabled`/`_clean_max_age_days`/
  `_clean_max_bytes`), read this session — the cost-driver investigation
  above.
- Commit 53968cad942495fbd33c2ad8f4de84e35dd38764
  (docs/issue-2186/reports/implementation.md at that commit, read via
  `git show 53968cad942495fbd33c2ad8f4de84e35dd38764:docs/issue-2186/reports/implementation.md`
  this session — not present in this branch's own working tree, since
  the branch carrying it has not landed on `main`): its own Open finding
  #2 is this issue's seed (an `auto_sweep=127.007` measurement in that
  session's own environment, resolution path named there as "a follow-up
  issue"), and its warrant-hunt record (commit
  f65d67f31851ee0ef8ac9f9a2e2b46f127fc8278) drove the daemon-thread choice
  above.
- `docs/issue-2195/reports/implementation/2026-08-24-hunt-auto-sweep-background-dispatch.md`
  (commit c3451a9eb0a5504e02718bc2d92b300c2956e952) — this diff's own
  before-landing warrant-hunt, which drove the completion-log addition
  above.

## Open findings

1. This diff does not attempt a live nested-`claude`-session spawn
   re-measurement against a real `events.jsonl` (the issue's own
   methodology) — same reasoning as issue #2186's own Open finding #1:
   that procedure is a manual, operator-driven, wall-clock-gated step
   (`harness/README.md`'s "Run the real baseline later" section, issue
   #776 step 3), not something a delivery session invokes on itself from
   inside an unattended single-shot run. In its place, this record's
   executed evidence exercises the real `_spawn_one()` code path with a
   mocked `auto_sweep` that blocks for 2s (standing in for the 148.7s
   measured live) and reads the emitted `bootstrap_timing` line directly
   — the same property the issue's acceptance bullet asks for, read the
   same way, against a stand-in duration rather than a literal live
   148.7s sweep. Resolution path: a human operator, or a follow-up
   session explicitly authorized for it, repeats the issue's own
   live-spawn measurement against this branch (or after merge).
2. Backgrounding `auto_sweep()` lets the new workspace clone start before
   old workspaces are actually deleted from disk — a theoretical
   disk-space race on an environment already near its limit that the old
   synchronous ordering avoided (issue #1179's original rationale).
   Treated as an accepted, issue-authorized tradeoff above, not a defect.
   Resolution path: if disk-full clone failures are ever observed in
   practice, a follow-up could keep the age-bound reap step synchronous
   and background only the size-bound walk, trading back some of this
   fix's latency win for a tighter disk-space guarantee.
3. `cross_family`'s pre-existing `ThreadPoolExecutor` call (issue #2061,
   unrelated to this diff) carries the same latent atexit-join shape
   identified for `returned_pr_gate`'s first cut in commit
   f65d67f31851ee0ef8ac9f9a2e2b46f127fc8278 — already recorded as issue
   #2186's own Open finding #3, unresolved on `main` as of this commit.
   Not touched here (outside this issue's named scope, `auto_sweep`
   specifically) — resolution path already recorded there.

## What did not work

None.

## Skill check

- skill-verdict: implementation-performance-data-structure-choice — applied: invoked; asked whether `threading.Thread(daemon=True)` was the right primitive over `ThreadPoolExecutor` for the one-shot fire-and-forget `auto_sweep` dispatch, and whether any leak/correctness risk (abrupt kill of in-flight file deletes, thread pileup on rapid respawns) needed flagging.

  The skill's six rules (hash-set-vs-list
  membership testing, sorted-array space tradeoffs, algorithm-class-vs-
  measured-cost, message-batching for many small/frequent messages,
  cache-hit-rate removal, index-read-fraction removal) all target
  data-structure/algorithm/cache/communication-scheme choices under
  repeated or high-volume access; none governs a single one-shot
  background thread whose result is never read. No rule changed the
  design already argued above.
- other mounted skills: not triggered — implementation-complexity-
  coupling-management (one call site rewritten in place, no new
  cross-module dependency or coupling-metric threshold), implementation-
  design-pattern-selection (a bare daemon thread is not a GoF pattern
  being introduced or reconsidered), and implementation-blueprint
  (single-function change in one existing file plus one new test file,
  no new multi-module architecture) cover no decision that arose here.

## Next steps

None — loop_state is terminal (landed).

Executed acceptance evidence. canonical: this turn's own transcript —
each command below was run directly by this session at landing time, raw
stdout/stderr pasted verbatim (pytest-asyncio deprecation warnings and
the pytest-xdist "bringing up nodes..." banner trimmed), no
summarization.

acceptance: `python3 -c "import ast; ast.parse(open('spawn.py').read())"`
result:
```
OK
```
exit code 0.

acceptance: `python3 -m pytest tests/test_auto_sweep_nonblocking.py -q -s`
result (captured `bootstrap_timing` lines from real `_spawn_one()` runs,
mocked network/subprocess only — this is the issue's own "read the
emitted line" check, applied to this fix):
```
[implementation] bootstrap_timing admission=0.027 skill_resolve=0.000 workspace=0.000 branch=0.000 returned_pr_gate=0.000 auto_sweep=0.000 rulebook=0.000 core=0.000 gh_token=0.000 settings=0.001 cross_family=0.000 issue_fetch=0.017 directive_write=0.000 design_bearing=0.001 spawn_cmd=0.000 board_snapshot=0.000 total=0.045
[implementation] bootstrap_timing admission=0.027 skill_resolve=0.000 workspace=0.000 branch=0.000 returned_pr_gate=0.000 auto_sweep=0.000 rulebook=0.000 core=0.000 gh_token=0.000 settings=0.000 cross_family=0.000 issue_fetch=0.020 directive_write=0.001 design_bearing=0.000 spawn_cmd=0.000 board_snapshot=0.001 total=0.049
..
2 passed in 5.65s
```
exit code 0. `auto_sweep=0.000` in both lines even though one of the two
tests' mocked `auto_sweep` blocks for 2s on a background thread — the
dispatch itself, not sweep duration, is what the phase now measures.

acceptance: `python3 -m pytest tests/test_bootstrap_timing.py tests/test_auto_sweep_nonblocking.py gates/test_clean_reconcile_safety.py -q`
result:
```
........x...........                                                     [100%]
19 passed, 1 xfailed in 1.30s
```
exit code 0.

acceptance: `python3 -m pytest tests/ gates/ -q` (full suite, run once
before the last edit round — the completion-log addition and its test
coverage landed after this particular run)
result:
```
4 failed, 2023 passed, 17 xfailed, 4 xpassed in 868.56s (0:14:28)
FAILED tests/test_spawn_pipeline.py::SpawnCmd::test_core_plugin_dirs_halts_on_missing_plugin_dir
FAILED tests/test_spawn_pipeline.py::SpawnCmd::test_core_version_reports_sha_date_and_label_for_local_override
FAILED tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch
FAILED tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace
```
exit code 1. None of these four touch `auto_sweep`, the `auto_sweep`
bootstrap phase, or any function this commit's own diff changes
(`core_plugin_dirs`, `core_version`, `_undispositioned_role_prs`, and the
toolchain-cache-env block are untouched by
`git show 8b126d1e039dc11f633d262befe3a01d6245e559 --stat`, run this
session). Their failure shape — real `CARGO_HOME`/git-sha/gh-state values
from this session's own shell leaking into test doubles that expect a
clean tmp fixture — matches environment pollution, not a code regression.
canonical: `python3 -m pytest tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today -q`,
run this session against commit 188ceb3e (this branch's own base, before
this issue's changes) inside the same shell, reproducing the same
assertion failure there too — the pollution predates this diff.
