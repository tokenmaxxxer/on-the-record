---
issue: 2291
role: implementation
loop_state: landed
upstream:
  - path: gates/state_paths.py
    sha: 6e406a1acf97b0f10a56171a997856ac9237de5d
code_under_review:
  - spawn.py
  - roster.py
  - watchdog.py
  - tests/_spawn_test_support.py
  - tests/test_spawn_pipeline.py
type: feat
breaking: "no"
verdict: pass
---

# issue-2291 — implementation record

## What was done

canonical: spawn.py/roster.py/watchdog.py diff, this commit (`git diff --stat -- spawn.py roster.py watchdog.py`)

Build-now bypass (contract v3 s19a, `CORE_BUILD_NOW=1` set by the spawner):
delivered directly on `issue-2291/implementation`, no phase-1 proposal round.

Two changes, matching the issue's two Ask items:

**1. Durable spawn-attempt trace (`spawn.py`).** A new append-only JSONL
file, `SPAWN_ATTEMPTS_PATH = STATE_ROOT / "spawn-attempts.jsonl"` (same
`STATE_ROOT` constant `ROSTER`/`DEADMAN_MARKER` already anchor to — this
module's own install checkout, `MUSTER_STATE_ROOT`-overridable, never a
caller-supplied target-repo path, per #2240):

- `_record_spawn_attempt(issue, role, pid)` appends a `spawn_attempt` line
  and returns an `attempt_id`. Wired into `main()` right after the
  dry-run branch returns — before `require_doctor()`/`ensure_target_remote()`
  (the first network call) and before `_spawn_one()` (workspace clone,
  branch checkout, admission gate, skill resolution) — i.e. before any
  network or workspace work, for `--issue` spawns only (ad-hoc spawns never
  register in the roster, so there is nothing for the watchdog to
  reconcile against).
- The whole window (`require_doctor()` through `_spawn_one()`'s return) is
  wrapped in `try/except (SystemExit, Exception)`. On any halt —
  `_fetch_or_halt()`-class `sys.exit()` or any other uncaught exception —
  `_record_spawn_outcome(attempt_id, "halted", reason)` appends the reason
  before re-raising, so the durable trace outlives a stdout/stderr pipe
  the consumer routes through `tail`.
- On success, `_spawn_one()` calls `_record_spawn_outcome(attempt_id,
  "session-log", str(log_path))` at the exact point the live-log path is
  computed — the earliest point a workspace/session log is known to exist.
  `_record_spawn_outcome()` is idempotent per `attempt_id`
  (`_SPAWN_ATTEMPT_OUTCOME_WRITTEN`) so an unrelated exception later in
  `_spawn_one()` (e.g. a `Popen` failure) can never overwrite an
  already-recorded success as a false bootstrap-halt outcome.
- `_load_spawn_attempts()` reads the trace back as `(attempts, outcomes)`
  dicts keyed by `attempt_id`.

**2. Roster-aware halt visibility (`roster.py` + `watchdog.py`).** A new
level-triggered advisory, `spawn_attempt_sweep(d_all, now)`, co-located
with `lease_reconcile_sweep` (same file, same "compare desired vs actual
every tick" shape) and called from `roster_watchdog()` right after it,
unconditionally every tick, before the `if not d:` early return — so an
attempt that never reached the roster is still seen even when the roster
itself is empty. For each attempt with no `"session-log"` outcome, the
sweep prints `[spawn-attempt] issue-<n>/<role>: spawn halted
pre-workspace: <reason>` when either: a `"halted"` outcome was recorded
(reported immediately, the recorded reason as detail); or no outcome was
ever recorded and `SPAWN_ATTEMPT_GRACE_SEC` (`CLONE_TIMEOUT +
NETWORK_TIMEOUT + 60` = 300s, the worst-case legitimate pre-roster
duration) has elapsed with no matching roster entry. Dedup-gated per
`attempt_id` via the existing `ledger_check_and_stamp` reconcile ledger
(same mechanism every other watchdog advisory uses), folded into
`anomaly_count` like `lease_reconcile_sweep`'s.

## Why

canonical: pipeline.py:810 (`_fetch_or_halt`, verified in this checkout before writing code), spawn.py's `main()`/`_spawn_one()` bootstrap-ordering (workspace/roster/session-log all created inside `_spawn_one()`, after `require_doctor()`/`ensure_target_remote()`)

amendments-reconciled: issuecomment-5403883219 — the issue's original
"Consumer report" section attributed the issue-538 incident to
`_fetch_or_halt`; the author's follow-up comment corrects this: the
consumer ran `spawn.py implementation 538` with `538` as the positional
*task* text, not `--issue 538`, so an **adhoc** session spawned, wrote to
`runs/last-session.log`, and stayed alive (watchdog correctly HEALTHY) —
it never touched `_fetch_or_halt`/workspace machinery at all. The 538
incident is explicitly **not** cited below as the motivating failure for
that reason; its actual defect (silent degenerate-task admission) is a
separate, out-of-scope issue per the comment. `issue-538`/`pid …` in the
"Provenance" acceptance evidence further below is this record's own
arbitrary synthetic issue number for the live-fire reproduction the
comment asked for — not a reference to the real incident's issue.

The issue named two structural defects that stand independently of that
misattribution, both verified in this checkout before writing any code and
both reaffirmed by the comment ("this issue's ask stands on its own merits
regardless: the pre-log bootstrap window IS traceless … and a genuine
`_fetch_or_halt` halt through a piped stdout would still vanish"): (1)
`_fetch_or_halt()` (pipeline.py:810) and the rest of workspace preparation
run before the session log, roster entry, and workspace directory exist, so
a fail-closed halt there reports only to stdout/stderr — the issue's own
cited prior sighting (spawn.py:3004, "events.jsonl 에 아무 흔적도 안
남았다", survey.md incident #2) is the actual motivating precedent, not the
538 incident; (2) a spawn that dies pre-roster leaves no roster entry, so
the watchdog has nothing to report for that (issue, role) and can mislead
by surfacing an unrelated entry as HEALTHY instead.

The fix follows the codebase's own established pattern for exactly this
class of problem rather than inventing a new one: `gates/state_paths.py`
(issue #2240) already solved "orchestrator cross-tick memory must never be
`root/"runs"` composed from a caller-supplied target repo" for `gh_delta`,
`closure_sweep`, `spawn_on_pr`, `spawn_on_approve`, and the board snapshot —
but `spawn.py` itself was never one of the modules with that bug (`ROSTER`/
`DEADMAN_MARKER` already anchor to its own `STATE_ROOT`, never a caller's
`root`), so the new trace file reuses that same in-module `STATE_ROOT`
convention rather than routing through `gates/state_paths.py`'s accessor
(which exists specifically for modules that accept a caller-supplied
`root:` parameter — `spawn.py` doesn't). `lease_reconcile_sweep` (issue
#2101 mechanism 3) is the established shape for "a level-triggered
advisory hooked into the watchdog tick, comparing desired vs actual roster
state, dedup-gated via the reconcile ledger" — `spawn_attempt_sweep` is the
same shape applied one layer earlier (pre-roster instead of post-roster).

Append-only JSONL (not a JSON dict + load-modify-save) for the trace file
itself: the entire point is that the writing process may die at any
instant in this window, including mid-write of a structured file — JSONL
append-then-close means every already-written line survives regardless of
where the process dies, matching `events.jsonl`'s existing convention in
this codebase for exactly the same crash-survival reason.

The `main()`-level `try/except` (rather than instrumenting every
`_fetch_or_halt()`/`sys.exit()` call site inside `_spawn_one()`
individually) was chosen because the bootstrap window has many potential
exit points (`admission_gate`, `--skills` validation, `issue_workspace()`,
`checkout_issue_branch()`, and any future one), and a per-site approach
guarantees a new halt point added later silently falls outside the trace
again — the exact failure mode this issue reports. Wrapping the whole
window at the single caller that already knows the `attempt_id` catches a
halt wherever in that window it originates, present or future.

## What did not work

None on the original delivery. See `## Rationale for deviations` below for
a CHANGES-round correction: the original delivery's diagnosis of the
`role_model.txt` flake as "not touched by this change" was right about
causation but wrong to leave unfixed, since it kept the PR's own acceptance
gate (`tests/test_spawn_pipeline.py`) unreliable.

## Rationale for deviations

CHANGES round on PR #2305: a reviewer reported
`SpawnCmd::test_role_model_env_overrides_config` passing on `main` but
failing on this branch, reading as a regression from this change.

acceptance: python3 -m pytest tests/test_spawn_pipeline.py -q -k test_role_model_env_overrides_config (isolated) — result:

```
1 passed in 1.21s
```

acceptance: python3 -m pytest tests/test_spawn_pipeline.py -q (full file, this branch, pre-fix) — result:

```
2 failed, 84 passed in 1.29s
```
(`test_role_model_env_overrides_config` and `test_resolved_role_model_builtin_default_is_sonnet`, both `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0`.)

To isolate cause from this branch's own diff, the same full-file run was
repeated against unmodified `main` (`git worktree add --detach
/tmp/otr-main-check main`, base `831c31dc`) three separate times:

acceptance: cd /tmp/otr-main-check && python3 -m pytest tests/test_spawn_pipeline.py -q (first repeat run) — result:

```
3 failed, 83 passed in 9.82s
```
(`test_role_model_env_overrides_config`, `test_role_model_config_only_appends_flag`, `test_role_model_whitespace_only_config_uses_builtin_default` — same `UnicodeDecodeError`.)

acceptance: same command (second repeat run) — result:

```
1 failed, 85 passed in 2.03s
```
(`test_role_model_env_overrides_config` alone.)

acceptance: same command (third repeat run) — result:

```
86 passed in 2.16s
```

canonical: `git diff main...HEAD -- spawn.py`, this session — the diff touches only a `_sweep_completion_in_flight`-adjacent re-export (spawn.py:92-95) and the new `SPAWN_ATTEMPTS_PATH`/`_record_spawn_attempt` block (from spawn.py:841); no `role_model`/`ROLE_MODEL_CONFIG`/`--model` line anywhere.

The repeat runs above reproduce `test_role_model_env_overrides_config`
failing, with the same `UnicodeDecodeError`, on the unmodified branch tip —
confirming the original record's diagnosis of cause was correct (this
branch's feature diff does not touch role-model code, so it cannot be the
cause) — but the failure is real, reviewer-blocking on PR #2305, and was
left as an open flake in the original delivery instead of fixed.

Root cause: `spawn.ROLE_MODEL_CONFIG` (`ROOT / "role_model.txt"`) is a
single fixed path shared by every `pytest-xdist` worker process (`pytest.ini`
sets `addopts = -n auto`).

canonical: spawn.py:1169 (`ROLE_MODEL_CONFIG = ROOT / "role_model.txt"`), pytest.ini `addopts = -n auto`, tests/test_spawn_pipeline.py (pre-fix state — tests reading/writing `spawn.ROLE_MODEL_CONFIG` directly with no per-test isolation)

Several `SpawnCmd`/`DryRunModelReflection` tests read and/or write that real
file directly, or depend on it being empty/absent, with no isolation: when
two land in different xdist workers at the same wall-clock moment their
writes/reads race — torn writes, or one test's non-UTF-8 fixture bytes
observed mid-write by another test's `read_text()`.

Fix, scoped to the two test files only (`spawn.py`/`roster.py`/`watchdog.py`
production code untouched by this round): added
`isolated_role_model_config()`, a context manager in
`tests/_spawn_test_support.py` (patches `spawn.ROLE_MODEL_CONFIG` to a
private `tempfile.mkdtemp()` path for the test's duration — removes the
shared mutable file instead of narrowing the race window) and applied it to
every affected test: `test_role_model_unset_uses_builtin_default`,
`test_role_model_whitespace_only_uses_builtin_default`,
`test_role_model_config_only_appends_flag`,
`test_role_model_env_overrides_config`,
`test_role_model_whitespace_only_config_uses_builtin_default`,
`test_role_model_non_utf8_config_uses_builtin_default`,
`test_role_model_no_config_file_uses_builtin_default`,
`test_resolved_role_model_builtin_default_is_sonnet`,
`test_config_only_output_reflects_model`. The first two only pass a
whitespace/absent env value through to `resolved_role_model()`'s config-file
rung (per pipeline.py:518-547, `read_role_model_config()` is only reached
when the env value is empty after `.strip()`) and were latent races the
reviewer's report didn't name individually, but share the same
unisolated-file cause.

canonical: pipeline.py:518-547 (`resolved_role_model()` — `env_value` checked and returned before `_sp.read_role_model_config()` is ever called)

Rejected alternative: an `fcntl.flock` around each read/write — would only
serialize access, not remove the shared-state coupling, and these tests'
own save/restore-real-file `finally` blocks would still leave one worker's
in-progress fixture value visible to another worker's concurrently-running
test in the gap between lock release and assertion. Per-test isolation
removes the coupling outright and is a smaller diff (deletes the
save/restore boilerplate rather than adding locking around it).

Not touched: `test_role_model_set_appends_flag` (sets `MUSTER_ROLE_MODEL` to
a non-empty value, which `resolved_role_model()` returns before ever calling
`read_role_model_config()`) and `test_role_model_does_not_affect_haiku_probe`
(reads `spawn.py`'s own source text, not the config file) — neither's
outcome can be affected by config-file state.

Post-fix verification: the full-file run was repeated several more times,
plus the broader regression sweep from the original delivery, this session:

acceptance: python3 -m pytest tests/test_spawn_pipeline.py -q, repeated back-to-back — result (each repetition):

```
86 passed
```

acceptance: python3 -m pytest tests/test_state_root_scoping.py tests/test_watch_hardening.py test/test_roster_role_field.py tests/test_standing_red_watch.py tests/test_poll_watchdog_log.py tests/test_spawn_pipeline.py -q — result:

```
145 passed in 30.31s
```

## Upstream basis

Base commit `6e406a1acf97b0f10a56171a997856ac9237de5d` (issue-2291/implementation
branch tip before this change, `issue-2226: fix gates/ sibling-import collision
under python3 -m gates.<X> (#2243)`). `gates/state_paths.py` (issue #2240) and
`roster.py`'s `lease_reconcile_sweep` (issue #2101 mechanism 3) are the two
precedents this change follows structurally — both already present at that
commit, sha above. `spawn.py`, `roster.py`, `watchdog.py` themselves are
`same-commit` (this record lands with their edits).

## Open findings

None.

## Next steps

None — `loop_state: landed`. Acceptance evidence below.

### Acceptance (issue #2291)

**Empty state** — a successful spawn: the attempt gains a `"session-log"`
outcome and the sweep reports nothing.

acceptance: python3 -c with `spawn._record_spawn_attempt`/`_record_spawn_outcome("session-log", ...)` then `roster.spawn_attempt_sweep(...)` — result:

```
empty-state anomaly count (expect 0): 0
```

**Provenance (executed-live)** — a synthetic reproduction (per
amendments-reconciled above: the 538 incident itself never reached
`_fetch_or_halt`, so this forces a genuine one directly, as the comment
asked) of a real `_fetch_or_halt` halt: unreachable remote, same technique
as the `WorkspaceSyncFailClosed` test class in tests/test_spawn_pipeline.py
(a real local git repo with `git remote add origin /no/such/path-xyz`),
with the spawn-attempt script's stdout piped through `tail -15` — the same
shell pattern (`2>&1 | tail`) the consumer's report used, which is what
made the original halt traceless — in an isolated clone of this checkout
(`MUSTER_STATE_ROOT` pointed at a scratch dir outside the target repo). The
issue number used below (538, matching the consumer's task-string digits
purely for readability) is this reproduction's own arbitrary choice, not a
claim about the real incident's issue. Two real, separately-executed steps:

acceptance: python3 script calling `spawn._record_spawn_attempt` then the real `spawn._fetch_or_halt(str(work), "신규 워크스페이스")` against a real unreachable git remote, piped `2>&1 | tail -15` — result:

```
### STEP 1: consumer-equivalent spawn attempt, piped through tail exactly as the consumer's report describes ###
신규 워크스페이스: fetch 실패 — fatal: '/no/such/path-xyz' does not appear to be a git repository
fatal: 리모트 저장소에서 읽을 수 없습니다

올바른 접근 권한이 있는지, 그리고 저장소가 있는지
확인하십시오.
(swallowed exit code as the consumer's shell would see it: 0)

### STEP 2: durable trace, STATE_ROOT-scoped — never in the target repo ###
{"event": "spawn_attempt", "attempt_id": "538:implementation:2617046:1787622816121", "issue": 538, "role": "implementation", "pid": 2617046, "ts": 1787622816.1217744}
{"event": "spawn_attempt_outcome", "attempt_id": "538:implementation:2617046:1787622816121", "outcome": "halted", "detail": "신규 워크스페이스: fetch 실패 — fatal: '/no/such/path-xyz' does not appear to be a git repository\nfatal: 리모트 저장소에서 읽을 수 없습니다\n\n올바른 접근 권한이 있는지, 그리고 저장소가 있는지\n확인하십시오.", "ts": 1787622816.1509821}
```

Confirmed afterward that neither the target repo's tree nor this install's
own `runs/` gained any file from this run (`ls
/tmp/otr-2291-demo/work` and `git status --porcelain -- runs/` in this
checkout both empty).

Then the real `spawn.py watchdog -C .` CLI, same `MUSTER_STATE_ROOT`, in
the same isolated clone (`SPAWN_WATCHDOG_ALLOW_NONCANONICAL=1` only to
satisfy the unrelated canonical-checkout guard for a throwaway clone — no
other override):

acceptance: python3 spawn.py watchdog -C . (real watchdog tick, same MUSTER_STATE_ROOT as above) — result:

```
[watchdog] board-sweep: on-the-record 건너뜀 (다른 워크스페이스가 스윕 중) — [watchdog] 이미 실행 중: pid=2359681 start_time=776649826 — lock=/home/jwjung/.tokenmaxxxer/locks/board-sweep-on-the-record.lock
[spawn-attempt] issue-538/implementation: spawn halted pre-workspace: 신규 워크스페이스: fetch 실패 — fatal: '/no/such/path-xyz' does not appear to be a git repository
fatal: 리모트 저장소에서 읽을 수 없습니다

올바른 접근 권한이 있는지, 그리고 저장소가 있는지
확인하십시오.
[returned-pr] issue #2262 (phase1): age=0.0h — https://github.com/tokenmaxxxer/on-the-record/pull/2299
[returned-pr] issue #2241 (phase1): age=0.2h — https://github.com/tokenmaxxxer/on-the-record/pull/2296
[returned-pr] issue #2250 (phase1): age=0.4h — https://github.com/tokenmaxxxer/on-the-record/pull/2292
돌고 있는 역할 세션 없음
```

The `[spawn-attempt] issue-538/implementation: spawn halted pre-workspace:
...` line is the watchdog's next tick naming the pre-workspace halt — the
exact state the issue says the system could not previously express.

**Gate**: `tests/test_spawn_pipeline.py`

Historical, as of the original delivery — superseded by the CHANGES-round
fix in `## Rationale for deviations` above, which made this gate
deterministic (`isolated_role_model_config()` in
`tests/_spawn_test_support.py`); the flake diagnosed just below is the one
that round fixed.

acceptance: python3 -m pytest tests/test_spawn_pipeline.py -q — result:

```
5 failed, 81 passed in 18.16s
```

canonical: `git stash` re-run of the same failing tests against the unmodified branch tip, this session (`git stash && python3 -m pytest tests/test_spawn_pipeline.py -q -k "test_role_model_unset_uses_builtin_default or test_unset_output_reflects_builtin_default" && git stash pop`)

The 5 failures (`test_role_model_*`/`DryRunModelReflection::*`, all
`'haiku' != 'sonnet'`) are pre-existing and unrelated to this change — the
`git stash` re-run above reproduced the same 2 (of the 5) failures checked
against the unmodified branch tip, and a repeat run of the unmodified file
alone (no stash, this session) reproduced a different subset (3 failures,
different test names) on the very next invocation — an order/state-dependent
pre-existing `MUSTER_ROLE_MODEL`/`role_model.txt` cross-test isolation issue
in this suite (a stray `role_model.txt` written into the repo root by one of
these tests, confirmed via `git status --porcelain` after the run), not
touched by this change.

Additional regression sweep (state-root scoping, watch/lease/roster
machinery, standing-red, poll/watchdog log — all pre-existing, all still
green):

acceptance: python3 -m pytest tests/test_state_root_scoping.py tests/test_watch_hardening.py test/test_roster_role_field.py tests/test_standing_red_watch.py tests/test_poll_watchdog_log.py tests/test_spawn_pipeline.py -q -k "not model" — result:

```
131 passed in 8.25s
```

canonical: `python3 -c "import spawn"` and `python3 -m py_compile spawn.py roster.py watchdog.py`, this session — both exit 0, no output

skill-verdict: implementation-blueprint — applied: invoked; classified the
new trace-file-plus-per-tick-reconciliation work as `data-centric`
(repository/service separation) via `prep.py classify --surface backend
--external no --logic crud --asynchronous no` + `recommend data-centric`;
used it to decide the read/write "repository" functions
(`_record_spawn_attempt`/`_record_spawn_outcome`/`_load_spawn_attempts`)
live in `spawn.py` beside `spawn.py`'s own existing `STATE_ROOT`-anchored
helpers (`ROSTER`/`DEADMAN_MARKER`), while the per-tick reconciliation
"service" (`spawn_attempt_sweep`) lives in `roster.py` beside
`lease_reconcile_sweep`, matching this codebase's own module-per-concern
extraction convention (roster.py/watchdog.py/events.py/plumbing.py) rather
than introducing a new module for two writer functions and one constant.
other mounted skills: not triggered — no coupling/cohesion metric crossed
a threshold requiring `implementation-complexity-coupling-management`
(the only new cross-module edge, `roster.py` reading `spawn.py`'s new
`SPAWN_ATTEMPTS_PATH`/`_load_spawn_attempts` via the existing `_sp.`
indirection, is the same pattern every other roster.py/spawn.py
cross-reference already uses, not a new direction); no GoF pattern
decision was in play (`implementation-design-pattern-selection`); no
data-structure/algorithm performance cliff was in play (append-only JSONL
+ dict lookups, `implementation-performance-data-structure-choice`);
`work-in-english` — not invoked as a skill call, but followed throughout
(all code, comments, commit messages, and this record in English; only the
final chat summary to the user will be in Korean).

CHANGES round (this session): no mounted skill invoked. The reviewer's
report already named the failing test and its cause category
(role-model flag composition); the work was reproduce-and-fix against a
concretely diagnosed test-isolation bug, not an open architecture/pattern/
coupling/data-structure decision, so none of
`implementation-blueprint`/`implementation-complexity-coupling-management`/
`implementation-design-pattern-selection`/
`implementation-performance-data-structure-choice` applied — other mounted
skills: not triggered. `work-in-english` followed throughout (fix, tests,
this record in English).
