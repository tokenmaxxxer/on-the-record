---
issue: 2383
role: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2383/reports/implementation.md
    sha: ef762a9fd5e1b4d1424f2bdf168b887a2d369a43
  - path: spawn.py
    sha: 18ec4c5501b4d113519c61e039fd4ec3c002c8ed
  - path: lifecycle.py
    sha: 18ec4c5501b4d113519c61e039fd4ec3c002c8ed
subject: PR #2389 (issue-2383, "fix(issue-2383): gitignore scratch, dedupe origin/HEAD refresh, prune stale worktrees on clean"), branch issue-2383/implementation, commits 18ec4c5501b4d113519c61e039fd4ec3c002c8ed / ef762a9fd5e1b4d1424f2bdf168b887a2d369a43, merge-base f63bb2e1ed061984d16dcbb9723b9bf0a3f71df3
test: independent re-derivation of every falsifiable claim in docs/issue-2383/reports/implementation.md (untracked in this tree — lives on branch issue-2383/implementation at commit ef762a9fd5e1b4d1424f2bdf168b887a2d369a43) plus this PR's mergeability against the current main tip — commands and outputs below, all run in a fresh git worktree of the branch, never the authoring session's pasted transcripts taken as given
result: failed
assertedBy: execution-observation session for issue-2383, independent of PR #2389's authoring (implementation) session
---

# issue-2383 — execution-observation record

## What was done

canonical: this session's own `git worktree add /tmp/exec-obs-2383-1773500
origin/issue-2383/implementation` (detached at `ef762a9f`), plus fresh,
independently-authored Python repro scripts (not copied from the PR's own
pasted scripts) — never the authoring session's claims taken as given.

### Claim 1 — `.gitignore` gains three scratch entries (acceptance check 1, gitignore half)

acceptance: `git diff origin/main HEAD -- .gitignore` (branch worktree) — result:
```
+.on-the-record/check-run-artifact.json
+.on-the-record/directive/
+role_model.txt
```
Matches docs/issue-2383/reports/implementation.md's claim exactly
(untracked in this tree — lives on branch issue-2383/implementation at
commit ef762a9f).

canonical: this observation session's own `git status` at start (this
branch, `issue-2383/execution-observation`) independently listed
untracked `.on-the-record/directive/*.md` (three files) before any edit
this session made — the same scratch class, reproduced for a different
session.

### Claim 2 — `tests/test_spawn_pipeline.py` xdist race isolated to a tempdir (acceptance check 1, process half)

acceptance: `git diff origin/main HEAD -- tests/test_spawn_pipeline.py`
(branch worktree) — result (excerpt, `SpawnCmd.setUp`):
```
+    def setUp(self):
+        self._role_model_tmpdir = tempfile.TemporaryDirectory()
+        self._saved_role_model_config = spawn.ROLE_MODEL_CONFIG
+        spawn.ROLE_MODEL_CONFIG = Path(self._role_model_tmpdir.name) / "role_model.txt"
+
+    def tearDown(self):
+        spawn.ROLE_MODEL_CONFIG = self._saved_role_model_config
+        self._role_model_tmpdir.cleanup()
```
same class-level isolation added to `DryRunModelReflection`; all seven
methods' manual save/restore and `isolated_role_model_config()`
context-manager calls dropped in the same diff.

acceptance: `python3 -m pytest tests/test_spawn_pipeline.py
test/test_spawn_model_override.py gates/test_clean_reconcile_safety.py -q
-n auto` (branch worktree, fresh run this session) — result:
```
102 passed, 1 xfailed in 37.48s
```
matches docs/issue-2383/reports/implementation.md's cited `102 passed, 1
xfailed` exactly (untracked in this tree — lives on branch
issue-2383/implementation at commit ef762a9f; wall-clock differs, shared-
host variance expected, not a correctness signal).

### Claim 3 — `git worktree prune` swept from `spawn.py clean` (acceptance check 2)

acceptance: `git diff origin/main HEAD -- lifecycle.py` (branch
worktree) — result (excerpt):
```
+def _prune_worktrees(repo: Path) -> None:
+    if not (repo / ".git").exists():
+        return
+    before = subprocess.run(["git", "-C", str(repo), "worktree", "list"], ...).stdout.splitlines()
+    ...
+    pruned = subprocess.run(["git", "-C", str(repo), "worktree", "prune", "-v"], ...)
+
+def roster_clean(wb: Path, issue: int | None, repo: Path | None = None) -> int:
+    if repo is not None:
+        _prune_worktrees(repo)
```
`git diff origin/main HEAD -- spawn.py` (branch worktree) — result
(excerpt): `-        return roster_clean(_workspace_base(), a.issue)` /
`+        return roster_clean(_workspace_base(), a.issue,
Path(a.cwd).resolve())` — confirms the `clean` call site wiring.

acceptance: independent smoke test, own script against a real throwaway
git repo (not the PR's own script) — result:
```
EDGE1 pass: no-extra-worktree repo did not crash
worktree 목록 (정리 전 2개):
  /tmp/tmptfp93s37/repo       d956057 [master]
  /tmp/tmptfp93s37/linked-wt  d956057 (detached HEAD) prunable
worktree prune: Removing worktrees/linked-wt: gitdir file points to non-existent location
EDGE2 pass: orphaned worktree pruned
EDGE3 pass: non-git path silently skipped, no crash
```
`_prune_worktrees` reproduces the record's claimed behavior (EDGE2) and
additionally holds on two negative paths the PR's own single smoke test
never exercised: a repo with nothing to prune (EDGE1), and a non-git
directory (EDGE3).

### Claim 4 — stale `origin/HEAD` refreshed on workspace-reuse paths (acceptance check 3, #2379 mechanism)

acceptance: `git diff origin/main HEAD -- spawn.py` (branch worktree) —
result (excerpt, both reuse branches of `issue_workspace()`):
```
+def _set_origin_head(work_dir: str) -> subprocess.CompletedProcess:
+    return subprocess.run(["git", "-C", work_dir, "remote", "set-head", "origin", "-a"], ...)
...
-        _fetch_or_halt(str(src), "재사용 워크스페이스")
+        _fetch_or_halt(str(src), "재사용 워크스페이스",
+                       after=lambda: _set_origin_head(str(src)))
...
-        _fetch_or_halt(str(work), "재사용 워크스페이스")
+        _fetch_or_halt(str(work), "재사용 워크스페이스",
+                       after=lambda: _set_origin_head(str(work)))
```
Previously only the new-clone path refreshed `origin/HEAD`.

canonical: `pipeline.py:855-859` (branch worktree, read directly) —
```
    r = _sp._run_net(["git", "-C", work_dir, "fetch", "-q", "origin"], label, env=_sp._git_env())
    if after is not None:
        after()
    if r.returncode != 0 or "failed to store" in r.stderr:
        sys.exit(...)
```
`after()` runs unconditionally, before the fail-closed halt check —
confirms the wiring is functionally live (a workspace-reuse call really
does invoke `_set_origin_head` every time), not just present in source.

acceptance: independent smoke test, own two-repo git fixture (origin +
clone, renamed default branch, not the PR's own script) — result:
```
before fix, origin/HEAD symref (stale): origin/trunk
after _set_origin_head: origin/main
PASS: _set_origin_head refreshes stale-but-present origin/HEAD (independent repro)
PASS (edge case): _set_origin_head also handles an absent origin/HEAD symref
```
second PASS line is an edge case (`origin/HEAD` symref entirely absent,
not merely stale) the PR's own smoke test did not cover.

### Claim 5 — two open findings left un-root-caused

acceptance: `grep -rn "roles/implementation" --include=*.py .` (branch
worktree, whole repo including the nested `on-the-record/` bundle) —
result:
```
gates/test_closes_gate_ci.py:832:    `roles/implementation.json` 은 ...
gates/ci.py:414:    ... `roles/implementation.json` 의
gates/gates.py:288:# CLAIM-CHECK: enum-subset roles/implementation.json:record_fields.loop_state ...
test/test_spawn_role_skill_resolution.py:133: ... 실제 roles/implementation.json 스펙을 읽는다
test/test_spawn_skills_mount.py:140: ... 실제 roles/implementation.json 스펙을 읽는다
```
zero write sites — only read/spec-assertion sites. Independently
corroborates docs/issue-2383/reports/implementation.md's own negative
finding (untracked in this tree — lives on branch
issue-2383/implementation at commit ef762a9f) rather than taking it on
faith, per skill defect-verification-independence-from-upstream-verdicts
(re-derived rather than cited; not-reproduced tracked with the same
rigor as reproduced).

acceptance: `grep -n "def rulebook_version" spawn.py roster.py
pipeline.py board.py` (branch worktree) — result: no match (empty). This
independently confirms `tests/test_gates.py`'s
`t_rulebook_version_is_recorded` calls a `spawn.rulebook_version(...)`
that no longer exists on any of those modules — the test can only be
masked-passing dead code, not a live corruption path, matching the
record's own dead-code claim.

Both open findings independently corroborate as genuinely unresolved,
not merely under-searched.

### Claim 6 (not asserted by the PR, found by this session) — PR #2389 does not currently merge cleanly into main

acceptance: `gh pr view 2389 --json mergeable,mergeStateStatus` — result:
```
{"mergeable":"CONFLICTING","mergeStateStatus":"DIRTY"}
```

acceptance: `git merge --no-commit --no-ff origin/main` (branch
worktree, `ef762a9f`) — result:
```
자동 병합: spawn.py
충돌 (내용): spawn.py에 병합 충돌
자동 병합이 실패했습니다. 충돌을 바로잡고 결과물을 커밋하십시오.
```
`git diff --name-only --diff-filter=U` — result: `spawn.py`. `git merge
--abort` run immediately after, leaving no trace in this observation's
own tree.

derived: `git log --oneline f63bb2e1..origin/main` — result:
```
ce7fadd7 issue-2293: degenerate-task admission guard + adhoc isolation + timestamped log
75390fc3 issue-2291: durable spawn-attempt trace + watchdog pre-workspace halt visibility
14e1042f issue-2293: re-review of PR #2368's CHANGES-round fix (REQ-B Incorrect -> Present)
1addbe9e issue-2291: re-review of PR #2366's CHANGES-round fix (R2/R4 Incorrect -> Present)
```
4 commits — the branch's own merge-base (`f63bb2e1`) is 4 commits behind
the current main tip (`ce7fadd7`); `75390fc3` and `ce7fadd7` both land
`spawn.py` changes (`_record_spawn_attempt`/`_record_spawn_outcome`,
`--force-adhoc-task`, `_admission_check_degenerate_task`) in the same
`main()`/`_spawn_one()`/`ADMISSION_CHECKS` regions this PR's own
`_spawn_one()`-signature and `main()`-body edits touch — that overlap is
the conflict.

derived: `git merge-base --is-ancestor f63bb2e1 origin/issue-2383/implementation`
(branch worktree) — result: exit 0 (true) — the merge-base is a genuine
ancestor of both branch and main, so this is ordinary unrebased-branch
drift, not a repeat of #2379's phantom-diff corrupted merge-base. It is
still a real, currently-reproducible landing blocker for this PR as
opened: merging it as-is, or resolving the conflict carelessly, risks
silently reverting issue-2291's and issue-2293's landed work — the same
failure shape (a later process silently clobbering earlier landed work)
issue #2383's acceptance check 1 is about, at the git layer instead of
the filesystem layer.

## Why

skill-verdict: defect-verification-independence-from-upstream-verdicts —
applied: canonical: Claim 5 above, this same record — the two open
findings were re-derived via this session's own fresh `grep` commands
rather than cited from docs/issue-2383/reports/implementation.md's
"not found" framing, and Claims 3/4's own smoke tests each add an edge
case beyond the PR's own script.

canonical: ef762a9fd5e1b4d1424f2bdf168b887a2d369a43:docs/issue-2383/reports/implementation.md:11
(`verdict: pass`, `loop_state: landed`) — the record this session set out
to independently test rather than accept on the strength of that
frontmatter. Every claim above was re-derived from the branch's own
diff/behavior and from freshly authored repro scripts, not from
re-running or citing the PR's own pasted scripts/output. Mergeability
against the current main tip was checked (Claim 6) because it is the
most basic falsifiable fact about whether this executable artifact, as
it stands on its branch right now, can actually be delivered, and it
cannot without further work.

## Upstream basis

- docs/issue-2383/reports/implementation.md, PR #2389, branch
  issue-2383/implementation (untracked in this tree). sha:
  ef762a9fd5e1b4d1424f2bdf168b887a2d369a43
- spawn.py, lifecycle.py, .gitignore, tests/test_spawn_pipeline.py, same
  branch (untracked in this tree). sha:
  18ec4c5501b4d113519c61e039fd4ec3c002c8ed
- main tip at observation time, `ce7fadd78f49e685bcca0ad451aafb96f6d28a28`
  ("issue-2293: degenerate-task admission guard + adhoc isolation +
  timestamped log") — the mergeability target for Claim 6. sha:
  ce7fadd78f49e685bcca0ad451aafb96f6d28a28

## Open findings

- Claim 6: PR #2389 does not currently merge cleanly into main —
  reproduced, `mergeable: CONFLICTING`, real content conflict in
  `spawn.py` against the current main tip. canonical: Claim 6 above,
  this same record — `gh pr view 2389 --json mergeable,mergeStateStatus`
  and `git merge --no-commit --no-ff origin/main`. Resolution path:
  whoever lands this PR needs to rebase/merge `origin/main` into
  `issue-2383/implementation`, resolve the `spawn.py` conflict by hand
  (both sides' changes are real and should both survive —
  `_record_spawn_attempt`/`_admission_check_degenerate_task` from main,
  `_set_origin_head`/admission-gate reordering from this branch), re-run
  the acceptance test command from Claim 2, and update the PR before it
  can land.
- `roles/implementation.json`'s corrupting process — independently
  corroborated as still unresolved. canonical: Claim 5 above, this same
  record — `grep -rn "roles/implementation" --include=*.py .` found zero
  write sites, and `grep -n "def rulebook_version" spawn.py roster.py
  pipeline.py board.py` found no match. Resolution path unchanged from
  docs/issue-2383/reports/implementation.md: capture the corrupting
  process's identity (parent PID, cwd, argv) live, at the moment it's
  next caught mid-write — static grepping has now failed twice.
- `/tmp/claude-*/scratchpad/*` worktrees' source — not independently
  re-swept this session (no new angle beyond the record's own sweep of
  every `git worktree add` call site in both repos). Resolution path
  unchanged: likely produced by the Claude Code harness itself or a tool
  outside both repos' own audit reach.

## Next steps

None — loop_state handed-off is terminal for this role. The rebase
needed to resolve Claim 6 is out of this role's own write scope; it
belongs to whichever session next touches issue-2383/implementation.

## What did not work

None.
