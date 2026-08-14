---
subject: issue-1360
---

# Current-state survey — issue #1360

Skip condition (scout-directive): pure bugfix, issue body already fully
specifies the fix. Scouting skipped on that basis.

## Write set

canonical: `sed -n '1,50p' gates/spawn_on_pr.py` (pre-change working tree)
`missing_verification()` filters only on `applicable_roles` and
`spawn._pr_open_or_merged_for_branch`. `spawn_missing_for_pr()` spawns
every returned pair uncapped. File has no `argparse`/`__main__` block.

canonical: `sed -n '2694,2716p' spawn.py` (pre-change working tree)
`_board_wide_sweep()` calls `spawn_on_pr.spawn_missing_for_pr(root,
str(root))` before its own `closure_sweep.issue_state_index_all(root)`
call.

canonical: full read of tests/test_spawn_on_pr.py this session
Existing fixture tests build one open-PR subject (`issue-9001`) via
`spawn._pr_open_or_merged_for_branch` monkeypatch only, no issue-state
setup.

derived: `grep -n "spawn_on_pr" tests/test_merge_gate.py gates/test_closure_sweep.py`
```
(no output)
```

## Reusable machinery

canonical: `sed -n '137,172p' gates/closure_sweep.py` (pre-change working
tree) — `issue_state_index_all(root)` returns `(dict[int,str] | None, ok:
bool)` from one `gh issue list --state all` call.

## No design decision left open

canonical: gh issue view 1360 (read at session start)
Cap default 4; deferral = one line naming deferred count; backfill =
separate CLI subcommand, dry-run default; #1332–#1358 disposition out of
scope.
