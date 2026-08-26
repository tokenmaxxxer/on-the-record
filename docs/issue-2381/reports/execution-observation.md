---
issue: 2381
role: execution-observation
author: execution-observation
loop_state: done
upstream:
  - path: docs/issue-2381/reports/implementation.md
    sha: dd55936b8b7a3626a8098311aa22483acf329f25
  - path: gates/check_runner.py
    sha: dd55936b8b7a3626a8098311aa22483acf329f25
  - path: on-the-record/directive/merge-gates.md
    sha: dd55936b8b7a3626a8098311aa22483acf329f25
  - path: .gitignore
    sha: dd55936b8b7a3626a8098311aa22483acf329f25
subject: PR #2445 (issue-2381/implementation, head dd55936b8b7a3626a8098311aa22483acf329f25, base main)
test: gates/test_check_runner.py -q; independent bare-repo repro of fetch_all_role_branches()'s --prune fail-closed fix; grep sweep for remaining writers of the flat hook-fires log; cea0f583/8ef2e3b7 read directly for the implementation.json root-cause claim
result: passed
assertedBy: execution-observation, independently re-run this session
---

# issue-2381 — execution-observation record

## What was done

Independent execution-observation of PR #2445
(`issue-2381/implementation`, head `dd55936b`, still OPEN against `main`
at observation time). I fetched the full origin refspec
(`git fetch origin '+refs/heads/*:refs/remotes/origin/*' --prune`) and
diffed `main..origin/issue-2381/implementation` directly rather than
reading the diff out of the PR body.

canonical: `git diff main origin/issue-2381/implementation --
gates/check_runner.py .gitignore on-the-record/directive/merge-gates.md`
(this session) — result: three files changed, matching the
implementation record's own "What was done" bullets.

**Acceptance criterion 1** ("the orchestrator-facing directive ... or
automates fetching all role branches ... before running
check_runner/merge_gate"):

canonical: `dd55936b:gates/check_runner.py:394-430` (read directly, this
session) — `checkout_pr_worktree()` now calls a new
`fetch_all_role_branches(repo)` helper that runs `git fetch --prune
origin '+refs/heads/*:refs/remotes/origin/*'` in place of the old
`git fetch origin <head_ref>` single-branch call.

derived: `grep -n "worktree add\|subprocess" gates/merge_gate.py`, run
in `/tmp/pr2445-worktree` this session — result: only `gh pr view` and
fetch-free ref resolution (`pr_refs()`, `stale_revert_reasons()` calling
`git merge-base`), no `git fetch` or `git worktree add` call anywhere in
`merge_gate.py`. `on-the-record/directive/merge-gates.md:38-40`
(pre-existing lines, unchanged by this diff, read directly this session)
documents that `merge_gate.py` runs after `check_runner.py` against the
same `--repo` and depends on `check_runner.py`'s own PR comment already
existing — so the one fetch site this PR fixed structurally covers both
gates named in the issue, not just the one it directly touches.

canonical: `dd55936b:on-the-record/directive/merge-gates.md:51-61` (read
directly, this session) — documents the new fetch-all-branches behavior
for the orchestrator.

I re-ran the before-landing warrant hunt's own repro independently, in a
disposable bare repo I built myself (not reusing any script or file from
the PR), to confirm the `--prune` fix actually restores fail-closed
behavior rather than taking the hunt record's paste on faith:

acceptance: independent bare-repo repro, built and run this session —
result:
```
$ git init --bare /tmp/origin_v.git -q && git clone /tmp/origin_v.git /tmp/vclone1 -q
$ cd /tmp/vclone1 && git commit --allow-empty -m init -q && git push origin HEAD:refs/heads/main -q
$ git checkout -b issue-99/role -q && git commit --allow-empty -m branchcommit -q && git push origin issue-99/role -q
$ git clone /tmp/origin_v.git /tmp/vclone2 -q && cd /tmp/vclone2
$ git fetch origin '+refs/heads/*:refs/remotes/origin/*'
$ git rev-parse origin/issue-99/role
0d775d45a7f868ea3f8a0e3c452619404ccc3939
$ (cd /tmp/vclone1 && git push origin --delete issue-99/role -q)
$ git fetch --prune origin '+refs/heads/*:refs/remotes/origin/*'
 - [deleted]         (none)     -> origin/issue-99/role
$ git rev-parse origin/issue-99/role; echo "exit=$?"
fatal: ambiguous argument 'origin/issue-99/role': unknown revision or path not in the working tree.
exit=128
```

PASS: the `--prune` fetch removes the stale local ref for a branch
deleted on origin, so the next `git worktree add origin/<ref>` fails
closed ("fatal: invalid reference") exactly as the pre-#2381
single-branch fetch used to, instead of silently succeeding against
stale content. canonical: `dd55936b:docs/issue-2381/reports/implementation/2026-08-26-hunt-orchestrator-fetch-all-branches.md`
(read directly, this session) — its own claimed repro/result matches
what I independently reproduced above, but mine was built from a repo I
created myself, not copy-run from that file's script.

acceptance: `python3 -m pytest gates/test_check_runner.py -q`, run this
session in a detached worktree at `origin/issue-2381/implementation`
(`/tmp/pr2445-worktree`, not my own branch) — result:
```
35 passed in 1.67s
```

Matches the PR's claimed count exactly. derived: `grep -rn
"fetch_all_role_branches" --include='*.py' .`, run in
`/tmp/pr2445-worktree` this session — result: one hit total (the
definition plus its one call site, both in `gates/check_runner.py`, no
test file). The 35-passed count is a no-regression signal on the
pre-existing suite, not evidence a persistent test exercises the new
behavior; the acceptance-level evidence for the new behavior is the
bare-repo repro above (this session's own run) plus the hunt record's
own before/after repro, consistent with this protocol's verify-at-landing
stance (no new persistent test file required by default).

**Acceptance criterion 2** (`roles/implementation.json` and
`.orchestrate-hook-fires.log` either gitignored or root-caused):

canonical: commit `8ef2e3b7` (issue-2383, already on `main` before this
branch existed), read directly this session — its message states the
corrupting writer was three test methods in
`tests/test_spawn_gate_wiring.py` that wrote/restored the real tracked
`roles/implementation.json` directly, vulnerable to a worker killed
mid-test under `pytest -n auto` leaving the file near-empty; fixed by
patching `spawn.ROOT` to an isolated tempdir. derived: `git log --oneline
-- roles/implementation.json` on `main`, run this session — result: no
commit on `issue-2381/implementation` touches that path, confirming the
implementation record correctly did not re-touch an already-fixed file.

derived: `grep -rn "orchestrate-hook-fires\.log" --include="*.py"
--include="*.sh"` across the repo, run this session — result: every
remaining reference outside `docs/` is either the replacement module's
own docstring naming the file it replaces (`hook_fires.py`,
`on-the-record/hooks/hook-fires.sh`) or a test asserting the file is
*not* created (`tests/test_spawn_consult_panel.py:1209`) — no live
writer remains. derived: `git ls-files | grep -x
'\.orchestrate-hook-fires\.log'` (match — still tracked) plus `git diff
--stat -- .orchestrate-hook-fires.log` (empty — no pending
modification) plus `git log -1 -- .orchestrate-hook-fires.log` (→
`cea0f583`, 2026-08-25), all run this session against my own checkout —
the file is tracked-but-dormant content, and this PR's `.gitignore`
addition stops it from silently reappearing if a stray old script or
branch ever targets that exact filename again.

## Why

Both fixes are structurally minimal and match the issue's stated
acceptance rather than over-scoping: criterion 1's fetch fix lives in
the one shared call site both named gates depend on (verified above, not
asserted), and criterion 2 required no new code because both named drift
sources were confirmed dead. canonical: `dd55936b:docs/issue-2381/reports/implementation.md`
"Rejected alternative" paragraph (read directly, this session) — a
standalone `spawn.py ps` fetch wrapper — is consistent with what this
session independently found reading `merge_gate.py` (derived: tag
above, same command): it has no fetch call of its own to wire a wrapper
into, so fixing the shared `check_runner.py` fetch site is smaller and
can't be bypassed by a caller forgetting to invoke a separate wrapper.

## What did not work

None encountered this session. canonical:
`dd55936b:docs/issue-2381/reports/implementation.md` "What did not
work" section (read directly, this session) — the implementation
record's own before-landing warrant hunt found and fixed a real gap in
its first cut (missing `--prune`) before this observation began; this
record re-verifies that fix independently (acceptance tag above) rather
than treating it as something to rediscover.

## Upstream basis

- docs/issue-2381/reports/implementation.md, sha
  `dd55936b8b7a3626a8098311aa22483acf329f25` (PR #2445,
  `issue-2381/implementation` -> `main`, still open)
- gates/check_runner.py, on-the-record/directive/merge-gates.md,
  .gitignore at the same sha, diffed against `main` directly
- commit `8ef2e3b7` (issue-2383, already on `main`), read directly for
  the `roles/implementation.json` root-cause claim

## Open findings

1. `gates/test_check_runner.py` carries no test naming
   `fetch_all_role_branches` or exercising the `--prune` fail-closed
   behavior (derived: tag above, "one hit total"). The 35-passed count
   is a regression signal on the pre-existing suite, not committed
   coverage of the new behavior. Acceptance-level evidence instead rests
   on the hunt record's own before/after repro plus this session's
   independent bare-repo re-derivation (acceptance: tag above).
   resolution path: none required to close this issue —
   verify-at-landing does not mandate a new persistent test file by
   default, and the behavior is independently reproduced twice now
   (hunt record + this record); a future session touching
   `fetch_all_role_branches()` again should consider adding a regression
   test at that point, but this is not a gap in issue #2381's own two
   acceptance criteria.
2. canonical: `dd55936b:docs/issue-2381/reports/implementation.md`
   "Open findings" section (read directly, this session) discloses that
   the *new* per-session shard directory `.orchestrate-hook-fires/` is
   not gitignored, and could accumulate as untracked drift for an
   orchestrator's own top-level (non-role) session. derived: this
   session's own `git status --porcelain=v1` (run at the start of this
   session, before any of this session's own writes) — result:
   `.orchestrate-hook-fires/10b719780d1c9a1d8b543923.log` and
   `.orchestrate-hook-fires/24b0bf02315a934dfd2fed3d.log` both untracked
   — confirming the disclosed gap is live, not hypothetical. However,
   this does not reproduce the specific symptom issue #2381 names (a
   stash needed before every rebase): `git pull --rebase` only fails on
   untracked files that collide with a path the rebase would create, and
   these shard filenames are content-hash-derived per session, so
   collision with an incoming commit's paths is not a realistic
   occurrence the way a modified *tracked* file (the old flat log, the
   old corrupted `implementation.json`) was. resolution path: none
   required for this issue's acceptance criteria, which name a
   stash-before-rebase symptom this shard directory does not reproduce;
   whether the orchestrator's own unspawned sessions should
   gitignore/sweep/bundle their own shards is a separate design question
   the implementation record correctly left open rather than folding
   into this fix.

## Next steps

None — `loop_state: done`. canonical: the `acceptance:`/`derived:` tags
throughout "What was done" above (this session's own bare-repo repro,
`pytest gates/test_check_runner.py -q` run, and grep sweeps) — both
acceptance criteria are verified independently against the
implementation branch's actual code and history, not against the PR's
own prose; the two open findings above are disclosed gaps outside this
issue's literal acceptance scope, not blockers to it.
