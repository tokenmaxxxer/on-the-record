---
proposal: docs/issue-1042/proposals/for-each-ref-branch-check.md
---

# Hunt record — for-each-ref-branch-check

## after-proposal — stance 1: assume the write set frozen in this proposal cannot carry the work it describes — find the path the build will need that the proposal does not list.

Verdict: NO FINDING
Seed: docs/issue-1042/proposals/for-each-ref-branch-check.md (commit 7c38100, docs-only diff)
cap_seconds: 60
tier: default
diff_stat_lines: 64
started_at: 2026-08-12T14:30:00+09:00
ended_at: 2026-08-12T14:31:30+09:00

Checked: require_requirement_linkage (spawn.py:1020-1057) constructs the
buggy `git branch -a --list` call inline with plain `subprocess.run`, no
shared helper imported — the swap to `for-each-ref` is a self-contained
edit inside spawn.py, no new file needed. gates/remediation_spawn.py is
cited only as an existing convention (`_branch_exists`, refs/heads +
refs/remotes/*/), not as code spawn.py imports or must modify — spawn.py
already does its own `sys.path.insert` + `import ci as _ci` /
`import requirement_linkage as _requirement_linkage` for other gates
but there is no such import for remediation_spawn, and the proposal does
not ask for one. Checked tests/test_spawn.py for a remote-branch test
fixture requirement: `test_checkout_tracks_origin_only_branch` (line
~1271) already builds an origin+clone pair with `_init_repo`/`_git`
helpers defined in the same file — the same helper pattern the two new
regression tests need, with no external conftest.py or fixture file.
grep for `git branch -a` / `for-each-ref` across *.py found only the two
proposal-cited sites (spawn.py's buggy call, gates/remediation_spawn.py's
existing correct one) — no other call site of the same buggy pattern
needing simultaneous fixing. Write set (spawn.py, tests/test_spawn.py) is
sufficient.
