---
issue: 2383
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: issue #2383 body
    sha: same-commit
code_under_review:
  - .gitignore
  - lifecycle.py
  - spawn.py
  - tests/test_spawn_pipeline.py
type: fix
breaking: none
verdict: pass
---

# issue-2383 — implementation record

## What was done

Audited the three acceptance checks and landed a fix for each, all inside
this repo (`tokenmaxxxer/on-the-record`), which is what actually spawned
this session. canonical: `git remote -v` run in this session's own working
directory returned `origin https://github.com/tokenmaxxxer/on-the-record.git`,
2026-08-25. The separate, older `/home/jwjung/.claude/tokenmaxxxer/muster`
checkout the issue's evidence pointed at turned out to be a stale,
unrenamed clone of the same project this session never ran through.
canonical: `git -C /home/jwjung/.claude/tokenmaxxxer/muster log --oneline -5`
showed `181f4be coding(issue-83): rebrand muster -> on-the-record per
approved proposal`, 2026-08-25.

1. **Intentional-scratch gitignore gaps (acceptance check 1, gitignore
   half).** `.gitignore` gained three entries: `role_model.txt` (an
   optional local model-override file `spawn.ROLE_MODEL_CONFIG` reads from
   the checkout root, issue #60), `.on-the-record/check-run-artifact.json`
   (written by `check_run_artifact.write_artifact()` into the checkout it
   runs against), and `.on-the-record/directive/` (the untracked
   per-session directive-text cache this very session's own checkout
   carried at startup).
   canonical: `gates/check_runner.py:22` `ARTIFACT_PATH =
   Path(".on-the-record/check-run-artifact.json")` and
   `gates/check_runner.py:484` `cra.write_artifact(repo / ARTIFACT_PATH,
   artifact)`; `git status --porcelain=v1 --untracked-files=all` at this
   session's start listed `.on-the-record/directive/*.md` as five
   untracked files before any edit this session made.

2. **The process writing garbage into checkout-root files (acceptance
   check 1, process half).** `tests/test_spawn_pipeline.py`'s `SpawnCmd`
   and `DryRunModelReflection` classes had seven test methods writing
   directly to the real `spawn.ROLE_MODEL_CONFIG` (checkout-root
   `role_model.txt`) with a manual save-before/restore-in-`finally`
   pattern, including `write_text("   ")` (whitespace-only) and
   `write_bytes(b"\xff\xfe\x00\x01")` (invalid UTF-8) as deliberate test
   inputs. `pytest.ini`'s `addopts = -n auto` runs this suite under
   pytest-xdist; a worker killed between the write and the `finally`
   leaves the real checkout-root file in exactly that corrupted,
   near-empty state — the same failure shape the issue describes for a
   tracked file (`roles/implementation.json`), reproduced here for a
   real, previously-unignored one. `test/test_spawn_model_override.py`
   had already solved this exact problem by patching
   `spawn.ROLE_MODEL_CONFIG` to a `tempfile.TemporaryDirectory()` path in
   `setUp`/`tearDown`; applied the same pattern to both classes in
   `tests/test_spawn_pipeline.py` and dropped the now-unneeded
   save/restore boilerplate from all seven methods.
   canonical: `test/test_spawn_model_override.py` lines 19-23 document the
   xdist race by name ("pytest-xdist(`-n auto`, pytest.ini)가 테스트를
   여러 프로세스에 흩뿌리므로... 서로 다른 워커에서 같은 파일을 동시에
   쓰고 지워 경합한다"); `git diff tests/test_spawn_pipeline.py`, this
   commit, for the applied fix.
   I could not find a writer for the specific tracked file the issue names
   (`roles/implementation.json`) — see Open findings.

3. **Worktree accumulation, monitored/pruned at routine cleanup
   (acceptance check 2).** `spawn.py clean` (-> `lifecycle.roster_clean()`)
   is this repo's existing routine landing/cleanup entry point; it already
   pruned stale workspace clone directories but never touched `git
   worktree` state. Added `lifecycle._prune_worktrees(repo)`, called from
   `roster_clean()` when a `repo` (the cwd `clean` was invoked from) is
   passed: it prints the current `git worktree list` before pruning (so
   accumulation is visible, not just silently swept) and then runs `git
   worktree prune -v`. Wired the `spawn.py clean` call site to pass
   `Path(a.cwd).resolve()`.
   canonical: `git diff lifecycle.py spawn.py`, this commit; smoke test
   below under Acceptance evidence confirms `_prune_worktrees` removes an
   orphaned worktree registration against a real git repo.
   This is a defense-in-depth sweep, not a replacement for site-level
   cleanup — both actual `git worktree add` call sites found
   (`gates/check_runner.py`'s `worktree_for_ref`/`checkout_pr_worktree`,
   temp-dir prefix `check-runner-pr-`, matching the issue's observed
   `/tmp/check-runner-pr-*` entries; and `gates/reexecution_gate.py:51`)
   already wrap their worktree in `try`/`finally` with `git worktree
   remove --force`. A `finally` doesn't run on a hard-killed process,
   which `roster_clean()`'s periodic sweep now catches.
   canonical: `gates/check_runner.py:376` `tmpdir =
   tempfile.mkdtemp(prefix="check-runner-pr-")`; `gates/check_runner.py:473,486-487`
   `try: ... finally: remove_worktree(repo, worktree)`;
   `gates/reexecution_gate.py:48-51,70-72` for the second site's own
   `TemporaryDirectory`/`finally` pair.
   The issue's other observed worktree cruft, `/tmp/claude-*/scratchpad/*`,
   has no corresponding `git worktree add` call site in either repo — see
   Open findings.

4. **#2379's corrupted merge-base (acceptance check 3).** `_base()`
   (`board.py:715-725`) resolves the branch-cut base via `git symbolic-ref
   --short refs/remotes/origin/HEAD` first, falling back to
   `origin/main`/`origin/master` only when that symref is absent — a
   present-but-stale `origin/HEAD` is trusted unconditionally, with no
   freshness check. `issue_workspace()`'s new-clone path already
   refreshes `origin/HEAD` right after fetching (`git remote set-head
   origin -a`, added for issue #221, predating #2379) — but the
   workspace-reuse paths (cwd already is the target workspace; or the
   target workspace directory already exists) only ran
   `_fetch_or_halt(..., "재사용 워크스페이스")` with no `after=` refresh.
   A workspace whose `origin/HEAD` was ever wrong (remote default branch
   renamed after first clone, or the original `set-head` call — whose
   return code was never checked — silently failed) stays wrong on every
   future reuse, and `_base()` resolves branch cuts against it without
   complaint. Extracted the refresh into a reusable
   `_set_origin_head(work_dir)` helper and wired it as the `after=`
   callback on both reuse-path `_fetch_or_halt()` calls (previously only
   the new-clone path had it).
   canonical: `board.py:715-725` for `_base()`'s resolution order;
   `git diff spawn.py`, this commit, for the fix; smoke test below under
   Acceptance evidence confirms `_set_origin_head` refreshes a stale
   symref against a real two-repo git setup.

## Why

Each fix targets the concrete, evidenced mechanism found for its
acceptance check rather than a plausible-sounding guess. canonical: the
gitignore gaps were confirmed against the actual writer code cited in item
1 above; the `role_model.txt` test race was confirmed against the
already-fixed sibling test cited in item 2; the worktree-prune gap was
confirmed by reading every `git worktree add` call site cited in item 3
and verifying each already has cleanup, which is why a periodic sweep
(not a per-site fix) is the right defense-in-depth; the #2379 fix targets
the one asymmetry found between `issue_workspace()`'s new-clone and reuse
paths, verified against `_base()`'s resolution order cited in item 4.

Where the evidence ran out — `roles/implementation.json`'s writer, and the
`/tmp/claude-*/scratchpad/*` worktrees' source — this record says so in
Open findings instead of proposing an unverified fix for a mechanism
nobody located.

## What did not work

- Initially traced #2379 against `/home/jwjung/.claude/tokenmaxxxer/muster`'s
  own `spawn.py` (the directory literally named after the pre-rebrand
  project), on the theory that "the orchestrator's own checkout" from the
  issue text meant that directory. A dispatched research agent found a
  real stale-`origin/HEAD` bug there (`_base()`/`checkout_issue_branch()`
  at muster's `spawn.py:857-867,1552-1553`) — but this repo's own
  `spawn.py` already carries the fix for that exact bug class in its
  new-clone path (`git log -S "remote set-head origin" -- spawn.py`, this
  session's own working directory, returned `fb7e84b8 issue-221: phase 2
  - workspace-sync fail-closed fixes`, dated well before #2379 was filed),
  which meant the muster-repo finding could not be #2379's actual cause
  for this repo's PRs. canonical: `git -C
  /home/jwjung/.claude/tokenmaxxxer/muster remote -v` returned `origin
  https://github.com/tokenmaxxxer/muster.git` — a different GitHub repo
  from `tokenmaxxxer/on-the-record`, confirming it is not what actually
  spawned this session or produced PR #2372/#2376 (#2379's subject).
  Re-traced the same question against this repo's own branch-cut code
  instead and found the narrower, real gap described in item 4 above.

## Skill verdicts

skill-verdict: work-in-english — applied: invoked; this record, the code
comments, and commit messages are written in English per the skill even
though the task/operator instructions arrived in Korean; only this
session's final user-facing turn summary is in Korean.

## Upstream basis

- issue #2383 body is the sole upstream input; this issue's own record
  directory carried no prior artifact for this session to build on.
  canonical: `gh issue view 2383`, run 2026-08-25.
  sha: same-commit (this record lands in the same commit as the fix).

## Open findings

- **`roles/implementation.json`'s corruption is not root-caused.** Grepped
  every `.py` file in both `muster` and this repo for any write targeting
  a `roles/*.json` path outside an isolated fixture. derived: `grep -rn
  'roles.*write_text\|ROOT / "roles"\|Path("roles"' tests/ test/ gates/
  *.py` (this session's own working directory) plus the equivalent sweep
  against `/home/jwjung/.claude/tokenmaxxxer/muster`, both run 2026-08-25.
  The only unisolated write into a real checkout's `roles/` directory
  found anywhere (`tests/test_gates.py:106-121`,
  `t_rulebook_version_is_recorded`, writes a differently-named
  `roles/_probe.json` probe file) turned out to be currently dead code: it
  calls `spawn.rulebook_version(...)`, which no longer exists on the
  `spawn` module. canonical: `python3 -m pytest tests/test_gates.py -k
  rulebook_version_is_recorded -v -n 0 --runxfail`, this session, output
  `AttributeError: module 'spawn' has no attribute 'rulebook_version'` —
  the test is permanently masked passing by its own
  `@pytest.mark.xfail(..., strict=False)` decorator, whose documented
  reason ("dirty checkout") is no longer what's actually failing. That
  test never reaches the file write in the current codebase, so it cannot
  explain live corruption. No other candidate writer was found.
  resolution path: a future session should (a) determine why
  `spawn.rulebook_version` disappeared and either restore it or delete the
  dead test, and (b) if `roles/implementation.json` corruption recurs,
  capture the corrupting process's identity (parent PID, cwd, argv) at the
  moment it's caught mid-write — static grepping across every test file in
  both repos found no candidate, so the next lead has to come from a live
  capture rather than more grepping.
- **`/tmp/claude-*/scratchpad/*` worktrees have no known source.**
  Grepped `muster` (`spawn.py`, `gates/gates.py`, `gates/ci.py`) and this
  repo (`spawn.py`, `lifecycle.py`, `board.py`, `pipeline.py`, every
  `gates/*.py`) for `"worktree add"`, `"scratchpad"`, and
  `"check-runner-pr"`. derived: `grep -rn "worktree add\|scratchpad" *.py
  gates/*.py` in both checkouts, run 2026-08-25. The only `git worktree
  add` call sites found are cited in item 3 above (`gates/check_runner.py`,
  prefix `check-runner-pr-`, matching the issue's *other* observed path;
  and `gates/reexecution_gate.py:51`, a bare `tempfile.TemporaryDirectory()`
  with no `scratchpad`/`claude-*` naming). Neither constructs a
  `/tmp/claude-*/scratchpad/*` path.
  resolution path: the naming convention (`claude-*`) suggests this is
  produced by the Claude Code harness itself or a different tool outside
  both repos this session had access to audit — out of this issue's reach
  without visibility into that code.
- **`.orchestrate-hook-fires.log` is a live, currently-unfixed instance of
  the exact bug class acceptance check 1 asks about, just not the file the
  issue named.** It's a tracked, single, append-only log that every
  session's hooks write timestamped lines into. canonical: `git diff
  --stat -- .orchestrate-hook-fires.log`, this session's own working
  directory, showed 2 lines/74 bytes added purely from this session's own
  hook fires, visible before any intentional edit. This repo already
  fixed the identical problem for a sibling log. canonical: `git log
  --oneline -1 -- .orchestrate-hook-fires.log` (run against the commit
  history in this session's own working directory) surfaces commit
  `983ad6e4 issue-2333: shard consult-log per session to eliminate the
  append-only merge-conflict class` as a recent, on-point precedent for a
  *different* log file — `.orchestrate-hook-fires.log` itself was not
  included in that fix and still accumulates unboundedly.
  resolution path: a follow-up issue should apply the same per-session
  sharding `983ad6e4` used for `consult-log` to
  `.orchestrate-hook-fires.log`. Left out of this change's scope — it's a
  structural rework of a shared, actively-written-to file, not a
  same-shape fix to slot in alongside the three landed above without its
  own dedicated review.

## Next steps

None — `loop_state: landed`. The three follow-ups above are filed as open
findings for a future session, not left implicit.

## Acceptance evidence

acceptance: `python3 -m pytest tests/test_spawn_pipeline.py test/test_spawn_model_override.py gates/test_clean_reconcile_safety.py -q -n auto` — result:
```
102 passed, 1 xfailed in 6.00s
```

acceptance: smoke test of `lifecycle._prune_worktrees` against a real git repo with an orphaned worktree registration (script run inline this session, not committed as a test file per the verify-at-landing convention) — result:
```
before prune:
/tmp/tmp2tmpromx/repo       7f0ace4 [master]
/tmp/tmp2tmpromx/orphan-wt  7f0ace4 (detached HEAD) prunable

worktree 목록 (정리 전 2개):
  /tmp/tmp2tmpromx/repo       7f0ace4 [master]
  /tmp/tmp2tmpromx/orphan-wt  7f0ace4 (detached HEAD) prunable
worktree prune: Removing worktrees/orphan-wt: gitdir file points to non-existent location
after prune:
/tmp/tmp2tmpromx/repo  7f0ace4 [master]
PASS: _prune_worktrees removes orphaned worktree registrations
```

acceptance: smoke test of `spawn._set_origin_head` against a real two-repo git setup (origin + clone) with a renamed default branch (script run inline this session, not committed as a test file) — result:
```
origin/HEAD before _set_origin_head: origin/main
origin/HEAD after _set_origin_head: origin/trunk
PASS: _set_origin_head refreshes a stale origin/HEAD symref
```

acceptance: `git diff --stat` (this commit, before staging) — result:
```
 .gitignore                   |  3 +++
 lifecycle.py                 | 32 ++++++++++++++++++++--
 spawn.py                     | 30 ++++++++++++++++-----
 tests/test_spawn_pipeline.py | 63 ++++++++++++++++++++++----------------------
 4 files changed, 89 insertions(+), 39 deletions(-)
```
