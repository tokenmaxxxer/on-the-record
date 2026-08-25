---
issue: 2291
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: pipeline.py
    sha: 46da1c8a199048b380c363a936e92bca1c7c5393
  - path: roster.py
    sha: same-commit
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

Redelivery of issue #2291 on the current `main` (base
`46da1c8a199048b380c363a936e92bca1c7c5393`).

canonical: `gh pr list --search "2291" --state all` (this session) —
result:
```
2365	issue-2291: builder-blind conformance review of PR #2305	issue-2291/conformance-review	CLOSED	2026-08-25T05:30:58Z
2362	issue-2291: independent execution-observation of PR #2305's traceless-bootstrap-fix acceptance	issue-2291/execution-observation	MERGED	2026-08-25T05:20:45Z
2305	issue-2291: durable spawn-attempt trace + watchdog pre-workspace halt visibility	issue-2291/implementation	CLOSED	2026-08-25T02:09:05Z
```
`gh pr view 2305 --json body` (this session) confirms #2305's own body
states it was delivered under this same build-now bypass and closes
issue #2291; the branch base for #2305 predates the 2026-08-25
co-author-trailer history rewrite (`git merge-base --is-ancestor
6e406a1a main` returned non-ancestor in this checkout, this session),
which is why it could not be merged as-is and this session redelivers
onto the rewritten `main` instead of reusing that branch.

Two changes, matching the issue's two Ask items, ported unchanged in
mechanism from `git diff 6e406a1a 7a1aa4ec -- spawn.py roster.py
watchdog.py` (the #2305 branch's own implementation commit, read in this
checkout via its still-resolvable commit objects) and adapted only where
`main` had drifted:

**1. Durable spawn-attempt trace (`spawn.py`).** A new append-only JSONL
file, `SPAWN_ATTEMPTS_PATH = STATE_ROOT / "spawn-attempts.jsonl"` (the
same `STATE_ROOT` constant `ROSTER`/`DEADMAN_MARKER` already anchor to —
this module's own install checkout, `MUSTER_STATE_ROOT`-overridable,
never a caller-supplied target-repo path, per #2240).

canonical: spawn.py:861 (`SPAWN_ATTEMPTS_PATH`), spawn.py:870-877
(`_record_spawn_attempt`), spawn.py:889-902 (`_SPAWN_ATTEMPT_OUTCOME_WRITTEN`,
`_record_spawn_outcome`), spawn.py:905-919 (`_load_spawn_attempts`),
spawn.py:1652-1653 (`main()` records the attempt before any network call),
spawn.py:1656-1687 (`try/except (SystemExit, Exception)` wraps
`require_doctor()` through `_spawn_one()`'s return, records `"halted"` on
any exit), spawn.py:3079 (`_spawn_one()` records `"session-log"` at the
point `log_path` is computed, before the roster/session-log exist for any
other reader) — all read directly from the file in this checkout, this
session.

**2. Roster-aware halt visibility (`roster.py` + `watchdog.py`).** A new
level-triggered advisory, `spawn_attempt_sweep(d_all, now)`, co-located
with `lease_reconcile_sweep` and called from `roster_watchdog()` right
after it, unconditionally every tick.

canonical: roster.py:432 (`SPAWN_ATTEMPT_GRACE_SEC = 180 + 60 + 60`),
roster.py:435-493 (`spawn_attempt_sweep` — reports a recorded `"halted"`
outcome immediately, or a no-outcome attempt once
`SPAWN_ATTEMPT_GRACE_SEC` has elapsed with no matching roster entry,
dedup-gated via `ledger_check_and_stamp`), watchdog.py:1483-1486
(`roster_watchdog()` calls `_sp.spawn_attempt_sweep(d_all=d_all)`
immediately after `lease_reconcile_sweep`, before the `if not d:` early
return) — all read directly from the file in this checkout, this
session. The roster-key comparison uses `main`'s current
`lease_key(issue, role)` helper (roster.py:141, issue #2241) rather than
a hand-rolled f-string, since that helper now lives in the same module
and — per its own docstring, roster.py:130-140 — produces the
byte-identical key; this is the one adaptation `main`'s drift required
versus the #2305 branch's original diff.

**3. Pre-existing test flake, ported alongside.** #2305's own CHANGES
round (visible in the branch's commit `53347a11`, read in this checkout)
found and fixed a pre-existing, unrelated flake in this issue's own
acceptance gate (`tests/test_spawn_pipeline.py`): `spawn.ROLE_MODEL_CONFIG`
is a single fixed path shared by every `pytest-xdist` worker, and several
tests read/write it directly with no isolation.

canonical: reproduced independently on this fresh checkout, before
porting the fix — see `## Rationale for deviations` below for the
before/after acceptance runs. `isolated_role_model_config()`
(`tests/_spawn_test_support.py`, new) patches `spawn.ROLE_MODEL_CONFIG`
to a private `tempfile.mkdtemp()` path per test; applied to the nine
affected tests in `tests/test_spawn_pipeline.py`. No production code in
this bullet.

## Why

canonical: pipeline.py:831 (`_fetch_or_halt`), spawn.py's `main()`
(spawn.py:1571 pre-fix / spawn.py:1652 post-fix) and `_spawn_one()`
bootstrap ordering (workspace/roster/session-log all created inside
`_spawn_one()`, after `require_doctor()`/`ensure_target_remote()`) — all
verified in this checkout before writing any code, this session.

The issue named two structural defects, both re-verified above: (1)
`_fetch_or_halt()` and the rest of workspace preparation run before the
session log, roster entry, and workspace directory exist, so a
fail-closed halt there reports only to stdout/stderr; (2) a spawn that
dies pre-roster leaves no roster entry, so the watchdog has nothing to
report for that (issue, role) and can mislead by surfacing an unrelated
entry as HEALTHY instead.

canonical: `gh issue view 2291 --comments` (this session) — the second
comment states verbatim: "the issue-538 spawn did NOT die at
`_fetch_or_halt`... an adhoc session spawned with the meaningless task
'538'... This issue's ask stands on its own merits regardless: the
pre-log bootstrap window IS traceless... and a genuine `_fetch_or_halt`
halt through a piped stdout would still vanish."

amendments-reconciled: per that comment, the originally-cited issue-538
incident is not cited here as the motivating failure — the issue's own
cited prior sighting (spawn.py:3004, "events.jsonl 에 아무 흔적도 안
남았다", survey.md incident #2) is. `issue-538`/`pid …` in the acceptance
evidence below is this reproduction's own arbitrary synthetic issue
number for the live-fire reproduction the comment asked for, matching
the digits used in the consumer's original (differently-caused) report
purely for readability — not a reference to the real incident.

This redelivery reused the design from PR #2305 rather than re-deriving
one, because that design already carries independent verification beyond
this session's own re-execution below.

canonical: `gh pr view 2362 --json state,title` / `gh pr view 2365
--json state,title` (this session) — #2362 ("independent
execution-observation of PR #2305's traceless-bootstrap-fix acceptance")
state MERGED; #2365 ("builder-blind conformance review of PR #2305")
state CLOSED — both titles read directly from GitHub in this session,
matching the `gh pr list` output cited under "What was done" above.
Neither this session nor the cited PR bodies were re-read line-by-line
for defects beyond their title/state (out of scope for this redelivery,
which stands on its own re-executed acceptance below rather than on
trusting those prior reviews' content) — the claim here is limited to
their recorded terminal state, not their content quality.

Re-deriving a different design from scratch would discard whatever
verification value those prior reviews carry for no benefit; porting the
identical diff (adjusted only for `main`'s unrelated drift, `lease_key()`
per issue #2241) preserves it, and this session independently
re-executes the issue's Acceptance criteria live (below) rather than
relying on the prior PRs' evidence.

The fix follows the codebase's own established pattern for this class of
problem: `gates/state_paths.py` (issue #2240) solved "orchestrator
cross-tick memory must never be `root/"runs"` composed from a
caller-supplied target repo" for other modules — `spawn.py` was never one
of those modules (`ROSTER`/`DEADMAN_MARKER` already anchor to its own
`STATE_ROOT`), so the new trace file reuses that same in-module
`STATE_ROOT` convention.

canonical: spawn.py:849 (`ROSTER = STATE_ROOT / "active.json"`), verified
in this checkout before writing code, this session.
`lease_reconcile_sweep` (issue #2101 mechanism 3) is the established
shape for "a level-triggered advisory hooked into the watchdog tick,
comparing desired vs actual roster state, dedup-gated via the reconcile
ledger" — `spawn_attempt_sweep` is the same shape applied one layer
earlier (pre-roster instead of post-roster).

canonical: roster.py:356-422 (`lease_reconcile_sweep`), read in this
checkout before writing `spawn_attempt_sweep`, this session.

Append-only JSONL (not a JSON dict + load-modify-save) for the trace
file: the writing process may die at any instant in this window,
including mid-write of a structured file — JSONL append-then-close means
every already-written line survives regardless of where the process
dies, matching `events.jsonl`'s existing convention in this codebase for
the same crash-survival reason.

The `main()`-level `try/except` (rather than instrumenting every
`_fetch_or_halt()`/`sys.exit()` call site inside `_spawn_one()`
individually) was chosen because the bootstrap window has many potential
exit points (`admission_gate`, `--skills` validation,
`issue_workspace()`, `checkout_issue_branch()`, and any future one), and
a per-site approach guarantees a new halt point added later silently
falls outside the trace again — the exact failure mode this issue
reports. Wrapping the whole window at the single caller that already
knows the `attempt_id` catches a halt wherever in that window it
originates, present or future.

## What did not work

None. The one adaptation `main`'s drift required (`lease_key()`, issue
#2241, roster.py:141) applied cleanly on the first attempt — no other
attempt was undone or replaced. See `## Rationale for deviations` below
for the ported test-isolation fix, which is a scope-preserving port from
#2305's own CHANGES round, not a deviation from this session's own plan.

## Upstream basis

`pipeline.py` (`_fetch_or_halt`, `bootstrap_fetch_and_record_sha`) is
unmodified upstream infrastructure this change relies on — cited at this
branch's base commit, `46da1c8a199048b380c363a936e92bca1c7c5393`.
`roster.py`'s pre-existing `lease_reconcile_sweep` (issue #2101
mechanism 3) and `lease_key()` (issue #2241) are the structural and
naming precedents `spawn_attempt_sweep` follows and reuses —
`same-commit` since `roster.py` itself is edited in this commit
alongside them. `spawn.py`, `watchdog.py`, and the two test files are
likewise `same-commit`.

Prior art (not upstream dependencies, but the design this redelivery
ports): `issue-2291/implementation` → PR #2305 (closed, base
invalidated), independent execution-observation PR #2362 (merged),
builder-blind conformance review PR #2365 (closed).

canonical: `gh pr list --search "2291" --state all` (this session, cited
in full under "What was done" above) is the source for all four PR
numbers/states/titles in this paragraph.

## Open findings

None.

## Next steps

None — `loop_state: landed`. Acceptance evidence below.

### Acceptance (issue #2291)

**Empty state** — a successful spawn: the attempt gains a
`"session-log"` outcome and the sweep reports nothing.

acceptance: `MUSTER_STATE_ROOT=<scratch>/state2 python3 -c "..."` calling
`spawn._record_spawn_attempt(9999, 'implementation', pid)` then
`spawn._record_spawn_outcome(attempt_id, 'session-log', '/fake/session.log')`
then `roster.spawn_attempt_sweep(d_all={}, now=time.time())` — result:

```
empty-state anomaly count (expect 0): 0
```

**Provenance (executed-live)** — a synthetic reproduction (per
amendments-reconciled above) of a real `_fetch_or_halt` halt: a real
local git repo (`git init` + `git remote add origin /no/such/path-xyz`,
an unreachable local path) in a scratch clone completely outside this
checkout (`/tmp/otr-2291-demo.*`, removed after capture), `MUSTER_STATE_ROOT`
pointed at a sibling scratch dir also outside this checkout and outside
the target repo. The issue number used below (538) is this
reproduction's own arbitrary choice matching the consumer's original
report's digits for readability, not a claim about the real incident
(amendments-reconciled above). Two real, separately-executed steps, the
first piped through `tail -15` — the same shell pattern (`2>&1 | tail`)
the consumer's report used, which is what made the original halt
traceless.

canonical: this session's own live execution, exact commands and raw
output quoted verbatim in the three result blocks immediately below —
not a summary or a re-statement, the fenced text is the literal captured
stdout/stderr from running them in this session.

acceptance: `python3 -c "..."` calling `spawn._record_spawn_attempt(538,
'implementation', pid)`, then `pipeline._fetch_or_halt(work, '신규
워크스페이스')` against the real unreachable remote, catching
`SystemExit` and calling `spawn._record_spawn_outcome(attempt_id,
'halted', reason)`, piped `2>&1 | tail -15` — result:

```
### STEP 1: consumer-equivalent spawn attempt, piped through tail exactly as the consumer's report describes ###
(swallowed exit code as the consumer's shell would see it: 0)
```

acceptance: `cat <scratch>/state/spawn-attempts.jsonl` (durable trace,
STATE_ROOT-scoped — never in the target repo) — result:

```
{"event": "spawn_attempt", "attempt_id": "538:implementation:2626105:1787636693047", "issue": 538, "role": "implementation", "pid": 2626105, "ts": 1787636693.0475821}
{"event": "spawn_attempt_outcome", "attempt_id": "538:implementation:2626105:1787636693047", "outcome": "halted", "detail": "신규 워크스페이스: fetch 실패 — fatal: '/no/such/path-xyz' does not appear to be a git repository\nfatal: 리모트 저장소에서 읽을 수 없습니다\n\n올바른 접근 권한이 있는지, 그리고 저장소가 있는지\n확인하십시오.", "ts": 1787636693.0704207}
```

derived: the `detail` field above (line 2 of the fence) is byte-identical
to STEP 1's would-be git stderr, read back from the durable file after
STEP 1's process exited — this is the claim "the halt reason survived
the tail-truncated pipe" made concrete: it is present in this fence
though absent from STEP 1's own truncated console output above.

Then the real `spawn.py watchdog -C .` CLI, same `MUSTER_STATE_ROOT`, in
the same isolated clone (`SPAWN_WATCHDOG_ALLOW_NONCANONICAL=1` only to
satisfy the unrelated canonical-checkout guard for a throwaway clone — no
other override):

acceptance: `MUSTER_STATE_ROOT=<scratch>/state SPAWN_WATCHDOG_ALLOW_NONCANONICAL=1 python3 spawn.py watchdog -C .` (real watchdog tick, same MUSTER_STATE_ROOT as above) — result:

```
[spawn-attempt] issue-538/implementation: spawn halted pre-workspace: 신규 워크스페이스: fetch 실패 — fatal: '/no/such/path-xyz' does not appear to be a git repository
fatal: 리모트 저장소에서 읽을 수 없습니다

올바른 접근 권한이 있는지, 그리고 저장소가 있는지
확인하십시오.
돌고 있는 역할 세션 없음
```

derived: the `[spawn-attempt] issue-538/implementation: spawn halted
pre-workspace: ...` line in the fence immediately above is, verbatim,
the watchdog's next tick naming the pre-workspace halt — quoted directly
from this session's own captured stdout, not paraphrased.

acceptance: `git status --porcelain -- runs/` (this checkout, executed in
this session immediately after the reproduction above) — result:

```
(no output)
```
canonical: the empty result directly above is this session's own
execution — no file was added to this checkout's `runs/` by the
reproduction.

**Gate**: `tests/test_spawn_pipeline.py`

Reproduced the pre-existing xdist flake on this fresh checkout, before
the test-isolation fix:

acceptance: `python3 -m pytest tests/test_spawn_pipeline.py -q` (this
branch, before the `role_model.txt` isolation fix) — result:

```
2 failed, 84 passed in 7.71s
```
(`test_role_model_env_overrides_config`,
`test_role_model_config_only_appends_flag`, both
`UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0`.)

After porting `isolated_role_model_config()` and applying it to the nine
affected tests:

acceptance: `python3 -m pytest tests/test_spawn_pipeline.py -q` (after
fix) — result:

```
86 passed in 1.15s
```

Additional regression sweep (state-root scoping, watch/lease/roster
machinery, standing-red, poll/watchdog log — all pre-existing):

acceptance: `python3 -m pytest tests/test_state_root_scoping.py tests/test_watch_hardening.py test/test_roster_role_field.py tests/test_standing_red_watch.py tests/test_poll_watchdog_log.py tests/test_spawn_pipeline.py -q` — result:

```
145 passed in 1.41s
```

acceptance: `python3 -c "import spawn"` and `python3 -m py_compile
spawn.py roster.py watchdog.py tests/_spawn_test_support.py
tests/test_spawn_pipeline.py` — result: both exit 0, no output.

## Rationale for deviations

No deviation from this session's own plan (ported the #2305 design
unchanged in mechanism, adapted for `main`'s drift, re-executed
Acceptance live) — this section documents the one pre-existing-flake fix
carried over from #2305's own CHANGES round, since it is scope-adjacent
(keeps this issue's own gate deterministic) rather than a divergence
introduced by this session.

Root cause: `spawn.ROLE_MODEL_CONFIG` (`ROOT / "role_model.txt"`) is a
single fixed path shared by every `pytest-xdist` worker process
(`pytest.ini` sets `-n auto`); several `SpawnCmd`/`DryRunModelReflection`
tests read/write it directly with no isolation, racing across workers.

canonical: spawn.py (`ROLE_MODEL_CONFIG = ROOT / "role_model.txt"`,
grep confirmed in this checkout, this session), pytest.ini (`-n auto`,
grep confirmed in this checkout, this session), the "before fix"
acceptance run above (2 failed, both `UnicodeDecodeError`) reproduces the
race directly on this fresh checkout.

Fix, scoped to the two test files only (`spawn.py`/`roster.py`/
`watchdog.py` production code untouched by this bullet): added
`isolated_role_model_config()` (`tests/_spawn_test_support.py`, patches
`spawn.ROLE_MODEL_CONFIG` to a private `tempfile.mkdtemp()` path for the
test's duration) and applied it to the nine affected tests in
`tests/test_spawn_pipeline.py`, ported verbatim from #2305 branch commit
`53347a11` (`git diff 7a1aa4ec 53347a11 -- tests/`, read in this
checkout, this session, then re-applied via `git apply` — applied
cleanly with no conflicts, confirming `main`'s test file had not drifted
in this region).

canonical: `git apply --check` exit 0 (this session) before the real
apply — cited as the check that `main`'s copy of the two test files was
byte-identical to #2305's pre-fix state in the affected regions.

## skill-verdict

skill-verdict: implementation-blueprint — not-applicable: this session
ported an already-designed architecture unchanged onto a rewritten
history — no open structural decision remained to classify in this
session; the #2305 branch's own record (commit `53347a11`, read in this
checkout) already documents the `classify`/`recommend data-centric` call
that produced this module layout.
skill-verdict: work-in-english — not-applicable: not invoked as a skill
call this session, since the module-layout convention it would have
governed was already established by the ported design; followed as a
standing convention instead — commit messages, this record, and the PR
description are in English, matching this codebase's own established
house style of Korean prose comments in the touched files (verified by
inspection of the surrounding, pre-existing comments in spawn.py/
roster.py/pipeline.py before writing new ones in the same style, this
session) for in-code comments; only the final chat summary to the user
is in Korean.
other mounted skills: not triggered —
`implementation-complexity-coupling-management`: the only new
cross-module edge (`roster.py` reading `spawn.py`'s new
`SPAWN_ATTEMPTS_PATH`/`_load_spawn_attempts` via the existing `_sp.`
indirection, roster.py:36) is the same pattern every other
`roster.py`/`spawn.py` cross-reference already uses (verified by reading
roster.py's existing `_sp.` call sites before writing new ones, this
session), not a new direction or a threshold crossing.
`implementation-design-pattern-selection`: no GoF pattern decision was in
play. `implementation-performance-data-structure-choice`: append-only
JSONL + dict lookups, no cliff.

## Build-now bypass note

`warrant`'s standing proposal-first gate did not apply this session —
`CORE_BUILD_NOW=1` was present in the environment and the spawning task
named the s19a bypass explicitly, so the default two-phase flow was
skipped per the role-handoff contract. The `warrant` plugin's own
directive text marks itself subordinate to contract v3 s22 in
headless/single-shot sessions for its hunter-dispatch step specifically;
this session additionally treated the s19a bypass as applying to the
plugin's proposal-gate step as a whole, since the spawning task's
explicit build-now authorization names skipping the proposal round as
the intended behavior. No `warrant-hunter` was dispatched for the same
s22 reason the directive names for its own dispatch step: this is a
headless, single-turn session with no later turn for an async background
result to land in, and waiting synchronously for a hunt at both the
after-proposal and before-landing moments was not compatible with
completing delivery within the turn.
