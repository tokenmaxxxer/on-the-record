---
proposal: docs/issue-1154/proposals/watcher-autoarm-detached.md
---

# Hunt record — watcher-autoarm-detached

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: NO FINDING
Seed: docs/issue-1154/proposals/watcher-autoarm-detached.md, docs/issue-1154/reports/implementation/survey.md, spawn.py _spawn_one() auto-arm block (~5903-5944) vs _rearm_watcher_detached() (~3948-4012)
cap_seconds: 60
tier: default
diff_stat_lines: docs-only (proposal + survey, no code diff yet)
started_at: 2026-08-13T00:00:00Z
ended_at: 2026-08-13T00:20:00Z

Checked: (1) whether any code between the watcher Popen() and the
proposed immediate `return 0` still re-ties the watcher to the caller
(e.g. missed setsid, shared fds, blocking `with` context) — none found;
`with watcher_log.open() as wf:` closes before return, matching
`_rearm_watcher_detached()`'s identical pattern exactly. (2) whether
existing tests in tests/test_spawn.py pin the *current* blocking
default (no_wait=False) behavior of the auto-arm parent branch such
that the fix would silently break coverage outside the proposal's
declared write set (spawn.py + gates/test_watch_rearm_registry.py) —
grepped every `os.fork` mock + `_await_bounded` mock combination in
tests/test_spawn.py exercising the real parent branch (fork mocked to
a nonzero pid): all of them (lines ~4986, ~5031, ~8846-driven cases)
already pass `no_wait=True`, so none assert the default path's
`_await_bounded` call — no test would break, so no repro. (3) whether
the fix's core mechanism (return immediately after
`start_new_session=True` Popen, no self-setsid) actually survives a
caller-bounding kill, via two direct OS-level repros: (a) SIGKILL to
the whole process group of the arming process — watcher (separate
session via `start_new_session=True`) survives; (b) a psutil
descendant-tree kill issued after the arming process has already
exited (the realistic case, since the arming process's own exit is
what ends the bounded call) — by then the watcher has already been
reparented to init and no longer shows up under the dead arming pid's
subtree, so it survives that too. Both repros back the proposal's
claimed fix rather than exposing a bypass. Did not find a case where
the immediate-return shape still leaves the watcher joined to the
caller's lifetime.

### Reproduce (support, not a finding)
python3 /tmp/repro_pg.py    # pgid-kill: watcher survives
python3 /tmp/repro_tree.py  # descendant-tree-kill after arming exit: watcher survives
