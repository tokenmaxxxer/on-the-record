---
issue: 2962
role: independent-verification-2
author: independent-verification-2
verifies_subject: true  # independent verification of PR #2966 (issue-2962/silent-failure-audit+test-derivation-167b9a63), reviewed and audited this session
code_under_review: on-the-record/hooks/fail-open-wrapper.sh, on-the-record/hooks/hook_ledger.py, on-the-record/hooks/stop-gate.sh, on-the-record/hooks/skill-verdict-guard.sh, on-the-record/hooks/post-landing-obligation-gate.sh, on-the-record/hooks/hook_classification.json, on-the-record/hooks/test_hook_classification.py, on-the-record/hooks/test_visible_fail_open.py, on-the-record/hooks/test_notice_no_external_dependency.py, on-the-record/hooks/test_heredoc_failure_bails.py, on-the-record/hooks/test_fail_open_ledger_fields.py
type: verification
breaking: no
verdict: pass
loop_state: terminal
upstream:
  - path: docs/issue-2962/reports/silent-failure-audit+test-derivation-167b9a63.md
    sha: bc88f397fcf9aa8d0153794e65d670b5f2ddef55
  - path: on-the-record/hooks/hook_classification.json
    sha: bc88f397fcf9aa8d0153794e65d670b5f2ddef55
---

# issue-2962 — independent-verification-2 record

## What was done

Independently audited PR #2966 (branch `issue-2962/silent-failure-audit+test-derivation-167b9a63`, code commit `bc88f397`, record commit `57fab5bd`, base `5c0cc599`) against issue #2962's 5 acceptance checks. Fetched the branch into a scratch git worktree, ran all 5 acceptance pytest selectors plus the PR's claimed regression suite, read every changed file's diff, and reproduced the runtime exit-code path of the heredoc-bail fix through each of the 3 affected hooks (including their pre-existing `EXIT` traps) to check the "must not fail-closed" claim by execution rather than by reading alone.

canonical: `gh pr view 2966 --json title,body,files,commits,state,mergeable,baseRefName,headRefName` output this session — state OPEN, mergeable MERGEABLE, base main, 12 files changed (5 modified, 7 added: `hook_classification.json` + 5 `test_*.py` + 1 report), body contains `Closes #2962`.

Acceptance checks, executed live this session against the fetched PR branch (`bc88f397fcf9aa8d0153794e65d670b5f2ddef55`), in a `git worktree add /tmp/pr2966-review2 FETCH_HEAD` scratch checkout, matching the PR body's own claimed counts exactly:

```
$ python3 -m pytest on-the-record/hooks/ -k hook_classification -q
6 passed in 0.81s
$ python3 -m pytest on-the-record/hooks/ -k visible_fail_open -q
6 passed in 0.98s
$ python3 -m pytest on-the-record/hooks/ -k notice_no_external_dependency -q
3 passed in 0.83s
$ python3 -m pytest on-the-record/hooks/ -k heredoc_failure_bails -q
5 passed in 0.81s
$ python3 -m pytest on-the-record/hooks/ -k fail_open_ledger_fields -q
5 passed in 0.87s
```

derived: `bash -n on-the-record/hooks/fail-open-wrapper.sh on-the-record/hooks/stop-gate.sh on-the-record/hooks/skill-verdict-guard.sh on-the-record/hooks/post-landing-obligation-gate.sh` (in the same worktree) — result: clean, no output, exit 0 on each of the 4 edited `.sh` files.

derived: `python3 -m pytest on-the-record/checks/ on-the-record/hooks/ -q` (same worktree) — result: `29 passed`, matching the PR body's claimed count.

derived: `grep -c '"command":' on-the-record/hooks/hooks.json` (same worktree) — result: `12`, matching `bc88f397fcf9aa8d0153794e65d670b5f2ddef55:on-the-record/hooks/hook_classification.json`'s 12 `registrations` entries (6 `invariant-injecting` / 6 `observability`, `pretooluse-dispatcher.sh` the sole `wrapped: false`) — canonical: `python3 -c "import json; c=json.load(open('on-the-record/hooks/hook_classification.json')); print(len(c['registrations']))"` output this session — result: `12`.

derived: `git diff 5c0cc599..57fab5bd -- on-the-record/hooks/pretooluse-dispatcher.sh` (same worktree) — result: empty diff, confirming `pretooluse-dispatcher.sh` is untouched by the PR.

## Why

Verified each of the PR's must-not claims by reading source and, where the claim was about runtime behavior rather than static text, by executing a faithful reproduction — this repo's own bar is a canonical citation, not a prose summary. The one claim needing a live repro rather than a read was the upstream record's "the 3 heredoc-bailed hooks forward the same exit code the old cascade already produced" — this interacts with a pre-existing `trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT` present in 2 of the 3 hooks (`stop-gate.sh` line 20, `skill-verdict-guard.sh` line 56, per `bc88f397fcf9aa8d0153794e65d670b5f2ddef55:on-the-record/hooks/stop-gate.sh:20` and `:on-the-record/hooks/skill-verdict-guard.sh:56`, both read directly this session), so reasoning from the diff alone was not enough.

derived: minimal repro of the actual trap + new bail shape (mirrors `stop-gate.sh` lines 20 and 115 exactly: pre-existing `EXIT` trap, then the PR's new `VAR="" ; heredoc ; [ -n "$VAR" ] || { echo ...; exit 1; }` bail):
```
$ cat > /tmp/test_stopgate.sh <<'OUTER'
#!/usr/bin/env bash
set -uo pipefail
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
CHECK=""
[ -n "$CHECK" ] || { echo "bail" >&2; exit 1; }
echo "unreachable"
OUTER
$ bash /tmp/test_stopgate.sh; echo "exit code: $?"
bail
exit code: 2
```
result: the observed process exit code for the `stop-gate.sh`/`skill-verdict-guard.sh` bail shape is `2`, not `1` — the pre-existing trap remaps any non-0/2 internal exit to `2` before `fail-open-wrapper.sh` ever runs its own detection. `fail-open-wrapper.sh`'s fail-open check (`bc88f397fcf9aa8d0153794e65d670b5f2ddef55:on-the-record/hooks/fail-open-wrapper.sh:57`: `[ "$rc" -ne 0 ] && [ "$rc" -ne 2 ]`) explicitly excludes `rc == 2`, so for these 2 hooks the heredoc-bail path does not trigger the new `[fail-open][DEGRADED]` notice — it resolves as a deny to the wrapper, both before this PR (the old unbound-variable cascade also ends in a bash-level exit 1 that the same pre-existing trap would already have remapped to 2) and after (this repro). Not a behavior change; see Open findings for the precise wording gap this produces in the upstream record. Only `post-landing-obligation-gate.sh` (no such trap — checked: `grep -n "trap\|set -u" bc88f397fcf9aa8d0153794e65d670b5f2ddef55:on-the-record/hooks/post-landing-obligation-gate.sh` — result: only `set -uo pipefail` at line 38, no `trap`) genuinely exercises the fail-open-detected-and-notice-fires path for the heredoc scenario — consistent with the upstream record's own must-not section, which separately states "post-landing-obligation-gate.sh remains fail-open."

## What did not work

None.

## Upstream basis

`docs/issue-2962/reports/silent-failure-audit+test-derivation-167b9a63.md` (`bc88f397fcf9aa8d0153794e65d670b5f2ddef55` — untracked on this branch's own tree; fetched via `git fetch origin issue-2962/silent-failure-audit+test-derivation-167b9a63` into a scratch worktree and read in full from that commit this session) — the phase-2 implementation record for PR #2966.

`on-the-record/hooks/hook_classification.json` (`bc88f397fcf9aa8d0153794e65d670b5f2ddef55` — likewise untracked on this branch, fetched the same way) — cross-checked directly against `on-the-record/hooks/hooks.json` at the same commit, independent of the PR's own `test_hook_classification.py`.

## Open findings

1. **Upstream record wording is imprecise about which exit code `fail-open-wrapper.sh` actually observes — not a functional defect.** `bc88f397fcf9aa8d0153794e65d670b5f2ddef55:docs/issue-2962/reports/silent-failure-audit+test-derivation-167b9a63.md`'s must-not section states "the 3 heredoc-bailed hooks forward the same exit code the old cascade already produced (`1`)" as a flat claim across all 3 hooks. Per the derived repro in `## Why` above, the exit code actually observed by `fail-open-wrapper.sh` is `2` for 2 of the 3 (`stop-gate.sh`, `skill-verdict-guard.sh`), not `1`, because of their pre-existing fail-closed `EXIT` trap. The claim holds only at the narrower layer of "the bash-level exit code produced at the bail statement itself, before the trap remaps it" (`1` in both old and new code — no regression there either). Resolution path: none required — the underlying safety property (no new fail-closed behavior introduced; these 2 hooks were already fail-closed-on-internal-error by design predating this issue, per their own inline comment "matching deliverable-guard.sh's house style") holds under direct execution regardless of the wording; a future editor of that record could tighten the sentence to name the trap explicitly, but nothing here blocks this PR.
2. **Soft test-coverage gap in `test_bail_exit_code_is_never_2_deny`.** `bc88f397fcf9aa8d0153794e65d670b5f2ddef55:on-the-record/hooks/test_heredoc_failure_bails.py` (`test_bail_exit_code_is_never_2_deny`) is a static regex check of the literal `exit 1` text in each hook's source; it does not execute the real wrapped hook end-to-end through bash, so it never reaches the pre-existing trap. For `post-landing-obligation-gate.sh` (no trap) the static check and real runtime behavior coincide; for `stop-gate.sh`/`skill-verdict-guard.sh` they diverge (source text says `exit 1`, real observed exit is `2`, per finding 1's repro), so the test's own docstring claim ("must not... must not be the platform's block/deny code") is not actually proven end-to-end for those 2 files by this test. Resolution path: not required for this PR to land — no functional defect results (finding 1) — but a future hardening pass on this test file should add an execution-based assertion (run the real hook with a monkeypatched-empty heredoc var, assert the wrapper-observed `$?`) for the 2 trap-wrapped hooks specifically, to make the docstring's claim true by construction rather than by accident of design.

Neither finding blocks this PR. acceptance: `python3 -m pytest on-the-record/hooks/ -k hook_classification -q; python3 -m pytest on-the-record/hooks/ -k visible_fail_open -q; python3 -m pytest on-the-record/hooks/ -k notice_no_external_dependency -q; python3 -m pytest on-the-record/hooks/ -k heredoc_failure_bails -q; python3 -m pytest on-the-record/hooks/ -k fail_open_ledger_fields -q` — result:
```
6 passed in 0.81s
6 passed in 0.98s
3 passed in 0.83s
5 passed in 0.81s
5 passed in 0.87s
```
All 5 acceptance checks pass (re-run this session in the same order as `## What was done`), matching the PR body's own claimed counts. The classification data and the wrapper's notice/ledger mechanism are correctly built and tested for the general (non-heredoc, non-trapped) fail-open path, which is what protects `directive.sh` and `session-role-bind.sh` — the issue's own named worst case (neither of those 2 hooks has an `EXIT` trap — checked: `grep -n "^trap" bc88f397fcf9aa8d0153794e65d670b5f2ddef55:on-the-record/hooks/directive.sh bc88f397fcf9aa8d0153794e65d670b5f2ddef55:on-the-record/hooks/session-role-bind.sh` — result: no matches in either file).

## Next steps

None — loop_state is terminal. acceptance: `python3 -m pytest on-the-record/hooks/ -k hook_classification -q; python3 -m pytest on-the-record/hooks/ -k visible_fail_open -q; python3 -m pytest on-the-record/hooks/ -k notice_no_external_dependency -q; python3 -m pytest on-the-record/hooks/ -k heredoc_failure_bails -q; python3 -m pytest on-the-record/hooks/ -k fail_open_ledger_fields -q` — result:
```
6 passed in 0.81s
6 passed in 0.98s
3 passed in 0.83s
5 passed in 0.81s
5 passed in 0.87s
```
All 5 acceptance requirements met, executed this session against PR branch `bc88f397fcf9aa8d0153794e65d670b5f2ddef55`, matching the PR body's own claimed counts.

skill-verdict: work-in-english — not-applicable: repo and task were already conducted in English; the user's Korean prompt was directive/task-assignment boilerplate, no content required translation.
other mounted skills: not triggered
