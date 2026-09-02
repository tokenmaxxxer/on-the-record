---
issue: 3127
role: silent-failure-audit+implementation-blueprint+experiment-trust-15d48cd6
author: silent-failure-audit+implementation-blueprint+experiment-trust-15d48cd6
skills: silent-failure-audit (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12)), experiment-trust (skill-repository(c05de12))
verifies_subject: true  # round-3 fix + residual-finding sweep on PR #3169's own deliverable, per PR #3219's round-2 finding
code_under_review: 421bfb7a619a8eb70b74cd29d3768aa8c7649a51
loop_state: landed
type: fix
breaking: false
verdict: fixed
upstream:
  - path: docs/issue-3127/reports/adversarial-review+experiment-trust+silent-failure-audit-6095e2ff.md
    sha: fb5bdd13fd5695e598736ec251374f2e1e756323
---

# issue-3127 — silent-failure-audit+implementation-blueprint+experiment-trust-15d48cd6 record

## What was done

Round 3 on PR #3169's own branch (`issue-3127/implementation-blueprint+experiment-trust+silent-failure-audit-9afe0675`, not this record's branch), fixing the one residual finding left open by the upstream verification record above: the merge-commit bind and the `--follow` rename fix were graded Present there and were not touched this round.

canonical: `docs/issue-3127/reports/adversarial-review+experiment-trust+silent-failure-audit-6095e2ff.md` (round-2 verification record, commit `fb5bdd13fd5695e598736ec251374f2e1e756323`) — names the residual finding this round fixes: `_first_commit_for_path` conflates a real git-command failure with "the path has no commits yet".

1. Fixed the residual finding. Before this round, `421bfb7a619a8eb70b74cd29d3768aa8c7649a51^:scripts/issue-3127/verify_preregistration.py` (the pre-fix version) had `_first_commit_for_path` return `None` on `git log` non-zero exit — the same `None` a genuinely-empty (but successful) `git log` also returns. `verify()`'s `results_commit is None` branch returns `ok=True` unconditionally, so a git failure on that specific query could read as a pass. Fixed at `421bfb7a619a8eb70b74cd29d3768aa8c7649a51:scripts/issue-3127/verify_preregistration.py:44-51` (new `GitCommandError` class) and `:68-77` (`_first_commit_for_path` now raises instead of returning `None` on non-zero exit); `verify()` wraps both calls in `try/except GitCommandError` at `421bfb7a619a8eb70b74cd29d3768aa8c7649a51:scripts/issue-3127/verify_preregistration.py:280-286`, failing closed with a message naming the git command and its exit status.
2. Swept every other subprocess call and every emptiness-carries-meaning return value in the same file against the same axis — see Open findings for the full site list and per-site verdict.
3. Stated the rule once, in `GitCommandError`'s docstring (`421bfb7a619a8eb70b74cd29d3768aa8c7649a51:scripts/issue-3127/verify_preregistration.py:44-51`): an empty result and a failed observation are different, and only the empty result is evidence the check may reason about.
4. Recorded, without acting on it, the construction-order-vs-decision-order limitation the upstream record named: added a `## Limitation of the mechanical ordering check` section to `421bfb7a619a8eb70b74cd29d3768aa8c7649a51:docs/issue-3127/decisions/pre-registration.md` (a file that also exists, with different content, on this record's own branch at `docs/issue-3127/decisions/pre-registration.md` — the section added there is untracked here).
5. Did not touch the merge-commit binding (`_resolve_via_pr_history`'s bind logic) or the `--follow` removal — both graded Present in the upstream record and out of scope for this round.

## Why

The upstream verification record (`docs/issue-3127/reports/adversarial-review+experiment-trust+silent-failure-audit-6095e2ff.md`) identified the residual finding as the same defect shape its own round removed one instance of elsewhere in the file (the `--follow` empty-read masking a real rename): a check that could not observe something reports the answer it would have given had it observed nothing. The fix follows the same principle — raise on command failure instead of returning a value indistinguishable from a legitimate empty result, and fail the check closed with a message naming what failed. The rest of the file's subprocess calls were swept on the same axis rather than assumed fine from inspecting only the fixed site, since this pattern has now recurred across sites in this file across rounds.

The construction-vs-decision-order limitation was recorded rather than acted on because there is no mechanical fix for it: git ancestry is the only automatable evidence for commit order, and no code change closes the gap between "committed in the right order" and "decided in the right order." Stating it in the decision record bounds what a future reader is entitled to conclude from a passing check.

## What did not work

None.

## Upstream basis

- `docs/issue-3127/reports/adversarial-review+experiment-trust+silent-failure-audit-6095e2ff.md` (commit `fb5bdd13fd5695e598736ec251374f2e1e756323`): round-2 verification record naming the residual finding this round fixes.
- The fix and its tests are committed as `421bfb7a619a8eb70b74cd29d3768aa8c7649a51` on PR #3169's branch (`issue-3127/implementation-blueprint+experiment-trust+silent-failure-audit-9afe0675`) and pushed there — not merged, not present on this record's own branch.

Acceptance checks (issue #3127), run against PR #3169's branch after the fix (all three from the issue text):
```
$ python3 scripts/issue-3127/run_consumer_pair.py --dry-run
exit=0 (dry-run plan printed, nothing executed)
$ test -f docs/issue-3127/_assets/consumer-path-results.json
exit=0
$ python3 scripts/issue-3127/verify_preregistration.py
OK: same-commit collapse resolved via PR #3131's own pre-squash commit history -- docs/issue-3127/decisions/pre-registration.md first appears at commit index 0 (84226988e930981b02d00abd30e22c83100e875f), docs/issue-3127/_assets/consumer-path-results.json at index 1 (9c9801cd470129580de54b78a32abc30875de90e), strictly earlier
exit=0
```
acceptance: all three of issue #3127's acceptance checks — result: exit 0 (see fences above).

Full test suite on PR #3169's branch after the fix:
```
$ python3 -m pytest tests/ -q
...
FAILED tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present
1 failed, 370 passed in 10.44s
```
derived: `python3 -m pytest tests/ -q` on PR #3169's branch — result: 1 failed (pre-existing, see below), 370 passed.

Branch staleness (the one failure above, unrelated to this round's fix):
```
$ git log --oneline HEAD..origin/main | wc -l
48
$ git diff HEAD origin/main -- on-the-record/hooks/hooks.json
... two PostToolUse hook commands added on main after this branch was cut:
+ ${CLAUDE_PLUGIN_ROOT}/hooks/fail-open-wrapper.sh ${CLAUDE_PLUGIN_ROOT}/hooks/amends-landing-apply.sh
+ ${CLAUDE_PLUGIN_ROOT}/hooks/fail-open-wrapper.sh ${CLAUDE_PLUGIN_ROOT}/hooks/amendment-channel.sh
```
derived: `git log --oneline HEAD..origin/main | wc -l` on PR #3169's branch — result: 48 commits behind `origin/main`. The failing test (class `HooksJsonWiringIsAdditive`, test `test_pre_existing_post_tool_use_commands_are_all_still_present` in `tests/test_spawn_gate_wiring.py`) diffs this branch's `hooks.json` against `origin/main` and correctly reports the two hooks above as "removed" relative to main — a staleness artifact of the branch being 48 commits behind, not a regression this round introduced. Matches PR #3219's own note of "one unrelated failure from branch staleness".

Added tests, committed in `421bfb7a619a8eb70b74cd29d3768aa8c7649a51:tests/test_issue_3127_verify_preregistration.py` (this file is untracked on this record's own branch; it was introduced by PR #3169 and lives only on its branch):
```
tests/test_issue_3127_verify_preregistration.py::FirstCommitForPathTest::test_returns_none_when_command_succeeds_with_no_matching_commit PASSED
tests/test_issue_3127_verify_preregistration.py::FirstCommitForPathTest::test_raises_git_command_error_when_git_itself_fails PASSED
tests/test_issue_3127_verify_preregistration.py::VerifyGitFailureTest::test_git_failure_on_results_path_fails_closed_not_read_as_pass PASSED
```
derived: `python3 -m pytest tests/test_issue_3127_verify_preregistration.py -q` on PR #3169's branch — result: 19 passed (16 pre-existing + 3 new).

## Open findings

Silent-failure-audit sweep of `421bfb7a619a8eb70b74cd29d3768aa8c7649a51:scripts/issue-3127/verify_preregistration.py` (every subprocess call, every place a return value's emptiness carries meaning), per-site verdict:

1. `_first_commit_for_path` (`421bfb7a619a8eb70b74cd29d3768aa8c7649a51:scripts/issue-3127/verify_preregistration.py:68-77`) — fixed this round. Was Silently Absorbed: git-command-failure and legitimate-empty both returned `None`, and `verify()`'s `results_commit is None` branch read that as an unconditional pass. Now Handled: raises `GitCommandError` on non-zero exit; `verify()` catches it and fails closed by name and status.
2. `_read_frontmatter` (`421bfb7a619a8eb70b74cd29d3768aa8c7649a51:scripts/issue-3127/verify_preregistration.py:99-112`) — inspected, no code change. `yaml.YAMLError` is caught and `{}` returned. Every caller already treats a missing/empty dict as failure (`_resolve_via_pr_history` fails closed on a non-int `verification_pr:` field), so a YAML parse error and a genuinely-absent field collapse to the same fail-closed outcome — no branch where this reads as a pass. Left as-is: the only cost is diagnostic precision (parse error reported with the same message as "field absent"), which is outside the empty-as-pass axis this round targets.
3. `_repo_owner_repo` (`421bfb7a619a8eb70b74cd29d3768aa8c7649a51:scripts/issue-3127/verify_preregistration.py:115-121`) — inspected, no code change. `gh` failure and an empty `nameWithOwner` string both return `None`; the caller fails closed uniformly on `None` ("could not resolve the GitHub owner/repo"). No incorrect-pass path.
4. `_pr_merge_commit` (`421bfb7a619a8eb70b74cd29d3768aa8c7649a51:scripts/issue-3127/verify_preregistration.py:124-141`) — inspected, no code change. `gh` failure, JSON-decode failure, and a genuinely-absent merge commit all collapse to `None`; the caller fails closed uniformly on `None` ("no recorded merge commit"). No incorrect-pass path.
5. `_pr_commit_order` (`421bfb7a619a8eb70b74cd29d3768aa8c7649a51:scripts/issue-3127/verify_preregistration.py:144-163`) — inspected, no code change. Same shape as (4); caller fails closed on `None` ("`gh pr view` failed or returned no commits").
6. `_first_pr_commit_touching` (`421bfb7a619a8eb70b74cd29d3768aa8c7649a51:scripts/issue-3127/verify_preregistration.py:166-180`) — inspected, no code change. A `gh api` failure on any commit returns `None` immediately; a clean loop that finds no match also returns `None` — the two causes are conflated at the source, but the caller fails closed on `None` either way and its own message hedges for both causes ("has no commit touching ... (or the lookup failed)"). Intentionally fail-closed regardless of cause; no incorrect-pass path.
7. `merge-base --is-ancestor` call in `verify()` (`421bfb7a619a8eb70b74cd29d3768aa8c7649a51:scripts/issue-3127/verify_preregistration.py:312-328`) — inspected, no code change, already correct before this round. Branches on exit `0`/`1`/`>1` explicitly, treating a real git error (`>1`) as distinct from "not an ancestor" (`1`).

Sites 2-7 route every failure mode to the same fail-closed outcome as their legitimate-empty case, so no code change was needed there. Site 1 was the only site where a specific `None` branch fed a `return True`; that is fixed.

skill-verdict: silent-failure-audit — applied: invoked; used its Step 1-3 procedure (enumerate subprocess/error-handling sites, classify Handled/Silently-Absorbed/Unreachable, trace each Silently-Absorbed site forward to its downstream consequence) to produce the site-by-site sweep above and confirm sites 2-7 are Handled via their callers' uniform fail-closed treatment of `None`, not Silently Absorbed.
skill-verdict: implementation-blueprint — not-applicable: single-function fix inside one existing file, no new module or architecture decision.
skill-verdict: experiment-trust — not-applicable: no experiment result was interpreted or acted on this round; `run_consumer_pair.py` was not invoked in an executing mode.

## Next steps

- PR #3169's branch needs an integration pass with `origin/main` before it can land: `derived: git log --oneline HEAD..origin/main | wc -l` on PR #3169's branch — result: 48 (see Upstream basis fence). The one pytest failure noted there is a staleness artifact of that gap, not caused by this round's fix.
- PR #3169 itself remains unmerged; this round's commit `421bfb7a619a8eb70b74cd29d3768aa8c7649a51` is pushed to its branch only, not to `main`.
