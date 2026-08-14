Subject: issue-1097

# Current-state survey (execution-observation)

## Scope statement
canonical: `gh pr list --search "1097" --state all` (read this session)
Observed target: the implementation role's session on issue #1097, branch `issue-1097/implementation`, two merged PRs against `main`, in landing order.

canonical: same `gh pr list` output above (read this session)
- PR **#1103** ("issue-1097 phase-1: consult judgment-JSON parse fix (root-caused, code attached)"), MERGED 2026-08-12T07:50:52Z.
- PR **#1104** ("issue-1097 phase-2: apply consult verdict-parse fix, live smoke proof"), MERGED 2026-08-12T07:57:27Z — carries the phase-2 delivery and `Closes #1097`.

## Fresh-eyes ordering — what was read, in order

1. canonical: `gh pr view 1103 --json body,commits,files` and `gh pr diff 1103` (read this session)
   Diff: `spawn.py` (+38/-15, `consult_cmd()`'s prompt assembly), `gates/test_consult_verdict_parsing.py` (new, +145), `docs/issue-1097/proposals/consult-verdict-parse-fix.md` (new, +96), `docs/issue-1097/reports/implementation/survey.md` (new, +72), `docs/issue-1097/reports/implementation/deviation-log.md` (new, +6), `docs/reports/consult-log.md` (+2). One commit `a19456bf`.
2. canonical: `gh pr view 1104 --json body,commits,files` (read this session)
   Diff: `docs/issue-1097/reports/implementation.md` (new, +79), `docs/issue-1097/reports/implementation/hunt-consult-verdict-parse-fix.md` (new, +34), `docs/reports/consult-log.md` (+1). Three commits: `a19456bf` (already on branch from #1103), `9acd5924` (phase-2 record + live smoke proof), `80e707ce` (merge main).
3. Only after both diffs — canonical: `git show origin/main:docs/issue-1097/reports/implementation.md` (read this session)
   The implementation role's own record states `verdict: pass`, `loop_state: landed`, cites `gh pr view 1103` (MERGED) as upstream basis, and pastes a live `spawn.py consult requirements-engineering` smoke-run transcript claiming an `ok:` outcome traced to `docs/reports/consult-log.md`'s 2026-08-12T07:53:18Z entry. That prior session's own pasted regression-suite output (the record's own text, not re-run in this survey step):
   ```
   4/4 passed
   8 passed, 477 deselected
   ```
   canonical: same `git show origin/main:docs/issue-1097/reports/implementation.md` read directly above; this survey does not independently re-verify that historical 07:53:18Z run here — see item 5 below for this session's own live re-run instead.
4. canonical: `gh issue view 1097 --json comments` (read this session)
   Issue-level trail: a `Judgment opened`/`Verdict: escalate` comment pair after PR #1103 opened, a `[watch]` session-end comment noting PR #1103, then an issue comment whose entire body is the exact string `APPROVE issue-1097/implementation`, author `JiwonJung94`.
   canonical: `git show origin/main:docs/specs/approvers.md` (read this session)
   Lists `JiwonJung94` as an approver account.
   canonical: `gh pr view 1103 --json author` (read this session) — PR author `JiwonJung94` (co-authored by the `claude` bot account, not listed in approvers.md). Same account authored the PR and posted the APPROVE string — single-account mode applies, per contract v3 s19.
5. Live re-run this session, against the current branch's checked-out `main`-derived tree.
   canonical: `git merge-base --is-ancestor origin/main HEAD && echo ancestor: yes` (run this session) → `ancestor: yes`.
   canonical: `python3 gates/test_consult_verdict_parsing.py` (run this session, twice, deterministic both times — direct terminal output)
   ```
   ok - t_parses_captured_real_transcript
   ok - t_prompt_overrides_repo_mutating_core_directives
   Traceback (most recent call last):
     ...
     File "gates/test_consult_verdict_parsing.py", line 84, in t_retries_once_and_recovers_when_first_attempt_has_no_json
       assert len(calls) == 2, f"expected exactly one retry, got {len(calls)} attempts"
   AssertionError: expected exactly one retry, got 4 attempts
   ```
   canonical: isolated repro run this session (`python3 -c "..."` reusing the test's own mock shape, direct terminal output, printing each captured call's argv) — confirmed the 4 captured calls are, in order: two `claude -p ...` invocations (the actual subject: base prompt, then retry prompt — matching `consult_cmd()`'s 2-attempt loop), followed by `git -C <root> add docs/consult-log.md ...` and `git -C <root> commit -m ...`.
   canonical: `spawn.py:4624-4643` (`_commit_consult_trace()`, read this session) — this function calls `subprocess.run(["git", ..., "add", ...])` and `subprocess.run(["git", ..., "commit", ...])` from inside the same code path `consult_cmd()` drives; its docstring cites issue #1134 as the origin of this git-commit-the-trace behavior, not issue #1097.
   canonical: `git log --oneline -1 -- gates/test_consult_verdict_parsing.py` (run this session) → last touched by `a19456bf` (PR #1103, issue-1097 itself) — the test's `len(calls) == 2` assertion has not been updated since to account for `_commit_consult_trace()`'s later-added git calls, which is why it now fails deterministically on current `main`.

## Diff hunks actually touched (for the diff-scope rule)
canonical: `gh pr diff 1103` (read this session)
- `spawn.py`: `consult_cmd()`'s prompt-assembly block, the diff hunk header `@@ -4389,27 +4389,50 @@` (pre-fix line numbers), replacing a single `subprocess.run` call with the two-attempt `base_prompt`/`retry_prompt` loop.
- `gates/test_consult_verdict_parsing.py`: whole-file addition, all four `t_*` functions including `t_retries_once_and_recovers_when_first_attempt_has_no_json` (the one failing live today, per item 5 above).
- `docs/issue-1097/proposals/consult-verdict-parse-fix.md`, `docs/issue-1097/reports/implementation/survey.md`, `docs/issue-1097/reports/implementation/deviation-log.md`: whole-file additions.
- `spawn.py:4624-4643` (`_commit_consult_trace()`) is **not** in this diff's hunks — it is later, unrelated drift (issue #1134), context only per the diff-scope rule, not evidence against PR #1103/#1104's own changes; it is cited above only to explain why the PR's own attached test now fails live.

## Independence statement
This role did not author or edit the observed artifact (PRs #1103/#1104, their commits, or `docs/issue-1097/reports/implementation.md`/`implementation/survey.md`) this session, and made no edit under `gates/`, `spawn.py`, `tests/`, or `docs/issue-1097/reports/implementation*` this session. The `python3 gates/test_consult_verdict_parsing.py` run and the isolated repro above executed the shipped, unmodified code as checked out on this branch — no source edit preceded or accompanied either run.
