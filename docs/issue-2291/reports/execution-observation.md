---
issue: 2291
role: execution-observation
author: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2291/reports/implementation.md
    sha: 3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d
subject: PR #2366 (branch issue-2291/implementation, head
  3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d — untracked on this
  issue-2291/execution-observation branch, not yet merged to main) —
  spawn.py durable spawn-attempt trace (SPAWN_ATTEMPTS_PATH,
  _record_spawn_attempt/_record_spawn_outcome, main()'s halt-catching
  try/except), roster.py spawn_attempt_sweep, watchdog.py's call to it,
  and the ported tests/_spawn_test_support.py isolation fix
test: tests/test_spawn_pipeline.py (gate, 86 cases `derived: see body`);
  regression sweep
  (tests/test_state_root_scoping.py, tests/test_watch_hardening.py,
  test/test_roster_role_field.py, tests/test_standing_red_watch.py,
  tests/test_poll_watchdog_log.py, tests/test_spawn_pipeline.py — 145
  cases `derived: see body`); independent empty-state repro
  (spawn._record_spawn_attempt/_record_spawn_outcome +
  roster.spawn_attempt_sweep against d_all={}); independent live-fire
  repro (a real unreachable git remote, pipeline._fetch_or_halt, piped
  through tail -15, then the real `spawn.py watchdog` CLI)
result: passed
assertedBy: execution-observation, this session, independent re-execution
---

# issue-2291 — execution-observation record

## What was done

Independently re-executed, against a fresh `git worktree` of PR #2366's
head commit (`3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d`, branch
`issue-2291/implementation`), the issue's Acceptance criteria and the
implementation record's cited test claims — per
`defect-verification-independence-from-upstream-verdicts`, each result
below was produced by running the command myself in a fresh scratch
location before comparing against the implementation record's own
transcript, not by reading its transcript and restating it.

**Gate — `tests/test_spawn_pipeline.py`.**

derived: `python3 -m pytest tests/test_spawn_pipeline.py -q` (this
session, `/tmp/otr-pr2366-verify`, a `git worktree` of the PR head) —
result:

```
86 passed in 10.38s
```

Matches the implementation record's "after fix" figure (86 passed).

**Regression sweep.**

derived: `python3 -m pytest tests/test_state_root_scoping.py
tests/test_watch_hardening.py test/test_roster_role_field.py
tests/test_standing_red_watch.py tests/test_poll_watchdog_log.py
tests/test_spawn_pipeline.py -q` (this session, same worktree) — result:

```
145 passed in 1.51s
```

Matches the implementation record's figure (145 passed).

**Empty state — independent repro** (own scratch `STATE_ROOT`, own
synthetic issue number 9999, distinct from the implementation record's
own reproduction):

derived: `MUSTER_STATE_ROOT=/tmp/otr-2291-obs-state2 python3 -c "..."`
calling `spawn._record_spawn_attempt(9999, 'implementation', pid)` then
`spawn._record_spawn_outcome(aid, 'session-log', '/fake/session.log')`
then `roster.spawn_attempt_sweep(d_all={}, now=time.time())` — result:

```
empty-state anomaly count (expect 0): 0
```

**Provenance — independent live-fire repro** (own scratch clone
`/tmp/otr-2291-obs-demo` with `git remote add origin
/no/such/path-xyz-obs`, own scratch `STATE_ROOT`
`/tmp/otr-2291-obs-state`, own synthetic issue number 7777 — deliberately
different scratch paths and issue number than the implementation
record's own `538`/`/tmp/otr-2291-demo.*` reproduction, to rule out
copy-pasted-output rather than a freshly executed one):

Step 1 — consumer-equivalent spawn attempt, piped through `tail -15`
exactly as the consumer's report describes:

derived: `MUSTER_STATE_ROOT=/tmp/otr-2291-obs-state python3 -c "..."`
calling `spawn._record_spawn_attempt(7777, 'implementation', pid)`, then
`pipeline._fetch_or_halt('/tmp/otr-2291-obs-demo', 'obs-workspace')`
against the real unreachable remote, catching `SystemExit` and calling
`spawn._record_spawn_outcome(aid, 'halted', reason)`, piped `2>&1 |
tail -15` — result:

```
### STEP 1: consumer-equivalent spawn attempt, piped through tail exactly as the consumer's report describes ###
(swallowed exit code as the consumer shell would see it: 0)
```

Confirms the halt is genuinely traceless from the piped-stdout side —
the halt reason itself never appears in the truncated console output.

Step 2 — durable trace, read back from the file, not restated from
memory:

derived: `cat /tmp/otr-2291-obs-state/spawn-attempts.jsonl` — result:

```
{"event": "spawn_attempt", "attempt_id": "7777:implementation:1466090:1787642261393", "issue": 7777, "role": "implementation", "pid": 1466090, "ts": 1787642261.39383}
{"event": "spawn_attempt_outcome", "attempt_id": "7777:implementation:1466090:1787642261393", "outcome": "halted", "detail": "obs-workspace: fetch 실패 — fatal: '/no/such/path-xyz-obs' does not appear to be a git repository\nfatal: 리모트 저장소에서 읽을 수 없습니다.\n\n올바른 접근 권한이 있는지, 그리고 저장소가 있는지\n확인하십시오.", "ts": 1787642261.41952}
```

The `detail` field is the real `git fetch` stderr against the
unreachable remote, present in the durable trace though absent from
Step 1's own truncated console output — the concrete claim under test
("the halt reason survives the tail-truncated pipe") holds.

Step 3 — the real watchdog CLI's next tick:

derived: `MUSTER_STATE_ROOT=/tmp/otr-2291-obs-state
SPAWN_WATCHDOG_ALLOW_NONCANONICAL=1 python3 spawn.py watchdog -C
/tmp/otr-2291-obs-demo` — result:

```
[spawn-attempt] issue-7777/implementation: spawn halted pre-workspace: obs-workspace: fetch 실패 — fatal: '/no/such/path-xyz-obs' does not appear to be a git repository
fatal: 리모트 저장소에서 읽을 수 없습니다

올바른 접근 권한이 있는지, 그리고 저장소가 있는지
확인하십시오.
돌고 있는 역할 세션 없음
```

Names the pre-workspace halt exactly as the issue's Acceptance
criterion requires. (The CLI exited non-zero on this invocation — not
asserted on either here or in the implementation record's own capture;
recorded as a plain observation, not a discrepancy, since neither
transcript claims exit-code 0.)

**No writes into the target repo's tree or this checkout's `runs/`.**

derived: `git status --porcelain -- runs/` (worktree, immediately after
the reproduction above) — result: empty (exit 0). No file was added.

**Ported test-isolation fix — spot-checked, not re-executed as a
before/after pair** (the "before fix" state is not reachable on the PR
branch itself; independently confirmed via the surrounding evidence
instead): `pytest.ini` sets `addopts = -n auto` (confirmed by reading
the file in the worktree) and `spawn.ROLE_MODEL_CONFIG = ROOT /
"role_model.txt"` is a single fixed path (confirmed by grep) — both
preconditions for the claimed xdist race are real. `git diff
main..pr-2366-check -- tests/_spawn_test_support.py` (this session, same
worktree) shows `isolated_role_model_config()` patches
`spawn.ROLE_MODEL_CONFIG` to a private `tempfile.mkdtemp()` path per
test, which is a sound fix for that race shape. The gate's 86-pass
result above is consistent with the fix working; this record does not
independently re-run the "before fix" 2-failed state, since reproducing
it would require reverting the ported test-support changes on the PR
branch, which is outside "independently re-run what's here" scope.

## Why

`defect-verification-independence-from-upstream-verdicts`: the value of
an execution-observation record is in re-deriving figures before reading
the upstream claim, not in restating it — so every command above was run
in a scratch location distinct from the implementation record's own
(different issue numbers, different scratch paths), and its output
compared against the implementation record's claims only afterward. Per
`gate_c_status: N/A` in this role's spec (`execution-observation.spec.json`),
this role's judgment is mechanical recomputation over already-run test
claims, not a discretionary finding — so this record's job is
re-execution and worst-case aggregation, not a design review of the
change (that is `conformance-review`'s job).

## Upstream basis

`docs/issue-2291/reports/implementation.md` — untracked on this
`issue-2291/execution-observation` branch, since PR #2366 has not yet
merged to `main` — (this same commit's citation target, `sha:
3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d`, PR #2366's head; read via
`git show pr-2366-check:docs/issue-2291/reports/implementation.md` in
this session) is the record this observation independently re-executes
against. `spawn.py`, `roster.py`, `watchdog.py`,
`tests/_spawn_test_support.py`, and `tests/test_spawn_pipeline.py` at
that same head commit are the code under observation.

canonical: `gh pr list --search "2291" --state all` (this session) —
result:
```
2371	issue-2291: builder-blind conformance review of PR #2366	issue-2291/conformance-review	OPEN	2026-08-25T07:14:09Z
2366	issue-2291: durable spawn-attempt trace + watchdog pre-workspace halt visibility	issue-2291/implementation	OPEN	2026-08-25T05:52:26Z
2365	issue-2291: builder-blind conformance review of PR #2305	issue-2291/conformance-review	CLOSED	2026-08-25T05:30:58Z
2362	issue-2291: independent execution-observation of PR #2305's traceless-bootstrap-fix acceptance	issue-2291/execution-observation	MERGED	2026-08-25T05:20:45Z
2305	issue-2291: durable spawn-attempt trace + watchdog pre-workspace halt visibility	issue-2291/implementation	CLOSED	2026-08-25T02:09:05Z
```
Prior art (not re-verified beyond this state check — this record stands
on its own re-execution above, not on trusting those PRs' content): PR
#2305 (closed, unmerged, base invalidated by the 2026-08-25
co-author-trailer history rewrite per the implementation record), PR
#2362 (independent execution-observation of #2305, MERGED), PR #2365
(builder-blind conformance review of #2305, CLOSED). PR #2371
(builder-blind conformance review of this same PR #2366) is OPEN and
out of scope for this record — a separate role's output.

## Open findings

None. No resolution path is needed — derived: see the per-item
re-execution results in `## What was done` above (this record); every
Acceptance item and every test-count claim cited by the implementation
record reproduced under this session's own independent re-execution,
with no divergence found.

## Next steps

None — derived: see `## What was done` above (this record); nothing
outstanding. `loop_state: handed-off`.
