---
status: proposed
files:
  - spawn.py
  - tests/test_spawn.py
---

Scout note: skipped — pure bugfix (fix direction and acceptance criteria
are fully specified in issue #1042; no design decision is open).

## Request

#1042: `spawn.py::require_requirement_linkage` checks whether an issue
was ever spawned by running `git branch -a --list "issue-{n}/*"`. With
`-a`, remote branches list as `remotes/origin/issue-N/...`, which that
glob does not match, so a remote-only branch (fresh clone, another
machine's spawn) is misread as never-spawned.

## Constraints

- Exact-ref check, matching `gates/remediation_spawn.py`'s existing
  convention (per the issue's fix direction).
- No behavior change for the already-working local-branch case.

## Rationale

Considered keeping `git branch -a --list` but adding a second
`--list "*/issue-{n}/*"` pattern (the issue's first suggested fix).
Rejected: `git branch -a` output format (`remotes/origin/issue-N/...`
vs plain `issue-N/...`) is a display convention, not a machine-stable
contract, and matching against it is exactly the fragility that caused
this bug. `git for-each-ref refs/heads/issue-{n}/* refs/remotes/*/issue-{n}/*`
checks real ref namespaces directly and is what
`gates/remediation_spawn.py` already uses for the same kind of check.

## What will be done

Replace the `git branch -a --list` call in
`require_requirement_linkage` with
`git for-each-ref "refs/heads/issue-{n}/*" "refs/remotes/*/issue-{n}/*"`.
Add two regression cases to `tests/test_spawn.py`: a remote-only
`issue-N/...` ref is detected as already-spawned (no `sys.exit`), and
no local/remote branch at all is not spawned (falls through to the
requirement-linkage check).

## Accumulation

This swaps one inline `subprocess.run(["git", ...])` call for another,
same call site, same shape — it does not add a new occurrence of the
pattern. If more issue-scoped branch-existence checks accumulate
elsewhere in `spawn.py`, they should converge on the same
`for-each-ref refs/heads/issue-{n}/* refs/remotes/*/issue-{n}/*` idiom
(matching `gates/remediation_spawn.py`'s existing convention) rather
than each re-deriving their own `git branch -a --list` glob; a third
occurrence would be the trigger to factor it into a shared helper.

## Out of scope

Any other `git branch -a` usage elsewhere in the codebase not cited by
the issue.

## How you'll know it worked

`python3 -m pytest tests/test_spawn.py -k remote_branch` passes.
