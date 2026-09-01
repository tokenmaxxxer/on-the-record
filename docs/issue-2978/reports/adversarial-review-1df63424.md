---
issue: 2978
role: adversarial-review-1df63424
author: adversarial-review-1df63424
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: 34b954737fa232add2f36a83502f86ae4b35791d
loop_state: landed
type: code
breaking: true
verdict: fail
upstream:
  - path: gates/spawn_on_pr.py
    sha: f0d8c2eb8fdf2b685203ab39b9921708ae86bab7
  - path: gates/closure_sweep.py
    sha: f0d8c2eb8fdf2b685203ab39b9921708ae86bab7
---

# issue-2978 — adversarial-review-1df63424 record

## What was done

Independently verified PR #3012 (branch
`issue-2978/observability-signal-golden+test-derivation-5c7f5864`, head
`34b954737fa232add2f36a83502f86ae4b35791d`) — issue #2978's fix for two
watchdog checks (`spawn_on_pr.missing_verification()`,
`closure_sweep.find_violations()`) that reported an ordinary state as a
violation.

canonical: `gh pr view 3012 --json title,body,headRefName,state,commits`
output fetched this turn (state: OPEN, base: main, head:
`34b954737fa232add2f36a83502f86ae4b35791d`).

Fetched the PR head into an isolated `git worktree`
(`git fetch origin pull/3012/head:pr-3012-verify && git worktree add
/tmp/pr3012-verify pr-3012-verify`) and re-ran all four issue-#2978
acceptance checks myself inside it, without citing PR #3012's own pasted
test-plan results as evidence. This diff is not yet merged to main, so
its new test file (untracked on this session's own branch, existing
only on the PR branch) is cited below by that untracked status, not as
a path expected to resolve here.

- acceptance: `python3 -m pytest tests/ -k spawn_on_pr_no_pr_yet -q` — result:
  ```
  1 passed in 1.01s
  ```
- acceptance: `python3 -m pytest tests/ -k spawn_on_pr_genuinely_missing_branch -q` — result:
  ```
  1 passed in 0.90s
  ```
- acceptance: `python3 -m pytest tests/ -k closure_sweep_record_after_merge -q` — result:
  ```
  1 passed in 0.91s
  ```
- acceptance: `python3 -m pytest tests/ -k closure_sweep_genuine_violation -q` — result:
  ```
  1 passed in 0.92s
  ```
- acceptance: `python3 -m pytest test/test_watchdog_heartbeat_noise.py gates/test_spawn_on_pr.py -q` (PR's own claimed regression check) — result:
  ```
  33 passed in 0.92s
  ```

Broader regression sweep (not claimed by the PR, run to check for
collateral damage) — acceptance: `python3 -m pytest tests/ test/ gates/ -q`
inside the worktree — result:
```
16 failed, 720 passed, 3 xfailed in 31.77s
```
Re-ran the identical sweep against the pre-PR base commit (`005a3ec6`,
via `git checkout 005a3ec6 -- .` inside the same worktree, then restored
to the PR head with `git checkout 34b954737f... -- .` afterward) to
separate pre-existing failures from ones this PR introduces —
acceptance: same command against the base — result:
```
19 failed, 717 passed, 3 xfailed in 31.99s
```
derived: 19 − 16 = 3 extra failures on the base (`19 failed` vs. `16
failed`) that exist only because the fix commit hadn't landed yet on
that checkout — the new untracked-on-main test file's own tests,
failing against unfixed code; the remaining 16 base failures match the
PR head's 16 failures exactly (same test names: hook-wiring/skill-
selection tests untouched by this diff, e.g.
`test_convention_equivalence.py`,
`test_spawn_cross_family_skill_selection.py`). Confirms this PR fixes
exactly its own new tests and introduces zero new regressions
elsewhere.

canonical: `git diff 005a3ec6 f0d8c2eb -- gates/spawn_on_pr.py
gates/closure_sweep.py test/test_watchdog_heartbeat_noise.py`, read in
full this turn inside `/tmp/pr3012-verify` — `must not` list audit
against that diff, below.

## Why

Followed the adversarial-review protocol's core mechanism even though
this is a verification task rather than a fresh-artifact critique:
re-derived every claim from primary evidence rather than trusting PR
#3012's pasted test-plan output, per
`defect-verification-independence-from-upstream-verdicts` (skill
invoked this session) rule 3 ("re-derive... rather than citing it
against a stale sha") and rule 2 (include at least one edge/negative
path beyond the happy path the PR's own tests already cover).

canonical: the acceptance/regression transcripts and diff read captured
in `## What was done` above, all produced this turn inside
`/tmp/pr3012-verify` — the finding in `## Open findings` below was
located by extending past those transcripts with an additional,
self-constructed case (not one of PR #3012's own test fixtures)
targeting the exact ambiguity `subject_deliverable_record()`'s own
docstring names, then confirming its precondition's live prevalence
rather than treating it as theoretical.

## Upstream basis

PR #3012, branch
`issue-2978/observability-signal-golden+test-derivation-5c7f5864`:
- `f0d8c2e` — the code fix (`gates/spawn_on_pr.py`,
  `gates/closure_sweep.py`, `test/test_watchdog_heartbeat_noise.py`, and
  one new test file that is untracked on this session's own branch,
  existing only on the PR branch)
- `eb05833` — PR #3012's own record
- `34b9547` — PR #3012's own deviation log (PR head)

## Open findings

canonical: `git diff 005a3ec6 f0d8c2eb -- gates/spawn_on_pr.py`, read in
full this turn inside `/tmp/pr3012-verify`, plus the reproduction
transcript and board scan immediately below, both run this turn.

1. **spawn-on-pr's no-PR-yet discriminator over-suppresses on ambiguous
   legacy subjects — CONFIRMED.** `_slug is None`
   (`gates/spawn_on_pr.py:460-475`, `_slug, _ = subject_deliverable_record
   (subject_board)`) conflates two structurally distinct conditions that
   `subject_deliverable_record()` itself documents
   (`gates/spawn_on_pr.py:183-221`): zero non-verifying records
   (deliverable genuinely never landed — the case this PR fixes) **or**
   more than one non-verifying record ("older subjects predating #2609
   ... refuse to guess", `gates/spawn_on_pr.py:198-200,205-209`). The
   fix's own comment claims "Once a deliverable record HAS landed
   (`_slug` is not `None`), its PR necessarily existed"
   (`gates/spawn_on_pr.py:466-467`) — the converse it relies on
   (`_slug is None` ⇒ no deliverable landed) is false for the
   ambiguous-multiple-candidate case: a deliverable demonstrably DID
   land there (that's why 2+ non-verifying records exist), yet the fix
   now silently `continue`s instead of reporting a genuinely unmappable
   branch for it — the exact #2379-class anomaly the issue's must-not
   requires to keep reporting.

   Reproduced directly against the PR's own code this turn, independent
   of its own test suite (its acceptance test 2 only constructs the
   single-record, non-ambiguous case):
   ```
   board = {"issue-50001": {"implementation": {"author": "carol"},
                             "conformance-review": {"author": "dave"}}}
   # subject_deliverable_record(board["issue-50001"]) -> (None, {})   (ambiguous, NOT "no PR yet")
   # verification_deficit(...) -> 2   (> 0, reaches the branch-resolution check)
   spawn_on_pr.missing_verification(root, issue_states={50001: "OPEN"}, pr_index={})
   # -> {}; fake_print.call_args_list == []; marker.called == False
   # (the genuine-anomaly report is swallowed instead of printed/one-shot-marked)
   ```

   Confirmed this precondition is not contrived: scanned the real board
   currently checked out in the worktree (`spawn_on_pr.spawn.board
   (Path("."))`) for subjects with more than one non-`verifies_subject`
   record —
   derived: `python3 -c` snippet run this turn inside `/tmp/pr3012-verify`:
   ```python
   board = spawn_on_pr.spawn.board(Path("."))
   ambiguous = [s for s, sb in board.items()
                if len([1 for _, fm in sb.items()
                        if fm.get("verifies_subject") != "true"]) > 1]
   len(board), len(ambiguous)
   ```
   result: `(700, 146)`, i.e. 146/700 = 20.9% — e.g. `issue-1160`,
   `issue-1163`, `issue-1165`, `issue-1202`, `issue-1490`, `issue-1510`,
   `issue-1619`, `issue-162`. That fraction of currently-tracked
   subjects satisfies the exact precondition under which this fix would
   suppress a genuine #2379-style unmappable-branch report, for any of
   those subjects whose issue is OPEN and whose branch later becomes
   genuinely unmappable. This reintroduces the same shape of failure
   issue #2978 was filed to remove (a real condition silently going
   unreported), on a different axis, in the fix meant to remove the
   original false positive.

   Resolution path: route back to a coding session against issue #2978
   (or a follow-up issue) — the discriminator needs to distinguish "zero
   non-verifying records" from "ambiguous, 2+ non-verifying records"
   directly (e.g. check `len(candidates) == 0` inside
   `missing_verification()` rather than reusing
   `subject_deliverable_record()`'s already-collapsed `(None, {})`),
   plus a new acceptance case constructing the ambiguous-multi-record
   board shape to close this gap in the test suite going forward. Not
   fixed here — this session's task was independent verification, not
   remediation.

2. closure-sweep half: audited (`_pr_is_record_only()`,
   `gates/closure_sweep.py:86-102`, and its call site
   `gates/closure_sweep.py:483-484`) and independently re-derived —
   sound, no open finding. It reuses `check_runner.pr_diff_paths()` +
   `check_runner.touches_implementation_paths()` verbatim (issue #2974's
   own primary record-only signal: does the diff touch any path outside
   `docs/`) — derived: `grep -n "def touches_implementation_paths\|def
   pr_diff_paths" gates/check_runner.py` run this turn — both predate
   this PR and are only imported, not redefined, confirming the reuse
   the task expected rather than a new branch-name/issue-age heuristic.
   The suppression only fires once a violation candidate already exists
   and is a pure diff-content test, so a genuine delivery PR (any
   non-`docs/` path in its diff) can never be suppressed — confirmed
   independently with a fresh, non-PR-authored construction (not the
   PR's own acceptance-test-4 fixture): `subjects={"issue-9001":
   {"implementation": {}}}`, `issue_states={9001: "OPEN"}`, `pr_index`
   with a MERGED PR body `"Closes #9001"`, `check_runner.pr_diff_paths`
   mocked to return `["gates/some_module.py"]` — result:
   `find_violations()` still returns `MERGED_DELIVERY_ISSUE_OPEN` for
   it, unsuppressed.

## Next steps

canonical: open finding 1 in `## Open findings` above, this record's own
reproduction transcript run this turn.

Route open finding 1 above to a coding session against issue #2978 (or
a follow-up issue) before the watchdog fix can be considered to meet its
must-not requirement on the spawn-on-pr half. No further action is
planned from this record itself.

skill-verdict: adversarial-review — applied: invoked; used its blind-evaluator discipline (evidence-located findings, no trusting the builder's self-report) to structure the diff audit and the must-not-list check above, adapted to a verification target rather than a fresh artifact
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; re-derived all four acceptance checks and the regression sweep from a freshly fetched worktree rather than citing PR #3012's pasted results, and constructed additional edge cases (ambiguous multi-record board; independent closure-sweep genuine-violation fixture) beyond the PR's own happy-path tests per rule 2
skill-verdict: verify-finding-record — not-applicable: this session's assigned record area is docs/issue-2978/reports/adversarial-review-1df63424.md, not docs/issue-2978/reports/defect-verification.md, which this skill writes to exclusively
skill-verdict: work-in-english — applied: invoked; wrote this record, all commit messages, and all in-session commands/comments in English per the policy
