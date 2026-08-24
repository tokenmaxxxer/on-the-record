---
proposal: docs/issue-2195/proposals/2026-08-24-auto-sweep-background-dispatch.md
---

# Hunt record — auto-sweep-background-dispatch

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — backgrounding `auto_sweep` defeats the issue-#2186 `bootstrap_timing` visibility gate for the `auto_sweep` phase: it now unconditionally reports ~0.000s no matter how long the real sweep runs, and nothing else logs the real duration, so a future 148s-class regression in `auto_sweep` (the exact failure #2195 fixed) is once again invisible.
Kind: silent-failure
Seed: `git diff -- spawn.py` (+22/-6 in `_spawn_one`'s `with _timed("auto_sweep"):` block) plus new `tests/test_auto_sweep_nonblocking.py`
cap_seconds: 120
tier: default (size:21-200-lines bucket)
diff_stat_lines: 183 (28 in spawn.py + ~155 new in tests/test_auto_sweep_nonblocking.py)
started_at: 2026-08-24T21:21:37+09:00
ended_at: 2026-08-24T21:24:10+09:00

### Reproduce
Ran `_spawn_one()` end-to-end (mirroring the new test's own harness) with `spawn.auto_sweep` mocked to a function that blocks for 2.000s before returning, and printed both the emitted `bootstrap_timing` line and whatever spawn.py itself logs during/after that 2s window:

```
python3 - <<'PY'
import sys, time, threading, tempfile, subprocess
from pathlib import Path
from unittest import mock
sys.path.insert(0, ".")
import spawn

def _prep_repo(td, name="work"):
    work = Path(td) / name
    work.mkdir()
    run = lambda *a: subprocess.run(a, cwd=str(work), capture_output=True, text=True, check=True)
    run("git", "init", "-q"); run("git", "config", "user.email", "t@example.com")
    run("git", "config", "user.name", "t"); (work / "f.txt").write_text("x")
    run("git", "add", "f.txt"); run("git", "commit", "-q", "-m", "init")
    return work

_NO_SKILLS = {"source": "skill-repo", "skill_dirs": [], "skills": [], "skill_sha": None}
started = threading.Event(); release = threading.Event()

def slow_auto_sweep(wb, max_age_days, max_bytes):
    t0 = time.monotonic(); started.set(); release.wait(2.0)
    dur = time.monotonic() - t0
    with open("/tmp/real_sweep_duration.txt", "w") as f:
        f.write(f"real sweep took {dur:.3f}s\n")

td = tempfile.TemporaryDirectory()
spawn.ROSTER = Path(td.name) / "active.json"
spawn.WORKSPACE_INDEX = Path(td.name) / "workspaces.json"
with tempfile.TemporaryDirectory() as td2:
    work = _prep_repo(td2)
    spawn._BOOTSTRAP_TIMING.clear()
    with mock.patch.object(spawn, "issue_workspace", lambda cwd, issue, role: str(work)), \
         mock.patch.object(spawn, "checkout_issue_branch", lambda cwd, issue, role: "b"), \
         mock.patch.object(spawn, "resolve_role_source", lambda role, repo_root: _NO_SKILLS), \
         mock.patch.object(spawn, "core_plugin_dirs", lambda: []), \
         mock.patch.object(spawn, "core_version", lambda: "v0"), \
         mock.patch.object(spawn, "_clean_auto_enabled", lambda: True), \
         mock.patch.object(spawn, "auto_sweep", slow_auto_sweep), \
         mock.patch.object(spawn, "spawn_cmd", lambda *a, **k: (["cat"], {})), \
         mock.patch.object(spawn, "_release_spawn_claim", lambda *a, **k: None), \
         mock.patch.object(spawn, "_rewrite_spawn_claim_pid", lambda w: None), \
         mock.patch.object(spawn, "_await_bounded", lambda *a, **k: 0), \
         mock.patch.object(spawn, "_undispositioned_role_prs", lambda root, exclude_issue=None: ([], True)), \
         mock.patch.object(spawn, "ledger_write", lambda *a, **k: None):
        rc = spawn._spawn_one(str(work), "implementation", "test\n",
                               unattended=True, issue=31, bounded=False,
                               no_wait=True, single_phase=False)
    print("BOOTSTRAP TIMING LINE:", spawn._bootstrap_timing_line("qa"))
    print("auto_sweep phase value:", spawn._BOOTSTRAP_TIMING.get("auto_sweep"))
started.wait(2.0); release.set(); time.sleep(0.3)
print(open("/tmp/real_sweep_duration.txt").read())
PY
```

### Observed
```
BOOTSTRAP TIMING LINE: [qa] bootstrap_timing ... auto_sweep=0.000 ... total=11.529
auto_sweep phase value: 0.00012617278844118118
real sweep took 2.000s
```
`spawn.py`'s own emitted `bootstrap_timing` line (the exact diagnostic line issue #2186 added to `_spawn_one` precisely so a phase this expensive could never again hide inside `total`) reports `auto_sweep=0.000` while the sweep is, in fact, still running for a further ~2s in a detached daemon thread. Nothing in spawn.py's stdout/stderr ever reports that real 2.000s figure — the only place it appears is a side-channel file I added purely to prove the number exists and is simply discarded. In production this side-channel does not exist: the real duration of `auto_sweep` is now unrecoverable from spawn's own logs no matter how long it runs.

### Expected
Either (a) the background thread should log its own completion time (e.g. `print(f"[{role}] auto-sweep 완료: {dur:.1f}s", file=sys.stderr)` alongside the existing failure-path print), so a regression back to 148s-class sweeps is still visible somewhere, or (b) `bootstrap_timing`'s `auto_sweep=` field should be understood/documented as "dispatch cost only, not sweep cost" so nobody reading a `bootstrap_timing` line mistakes a fast `auto_sweep=0.000` for "the sweep was fast" the way #2186's own phase-naming exercise trained readers to. As shipped, the diff silently repeats — for exactly the phase issue #2195 was filed about — the same "hidden time behind a near-zero phase" failure mode that issue #2186 was filed to eliminate for the other eight phases.
