---
issue: 2976
role: adversarial-review-2acc75af
author: adversarial-review-2acc75af
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2987, the subject's own deliverable for issue #2976
loop_state: landed
upstream:
  - path: spawn.py (PR #2987)
    sha: bc0e7f2836650f1a33777bd73461865415c243c2
  - path: bc0e7f28:tests/test_task_stdin_input_2976.py
    sha: bc0e7f2836650f1a33777bd73461865415c243c2
  - path: bc0e7f28:tests/test_gh_body_not_heredoc_2976.py
    sha: bc0e7f2836650f1a33777bd73461865415c243c2
---

# issue-2976 — adversarial-review-2acc75af record

## What was done

Independently verified PR #2987 (head `bc0e7f28`, merge-base with `main`
`167cc19a`) against issue #2976's acceptance criteria and must-not list,
without trusting the PR's own claimed results. canonical: `gh pr view
2987` (state: OPEN, url
https://github.com/tokenmaxxxer/on-the-record/pull/2987) and `gh issue
view 2976` (state: OPEN) — both fetched live this turn. Method: fetched
the PR head into two throwaway `git worktree`s (one at the PR head, one
at the merge-base `167cc19a`) outside this session's own working tree.

**Acceptance checks, re-run myself in the PR-head worktree this turn:**

acceptance: `python3 -m pytest tests/ -k task_from_stdin -q` — result:
```
1 passed in 0.84s
```
acceptance: `python3 -m pytest tests/ -k task_input_conflict_refused -q` — result:
```
1 passed in 1.16s
```
acceptance: `python3 -m pytest tests/ -k task_body_survives_shell_metacharacters -q` — result:
```
1 passed in 1.18s
```
acceptance: `python3 -m pytest tests/ -k gh_body_not_heredoc -q` — result:
```
1 passed in 0.90s
```

**Full-suite regression check** (not on the acceptance list, but run to
check the PR's own "16 pre-existing failures" claim rather than cite it):

derived: `python3 -m pytest test/ tests/ -q` run in both worktrees this turn:
```
PR-head (bc0e7f28):      16 failed, 626 passed, 3 xfailed in 31.52s
base (167cc19a):         16 failed, 617 passed, 3 xfailed in 32.36s
```
derived: `grep '^FAILED' <each run's output> | sort > {base,pr}_failed.txt && diff base_failed.txt pr_failed.txt` run this turn:
```
(no output -- diff exit 0)
IDENTICAL FAILURE SETS
```
The same 16 tests (derived: counted directly from the `FAILED` line list
in each pytest run above) fail on both commits — no regression. Net new
passing tests on the PR side = 626 - 617 = 9 (derived: arithmetic on the
two pytest summary lines above), matching the test methods PR #2987
adds: derived: `grep -c "    def test_" bc0e7f28:tests/test_task_stdin_input_2976.py bc0e7f28:tests/test_gh_body_not_heredoc_2976.py`
```
tests/test_task_stdin_input_2976.py: 8
tests/test_gh_body_not_heredoc_2976.py: 1
```
8 + 1 = 9, equal to the 626 - 617 = 9 derived above. The pre-existing-failure claim holds.

**Metacharacter survival, tested for real** rather than trusting the
PR's own `io.StringIO`-based unit test: spawned a real `python3 -c ...`
subprocess this turn, piped a body containing `->`, embedded double and
single quotes, and multiple newlines to it over a genuine OS pipe
(`subprocess.run([...], input=body, text=True)`), had the subprocess
call `spawn.resolve_task_text(None, True)` and print the `repr()` of the
result, then compared SHA-256 hashes of the input and recovered
strings. derived: the probe script run this turn — result:
```
MATCH: True
sha256 in:  d909b486e3b0ebdba5058e3f74ac7e34cd1dfef1dadf9250f2df9dfc79a2d2e9
sha256 out: d909b486e3b0ebdba5058e3f74ac7e34cd1dfef1dadf9250f2df9dfc79a2d2e9
```
Byte-for-byte survival confirmed independently of the PR's own test.

**Double-supply refusal, also exercised via a real subprocess** rather
than only the in-process unit test: called
`spawn.resolve_task_text('positional here', True)` in a fresh subprocess
with `"stdin body"` piped on stdin. derived: the probe run this turn —
result:
```
returncode: 1
stderr: spawn.py: task supplied both positionally ('positional here') and via --task-stdin -- refuses to silently prefer one. Supply the task exactly once: either the positional "<task>" argument, or --task-stdin with the body piped on stdin, not both.
```
Confirms the refusal is a real `sys.exit`, not a mocked assertion.

**Must-not list audit**, each checked against the actual diff
(`git diff main...pr-2987-verify`) this turn, not the PR description:

1. **Positional `<task>` stays the unchanged default.** canonical:
   `git diff main...pr-2987-verify -- spawn.py` (read this turn) shows
   `resolve_task_text()` returns `positional_task` unmodified whenever
   `use_stdin` is `False` (`return positional_task` as the function's
   final line), and the only call site changed is the `--skills` branch
   (`bc0e7f28:spawn.py:2421`, `task_text = resolve_task_text(a.role,
   a.task_stdin)`). The other positional-consuming branches (`--skill`
   at `bc0e7f28:spawn.py:2462`, `--skill-candidates` at
   `bc0e7f28:spawn.py:2498`) do not appear in the diff at all. #2572's
   `--skills <skill> "<task>"` form remains the only session-spawning
   form; `--task-stdin` adds a channel under it, not a new spawn form.
2. **Conflicting double-supply is refused, not resolved by precedence.**
   Confirmed by both the diff (`sys.exit` naming both values, in the
   `resolve_task_text` body added by `git diff main...pr-2987-verify --
   spawn.py`) and the real-subprocess re-run above.
3. **`heredoc-command-refusal-gate.sh` is not weakened or bypassed.**
   canonical: `git diff main...pr-2987-verify --
   'on-the-record/hooks/heredoc*'` (run this turn) — result: empty, no
   output. The gate file itself is byte-identical to `main`. The PR's
   fix is caller-side only: `bc0e7f28:tests/test_gh_body_not_heredoc_2976.py`
   is a new static-scan regression test locking in that no `.py`/`.sh`
   file in the repo builds a `gh --body`/`--body-file` argument from a
   `$(cat <<DELIM ... DELIM)` heredoc. canonical: `grep -n "body"
   gates/check_runner.py relay.py` and reading the matched lines (run
   this turn) confirm the two production `gh --body` call sites the PR
   names — `gates/check_runner.py:508` and `relay.py:268` — both already
   build the command as a `subprocess.run([...])` argv list, not a
   shell heredoc, so the gate (which inspects Bash-tool shell strings)
   has nothing to refuse there.
4. **No temp-file-as-primary-mechanism.** canonical: reading
   `git diff main...pr-2987-verify -- spawn.py` this turn —
   `resolve_task_text()` calls `stdin.read()` directly, no
   `tempfile`/`NamedTemporaryFile`/`mkstemp` call anywhere in the added
   lines. derived: `grep -n "tempfile\|NamedTemporaryFile\|mkstemp"
   spawn.py` (run this turn) shows 3 hits, at lines 1735-1736, 2158, and
   4426 — none of which appear in `git diff main...pr-2987-verify --
   spawn.py`, i.e. all three predate the PR and are unrelated call
   sites.

Also read the PR's own deviation-log entry,
`bc0e7f28:docs/issue-2976/reports/api-design-tool-landscape+test-derivation-451375cb/deviation-log/20260901T040551750552-400a60b2ff4812ba.md`
(commit `bc0e7f28`): it records that a first attempt mirrored the
stdin/`--body-file` fix into `gates/check_runner.py` and `relay.py` for
symmetry, broke `test/test_branch_skill_field.py`'s
`PrBodyTrailerWriteShapeTest`, and was reverted in favor of the static
regression test instead. This account is consistent with what I found
independently in point 3 above (both call sites already used argv
lists, so the gate could never have reached them) — a reasonable
engineering call, not a cover for weakening the gate.

**Verdict: PR #2987 satisfies all four of issue #2976's acceptance
checks and all four must-not constraints**, verified independently
rather than by citing the PR's own claims. No regressions found in the
full test suite (identical 16-failure set on base and head, derived
above). No open findings.

## Why

The task explicitly required not trusting the PR's claimed results and
re-deriving evidence independently
([[defect-verification-independence-from-upstream-verdicts]]). Two
throwaway `git worktree`s (PR head + merge-base) kept the verification
isolated from this session's own working tree and let a real
base-vs-head regression diff be computed rather than assumed.
Real-subprocess/real-OS-pipe re-tests of the metacharacter-survival and
double-supply-refusal claims were used instead of only re-running the
PR's own `io.StringIO`-based unit tests, per the task's explicit
instruction to "test the metacharacter claim for real."

## What did not work

None.

## Upstream basis

PR #2987 (branch `pr-2987-verify`, fetched from `refs/pull/2987/head`
this turn), head commit `bc0e7f2836650f1a33777bd73461865415c243c2`,
merge-base with `main` at `167cc19a9cf9dd31ac90250d0f9a069f6d70bf68`.
Issue #2976 (`gh issue view 2976`, read this turn) for the acceptance
criteria and must-not list verbatim.

## Open findings

None.

## Next steps

canonical: all four acceptance checks and the full-suite regression
diff above were re-run by this session this turn against PR #2987's
actual head commit, not cited from the PR's description — no further
verification action remains open. loop_state terminal.
