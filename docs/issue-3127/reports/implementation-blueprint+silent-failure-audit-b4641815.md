---
issue: 3127
role: implementation-blueprint+silent-failure-audit-b4641815
author: implementation-blueprint+silent-failure-audit-b4641815
skills: implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # round-4 fix on PR #3169's own deliverable, addressing two open findings PR #3223's round-3 verification recorded but did not fix
code_under_review: 824bbf8fc57b96783c5e83ae818a87bff4325b1d
loop_state: landed
type: fix
breaking: false
verdict: fixed
upstream:
  - path: docs/issue-3127/reports/adversarial-review+silent-failure-audit+experiment-trust-97f69e0b.md
    sha: 6d1a233b74f0f19cc7ef5b7fdb26e9c7cf6a3d2b  # round-3 verification record (PR #3223), landed to main; frontmatter open findings 1 and 2 are this round's scope
---

# issue-3127 — implementation-blueprint+silent-failure-audit-b4641815 record

## What was done

canonical: `gh pr view 3223 --json body -q .body` and `git show 6d1a233b:docs/issue-3127/reports/adversarial-review+silent-failure-audit+experiment-trust-97f69e0b.md` — read first, per the task instructions, before touching PR #3169's branch.

Two changes to `scripts/issue-3127/verify_preregistration.py` on PR #3169's branch (`issue-3127/implementation-blueprint+experiment-trust+silent-failure-audit-9afe0675`), plus a branch-integration merge, plus tests for both changes.

**1. Timeout on every subprocess call (PR #3223 open finding 1).** derived: `grep -n "subprocess.run" scripts/issue-3127/verify_preregistration.py` on the pre-fix commit `421bfb7a` — result: two sites, `_run_git` (`:73-75`, calls `git`) and `_default_gh_runner` (`:78-79`, calls `gh`), neither setting `timeout=`. Both now do:
```python
GIT_TIMEOUT = 10   # local git reads (git log, merge-base) -- no network
GH_TIMEOUT = 30     # gh's GitHub API calls -- network-bound
```
and each wraps its `subprocess.run` in `try/except subprocess.TimeoutExpired`, converting the exception into a synthetic `CompletedProcess(returncode=124, stderr="timed out after Ns waiting for `<command>`")` rather than letting it propagate uncaught (round-3 verification's Attack 3 confirmed it previously did). `124` is the conventional `timeout`-command exit code, distinct from any real git/gh exit code, so a message reading "(exit 124)" is legible as a timeout, not confused with a real git/gh failure.

No call site's own `if r.returncode != 0` fail-closed logic changed -- a timeout now produces the same shape of failure every existing branch already handles closed (`GitCommandError` in `_first_commit_for_path`, the `merge-base --is-ancestor` else-branch in `verify()`, and the generic `return None` in `_repo_owner_repo`/`_pr_merge_commit`/`_pr_commit_order`/`_first_pr_commit_touching`, all of which round 3's own re-derived sweep already confirmed fail closed uniformly on any non-zero exit). This is the minimal fix: it closes the observable gap (a hang blocks forever) without touching the merge-commit bind, `--follow` removal, or the failure-vs-empty distinction, all of which round 3's verification (PR #3223) already graded Present and which the task instructed not to touch.

silent-failure-audit Step 1-3 applied to the two new `except subprocess.TimeoutExpired` blocks: classified Handled (H), not Silently Absorbed -- the caught exception is not swallowed, it is converted into an equally-actionable failure value (non-zero returncode + a stderr string naming the command and the timeout) that flows into the same fail-closed branches every other command failure already flows into. Forward-traced both: `_run_git` timeout on the `_first_commit_for_path` call path raises `GitCommandError`, caught by `verify()`'s `except` and reported as `ok=False`; `_run_git` timeout on the `merge-base --is-ancestor` call path falls into the pre-existing `else` branch ("errored, not a normal ancestry negative"), also `ok=False`; every `gh_runner` timeout site already returns `None` on any non-zero exit and every caller of each already fails closed on `None` (round 3's own re-derived sweep, unchanged by this fix).

**2. Git-log output-shape validation (PR #3223 open finding 2).** derived: `421bfb7a619a8eb70b74cd29d3768aa8c7649a51:scripts/issue-3127/verify_preregistration.py:108-114` (cited in PR #3223's record) accepted any non-blank line from `git log --format=%H` as a commit sha, with no shape check. `_first_commit_for_path` now validates the first line against `_COMMIT_SHA_RE = re.compile(r"[0-9a-f]{40}")` and raises the new `GitOutputError` (distinct from `GitCommandError`, which is reserved for a non-zero exit) when it doesn't match; `verify()`'s `except` clause now catches `(GitCommandError, GitOutputError)` together and reports the same fail-closed shape for both. PR #3223's own forward-trace found no exploitable false-pass from the pre-fix gap (the one branch that reads a garbage sha unconditionally, `results_commit is None`, is unaffected by sha validity; the two branches where a garbage sha would matter already fail on it via a real git/gh error) -- this fix is preventive tightening of the same defect shape the task named ("a check that cannot observe something ... waits" / accepts unverified input), not a correctness repair, since PR #3223 traced no live exploit.

**3. Branch integration.** derived: `git rev-list --left-right --count origin/main...origin/issue-3127/implementation-blueprint+experiment-trust+silent-failure-audit-9afe0675` before this round — result: `51	6` (51 commits behind, matching the task's "50 commits behind" plus one more landed in the interval). `git merge origin/main --no-edit` on PR #3169's branch produced merge commit `824bbf8fc57b96783c5e83ae818a87bff4325b1d` with zero conflicts (`git diff --name-only --diff-filter=U` empty). derived: `git log --oneline --all -- scripts/issue-3127/verify_preregistration.py` -- every commit touching this file traces back through this branch's own lineage (round 2, round 3, this round's fix); `git diff origin/main HEAD -- scripts/issue-3127/verify_preregistration.py` shows the full diff is this branch's own accumulated history being added on top of main's copy, confirming `origin/main` carries no commit of its own that touches this file -- the merge could not have altered `verify_preregistration.py`'s behavior.

Pushed directly to PR #3169's branch (not merged, no new PR opened for the code): `git push origin pr3169-work:issue-3127/implementation-blueprint+experiment-trust+silent-failure-audit-9afe0675` -- result: `421bfb7a..824bbf8f`. This record's own delivery follows round 3's established split (round-3 fix commit `421bfb7a` pushed directly to PR #3169's branch; round-3's own record landed to main separately via PR #3222/#3223): this record lands to main from this session's own branch, the code fix lives on PR #3169's branch.

## Why

The task named this as the same defect class round 3 just fixed, in its time dimension rather than its exit-status dimension: a check that cannot observe an outcome should say so, not wait forever. Converting `TimeoutExpired` into a synthetic non-zero `CompletedProcess` inside the two wrapper functions (`_run_git`, `_default_gh_runner`) closes the gap at its single narrowest point -- every one of the file's many call sites already has a `returncode != 0` fail-closed branch (confirmed unchanged by round 3's own re-derived 7-site sweep), so routing a timeout through that same signal reuses already-verified fail-closed logic instead of adding a new, unverified failure path per call site. A raw `sys.exit`-on-timeout pattern (used elsewhere in this repo, e.g. `plumbing.py`'s `_run_net`) was rejected for these two wrapper functions specifically because `verify()` is a testable function that returns `(ok, message)` tuples, not a process that exits directly -- `main()` is the only caller that exits, and it already does so based on `verify()`'s return value.

`GIT_TIMEOUT=10` / `GH_TIMEOUT=30`: git operations here (`log`, `merge-base --is-ancestor`) are local, read-only, and already-fetched -- 10s is generous headroom over a real run, not a tight margin, since a local git command that hasn't returned in 10s is stuck (lock contention, corrupt object), not still working. `gh` calls cross the network to the GitHub API; derived: `grep -rn "timeout=" --include=*.py .` found this repo's other single-API-read gh call sites (`gates/gh_budget.py:37`, `harness/driver.py:165`) use 10s and `gates/probe_cwd_shapes.py:66` uses 30s -- 30s matches the high end of that existing range so an ordinary slow-network moment isn't misread as "gh failed" and doesn't fail this check closed on a false alarm, while still bounding a genuine hang.

`GitOutputError` as a sibling of `GitCommandError`, not a reuse of it: `GitCommandError`'s own docstring scopes it to "exits non-zero" (round 3's own text, quoted in PR #3223's record) -- reusing it for an exit-0-but-malformed case would have made its `(exit {returncode})` message read "(exit 0)" for what is not, in the ordinary sense, a failed exit. A distinct exception with its own message, caught alongside `GitCommandError` in `verify()`'s existing `except` clause, keeps both exceptions' own docstrings accurate to what they each actually mean.

## What did not work

None.

## Upstream basis

`docs/issue-3127/reports/adversarial-review+silent-failure-audit+experiment-trust-97f69e0b.md` (frontmatter `upstream:`, commit `6d1a233b74f0f19cc7ef5b7fdb26e9c7cf6a3d2b`, landed via PR #3223) -- its "Open findings" 1 and 2 are this round's entire scope; its Attack 1-7 Present grades on the round-3 fix (git-command-failure/empty-result distinction, merge-commit bind, `--follow` removal) are read as already-verified and not re-derived or touched here, per the task's explicit constraint.

## Open findings

None from this round's own scope. PR #3223's third open finding (branch staleness) is resolved by this round's merge (see "What was done", item 3). derived: `python3 -m pytest tests/ -q` on PR #3169's branch post-merge (`824bbf8f`) — result: `535 passed, 2 warnings` (0 failures) — vs. round 3's own last-measured `370 passed, 1 failed` at `421bfb7a`, pre-merge (see "Acceptance checks and full test suite" below for the full run and the pre-existing-warning caveat).

## Next steps

None queued by this record. canonical: `gh pr view 3169 --json state -q .state` — result: `OPEN` (not merged, per the task's instruction). Whoever owns PR #3169 next decides whether to land it.

## Acceptance checks and full test suite

acceptance: `python3 scripts/issue-3127/run_consumer_pair.py --dry-run` — checked on PR #3169's branch post-merge (`824bbf8f`) — result: exit=0 (dry-run plan printed, nothing executed)
acceptance: `test -f docs/issue-3127/_assets/consumer-path-results.json` — result: exit=0
acceptance: `python3 scripts/issue-3127/verify_preregistration.py` — result:
```
OK: same-commit collapse resolved via PR #3131's own pre-squash commit history -- docs/issue-3127/decisions/pre-registration.md first appears at commit index 0 (84226988e930981b02d00abd30e22c83100e875f), docs/issue-3127/_assets/consumer-path-results.json at index 1 (9c9801cd470129580de54b78a32abc30875de90e), strictly earlier
```
exit=0

derived: `python3 -m pytest tests/test_issue_3127_verify_preregistration.py -q` — result: `23 passed` (round 3's 19, plus 4 new tests: a malformed-git-log-output case added to `FirstCommitForPathTest`, `SubprocessTimeoutTest`'s two unit tests on `_run_git`/`_default_gh_runner`, and a new end-to-end timeout case in `VerifyGitFailureTest`).

derived: `python3 -m pytest tests/ -q` on PR #3169's branch post-merge — result: `535 passed, 2 warnings` in 22.32s. The 2 warnings are a pre-existing, unrelated pinned-fixture-divergence notice in `tests/test_skill_candidates_floor.py` (`SkillCandidatesPinnedFixtureDivergenceTest`), not a failure. Round 3's single branch-staleness failure -- in the file `tests/test_spawn_gate_wiring.py`, class `HooksJsonWiringIsAdditive`, method `test_pre_existing_post_tool_use_commands_are_all_still_present` -- is gone post-merge: the merge brought in the two `PostToolUse` hooks that test expected and this branch was previously missing.

skill-verdict: implementation-blueprint — not-applicable: single-file fix to one existing module (`scripts/issue-3127/verify_preregistration.py`), no new module boundary or multi-file structure decision; the skill's own scope note excludes "a one-line fix" and small single-file changes.
skill-verdict: silent-failure-audit — applied: invoked; used Steps 1-3 to classify the two new `except subprocess.TimeoutExpired` blocks (`_run_git`, `_default_gh_runner`) as Handled, not Silently Absorbed, and forward-traced both to confirm the synthetic non-zero `CompletedProcess` they produce flows into the same already-verified `returncode != 0` fail-closed branches every other command failure in the file already uses -- see "What was done", item 1.
