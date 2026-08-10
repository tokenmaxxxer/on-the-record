---
code_under_review:
  - spawn.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #619 (phase 2)

## Summary of work

Translated the Korean body text of `spawn.py`'s four issue-comment
emitters (`_post_crash_comment`, `_post_stall_comment`,
`_post_session_end_comment`, `_post_stranded_push_comment`) to English
with stable field-label tokens (`trigger:`, `workspace:`, `log:`,
`branch:`, `reason:`, `detail:`), and translated
`_CRASH_COMMENT_MARKER`'s embedded Korean substring to English, per
`docs/issue-619/proposals/2026-08-10-korean-emitter-sweep.md`.

## Why

Issue #619: repo-bound output from the deployed surface (issue/PR
comments, committed records, parser-matched refusal texts) must be
English with stable machine-matchable tokens, per the project's
work-in-english policy — downstream parsers (remediation spawn
templates, #597's framing writer) are locale-fragile against Korean
field labels.

## Upstream basis

docs/issue-619/proposals/2026-08-10-korean-emitter-sweep.md

## What did not work

None.

## Test run

```
$ python3 -m pytest test_spawn.py -q
358 passed in 24.60s

$ python3 -m pytest -q
2 failed, 938 passed in 42.16s
```

The 2 failures (test names: `t_all_gates_modules_recorded` in
gates/test_boundary.py, `t_rulebook_version_is_recorded` in
test_gates.py) are pre-existing and unrelated to this change —
reproduced identically on a clean `main`-merge tree before this
change's edits. They assert on `rulebook_version()` reporting a
dirty/uncommitted working tree, a property of the ambient session
environment, not of the emitter translation.

## Classification of Korean strings found (repo-bound vs console-only)

Repo-bound (changed, now English):
- `spawn.py::_post_crash_comment` body + `_CRASH_COMMENT_MARKER`
- `spawn.py::_post_stall_comment` body
- `spawn.py::_post_session_end_comment` body
- `spawn.py::_post_stranded_push_comment` body

Console-only (left as Korean, out of scope per proposal):
- `spawn.py::_post_crash_comment`/`_post_session_end_comment` stderr
  failure prints (`[spawn] 이슈 #{issue} ... 게시 실패`)
- `spawn.py`'s `clean` subcommand summary output
- kill-signal/warning/hint prints throughout `spawn.py`
- `--help` text
- Docstrings (developer-facing, never emitted to a repo artifact)

## Doc-placement ladder

- [x] No new env var/config key/dependency/migration/setup step —
      nothing to add to a handbook.
- [x] No changed public signature or wire format beyond the comment
      body text itself (comment bodies are not a parsed wire format
      elsewhere in-repo, per survey) — no docs/issue-619/decisions/
      entry needed.
- [x] No benchmark/investigation numbers produced — no
      docs/issue-619/reports/ entry beyond this record.

## Open findings

None.

## Next steps

Run full test suite, commit, push, open PR carrying `Closes #619`.

## Resolution path

No open findings; none to resolve.
