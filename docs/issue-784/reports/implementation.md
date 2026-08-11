---
code_under_review:
  - spawn.py
  - on-the-record/hooks/absorbed-branch-recut-guard.sh
  - tests/test_spawn.py
  - on-the-record/hooks/test_absorbed_branch_recut_guard.py
  - docs/specs/enforcement-boundary.md
  - docs/specs/generated-paths.md
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue-784 phase 2

Subject: issue-784. Upstream: docs/issue-784/proposals/absorbed-branch-mid-run-recut.md
(approved via `APPROVE issue-784/implementation`).

## What was done

Delivered option (b) from the approved proposal: extended #732's
absorbed-branch detection so a running session's own mid-run work re-runs
the same 0-ahead-vs-base check `checkout_issue_branch()` performs at
spawn, right before the point where absorption would otherwise surface as
a silent "No commits" PR-create failure.

- Factored the existing local-branch-exists absorption check out of
  `checkout_issue_branch()` (spawn.py) into a shared helper
  `_recut_absorbed_branch(cwd, br)` — identical logic (local_zero /
  remote_stale_only detection, stash preserve/recut/pop, leftover-stash
  recovery), now callable from two sites, `checkout_issue_branch()`
  unchanged in behavior.
- Added a `spawn.py recut-if-absorbed -C <cwd>` CLI subcommand
  (`recut_if_absorbed_cli`) that derives the branch from the session's own
  `HEAD` (no roster, no cross-process lookup), fetches only that branch +
  base non-fatally, and calls `_recut_absorbed_branch`. No-ops (returns 0)
  when `HEAD` isn't an `issue-<n>/<role>`-shaped branch.
- Added `on-the-record/hooks/absorbed-branch-recut-guard.sh`, a
  `PreToolUse`/`Bash` hook matching the same `git commit`/`gh pr create`
  prefixes spawn.py already tracks via `_PROGRESS_BASH_PREFIXES`, shipping
  zero-install like `contract-guard.sh`. It shells out to
  `spawn.py recut-if-absorbed` before allowing the matched command
  through, so the recut runs synchronously inside the session's own
  process — not the parent's post-hoc transcript scan the after-proposal
  hunt found broken. Fail-open when `spawn.py` isn't present in the
  checkout (non-self-hosted consumer repos) or the recut attempt itself
  fails — never denies, only ever adds a recut.
- Registered the new hook module in `docs/specs/enforcement-boundary.md`
  and `docs/specs/generated-paths.md` (`gate-registration-guard.sh`
  requires a row for any newly-staged `on-the-record/hooks/*.sh`; both are
  `docs/` paths, writable regardless of the frozen write set per the
  warrant directive).
- Added a new `AbsorbedBranchRecutMidRun` test class in `tests/test_spawn.py`
  for `_recut_absorbed_branch`/`recut_if_absorbed_cli`, mirroring the
  existing `test_checkout_recuts_when_truly_fully_absorbed_local_and_remote`
  / `test_checkout_recuts_absorbed_branch_and_preserves_untracked_files`
  shape, plus `on-the-record/hooks/test_absorbed_branch_recut_guard.py`,
  invoking the hook script directly against a fixture repo in the
  merged/absorbed state, asserting it recuts before exiting 0 (allow),
  including a `cd <dir> && git commit` compound-command case (added after
  the before-landing hunt below). Counts: see Test evidence below.

## Why

Per the approved proposal's Rationale: direction (a) (merge-time roster
read) was rejected as fragile — `contract-guard.sh` is zero-install and
cannot assume co-location with `spawn.py`'s roster file. Direction (c)
(directive-only) was rejected — no mechanical gate exists to enforce it.
Direction (b), delivered here, reuses tested, already-landed absorption
detection as pure git state on the session's own workspace, adding only
*when* the check re-runs (a synchronous `PreToolUse` hook, the
interposition point the after-proposal hunt corrected the proposal to
use), never new detection machinery.

## Upstream

docs/issue-784/proposals/absorbed-branch-mid-run-recut.md

## Kind

feature

## loop_state

landed

## Hunt record

Before-landing hunt (stance 2, docs/issue-784/reports/implementation/2026-08-11-hunt-before-landing-absorbed-branch-mid-run-recut.md):
FINDING — the `git commit` match used an anchored `str.startswith`, so a
compound command (`cd <dir> && git commit ...`) never matched and the
guard silently skipped the recut. Fixed in the same commit: switched to
`re.search(r"(?:^|&&)\s*git\s+commit\b", cmd)` plus a `cd <path> &&`
prefix parse (mirroring `contract-guard.sh`'s own target-repo
resolution) so the extracted `target_cwd` follows the `cd`. Regression
test added: `test_recuts_absorbed_branch_for_cd_prefixed_commit`.

closed_checks:
- check: before-landing warrant hunt, stance 2 (malformed/compound-command
  input silently skipping the guard)
  code_sha: (this record's `code_under_review:` file list, post-fix)
  result: finding fixed and covered by a new regression test

## Open findings

None outstanding — the one before-landing finding above was fixed in this
delivery and covered by a new test.

## Test evidence

derived: python3 ./tests/test_spawn.py
```
Ran 339 tests in 21.037s

OK
```

derived: python3 -m pytest on-the-record/hooks/test_absorbed_branch_recut_guard.py -q
```
.....                                                                    [100%]
5 passed in 0.86s
```

derived: python3 -m pytest gates/test_boundary.py gates/test_generated_paths.py -q
```
..............                                                           [100%]
14 passed in 0.06s
```

## What did not work

- First draft of the hook's Python extraction snippet matched `git commit`
  with an anchored `cmd.lstrip().startswith("git commit")` (mirroring
  `_PROGRESS_BASH_PREFIXES`'s own plain-startswith semantics) and used
  `os.getcwd()` unconditionally for `target_cwd`, with no `cd`-prefix
  resolution. Expected: matches every `git commit` the session's Bash tool
  runs. Actual: the before-landing hunt found a `cd <dir> && git commit`
  compound command never matched at all, silently skipping the recut —
  replaced with a `re.search` pattern plus explicit `cd <path> &&` prefix
  parsing (mirroring `contract-guard.sh`'s existing target-repo
  resolution) before landing.
