---
proposal: none (build-now bypass, CORE_BUILD_NOW=1 -- issue #2201 is the authority)
---

# Hunt record — bootstrap-cross-family-returned-pr-gate

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the new `returned_pr_gate` fire-and-forget daemon thread almost never runs to completion in the real (bounded) CLI spawn path, so its only remaining function — surfacing undispositioned PRs / writing the `returned_pr_gate_fail_open` ledger event — is silently skipped every time, not just raced.
Kind: composition
Seed: git diff -- spawn.py consult.py (the `returned_pr_gate` ThreadPoolExecutor -> `threading.Thread(daemon=True)` conversion in `_spawn_one()`)
cap_seconds: 180
tier: full
diff_stat_lines: consult.py 32 (+28/-4), spawn.py 63 (+41/-22) — 2 files changed, 67 insertions(+), 28 deletions(-)
started_at: 2026-08-24T22:15:00Z
ended_at: 2026-08-24T22:33:00Z

### Reproduce

`spawn.py`'s real CLI entrypoint calls `_spawn_one(..., bounded=a.issue is not None, ...)` (line ~1507) and the module ends with `sys.exit(main())` — so every normal `spawn.py <role> "<task>" --issue <n>` invocation runs `_spawn_one(bounded=True, issue=<n>)`, and the interpreter tears down immediately once `main()` returns.

`_spawn_one()` starts the `returned-pr-gate` daemon thread near the top of the `if issue is not None:` block (spawn.py ~line 2362-2364), long before the `if bounded and issue is not None: child_pid = os.fork(); ...` block (~line 2757-2846). `os.fork()` only clones the calling thread — the `child_pid > 0` (parent) branch keeps the already-running daemon thread, does a few fast bookkeeping steps (arm watcher, `_workspace_index_put`), and does `return 0` from `_spawn_one()` by design (issue #1154: "bounded 부모는 즉시 리턴해야 한다"). Nothing joins the `returned-pr-gate` thread anywhere after that.

Standalone confirmation that CPython does not wait for daemon threads on normal or exceptional interpreter shutdown:
```
$ cat > /tmp/daemon_exit_test.py <<'PY'
import threading, time, sys
def slow():
    time.sleep(2.0)
    print("daemon thread finished its 2s sleep", file=sys.stderr)
threading.Thread(target=slow, daemon=True).start()
PY
$ time python3 /tmp/daemon_exit_test.py
# real 0m0.058s -- "daemon thread finished" never printed
```

Direct repro against the actual `_spawn_one()` code path (mirrors `tests/test_spawn_gate_wiring.py::ReturnedPRGateIsNonBlocking`'s own mocks, but exercises `bounded=True` — the value the real CLI always passes when `--issue` is given, which that new test never sets, so the test suite never observes this):
```python
# /tmp/repro_gate_bypass3.py
import sys, os, subprocess as sp, tempfile, time
sys.path.insert(0, os.getcwd())
import spawn, events
from pathlib import Path
from unittest import mock

td = tempfile.mkdtemp()
work = Path(td) / "issue-9-impl"
work.mkdir()
def run(*a):
    sp.run(a, cwd=str(work), capture_output=True, text=True, check=True)
run("git", "init", "-q"); run("git", "config", "user.email", "t@example.com")
run("git", "config", "user.name", "t")
(work / "f.txt").write_text("x"); run("git", "add", "f.txt")
run("git", "commit", "-q", "-m", "init")

spawn.ROSTER = Path(td) / "active.json"
spawn.WORKSPACE_INDEX = Path(td) / "workspaces.json"
events.WORKSPACE_INDEX = spawn.WORKSPACE_INDEX

marker = Path(td) / "gate_completed.marker"
GH_LOOKUP_SECONDS = 2.0
def slow_undispositioned_role_prs(root, exclude_issue=None):
    time.sleep(GH_LOOKUP_SECONDS)
    marker.write_text("done")
    return [], True

with mock.patch.object(spawn, "issue_workspace", lambda cwd, issue, role: str(work)), \
     mock.patch.object(spawn, "checkout_issue_branch", lambda cwd, issue, role: "b"), \
     mock.patch.object(spawn, "spawn_cmd", lambda *a, **k: (["cat"], {})), \
     mock.patch.object(spawn, "ensure_pushed", lambda *a, **k: None), \
     mock.patch.object(spawn, "roster_register", lambda *a, **k: None), \
     mock.patch.object(spawn, "_cross_family_skill_matches_with_consult",
                        lambda *a, **k: ([], "skipped-for-repro")), \
     mock.patch.object(spawn, "_undispositioned_role_prs", slow_undispositioned_role_prs), \
     mock.patch.object(spawn, "ledger_write", lambda entry: None):
    rc = spawn._spawn_one(str(work), "execution-observation", "task\n",
                          unattended=True, issue=9, bounded=True)

sys.stderr.write(f"=== marker written before _spawn_one() returned to caller? {marker.exists()} ===\n")
os._exit(rc)  # mimic sys.exit(main()) -- the real CLI's teardown right after main() returns
```
```
$ cd <repo> && python3 /tmp/repro_gate_bypass3.py   # run 3x
```

### Observed

All 3 runs: `_spawn_one(bounded=True, issue=9)` returns in ~0.11s while the background `gh`-backed lookup needs 2.0s.
```
=== _spawn_one(bounded=True) returned rc=0 after 0.109s (background gh lookup needs 2.000s to finish) ===
=== marker written before _spawn_one() returned to caller? False ===
```
After `os._exit(rc)` (mimicking the real `sys.exit(main())`), the marker file — which only the background thread's completion path writes, right alongside the same `returned-pr 게이트(백그라운드) ... 끝남` stderr line and the `ledger_write({"event": "returned_pr_gate_fail_open", ...})` call — was never created in any of the 3 runs' temp dirs, even checked several seconds later:
```
/tmp/tmp1j3rzd2y: marker exists = NO
/tmp/tmpqmc8ejml: marker exists = NO
/tmp/tmplfmu2h4w: marker exists = NO
```
No "returned-pr 게이트(백그라운드)" line appears in stderr in any of the 3 runs either. The gate's surfacing/ledger side effect silently never happens.

(By contrast, two *earlier* exploratory runs that happened to leave several seconds of wall time between thread-launch and process-exit — once because the real, still-synchronous `cross_family` phase made an actual `claude -p` call that took ~31s, once because of an incidental delay before a `_workspace_index_put` collision crash — did leave a marker file behind, confirming the thread's own logic is fine in isolation; the bug is purely that the real bounded/fork/fast-return path races it out almost every time.)

### Expected

The real `spawn.py <role> "<task>" --issue <n>` CLI path — the only path that matters, since it is what `bounded=a.issue is not None` targets — should reliably run the returned-pr surfacing/fail-open-ledger side effect to completion before the process exits, the same way the pre-#2201 `.result()`-joined design guaranteed. Instead, because the daemon thread is launched well before the `os.fork()` + immediate `child_pid > 0: ... return 0` bounded-parent-return, and nothing ever joins it, the gate's entire remaining purpose (surfacing undispositioned PRs, recording the fail-open ledger event) is now silently dropped in the common case — a strictly worse outcome than "non-blocking": it is close to "never happens" for `--issue`-driven spawns, the exact invocation pattern this repo's own tests (`ReturnedPRGateIsNonBlocking`, which never passes `bounded=True`) do not exercise.

### Resolution

Fixed on this same branch (spawn.py, the bounded-parent's single `return 0` in `_spawn_one()`, ~line 2846): the daemon thread is now captured in `_returned_pr_gate_thread` and joined with a bounded `.join(timeout=10.0)` immediately before that `return 0` — the only exit point the bounded/`--issue` CLI path (`os.fork()`'s `child_pid > 0` branch) actually takes. This restores the guarantee (the gh lookup almost always finishes and its surfacing/ledger side effect fires) while staying off the `returned_pr_gate` bootstrap_timing phase (still measures dispatch only) and off the spawned session's own path entirely (the fork already happened; the child session is independent of whatever the parent does next). 10.0s is a safety-margined bound over the issue's own measured 6.608s gh round-trip — strictly better than the pre-#2201 code's fully *unbounded* synchronous `.result()` wait on the same call. New regression test added:
`tests/test_spawn_gate_wiring.py::ReturnedPRGateIsNonBlocking::test_bounded_fork_parent_join_still_captures_a_slow_lookup` — mocks `os.fork()` to take the parent branch without a real fork (matching `test_spawn_board_flows.py`'s existing `_full_mock_scaffold` pattern), gives `_undispositioned_role_prs` a 1s artificial delay, and asserts the `returned_pr_gate_fail_open` ledger event is already present by the time `_spawn_one(bounded=True, issue=...)` returns. Verified this test fails (ledger stays empty) with the `.join(timeout=10.0)` line reverted, and passes with it restored — confirmed both directions this session.
