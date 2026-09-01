---
issue: 2976
role: adversarial-review-8afe9ef3
author: adversarial-review-8afe9ef3
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2987 (issue-2976/api-design-tool-landscape+test-derivation-451375cb), reviewed and audited this session
code_under_review: spawn.py, tests/test_task_stdin_input_2976.py, tests/test_gh_body_not_heredoc_2976.py
type: verification
breaking: no
verdict: pass
loop_state: terminal
upstream:
  - path: docs/issue-2976/reports/api-design-tool-landscape+test-derivation-451375cb.md
    sha: bc0e7f2836650f1a33777bd73461865415c243c2
---

# issue-2976 — adversarial-review-8afe9ef3 record

## What was done

Independently verified PR #2987 (branch
`issue-2976/api-design-tool-landscape+test-derivation-451375cb`, head
`bc0e7f2836650f1a33777bd73461865415c243c2`, base `main`). Fetched the PR
head into an isolated `git worktree` (`/tmp/verify-2976/pr2987`, removed
before this record was written), re-ran all four of issue #2976's
acceptance checks there from scratch, re-derived the metacharacter
survival claim independently (not by trusting the shipped test), and
read the full `spawn.py` diff line-by-line against the issue's must-not
list.

canonical: `gh pr view 2987 --json headRefName,headRefOid,baseRefName,mergeable` output this session — head `bc0e7f2836650f1a33777bd73461865415c243c2`, base `main`, mergeable `MERGEABLE`.

Acceptance checks, executed live this session against the fetched PR
branch in the isolated worktree:

```
$ python3 -m pytest tests/ -k task_from_stdin -q
1 passed in 0.82s
$ python3 -m pytest tests/ -k task_input_conflict_refused -q
1 passed in 0.81s
$ python3 -m pytest tests/ -k task_body_survives_shell_metacharacters -q
1 passed in 1.19s
$ python3 -m pytest tests/ -k gh_body_not_heredoc -q
1 passed in 1.29s
```

derived: `python3 -m pytest test/ tests/ -q` (same worktree, full suite
rather than the four `-k` filters alone) — result: `16 failed, 626
passed, 3 xfailed`, matching the PR body's claimed counts exactly. To
confirm these 16 failures are genuinely pre-existing and not introduced
by this PR (the PR's own base, `167cc19a`, is far older than current
`main`), I fetched current `origin/main` tip (`dad6b21e`) into a second
isolated worktree and ran the identical full suite there: `16 failed, 642
passed, 3 xfailed` — the higher pass count reflects tests added to
`main` after the PR's fork point, but the set of 16 failing test names is
byte-identical between the PR branch and current `main` tip (both list
the same `test_convention_equivalence.py`,
`test_spawn_cross_family_skill_selection.py`,
`test_spawn_artifact_skill_pairing.py`,
`test_spawn_skill_judge_haiku_timeout_overlap.py`,
`tests/test_spawn_gate_wiring.py`, and
`test_local_dependency_env.py` failures). This PR introduces zero new
test failures relative to current `main`.

Re-derived the metacharacter-survival claim independently, two ways,
rather than trusting `tests/test_task_stdin_input_2976.py` (untracked on
this record's own branch, present only on PR #2987's branch, fetched and
read there this session)'s own assertion:

1. Direct call with a fabricated `io.StringIO` stdin containing `->`,
   double quotes, single quotes, backticks, `$(...)`, and embedded
   newlines: `spawn.resolve_task_text(None, True, stdin=fake_stdin)` —
   result byte-identical (`MATCH: True`) to the input.
2. Through a real OS pipe (`subprocess.run(..., input=body)`, not an
   in-process `StringIO`) with a body containing `->`, an embedded
   double quote, and a newline — `stdout` byte-identical to the piped
   input.

Code-level audit against the issue's must-not list (`spawn.py` diff on
the PR branch, read in full this session):

- **"do not retire or alter the positional `<task>` form"** —
  `resolve_task_text(positional_task, use_stdin, stdin=None)` returns
  `positional_task` unchanged when `use_stdin` is `False`; the call site
  (`task_text = resolve_task_text(a.role, a.task_stdin)`) is the same
  assignment point `task_text = a.role` occupied before this PR. checked:
  `spawn.py` diff hunk around line 2421, read this session. Confirmed
  end-to-end via CLI: `python3 spawn.py --skills adversarial-review "a
  plain positional task"` (no `--task-stdin`) still reaches the same
  `--issue`-required validation error as before this PR, with the
  positional string threaded through unchanged — no side effects (no
  worktree, no branch, no process) resulted from this probe, confirmed
  via `git worktree list` / `ps aux` immediately after.
- **"a conflicting double-supply must be refused rather than resolved by
  precedence"** — `resolve_task_text` calls `sys.exit(...)` (never
  returns) the moment `use_stdin` is `True` and `positional_task` is
  truthy, naming the positional value and `--task-stdin` in the message.
  Confirmed via direct call (`SystemExit` raised, message contains both
  `'positional body'` and `--task-stdin`) and via a real CLI invocation
  (`printf 'stdin body' | python3 spawn.py --skills adversarial-review
  --task-stdin "positional body" --issue 1`) — exits 1 with the same
  message, never proceeds to spawn anything.
- **"`heredoc-command-refusal-gate` must not be weakened or bypassed —
  fix the callers"** — the diff (`git diff main...HEAD --name-only`)
  touches only `spawn.py`, two new test files
  (`tests/test_task_stdin_input_2976.py`,
  `tests/test_gh_body_not_heredoc_2976.py` — both untracked on this
  record's own branch, present only on PR #2987's branch, fetched and
  read there this session), and two doc/deviation-log files;
  `on-the-record/hooks/heredoc-command-refusal-gate.sh` itself is
  untouched. checked: full changed-file list, this session. Separately
  verified the claim underlying the "no caller needs fixing" approach —
  `grep -rn '"--body"' --include="*.py" .` (excluding `test/`/`tests/`)
  shows the repo's only two production `gh --body` call sites
  (`gates/check_runner.py:508`, `relay.py:270`) already build the
  argument as a `subprocess.run([...])` argv list, never a shell string
  with `<<` — the shape `heredoc-command-refusal-gate.sh` refuses.
  `tests/test_gh_body_not_heredoc_2976.py` (untracked on this record's
  own branch, present only on PR #2987's branch) locks this in
  mechanically (scans `.py`/`.sh` sources, excluding `docs/`, `test/`,
  `tests/`, `runs/`, with an explicit allowlist for the two hook files
  that legitimately carry the refused shape in their own detection
  regex/comments) and passed when I re-ran it.
- **"do not introduce a path that writes the body to a temp file as its
  primary mechanism"** — `resolve_task_text`'s stdin branch is
  `return (stdin if stdin is not None else sys.stdin).read()` — a direct
  stream read, no `tempfile`/`NamedTemporaryFile`/file-write anywhere in
  the new code. checked: full text of the added function, `spawn.py`
  diff, read this session; confirmed no `tempfile` import was added
  (`git diff main...HEAD -- spawn.py` shows none).

Read the PR's own deviation log
(`docs/issue-2976/reports/api-design-tool-landscape+test-derivation-451375cb/deviation-log/20260901T040551750552-400a60b2ff4812ba.md`
— untracked on this record's own branch, present only on PR #2987's
branch, fetched and read there this session) documenting a reverted
approach: the builder initially patched `gates/check_runner.py`/
`relay.py` to use `--body-file -`, then reverted via `git checkout --`
after confirming (a) neither call site runs through the Bash-tool shell
string the gate inspects (both already used argv lists) and (b) the
change broke the `PrBodyTrailerWriteShapeTest` class in
`test/test_branch_skill_field.py` (that file exists and is tracked on
this record's own branch too; the deviation log's claim about which test
it broke was not independently re-run by me — I read the log's own
`derived:` citation of the failure and re-revert as evidence, not a
claim I reproduced myself). This account matches what I independently
found above (both call sites already argv-list form) — the revert was
the correct call, not a skipped obligation.

## Why

Per the loaded `adversarial-review` skill, this session's structural
independence from PR #2987's builder session (fresh context, no shared
reasoning trail, spawned separately per this repo's role-handoff
protocol) already satisfies the skill's core mechanism, so no further
nested evaluator session was spawned — the skill's mindset was applied
directly: re-deriving every acceptance number, the metacharacter claim,
and every must-not clause from a freshly fetched worktree instead of
reading the PR body's claimed output, and specifically re-testing the
metacharacter survival claim through a real OS pipe rather than only
trusting the shipped `io.StringIO`-based test.

## What did not work

None.

## Upstream basis

- `docs/issue-2976/reports/api-design-tool-landscape+test-derivation-451375cb.md` (untracked on this record's own branch — it lives only on PR #2987's branch, fetched and read in full there this session) — sha: bc0e7f2836650f1a33777bd73461865415c243c2
- `spawn.py`, `tests/test_task_stdin_input_2976.py`, `tests/test_gh_body_not_heredoc_2976.py` (all at `bc0e7f2836650f1a33777bd73461865415c243c2`; the test files are untracked on this record's own branch, present only on the PR branch, read and executed in full from the fetched PR branch this session) — sha: bc0e7f2836650f1a33777bd73461865415c243c2

## Open findings

None. Resolution path: not applicable — derived: see the `checked:`/
`derived:` citations under `## What was done` above (the four acceptance
re-runs, the independent metacharacter re-derivation, the four
must-not-clause audit entries, and the full-suite differential against
current `main` tip); nothing surfaced there is left open to route to a
resolution path.

## Next steps

None — loop_state is terminal.

acceptance: `python3 -m pytest tests/ -k task_from_stdin -q; python3 -m pytest tests/ -k task_input_conflict_refused -q; python3 -m pytest tests/ -k task_body_survives_shell_metacharacters -q; python3 -m pytest tests/ -k gh_body_not_heredoc -q` — result:
```
1 passed in 0.82s
1 passed in 0.81s
1 passed in 1.19s
1 passed in 1.29s
```

skill-verdict: adversarial-review — applied: invoked; this session's
structural independence from PR #2987's builder session already
satisfies the skill's core mechanism (fresh context, no shared reasoning
trail), so no further evaluator session was spawned — the skill's
procedure was applied directly as the adversarial mindset for this
verification: re-deriving every claim from a fresh worktree instead of
reading the PR's claimed output, re-testing the metacharacter claim
through a real OS pipe rather than trusting the shipped test alone, and
independently confirming the "16 pre-existing failures" claim against
current `main` tip rather than the PR's own (older) baseline.
other mounted skills: not triggered (work-in-english is guidance-only
per this session's directive stack, enforced by hook rather than invoked
via the Skill tool; this record was written in English throughout).
