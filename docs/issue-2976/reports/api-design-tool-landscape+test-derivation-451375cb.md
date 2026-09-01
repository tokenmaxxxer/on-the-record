---
issue: 2976
role: api-design-tool-landscape+test-derivation-451375cb
author: api-design-tool-landscape+test-derivation-451375cb
skills: api-design-tool-landscape (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: spawn.py
    sha: same-commit
  - path: tests/test_task_stdin_input_2976.py
    sha: same-commit
  - path: tests/test_gh_body_not_heredoc_2976.py
    sha: same-commit
---

# issue-2976 — api-design-tool-landscape+test-derivation-451375cb record

## What was done

Added `spawn.resolve_task_text(positional_task, use_stdin, stdin=None)` in
`spawn.py` and a new `--task-stdin` flag, wired into the `--skills` spawn
branch (the sole spawn form since #2572). Behavior:

- Default (no `--task-stdin`): identical to before — the positional
  `<task>` argument is the task body, byte-for-byte unchanged.
- `--task-stdin` with no positional task: the task body is read from
  stdin (`sys.stdin.read()` by default, injectable for tests) instead of
  the CLI argument, so a long body with `->`, quotes, or embedded
  newlines never has to survive shell quoting.
- Both a positional task and `--task-stdin` supplied together: refused
  via `sys.exit()`, naming both the positional value and `--task-stdin`
  in the message — never silently resolved by precedence.
- Neither supplied: falls through to the pre-existing
  `if not task_text: sys.exit('usage: ...')` check in `main()`, now with
  the stdin alternative mentioned in the usage text.

Also added `tests/test_gh_body_not_heredoc_2976.py`, a regression-guard
test for the acceptance criterion's other half (callers that pass a long
body to `gh` must use a file/stdin path, not a heredoc, so
`on-the-record/hooks/heredoc-command-refusal-gate.sh` has nothing to
refuse). It scans this repo's own `.py`/`.sh` source (excluding `docs/`,
`test/`, `tests/`, and the gitignored `runs/` mounted-plugin checkout) for
the `--body`/`--body-file` + `$(cat <<...)` shape the gate refuses, with
an explicit allowlist for the two hook files
(`on-the-record/hooks/pr-preflight.sh`,
`on-the-record/hooks/gh-write-allow-gate.sh`) that legitimately carry that
shape in their own detection regex/comments.

canonical: `grep -rn '"--body"' --include="*.py" .` (excluding
`/test/`, `/tests/`) — only two production call sites in this repo build
a `gh --body ...` argument: `post_comment()` in `gates/check_runner.py`
and the PR-create call inside `ensure_pushed()` in `relay.py`. Both
already use `subprocess.run(["gh", ...])` argv-list form, never a shell
string with `<<` — confirmed no production caller in this repo
constructs a heredoc-shaped `gh` body today. The new test locks that
clean state in mechanically and will fail the moment a future caller
reintroduces the pattern.

## Why

`resolve_task_text()` is a small pure function (not inlined in `main()`)
so the four acceptance behaviors — stdin-read, conflict-refusal,
byte-for-byte survival, and the unchanged positional default — are each
directly unit-testable via `spawn.resolve_task_text(...)` with an
injected `io.StringIO`, without invoking the full `_spawn_one()` session-
launch machinery (workspace/branch/roster side effects) that a CLI-level
test would otherwise have to mock out.

Reads a stream rather than writing the body to a temp file first, per the
issue's explicit must-not (temp-file creation is exactly the disk-full
failure mode issue #2962 documents) — `sys.stdin.read()` needs no
filesystem write at all.

The double-supply case is refused, not resolved by precedence (positional
silently winning over stdin, or vice versa) — matching the issue's
explicit must-not and `test-derivation`'s decision-table framing: this is
two independent booleans (positional present, `--task-stdin` set)
selecting an outcome, and "refuse" is the correct action for the
positional-AND-stdin column, not a silent pick.

`--body-file -`/stdin was considered as a live fix for the two identified
production `gh --body` callers, for symmetry with the spawn-side fix,
implemented, then reverted (see `## What did not work`) — neither caller
ever goes through the Bash tool / shell heredoc that
`heredoc-command-refusal-gate.sh` inspects (both use `subprocess.run`
argv lists, see the `canonical:` grep above), so the change had no
bearing on the gate and only cost an existing test its `--body` argv
assumption for no acceptance-criterion benefit. The regression-guard test
operationalizes the acceptance criterion directly against what actually
triggers the gate (a heredoc-shaped shell string), which is a better
match for "so heredoc-command-refusal-gate has nothing to refuse" than an
unrelated CLI-shape change to two callers that were never subject to that
gate.

canonical: `on-the-record/hooks/heredoc-command-refusal-gate.sh` (read in
full this session) — the gate's `_GH_WRITE_RE`/`_COMMIT_RE` matching is
applied only to `tool_input.command` of a `Bash` tool call containing
`<<`; a Python `subprocess.run([...])` argv-list call is never a Bash
tool invocation and is structurally outside what this gate inspects.

`test-derivation` skill applied (invoked via Skill tool this session):
routed the four acceptance criteria — task-from-stdin / conflict /
positional-default is one decision table on two booleans (positional
present x `--task-stdin` set, 4 feasible columns); the metacharacter-
survival criterion is EP/BVA on stdin body content (plain vs.
shell-metacharacter vs. empty-boundary partitions); the heredoc-absence
criterion is a single GWT regression-guard scenario (Low classification —
a structural invariant over the repo's own source, no per-input
variation to partition). All four decision-table columns and all three
EP/BVA partitions are exercised: tests/test_task_stdin_input_2976.py has
8 tests derived: `grep -c "def test_" tests/test_task_stdin_input_2976.py`
(see the acceptance run below for the passing result).

## What did not work

- Wrote `--body-file -`/stdin changes to `gates/check_runner.py`'s
  `post_comment()` and `relay.py`'s `ensure_pushed()` PR-create call
  (mirroring the spawn.py stdin fix), then reverted both via `git
  checkout --`.

  derived: reapplied the same edit a second time in isolation and ran
  `python3 -m pytest test/test_branch_skill_field.py::PrBodyTrailerWriteShapeTest -q`
  to confirm the exact break before writing this claim:
  ```
  FAILED test/test_branch_skill_field.py::PrBodyTrailerWriteShapeTest::test_ensure_pushed_body_carries_role_trailer
  AssertionError: 'pr-create-failed' != 'pr-opened'
  : {'status': 'pr-create-failed', 'reason': "...ValueError: '--body' is not in list"}
  1 failed in 1.02s
  ```
  What broke it: `PrBodyTrailerWriteShapeTest`'s fake `gh` shim reads
  `argv[argv.index("--body") + 1]` to capture the PR body for assertion;
  once `--body` is replaced with `--body-file -`, that lookup raises
  `ValueError`. Neither call site ever runs through a Bash-tool shell
  string in the first place (see the `canonical:` grep in `## What was
  done`), so `heredoc-command-refusal-gate.sh` was never able to see or
  refuse either call — the change addressed a caller shape the gate
  cannot reach. Reverted with `git checkout -- relay.py
  gates/check_runner.py` and re-ran the same test to confirm it passed
  again clean before proceeding.

## Upstream basis

- `spawn.py`: `--skills`/`--task-stdin` argument wiring and
  `resolve_task_text()`. sha: same-commit.
- `tests/test_task_stdin_input_2976.py`,
  `tests/test_gh_body_not_heredoc_2976.py`: new acceptance tests. sha:
  same-commit.
- `gates/check_runner.py`, `relay.py` (read, unchanged in this commit):
  basis for scoping the `gh_body_not_heredoc` fix to a regression-guard
  test rather than a caller-shape change — see `canonical:` tags above.
- `on-the-record/hooks/heredoc-command-refusal-gate.sh` (read, unchanged):
  basis for the `gh_body_not_heredoc` test's detection regex and
  allowlist — see `canonical:` tag in `## Why`.

## Open findings

None.

## Next steps

None — `loop_state: landed`.

acceptance: `python3 -m pytest tests/ -k task_from_stdin -q` — result:
```
1 passed in 0.84s
```

acceptance: `python3 -m pytest tests/ -k task_input_conflict_refused -q` — result:
```
1 passed in 0.83s
```

acceptance: `python3 -m pytest tests/ -k task_body_survives_shell_metacharacters -q` — result:
```
1 passed in 0.84s
```

acceptance: `python3 -m pytest tests/ -k gh_body_not_heredoc -q` — result:
```
1 passed in 1.22s
```

acceptance: `python3 -m pytest test/ tests/ -q` (full-suite regression check) — result:
```
16 failed, 626 passed, 3 xfailed in 32.02s
```
All 16 failures are pre-existing, not introduced by this change —
derived: `git worktree add /tmp/otr-2976-baseline 167cc19a && cd
/tmp/otr-2976-baseline && python3 -m pytest test/ tests/ -q` (base commit
before this session's changes) produced the identical 16 failing test
IDs (617 passed there instead of 626, since the base commit predates this
session's two new test files — no other difference), then `git worktree
remove /tmp/otr-2976-baseline --force` to clean up.

skill-verdict: test-derivation — applied: invoked; routed the four
acceptance criteria to decision-table / EP-BVA / GWT techniques and used
the resulting gap check (missing 4th decision-table column, missing
empty-body boundary) to add two test cases before landing (see `## Why`,
`tests/test_task_stdin_input_2976.py`).
skill-verdict: api-design-tool-landscape — not-applicable: this issue
changes a CLI argument-parsing interface (`spawn.py`'s argparse flags),
not an HTTP/service API surface, payload schema, or cross-service
contract that the skill's mock-server/schema-validator/SDK/contract-test
tooling targets.
