# Issue #1134 — current-state survey

## Write surface

- `spawn.py::_append_consult_trace()` (spawn.py:4466-4476) — appends one
  line to `_consult_trace_path(issue)` (spawn.py:4457-4463), which
  resolves to `docs/issue-<n>/reports/consult-log.md` when `issue` is
  given, else `docs/reports/consult-log.md`. Called from `consult_cmd()`'s
  `finally` block (spawn.py:4604) — always, success or failure.
- `spawn.py::_persist_consult_raw_output()` (spawn.py:4440-4454) — on
  parse failure only, writes a side file under
  `docs/issue-<n>/reports/consult-raw-failures/<ts>-<attempt>.txt` (or
  the no-issue equivalent under `docs/reports/`). Both paths are inside
  the tracked tree — neither is gitignored.
- Both writers just `Path.write_text`/append; neither stages nor commits.
  `consult_cmd()` (spawn.py:4519-4604) has no git call anywhere in its
  body.

## Reported symptom

canonical: gh issue view 1134 (issue body, 2026-08-13 observed-state
paragraph)

On main at 930d415 the issue body reports two consult failures left
`docs/reports/consult-log.md` dirty, which fails
`t_rulebook_version_is_recorded` in tests/test_gates.py (function at
tests/test_gates.py:95) — that gate asserts `"커밋안됨" not in v`
(tests/test_gates.py:100), i.e. it fails specifically because the repo
is dirty, not because of anything the trace content says.

## Distinction from #1110

canonical: git log --oneline (commit 6af24fe, "issue-1110: gitignore
.orchestrate-monitor-alive/ marker dir")

#1110 gitignored `.orchestrate-monitor-alive/` — a *generated,
disposable* runtime marker with no record value, so hiding it from git
was correct there. Consult traces are the opposite: `_append_consult_trace()`'s
own docstring (spawn.py:4468-4471) calls "no traceless consults" an
operator invariant (issue #699), and northpole req#2
(docs/specs/northpole.md §2) requires every deliverable to be
"documented in the repo" as a durable record — so gitignoring the trace
file would fix the dirty-checkout symptom while deleting the record
req#2 requires. #1110's approach does not transfer to this file.

## Existing auto-commit precedent in this codebase

canonical: spawn.py:1367-1387 (approve-scope subcommand body, read this
session)

`spawn.py`'s `approve-scope` subcommand already solves the identical
shape of problem: it writes to a tracked record file then immediately
`git add` + `git commit -m` with a fixed message (`f"{subject}:
scope-approved (approved by {login} via spawn.py approve-scope)"`), and
on `CalledProcessError` it reverts the write (`record_path.write_text(text,
...)`, spawn.py:1381) before exiting — so a failed commit never leaves a
state where the write happened but the git history disagrees with it.
This is the direct precedent for "auto-commit with a fixed message
shape" named as requirement 1's first option.

## Trailer-gate constraint

canonical: this session's SessionStart interaction-protocol directive
(role-handoff contract v3 s13)

It states that a commit staging any `docs/issue-<n>/**` work must carry a
`Subject: issue-<n>` trailer, enforced mechanically at commit time. Since
`docs/issue-<n>/reports/consult-log.md` and
`docs/issue-<n>/reports/consult-raw-failures/` sit under `docs/issue-<n>/`,
an auto-commit that stages them while `issue` is set must carry that
trailer or the commit-time hook rejects it. The `issue is None` path
(`docs/reports/consult-log.md`) carries no issue number and does not
fall under that trailer requirement.

## #1123 interaction (issue's stated sequencing constraint)

canonical: git log --oneline (commit 7de5c9f, merge of PR #1136); gh pr
view 1136 (summary body)

#1123 phase-2 (PR #1136) landed on main and already edited
`consult_cmd()`'s failure-persistence path (`_persist_consult_raw_output()`,
spawn.py:4440, and its call site at spawn.py:4586). Requirement 3
("sequence AFTER #1123's PR lands") reads as satisfied — the consult
region of spawn.py is free, matching the issue text's own note that
#1141 also landed (commit a3b1e5c, unrelated `CLAUDE_PLUGIN_ROOT_CORE`
injection at spawn.py:4485-4496). No open PR currently touches this
region — searched via `git log --oneline --all | grep -i 1123`.

## Test surface

canonical: tests/test_gates.py:95 (function body, read this session)

`t_rulebook_version_is_recorded` is the gate the issue names as
currently failing. No existing test drives `consult_cmd()` end-to-end and
asserts an empty `git status --porcelain` afterward — this is new
coverage the acceptance criteria call for. gates/test_consult_json_parse.py,
gates/test_consult_verdict_parsing.py, and
gates/test_consult_gate_lib_env.py exercise parsing/env assembly, not the
trace-write/commit path.
