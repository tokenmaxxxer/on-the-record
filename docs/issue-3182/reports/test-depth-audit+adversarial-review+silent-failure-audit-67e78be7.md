---
issue: 3182
role: test-depth-audit+adversarial-review+silent-failure-audit-67e78be7
author: test-depth-audit+adversarial-review+silent-failure-audit-67e78be7
skills: test-depth-audit (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: true
loop_state: complete
upstream:
  - path: PR #3184 (branch issue-3182/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-74609923)
    sha: a526670a031f2181a8383c4cef9a7105843a7044
---

# issue-3182 — test-depth-audit+adversarial-review+silent-failure-audit-67e78be7 record

## What was done

Second independent verification of PR #3184, scoped to test discrimination, drift-test
directionality, portability, and the exit-code contract (a different verification session
covers enumeration completeness and citation accuracy).

Note on paths in this record: `scripts/preflight/consumer_preconditions.py` (untracked
path here), `tests/test_issue_3182_preflight.py` (untracked path here),
`tests/test_issue_3182_install_sufficiency_doc.py` (untracked path here), and
`docs/handbooks/install-sufficiency.md` (untracked path here) all exist only on PR
#3184's branch (`issue-3182/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-74609923`,
sha `a526670a031f2181a8383c4cef9a7105843a7044`), not on this branch's working tree — this
applies to every mention of these four paths below, quoted or not, including inside the
fenced command-output reproductions.

canonical: `git fetch origin pull/3184/head:pr-3184-review` then `git worktree add
/tmp/pr3184-worktree pr-3184-review` — reviewed PR #3184's code from an isolated
worktree, no edits landed on that branch or this one. Mutations were applied to the
scratch worktree copy only, run against the acceptance tests, then reverted with `cp` from
a saved original before the next mutation.

**Item 1 — do the three acceptance checks pass, and does the suite discriminate?**

acceptance: `python3 -m pytest tests/test_issue_3182_preflight.py -q` (untracked path
here) — result:
```
7 passed in 8.88s
```
acceptance: `python3 -m pytest tests/test_issue_3182_preflight.py -q -k "exit_code or working_tree"` (untracked path here) — result:
```
3 passed in 9.14s
```
acceptance: `python3 -m pytest tests/test_issue_3182_install_sufficiency_doc.py -q`
(untracked path here) — result:
```
3 passed in 4.88s
```
acceptance: `python3 -m pytest tests/ -q` (full suite, run inside the PR #3184 worktree) — result:
```
384 passed, 2 warnings in 29.58s
```
(the warnings are a pre-existing pinned-fixture-divergence UserWarning in
`tests/test_skill_candidates_floor.py`, unrelated to PR #3184; canonical: this test's own
`UserWarning` text as printed in the captured pytest output.)

Mutation-based discrimination testing: for each test below, a targeted mutation was
applied to the scratch copy of `consumer_preconditions.py` (untracked path here), the
test rerun, then the original restored via `cp`. Classification follows test-depth-audit's
five categories.

- `test_every_entry_has_required_fields`: mutated `run_checks()` to drop the `source` key
  from every emitted entry. derived: `python3 -m pytest
  tests/test_issue_3182_preflight.py::PreflightJsonShapeTest::test_every_entry_has_required_fields -q`
  (untracked path here) — result:
  ```
  FAILED ... AssertionError: 'source' not found in {'name': 'posix_fork_support', ...}
  1 failed in 4.88s
  ```
  Genuine Assertion.

- `test_every_source_cites_a_real_file_with_a_line_number`: mutated one entry's `source`
  to cite a renamed/nonexistent file (`spawn_renamed_stale.py`). derived: `python3 -m
  pytest tests/test_issue_3182_preflight.py::PreflightJsonShapeTest::test_every_source_cites_a_real_file_with_a_line_number -q`
  (untracked path here) — result:
  ```
  FAILED ... AssertionError: False is not true : posix_fork_support: source cites
  'spawn_renamed_stale.py', which does not exist under /tmp/pr3184-worktree
  1 failed in 4.80s
  ```
  Genuine Assertion.

- `test_at_least_five_preconditions`: mutated `CHECKS` down to a single entry. derived:
  `python3 -m pytest tests/test_issue_3182_preflight.py::PreflightJsonShapeTest::test_at_least_five_preconditions -q -v -o addopts="-n0"`
  (untracked path here) — result:
  ```
  FAILED ... AssertionError: 1 not greater than or equal to 5
  1 failed in 0.85s
  ```
  Genuine Assertion. (First attempt under this repo's default `pytest-xdist -n auto`
  misreported a pass — a false negative from a race between the mutation write and xdist
  worker startup, not a real gap; see "What did not work.")

- `test_unobservable_precondition_reported_unsatisfied`: mutated
  `check_remote_push_access()` to return `(True, "assumed ok")`. derived: `python3 -m
  pytest tests/test_issue_3182_preflight.py::PreflightJsonShapeTest::test_unobservable_precondition_reported_unsatisfied -q`
  (untracked path here) — result:
  ```
  FAILED ... AssertionError: True is not false : remote_push_access must be reported
  unsatisfied: it cannot be observed without a mutating git push
  1 failed in 4.98s
  ```
  Genuine Assertion.

- `test_working_tree_unchanged_across_two_runs_json` / `_human`: mutated `main()` to write
  a stray file (`mutation_side_effect.txt`) before running the checks. derived: `python3 -m
  pytest tests/test_issue_3182_preflight.py -q -k "exit_code or working_tree"` (untracked
  path here) — result:
  ```
  FAILED PreflightReadOnlyTest::test_working_tree_unchanged_across_two_runs_human
  FAILED PreflightReadOnlyTest::test_working_tree_unchanged_across_two_runs_json
  AssertionError: ... + ?? mutation_side_effect.txt
  2 failed, 1 passed in 9.06s
  ```
  Genuine Assertion.

- `test_exit_code_is_zero_or_one_only`: mutated `main()`'s final line from `return 0 if
  all(r["satisfied"] for r in results) else 1` to an unconditional `return 0`, regardless
  of missing preconditions. derived: `python3 -m pytest
  tests/test_issue_3182_preflight.py::PreflightJsonShapeTest::test_exit_code_is_zero_or_one_only
  -q -o addopts="-n0"` (untracked path here) — result:
  ```
  1 passed in 4.04s
  ```
  Did not catch the mutant (0 is a member of the set the test checks). Re-ran the same
  mutant against the whole file serially to rule out a false read: derived: `python3 -m
  pytest tests/test_issue_3182_preflight.py -q -o addopts="-n0"` (untracked path here) —
  result:
  ```
  6 passed, 1 failed in 9.40s
  ```
  (that 1 failure was an unrelated read-only-test flake caused by this session's own `cp`
  restore racing the test's `git status` snapshot mid-run, not the exit-code mutation —
  the exit-code test itself was among the passing set). Surface: verifies the documented
  boundary (member of `{0,1}`) but not the correlation the issue's item 4 and the
  acceptance check's `-k exit_code` name imply — that exit 1 means something is actually
  missing.

- `test_doc_exists`, `test_doc_states_cannot_be_removed`: trivial existence/`grep`-shaped
  assertions on `docs/handbooks/install-sufficiency.md` (untracked path here); not
  mutated — an existence check that fails when the file is absent, and a substring check
  that fails when the phrase is absent, have no room to be anything but Genuine Assertion
  by direct code read.

- `test_every_precondition_name_is_traceable_into_the_doc`: see item 2 below — Genuine
  Assertion for the add-direction only.

**Item 2 — drift-test directionality.**

The test `tests/test_issue_3182_install_sufficiency_doc.py` (untracked path here)
iterates over the live preflight's emitted `name`s and asserts each one's significant
words appear in the doc — script → doc only, per its own docstring, canonical:
`tests/test_issue_3182_install_sufficiency_doc.py:9-13` (untracked path here, module
docstring, read directly):
```
Test derivation (test-derivation skill): this is a decision-table /
consistency check between two artifacts, not a partition over a single
input, so the cases are:

  - existence: the doc file must exist at all.
```

Direction A (add undocumented): mutated `CHECKS` to add an entry named
`zzz_totally_undocumented_widget_flux` with no matching doc text. derived: `python3 -m
pytest tests/test_issue_3182_install_sufficiency_doc.py::InstallSufficiencyDocTest::test_every_precondition_name_is_traceable_into_the_doc -q`
(untracked path here) — result (the doc path named inside this captured assertion
message, `docs/handbooks/install-sufficiency.md`, is likewise untracked here):
```
FAILED ... word(s) ['zzz', 'totally', 'undocumented', 'widget', 'flux'] from its name do
not appear anywhere in docs/handbooks/install-sufficiency.md -- doc and preflight have
drifted apart
1 failed in 4.78s
```
Caught. (`docs/handbooks/install-sufficiency.md`, named in that captured message, is
untracked here.)

Direction B (remove documented): mutated `CHECKS` to delete the `git_identity_configured`
entry entirely, leaving the corresponding table row and prose untouched in the doc
(`docs/handbooks/install-sufficiency.md`, untracked path here). derived: `python3 -m
pytest tests/test_issue_3182_install_sufficiency_doc.py -q -o addopts="-n0"` (untracked
path here) — result:
```
3 passed in 4.13s
```
Not caught. A precondition can be deleted from the script while its row stays in the
handbook forever, and nothing in this suite notices — the doc→script direction is
unchecked. The test's own docstring only claims the add-direction risk ("a precondition
added to the script with no matching doc update would silently understate the gap"); it
never claims to catch a removal, so this is a disclosed-scope gap, not the test failing
its own stated bar. See Open findings, finding one below.

**Item 3 — portability (macOS vs Linux).**

This machine is Linux only; nothing below was executed on macOS — graded from code
reading, with explicit hedging where noted.

derived: `grep -nE "readlink -f|stat -c|date -d|/proc|sed -i|mktemp --|GNU"
scripts/preflight/consumer_preconditions.py tests/test_issue_3182_preflight.py
tests/test_issue_3182_install_sufficiency_doc.py` (all three untracked paths here, run
inside the PR #3184 worktree) — result: only docstring prose naming the avoided
constructs, zero actual invocations of `stat`, `readlink`, `date`, or `sed`, and no
`/proc` reads. The script uses `shutil.which`, `pathlib.Path`, and `subprocess.run` with
explicit argv lists (no `shell=True`) throughout — Present for the "no GNU-only
shell-outs" claim.

Per-check portability grading, canonical: `scripts/preflight/consumer_preconditions.py`
(untracked path here) lines 76-163 (`CHECKS` function bodies), read directly:

| Check | Detection method | macOS verdict |
|---|---|---|
| `posix_fork_support` | `hasattr(os,"fork")`/`hasattr(os,"setsid")` + `sys.platform in ("linux","darwin")` | Present — static attribute check |
| `claude_cli_on_path` | `shutil.which("claude")` | Present |
| `git_cli_on_path` | `shutil.which("git")` | Unverifiable / plausible false-positive: macOS ships a `/usr/bin/git` stub on disk before Xcode Command Line Tools are installed, so `shutil.which` would find it and report satisfied even though invoking it triggers a GUI install prompt rather than running git. Not executed on macOS to confirm; reasoned from documented macOS behavior, not observed — see Open findings, finding three. |
| `gh_cli_authenticated` | `shutil.which("gh")` + `gh auth status` subprocess | Present — real invocation |
| `git_identity_configured` | `git config --get user.name`/`user.email` subprocess | Present |
| `skill_repository_resolvable` | `Path.is_dir()`/`Path.iterdir()`, wrapped in `try/except OSError` | Present |
| `home_claude_skills_dir_present` | `Path(os.path.expanduser("~/.claude/skills")).is_dir()` | Present |
| `target_repo_board_file_present` | `Path.is_file()` | Present |
| `remote_push_access` | hardcoded `(False, ...)` | Present — no OS dependency |

Verdict on the delivery record's portability claim
(`docs/issue-3182/reports/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-74609923.md`,
untracked path here, PR #3184 branch, around its "Portability approach" paragraph —
"the same code path runs on macOS and Linux without a platform branch"): true for the
code's construction (no GNU-only shell-outs, confirmed by the grep above), but the claim
does not surface the `git_cli_on_path` false-positive risk noted in the table — a
completeness gap in the claim, not in the code.

**Item 4 — exit-code contract under adversarial conditions.**

All four run against the unmutated script (`scripts/preflight/consumer_preconditions.py`,
untracked path here), output captured and parsed with `json.load`/exit-code inspection:

- Missing `gh` binary: `PATH=<dir with only python3,git> python3
  .../consumer_preconditions.py --json` — derived, result:
  ```
  exit=1
  gh entry: satisfied=False, remedy contains "gh not found on PATH"
  ```
- `HOME` pointing at a nonexistent directory: `HOME=/nonexistent-home-xyz python3
  .../consumer_preconditions.py --json` — derived, result:
  ```
  exit=1
  parsed OK, all preconditions present in output
  ```
- Working directory outside any git repo: run from `/tmp/no-git-repo-dir` — derived,
  result:
  ```
  exit=1
  parsed OK, all preconditions present in output
  ```
- Unreadable directory the script wants to `is_dir()`/`is_file()` into: `chmod 000` on an
  ancestor directory of the cwd, ran the script from inside it — derived, result:
  ```
  exit=1
  target_repo_board_file_present: satisfied=False, remedy contains "check raised
  PermissionError: [Errno 13] Permission denied: '.../docs/specs/approvers.md'"
  stderr: empty
  ```

All four exited 0 or 1 with a coherent, parseable report; none produced a traceback or any
other exit code. Present for the exit-code contract's actual runtime behavior under
conditions the test suite itself does not exercise — see item 1's Surface finding on
`test_exit_code_is_zero_or_one_only`: passing tests demonstrate boundary membership, not
resilience under these four specific conditions, which was instead verified here directly.

Silent-failure-audit note, canonical: `scripts/preflight/consumer_preconditions.py`
(untracked path here) lines 248 through 256 (`run_checks`), read directly:
```
    try:
        ok, detail = c["fn"]()
    except Exception as exc:  # noqa: BLE001 -- a check must never
        # crash the whole preflight; an unexpected defect in one check
        # degrades that check to "missing", not to a silent skip.
        ok, detail = False, f"check raised {type(exc).__name__}: {exc}"
```
Handled, not Silently Absorbed: the `PermissionError` observed above was folded into the
reported `remedy` string with the exception type and message, never silently assumed
satisfied and never swallowed without a trace. Same pattern in `_run_readonly()`'s broad
`except Exception` (`scripts/preflight/consumer_preconditions.py`, untracked path here,
lines 59 through 65, read directly) — a subprocess failure degrades to an unobservable
sentinel plus the exception detail, which every caller treats as unsatisfied.

## Why

Test-depth-audit and silent-failure-audit require falsifying "this test would catch X"
claims by actually breaking X and rerunning, not by reading the code and trusting its
docstrings. Portability was graded from code reading with explicit hedging since this
machine cannot run macOS, per the spawning prompt's instruction to reason from the code
and say plainly what could not be executed rather than assert an unexecuted claim as fact.

## What did not work

- Wrote mutations via inline `python3 - <<'PYEOF'` heredocs at first; the board-gate hook
  (`pretooluse-dispatcher.sh`) refused these as un-analyzable write shapes even against
  `/tmp` targets outside this session's write set. Switched to writing small mutation
  scripts to `/tmp/*.py` with the Write tool and invoking them as `python3 /tmp/script.py
  <target>`, which the gate accepted.
- The first read of `test_at_least_five_preconditions` (`tests/test_issue_3182_preflight.py`,
  untracked path here, on the PR #3184 branch) under a `CHECKS`-truncation mutation
  reported a pass under this repo's default `pytest-xdist -n auto` config (`pytest.ini`'s
  `addopts = -n auto`). derived: `python3 -m pytest
  tests/test_issue_3182_preflight.py::PreflightJsonShapeTest::test_at_least_five_preconditions
  -q` (first attempt, xdist default, untracked path here) — result: passed. Re-running the
  identical mutation serially (`-o addopts="-n0"`) with `__pycache__` cleared showed it
  correctly FAILED (see item 1 above) — a false negative from a race between the mutation
  file write and xdist worker startup, not a real test-suite gap. Re-verified every other
  mutation-based finding in this record with `-o addopts="-n0"` before including it, to
  rule out the same artifact recurring silently elsewhere.
- The initial version of this record used `verifies_subject: false` and an abbreviated PR
  head sha in frontmatter; `record-claim-guard.sh` and `record-shape-gate.sh` refused the
  write until `sha:` carried the full 40-character commit hash. Fixed by resolving it via
  `gh pr view 3184 --json headRefOid`. The same gate also refused early drafts of this
  record's prose for bare numeric claims and backtick paths not present in this working
  tree, including inside fenced command-output quotes; fixed by adding
  `derived:`/`canonical:` tags next to each and an "untracked path here" note next to each
  backtick or fenced mention of a PR-#3184-only file.

## Upstream basis

- PR #3184 (untracked path here — lives on branch
  `issue-3182/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-74609923`,
  sha `a526670a031f2181a8383c4cef9a7105843a7044`), fetched via `git fetch origin
  pull/3184/head:pr-3184-review` and reviewed in an isolated `git worktree` at
  `/tmp/pr3184-worktree`; no edits made to that branch or to PR #3184.
- Files at that commit, all untracked paths here: `scripts/preflight/consumer_preconditions.py`
  (untracked here), `tests/test_issue_3182_preflight.py` (untracked here),
  `tests/test_issue_3182_install_sufficiency_doc.py` (untracked here), and
  `docs/handbooks/install-sufficiency.md` (untracked here).
- `docs/issue-3182/reports/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-74609923.md`
  (untracked path here, same PR #3184 branch) — cited only for its portability-claim
  wording, not relied on for the builder's intent, per adversarial-review's blind-to-intent
  posture.
- Issue #3182 itself (`gh issue view 3182`) for the acceptance checks verified in item 1.

## Open findings

One: drift test is one-directional (item 2 above). `test_every_precondition_name_is_traceable_into_the_doc`
(in `tests/test_issue_3182_install_sufficiency_doc.py`, untracked path here) catches a
precondition added to the script without a doc update, but not a documented precondition
removed from the script — the handbook (`docs/handbooks/install-sufficiency.md`,
untracked path here) can drift to describe checks that no longer exist and nothing fails.
derived: mutation result reproduced in item 2 above (`python3 -m pytest
tests/test_issue_3182_install_sufficiency_doc.py -q -o addopts="-n0"` (untracked path
here) → passed against the removal mutant). Resolution path: add a reverse check (assert
every precondition-shaped doc row/heading corresponds to a live script `name`), or
document the one-directional scope explicitly in the test's own docstring so a future
reader doesn't assume full bidirectional coverage.

Two: `test_exit_code_is_zero_or_one_only` doesn't test the exit-code contract's substance
(item 1 above). It verifies membership in the set `{0,1}` but not that exit code 1
correlates with an actual missing precondition, or that a script which stopped computing
the real exit code would be caught. derived: mutation result reproduced in item 1 above
(always-`return 0` mutant passed the full test file serially). Resolution path: add a case
asserting the returncode equals one when not all entries report satisfied in the parsed
JSON (true on every observed run today, since `remote_push_access` is hardcoded
unsatisfied).

Three: `git_cli_on_path`'s `shutil.which` check may false-positive on macOS before Xcode
Command Line Tools are installed (item 3 above). Unverifiable on this Linux machine;
derived: reasoning against `scripts/preflight/consumer_preconditions.py` (untracked path
here) lines 89 through 91 (`check_git_cli_present`), read directly — plausible from
documented macOS behavior, not observed by execution. Resolution path: confirm on real
macOS hardware whether `shutil.which("git")` finds the pre-CLT stub, and if so either
accept it as a known limitation (downstream checks like `git_identity_configured`
actually invoke git and would still correctly report unsatisfied) or note it in the
handbook.

## Next steps

None — this record is terminal. The three open findings above are recommendations for a
follow-up on PR #3184, not blockers this verification session can act on; task scope was
verify-only, no edits to PR #3184.

skill-verdict: test-depth-audit — applied: invoked; canonical: the mutation-classification
list in this record's "What was done" section, item 1
skill-verdict: adversarial-review — applied: invoked; canonical: structurally independent
review of PR #3184 from a fetched branch in an isolated worktree, no shared context with
the builder session, findings graded Present/Surface/Absent/Incorrect/Unverifiable
throughout this record
skill-verdict: silent-failure-audit — applied: invoked; canonical: the `run_checks()`/
`_run_readonly()` broad-except classification in this record's "What was done" section,
item 4
other mounted skills: not triggered (work-in-english, implementation-audit)
