---
issue: 3057
role: independent-verification-1
author: independent-verification-1
verifies_subject: true  # independent verification of PR #3058's own deliverable against issue #3057's three verbatim Acceptance checks
code_under_review: on-the-record PR #3058 (cefee7733de82858899c836d98bcff2e6f241fe7, merged to main)
loop_state: landed
type: review
breaking: false
verdict: approve — all three of issue #3057's verbatim `check:` commands pass under fresh, independent re-execution against the merged commit; the two must-not clauses (no catch-and-continue past the AttributeError, no rename of `gates/gates.py`) hold under direct inspection of the diff and a forced-failure unit test that reproduces the exact reported traceback.
upstream:
  - path: on-the-record PR #3058, branch issue-3057/refactoring-legacy-seam-selection+silent-failure-audit+merge-gates+architecture-dependency-direction-9b4a1ebc
    sha: cefee7733de82858899c836d98bcff2e6f241fe7
  - path: docs/issue-3057/reports/refactoring-legacy-seam-selection+silent-failure-audit+merge-gates+architecture-dependency-direction-9b4a1ebc.md
    sha: cefee7733de82858899c836d98bcff2e6f241fe7
---

# issue-3057 — independent-verification-1 record

## What was done

Independent, fresh-checkout verification of PR #3058 (the fix for issue
#3057's merge-gate sibling-import crash) after it landed on `main` at
`cefee7733de8`. Re-ran all three of the issue's verbatim `check:`
commands myself, from a pulled, non-stale checkout, without citing PR
#3058's own record or either of the two prior verification records
(#3060, #3062) as evidence.

acceptance: `diff <(python3 -m gates.merge_gate 3043 issue-3042 2>&1) <(python3 gates/merge_gate.py 3043 issue-3042 2>&1)` — result:
```
(empty — no diff output, diff exit code 0)
```
derived: `python3 -m gates.merge_gate 3043 issue-3042; echo m-exit=$?` and `python3 gates/merge_gate.py 3043 issue-3042; echo script-exit=$?` run separately (not just diffed) — result:
```
m-exit=1
script-exit=1
```
Both invocation forms agree on exit code too, not just on stdout/stderr text.

acceptance: `python3 -m pytest gates/test_merge_gate.py -q` — result:
```
....                                                                     [100%]
4 passed in 0.86s
```
canonical: `gates/test_merge_gate.py:44-63` (`test_internal_failure_exits_two_not_zero_not_one`) — read directly, not summarized:
```python
def test_internal_failure_exits_two_not_zero_not_one(monkeypatch, capsys):
    """must-not (issue #3057): a crash inside `evaluate()` must not be
    caught-and-continued into a fabricated verdict -- it must abort with
    a distinct, non-zero code the caller can never confuse with
    `EXIT_REFUSED`."""
    monkeypatch.setattr(sys, "argv", ["merge_gate.py", "1", "issue-1"])

    def _boom(root, repo, pr, subject):
        raise AttributeError("module 'gates' has no attribute 'record_frontmatter'")

    monkeypatch.setattr(merge_gate, "evaluate", _boom)

    rc = merge_gate.main()

    assert rc == merge_gate.EXIT_COULD_NOT_DECIDE == 2
    assert rc not in (merge_gate.EXIT_ALLOWED, merge_gate.EXIT_REFUSED)
    out = capsys.readouterr()
```
This monkeypatches `evaluate()` to raise the exact `AttributeError` string from the original bug report and asserts `rc == 2` plus the traceback text lands in captured stderr — a direct, non-vacuous reproduction of the reported crash, not a generic exception test.

acceptance: `test -z "$(grep -rln '^import gates$' gates/ on-the-record/gates/)"` — result:
```
(grep produced no output; exit code 1, so the command substitution is empty and -z holds)
```

Beyond the three mandated checks, additionally exercised behavior the
checks don't directly cover, to rule out regressions the diff alone
wouldn't catch.

acceptance: `python3 -m gates.merge_gate 999999 issue-nonexistent` (a PR with no record — check 1's empty-state clause) — result:
```
거절: PR #999999 (issue-nonexistent)
  - check-runner 코멘트를 찾을 수 없다
  - required_verification_missing(): 독립 검증 기록이 부족하다 -- 0/2개 확인됨 (2개 더 필요)
exit=1
```
A PR with no record still produces a considered verdict (refuse, exit 1), not a traceback.

acceptance: `python3 -m gates.merge_gate` (no args) — result:
```
usage: merge_gate.py <pr> <subject> [--repo <경로>]
exit=2
```
This satisfies check 2's empty-state clause ("a gate that cannot decide must not report success") — never `0`.

canonical: `git diff 465f6efc cefee773 -- gates/merge_gate.py gates/check_runner.py` output — read directly: both files replace the bare `import gates` with the same `importlib.util.spec_from_file_location`-by-explicit-path pattern under a shared `sys.modules["_on_the_record_gates_sibling_impl"]` key.

derived: `git diff 465f6efc cefee773 -- gates/gates.py | wc -l` — result:
```
0
```
`gates/gates.py` is untouched by this fix, satisfying the "do not rename `gates/gates.py`" must-not.

canonical: `gates/merge_gate.py` `main()`, read directly in the diff above — the `except Exception:` branch calls `traceback.print_exc()` (prints to stderr) before `return EXIT_COULD_NOT_DECIDE`; nothing is swallowed, satisfying the "do not catch the AttributeError and continue" must-not.

## Why

canonical: this record's own `## What was done` section above (same file, same commit) — every command it cites was executed in this session.

The issue's own text records that a prior landing attempt was stopped
specifically because a gate result would have been recorded without
the gate having run. That raises the bar for this verification: each
check above was re-executed live against the actual merged commit in
this session's own checkout, rather than taken on the word of any
prior session's (including the subject's own) prose description of
what it ran.

## What did not work

None.

## Upstream basis

derived: `git log origin/main --oneline -1 cefee7733de82858899c836d98bcff2e6f241fe7` — result:
```
cefee773 issue-3057: fix merge_gate sibling-import crash, add three-way exit codes (#3058)
```

- `gates/merge_gate.py`, `gates/check_runner.py`, `gates/test_merge_gate.py` at `cefee7733de82858899c836d98bcff2e6f241fe7` (PR #3058, merged to `main`, confirmed above).
- `docs/issue-3057/reports/refactoring-legacy-seam-selection+silent-failure-audit+merge-gates+architecture-dependency-direction-9b4a1ebc.md` — the subject's own deliverable record, read only to identify what to independently re-check, not cited as evidence for any claim above.

## Open findings

canonical: `python3 gates/merge_gate.py 3058 issue-3057` output (run from this checkout before the mid-session `git fetch origin`) —
```
거절: PR #3058 (issue-3057)
  - required_verification_missing(): 독립 검증 기록이 부족하다 -- 1/2개 확인됨 (1개 더 필요)
```
derived: `git log origin/main --oneline -3` (re-run after `git fetch origin` mid-session) — result:
```
cefee773 issue-3057: fix merge_gate sibling-import crash, add three-way exit codes (#3058)
65715ac1 issue-3057: second independent verification of PR #3058 (all criteria Present) (#3062)
f4395d53 issue-3041: builder-blind conformance review of PR #3052 + experiment attack (#3056)
```
Both PR #3062 (second independent verification) and PR #3058 itself merged during this session. No open finding remains: the subject and both required independent verifications are all landed on `main` as of this record.

## Next steps

canonical: `git log origin/main --oneline -1` (same output cited under `## Open findings` above, `cefee773` as tip) — subject already merged, `loop_state: landed` reflects that.

## Skill obligations

skill-verdict: work-in-english — applied: invoked; used via the Skill tool this session to keep this record, the commit message, and the PR body in English per the Korean-language-session policy.
