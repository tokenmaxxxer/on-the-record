---
issue: 3129
role: implementation-blueprint+silent-failure-audit-51babd11
author: implementation-blueprint+silent-failure-audit-51babd11
skills: implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: []
type: chore
breaking: false
verdict: This session's task named PR #3137 explicitly and directed the rebase/merge-and-resolve work straight to that PR's own branch (issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019), not this session's own branch/PR. The full record with all citations and derived evidence is at that location, not here — this record is a pointer.
loop_state: landed
upstream:
  - path: docs/issue-3129/reports/implementation-blueprint+silent-failure-audit-51babd11.md
    sha: same-commit
---

# issue-3129 — implementation-blueprint+silent-failure-audit-51babd11 record

## What was done

Integration-only task: brought PR #3137's branch
(`issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019`)
up to date with `origin/main` and resolved the resulting conflicts, no
behavior change. No commits landed on this session's own branch — per the
task's explicit instruction the work was pushed directly to PR #3137's
branch.

- checked: `gh pr view 3137 --json headRefName,baseRefName,mergeable,mergeStateStatus` — result (before): `{"base":"main","head":"issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019","mergeState":"DIRTY","mergeable":"CONFLICTING"}`
- Set up a separate `git worktree` at PR #3137's branch tip (`b5b27e9e39fb04e24fbc8eabeddcc6335e9007c0`, "issue-3129: round-7 record + deviation log"). derived: `git rev-list --count HEAD..origin/main` → `66`; derived: `git rev-list --count origin/main..HEAD` → `26` (`origin/main` at `f5fd4b9f60d1db392b7ac90100222f48569b3cd8`).
- derived: `git merge origin/main --no-edit` — three files reported merge activity: `docs/specs/enforcement-boundary.md` (real conflict markers, "자동 병합이 실패했습니다"), `docs/specs/generated-paths.md` and `on-the-record/hooks/hooks.json` (git reported "자동 병합" for both — three-way merge resolved them without markers).
- `docs/specs/enforcement-boundary.md`: genuine `<<<<<<<`/`=======`/`>>>>>>>` conflict at the `gates/*.py` registry table (derived: `grep -n '^<<<<<<<\|^=======\|^>>>>>>>' docs/specs/enforcement-boundary.md` → lines 55, 58, 61). canonical: the conflicted hunk (own read, `docs/specs/enforcement-boundary.md` lines 55-61 pre-resolution) shows HEAD's branch had added two rows for its own issue #3129 acceptance-check probes (`probe_running_session_sees_amendment.py`, `probe_amendment_notice_fires_once.py`), and `origin/main` had added two unrelated rows for other issues' probes (`probe_wake_notice_clears.py`, issue #3120; `probe_orphan_sweep_spares_live.py`, issue #3118) at the same table-insertion point (both sides inserted immediately after the `probe_parked_report_repo_leak.py` row). Four independent table-row additions, not a semantic conflict — no two rows describe the same mechanism or contradict each other. Resolved keep-both: all four rows now present, HEAD's two first then `origin/main`'s two. derived: `grep -c 'probe_running_session_sees_amendment.py\|probe_amendment_notice_fires_once.py\|probe_wake_notice_clears.py\|probe_orphan_sweep_spares_live.py' docs/specs/enforcement-boundary.md` → `4` (one occurrence each, no duplicates) post-resolution.
- `docs/specs/generated-paths.md`: git auto-merged with no conflict markers; verified independently rather than trusting the auto-merge. derived: `git diff <merge-base 820e9dc5> <branch-tip b5b27e9e> -- docs/specs/generated-paths.md` shows the branch's only addition was one row, `amendment-channel.sh` (issue #3129, at the file's line ~22). derived: `git diff <merge-base> origin/main -- docs/specs/generated-paths.md` shows main's only addition was two rows, `amends-index-preflight.sh` + `amends-landing-apply.sh` (issue #3061 amends work, at the file's lines ~70-71). Different, non-adjacent locations in the table — a true independent-addition case, correctly auto-mergeable. derived: `grep -n "amendment-channel.sh\|amends-index-preflight.sh\|amends-landing-apply.sh" docs/specs/generated-paths.md` on the merged file → all three rows present (lines 22, 73, 74).
- `on-the-record/hooks/hooks.json`: git auto-merged with no conflict markers. This is the file the task singled out for extra care (round 5 of this issue previously dropped a `PostToolUse` entry during an earlier repair, round 6 restored it). Checked directly rather than trusting the auto-merge. derived: `git diff <merge-base> origin/main -- on-the-record/hooks/hooks.json` shows main's only addition beyond the merge-base was one `PostToolUse` entry, `amends-landing-apply.sh` (wrapped in `fail-open-wrapper.sh`) — and derived: `git diff <merge-base> b5b27e9e -- on-the-record/hooks/hooks.json` shows the branch tip already carried that exact same entry (picked up from an earlier partial-main state before this integration) plus the branch's own further addition, `amendment-channel.sh`. Post-merge verification did a full command-set diff rather than trusting that reasoning alone: extracted every `"command": "..."` string from `origin/main`'s `hooks.json` (derived: `git show origin/main:on-the-record/hooks/hooks.json | grep -o '"command": "[^"]*"' | sort | wc -l` → `15`), from the branch tip's pre-merge `hooks.json` (derived: `git show b5b27e9e:on-the-record/hooks/hooks.json | grep -o '"command": "[^"]*"' | sort | wc -l` → `16`), and from the merged working-tree `hooks.json` (derived: `grep -o '"command": "[^"]*"' on-the-record/hooks/hooks.json | sort | wc -l` → `16`), then diffed each side against the merged set — derived: `comm -23 /tmp/main_cmds.txt /tmp/merged_cmds.txt` → empty; derived: `comm -23 /tmp/branch_cmds.txt /tmp/merged_cmds.txt` → empty. Every hook command present on `origin/main` is present in the merged file, and every one the branch added is too — no entry lost in either direction.
- `docs/specs/reconciled-index.md` regeneration (per the docs/specs/* commit obligation): attempted derived: `python3 gates/spec_index.py --update` post-merge; it raised `FileNotFoundError: roles/specs/brand-design.spec.json` (a stale index entry pointing at a path the `roles/` → `spawn_roles.json` consolidation, commit `480d1a78` "issue-2539: Stage 6C", deleted). Verified this is pre-existing and not something this merge introduced or is responsible for fixing: derived: `git worktree add /tmp/main-check origin/main --detach && python3 gates/spec_index.py --update` on an unmodified `origin/main` checkout raises the identical `FileNotFoundError` at the identical path. Left untouched — out of scope for an integration-only task ("nothing else").
- derived: `git commit --no-edit` for the merge → `f6d14a268dce33ba2d0296c1139350b61e394394`, "Merge remote-tracking branch 'origin/main' into issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019".
- Chose merge over rebase: rebasing would rewrite the branch's 26 commits, including the round-6 and round-7 tip commits that two independent-verification records on this same issue (PR #3205, PR #3210) already cite by exact SHA. A merge preserves those SHAs; a rebase would silently invalidate those citations.
- derived: `git push origin HEAD:issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019` → `b5b27e9e..f6d14a26`.
- checked: `gh pr view 3137 --json mergeable,mergeStateStatus` — result (after push, GitHub recompute settled): `{"mergeState":"CLEAN","mergeable":"MERGEABLE"}`.

## Test results

- checked: `bash -c "python3 -m pytest tests/test_amendment_channel.py -q"` — result: `83 passed in 1.03s`
- checked: `bash -c "python3 gates/probe_running_session_sees_amendment.py"` — result: `ok`
- checked: `bash -c "python3 gates/probe_amendment_notice_fires_once.py"` — result: `ok`
- checked: `bash -c "python3 -m pytest tests/ -q"` — result: `486 passed, 2 warnings in 10.48s` (the 2 warnings are the pre-existing `pinned-fixture-divergence (issue #3019)` UserWarnings, unrelated to this integration)

Count reconciliation (task asked to say why if the count didn't land on "main's number plus the branch's own tests" — it does land there, exactly):
- derived: `git worktree add /tmp/mb-check <merge-base 820e9dc5> --detach && python3 -m pytest tests/ -q` at the merge base → `1 failed, 253 passed` (254 total; the one failure is pre-existing at the merge base — see below — not introduced by this integration).
- Branch tip (pre-merge, `b5b27e9e`) — derived: `python3 -m pytest tests/ -q` on that commit → `337 passed` (337 − 254 = 83 net-new tests the branch added over the merge base).
- `origin/main` tip (`f5fd4b9f`) — derived: `python3 -m pytest tests/ -q` on that commit → `403 passed` (403 − 254 = 149 net-new tests main added over the merge base).
- 254 + 83 + 149 = 486, matching the merged-result `486 passed` above exactly (equivalently: main's 403 + the branch's own net-new 83 = 486).
- canonical: the merge-base failure is in `tests/test_spawn_gate_wiring.py`, class `HooksJsonWiringIsAdditive`, method `test_pre_existing_post_tool_use_commands_are_all_still_present` (own read of that file, lines 92-118). derived: `python3 -m pytest tests/test_spawn_gate_wiring.py -k test_pre_existing_post_tool_use_commands_are_all_still_present -q` → `1 passed` post-merge — this merge's own `hooks.json` resolution (additive, nothing dropped) is exactly the condition that test asserts, so it now passes.

## Why

Merge (not rebase) to preserve commit SHAs two other records on this issue
already cite by hash (PR #3205, PR #3210). Keep-both for all three
registry-shaped conflicts, verified per-file (see the `derived:`/`canonical:`
citations in "What was done" above) rather than assumed, because each was
confirmed to be two independent additions with no overlapping claim about the
same mechanism. `hooks.json` got the extra full command-set diff (not just a
read of the merged file) specifically because this file has a prior
silent-drop history on this same issue (round 5) — see the `comm -23` derived
citations above; a git-auto-merge with no conflict markers is not on its own
proof that nothing was silently dropped.

## What did not work

None.

## Upstream basis

- PR #3137, branch `issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019`, merge commit `f6d14a268dce33ba2d0296c1139350b61e394394` (pushed — derived: `git push origin HEAD:issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019` → `b5b27e9e..f6d14a26`, above).
- Pre-merge branch tip: `b5b27e9e39fb04e24fbc8eabeddcc6335e9007c0`.
- `origin/main` tip merged in: `f5fd4b9f60d1db392b7ac90100222f48569b3cd8` — derived: `git rev-parse origin/main` (run before the merge, see "What was done").
- Independent verification records this integration's merge strategy protects (SHAs preserved, not rewritten): PR #3205 (round-6 tip) and PR #3210 (round-7 tip).

## Open findings

None. All four of the issue's acceptance checks pass and PR #3137 is mergeable.

acceptance: `bash -c "python3 -m pytest tests/test_amendment_channel.py -q"` — result:
```
83 passed in 1.03s
```
acceptance: `bash -c "python3 gates/probe_running_session_sees_amendment.py"` — result:
```
ok
```
acceptance: `bash -c "python3 gates/probe_amendment_notice_fires_once.py"` — result:
```
ok
```
acceptance: `bash -c "python3 -m pytest tests/ -q"` — result:
```
486 passed, 2 warnings in 10.48s
```
acceptance: `gh pr view 3137 --json mergeable,mergeStateStatus` — result:
```
{"mergeState":"CLEAN","mergeable":"MERGEABLE"}
```

## Next steps

None. `amendment_channel.py`'s behavior, its tests, and the captured fixture
were not touched (out of scope per the task, and unnecessary — the conflicts
were all in registry/spec files, not in that module).

skill-verdict: work-in-english — applied: invoked; followed for this record and all commits/PR-facing text (English), reserving Korean for the final user-facing summary only.
skill-verdict: implementation-blueprint — not-applicable: no new module/architecture decision — this task was conflict resolution across three existing registry-shaped files, not new code structure.
skill-verdict: silent-failure-audit — not-applicable: no error-handling code was written or touched — the diff is markdown/JSON registry rows plus a merge commit, `amendment_channel.py` itself was explicitly out of scope.
skill-verdict: prose-modes — not-applicable: this record follows the existing pointer-record convention (docs/issue-3182/reports/silent-failure-audit+implementation-blueprint+test-derivation-b63078f1.md) rather than open-ended explanatory prose.
