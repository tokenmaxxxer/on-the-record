---
issue: 2313
role: implementation
loop_state: landed
upstream:
  - path: docs/issue-2313/reports/implementation.md
    sha: same-commit
code_under_review:
  - gates/check_runner.py
  - gates/test_check_runner.py
  - on-the-record/directive/merge-gates.md
type: fix
breaking: "none — classification of non-compound commands is byte-identical; compound commands were previously always misclassified/never-executed, so there is no prior correct behavior to break"
verdict: pass
---

# issue-2313 — implementation record

## What was done

canonical: this commit's diff to gates/check_runner.py, gates/test_check_runner.py, on-the-record/directive/merge-gates.md; derived: python3 gates/test_check_runner.py (full output in Evidence below)

Two independent fixes in `gates/check_runner.py`, both from the issue's
consumer report:

1. **Compound-check classification.** `parse_checks()` classified a
   `check:`/`gate:` backtick command by the whole string's first token.
   For `` `cd frontend && node scripts/check-hex-tokens.mjs` ``, the first
   token is `cd` — not in `INTERPRETERS`, no `/` in itself — so
   `looks_like_command` was `False`, and the fallback `_looks_like_path()`
   fired on the *whole* compound string (which contains `/` via
   `scripts/check-hex-tokens.mjs`), yielding `file-existence` with
   `path` set to the entire compound string — a path that can never
   exist. Added `_COMPOUND_SEP` (`&&|;`) and `_final_segment()`; every
   classification branch (`test`/interpreter check, bare-`.py`-through-
   pytest wrap, `file-existence` fallback, and the declared-
   `runtime-artifacts` touch check `_artifact_touched`) now classifies
   against the final segment instead of the full compound string. The
   `command`/`path` fields still carry the full original compound string
   so execution still `cd`s first.
2. **Compound-command execution.** Classifying correctly wasn't enough —
   `run_checks()` ran `test`/`artifact-smoke` commands via
   `subprocess.run(shlex.split(command), cwd=repo, ...)` with no shell,
   and `cd` is a shell builtin, not an executable — `shlex.split("cd
   frontend && node …")` never runs correctly without a shell. `cd`/`;`-
   containing commands now run via `subprocess.run(command, shell=True,
   cwd=repo, ...)`; non-compound commands are untouched (still
   `shlex.split` + argv-exec, no shell).
3. **`--repo` semantics.** Clarified in `gates/check_runner.py`'s module
   docstring and `main()`'s usage string, and in
   `on-the-record/directive/merge-gates.md`'s `ACCEPTANCE CHECK-RUNNER AT
   LANDING` bullet, that `--repo` is the checkout of the repo the
   PR/issue **being checked** belongs to (it's the `cwd` for every `gh`
   call check_runner makes) — for on-the-record's own landing that's
   `${CHECKOUT}`, but for target-repo (consumer) work it must be the
   target repo's checkout, never `${CHECKOUT}` (which reads the plugin
   repo's own same-numbered issue and fails with "Acceptance 절이
   없다").

A `warrant-hunter` run against the working-tree diff before landing
(agent transcript this turn) surfaced one real composition gap in the
first pass — canonical: warrant-hunter agent output this turn, reproduced
independently below:

```
$ python3 -c "
import sys; sys.path.insert(0, 'gates')
import check_runner
declared = ['dist/bundle.js']
print(check_runner.parse_checks('\n- check: \`cd frontend && node dist/bundle.js\`\n', declared))
"
[{'type': 'artifact-smoke', 'raw': '`cd frontend && node dist/bundle.js`', 'command': 'cd frontend && node dist/bundle.js', 'artifact': 'dist/bundle.js'}]
```

`_artifact_touched()` was still called with the *un-split* full command
while every other branch had moved to `classify_cmd` — so a compound,
declared-`runtime-artifacts` check (`cd frontend && node dist/bundle.js`)
would have silently downgraded from `artifact-smoke` to plain `test`,
losing its `artifact` field and flipping `check_run_artifact.py`'s
`_is_non_hermetic` flag (keyed on `type == "test"`). Fixed by passing
`classify_cmd` (final segment) to `_artifact_touched()` too, confirmed by
the live rerun above and pinned with
`t_compound_cd_command_with_declared_artifact_still_classifies_as_artifact_smoke`
in `gates/test_check_runner.py`.

## Why

The issue's Acceptance names `gates/test_check_runner.py` as the gate and
requires the empty-state case (a simple, non-compound command) to classify
unchanged. Splitting on `&&`/`;` and classifying by the final segment is
the narrowest fix that satisfies both: it's a pure no-op for any command
without those separators (`_final_segment()` returns the input unchanged
when there's nothing to split — see `t_simple_noncompound_command_classification_is_unchanged`),
and it fixes the exact reported shape without touching the surrounding
`#2278`/`#2231` classification logic (measurement-language judgment
downgrade, bare-path allowlist, etc.), which stays keyed off the same
final-segment string so its own guarantees carry over unchanged.

`requirement_met.py` already has a `_CD_PREFIX` regex for a related but
narrower purpose (stripping a `cd X &&` head for command-identity
comparison) — canonical: gates/requirement_met.py:88, read this session
— confirming `cd X && CMD` is a recognized shape in this codebase; its
regex only strips a single leading `cd`, not the general "classify by
final command of an arbitrary `&&`/`;` chain" the issue asks for, so it
wasn't reused directly.

Execution needed `shell=True` for the compound case specifically because
`cd` has no standalone executable — this doesn't widen the tool's trust
boundary: `run_checks` already execs arbitrary `check:`-declared commands
via argv (the whole point of a check-runner), so a compound command
running through a shell is the same trust boundary, not a new one.

## What did not work

None.

## Upstream basis

Issue #2313 (consumer report, 2026-08-25) — the `cd frontend && node
scripts/check-hex-tokens.mjs` misclassification and the `--repo`
ambiguity are both quoted directly from the issue body (`gh issue view
2313`, read this session). No other docs/issue-2313/ upstream artifacts
existed (build-now delivery per `CORE_BUILD_NOW=1`, no separate proposal
round).

## Open findings

None — the one warrant-hunter finding raised during this session (compound
+ declared-artifact interaction, see "What was done" above) was fixed and
pinned with a regression test before landing.

## Next steps

None — `loop_state: landed`.

## Evidence

`python3 gates/test_check_runner.py` — 28/28 derived: python3 gates/test_check_runner.py (includes five new tests for issue #2313: compound `&&`/`;` classify as `test`, compound `cd` command actually executes and reaches `pass` through a real shell, bare-`.py` final segment still wraps through pytest inside a compound command, a non-compound command's classification/command string is byte-identical to before, and a compound command with a declared runtime-artifact still classifies `artifact-smoke`):

```
$ python3 gates/test_check_runner.py
ok - t_all_judgment_checks_do_not_abort_run_checks_when_pre_filtered
ok - t_artifact_smoke_check_actually_runs_and_fails_on_a_broken_artifact
ok - t_artifact_smoke_check_passes_when_the_artifact_parses
ok - t_bare_artifact_path_without_measurement_language_stays_file_existence
ok - t_bare_conventional_filename_and_dotfile_still_classify_as_file_existence_and_fail
ok - t_bare_path_still_classifies_as_file_existence
ok - t_bare_py_gate_path_is_wrapped_to_run_through_pytest
ok - t_classification_is_byte_identical_without_a_declaration
ok - t_compound_cd_command_actually_runs_through_a_shell_and_passes
ok - t_compound_cd_command_classifies_as_test_not_file_existence
ok - t_compound_cd_command_with_declared_artifact_still_classifies_as_artifact_smoke
ok - t_compound_command_final_bare_py_segment_is_wrapped_through_pytest
ok - t_compound_semicolon_command_classifies_as_test_not_file_existence
ok - t_cross_family_bare_identifier_classifies_as_judgment_not_file_existence
ok - t_declared_artifact_command_classifies_as_artifact_smoke
ok - t_format_comment_lists_skipped_judgment_items_outside_the_pass_total
ok - t_format_comment_names_the_artifact_smoke_type
ok - t_format_no_checks_comment_reports_judgment_items_distinctly
ok - t_genuinely_missing_path_shaped_artifact_still_classifies_as_file_existence_and_fails
ok - t_measurement_language_prose_bullet_classifies_as_judgment_not_file_existence
ok - t_node_command_without_declaration_classifies_as_test_not_file_existence
ok - t_npx_deno_bun_are_on_the_interpreter_allowlist
ok - t_py_gate_path_with_explicit_interpreter_is_left_alone
ok - t_run_checks_records_a_failure_instead_of_crashing_on_unexecutable_command
ok - t_simple_noncompound_command_classification_is_unchanged
ok - t_source_level_command_stays_test_even_with_a_declaration
ok - t_unclassifiable_check_is_still_judgment_and_refused_by_the_runner
ok - t_work_in_english_skill_name_classifies_as_judgment_not_file_existence
28/28 passed
```

Full `gates/` suite regression check — derived: python3 -m pytest gates/ -q:

```
$ python3 -m pytest gates/ -q
970 passed, 8 xfailed in 6.29s
```

The consumer's exact compound check, re-run post-fix end-to-end
(classify → execute) — derived: the python3 command shown, run against a
stand-in `/tmp/repro/frontend/scripts/check-hex-tokens.mjs` (contained
`process.exit(0);`, since the consumer's real script was not available in
this checkout) — showing `test`-classification and `status: pass`:

```
$ python3 -c "
import sys; sys.path.insert(0, 'gates')
import check_runner as cr
from pathlib import Path
section = '\n- check: \`cd frontend && node scripts/check-hex-tokens.mjs\`\n'
checks = cr.parse_checks(section)
print('classified:', checks)
print('results:', cr.run_checks(Path('/tmp/repro'), checks))
"
classified: [{'type': 'test', 'raw': '`cd frontend && node scripts/check-hex-tokens.mjs`', 'command': 'cd frontend && node scripts/check-hex-tokens.mjs'}]
results: [{'check': '`cd frontend && node scripts/check-hex-tokens.mjs`', 'type': 'test', 'command': 'cd frontend && node scripts/check-hex-tokens.mjs', 'status': 'pass', 'output': ''}]
```

Pre-fix vs. post-fix classification of the same input, executed live
against `HEAD` (972997f44277ce5d5bc3446e6a156cbe07c4e22f, pre-fix) and this
working tree (post-fix) — derived: the two python3 invocations shown:

```
$ git show HEAD:gates/check_runner.py > /tmp/precheck/check_runner_pre.py
$ python3 -c "... cr_pre.parse_checks(section) ..."
PRE-FIX classify: [{'type': 'file-existence', 'raw': '`cd frontend && node scripts/check-hex-tokens.mjs`', 'path': 'cd frontend && node scripts/check-hex-tokens.mjs'}]
$ python3 -c "... check_runner.parse_checks(section) ..."
POST-FIX classify: [{'type': 'test', 'raw': '`cd frontend && node scripts/check-hex-tokens.mjs`', 'command': 'cd frontend && node scripts/check-hex-tokens.mjs'}]
```

The `--repo` case: pre-fix directive bullet (misleading — `--repo
${CHECKOUT}` with no target-repo warning) vs. post-fix (clarified) — derived: git show HEAD:on-the-record/directive/merge-gates.md vs. this working tree's copy, both read this session:

```
=== pre-fix (HEAD, 972997f4) ===
  step — `python3 gates/check_runner.py <pr> <issue> --repo ${CHECKOUT}` —
  so its PR comment exists for `gates/merge_gate.py`'s `evaluate()` to
  read. This is manual, not CI-wired: this repo carries no
  ...
=== post-fix (this working tree) ===
  step — `python3 gates/check_runner.py <pr> <issue> --repo <repo>` — so
  its PR comment exists for `gates/merge_gate.py`'s `evaluate()` to read.
  issue #2313: `--repo` is the checkout of the repo the PR/issue actually
  belongs to (`check_runner.py:381`'s `gh` calls use it as `cwd`) — when
  orchestrating on-the-record's own landing that repo is `${CHECKOUT}`,
  but for **target-repo** (consumer) work `--repo` must be that target
  repo's checkout, never `${CHECKOUT}` — passing `${CHECKOUT}` there
  fetches the plugin repo's own same-numbered issue instead and fails
  with "Acceptance 절이 없다". ...
```

## Deviations

None from the issue's Acceptance — derived: python3 gates/test_check_runner.py (full output in the Evidence section above). `gates/test_check_runner.py` is the gate named, extended (not replaced) with tests pinning both the reported bug and the warrant-hunter's compound+artifact-smoke finding.

skill-verdict: work-in-english — applied: invoked; loaded the skill and
followed its routing (English for code/comments/commits/this record's
body, Korean reserved for the final user-facing chat summary); matched
this repo's existing convention of Korean rationale comments next to code
(e.g. `_COMPOUND_SEP`'s comment in gates/check_runner.py) since the
skill's own guard says match surrounding style rather than force a
language switch mid-file.
other mounted skills: not triggered (implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint — no coupling/cohesion threshold, no GoF pattern decision, no data-structure/perf tradeoff, and no new multi-module structure was involved; this is a narrow classifier fix inside one existing function plus a docs clarification).
