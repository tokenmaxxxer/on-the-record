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
  - tests/test_spawn_gate_wiring.py
  - gates/test_clean_reconcile_safety.py
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
- CHANGES round (2026-08-25): the first cut of the REQ-2b age-prune fix
  used the worktree's own top-level directory mtime as its "last
  activity" signal. A background warrant-hunter run before landing (per
  the warrant protocol's before-landing check) found this was wrong —
  git only bumps a directory's own mtime on entry add/remove/rename, not
  on writes to files already inside it, so a still-actively-used worktree
  could be force-removed. canonical:
  `docs/issue-2383/reports/implementation/2026-08-25-hunt-worktree-age-prune.md`,
  this session, 2026-08-25. Fixed by walking the whole tree
  (`_worktree_last_activity()`) instead of trusting the top directory
  alone — see item 2's follow-up note above.

## Skill verdicts

skill-verdict: work-in-english — applied: invoked; this record, the code
comments, and commit messages are written in English per the skill even
though the task/operator instructions arrived in Korean; only this
session's final user-facing turn summary is in Korean. Re-invoked and
re-applied in the CHANGES round above (same convention, no change).

other mounted skills: not triggered — this CHANGES round is a small,
same-shape bugfix (root-cause a known test anti-pattern, extend an
existing sweep function's condition) with no GoF-pattern decision, no
coupling/cohesion threshold crossed, no performance-cliff data-structure
choice, no multi-module architecture decision, and no conformance-review
role output to record (conformance-review-finding-record targets
`docs/issue-<n>/reports/conformance-review.md`, not this implementation
record).

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
  **Resolved in the PR #2398 CHANGES round (2026-08-25) — see "CHANGES
  round" below for the fix and evidence.** The earlier grep pattern above
  (`roles.*write_text\|ROOT / "roles"\|Path("roles"`) missed
  `tests/test_spawn_gate_wiring.py`'s three offending methods because
  they spell the path as `Path(spawn.ROOT) / "roles" /
  "implementation.json"` on one line and call `.write_text()` on it
  several lines later, not matching any single-line substring in that
  pattern. canonical: `grep -n "implementation\.json" tests/test_spawn_gate_wiring.py`
  this session, 2026-08-25, output lines 47, 160, 190 — each a
  `f = Path(spawn.ROOT) / "roles" / "implementation.json"` assignment
  immediately preceding a `try: ... f.write_text(json.dumps(spec)) ...
  finally: f.write_text(original_text)` block, this session's own
  working directory.
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

## CHANGES round (2026-08-25) — response to PR #2398 conformance review

The conformance review (PR #2398, merged as `e97be75c`) found requirements
unmet in the PR #2389 head this record originally described.
derived: `gh pr view 2398 --json body -q .body`, this session, 2026-08-25:
```
5 of 7 verify Present: the audit itself, the gitignore-scratch remedy,
the git worktree prune wiring into spawn.py clean's routine-cleanup
path, and both halves of the #2379 determine-and-fix check.
2 of 7 do not verify Present:
- Absent — the issue's own named example, roles/implementation.json's
  corrupting process, was never found or fixed
- Incorrect — the worktree-prune fix only removes registrations whose
  backing directory is already gone; it does not monitor/prune by age
```
The two non-Present items are REQ-1c (Absent, `roles/implementation.json`'s
corrupting process never found) and REQ-2b (Incorrect, worktree prune
covers existence but not age). Both are fixed in this round; the branch
was also rebased onto current `origin/main` (was 4 commits behind with
overlapping `spawn.py` regions touched by an unrelated issue-2293
landing).
canonical: `gh pr view 2398 --json body,state`, this session, 2026-08-25,
`state: MERGED`; `gh pr view 2389 --json body`, this session, 2026-08-25,
for the two named unmet requirements.

1. **REQ-1c fixed — `roles/implementation.json`'s corrupting process,
   root-caused and fixed.** `tests/test_spawn_gate_wiring.py` had three
   test methods (`test_role_declared_permissions_allow_entries_preserved`,
   `test_duplicate_against_role_declared_entry_is_not_duplicated`,
   `test_sandbox_never_enabled_regardless_of_role_declaration`) that
   wrote directly to the real, tracked `roles/implementation.json` with a
   save-before/restore-in-`finally` pattern — the same anti-pattern this
   PR already fixed for `role_model.txt` in `tests/test_spawn_pipeline.py`,
   but missed in this sibling file. Under pytest-xdist (`-n auto`,
   `pytest.ini`), a worker killed between the write and the `finally`
   leaves the real checkout-root file in exactly the near-empty state the
   issue names. canonical: `pytest.ini` line 4, `addopts = -n auto`
   (applies repo-wide, this file included), this session's own working
   directory.
   Fix: added a `_role_settings_over_patched_spec(role, mutate)` helper
   (`tests/test_spawn_gate_wiring.py`) that reads the real spec, applies
   the mutation to an in-memory copy, writes that copy into an isolated
   `tempfile.TemporaryDirectory()`, and monkeypatches `spawn.ROOT` to
   point there for the duration of the `role_settings()` call — the real
   tracked file is never opened for writing. This is safe specifically
   because all three call sites invoke `spawn.role_settings(role)` with
   `cwd=None`: `pipeline.role_settings()`'s only other `ROOT`-dependent
   branch (`self_hosted_hooks()`/core-rulebook clone under
   `_sp.ROOT / "runs" / "rulebooks"`) is gated on `cwd is not None`, so
   redirecting `ROOT` cannot trigger a real network clone in these tests.
   canonical: `pipeline.py:358` `if cwd is not None and
   inject_self_hosted_hooks:`, this session's own working directory,
   2026-08-25.
   acceptance: `git diff --stat -- roles/implementation.json` after
   running the full suite (including this file) under `-n auto` — result:
   ```
   (no output — file untouched)
   ```
2. **REQ-2b fixed — worktree pruning now covers age, not just
   existence.** `lifecycle._prune_worktrees()` gained a second sweep
   after the existing `git worktree prune -v` call: it lists all
   registered worktrees (`git worktree list --porcelain`), skips index 0
   (the primary checkout itself, matched by path as a second guard), and
   for every other entry whose directory is still present, compares its
   last-activity time against `MUSTER_WORKTREE_MAX_AGE_HOURS` (new env
   var, default 24h — much shorter than workspace `auto_sweep`'s 14-day
   default, since these `check_runner.py`/`reexecution_gate.py` worktrees
   are meant to live for one check run, not days). Anything older is
   removed with `git worktree remove --force`; a removal failure (e.g. a
   locked worktree) is printed and treated as non-fatal, matching this
   function's existing "cleanup is nice-to-have, not a hard
   precondition" stance.
   canonical: `lifecycle.py` `_worktree_max_age_hours()` and the age-sweep
   block in `_prune_worktrees()`, this commit, this session's own working
   directory.
   **Follow-up fix within the same round — a background warrant-hunter
   run before landing found a real bug in the first cut of this fix**:
   "last-activity time" was originally just the worktree's own top-level
   directory mtime, which git only updates when a directory *entry* is
   added/removed/renamed — a process that keeps writing into files that
   already exist inside the worktree (the normal shape of a running
   check, e.g. appending to a log or overwriting an already-gitignored
   artifact file) never bumps that mtime, so a still-actively-used
   worktree could be force-removed once its checkout time alone crossed
   24h. canonical: `docs/issue-2383/reports/implementation/2026-08-25-hunt-worktree-age-prune.md`
   (warrant-hunter's report, this session, 2026-08-25) — includes a
   standalone repro script that creates a real worktree, appends to an
   existing nested file, then shows `_prune_worktrees` deleting it
   anyway under the pre-fix code.
   Fixed by adding `_worktree_last_activity(path)`, which takes the max
   mtime across the worktree's top directory **and every file/subdirectory
   under it** (`path.rglob("*")`), not just the top directory alone — a
   fresh write anywhere in the tree now correctly resets the clock.
   canonical: `lifecycle.py` `_worktree_last_activity()`, this commit.

Regression tests for both fixes are committed (not just inline smoke
tests) since this is a second gap found in the same area by the same
review process — `gates/test_clean_reconcile_safety.py` gained a new
`PruneWorktreesTest` class (5 methods: existence-prune, age-prune
reproducing the reviewer's 90-day-backdated case, actively-written
worktree survives despite an old top-dir mtime (reproducing the
warrant-hunter's finding above), fresh-worktree survives, primary
worktree never touched) and 3 methods in `tests/test_spawn_gate_wiring.py`
were rewritten to use the `spawn.ROOT`-redirect helper above.
acceptance: `python3 -m pytest gates/test_clean_reconcile_safety.py -q -n auto` — result:
```
....x...........                                                         [100%]
15 passed, 1 xfailed in 0.92s
```
acceptance: `python3 -m pytest tests/test_spawn_pipeline.py test/test_spawn_model_override.py gates/test_clean_reconcile_safety.py tests/test_spawn_gate_wiring.py -q -n auto -m "not slow"` — result:
```
.....................................................................x.. [ 45%]
........................................................................ [ 90%]
...............                                                          [100%]
158 passed, 1 xfailed in 1.25s
```
acceptance: `git log --oneline HEAD..origin/main | wc -l` after rebase — result:
```
0
```

## Next steps

None — `loop_state: landed`. The open findings above are filed for a
future session where still open, not left implicit — REQ-1c's
`roles/implementation.json` corruption open finding is resolved by this
CHANGES round.

amendments-reconciled: issuecomment-5407528172 reports the same mechanism
as item 2 under What was done above, quoted verbatim: "reproduced this
session: `tests/test_spawn_pipeline.py`'s `DryRunModelReflection`
class, method `test_config_only_output_reflects_model`, failed with a
UnicodeDecodeError (garbage/partial bytes) under `-n auto` full-suite
run, passed cleanly in isolation." canonical: `gh issue view 2383
--comments`, this session. Already covered by the same
`tempfile.TemporaryDirectory()` isolation applied to that test's class.
The comment's suggested alternative (make `ROLE_MODEL_CONFIG` itself
per-worktree/per-session) was not taken — isolating the test suite is the
narrower, zero-runtime-overhead fix consistent with the issue's
operator-frozen constraint (no added per-spawn overhead, no
consumer-tree pollution); the file staying a single shared path is
intentional per its own issue #60 design and out of this issue's scope to
redesign.

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
