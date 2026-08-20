# issue-1742 execution-observation — current-state survey

## Scope statement

canonical: `gh issue view 1742` (read this session, full body + Acceptance section). Subject: issue #1742 (`spawn.py: additive --skills mount from skill-repository`), state `CLOSED` per that output.

canonical: `gh issue view 1742 --comments` (read this session, full thread). Observed role: implementation, session `issue-1742/implementation`. The thread's last two `[watch]` lines name the observed artifacts: PR #1743 (phase-1 proposal) and PR #1744 (phase-2 delivery).

canonical: `gh pr view 1743 --json number,mergedAt` and `gh pr view 1744 --json number,mergedAt,mergeCommit` (both read this session). PR #1743 merged `2026-08-20T23:12:03Z`; PR #1744 merged `2026-08-20T23:23:39Z`, merge commit `df7046f77bf3403342f6ed432e3478b4ab083c6e`.

## Fresh-eyes ordering

Read this session, in this order, before reading the observed role's own record narrative: `gh issue view 1742` (issue text + Acceptance), `gh issue view 1742 --comments` (full thread), `gh pr view 1744 --json number,title,body,mergedAt,mergeCommit,commits,files,url`, then `git show 3f77c1227331b5e1d4fdd9eb866ba2d695bec71d -- spawn.py` (full diff) and `test/test_spawn_skills_mount.py` in full. The observed role's own record file, `docs/issue-1742/reports/implementation.md` (part of PR #1744's diff), was read last, after all of the above.

## Research (discovery-over-guessing)

canonical: `gh issue view 1742 --comments` (read this session) — the thread's `[watch]` lines name both observed PR URLs directly (`.../pull/1743`, `.../pull/1744`), so PR numbers were read from the thread, not assumed from the issue title.

canonical: `git show 3f77c1227331b5e1d4fdd9eb866ba2d695bec71d --stat` and `git show df7046f77bf3403342f6ed432e3478b4ab083c6e --stat` (both read this session via `git show`, not summarized secondhand) — the code+test commit and the squash-merge commit on `main` respectively.

canonical: `gh pr view 1744 --json files` (read this session) lists `docs/issue-1742/reports/implementation.md` as an ADDED path — the observed role's own record file, read this session as part of PR #1744's diff.

## Current-state facts (verifiable, not evaluative — no verdict language)

canonical: `gh issue view 1742` (read this session) — the Acceptance section names exactly three checks, all `provenance: executed-live`, all pointing at `test/test_spawn_skills_mount.py`: (1) argv/env/workspace-layout for both no-flag and `--skills` cases, byte-identical no-flag diff against "the pre-change fixture"; (2) unknown-name case, non-zero exit, no workspace/branch creation; (3) record-fields case (skill list + skill-repository SHA in roster entry + co-injected directive).

canonical: `git show 3f77c1227331b5e1d4fdd9eb866ba2d695bec71d -- test/test_spawn_skills_mount.py` (read this session, new 226-line file). derived:
```
$ grep -c '^class ' test/test_spawn_skills_mount.py
5
$ grep -n 'def test_' test/test_spawn_skills_mount.py | wc -l
11
```

canonical: `docs/issue-1742/reports/implementation/survey.md` line 85-87 (the observed role's own phase-1 survey, read this session as part of PR #1743's diff). It states no stored "argv+env fixture" file exists on disk, backed by `derived: find test -iname '*argv*fixture*' -o -iname '*spawn*fixture*'` (no output). `docs/issue-1742/proposals/skills-mount.md` line 130-133 (read this session, same PR) restates the same substitution — call the assembly path twice, with and without the new params, and diff the two in-session results, rather than diffing against a pre-change fixture file — as a build commitment.

canonical: `git show 3f77c1227331b5e1d4fdd9eb866ba2d695bec71d -- spawn.py` (read this session, hunk inside `_spawn_one()`). `_spawn_one()` calls `resolved_skill_dirs(skills, _skill_repo_root())` before the `if issue is not None:` workspace/branch-creation block; `resolved_skill_dirs()` calls `sys.exit(...)` on an unknown name.

canonical: `git show 3f77c1227331b5e1d4fdd9eb866ba2d695bec71d -- spawn.py` (read this session, four hunks). The roster-entry and task-string fields for `--skills` (`skills`, `skills_sha` keys; the "마운트된 스킬..." task-string suffix) are added conditionally (`if skill_dirs`) in two places inside `_spawn_one()`, and `spawn_cmd()`'s env dict gains `MUSTER_SKILLS`/`MUSTER_SKILL_REPO_SHA` under the same `if skill_dirs:` guard.

canonical: `git show 3f77c1227331b5e1d4fdd9eb866ba2d695bec71d -- test/test_spawn_skills_mount.py` (read this session, lines ~178-215, class `RecordFieldsCarrySkillsAndShaTest`). Its two "record-fields" test methods construct local dict/string literals reproducing the same conditional shape described above, rather than calling `spawn._spawn_one()` or `spawn.roster_register()` directly and inspecting the real result. This is a plain textual fact about the test file, not yet a verdict — evaluated in phase 2.

canonical: `gh issue view 1742 --comments` (read this session) and `docs/specs/approvers.md` (read this session). A comment by `JiwonJung94` (listed in `docs/specs/approvers.md`) with body exactly `APPROVE issue-1742/implementation` appears in the thread, posted before the `[watch]` line reporting PR #1744 opened. PR #1743's author and this approving commenter are the same account (`JiwonJung94`).

canonical: this session's own live run, `python3 -m pytest -q test/test_spawn_skills_mount.py`, executed this turn — output `11 passed in 0.86s`. mode: command. This matches the pass count and shape the observed role's own record claims in `docs/issue-1742/reports/implementation.md`'s "## Test run" section (read this session).

## Diff-scope note

All file:line citations above that name `spawn.py` or `test/test_spawn_skills_mount.py` fall inside the hunks `git show 3f77c1227331b5e1d4fdd9eb866ba2d695bec71d` actually touched: `spawn.py`'s changed hunks are the named functions/call-sites above; `test/test_spawn_skills_mount.py` is an entirely new file in that same commit, so every line in it sits inside a changed hunk.
