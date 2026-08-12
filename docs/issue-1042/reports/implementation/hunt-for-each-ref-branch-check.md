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

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — `git for-each-ref "refs/heads/issue-{issue}/*"` does not match branches nested more than one level below `issue-{issue}/`, unlike the old `git branch --list "issue-{issue}/*"` glob, so a prior spawn on a deeply-nested branch name is invisible to the new check and the "already spawned" retroactive-skip fails silently, causing require_requirement_linkage to wrongly treat an already-spawned issue as brand-new and block it.
Kind: silent-failure
Seed: spawn.py::require_requirement_linkage diff (git branch --list -> git for-each-ref), tests/test_spawn.py RequireRequirementLinkageRemoteBranch
cap_seconds: 120
tier: default
diff_stat_lines: 21-200 (bucket)
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:10:00Z

### Reproduce
```
rm -rf /tmp/ferf2 && mkdir /tmp/ferf2 && cd /tmp/ferf2 && git init -q && git commit -q --allow-empty -m init
git branch -q issue-1042/a/b/c
git for-each-ref "refs/heads/issue-1042/*"
echo "---"
git branch --list "issue-1042/*"
```

### Observed
`git for-each-ref "refs/heads/issue-1042/*"` prints nothing (no match), while
`git branch --list "issue-1042/*"` prints `issue-1042/a/b/c`. The two commands
disagree on whether the branch counts as a prior spawn of issue 1042. Any
issue whose spawned branch name has more than one path segment after
`issue-<n>/` (e.g. a role name containing a slash, or any deliberately
nested branch scheme) will be invisible to the new for-each-ref check, so
`require_requirement_linkage` falls through past the "already spawned"
early-return and applies the phase-1 requirement-linkage gate retroactively
to an issue that was, per the proposal's own stated intent, supposed to be
exempt.

### Expected
The for-each-ref pattern should match every branch that the old
`git branch --list "issue-{issue}/*"` glob matched (any nesting depth), since
the proposal states this is a drop-in replacement that also adds
remote-branch detection, not a narrowing of the local-branch match.
