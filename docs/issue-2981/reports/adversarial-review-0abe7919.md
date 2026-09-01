---
issue: 2981
role: adversarial-review-0abe7919
author: adversarial-review-0abe7919
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: 1205bdab3c7cfe41c40b269cdc98d5dcea7d67f7
loop_state: landed
type: review
breaking: false
verdict: verified -- the fix round at 702b4562 correctly replaces the name-regex record-only exclusion with issue #2974's diff-content standard, and both classification directions hold on real, live PR data (an actual adversarial-review-* record PR, an actual implementation PR). The must-not list holds. One known gap remains open but is not new here and was already adjudicated as a non-blocker for this issue's literal scope -- `_self_trigger_respawn()` still reaches `_respawn_or_cap()` with no deliverable check.
upstream:
  - path: gates/spawn_on_pr.py, gates/test_spawn_on_pr.py, tests/test_respawn_deliverable_gate.py -- untracked on this branch (PR #3002's own branch, not merged to main; fetched live into an isolated worktree for this review, not present in this checkout)
    sha: 702b4562bd5cef101e347fe20d8a5541da654777
---

# issue-2981 — adversarial-review-0abe7919 record

## What was done

Independently re-verified PR #3002 (issue #2981's deliverable) after its
fix round at commit 702b4562, which itself was written in response to a
prior independent-verification PR's live-reproduced finding that the
still-open-PR record-only exclusion in `gates/spawn_on_pr.py` matched only
the literal `independent-verification-<N>` branch slug — silently
misresolving this repo's other real record-only convention
(`adversarial-review-*`) as a genuine deliverable, inverting the
respawn-suppression gate for most of this repo's actual verification
traffic. All paths under `gates/` and `tests/` named below are untracked
on this review's own branch (PR #3002 has not merged to main) and were
read live from an isolated worktree fetched for this review, removed
after use.

derived: `git fetch origin pull/3002/head:pr-3002-verify && git worktree add <isolated-path> pr-3002-verify` — result:
```
HEAD의 현재 위치는 1205bdab입니다 issue-2981: log inline deviation (branch behind main for check_runner reuse)
```

derived: `git log --oneline -6` (isolated worktree) — result:
```
1205bdab issue-2981: log inline deviation (branch behind main for check_runner reuse)
702b4562 issue-2981: generalize record-only PR detection past one hardcoded branch slug
4fd0dc65 Merge remote-tracking branch 'origin/main' into local-3002-work
b2ec4e1d issue-2981: log skipped warrant-hunter dispatch under build-now bypass
6a27352f issue-2981: check for an existing deliverable PR before respawning a crashed session
f156fdee issue-2977: rebase PR #2993 onto main to resolve landed-record conflict (#3001)
```
`702b4562` is the fix-round commit under review; `1205bdab` (the PR's
current head) is docs-only — derived: `git show 1205bdab --stat` (isolated worktree) — result:
```
 .../deviation-log/20260901T051421117330-40a18a0a24444b18.md       | 8 ++++++++
 1 file changed, 8 insertions(+)
```

**Acceptance checks, re-run against the fetched PR head in the isolated worktree (not trusted from the PR's own test-plan output):**

checked: `python3 -m pytest tests/ -k respawn_skips_existing_deliverable -q` (isolated worktree, untracked in this branch) — result:
```
....                                                                     [100%]
4 passed in 0.98s
```
checked: `python3 -m pytest tests/ -k respawn_proceeds_without_deliverable -q` (isolated worktree, untracked in this branch) — result:
```
.......                                                                  [100%]
7 passed in 0.89s
```
checked: `python3 -m pytest tests/ -k respawn_skip_is_reported -q` (isolated worktree, untracked in this branch) — result:
```
..                                                                       [100%]
2 passed in 0.92s
```
All three named acceptance checks hold. The middle count (7, not the 6 PR
#3002's own body cites) is not a discrepancy: derived: `git show 702b4562 -- tests/test_respawn_deliverable_gate.py` (isolated worktree, untracked in this branch) — result (excerpt) shows the fix round adding exactly one new case,
`test_respawn_proceeds_without_deliverable_when_only_adversarial_review_pr_open`,
alongside the pre-existing `..._independent_verification_pr_open` case —
6 (pre-fix) + 1 (added by 702b4562) = 7 (post-fix), and PR #3002's body was
written before this fix-round commit landed.

**Full regression sweep, same worktree:**

checked: `python3 -m pytest test/ tests/ gates/ -q` (isolated worktree) — result:
```
16 failed, 706 passed, 3 xfailed in 32.99s
```
None of the 16 failing test files (`test_local_dependency_env.py`,
`test_spawn_cross_family_skill_selection.py`,
`test_spawn_skill_judge_haiku_timeout_overlap.py`,
`test_spawn_artifact_skill_pairing.py`, `test_spawn_gate_wiring.py`) are
in the touched-file set (`gates/spawn_on_pr.py`, `gates/test_spawn_on_pr.py`,
`lifecycle.py`, `spawn.py`, `tests/test_respawn_deliverable_gate.py` --
all untracked on this review's own branch, read in the isolated worktree)
— consistent with the PR's own claim that these are pre-existing,
unrelated failures.

**Live reproduction on real repository data (not synthetic fixtures) —
the specific probe this re-verification adds beyond re-running the named
checks:**

checked: `check_runner.pr_diff_paths(root, 3006)` then
`spawn_on_pr._branch_looks_like_deliverable(root, 3006)` (isolated
worktree) against PR #3006 itself, a real, currently-open
`issue-2981/adversarial-review-463d9ca3` record-only PR — result:
```
PR 3006 diff paths: ['docs/issue-2981/reports/adversarial-review-463d9ca3.md', 'docs/issue-2981/reports/adversarial-review-463d9ca3/deviation-log/20260901T045629077582-cab50e9950751d83.md']
touches_implementation_paths: False
_branch_looks_like_deliverable(3006): False
```
Correctly classified NOT a deliverable — the exact gap PR #3006 reported
is closed on the real branch that exposed it.

checked: same two calls against PR #3002 itself, a real genuine
implementation PR — result:
```
PR 3002 non-docs paths sample: ['gates/spawn_on_pr.py', 'gates/test_spawn_on_pr.py', 'lifecycle.py', 'spawn.py', 'tests/test_respawn_deliverable_gate.py']
touches_implementation_paths: True
_branch_looks_like_deliverable(3002): True
```
Correctly classified as a deliverable.

checked: constructing the pre-fix `_VERIFICATION_SLOT_RE` regex
(`^independent-verification-\d+$`) and matching it against the literal
suffix `adversarial-review-463d9ca3` — result: `not match` = `True`, i.e.
the pre-fix code would have treated this real branch as a deliverable
candidate (the inversion the prior verification round reported),
confirming the bug existed on this exact real data and that 702b4562 is
what closes it.

**Inverse-failure probes (per this task's own instruction to check both
directions of misclassification), run as a script file (not `python3 -c`,
per this repo's write-set gate) against the real, unmodified
`_branch_looks_like_deliverable()`, mocking only `check_runner.pr_diff_paths`:**

checked: a record-only diff that also happens to touch one non-`docs/`
path (e.g. a stray edit swept into a record commit) — result:
`_branch_looks_like_deliverable` returns `True` (classified as a
deliverable). This is not a regression introduced by 702b4562 — it is the
same characteristic already accepted for `touches_implementation_paths()`
under issue #2974 (decided by diff content, not intent), reused here
verbatim. It is a real residual edge case worth naming: a record commit
that accidentally includes one non-docs file would suppress a respawn it
should not. Not raised as a blocking finding because it reproduces
identical behavior to the already-accepted #2974 standard this fix
deliberately reuses, not a new defect 702b4562 introduces.

checked: a genuine one-file diff (e.g. `['lifecycle.py']` as the only
touched path, standing in for a small implementation change) — result:
`_branch_looks_like_deliverable` returns `True`. Diff size does not affect
classification, only whether any touched path falls outside `docs/` —
matches the design intent stated in the function's own docstring.

checked: a `gh pr diff` read failure (`pr_diff_paths` returning `None`) —
result: `_branch_looks_like_deliverable` returns `False` (falls through to
"not a confirmed deliverable", i.e. respawn proceeds), and the stderr
audit line fires:
```
[spawn-on-pr] PR #997 의 diff 를 gh 로 못 읽었다 -- deliverable 후보에서 제외 (fail-open: respawn 판단은 '없음' 쪽으로)
```
This matches the issue's must-not (absence or lookup error must default
to respawn, never a silent skip) and the fix commit's stated silent-
failure-audit addition.

**Must-not audit:**

1. Does not disable automatic respawn — canonical: `sed -n '501,570p' lifecycle.py` (isolated worktree, untracked on this review's own branch) shows `_auto_respawn_check()`'s new gate block returns early only on a positive match from `_subject_has_deliverable()`; every `None` result (genuine absence, record-only-only, or lookup error) falls through into the pre-existing, unmodified crashed-respawn body.
2. Does not treat a record-only PR as the deliverable that suppresses a respawn — verified live above against PR #3006 (open, record-only) and already held for the merged-record path (`subject_deliverable_record()`, untouched by 702b4562, still gated on `verifies_subject: true`).
3. Does not close, alter, or force-push any existing PR — checked: `git diff f156fdee..HEAD -- gates/spawn_on_pr.py lifecycle.py spawn.py tests/test_respawn_deliverable_gate.py gates/test_spawn_on_pr.py | grep -iE "pr close|pr edit|force-push|force_push|git push --force"` (isolated worktree, all listed paths untracked on this review's own branch) — result: no output (no match).
4. Does not fix the unreliable verdict itself (issue #2969's separate
   scope) — checked: `git diff f156fdee..HEAD --stat` (isolated worktree)
   lists no `watchdog.py` entry, and the new gate block in
   `_auto_respawn_check()` sits strictly after the pre-existing,
   unmodified `if verdict != "crashed": return` line — session-end-verdict
   computation itself is untouched.

**`_self_trigger_respawn()` status:** canonical: `grep -n "_self_trigger_respawn\|_respawn_or_cap(" lifecycle.py` (isolated worktree, untracked on this review's own branch) — result confirms `_respawn_or_cap()` has exactly two call sites: `_auto_respawn_check()` (now gated by `_subject_has_deliverable()`, this fix round's and the original PR's scope) and `_self_trigger_respawn()` (line 615, still ungated). A prior independent-verification round first live-reproduced this gap (PR #3006, head commit 0322c56bfd0403cbfbef7af34152f2c314db1e22) and a second independent-verification round explicitly adjudicated it as "not treated as a blocker on PR #3002 -- logged as a possible follow-up" (PR #3004, head commit f495f91ce7a793c8a822b66eb72e858bf5cb8807), reasoning that it "falls outside issue #2981's literal 'crashed verdict' framing" (`_self_trigger_respawn` fires on self-detected `uncommitted-work`/`failed-no-commit`/`silent-failure` outcomes, not on a watchdog `crashed` verdict). canonical: `gh pr view 3004` body (read live) contains that adjudication text verbatim. 702b4562 does not touch `_self_trigger_respawn()` -- consistent with that adjudication, not a regression it introduced or silently dropped.

## Why

Per the adversarial-review skill: this session is structurally
independent of the builder sessions behind PR #3002, PR #3006, and
PR #3004 (fresh context, no access to their reasoning), so every claim
above was re-derived against a freshly fetched copy of the PR's actual
head in an isolated worktree rather than accepted from any prior record's
or PR body's own narrative. The task explicitly asked for both
classification directions to be probed on real data, not just the named
unit tests, so the live checks against PR #3006 (a real record-only PR)
and PR #3002 (a real implementation PR) — plus the three inverse-failure
probes — are the substantive addition this record makes beyond re-running
the three `pytest -k` commands.

skill-verdict: adversarial-review — applied: invoked; used its blind,
structurally-independent re-verification stance (fresh worktree, re-run
checks and live probes against real PR data rather than trusting PR
#3002's or PR #3006's own claimed output) to produce this record.
other mounted skills: not triggered.

## Upstream basis

derived: `git fetch origin pull/3002/head:pr-3002-verify && git log --oneline -6` (isolated worktree, this review's own fetch) — result reproduced in "What was done" above. `code_under_review` (`1205bdab`) is PR #3002's own current head; `702b4562` (the fix commit under review) sits three commits back on that same branch.

`702b4562`, `1205bdab`, and the `gates/spawn_on_pr.py` /
`tests/test_respawn_deliverable_gate.py` paths they touch are untracked
on this review's own branch (`main` has not merged PR #3002 yet, so these
paths do not exist in this checkout) and exist only in the isolated
worktree fetched for this review, removed after use.

canonical: `gh pr view 3006` and `gh pr diff 3006` output (read live, this review) — PR #3006 (head `0322c56bfd0403cbfbef7af34152f2c314db1e22`) is the prior independent-verification round that first live-reproduced both the record-only-exclusion gap 702b4562 fixes and the still-open `_self_trigger_respawn()` gap.

canonical: `gh pr view 3004` output (read live, this review) — PR #3004 (head `f495f91ce7a793c8a822b66eb72e858bf5cb8807`) is the round that explicitly adjudicated the `_self_trigger_respawn()` gap as out of issue #2981's literal scope and not a blocker on PR #3002.

## Open findings

1. (already known, adjudicated non-blocking — not new) canonical: `grep -n "_self_trigger_respawn\|_respawn_or_cap(" lifecycle.py` (isolated worktree, untracked on this review's own branch) confirms `_self_trigger_respawn()` (`lifecycle.py:615`) reaches `_respawn_or_cap()` with no `subject_has_deliverable()` consultation. First reported by PR #3006 (head `0322c56b`); PR #3004 (head `f495f91c`) explicitly adjudicated this as out of issue #2981's literal scope and not a blocker on PR #3002 — canonical: `gh pr view 3004` body, read live this review, states verbatim "not treated as a blocker on PR #3002 -- logged as a possible follow-up." derived: `git show 702b4562 --stat` (isolated worktree) lists no `lifecycle.py` entry, confirming the fix round left this file, and this gap, untouched — consistent with the adjudication, not a silent regression.
2. (residual design characteristic, not a regression) derived: inverse-failure probe above ("record-only diff that also happens to touch one non-`docs/` path" — result `True`) shows a record-only PR whose diff happens to also touch one non-`docs/` path is classified as a deliverable. Inherent to the diff-content standard reused verbatim from issue #2974 (`check_runner.touches_implementation_paths()`, unchanged by 702b4562); not introduced by this fix round. Worth naming for anyone revisiting this gate, not worth blocking on since it reproduces already-accepted #2974 behavior exactly.

## What did not work

None.

## Next steps

None required to close this re-verification — `loop_state: landed`. Both
open findings above are pre-existing/adjudicated, not new work this
record is generating; no code change is proposed here.
