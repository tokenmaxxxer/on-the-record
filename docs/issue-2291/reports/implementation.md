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

None.

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
