---
code_under_review:
  - on-the-record/hooks/delegated-judgment-gate.sh
  - on-the-record/hooks/live-fire-claim-real-run-guard.sh
  - on-the-record/hooks/live-fire-test-guard.sh
  - on-the-record/hooks/test-authoring-invariant-guard.sh
  - on-the-record/hooks/test_hook_cache_layout.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

Subject: issue-948

## Summary of work

Fixed the 4 hooks.json-wired scripts committed mode 100644
(`delegated-judgment-gate.sh`, `live-fire-claim-real-run-guard.sh`,
`live-fire-test-guard.sh`, `test-authoring-invariant-guard.sh`) by
`chmod 755` + `git add` (git records the mode change as 100755 in the
index). Added a regression guard to
`on-the-record/hooks/test_hook_cache_layout.py`:
`t_all_wired_hook_scripts_are_executable` parses `hooks.json` for every
`${CLAUDE_PLUGIN_ROOT}/hooks/*.sh` command and asserts
`os.access(path, os.X_OK)` on each, and
`t_seeded_non_exec_wired_script_is_refused` proves the assertion
actually catches the failure mode (not just passing trivially) by
copying the hooks dir, stripping the exec bit from one wired script,
and confirming `AssertionError` names it.

Skip-condition per scout-directive: this is a pure bugfix (git file
mode + a mechanical test assertion) — the spec leaves no design
decision open, so scouting was skipped.

## Why

Issue #948: every invocation of the 4 non-exec scripts died with
`/bin/sh: Permission denied`, so the 4 gates never ran — a silent
fail-open, violating the gates-fail-closed invariant. No existing gate
verified hook executability, so the gap could recur.

## Upstream / basis

Issue #948.

## Evidence

derived: `git ls-files -s on-the-record/hooks/ | grep -E '(delegated-judgment-gate|live-fire-claim-real-run-guard|live-fire-test-guard|test-authoring-invariant-guard)\.sh'`
```
100755 702e2d53ae60b8a81a74c998ee0aa2299d0ec626 0	on-the-record/hooks/delegated-judgment-gate.sh
100755 81e1cc349ff459866ca0ba3874df82b1eaf803ff 0	on-the-record/hooks/live-fire-claim-real-run-guard.sh
100755 08300886afafb2e753143c92ab5e07f8de398acc 0	on-the-record/hooks/live-fire-test-guard.sh
100755 9736f08367348381e12168f07962990f8186ffac 0	on-the-record/hooks/test-authoring-invariant-guard.sh
```
canonical: git index read via `git ls-files -s`, shown above — all 4 wired scripts are now 100755. All wired hook scripts are 100755 (requirement met).

derived: `python3 -m pytest on-the-record/hooks/test_hook_cache_layout.py -q`
```
........                                                                 [100%]
8 passed in 0.25s
```
canonical: pytest run above, executed live against the current working tree (6 pre-existing tests + the 2 new tests from this change) — PASS, including `t_all_wired_hook_scripts_are_executable` and `t_seeded_non_exec_wired_script_is_refused`.

## What did not work

None.

## Open findings

None.
