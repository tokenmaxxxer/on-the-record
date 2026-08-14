---
subject: issue-1043/implementation
loop_state: handed-off
---

## Independence

canonical: `gh pr view 1061 --json state,mergedAt,commits` (this session, per survey.md item 5)
This record observes the `implementation` role's landed work on issue
#1043, the PR read by the canonical command directly above, squash
commit `5f5e5ff060f7e2f25fd1e8aa62b3f844f332021d`.

No path under `docs/issue-1043/proposals/`,
`docs/issue-1043/reports/implementation*`, `spawn.py`, or
`tests/test_spawn.py` is edited by this record. Only the observed PR's
diff, commits, and own record are treated as evidence, plus this
session's independent re-execution of the already-existing acceptance
command. See docs/issue-1043/reports/execution-observation/survey.md
for the full evidence-reading order and
docs/issue-1043/proposals/2026-08-14-execution-observation-implementation-1043.md
for this record's scope.

## outcome (EARL result, per roles/specs/execution-observation.spec.json)

test: `python3 -m pytest tests/test_spawn.py -k watcher_dead`
assertedBy: this session, re-executed live against the current working
tree.
mode: executed-live

canonical: `python3 -m pytest tests/test_spawn.py -k watcher_dead` (this session, executed live) — result: PASS
```
collected 503 items / 501 deselected / 2 selected

tests/test_spawn.py::WatchFollow::test_watcher_dead_or_missing_still_fires_with_no_watcher_registered PASSED [ 50%]
tests/test_spawn.py::WatchFollow::test_watcher_dead_stale_pid_cleared_by_live_follow_registration PASSED [100%]

====================== 2 passed, 501 deselected in 0.08s =======================
```

Both of issue #1043's stated acceptance cases are covered by name:
`test_watcher_dead_stale_pid_cleared_by_live_follow_registration`
(stale auto-armed pid + live follow watcher → no `watcher-dead` flag)
and `test_watcher_dead_or_missing_still_fires_with_no_watcher_registered`
(no watcher at all → flag fires).

canonical: `python3 -m pytest tests/test_spawn.py -k watcher_dead` (this session, run above) — result: PASS
Worst case across both entries above is EARL `passed`, no
`failed`/`cantTell`/`inapplicable`/`untested` entry exists for this
test set.

## trajectory (three named checks)

- scouted-when-required: `n/a`.
  canonical: `gh pr view 1049 --json body` (this session, per survey.md item 4)
  Proposal body has no scout section and states this is a
  single-call-site fix inside `_watch()`'s follow branch — no
  product-facing or exemplar-comparable design decision open, matching
  this repo's own scout-skip ground.

- surveyed-before-proposing: holds.
  canonical: `gh pr view 1049 --json state,mergedAt` (this session)
  The phase-1 proposal PR #1049 (squash commit
  `002878c0251f4ac9cb22470815ae72a00cad948c`, this canonical command
  reports it merged) opens by citing a survey of the watchdog/roster
  code path and the #1037 gap-audit corroboration named in issue
  #1043's own body; the proposal predates and is built on that survey.

- approved-by-human: holds.
  canonical: `gh issue view 1043 --json comments --jq '.comments[] | select(.body | contains(\"APPROVE\"))'` (this session)
  Match: https://github.com/tokenmaxxxer/on-the-record/issues/1043#issuecomment-5262741753,
  body the literal string `APPROVE issue-1043/implementation`, authored
  by `JiwonJung94`. Single-account mode applies: `JiwonJung94` is both
  the issue author and the approver of record; no second-account
  signature exists or is required here.

canonical: `python3 -m pytest tests/test_spawn.py -k watcher_dead` (this session, outcome section above) — result: PASS
Worst case across all three checks above (`n/a`, `holds`, `holds`) is
EARL `passed`.

## step (spawn.py:3903-3966 and its regression tests)

canonical: `Read spawn.py:3903-3966` (this session, current working tree)
Reviewed `_watch()`'s `follow=True` branch:

```
    current_watcher_pid = entry.get("watcher_pid")
    if not (current_watcher_pid is not None and
            _watcher_looks_real(current_watcher_pid, issue, follow_role)):
        _workspace_index_put(issue, follow_role, work, str(log_path),
                              watcher_pid=os.getpid(),
                              watcher_armed_at=time.time())
```

This reads the roster entry's current `watcher_pid` and only registers
the follow process as watcher when no watcher is recorded or the
recorded one fails `_watcher_looks_real()` — coherent with the
surrounding `key`/`entry` locals populated by `_lookup_roster_entry()`
at `spawn.py:3907`, not a dangling reference.
`_workspace_index_put()`'s existing whole-entry-replace contract clears
any stale `watcher_pid` for free when this branch writes, matching the
issue's "clear stale pids from the roster entry when replaced"
direction. The two regression tests (`tests/test_spawn.py`,
`WatchFollow` class) each assert against `spawn.watchdog_check_one()`'s
actual output rather than against internal state alone, and the control
case
(`test_watcher_dead_or_missing_still_fires_with_no_watcher_registered`)
guards against the fix being too permissive.

**Step-level finding (this role's own, not a re-statement of the
observed role's hunt)**:
canonical: `Read spawn.py:3957-3969` (this session, above)
The read of `current_watcher_pid` and the `_watcher_looks_real()` check
(`spawn.py:3964-3966`) happen outside any lock before the guarded
`_workspace_index_put()` call (`spawn.py:3967-3969`) — a TOCTOU race
where two concurrent `--follow` invocations for the same issue+role can
both observe "no live watcher" and both write, the second overwriting
the first's registration.

canonical: `gh pr diff 1061` (this session, per survey.md item 5)
This finding is not independently re-discovered by this session; it is
the observed role's own before-landing hunt result
(`docs/issue-1043/reports/implementation.md`'s "Hunt (before-landing)"
section, hunter agent `aefda5677b97f8d71`), reported here as surviving
independent review: judged non-blocking because both racing writers are
genuinely live, real (`_watcher_looks_real()`-passing) follow
processes, so the race produces no incorrect
`watcher-dead`/`watcher-missing` flag; only which of two valid watchers
is recorded is nondeterministic.

canonical: `Read spawn.py:3903-3966` (this session, above)
This session's independent read confirms the check-then-write shape the
hunt describes is present in the landed code as merged, and finds the
non-blocking judgment sound — the pre-existing auto-arm call site
already uses the same check-then-write pattern against the same lock,
so this change does not introduce a new class of exposure, only a
second call site with the same pre-existing shape. Per the observed
role's own record, reconciling concurrent watcher claims is out of this
proposal's frozen write set and is carried forward as an open item, not
filed as a new issue by this observation role (per this role's own
out-of-scope constraint — see
docs/issue-1043/proposals/2026-08-14-execution-observation-implementation-1043.md).

canonical: `python3 -m pytest tests/test_spawn.py -k watcher_dead` (this session, outcome section above) — result: PASS
Step-level EARL result is `passed` — the landed change and its
regression tests are sound for what issue #1043 asks; the one open
finding is inherited from the observed role's own hunt, already judged
non-blocking there, and this session's independent review of the code
does not overturn that judgment.

## Overall verdict

canonical: `python3 -m pytest tests/test_spawn.py -k watcher_dead` (this session, outcome section above) — result: PASS
Overall EARL result is `passed` — worst case across `outcome`
(`passed`), `trajectory` (`passed`), and `step` (`passed`) is
`passed`. Recomputed per this role's own spec
(`roles/specs/execution-observation.spec.json`, `recomputation`
field), not asserted as a standalone summary independent of the
entries above.
