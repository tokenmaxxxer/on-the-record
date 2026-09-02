---
issue: 3118
role: implementation-blueprint+silent-failure-audit+test-derivation-c9ef1cc3
author: implementation-blueprint+silent-failure-audit+test-derivation-c9ef1cc3
skills: implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review:
  - path: lifecycle.py
    sha: bc5f0ada957bddcb4928af6b050bac6f9a7e0b77
  - path: spawn.py
    sha: bc5f0ada957bddcb4928af6b050bac6f9a7e0b77
type: feature
breaking: false
verdict: pass — all four issue-3118 acceptance checks pass, re-run against bc5f0ada957bddcb4928af6b050bac6f9a7e0b77 (see "How you will know it worked")
loop_state: landed
upstream:
  - path: bc5f0ada957bddcb4928af6b050bac6f9a7e0b77
    sha: bc5f0ada957bddcb4928af6b050bac6f9a7e0b77
---

# issue-3118 — implementation-blueprint+silent-failure-audit+test-derivation-c9ef1cc3 record

## What was done

canonical: `gh issue view 3118 --repo tokenmaxxxer/on-the-record --comments` output, read at session start — main body measured 193 `/tmp` worktree directories (only 3 known to `git worktree list`), 236 session logs never swept, and 68 `_workspace_base()` workspaces older than a day whose PR never merged; the comment added the cross-platform-portability requirement (`/proc` non-existence on macOS, `$TMPDIR` vs `/tmp`, no platform-gated no-op).

Delivered `spawn.py sweep-orphans [--dry-run]`, committed at `bc5f0ada957bddcb4928af6b050bac6f9a7e0b77`. Build-now bypass — derived: `echo "CORE_BUILD_NOW=$CORE_BUILD_NOW"` → `CORE_BUILD_NOW=1` at session start — so this record covers the single delivery PR, no separate phase-1 proposal round.

New machinery lands in `lifecycle.py` (following that file's own documented "extraction 7/N" convention — flat functions, `_sp.`-mediated cross-function calls for anything a test might monkeypatch, alphabetically aliased into `spawn.py`'s namespace) and is wired into `spawn.py`'s `main()` as the `sweep-orphans` role, reusing the pre-existing `--dry-run` flag:

- `_sweep_temp_roots()` — resolves `[tempfile.gettempdir(), Path("/tmp")]`, deduplicated, pure `tempfile`/`pathlib`, no `stat`/`find`/`du` subprocess.
- `_worktree_admin_dir()` / `_scan_orphan_worktrees()` — category 1, the `/tmp` worktrees the issue measured. Reads the `.git` pointer file `git worktree add` writes back to its admin dir (`<owner-repo>/.git/worktrees/<name>`), and asks whether `owner-repo` is a currently pid-alive session workspace via `_live_workspaces_union()` (the same roster lookup `_workspace_clean_state()` uses elsewhere in this file). A plain `.git` directory (a full clone, not a worktree) has no such pointer and is left out of scope rather than guessed at.
- `_scan_orphan_workspaces()` — category 3 (workspaces whose branch never merged). Delegates to the existing `_workspace_clean_state()` for the live/dirty/unknown judgment, then adds a second, tighter, on-demand signal on top of `auto_sweep()`'s 14-day age fallback: a branch with no OPEN or MERGED PR (`board._pr_open_or_merged_for_branch()`) has nothing left to protect, gated on a `gh` call that actually succeeded (`_pr_list_call_ok()`) so an API hiccup reads as "unknown," never as "no PR."
- `_sidecar_groups()` / `_orphaned_sidecar_groups()` — category 2 (orphaned session-log sidecars), extracted out of the pre-existing `_prune_orphaned_sidecars()` (issue #2443) so `sweep_orphans()`'s tighter on-demand threshold and the passive 14-day sweep share one selection rule instead of risking silent divergence.
- `sweep_orphans()` — orchestrates all three scans, gated on `_orphan_min_age_seconds()` (default 3600s, `MUSTER_ORPHAN_MIN_AGE_SECONDS` override) as a floor against a create-time race, never as the sole trigger; when not `dry_run`, actually removes (via `_force_rmtree()` for worktrees, the existing `_delete_workspace()` for workspaces, `Path.unlink()` for sidecars) and records per-item `removed`/`error` outcomes rather than raising.
- `sweep_orphans_cli()` — the `--dry-run` entry point.

New test/gate files, all committed at `bc5f0ada957bddcb4928af6b050bac6f9a7e0b77`: `tests/test_orphan_sweep.py`, `tests/test_orphan_sweep_portability.py`, `gates/probe_orphan_sweep_spares_live.py`. Case counts — derived: `python3 -m pytest tests/test_orphan_sweep.py -q` → `27 passed in 0.86s`; `python3 -m pytest tests/test_orphan_sweep_portability.py -q` → `6 passed in 0.78s`.

`tests/test_orphan_sweep.py` covers `_worktree_admin_dir`/`_scan_orphan_worktrees`/`_scan_orphan_workspaces` (dead/live owner, admin-dir-gone, age-floor gating, unreadable-roster conservatism, plain-clone out-of-scope, the `/tmp/claude-1000`-shaped scratch-namespace must-not, a `sys.platform="darwin"` regression guard) and `sweep_orphans()`/`sweep_orphans_cli()` orchestration (dry-run vs real removal, live-pair survival, the symmetric negative, the CLI failure-surfacing fix below). `tests/test_orphan_sweep_portability.py` covers liveness true/false without touching `/proc` (`os.path.exists` patched to raise on any `/proc` path), the same check wired into the worktree scan, and `_sweep_temp_roots()` following a mocked `tempfile.gettempdir()` rather than a hardcoded `/tmp`, plus literal-`/tmp` inclusion and dedup. `gates/probe_orphan_sweep_spares_live.py` builds a real live session's worktree+log pair (owner repo live via `_live_workspaces_union()`, current pid) alongside a real orphaned pair (dead pid via fork/exit/reap), runs `sweep_orphans()` for real, and asserts the live pair survives and the orphan pair is gone, plus the symmetric negative on a second, empty scratch environment.

canonical: this session's own re-run — `git worktree add /tmp/verify-3118-main bc5f0ada957bddcb4928af6b050bac6f9a7e0b77~1` (the pre-issue-3118 commit `78fda1e0`), copied the probe script in, ran it there — result: `FAIL: spawn.sweep_orphans does not exist -- this is exactly the gap issue #3118 reports: no mechanism a --dry-run could inspect`, exit 1. Confirms the probe genuinely fails against unmodified `main`.

## Why

canonical: `gh issue view 3118 --repo tokenmaxxxer/on-the-record --comments` output (read before designing, per the task's own instruction).

Three design decisions, each tied to a must-not from that issue text:

1. **Liveness via the owning checkout, not the `/tmp` directory's own age.** The issue's own numbers (cited in "What was done" above) explain why `git worktree prune`/`auto_sweep()` can't see the orphans: they were registered (at creation time) against the verification session's own throwaway workspace, not the canonical repo — and that throwaway workspace is usually the first thing to get cleaned up. Rather than inventing a new cooperative-registration mechanism (which the issue's must-not rules out — "do not make cleanup a step sessions are asked to perform"), the sweep reads back the `.git` pointer file `git worktree add` *already* writes on its own, and asks the existing roster (`_live_workspaces_union()`) whether the owner is still alive. No verification-session brief has to change.
2. **Portability per the issue's cross-platform comment.** `/proc/<pid>` does not exist on macOS — the sweep never touches it; liveness comes entirely from `_live_workspaces_union()` → roster `_alive()` → `os.kill(pid, 0)`, pinned by `tests/test_orphan_sweep_portability.py` patching `os.path.exists` to raise on any `/proc` path. Temp-root resolution goes through `tempfile.gettempdir()` (macOS: `$TMPDIR`/`/var/folders/...`) *and* the literal `/tmp` (this session's own verification briefs write `/tmp/...` paths directly, so both may hold orphans on a Mac) — no `sys.platform` branch anywhere in the sweep path. derived: `python3 -m pytest tests/test_orphan_sweep.py::test_no_platform_gate_disables_the_sweep_on_darwin -q` → `1 passed`.
3. **Never touch `/tmp/claude-1000` as a unit.** The scan only resolves a `.git` pointer file directly at a temp-root entry's own top level (`entry / ".git"`, one level under the temp root, never recursed) — a scratch namespace with no such pointer is never flagged and its contents are never even walked. derived: `python3 -m pytest tests/test_orphan_sweep.py::test_orchestrator_scratch_namespace_is_never_touched_or_recursed_into -q` → `1 passed`.

**Silent-failure-audit finding, found and fixed within this same session.** Skill invoked (Skill tool, `silent-failure-audit`) against the new code before calling it done. Original `sweep_orphans_cli()` printed the same `[reason; age]` line for every candidate regardless of whether `sweep_orphans()`'s real-removal pass had recorded `item["removed"] = False` / `item["error"]` for it — a failed `rmtree`/`unlink` would look identical to a successful one in the operator-facing output, and the CLI always returned 0. Root cause traced to a second, independent bug in the same code path: `sweep_orphans()`'s removal loop called the local `_force_rmtree()` directly instead of through `_sp._force_rmtree()`, breaking this file's own `mock.patch.object(spawn, ...)` test-patchability convention that every other cross-function call in `auto_sweep()`/`roster_clean()` a test might reasonably intercept follows. Reproduced with a failing test first (patched `spawn._force_rmtree` to raise `OSError`; with the direct call, the CLI still printed a success-shaped line and returned 0), then fixed both: the removal call now goes through `_sp._force_rmtree()`, and `sweep_orphans_cli()` prints an explicit `** 삭제 실패: <error> **` suffix per failed item and returns 1 if any real deletion failed. derived: `python3 -m pytest tests/test_orphan_sweep.py::test_sweep_orphans_cli_surfaces_a_failed_deletion_not_silently -q` → `1 passed`.

**implementation-blueprint verdict.** Skill invoked (Skill tool). `python3 <skill-dir>/scripts/prep.py classify --surface backend --external yes --logic crud --asynchronous no` → routed to the `library` archetype (external callers: the CLI operator and the tests that `import spawn`). Gate: "public surface smaller than the implementation, no internal type in a public signature." The actual placement — two public entry points (`sweep_orphans`, `sweep_orphans_cli`) against ~10 `_`-prefixed internal helpers, plain `Path`/`bool`/`float`/`dict` types on the public signatures, no new module or class — already satisfies that gate by following `lifecycle.py`'s own pre-existing flat-module convention (every sibling sweep function — `auto_sweep`, `sweep_temp_repos`, `roster_clean`, `_prune_orphaned_sidecars` — already lives there the same way); introducing a new module boundary for one more function family would have violated the tool's own "Conway: one owner — collapse elaborate module boundaries" note. No restructuring applied.

**test-derivation verdict.** Skill invoked (Skill tool) to build a traceability matrix from the issue's 7 acceptance/must-not requirements against the tests already written. Found two thin spots — no test proved the `/tmp/claude-1000`-shaped scratch namespace is left alone, and no test proved the sweep path has no `sys.platform` no-op branch — and one under-specific assertion (the CLI-format test checked the reason text but not that the literal word "age" appears in output, which is the issue's own acceptance wording). Added the two tests cited in points 2-3 above, and strengthened the existing CLI-format test — derived: `python3 -m pytest tests/test_orphan_sweep.py::test_sweep_orphans_cli_lists_each_candidate_with_a_reason -q` → `1 passed`.

## What did not work

None — the implementation matched the design from the first working version, aside from the silent-failure-audit finding described above, which was found and fixed within this same session rather than being an abandoned approach. derived: `git log --oneline -3` on this branch — result:
```
bc5f0ada issue-3118: add spawn.py sweep-orphans for /tmp worktree, workspace, and session-log orphan reclaim
78fda1e0 issue-3095: rebase PR #3106 onto origin/main, record the rebase session (#3112)
7ee16612 issue-3083: fix hooks.json additive guard and respawn-gate debounce test gap (#3089)
```
a single implementation commit on top of this branch's prior tip, no revert/redo commits.

## Upstream basis

derived: `git log --all --diff-filter=A -- docs/issue-3118` (run before this record's own commit) — empty; no prior docs/issue-3118 artifact existed before this session. Upstream input was the GitHub issue itself, read via `gh issue view 3118 --repo tokenmaxxxer/on-the-record --comments` before any design decision — see the canonical citation and requirement summary already given in "What was done" and "Why" above, not repeated here. The code this record reviews is committed at `bc5f0ada957bddcb4928af6b050bac6f9a7e0b77` — derived: `git rev-parse HEAD` on this branch → `bc5f0ada957bddcb4928af6b050bac6f9a7e0b77`.

## Open findings

None open. The one finding surfaced during this session (the CLI's silent deletion-failure gap, see "Why" above) was fixed in the same commit (`bc5f0ada957bddcb4928af6b050bac6f9a7e0b77`) and has a regression test — derived: `python3 -m pytest tests/test_orphan_sweep.py::test_sweep_orphans_cli_surfaces_a_failed_deletion_not_silently -q` → `1 passed`.

## Next steps

None — `loop_state: landed`. This is a delivery PR; per pr-preflight.sh guidance its trailer is `Closes #3118`, since this session delivers the issue's full acceptance surface rather than a partial/`Advances` delivery.

## How you will know it worked

acceptance: `bash -c "python3 -m pytest tests/test_orphan_sweep.py -q"` — result:
```
27 passed in 0.86s
```

acceptance: `bash -c "python3 gates/probe_orphan_sweep_spares_live.py"` — result:
```
ok: live worktree survived — /tmp/probe-orphan-sweep-uk3w20ni/tmp-root/pr-live-verify
ok: live session log survived — /tmp/probe-orphan-sweep-uk3w20ni/work/issue-1-implementation-live.session.20260101T000000.999998.log
ok: orphaned worktree removed — /tmp/probe-orphan-sweep-uk3w20ni/tmp-root/pr-orphan-verify
ok: orphaned session log removed — /tmp/probe-orphan-sweep-uk3w20ni/work/issue-2-implementation-dead.session.20260101T000000.999999.log
ok: report attributes the removal to the orphan, not the live pair
ok: empty environment reports zero candidates in every category
ok: --dry-run says explicitly there is nothing to remove
ok
```
exit code 0 — derived: `python3 gates/probe_orphan_sweep_spares_live.py; echo "EXIT=$?"` → `EXIT=0`.

acceptance: `bash -c "python3 spawn.py sweep-orphans --dry-run 2>&1 | head -20"` — result: prints real candidates from this machine's own accumulated state, ending in a total line:
```
[dry-run] workspace: /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-3059-test-derivation+silent-failure-audit-40945f98  [no live pid, no open PR (branch issue-3059/test-derivation+silent-failure-audit-40945f98); age 2.9h]
[sweep-orphans] 지울 후보 97건
```

acceptance: `bash -c "python3 -m pytest tests/ -q"` — result:
```
249 passed, 2 warnings in 10.48s
```
216 pre-existing + 33 new (27 in `tests/test_orphan_sweep.py` + 6 in `tests/test_orphan_sweep_portability.py`) = 249 — derived: `python3 -m pytest tests/test_orphan_sweep.py tests/test_orphan_sweep_portability.py -q` → `33 passed`. The 2 warnings are pre-existing `pinned-fixture-divergence` (issue #3019) noise, unrelated to this change.

extra: `bash -c "python3 -m pytest tests/test_orphan_sweep_portability.py -q"` (issue's additional acceptance line from the cross-platform comment) — result:
```
6 passed in 0.78s
```

`test/` baseline, reported separately per the spawning task's own instruction (owned by #3091, not this issue) — derived: `python3 -m pytest test/ -q` → `15 failed, 548 passed, 3 xfailed in 32.36s`. Same 15-failure count as the spawning task's own stated baseline ("test/ has 15 pre-existing failures owned by #3091"); this session touched no file under `test/`.

## skill-verdict

skill-verdict: implementation-blueprint — applied: invoked; ran `classify`/`recommend` against the placement decision (flat functions in `lifecycle.py`, two public entry points) before calling the structure final — canonical: this record's own "Why" section above, where the `classify` command and its output are quoted verbatim.
skill-verdict: silent-failure-audit — applied: invoked; audited every new `try`/`except` in `lifecycle.py`'s sweep-orphans machinery, found `sweep_orphans_cli()` silently absorbing per-item deletion failures into an unused report field, fixed it, added a regression test — derived: `python3 -m pytest tests/test_orphan_sweep.py::test_sweep_orphans_cli_surfaces_a_failed_deletion_not_silently -q` → `1 passed`.
skill-verdict: test-derivation — applied: invoked; built a traceability matrix from the issue's 7 acceptance/must-not requirements to the existing test files, found two thin spots and one under-specific assertion, added two tests and strengthened one — derived: `python3 -m pytest tests/test_orphan_sweep.py::test_orchestrator_scratch_namespace_is_never_touched_or_recursed_into tests/test_orphan_sweep.py::test_no_platform_gate_disables_the_sweep_on_darwin -q` → `2 passed`.
other mounted skills: not triggered — parallel-decomposition, adversarial-review, merge-gates, product-discovery-guardrail-metrics were configured for this task's text match but this was a solo, non-fan-out delivery with no concurrent-landing or product-hypothesis surface; work-in-english guided commit/PR/record language choice without being separately invoked as a tool call.
