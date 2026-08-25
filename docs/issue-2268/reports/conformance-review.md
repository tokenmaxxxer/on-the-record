---
issue: 2268
role: conformance-review
kind: review-record
loop_state: reported
upstream:
  - path: docs/issue-2268/reports/implementation.md
    sha: 577d03a8321d3b6ae21cb62b3b34a9c1e7eff26a
  - path: gates/merge_gate.py
    sha: 577d03a8321d3b6ae21cb62b3b34a9c1e7eff26a
  - path: gates/test_merge_gate.py
    sha: 577d03a8321d3b6ae21cb62b3b34a9c1e7eff26a
subject: PR #2271 (branch issue-2268/implementation, head 577d03a8321d3b6ae21cb62b3b34a9c1e7eff26a)
test: gates/test_merge_gate.py (full suite re-run live below)
result: passed
assertedBy: conformance-review session, issue-2268
---

# issue-2268 — conformance-review record

## What was done

Builder-blind conformance review of PR #2271 against issue #2268's
frozen `## Acceptance` section (gate / empty-state / provenance) and
the `## Ask` clauses it points back to. Added the PR branch as a git
worktree at `/tmp/wt-2271` (head `577d03a8321d3b6ae21cb62b3b34a9c1e7eff26a`)
and independently re-executed every acceptance claim below rather than
citing the builder's implementation record as evidence in itself.

canonical: cd /tmp/wt-2271 && git log --oneline -1 HEAD
```
$ cd /tmp/wt-2271 && git log --oneline -1 HEAD
577d03a8 issue-2268: widen merge_gate's finder to match the no-checks header
```

skill-verdict: conformance-review-requirement-extraction — applied: invoked; used to split issue #2268's Ask/Acceptance text into the six discrete obligations verdicted below
skill-verdict: conformance-review-verification-method-selection — applied: invoked; used to pick Inspection (regex/precedence diff) vs Test (existing suite reuse) vs Demonstration (live before/after command) per requirement
skill-verdict: conformance-review-verdict-assignment — applied: invoked; used to assign Present per requirement below, each carrying its own re-derived evidence rather than a carried-forward prior verdict
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; used to cite file:line + head sha + live command output per finding, and to check the upstream commit the implementation record cites (9e2e2382) before relying on it, see Upstream basis
skill-verdict: conformance-review-finding-record — applied: invoked; used to shape each per-requirement block (requirement/spec_ref/verdict/evidence/rationale)
skill-verdict: conformance-review-sampling-derivation — not-applicable: issue #2268's Acceptance section is one gate line, one empty-state line, and one provenance line plus the Ask's two clauses — fully enumerable, no sampling needed
skill-verdict: conformance-review-severity-classification — not-applicable: review scope was not explicitly extended into risk-weighting a recorded finding; no finding needed banding
skill-verdict: implementation-audit — not-applicable: cross-family match on this session's task text (issue keywords "spec"/"implementation"/"verify"), but this session already runs under the role-handoff contract's own two-session builder/evaluator split (implementation session #2271 built, this conformance-review session evaluates independently) — a second, separate audit protocol was not invoked on top of it

## Why

Issue #2268's `provenance:` line demands the before/after command pair
be run live with real output pasted, not merely asserted from a diff
read — a review that only reads the diff and cites the builder's own
pasted transcript as its evidence repeats the "looked green, checked
nothing" failure mode this repo has hit before (issue-2231
conformance-review precedent, also cited by the issue-2214
conformance-review record). Every acceptance-evidence claim in the
builder's implementation record was independently re-executed in this
session, including reconstructing the pre-fix regex myself to
reproduce the "before" behavior rather than trusting the record's
pasted "before" transcript at face value.

## Upstream basis

- The builder's implementation record at
  `577d03a8321d3b6ae21cb62b3b34a9c1e7eff26a` (PR #2271 branch) — every
  acceptance-evidence line in it was independently re-executed here,
  not cited as evidence in itself.
- `gates/merge_gate.py` at `577d03a8321d3b6ae21cb62b3b34a9c1e7eff26a`
  — `_RESULT_HEADER` (lines 29-31), `parse_check_runner_result()`
  (34-46), `latest_check_runner_comment()` (50-67).
- `gates/test_merge_gate.py` at `577d03a8321d3b6ae21cb62b3b34a9c1e7eff26a`
  — `t_finder_reaches_no_checks_branch_through_evaluate` and
  `t_finder_empty_state_still_reports_comment_missing`, re-run live
  below alongside the full pre-existing suite.
- `gates/check_runner.py` at `577d03a8321d3b6ae21cb62b3b34a9c1e7eff26a`
  — `NO_CHECKS_MARKER` (line 36), `format_no_checks_comment()`
  (248-267) — read, not modified this session.
- Commit `9e2e2382ada5f1da915c015e8288fb1bc0f20cd0` (issue-2231, PR
  #2244) — the commit the implementation record cites as the one that
  added `NO_CHECKS_MARKER` handling without widening the finder;
  checked below rather than trusted from the record's citation alone.

canonical: cd /tmp/wt-2271 && git cat-file -e 9e2e2382ada5f1da915c015e8288fb1bc0f20cd0 && git log --oneline -1 9e2e2382ada5f1da915c015e8288fb1bc0f20cd0 && diff <(git show 9e2e2382ada5f1da915c015e8288fb1bc0f20cd0:gates/merge_gate.py) <(git show 577d03a8321d3b6ae21cb62b3b34a9c1e7eff26a~1:gates/merge_gate.py)
```
$ cd /tmp/wt-2271 && git cat-file -e 9e2e2382ada5f1da915c015e8288fb1bc0f20cd0 && echo exists
exists
$ git log --oneline -1 9e2e2382ada5f1da915c015e8288fb1bc0f20cd0
9e2e2382 issue-2231: grade prose Acceptance criteria, distinguish no-criteria from pass, fix citation-format false-block (#2244)
$ diff <(git show 9e2e2382ada5f1da915c015e8288fb1bc0f20cd0:gates/merge_gate.py) <(git show 577d03a8321d3b6ae21cb62b3b34a9c1e7eff26a~1:gates/merge_gate.py)
(no output — identical: 9e2e2382's gates/merge_gate.py is byte-identical to 577d03a8's immediate parent's version of the same file)
```
Issue #2268's own repro description ("PR #2228 carries the no-checks
comment ... $2268's finder never widened") matches this commit's known
role (adds the `NO_CHECKS_MARKER`-first branch to
`parse_check_runner_result`, per its own subject line above) and its
`gates/merge_gate.py` content is confirmed identical to the file state
immediately before `577d03a8`'s fix — independently verifying the
implementation record's upstream citation rather than trusting it.
- Issue #2268's frozen `## Problem`/`## Ask`/`## Acceptance` text, as
  supplied in this review's dispatch (also re-fetched via
  `gh issue view 2268` this session, byte-identical to the dispatch
  text).

## Open findings

One informational, non-blocking observation outside the frozen
Acceptance scope: `parse_check_runner_result()` (`gates/merge_gate.py:41-46`)
checks `check_runner.NO_CHECKS_MARKER in comment_body` (an exact
substring test) before falling back to `_RESULT_HEADER.search()` and
then unconditionally reading `m.group(1)`/`m.group(2)`. The widened
regex's `no checks declared` alternative can in principle match comment
text that does not contain the exact `NO_CHECKS_MARKER` substring
(e.g. extra internal whitespace, since the regex's `\s*` is more
permissive than the literal marker string) — in that case `m.group(1)`
is `None` and `int(None)` would raise `TypeError` rather than returning
a `no_checks` result.

canonical: cd /tmp/wt-2271 && grep -rn "no checks declared" --include=*.py .
```
$ cd /tmp/wt-2271 && grep -rn "no checks declared" --include=*.py .
./gates/merge_gate.py:30:    r"^## Acceptance check-runner result:\s*(?:(\d+)/(\d+)\s*passed|no checks declared)",
./gates/merge_gate.py:207:                            "없다(no checks declared) — 통과로 취급하지 않는다")
./gates/test_merge_gate.py:17:   아니라 별개의 "no checks declared" 결과여야 하고, 머지 게이트는 그걸
./gates/check_runner.py:36:NO_CHECKS_MARKER = "## Acceptance check-runner result: no checks declared"
```
This confirms `NO_CHECKS_MARKER` (`gates/check_runner.py:36`) is the
sole producer of the "no checks declared" header text anywhere in this
repo, and it always emits the marker byte-for-byte — so the latent gap
above is not reachable through any code path in this repo today, does
not violate any clause of issue #2268's frozen Acceptance section, and
is not verdicted as a requirement below. Resolution path, if picked
up: have `parse_check_runner_result` special-case a `None` group
instead of indexing it directly, or leave as-is with a comment noting
the invariant it currently relies on.

## Next steps

`loop_state` is set to `reported`, the terminal value for a
`review-record`. Nothing further from this review; the human decision
on PR #2271 (merge/close) is out of this record's scope.

---

requirement: `_RESULT_HEADER` (the finder `latest_check_runner_comment` searches PR comments with) matches both the numeric `N/M passed` header and the no-checks `## Acceptance check-runner result: no checks declared` header
spec_ref: issue-2268 ## Ask paragraph 1, first clause ("Widen the finder to match both header shapes (numeric and no-checks)")
verdict: Present
canonical: git diff 9e2e2382..577d03a8 -- gates/merge_gate.py
```
$ cd /tmp/wt-2271 && git diff 9e2e2382ada5f1da915c015e8288fb1bc0f20cd0 577d03a8321d3b6ae21cb62b3b34a9c1e7eff26a -- gates/merge_gate.py
-_RESULT_HEADER = re.compile(
-    r"^## Acceptance check-runner result:\s*(\d+)/(\d+)\s*passed", re.MULTILINE)
+_RESULT_HEADER = re.compile(
+    r"^## Acceptance check-runner result:\s*(?:(\d+)/(\d+)\s*passed|no checks declared)",
+    re.MULTILINE)
```
evidence: `gates/merge_gate.py:29-31`. `latest_check_runner_comment()`
(`gates/merge_gate.py:50-67`) is the only function that scans PR
comments and it gates on `_RESULT_HEADER.search(body)` (line 65) — the
same compiled pattern now widened above.
rationale: The finder's own search pattern now contains a
non-capturing alternation whose second branch is the literal no-checks
header text, so a comment carrying either header shape satisfies
`_RESULT_HEADER.search()` and is returned by the finder; independently
confirmed live below (requirement "empty state" and "provenance").

---

requirement: `parse_check_runner_result`'s existing no-checks-before-numeric precedence is left untouched by the finder widening
spec_ref: issue-2268 ## Ask paragraph 1, second clause ("keeping `parse_check_runner_result`'s existing precedence")
verdict: Present
canonical: git diff 9e2e2382..577d03a8 -- gates/merge_gate.py (parse_check_runner_result hunk)
```
$ cd /tmp/wt-2271 && git diff 9e2e2382ada5f1da915c015e8288fb1bc0f20cd0 577d03a8321d3b6ae21cb62b3b34a9c1e7eff26a -- gates/merge_gate.py | grep -c "parse_check_runner_result"
0
```
evidence: `gates/merge_gate.py:34-46` — `parse_check_runner_result()`
still checks `if check_runner.NO_CHECKS_MARKER in comment_body: return
{"no_checks": True}` (line 42) before ever calling
`_RESULT_HEADER.search()` (line 44); the diff above touches nothing in
this function (0 lines mentioning it), confirming the function body is
byte-for-byte identical between `9e2e2382` and `577d03a8`.
rationale: The diff touches only `_RESULT_HEADER`'s own regex
definition, not the function that consumes it — the no-checks-first
precedence the issue asks to preserve was never edited, confirmed by
the zero-hit diff on that function.

---

requirement: a test drives the real chain `latest_check_runner_comment` -> `parse_check_runner_result` -> `evaluate()` with a no-checks comment, via a mocked `gh pr view` (not a monkeypatched finder)
spec_ref: issue-2268 ## Ask paragraph 2 ("Add a test that goes through latest_check_runner_comment -> parse_check_runner_result -> evaluate() with a no-checks comment — the unit tests in #2244 tested the parser directly and missed the finder")
verdict: Present
canonical: python3 -m pytest gates/test_merge_gate.py::t_finder_reaches_no_checks_branch_through_evaluate -v
```
$ cd /tmp/wt-2271 && python3 -m pytest gates/test_merge_gate.py::t_finder_reaches_no_checks_branch_through_evaluate -v 2>&1 | grep -E "PASSED|FAILED|ERROR"
gates/test_merge_gate.py::t_finder_reaches_no_checks_branch_through_evaluate PASSED
```
evidence: `gates/test_merge_gate.py:322-350` —
`t_finder_reaches_no_checks_branch_through_evaluate` monkeypatches
`subprocess.run` (the `gh pr view` call inside
`latest_check_runner_comment`, `gates/merge_gate.py:52`) to return a
comment list containing `check_runner.format_no_checks_comment()`
verbatim, then calls `merge_gate.latest_check_runner_comment()`
directly and asserts it returns the no-checks body, then calls
`merge_gate.evaluate()` and asserts the reasons contain the no-checks
refusal text and not the comment-not-found text. It does not
monkeypatch `latest_check_runner_comment` itself.
rationale: This is exactly the finder-through-evaluate path the issue
asks for, exercised through the same `subprocess.run` seam the real
`gh pr view` call uses rather than by substituting a fake finder
function — satisfying the issue's explicit complaint that #2244's
tests "tested the parser directly and missed the finder."

---

requirement: empty state — a PR with no check-runner comment of either shape still reports comment-not-found
spec_ref: issue-2268 ## Acceptance, "empty state:" line
verdict: Present
canonical: python3 -m pytest gates/test_merge_gate.py::t_finder_empty_state_still_reports_comment_missing -v
```
$ cd /tmp/wt-2271 && python3 -m pytest gates/test_merge_gate.py::t_finder_empty_state_still_reports_comment_missing -v 2>&1 | grep -E "PASSED|FAILED|ERROR"
gates/test_merge_gate.py::t_finder_empty_state_still_reports_comment_missing PASSED
```
evidence: `gates/test_merge_gate.py:353-370` — mocks `subprocess.run`
to return a comment list with only an unrelated comment (neither header
shape present), asserts `merge_gate.latest_check_runner_comment()`
returns `None`, and asserts `evaluate()`'s reasons still contain
`"코멘트"` (comment-not-found).
rationale: Directly matches the Acceptance section's stated empty-state
clause, independently re-run and passing.

---

requirement: gate — `gates/test_merge_gate.py` passes in full
spec_ref: issue-2268 ## Acceptance, "gate:" line
verdict: Present
canonical: python3 -m pytest gates/test_merge_gate.py -q
```
$ cd /tmp/wt-2271 && python3 -m pytest gates/test_merge_gate.py -q 2>&1 | tail -3
.........................                                                [100%]
25 passed in 0.94s
```
evidence: Full suite re-run live in this review's own worktree
(`/tmp/wt-2271`, head `577d03a8321d3b6ae21cb62b3b34a9c1e7eff26a`), not
copied from the implementation record's pasted count — 25 passed
matches the record's claim, independently reproduced.
rationale: The issue's gate criterion is satisfied by a suite that
passes in full; this review ran it itself rather than trusting the
pasted transcript.

---

requirement: provenance — `python3 gates/merge_gate.py 2228 issue-2211` before this commit shows comment-not-found despite the comment existing; after this commit shows the no-checks branch reached and still not treated as a pass
spec_ref: issue-2268 ## Acceptance, "provenance:" line
verdict: Present
canonical: python3 gates/merge_gate.py 2228 issue-2211 (before, via commit 9e2e2382's gates/merge_gate.py; after, via HEAD)
```
$ cd /tmp/wt-2271 && cp gates/merge_gate.py /tmp/merge_gate_after.py
$ git show 9e2e2382ada5f1da915c015e8288fb1bc0f20cd0:gates/merge_gate.py > gates/merge_gate.py   # reconstruct pre-fix finder
$ python3 gates/merge_gate.py 2228 issue-2211
거절: PR #2228 (issue-2211)
  - check-runner 코멘트를 찾을 수 없다
$ cp /tmp/merge_gate_after.py gates/merge_gate.py   # restore PR #2271's fix
$ python3 gates/merge_gate.py 2228 issue-2211
거절: PR #2228 (issue-2211)
  - check-runner: 이슈의 Acceptance 절에 실행가능한 검사가 없다(no checks declared) — 통과로 취급하지 않는다
```
evidence: Both runs executed live against the real PR #2228 in this
review session (not copied from the implementation record) — the
"before" run used the actual pre-fix regex reconstructed from commit
`9e2e2382` (confirmed identical to `577d03a8`'s parent in Upstream
basis above), not a paraphrase. Output matches the implementation
record's pasted pair byte-for-byte, independently reproduced.
rationale: The before/after pair shows exactly the transition the
issue's provenance line requires — comment-not-found becomes the
no-checks refusal, while the PR remains refused either way (not treated
as satisfied-by-default), matching the Acceptance clause's explicit
"still not treated as satisfied-by-default" condition.
