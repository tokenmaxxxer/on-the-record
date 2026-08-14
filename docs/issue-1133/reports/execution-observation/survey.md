# Current-state survey: execution-observation of the implementation role on issue #1133

Scope: the `implementation` role's phase-1→phase-2 execution on issue
#1133 (watcher re-arm never updates the watchdog registry; watcher-dead
remediation text blocks foreground), branch `issue-1133/implementation`,
citing requirement northpole req#1 (docs/specs/northpole.md).

canonical: `gh pr list --search "head:issue-1133/implementation" --state all --json number,title,state,url,mergeCommit,commits`, read this session.
Delivered through three merged PRs against `origin/main` at `2e51bd92`
(`git rev-parse origin/main`, run this session):
- #1138 (phase-1 survey + proposal, commit `082b5916`)
- #1143 (phase-2 code delivery, commits `3ec43128`, `b2491a8b`)
- #1149 (reopen fix, commit `11efcb02`)

## What was read this session, in order

canonical: `gh pr list --head issue-1133/implementation --state all`, output read this session — resolves the three merged PRs listed above.

1. `gh issue view 1133` — issue body (two named defects: registry
   staleness on re-arm, blocking `--follow` remediation text).
   canonical: `gh issue view 1133`, output read this session.
2. `gh issue view 1133 --json comments` — full comment thread,
   including the `APPROVE issue-1133/implementation` exact-string
   comment (2026-08-13T02:15:54Z) and the later reopen comment
   (2026-08-13T02:35:13Z), whose body states: "the detached child that
   --rearm spawns exits immediately with '기록 없음 — 아직 스폰된 적이
   없다' ... because the child re-runs 'spawn.py watch --issue N --role
   R --follow' WITHOUT the repo context".
   canonical: `gh issue view 1133 --json comments`, output read this session.
3. `gh pr diff 1143` and `gh pr diff 1149` — the diffs themselves, read
   before either record narrative (fresh-eyes ordering): `spawn.py`'s
   `_rearm_watcher_detached()` (new function, holds
   `_workspace_index_locked()` across the whole read-decide-spawn-write
   span, spawns the replacement watcher detached via
   `subprocess.Popen(..., start_new_session=True)`), the new `--rearm`
   CLI flag, the repointed `watcher-dead`/`watcher-silent` remediation
   strings, and additions to `gates/test_watch_rearm_registry.py`.
   canonical: `gh pr diff 1143`, output read this session.
   derived: `gh pr diff 1143` — 5 `def test_` methods added to gates/test_watch_rearm_registry.py in that diff.
   canonical: `gh pr diff 1149`, output read this session.
   derived: `gh pr diff 1149` — 1 more `def test_` method (`test_rearm_passes_repo_context_for_mismatched_cwd`) added on top of #1143's.
   #1149's diff adds a `cwd` parameter to `_rearm_watcher_detached()`
   and threads `-C <resolved cwd>` into the detached child's argv.
4. `gh pr view 1143 --json body,reviews`, `gh pr view 1149 --json
   body,reviews`, `gh pr view 1138 --json body,reviews` — all three
   show `"reviews":[]`. Approval for this repo's single-account mode is
   the issue comment, not a PR review (per role directive's two
   approval paths).
   canonical: the three `gh pr view --json body,reviews` commands, output read this session.
5. `git show origin/main:docs/issue-1133/reports/implementation.md` —
   the observed role's own phase-2 record, read only after the diffs
   above.
   canonical: `git show origin/main:docs/issue-1133/reports/implementation.md`, output read this session. Frontmatter carries `verdict: pass` and `loop_state: landed`; a "Reopen fix" section documents the same residual defect item 2's comment describes, and its fix, added by #1149's commit on top of the record #1143 first wrote.
6. `cat docs/specs/approvers.md` — `JiwonJung94` and `jjongkwann` are
   the only listed approver accounts; the issue's `APPROVE
   issue-1133/implementation` comment and every PR/commit author in
   this chain is `JiwonJung94` — single-account mode (PR author and
   approver are the same account) applies.
   canonical: `cat docs/specs/approvers.md`, output read this session.
7. `find docs/issue-1133 -iname "*scout*"` and `grep -n -i
   "scout\|skip" docs/issue-1133/proposals/watcher-rearm-detached.md
   docs/issue-1133/reports/implementation/survey.md` — no scout-brief
   file exists anywhere under `docs/issue-1133/`; the implementation
   role's own survey.md:7-11 carries an explicit skip-record ("Scout-
   directive skip condition applies: this is a pure bugfix... Recorded
   per survey-order-directive's mandatory skip-record requirement").
   canonical: the `find` and `grep` commands above, output read this session.
8. `docs/issue-1133/reports/implementation/2026-08-13-hunt-watcher-rearm-detached.md`
   — read this session.
   canonical: that file, read this session — a before-landing warrant hunt (stance 1, plugin-rule-cancellation) ran before PR #1143 landed; its own text states "No reproducible pair of rules found that cancel each other." An earlier-dated after-proposal-hunt section (stance 0, TOCTOU) in the same file records a race found in the original design, folded into the proposal before code was written.

## Independent re-execution of the cited evidence

On the current working tree (`origin/main` at `2e51bd92`, this branch
checked out from it with no other changes):

canonical: `python3 -m pytest gates/test_watch_rearm_registry.py -v`, run this session.
```
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_already_alive_watcher_is_not_respawned PASSED [ 14%]
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_autoarm_returns_immediately_surviving_caller_exit PASSED [ 28%]
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_never_armed_entry_untouched_and_still_missing PASSED [ 42%]
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_rearm_clears_watcher_dead_and_updates_registry PASSED [ 57%]
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_rearm_passes_repo_context_for_mismatched_cwd PASSED [ 71%]
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_rearmed_watcher_dying_again_is_still_flagged PASSED [ 85%]
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_remediation_strings_carry_no_bare_follow PASSED [100%]

7 passed in 0.20s
```
canonical: the `pytest -v` run immediately above, executed live this
session — checks the outcome claim against currently-merged code; not
a re-execution of the observed role's own task (building/fixing
spawn.py), per role-directive PROHIBITED clause. The fenced output
shows one test method
(`test_autoarm_returns_immediately_surviving_caller_exit`) that this
session's item-3 `derived:` lines above did not find in either PR's
diff to this file — it landed via a later, unrelated commit on `main`.

## Open question carried into phase 2

canonical: item 4 (`gh pr view --json body,reviews`, three commands) and item 2 (`gh issue view 1133 --json comments`), both read this session, above.
Neither #1143 nor #1149 carries a GitHub PR review Approve (empty
`reviews` array on both). Approval instead took single-account-mode
form: the issue-level `APPROVE issue-1133/implementation` comment
(2026-08-13T02:15:54Z), which predates both PRs' commits and so can
textually cover both under one phase-2 approval — but #1149 was pushed
straight to the same branch after the plain-prose "Reopening on
live-fire evidence" comment (2026-08-13T02:35:13Z), with no new
exact-match `APPROVE` string posted afterward. Whether a residual-
defect reopen-fix on an already-approved branch is covered by the
original phase-2 approval, or needed its own fresh one, is a phase-2
trajectory judgment call, not resolved here.
