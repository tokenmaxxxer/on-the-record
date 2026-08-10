---
status: proposed
files:
  - spawn.py
  - test_spawn.py
---

Skip condition: pure bugfix (contract v3 scout-directive) — see
docs/issue-576/reports/implementation/survey.md for the recorded skip
reason and root-cause trace.

## Request

`spawn.py watch`'s `pr-opened` event resolves to an already-merged PR
instead of the newly opened one, when a role session reuses a head
branch whose earlier round's PR already merged (4 reproductions logged
in issue #576). Fix the resolution so it reports the OPEN PR the armed
session itself created; add a regression test for the branch-reuse
scenario; report (not fix) two separately observed symptoms — a stall
report on an already-completed session, and a DEAD watcher — since
neither has enough repro detail in the issue to diagnose safely.

## Constraints

- Do not change `_pr_for_branch`'s existing `--state all` semantics or
  signature: `approve_scope` (spawn.py:1225) depends on it matching a
  merged PR when approval lives on an already-merged phase-1 PR.
- Do not touch `_merged_pr_for_branch` / `_pr_open_or_merged_for_branch`
  — different callers, different intentional state filters, out of
  scope.
- Preserve the existing per-session memoization behavior at the
  `_watch` call site (spawn.py:4355-4362): one `gh` call per session
  while the PR is unresolved, no re-query per candidate URL once
  resolved.

## Accumulation

This adds one more `gh pr list --head <branch> --state <X>` subprocess
call variant (`_open_pr_for_branch`) beside the three that already exist
(`_pr_for_branch`, `_merged_pr_for_branch`,
`_pr_open_or_merged_for_branch`) — each a few-line wrapper around the
same `gh pr list ... --json number ...` shape with a different `--state`
filter and a docstring naming the one caller that needs it. This is the
file's established convention for this exact axis (state filter x
caller intent), not ad-hoc inline `gh` calls: four such wrappers is not
a growth pattern that needs consolidating, since each one exists because
a past incident (issue #60, #484, #576) showed the *other* filters were
wrong for that specific caller. If a fifth distinct `--state` need shows
up, or any of these wrappers grows call sites beyond the one each has
today, that is the trigger to extract a shared
`_pr_for_branch_impl(root, branch, states: set[str])` and have all four
call it — not before, since premature sharing here is what caused the
original bug (one shared function serving two callers with incompatible
state needs).

## Rationale

Two approaches were considered:

1. **Add `--state open` to `_pr_for_branch` itself.** Rejected: it has a
   second caller, `approve_scope` (spawn.py:1225), which intentionally
   needs `--state all` — an approval can legitimately live in comments
   on an already-merged phase-1 PR. Narrowing the shared function would
   silently break that caller's correctness (a scope approval posted on
   a merged PR would stop being found).

2. **Introduce a new `_open_pr_for_branch` helper (chosen)**, mirroring
   the file's existing convention (`_merged_pr_for_branch`,
   `_pr_open_or_merged_for_branch`: one function per needed `--state`
   filter, each with its own docstring recording which caller needs it
   and why) and swap only the `_watch` `pr-opened` call site
   (spawn.py:4378) to use it. This isolates the fix to the one call site
   that actually wants "open PR only" semantics, leaves
   `approve_scope`'s behavior untouched, and matches the pattern already
   used by `ensure_pushed` (spawn.py:3994, `--state open`, with its own
   comment citing the analogous past incident, issue #60).

## What will be done

- Add `_open_pr_for_branch(root: Path, branch: str) -> int | None` near
  `_pr_for_branch` (spawn.py, around line 1074-1101), using
  `gh pr list --head <branch> --state open --json number -q
  ".[0].number"`.
- Change the `_watch` pipeline's `pr-opened` resolution (spawn.py:4378)
  from `_pr_for_branch(Path(cwd), br)` to
  `_open_pr_for_branch(Path(cwd), br)`.
- Update `test_spawn.py`'s `_run` helper (class around line 2203) to
  patch `spawn._open_pr_for_branch` instead of `spawn._pr_for_branch`
  for the `_watch` pipeline test suite, keeping its existing
  `pr_for_branch=` parameter name and all currently-passing tests
  (lines 2722-2800) green against the new patch target.
- Add one new regression test reproducing the issue's acceptance
  criterion directly: a head branch with an existing MERGED PR and a
  newly OPENED PR on the same branch — assert the `pr-opened` event's
  reported URL is the new PR's, not the merged one's (exercised through
  the mocked `_open_pr_for_branch` returning only the open PR's number,
  matching how `gh pr list --state open` would behave against that
  fixture).
- Run the full test suite (`pytest` / project's existing runner) and
  report fenced output.

## Out of scope

- The stall-report and DEAD-watcher symptoms mentioned in the task
  prompt — reported back to the user as separate findings needing their
  own issue with concrete repro evidence, not fixed here.
- Any change to `approve_scope`, `_merged_pr_for_branch`,
  `_pr_open_or_merged_for_branch`, or `ensure_pushed`.
- Issue #557 (cursor scoped to armed session) and #554, referenced in
  #576 as "same family" — different lookup, not touched.

## How you'll know it worked

- New regression test reproduces the exact acceptance scenario (merged
  PR exists on same head branch, new PR opened) and fails against the
  pre-fix `_pr_for_branch` call site, passes against
  `_open_pr_for_branch`.
- Full existing `_watch`/`pr-opened` test suite (spawn.py:2722-2800 and
  neighbors) still passes unmodified in behavior, only its patch target
  renamed.
- `approve_scope`'s own tests (test_approve_scope.py) are unaffected —
  `_pr_for_branch` signature and behavior unchanged.
