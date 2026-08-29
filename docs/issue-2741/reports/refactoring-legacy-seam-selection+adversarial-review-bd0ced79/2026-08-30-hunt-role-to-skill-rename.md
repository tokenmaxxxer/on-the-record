---
proposal: docs/issue-2741 role->skill persisted-key rename (no dedicated docs/issue-2741/proposals/ file found in either repo; scope taken from PR #2746 diff + companion core PR #353)
---

# Hunt record — role-to-skill-rename

## after-proposal — stance 1: assume the change just made is bypassable or has a silent-failure gap

Verdict: NO FINDING
Seed: relay.py:267 trailer f-string, gates/flows.py:36 `_ROLE_TRAILER_RE`/`_role_from_pr()`, gates/patrol_board.py (~229,332,337) + gates/patrol_promote.py (~236,242) GH label literals, test/test_branch_role_field.py + test/test_convention_equivalence.py mock literals, plus companion core PR #353's board-gate.sh sidecar-key rename and new shape-mismatch `sys.stderr.write` diagnostic mirroring six on-the-record hooks (approval-gate.sh, call-shape-guard.sh, contract-guard.sh, deviation-log-guard.sh, pr-preflight.sh, skill-verdict-guard.sh)
cap_seconds: not specified by dispatcher (standalone invocation, no explicit cap given)
tier: default
diff_stat_lines: ~55 (relay.py 3, gates/flows.py 8, gates/patrol_board.py 3, gates/patrol_promote.py 3, test/test_branch_role_field.py 5, test/test_convention_equivalence.py 6, core board-gate.sh 8)
started_at: 2026-08-30T02:20:00+09:00
ended_at: 2026-08-30T03:05:00+09:00

### Investigation

(a) Fresh grep across both repos for any remaining `"role:"` trailer/label
construction.
canonical: `grep -rn 'role:{skill}\|role:{role}\|role:%s\|'"'"'role:'"'"'\|"role:"' --include=*.py --include=*.sh .` — result: only match was gates/flows.py:34, a comment (`# creates ("skill: <skill>", renamed from "role:" by issue #2741, ...`), no live construction site outside the edited files.

(b) Checked every other GH-label call site in the on-the-record repo.
canonical: `grep -rln "LABEL_BOARD\|gh issue list\|--label" --include=*.py .` — result: `gates/patrol_promote.py`, `gates/spawn_coverage.py`, `gates/patrol_board.py`, `gates/closure_sweep.py`, `gates/acceptance_gate.py`, `gates/open_work.py`, `watchdog.py`; then `grep -n "label" gates/spawn_coverage.py gates/closure_sweep.py gates/acceptance_gate.py gates/open_work.py watchdog.py` — result: no hits in any of those five, so `gates/patrol_board.py`'s `find_board_issue()` (already updated to `skill:{skill}` at line 229 of the current diff) is the only label-filter query in the repo.

(c) No test file references the label-creating modules.
canonical: `grep -rln "LABEL_BOARD\|LABEL_PROMOTED\|find_board_issue\|promote_tick\|run_patrol_board" test/` — result: empty (no output). `grep -rn "role:" test/` — result: only `test/test_convention_equivalence.py:215,217,228,233` (approval-gate.sh's local `role`/`branch_role` variable names, unrelated to the persisted-key rename), `test/test_spawn_attempt_staleness.py:394,408` (uses the literal string `"role"` as a generic skill-name placeholder value, not a key), `test/test_branch_role_field.py:8` (stale docstring prose only), and `test/test_record_kind_field.py:27` (an unrelated frontmatter `kind:` vocabulary test).

(d) Compared the board-gate.sh shape-mismatch diagnostic against the six on-the-record hooks.
canonical: `git -C /home/jwjung/tokenmaxxxer-core show ffaf0d9:core/hooks/board-gate.sh` plus `grep -n "role.json\|sys.stderr.write" on-the-record/hooks/{approval-gate,call-shape-guard,contract-guard,deviation-log-guard,pr-preflight,skill-verdict-guard}.sh -A8 -B2` — result: all seven blocks use identical message wording/key names (`skill: str, issue: int`) and equivalent control flow; contract-guard.sh's extra nested `if sidecar["issue"] == issue:` is indented one level deeper than its `else:`, confirmed via `sed -n '207,222p' on-the-record/hooks/contract-guard.sh | cat -A`, so the `else:` still attaches to the outer shape-check `if`, not the inner one.

Live reproduction of the board-gate.sh fallback path with an old-shaped sidecar, run in a disposable sandbox repo at /tmp/coretest (untracked scratch directory, not part of either project repo — its `docs/issue-3/reports/qa.md` target path is a synthetic fixture for this reproduction only, never written):
acceptance: `printf '%s' "$payload" | CLAUDE_PROJECT_DIR="$PWD" CLAUDE_PLUGIN_ROOT=/home/jwjung/tokenmaxxxer-core CLAUDE_SKILL=qa /bin/bash /tmp/coretest/board-gate-ffaf0d9.sh` (sandbox repo on branch issue-3/qa, `.on-the-record/role.json` containing `{"role":"qa","issue":3}`, `tool_input.file_path` = `docs/issue-3/reports/qa.md`) — result:
```
board-gate: .on-the-record/role.json present but not in the expected shape (skill: str, issue: int) -- falling back to branch-name parsing (issue #2741: this key was renamed role -> skill, forward-only; a sidecar written before that rename no longer resolves here).
rc=0
```
This matches the intended design (diagnostic fires, then falls back to branch-name parsing and allows, same as the pre-existing "corrupt sidecar" and "no sidecar" fallback paths) — not a defect.

Also checked (adjacent to the seed, same rename thread): `gates/flows.py`'s in-memory dict keys.
canonical: `grep -n '"role"' roster.py` — result: empty; `sessions.append({"skill": e.get("skill"), ...})` at gates/flows.py reads from `roster.items()`, and roster.py's own entries already use the `"skill"` key throughout, so no stale-producer/renamed-consumer split.
derived: `gates/findings_due.py` still uses an in-memory `"role"` key end-to-end (producer `findings_due()` and consumer `format_report()` in the same file, sole caller `spawn.py`'s `findings-due` subcommand, confirmed via `grep -rn "findings_due\b" --include=*.py .`) — internally self-consistent, not a persisted cross-process key, and outside this session's enumerated rename scope, so not flagged.

Found no reproducible defect within the stated stance.

derived: a pre-existing, unrelated test failure (`test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape`, asserting a regex string `[\w-]+` that is not present in approval-gate.sh's actual `[^/]+` regex) was confirmed present identically at the prior commit via `git checkout -q 00aeaae4 -- . && python3 -m pytest test/test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape -q` (same failure reproduced before this session's changes, then working tree restored with `git checkout -q HEAD -- .`), so it predates and is unrelated to this rename and is not reported as this hunt's finding.
