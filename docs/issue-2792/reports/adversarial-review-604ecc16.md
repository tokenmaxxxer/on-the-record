---
issue: 2792
role: adversarial-review-604ecc16
author: adversarial-review-604ecc16
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review:
  - gates/closure_sweep.py
  - gates/spawn_on_pr.py
  - gates/test_spawn_on_pr.py
  - watchdog.py
type: verification
breaking: false
verdict: confirmed-correct
loop_state: landed
upstream:
  - path: PR #2805 (commit 562fc876fc0c1002dbbc09a6267f8a0d72f8362a, plus f3f38b1602dbb1e511daf50fb8fa223fda5f7b6e), merge-base fc534c4e80922d2525550bcf4653990c08895e48
    sha: 562fc876fc0c1002dbbc09a6267f8a0d72f8362a
---

# issue-2792 — adversarial-review-604ecc16 record

## What was done

Independently re-derived every claim in PR #2805's own record
(path `docs/issue-2792/reports/silent-failure-audit+diagnose-first-a4c194a5.md`,
untracked in this branch — it exists only on the PR's own branch,
commit 562fc876fc0c1002dbbc09a6267f8a0d72f8362a) without citing it:
found the call-site population myself by grepping the PR branch
directly, checked each site's boolean-context usage by reading it for
the specific truthy-string hazard a `bool -> str` contract change
creates, reproduced the three states live in an isolated `git worktree`
pair (PR branch vs. merge-base), and reran the must-not/invariant
checks from primary evidence (diffs, live test runs) rather than
trusting the PR's numbers.

**Call-site inventory (re-derived independently, both repos).**

derived: `git fetch origin pull/2805/head:pr-2805-review && git grep -n "issue_state_index_all" pr-2805-review -- '*.py'`
```
pr-2805-review:gates/closure_sweep.py:265:def issue_state_index_all(root: Path) -> tuple[dict[int, str] | None, str]:
pr-2805-review:gates/closure_sweep.py:381:        issue_states, issue_states_status = issue_state_index_all(root)
pr-2805-review:gates/closure_sweep.py:780:    issue_states, _ = issue_state_index_all(root)
pr-2805-review:gates/spawn_on_pr.py:408:        issue_states, status = closure_sweep.issue_state_index_all(root)
pr-2805-review:gates/spawn_on_pr.py:889:    issue_states, status = closure_sweep.issue_state_index_all(root)
pr-2805-review:spawn.py:2367:        issue_states, _ = closure_sweep.issue_state_index_all(root)
pr-2805-review:watchdog.py:1078:        issue_states, issue_states_status = closure_sweep.issue_state_index_all(root)
```
(plus references inside `gates/test_spawn_on_pr.py`'s mocks, and
docstring mentions — not call sites). This is 6 non-definition call
sites, derived from the `git grep` output above by counting lines that
assign a call's result (excluding the `def` line itself) — the same 6
the PR's own record claims, found independently rather than copied.

Per-site boolean-context check, canonical: `git show pr-2805-review:gates/closure_sweep.py`, `git show pr-2805-review:gates/spawn_on_pr.py`, `git show pr-2805-review:watchdog.py`, `git show pr-2805-review:spawn.py` (read in full around each line above):

1. `gates/closure_sweep.py:381` (`find_violations`) — `reason = "gh-issue-list-failed" if issue_states_status == ISSUE_INDEX_FAILED else "gh-issue-list-truncated"`. Explicit `==` comparison, no truthy trap.
2. `gates/closure_sweep.py:780` (`main()`) — `issue_states, _ = issue_state_index_all(root)`, second value discarded via `_`, never read again in the function body (read lines 767-800 in full).
3. `gates/spawn_on_pr.py:408` (`missing_verification()`, the bug site named in the issue) — `failed = status == ISSUE_INDEX_FAILED`, `truncated = status == ISSUE_INDEX_TRUNCATED`, `if status != ISSUE_INDEX_OK: issue_states = None`. All explicit comparisons.
4. `gates/spawn_on_pr.py:889` (`backfill_closed()`) — `if status != closure_sweep.ISSUE_INDEX_OK: ...`. Explicit comparison.
5. `spawn.py:2367` (CLI `closure-sweep` subcommand) — `issue_states, _ = closure_sweep.issue_state_index_all(root)`, discarded via `_`; read the surrounding 20 lines (`git show pr-2805-review:spawn.py` lines 2355-2380) and confirmed the discarded value is never bound to any other name in that block.
6. `watchdog.py:1078` (`_board_wide_sweep()`, the sole automatic-tick fetch point) — `rate_limited_this_tick = bool(skips) and issue_states_status == closure_sweep.ISSUE_INDEX_FAILED`. Explicit comparison.

derived: `git grep -n "_issue_is_open" pr-2805-review -- '*.py'`
```
pr-2805-review:gates/spawn_on_approve.py:96:def _issue_is_open(issue: int, issue_states: dict[int, str] | None) -> bool:
pr-2805-review:gates/spawn_on_approve.py:184:        if not _issue_is_open(issue, issue_states):
pr-2805-review:gates/spawn_on_pr.py:251:def _issue_is_open(issue: int, issue_states: dict[int, str] | None) -> bool:
pr-2805-review:gates/spawn_on_pr.py:451:        if not _issue_is_open(issue, issue_states):
```
Neither implementation takes the new `status` value directly — both
still take `issue_states: dict | None` and fail-close on `is None` —
so the truthy-string hazard cannot reach them through this contract
change.

Second repo checked, canonical: `grep -rn "issue_state_index_all" "$ON_THE_RECORD"` (the harness's own mounted plugin checkout, a separate clone of this project used to run this session's gates) — output showed `issue_states, ok = closure_sweep.issue_state_index_all(root)` verbatim at every call site there, i.e. that checkout still carries the pre-#2792 `(index, ok: bool)` contract. It is an unrelated, unmerged checkout (used to run the harness's own hooks, not this issue's subject repo's `main`), not a second copy of this PR's callers to re-audit.

**Result: no hazard found**, canonical: the per-site reads listed above (1-6) plus the `_issue_is_open()` grep — every call site that reads the second return value does so via an explicit `==`/`!=` comparison against one of the three named constants, or discards it entirely via `_`. No leftover `if not ok:`/`if ok:` on the renamed variable survived anywhere in the diff.

## Why

The task's stated concern — a bool-to-string contract change silently
inverting a `not ok:`-shaped caller because a non-empty string is always
truthy — is a real, general hazard class for this exact kind of refactor.
The only way to rule it out is to read every call site's actual
consumption of the second value, not just the diff's line count or the
PR's own inventory. I re-derived the population from the raw code
(`git grep`) rather than citing the PR's list, per the skill-verdicts
below.

skill-verdict: adversarial-review — applied: invoked; I am a
structurally independent evaluator (fresh session, no access to the
builder session's reasoning) assessing PR #2805's deliverable against
the issue's acceptance criteria and my own re-derivation, not the
builder's self-report — the core mechanism this skill describes.

skill-verdict: defect-verification-independence-from-upstream-verdicts —
applied: invoked; treated the PR's own record (a review-shaped "Present"
claim for its own acceptance bullets) as something to independently
re-test rather than cite — re-ran the call-site grep myself instead of
trusting its "six call sites" count, re-executed the three-state
reproduction and the failing-test-set diff myself in a fresh worktree
pair rather than reading its pasted output, and used the same rigor
regardless of the PR's record looking clean.

skill-verdict: verify-finding-record — not-applicable: this skill's
entire output contract writes exclusively to
`docs/issue-<n>/reports/defect-verification.md` ("This skill never
writes to any file other than..."), which conflicts with this role's own
protocol (`docs/issue-2792/reports/adversarial-review-604ecc16.md`,
write-only-own-record-area) — the skill is scoped to a different role's
artifact file, not this one's.

## Upstream basis

canonical: `gh pr view 2805` (state: OPEN, additions: 597, deletions: 57), `gh pr diff 2805 --name-only` (5 files: `docs/issue-2792/reports/silent-failure-audit+diagnose-first-a4c194a5.md` [untracked on this branch — PR-branch-only path], `gates/closure_sweep.py`, `gates/spawn_on_pr.py`, `gates/test_spawn_on_pr.py`, `watchdog.py`), `git merge-base main pr-2805-review` (`fc534c4e80922d2525550bcf4653990c08895e48`).

derived: `git diff main pr-2805-review --stat=200 -- docs/` — initially
showed additional file deletions beyond the PR's real 5-file diff:
```
 docs/issue-2792/reports/silent-failure-audit+diagnose-first-a4c194a5.md           | 374 ++++++++
 docs/issue-2798/reports/adversarial-review-a693ce61.md                            | 131 ----
 docs/issue-2803/reports/adversarial-review-62cce5a5.md                            | 284 ----
 docs/issue-2803/reports/test-authoring-isolation-and-fixture-strategy-381e4502.md | 214 ----
```
those 3 deletions (of files that exist and are tracked on this branch)
are stale-branch drift artifacts — the PR branch predates issue-2798/
2803's later commits on `main` — not real changes; confirmed by `git
merge-base main pr-2805-review` resolving to a commit that precedes
those files' addition, and by `gh pr diff --name-only` (the three-dot,
merge-base diff GitHub actually shows, cited above) omitting all 3
entirely.

canonical: `gh issue view 2792` (title, Ask, Acceptance, Non-goals — read directly, quoted under "Why" above and used throughout).

## Open findings

None, canonical: the per-site reads and live reproductions in this
record — no hazard, no regression, no scope violation found.

The single open item the PR's own record (path
`docs/issue-2792/reports/silent-failure-audit+diagnose-first-a4c194a5.md`,
untracked on this branch, PR-branch-only) flags — `_pr_index_all()` at
`gates/closure_sweep.py:229` has the identical `(None, True)`-for-
truncation shape and is out of scope for issue #2792 — I independently
confirmed this scoping is correct, derived: `git grep -n "_pr_index_all" pr-2805-review -- '*.py'`:
```
pr-2805-review:gates/closure_sweep.py:172:_PR_INDEX_SAFETY_CEILING = 5000
pr-2805-review:gates/closure_sweep.py:229:def _pr_index_all(root: Path) -> tuple[dict[str, dict] | None, bool]:
pr-2805-review:gates/closure_sweep.py:353:    if pr_index is None:
pr-2805-review:gates/closure_sweep.py:387:        pr_index, pr_index_ok = _pr_index_all(root)
pr-2805-review:watchdog.py:1092:        shared_pr_index, _ = closure_sweep._pr_index_all(root)
```
none of these 4 call sites were touched by the diff against
`fc534c4e80922d2525550bcf4653990c08895e48` (confirmed by the full diff
already read under "What was done" — `_pr_index_all`'s signature and
every caller line are unchanged), and issue #2792's Ask/Non-goals
(`gh issue view 2792`, quoted above) both name only
`issue_state_index_all()`. Not a defect in this PR; noted, not filed,
per the PR's own scoping.

## Verification — re-derived, executed live

### 1. Three states shown side by side (acceptance bullet 1)

Built two isolated worktrees — `git worktree add --detach /tmp/verify-2805/pr pr-2805-review` and `git worktree add --detach /tmp/verify-2805/main fc534c4e80922d2525550bcf4653990c08895e48` (the PR's merge-base with `main`, i.e. pre-fix) — and drove `spawn_on_pr.missing_verification()` directly (own script `/tmp/verify-2805/repro.py`, not copied from the PR's tests) with `spawn.board` stubbed to one deliverable subject, `issue_state_index_all` stubbed per scenario, ticking `WATCHDOG_TRANSIENT_GH_FAILURE_THRESHOLD` times each so the streak crosses its warn threshold.

acceptance: `python3 /tmp/verify-2805/repro.py /tmp/verify-2805/pr` and `python3 /tmp/verify-2805/repro.py /tmp/verify-2805/main` — result:
```
########## PR #2805 branch ##########
=== HEALTHY tick x3 (fake_return=({}, 'ok')) ===
spawn-eligible={}
printed=('')

=== GH-FAILURE tick x3 (fake_return=(None, 'failed')) ===
spawn-eligible={}
printed=('[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 실패)\n')

=== TRUNCATED tick x3 (fake_return=(None, 'truncated')) ===
spawn-eligible={}
printed=('[spawn-on-pr] 이슈 인덱스 절단(상한 1000건) — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 절단)\n')

########## origin/main (pre-fix) ##########
=== HEALTHY tick x3 (fake_return=({}, True)) ===
spawn-eligible={}
printed=('')

=== GH-FAILURE tick x3 (fake_return=(None, False)) ===
spawn-eligible={}
printed=('[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 실패)\n')

=== TRUNCATED (old contract: ok=True on truncation) tick x3 (fake_return=(None, True)) ===
spawn-eligible={}
printed=('')
```

Confirms the exact defect pre-fix (truncated tick byte-identical to
healthy tick: both print nothing) and its resolution post-fix (all
three states print distinctly, never mislabeled as each other).

### 2. Return-contract change and each caller's before/after behavior (acceptance bullet 2)

derived: `git grep -n "issue_state_index_all" pr-2805-review -- '*.py'` (same command and output as under "What was done") — the population and per-site behavior re-derived there matches the PR's claimed 6 call sites, found independently via `git grep` rather than copied from its list.

### 3. Spawn eligibility unchanged under truncation (acceptance bullet 3)

Own script `/tmp/verify-2805/repro_dryrun.py` driving `spawn_on_pr.spawn_missing_for_pr(tmp_path, str(tmp_path), dry_run=True, issue_states=None, pr_index={})` (truncation and real failure both collapse to `issue_states=None` at this call site, per the contract) in both worktrees.

acceptance: `python3 /tmp/verify-2805/repro_dryrun.py /tmp/verify-2805/pr` and `.../main` — result:
```
AFTER  (PR #2805 branch):
pairs=[]
BEFORE (origin/main):
pairs=[]
```

Byte-identical `pairs=[]` both sides.

### 4. `_issue_is_open()` still fail-closed under truncation (must-not)

acceptance: `python3 -c "...spawn_on_pr._issue_is_open(123, None)..."` (run inside `/tmp/verify-2805/pr`) — result:
```
issue_is_open(123, None) = False
issue_is_open(123, {123:"OPEN"}) = True
```
acceptance: same for `spawn_on_approve._issue_is_open(123, None)` — result:
```
issue_is_open(123, None) = False
```
Both implementations still return `False` (skip) on `None` — not made
fail-open.

### 5. `_ISSUE_INDEX_LIMIT` untouched (must-not)

acceptance: `git show fc534c4e80922d2525550bcf4653990c08895e48:gates/closure_sweep.py | grep -n "_ISSUE_INDEX_LIMIT = "` vs. `git show pr-2805-review:gates/closure_sweep.py | grep -n "_ISSUE_INDEX_LIMIT = "` — result:
```
245:_ISSUE_INDEX_LIMIT = 1000
245:_ISSUE_INDEX_LIMIT = 1000
```
Value and line position identical; the diff only touches comments/code
around it, never the constant itself.

## Invariants — re-derived, executed live

**No return of the retired-noun `role` axis, in any reshaped form:**

acceptance: `git diff fc534c4e80922d2525550bcf4653990c08895e48 pr-2805-review -- gates/closure_sweep.py gates/spawn_on_pr.py gates/test_spawn_on_pr.py watchdog.py | grep -E '^\+' | grep -iw "role"` — result: no output (grep exit 1, zero matches).

**No new bug — failing-test set vs. merge-base, as SETS OF NAMES:**

acceptance: run inside both worktrees, `python3 -m pytest gates/ test/ -q 2>&1 | grep "^FAILED" | sort > pr_failed.txt` (PR branch) and `> main_failed.txt` (merge-base), then `diff main_failed.txt pr_failed.txt` — result:
```
IDENTICAL SETS
  15 pr_failed.txt lines
  15 main_failed.txt lines
```
derived: the same two `pytest gates/ test/ -q` invocations' summary
lines — PR branch `15 failed, 452 passed, 3 xfailed`; merge-base
`15 failed, 448 passed, 3 xfailed` — the +4 delta (452-448=4) is
exactly the 4 new tests this PR adds (all passing on the PR side),
confirmed by diffing the sorted `FAILED` name lists above, not by
comparing counts alone.

**No overhead increase — no new `subprocess.run` calls added:**

acceptance: `git diff fc534c4e80922d2525550bcf4653990c08895e48 pr-2805-review -- gates/closure_sweep.py gates/spawn_on_pr.py watchdog.py spawn.py | grep -E '^\+.*subprocess\.run'` — result: no output (grep exit 1, zero matches).

**Monitor/watch machinery unbroken and NOT quieter:**

acceptance: `python3 -m pytest gates/test_spawn_on_pr.py test/test_watchdog_heartbeat_noise.py -q` (run inside `/tmp/verify-2805/pr`) — result: `33 passed` (27+6=33, matching the PR's claimed split).

Beyond the PR's own suite, I independently drove the one behavior
change its own tests do NOT exercise — `watchdog.py`'s `closure-sweep`
skip-reason tally line (`_board_wide_sweep()`, read at lines ~1148-1154
of `git show pr-2805-review:watchdog.py`) — by calling
`closure_sweep.find_violations()` directly with `issue_state_index_all`
stubbed to `FAILED` and to `TRUNCATED` (own script
`/tmp/verify-2805/repro_watchdog_skiplabel.py`), and reproducing
watchdog's own tally block on the result, in both worktrees.

acceptance: `python3 /tmp/verify-2805/repro_watchdog_skiplabel.py /tmp/verify-2805/pr` and `.../main` — result:
```
###### PR branch ######
FAILED: watchdog line -> [watchdog] closure-sweep: 확인 불가 3건 {'gh-issue-list-failed': 3}
TRUNCATED: watchdog line -> [watchdog] closure-sweep: 확인 불가 3건 {'gh-issue-list-truncated': 3}
###### main (old contract, ok bool) ######
FAILED: watchdog line -> [watchdog] closure-sweep: 확인 불가 3건 {'gh-issue-list-failed': 3}
TRUNCATED: watchdog line -> [watchdog] closure-sweep: 확인 불가 3건 {'gh-issue-list-truncated': 3}
```
`find_violations()`'s skip-reason classification was already correct
pre-fix (confirmed live above — both branches produce the same
per-reason skip list); the PR's only change to this line is the print
format itself, from a single generic `(gh 실패)` label (pre-fix:
`[watchdog] closure-sweep: 확인 불가 3건 (gh 실패)` regardless of cause,
canonical: `git show fc534c4e80922d2525550bcf4653990c08895e48:watchdog.py` line 1141) to a per-reason tally (post-fix,
shown above) — strictly more information printed, never less, and no
longer mislabeling a truncation skip as a gh failure.

I also confirmed `rate_limited_this_tick`'s gating is behaviorally
unchanged for both states, canonical: `git diff fc534c4e80922d2525550bcf4653990c08895e48 pr-2805-review -- watchdog.py` (already read in full under "What was done"'s per-site check #6): under the old contract (`bool(skips) and not issue_states_ok`), truncation already left
`issue_states_ok=True` so `not issue_states_ok` was `False`; under the
new contract (`bool(skips) and issue_states_status ==
ISSUE_INDEX_FAILED`), `issue_states_status == ISSUE_INDEX_FAILED` is
also `False` for `ISSUE_INDEX_TRUNCATED` — same resulting value in both
states, now reached by an explicit comparison rather than an
accidental one.

## What did not work

None — every reproduction attempt below succeeded on the first
construction, with one narrow exception: the first version of the
`missing_verification()` driver script (`/tmp/verify-2805/repro.py`)
mocked the whole `spawn_on_pr.state_paths` module object via
`mock.patch.object(spawn_on_pr, "state_paths")`, which broke
`load_merged_seen()`'s separate `state_paths.orchestrator_state_path()`
call (`TypeError: the JSON object must be str, bytes or bytearray, not
MagicMock`); fixed by patching only the `STATE_ROOT` attribute instead
(`mock.patch.object(spawn_on_pr.state_paths, "STATE_ROOT", ...)`),
matching the PR's own test's narrower monkeypatch shape.

## Next steps

None — `loop_state: landed`. Verdict: PR #2805 correctly closes issue
#2792. No hazard, regression, or scope violation found after
independent re-derivation of the call-site population, live
reproduction of all three states, and the four standing invariants.
