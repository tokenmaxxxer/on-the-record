---
issue: 3118
role: test-depth-audit+experiment-trust+silent-failure-audit-b3d43cb1
author: test-depth-audit+experiment-trust+silent-failure-audit-b3d43cb1
skills: test-depth-audit (skill-repository(c05de12)), experiment-trust (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: true
code_under_review:
  - path: lifecycle.py
    sha: 0a6dc9ccaa5687edd05ac75d77b924c072125a63
  - path: spawn.py
    sha: 0a6dc9ccaa5687edd05ac75d77b924c072125a63
type: verification
breaking: false
verdict: pass — 4/4 acceptance checks Present, 4/4 must-nots Present (all independently reproduced this session), plus two open findings this session found that neither the builder's own record nor PR #3130 mention
loop_state: terminal
upstream:
  - path: docs/issue-3118/reports/implementation-blueprint+silent-failure-audit+test-derivation-c9ef1cc3.md
    sha: bc5f0ada957bddcb4928af6b050bac6f9a7e0b77
  - path: docs/issue-3118/reports/adversarial-review+defect-verification-independence-from-upstream-verdicts+silent-failure-audit-f68edefd.md
    sha: 54c1cf3275e4b824b0abc84a36e7031d35e97a8c
---

# issue-3118 — test-depth-audit+experiment-trust+silent-failure-audit-b3d43cb1 record

## What was done

Second independent, builder-blind verification of PR #3126 against issue #3118. Checked out separately from PR #3130 (the first verification): `gh pr view 3126 --json headRefName,headRefOid` — result: `headRefOid: 0a6dc9ccaa5687edd05ac75d77b924c072125a63`. `git fetch origin pull/3126/head:pr-3126-verify && git worktree add /tmp/verify-3118-pr3126 pr-3126-verify` (scratch, not the live checkout; removed via `git worktree remove --force` + `git branch -D` before this record was written).

All paths below under `tests/`, `gates/`, and the PR's own `docs/issue-3118/reports/implementation-blueprint...` are untracked on this session's own branch (`issue-3118/test-depth-audit+...`) — they exist only on PR #3126's branch at `0a6dc9ccaa5687edd05ac75d77b924c072125a63`, where every command below was actually run, inside `/tmp/verify-3118-pr3126`.

### Acceptance checks — all 4 run independently from `/tmp/verify-3118-pr3126`

- checked: `python3 -m pytest tests/test_orphan_sweep.py -q` — result:
```
27 passed in 0.91s
```
Present.
- checked: `python3 gates/probe_orphan_sweep_spares_live.py` — result: exit 0,
```
ok: live worktree survived
ok: live session log survived
ok: orphaned worktree removed
ok: orphaned session log removed
ok: report attributes the removal to the orphan, not the live pair
ok: empty environment reports zero candidates in every category
ok: --dry-run says explicitly there is nothing to remove
```
Present.
- checked: `python3 spawn.py sweep-orphans --dry-run 2>&1 | head -20` — result: 20 lines, each shaped `[dry-run] tmp-worktree: <path>  [<reason>; age <n>h]`. Present.
- checked: `python3 -m pytest tests/ -q` — result:
```
249 passed, 2 warnings in 10.51s
```
Present.
- checked (issue-comment's 5th acceptance line, run for completeness): `python3 -m pytest tests/test_orphan_sweep_portability.py -q` — result:
```
6 passed in 0.88s
```
- checked: `python3 -m pytest test/ -q` on the PR branch — result:
```
15 failed, 548 passed, 3 xfailed in 32.03s
```
same 15 failing node IDs as the PR description's own claim, all under `test_convention_equivalence.py` / `test_local_dependency_env.py` / `test_spawn_cross_family_skill_selection.py` / `test_spawn_artifact_skill_pairing.py` / `test_spawn_skill_judge_haiku_timeout_overlap.py`, none touching orphan-sweep code — pre-existing, owned by #3091.

derived: `python3 -m pytest tests/ -q` on this session's own branch (main, after PR #3130 merged, which does not include PR #3126's code) —
```
254 passed, 2 warnings in 10.06s
```
5 more than the PR-3126 branch's 249 — `254 - 249 = 5`. derived: `ls tests/ | grep orphan` on this session's own branch → empty output (confirms `tests/test_orphan_sweep.py` does not exist there — untracked on this branch — since PR #3126 is unmerged). derived: `git merge-base main pr-3126-verify` → `78fda1e03f028e1011f75ff31252a99d7f3a4316`; `git log --oneline main ^pr-3126-verify -- tests/` →
```
b9457ad1 issue-3095: attribute spawn-on-pr's park state to a repo (#3106)
871738e9 issue-3050: sanctioned two-artifact supersession shape + remote-reconciled failed-no-commit classification (#3086)
```
2 commits, landed on `main` after PR #3126 branched off, unrelated to issue #3118. Conclusion: ordinary merge-base staleness on an open PR — PR #3126's own tree is internally consistent at 249/249 — not a defect in the PR.

### Must-nots — all 4 independently constructed this session, not reused from PR #3130's or the builder's own fixtures

1. *Do not sweep by age alone.* canonical: `lifecycle.py:1652-1753` (`_scan_orphan_worktrees`/`_scan_orphan_workspaces`) and `lifecycle.py:1501-1523` (`_orphaned_sidecar_groups`), read at the PR-3126 head commit — every path checks `live`/PR status before age; `min_age_seconds` gates via `age_sec < min_age_seconds: continue`, a floor only. derived: `spawn._scan_orphan_worktrees([tmp1], live={owner_repo.resolve(): {"pid": os.getpid()}}, unreadable=[], now=time.time()+10_000_000, min_age_seconds=60)` against a fresh fixture at an absurdly old age — result: `[]` (survives). Present.
2. *Do not delete `/tmp/claude-1000` wholesale.* Independently built (not reusing the PR's own equivalent test) a `claude-1000/session-a/deep/nested/f.json` tree. derived: real (non-dry-run) `spawn.sweep_orphans(root, temp_roots=[root], now=time.time()+10_000_000, min_age_seconds=1, dry_run=False)` against it — result: `tmp_worktrees flagged: []`; the `claude-1000` dir, its nested file, and its top-level scratch file all still present afterward (checked via `.exists()` on each). `_worktree_admin_dir` requires a `.git` pointer FILE directly at a temp-root entry's own top level (`lifecycle.py:1630-1649`); a scratch namespace with no such pointer is never flagged and never walked below one level. Present.
3. *Do not make cleanup a step sessions are asked to perform.* derived: `grep -rln "sweep-orphans\|sweep_orphans" --include="*.py" --include="*.sh" --include="*.json" .` on the PR-3126 worktree, excluding `tests/`/`gates/`/`docs/` — result:
```
lifecycle.py
spawn.py
```
canonical: `spawn.py:2801-2802` (`if a.role == "sweep-orphans": return sweep_orphans_cli(...)`) — wired solely as a manually-invoked CLI subcommand, never called from `auto_sweep()`, a directive, or a session-end hook. Present.
4. *Do not gate the sweep behind a platform check that turns it off on macOS.* derived: `grep -n sys.platform lifecycle.py spawn.py` — result: no output (zero matches in either file). derived: `python3 -m pytest tests/test_orphan_sweep_portability.py -q` — result: `6 passed in 0.88s` (same run cited above). Present.

### Deep dive — cases a passing first verification (PR #3130) was least likely to construct

- *Recycled pid.* canonical: `lifecycle.py:707-715` (`_live_workspaces()`, pre-existing since commit `677b9d74a` on 2026-08-23 — confirmed via `git blame -L 707,715 lifecycle.py`, not touched by PR #3126) computes liveness as `_sp._alive(e.get("pid", 0))` alone — a bare `os.kill(pid, 0)` existence check, no identity cross-check. derived: constructed a roster entry whose `pid` is this session's own live pid (`os.getpid()`) but whose recorded `work` is a directory that pid does not actually own, fed as `live` into `spawn._scan_orphan_worktrees(..., now=time.time()+100_000, min_age_seconds=60)` — result: `[]`. The worktree survives forever: pid-exists alone keeps the owning workspace "live" regardless of whether that pid still owns it. This is the "never reclaims it" branch, not the "deletes live work" branch — the safe direction the issue text itself prioritizes ("the failure mode of an over-eager cleaner is worse than the disk it reclaims"). canonical: `roster.py:237-266` (`_session_looks_real()`) and `spawn.py:3612-3626` (`self_update_pull_cli()`, issue #2749/PR #2823) — this same codebase already found and fixed this exact pid-recycling hole for a sibling feature, and `sweep_orphans()` reuses the older `_live_workspaces_union()` primitive rather than `_session_looks_real()`. Logged as open finding 2 below; not a required must-not, errs safe.
- *Session alive, worktree already removed by something else.* derived: `spawn._scan_orphan_worktrees([tmp2], live={}, unreadable=[], now=time.time()+100_000, min_age_seconds=60)` against an already-empty temp root — result: `[]`, no exception.
- *Dead session, branch has an open unmerged PR.* derived: built a real git repo + branch, mocked `_pr_open_or_merged_for_branch` to return an OPEN PR dict — `spawn._scan_orphan_workspaces(...)` → `[]` (survives). Flipped the mock to return `None` (no open/merged PR) — result: correctly flagged with reason `no live pid, no open PR (branch issue-1/feature)`.
- *Permission-denied during real removal.* derived: mocked `_force_rmtree` to raise `PermissionError`; `spawn.sweep_orphans(..., dry_run=False)` recorded `removed=False, error="[Errno 13] Permission denied: ..."` on the item rather than raising; `spawn.sweep_orphans_cli(...)` printed the failure line and returned exit code `1`.
- *Paths with spaces / newlines.* derived: built worktree entries named `pr weird name verify` and `pr\nnewline-verify` under a `.git`-pointer-bearing owner directory named with spaces — both scanned and reported correctly (`pathlib`, no shell interpolation anywhere in the scan path).
- *Dry-run honesty, sampled against real ground truth on this host.* derived: `python3 spawn.py sweep-orphans --dry-run` produced 98 lines total. For `/tmp/check-runner-pr-nst9ico2` (labelled "no live pid"): `cat /tmp/check-runner-pr-nst9ico2/.git` → `gitdir: /tmp/pytest-of-jwjung/pytest-12625/test_worktree_for_ref_success_0/repo/.git/worktrees/check-runner-pr-nst9ico2`; `ls -ld` on that admin dir → exists, owned by a `pytest` tmp-repo never registered as a session workspace, so correctly absent from `live`. For `/tmp/core-353` and `/tmp/core-main` (labelled "owning checkout gone"): `ls -ld` on their admin dirs → both `그런 파일이나 디렉터리가 없습니다` (no such file or directory) — admin dir genuinely gone, matching the stated reason. Reasons are derived from live filesystem/roster state, not asserted strings.
- *Dry-run vs. real removal agreement.* derived: built a from-scratch fixture (a live-pid-owner worktree + a dead-pid-owner worktree, both under a scratch `tmproot`), ran `spawn.sweep_orphans(..., dry_run=True)` then `dry_run=False)` against the identical mocked `live` dict — dry-run listed exactly the dead-owner path; the real run removed exactly that path (confirmed `not orphan_wt.exists()`) and left the live pair untouched (confirmed `live_wt.exists()`).
- *Portability, independently re-verified rather than trusting the PR's own portability test.* derived: patched `os.path.exists` to raise `AssertionError` on any path containing `/proc` and ran `spawn._scan_orphan_worktrees(...)` plus `spawn._live_workspaces()` through it — no exception raised, confirming the sweep's own liveness path never reads `/proc`. derived: patched `tempfile.gettempdir()` to return a macOS-shaped `/var/folders/xy/mock-macos-tmp` and called `spawn._sweep_temp_roots()` — result: `[PosixPath('/var/folders/xy/mock-macos-tmp'), PosixPath('/tmp')]`, both roots present, not hardcoded to `/tmp` alone. derived: `sed -n '1601,1895p' lifecycle.py | grep -n subprocess` — result: exactly one call, `git rev-parse --abbrev-ref HEAD` inside `_scan_orphan_workspaces` (portable across GNU/BSD) — no `stat`/`find`/`du` shell-out anywhere in the sweep functions.

## Why

[[defect-verification-independence-from-upstream-verdicts]] (rule 1, rule 3: treat a prior Present verdict as a claim to re-test, re-derive rather than cite) governed the session's ordering: every check and must-not above was constructed and run before PR #3130's record was opened. Comparison, run only after this session's own gradings above were already fixed:
```
$ git show 54c1cf32:docs/issue-3118/reports/adversarial-review+defect-verification-independence-from-upstream-verdicts+silent-failure-audit-f68edefd.md | grep -c '\. Present\.'
8
```
PR #3130 independently reaches 8 Present gradings (4 checks + 4 must-nots) — the same 8 this session reached above, zero disagreement. Per rule 2 (deliberately include edge/negative paths a happy-path bias would skip), the "Deep dive" probes above target scenarios outside PR #3130's own description ("a real forked/reparented live-vs-dead-pid fixture", "a forced deletion failure injected directly") — recycled-pid identity, filesystem permission failure, and space/newline paths appear in neither that description nor PR #3126's own test-plan bullets.

[[silent-failure-audit]] was applied directly against the PR's own claimed fix (PR #3126 description: "`sweep_orphans_cli()` ... now surfaces per-item failures and returns non-zero on any"): traced all three per-category failure paths (`tmp_worktrees`, `workspaces`, `sidecars`) in `sweep_orphans()`/`sweep_orphans_cli()` (`lifecycle.py:1774-1895`) individually instead of accepting the PR description's single worked example as covering all three. That trace-forward is what surfaced open finding 1 below: the `sidecars` category's except-block never records `str(ex)`, unlike the other two.

[[test-depth-audit]] — derived: both commands below ran inside `/tmp/verify-3118-pr3126` against `tests/test_orphan_sweep.py` (untracked on this session's own branch; exists only at PR-3126 head `0a6dc9ccaa5687edd05ac75d77b924c072125a63`), applied instead of trusting the PR's stated pass count as proof of depth:
```
$ grep -c "^def test_" tests/test_orphan_sweep.py
27
$ grep -B1 -A15 "^def test_" tests/test_orphan_sweep.py | grep -c "assert "
39
```
39 assert statements across those 27 tests — a ratio of `39 / 27 ≈ 1.4` asserts per test. Every test read in the sample (worktree-admin-dir group, orphan-scan group, sweep-orchestration group, CLI-output group — the ranges `lines 57-146` and `lines 292-433` of that same untracked file) carries a Genuine Assertion on a specific value (a path list, a reason substring, a `removed` boolean, printed CLI text) — none read as Execution-Only or Mock-Dominated. Reading the test function `test_sweep_orphans_cli_surfaces_a_failed_deletion_not_silently` specifically (same untracked file, `lines 404-422`) — the test backing the PR's "silent-failure fix" claim — showed it exercises only the `tmp_worktrees` category's failure path via `mock.patch.object(spawn, "_force_rmtree", side_effect=OSError(...))`, never `workspaces` or `sidecars`: a Happy-Path-Only gap in exactly the category (`sidecars`) that turned out to have the real behavioral gap in open finding 1.

experiment-trust: not applicable — reviewed against issue #3118 and PR #3126's full text (issue body, both comments, PR description; read via `gh issue view 3118 --comments` and `gh pr view 3126`) and found no A/B experiment, variant comparison, or metric contrast anywhere; this is disk/process hygiene machinery with no such surface.

## What did not work

None.

## Upstream basis

- `docs/issue-3118/reports/implementation-blueprint+silent-failure-audit+test-derivation-c9ef1cc3.md` — untracked on this session's own branch; exists at PR #3126's commit `bc5f0ada957bddcb4928af6b050bac6f9a7e0b77`, read via `git show bc5f0ada:docs/issue-3118/reports/implementation-blueprint+silent-failure-audit+test-derivation-c9ef1cc3.md` inside the PR-3126 worktree — the builder's own record; read for orientation only, no claim in it taken as settled without independent re-derivation above.
- `docs/issue-3118/reports/adversarial-review+defect-verification-independence-from-upstream-verdicts+silent-failure-audit-f68edefd.md` at `54c1cf3275e4b824b0abc84a36e7031d35e97a8c` (PR #3130, already merged to this session's own branch — present, tracked) — canonical: `git show 54c1cf32 --stat` and the file itself, read directly on this session's own branch (see the `grep -c` comparison in "Why" above). The first verification's record; read after this session's own probes were run.
- `lifecycle.py`, `spawn.py` at PR #3126 head `0a6dc9ccaa5687edd05ac75d77b924c072125a63` — code under review; these paths exist and are tracked on this session's own branch too (pre-existing files), but the *content* cited throughout this record (line ranges, new functions) reflects the PR-3126 head commit, not this session's own branch's version of these files, since PR #3126 is unmerged.

## Open findings

1. **Sidecar-deletion failures lose their error message (low severity).** canonical: `lifecycle.py:1829-1836` at PR-3126 head:
   ```python
   for item in sidecars:
       failed_files = []
       for f in item["files"]:
           try:
               f.unlink()
           except OSError:
               failed_files.append(f)
       item["removed"] = not failed_files
   ```
   compared against the equivalent `tmp_worktrees`/`workspaces` except-blocks at `lifecycle.py:1815-1817` and `:1825-1827`, both of which do `item["error"] = str(ex)`. `sweep_orphans_cli`'s `_outcome_suffix()` (`lifecycle.py:1857-1862`) falls back to the literal string `"알 수 없는 오류"` ("unknown error") when `item.get("error")` is absent. derived: forced `Path.unlink` to raise `PermissionError(13, "Permission denied", ...)` on a sidecar file, then ran `spawn.sweep_orphans(wb, ..., dry_run=False)` followed by `spawn.sweep_orphans_cli(wb, dry_run=False)` — result:
   ```
   session-log: issue-1-x (1 files)  [orphaned sidecar (paired workspace gone); age 277.8h]  ** 삭제 실패: 알 수 없는 오류 **
   [sweep-orphans] 지움 1건 (성공 0, 실패 1)
   exit code: 1
   ```
   The failure itself is not silently absorbed (correct exit code, correct visibility), but the actual OS-level reason is discarded rather than surfaced — a Handled-but-degraded-diagnostics gap, not a Silently-Absorbed one. The PR's own test for this exact claim (`test_sweep_orphans_cli_surfaces_a_failed_deletion_not_silently`, see "Why" above) only exercises the `tmp_worktrees` path, so this gap was not caught by the PR's own suite. Resolution path: add `item["error"] = str(ex)` inside the sidecar except-block, matching the other two categories — a one-line fix; does not block any acceptance check or must-not.
2. **Recycled-pid liveness gap (informational, not introduced by this PR).** See "Deep dive" above for the full reproduction. `_live_workspaces()`/`_live_workspaces_union()` predate PR #3126 (confirmed via `git blame`, see Deep dive) and determine liveness via bare `_alive(pid)`, with no `/proc`-cwd identity cross-check of the kind `roster._session_looks_real()` already performs for a sibling feature. Effect on `sweep_orphans()`: a workspace whose registered pid has been recycled to an unrelated process is treated as live forever, so its `/tmp` worktree/logs are never reclaimed — errs toward the safe side the issue text explicitly prioritizes, so it violates no stated must-not, but the sweep's actual reclaim rate is below 100% of true orphans in that window. Resolution path, if wanted: have `sweep_orphans()`'s liveness lookup use `_session_looks_real()`-style cwd cross-checking instead of `_live_workspaces_union()`'s plain `_alive()`, mirroring `self_update_pull_cli()` (issue #2749) — a design decision for a follow-up, not required by issue #3118's stated acceptance.

Both findings are candidates for a small follow-up issue; neither is required for issue #3118's own acceptance — acceptance: all four checks listed in the "Acceptance checks" section above — result: all 4 Present, and all 4 must-nots in the "Must-nots" section above — result: all 4 Present.

## Next steps

loop_state: terminal — no further action required from this session. A follow-up issue for the two open findings above is optional and left to the team.

skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; see "Deep dive" and "Why" sections above for the independent re-derivation this skill required
skill-verdict: silent-failure-audit — applied: invoked; see "Why" and "Open findings" §1 above for the trace-forward this skill required
skill-verdict: test-depth-audit — applied: invoked; see "Why" section above for the assertion-density sampling this skill required
skill-verdict: experiment-trust — not-applicable: issue #3118 and PR #3126 are disk/process hygiene machinery with no A/B experiment, variant comparison, or metric contrast anywhere in scope
