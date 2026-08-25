---
issue: 2417
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: docs/issue-2417/reports/implementation/2026-08-26-hunt-disk-inode-exhaustion-fix.md
    sha: same-commit
code_under_review:
  - spawn.py
  - watchdog.py
  - tests/test_spawn_pipeline.py
  - tests/test_spawn_observation_recovery.py
type: fix
breaking: "none — new checks are additive (sys.exit on a path that would otherwise fail differently later) and overridable (MUSTER_SKIP_SPACE_CHECK=1, MUSTER_MIN_FREE_BYTES, MUSTER_MIN_FREE_INODES)"
verdict: pass
---

# issue-2417 — implementation record

Build-now bypass (contract v3 s19a): `CORE_BUILD_NOW=1` was set by the
spawner. No phase-1 proposal/survey/scout round for this delivery — went
straight to build on `issue-2417/implementation`.
canonical: `printenv | grep CORE_BUILD_NOW` at session start —
```
CORE_BUILD_NOW=1
```

## What was done

Four changes in `spawn.py` / `watchdog.py`, all under `issue_workspace()`
(spawn.py) and `roster_watchdog()` (watchdog.py):

1. **Pre-flight capacity check** (`_spawn_capacity_check()`, spawn.py):
   checks `shutil.disk_usage()` (bytes) and `os.statvfs()` (inodes) against
   `MIN_FREE_BYTES_DEFAULT` (~357MB) / `MIN_FREE_INODES_DEFAULT` (1000)
   before any of `issue_workspace()`'s three branches (self-reuse,
   workspace-reuse, fresh clone) touches disk — `git clone` or
   `_fetch_or_halt`. Refuses via `sys.exit()` naming the actual free
   space/inodes and the threshold. Overridable per-consumer via
   `MUSTER_SKIP_SPACE_CHECK=1` (off) or `MUSTER_MIN_FREE_BYTES=`/
   `MUSTER_MIN_FREE_INODES=` (change the threshold).
2. **watchdog tempdir resilience** (`roster_watchdog()`, watchdog.py): the
   per-live-entry `checkpoint.checkpoint_workspace(work)` call is now
   wrapped in `try/except OSError` — on failure it counts an anomaly,
   prints `[checkpoint] <key>: ... (계속 진행)`, and the tick continues to
   that entry's other diagnostics and the rest of the roster instead of
   the exception reaching the CLI's outer `except Exception: return
   WATCHDOG_CRASH_SENTINEL` (rc=97) handler.
3. **Incomplete-clone reclassification** (`_workspace_clone_incomplete()`,
   spawn.py): before the pre-existing origin-mismatch check (which fires
   whenever a workspace path already has a `.git` dir), a new check asks
   whether `git rev-parse --verify -q HEAD` fails or `git status
   --porcelain` errors. If so, the workspace is reported as an incomplete
   clone (names the likely cause and the remedy — `rm -rf` and retry)
   instead of falling into the existing "작업 경로에 다른 레포가 있다
   (origin 불일치)" `sys.exit`. A workspace that passes this check (has a
   real HEAD, `git status` runs clean) still goes through the unchanged
   origin-mismatch identity check below it.
4. **Buried clone error**: no separate code change — pre-empted by (1).
   In the disk-full case the capacity check now refuses before `git
   clone`/`_fetch_or_halt` ever runs, so the buried multi-line git stderr
   this bullet in the issue names is simply never reached for that cause.
   The clone-failure `sys.exit` itself (spawn.py, unchanged) still exists
   for genuine non-space clone failures (auth, network, etc.).

Regression/new-behavior tests added to the existing suites (no new test
files). Full names, derived from a real collection run:
derived: `python3 -m pytest tests/test_spawn_pipeline.py tests/test_spawn_observation_recovery.py -k "SpawnCapacityCheck or WorkspaceIncompleteCloneNotOriginMismatch or test_roster_watchdog_survives_checkpoint_workspace_oserror" --collect-only -q`
```
tests/test_spawn_pipeline.py::SpawnCapacityCheck::test_refuses_before_clone_when_free_bytes_below_threshold
tests/test_spawn_pipeline.py::SpawnCapacityCheck::test_reuse_branch_is_also_refused_not_just_fresh_clone
tests/test_spawn_pipeline.py::SpawnCapacityCheck::test_skip_env_var_bypasses_the_check
tests/test_spawn_pipeline.py::WorkspaceIncompleteCloneNotOriginMismatch::test_partial_clone_with_no_head_is_reported_as_incomplete
tests/test_spawn_pipeline.py::WorkspaceIncompleteCloneNotOriginMismatch::test_complete_but_foreign_repo_is_still_origin_mismatch
tests/test_spawn_observation_recovery.py::Watchdog::test_roster_watchdog_survives_checkpoint_workspace_oserror
6 tests collected
```
- `SpawnCapacityCheck` (3 of the 6 above): refuses before clone on low
  free bytes; the reuse branch is refused too (added after the
  before-landing hunt finding below); `MUSTER_SKIP_SPACE_CHECK=1` bypasses.
- `WorkspaceIncompleteCloneNotOriginMismatch` (2 of the 6 above): a
  `.git`-with-no-HEAD workspace is reported as incomplete, not
  origin-mismatch; a complete-but-foreign repo is still origin-mismatch
  (regression guard on the pre-existing `WorkspaceReuseOriginMismatch`
  class in the same file).
- `test_roster_watchdog_survives_checkpoint_workspace_oserror` (last of
  the 6 above): `checkpoint.checkpoint_workspace` raising
  `FileNotFoundError` no longer crashes the tick.

## Why

The issue's four symptoms share one root cause (host disk/inode
exhaustion outside on-the-record's control) but reach the operator as
four unrelated-looking failures because nothing checks capacity before
writing, and nothing distinguishes "this .git is a different repo" from
"this .git is what a killed-mid-write clone leaves behind". The fix adds
exactly those two missing checks at the two points that actually write
(clone/fetch, and the per-tick checkpoint), rather than trying to
harden every individual write call site — the acceptance criteria name
these two behaviors specifically (pre-flight refusal named-cause, and
watchdog survives instead of crashing), and the existing origin-mismatch
check already had the right shape, it was just missing one prior
question ("did this clone ever finish?").

`_workspace_clone_incomplete()` checks `HEAD` + `git status`, not a
sentinel file the code itself writes: the existing
`WorkspaceReuseOriginMismatch` regression test (tests/test_spawn_pipeline.py,
`test_foreign_origin_at_work_path_is_refused_by_identity`) builds a
genuinely foreign repo with `git init` + a real commit + a mismatched
origin remote and never touches any on-the-record bookkeeping
(`.on-the-record/role.json` sidecar) — a sentinel-based completeness
check would misclassify that existing, intentional test case as
"incomplete" too. HEAD/status are git's own notion of "does this repo
have a working commit", generic to any git repository regardless of who
created it.

The byte threshold (`3 * 119MB`) comes from `du -sh` across the
workspaces live under `$MUSTER_WORKSPACE_ROOT` on this host at the time
of this change (50–121MB each, matching the issue's own ~119MB figure):
canonical: `du -sh "$MUSTER_WORKSPACE_ROOT"/*/ 2>/dev/null | sort -h`, run
this session before any code change —
```
...
71M	.../on-the-record-issue-2431-implementation/
102M	.../on-the-record-issue-2395-implementation/
121M	.../on-the-record-issue-2288-implementation/
```
(25 workspaces total that run, min 50M–max 121M; `du -sh --total` gave
1.5G/25 ≈ 60M average). 3x the observed per-workspace upper bound (121M)
gives headroom for a few concurrent spawns landing in the same window
without hand-picking an arbitrary round number.

## What did not work

- First watchdog-crash repro attempt used `os.environ["TMPDIR"] =
  <nonexistent path>` — didn't reproduce the crash. Python's
  `tempfile.gettempdir()` treats `TMPDIR` as only the first of several
  fallback candidates (`/tmp`, `/var/tmp`, `/usr/tmp`, cwd); since real
  `/tmp` on this host still worked, it silently fell through. Fixed by
  setting `tempfile.tempdir` (the resolved-value cache) directly instead
  of the env var — that bypasses the fallback search and reproduces the
  issue's exact `FileNotFoundError` (see Acceptance evidence below for
  the resulting live output).
- First incomplete-clone repro let `git clone` fail via genuine ENOSPC
  (tiny tmpfs target) and expected a leftover partial `.git` — instead
  `git clone` cleaned up its own partial directory on a clean ENOSPC
  failure, so a retry always re-took the fresh-clone branch, not the
  reuse/origin-mismatch branch the issue actually hit. The issue's own
  partial tree required an unclean death (the process itself killed
  mid-write, not git's own failure-exit running its cleanup) — reproduced
  by launching `git clone` as a subprocess and `kill -9`'ing it ~20ms in,
  which reliably leaves a `.git` with no reachable `HEAD` (see Acceptance
  evidence below).
- A `roster_watchdog()` demo hung (2+ minutes, no output) when called
  with the default `root=ROOT` (this repo's own live board) unmocked.
  canonical: `ps aux | grep -E "spawn\.py|claude -p"`, run this session
  while the demo was hanging —
```
jwjung   1119117  ...  spawn.py -C .../tokenmaxxxer-core-issue-304-execution-observation watch --issue 304 --role execution-observation --follow ...
jwjung   1322600  ...  spawn.py implementation ... --issue 2443 -C ...
jwjung   1322601  ...  spawn.py -C .../on-the-record-issue-2443-implementation watch --issue 2443 --role implementation --follow ...
jwjung   1324648  ...  spawn.py implementation ... --issue 2288 -C ...
jwjung   1324649  ...  spawn.py -C .../on-the-record-issue-2288-implementation watch --issue 2288 --role implementation --follow ...
```
  — dozens of other real role sessions concurrently running on this
  shared host; `uptime` at the same moment showed `load average: 127.83,
  100.67, 77.30` on a 16-core box (`nproc` = 16), i.e. ~8x oversubscribed.
  Not a defect in the change; `_board_wide_sweep`/related board-scan
  functions do real work against the live board by design and simply
  couldn't get scheduled promptly. Fixed by mocking
  `_board_wide_sweep_all`/`lease_reconcile_sweep`/`spawn_attempt_sweep`/
  `standing_red_check`/`_undispositioned_role_prs` and using an isolated
  temp `root`, matching how the existing `roster_watchdog()` test suite
  (tests/test_spawn_observation_recovery.py, e.g.
  `test_roster_watchdog_returns_zero_for_clean_non_empty_roster`) already
  isolates these calls.
- Running the new/changed tests via `pytest -n auto` (this repo's default
  `addopts`) intermittently hung at "bringing up nodes..." for minutes —
  same host-load cause as above (xdist spinning up 16 worker processes on
  an already 8x-oversubscribed host; reproduced identically on an
  unmodified, pre-existing test in this same file, so not caused by this
  change). Worked around by disabling xdist for slow single-test runs
  (`-p no:xdist -o addopts=""`).
- Mid-session, the harness's own Bash/Write tools started failing with
  live `ENOSPC` for roughly ten consecutive tool calls over a few
  minutes.
  canonical: `df -i /` and `df -h /`, run this session at the moment tools
  recovered —
```
$ df -i /
파일 시스템      Inodes    IUsed IFree IUse% 마운트위치
/dev/nvme0n1p2 61022208 61022123    85  100% /
$ df -h /
파일 시스템     크기  사용  가용 사용% 마운트위치
/dev/nvme0n1p2  916G  788G   81G   91% /
```
  100% inodes used, free-inode count fluctuating between 85 and 57478
  across a few minutes of repeated checks in this same session — byte
  space was fine (91% used, 81-83G free) the whole time. This is the
  exact failure mode the issue describes (df -i near 100%, byte space
  not the bottleneck), observed live and unprompted during this
  delivery, not simulated. It resolved on its own after several retries
  (consistent with the issue's own "not multi-tenant [...] but bursts"
  framing). Own leftover fixture files under /tmp (~950MB combined, from
  the live clone-kill repro above — few large files, not an inode
  contributor) were cleaned up once tools recovered.
  canonical: `git status --short`, run this session immediately after
  cleanup —
```
 M .orchestrate-hook-fires/unknown.log
 M spawn.py
 M tests/test_spawn_observation_recovery.py
 M tests/test_spawn_pipeline.py
 M watchdog.py
?? .orchestrate-hook-fires/2cc38386f7c687a6ee01b9e0.log
?? docs/issue-2417/
```
  (`.orchestrate-hook-fires/*` are harness-generated, not part of this
  change — left untouched, not staged) — no leftover repo-tree residue
  from the /tmp incident.
- Before-landing warrant-hunter (stance 0, "assume the gate just touched
  is bypassable") found a real gap: `_spawn_capacity_check()` was only
  called on the fresh-clone branch, so a respawn onto an existing
  workspace (reuse branch, which calls `_fetch_or_halt` not `git clone`)
  on a near-full disk still hit `_fetch_or_halt`'s buried/truncated fetch
  error — the exact failure class this issue is about, just relocated
  from clone to fetch.
  canonical: the before-landing hunt record (this record's own
  `upstream:` frontmatter field carries its path) — hunter's full
  reproduction and this record's resolution note live there. Fixed by
  moving the check to run once before all three branches; verified by
  the added `test_reuse_branch_is_also_refused_not_just_fresh_clone`
  (see the 6-test collect-only list above).

## Upstream basis

No phase-1 proposal exists for this delivery (build-now bypass, see top
of this record). The only upstream input is the before-landing hunt
record this same commit adds (see the `upstream:` frontmatter field
above; `sha: same-commit`).

## Doc-placement ladder

- `docs/specs/`: untouched — no system-design change, this is failure-path
  hardening inside existing functions.
- `docs/decisions/`: untouched — no hard-to-reverse choice; the threshold
  is a stated, overridable policy documented inline in `spawn.py` next to
  `MIN_FREE_BYTES_DEFAULT`/`MIN_FREE_INODES_DEFAULT`, not a one-way door.
- `docs/reports/`: this record + the hunt record referenced in
  `upstream:` above are the reports for this issue; no separate
  `docs/reports/` entry.
- `docs/proposals/`: none — build-now bypass skipped phase 1.
- this record's own directory: the hunt record referenced in `upstream:`
  above lives alongside it.
- this file: the implementation record itself, referenced in this
  record's own `code_under_review:`/frontmatter context.

## What was left untouched (acceptance criterion 6)

Nothing in the recording or observer path was removed or altered beyond
the four changes above:
canonical: the `code_under_review:` frontmatter list above names the
exact 4 files touched this delivery
- `checkpoint.py` (`checkpoint_workspace`/`checkpoint_health`/
  `cleanup_checkpoint_ref`) — not in the touched-files list above; still
  raises on tempdir failure as a pure function. Only its one call site in
  `watchdog.py` now catches that exception; the module's own contract is
  untouched.
- The origin-mismatch check itself (`spawn.py`, the `_norm()`/
  ssh-vs-https comparison logic) — unchanged; still fires exactly as
  before for a workspace that passes the new incomplete-clone check.
  derived: `python3 -m pytest tests/test_spawn_pipeline.py -k WorkspaceReuseOriginMismatch -q`
```
2 passed in 0.89s
```
- `watchdog_check_one`, `diagnose_health`, `reconcile`, `lease_renew`,
  board-wide sweeps, standing-red checks, returned-PR reporting — all
  unchanged; the fix only wraps the one `checkpoint_workspace()` call, the
  rest of `roster_watchdog()`'s per-tick loop body is untouched (see the
  watchdog.py diff: a single `try/except` added around one existing call,
  nothing else in the function body moved or removed).
- The buried clone-error `sys.exit` message itself (spawn.py, `git clone`
  non-zero-exit branch) — code unchanged; functionally pre-empted for the
  disk-full case by the earlier capacity refusal, but still reachable
  (and still buried, as before) for non-space clone failures.

## Acceptance evidence (executed live this session)

acceptance: pre-flight refusal before clone, simulated-full condition —
result:
mounted an unprivileged 8MB tmpfs (`unshare --user --mount
--map-root-user`, no root/sudo used), pointed `MUSTER_WORK_DIR` at it,
called `spawn.issue_workspace()` on a real local git repo as `src`:
```
파일 시스템     크기  사용  가용 사용% 마운트위치
tmpfs           8.0M     0  8.0M    0% /tmp/demo2417/work_base
refused as expected, elapsed=0.0286s
MESSAGE: 스폰을 거부한다: /tmp/demo2417/work_base 에 여유 공간이 부족하다 (8MB 가용, 임계값 357MB) — clone 을 시도하기 전에 미리 막는다. 정책: 워크스페이스 상한 실측치(~119MB)의 3배를 동시-스폰 헤드룸으로 둔다. 알고 진행하려면 MUSTER_SKIP_SPACE_CHECK=1.
```
refused before any `git clone` subprocess ran — not a clone error, not an
origin-mismatch accusation.

acceptance: watchdog survives an unwritable tempdir — result: reproduced
the exact `FileNotFoundError` from `tempfile.TemporaryDirectory()` by
setting `tempfile.tempdir` to a nonexistent path, then called
`spawn.roster_watchdog()` with one live roster entry (dirty git repo,
real pid). BEFORE (original watchdog.py, via `git stash`):
```
CRASHED (-> rc=97 via CLI's except-Exception wrapper at spawn.py watchdog branch): FileNotFoundError: [Errno 2] No such file or directory: '/tmp/tmpi6_ztczb/nonexistent-tmp/tmp4l6bzzea'
```
AFTER (current code):
```
SURVIVED — anomaly_count returned = 1
--- captured stdout (relevant lines) ---
[checkpoint] k: 워크스페이스 체크포인트 실패 (디스크/tempdir 문제로 보임, 이 틱은 계속 진행) — [Errno 2] No such file or directory: '/tmp/tmp8gd1nr3y/nonexistent-tmp/tmp8a9hj_xp'
[watchdog] k: 정상
```
the tick completed and continued diagnosing the same entry.

acceptance: origin-mismatch → incomplete workspace, exact repro — result:
launched a real `git clone` of a 400MB local repo, `kill -9`'d it ~20ms in
(leaves `.git` with no reachable `HEAD`, origin remote still pointing at
the local clone source). Retried the same spawn — BEFORE (`git stash` on
spawn.py only):
```
OLD MESSAGE: 작업 경로에 다른 레포가 있다 (origin 불일치): /tmp/demo3/work_base/demo-repo-issue-24171-implementation — 기대: https://github.com/example/demo-repo.git, 실제: /tmp/demo3/src
```
this is the literal message this session's original incident produced.
AFTER (current code):
```
NEW MESSAGE: 워크스페이스가 불완전하다: /tmp/demo3/work_base/demo-repo-issue-24171-implementation — 이전 clone 이 도중에 실패해 (디스크 공간/inode 부족 등) 남의 레포가 아니라 partial 상태의 미완성 클론으로 남아 있다. 해결: 지우고 재시도하라 — rm -rf /tmp/demo3/work_base/demo-repo-issue-24171-implementation
```

acceptance: threshold policy + override — result: policy stated inline in
`spawn.py` next to `MIN_FREE_BYTES_DEFAULT`/`MIN_FREE_INODES_DEFAULT` (3x
the ~119MB/workspace measured upper bound, see "Why" above). Override
demonstrated live:
derived: `python3 -m pytest tests/test_spawn_pipeline.py -k test_skip_env_var_bypasses_the_check -q`
```
1 passed in 0.9s
```
`MUSTER_SKIP_SPACE_CHECK=1` lets a spawn proceed under the same 1KB-free
mock that otherwise refuses.

acceptance: no added steady-state cost — result: the probe runs once per
`issue_workspace()` call (once per spawn attempt; all three branches now
share the single call — see the before-landing hunt fix above), never per
watchdog tick.
```
$ python3 -c "
import shutil, os, time
N = 2000
t0 = time.perf_counter()
for _ in range(N):
    shutil.disk_usage('.')
    os.statvfs('.')
dt = time.perf_counter() - t0
print(f'{N} calls in {dt*1000:.1f}ms -> {dt/N*1e6:.1f}us/call')
"
2000 calls in 3.7ms -> 1.8us/call
```
1.8µs/call combined for both syscalls — negligible against a clone that
runs for whole seconds (`CLONE_TIMEOUT = 180` in spawn.py).

acceptance: nothing removed from the recording/observer path — result:
see "What was left untouched" section above.

acceptance: full targeted test run, this session's final state — result:
```
$ python3 -m pytest tests/test_spawn_pipeline.py -k "SpawnCapacityCheck or WorkspaceIncompleteCloneNotOriginMismatch or WorkspaceReuseOriginMismatch"
7 passed in 1.79s

$ python3 -m pytest tests/test_workspace_checkpoint.py tests/test_watchdog_local_signals.py tests/test_watchdog_freshness.py tests/test_watchdog_heartbeat_noise.py
39 passed in 1.02s

$ python3 -m pytest tests/test_spawn_observation_recovery.py -k test_roster_watchdog_survives_checkpoint_workspace_oserror -p no:xdist -o addopts=""
1 passed, 171 deselected in 9.64s
```
7 + 39 + 1 = 47 passed, 0 failed, 0 error across all three runs above (the
171-deselected count in the third run is pytest's own report of
non-matching tests in that file under the `-k` filter, not a failure).

## Open findings

None outstanding — the one before-landing hunt finding (capacity check
missing on the reuse branches) was fixed in this same commit; see the
hunt record referenced in this record's `upstream:` frontmatter field for
the full trace.

## Next steps

None — `loop_state: landed`. This record ships in the delivery PR
alongside the code.
