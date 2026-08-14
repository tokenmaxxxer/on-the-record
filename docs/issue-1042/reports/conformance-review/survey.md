---
kind: survey
loop_state: draft-reported
---

## Current-state survey

canonical: `gh issue view 1042`, executed live this session.

Issue #1042 (closed) cites requirement R001 (multi-session/multi-machine
correctness family). Fix direction: replace
`git branch -a --list "issue-{n}/*"` in
`spawn.py::require_requirement_linkage` with an exact-ref check
(`git for-each-ref`), so a remote-only `issue-N/...` branch is
detected as already-spawned instead of misread as never-spawned.
Acceptance: `python3 -m pytest tests/test_spawn.py -k remote_branch`.

canonical: `git log origin/issue-1042/implementation --oneline -3`, executed live this session.

```
fb505bd7 issue-1042 phase-2: for-each-ref branch-existence check delivery (#1058)
```

canonical: `gh pr view 1058`, executed live this session.

fb505bd7 is the implementation-branch commit landed after PR #1058
merged.

canonical: `find docs/issue-1042/reports -iname '*conformance*'`, executed live this session — no matches.

No conformance-review record file exists yet under
docs/issue-1042/reports (a path, not yet a file) on this branch. The
board condition (issue-521: implementation commit landed, no
conformance-review record for its sha) is met.

canonical: spawn.py:1058-1061, read this session.

```
    br = subprocess.run(
        ["git", "for-each-ref",
         f"refs/heads/issue-{issue}/**", f"refs/remotes/*/issue-{issue}/**"],
        cwd=root, capture_output=True, text=True)
```

canonical: `docs/issue-1042/reports/implementation.md`'s `code_under_review` frontmatter field, read this session.

The write set the implementation report declares is `spawn.py`,
`tests/test_spawn.py`.

canonical: `grep -n "RequireRequirementLinkageRemoteBranch" tests/test_spawn.py`, executed live this session.

`tests/test_spawn.py` carries a `RequireRequirementLinkageRemoteBranch`
test class at tests/test_spawn.py:10750, covering both acceptance
cases named in the issue body (remote-only branch detected as
already-spawned; no branch anywhere falls through to the
requirement-linkage check).

## Scout note

canonical: `gh issue view 1042`, executed live this session (see body quoted above).

Skipped — pure conformance check against a single, already-fully-specified
requirement (R001) and issue #1042's stated fix direction/acceptance
criteria; no design decision is open in extracting the requirement list.
