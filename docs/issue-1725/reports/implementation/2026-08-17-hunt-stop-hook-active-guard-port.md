---
proposal: docs/issue-1725/proposals/2026-08-17-stop-hook-active-guard-port.md
---

# Hunt record — stop-hook-active-guard-port

## after-proposal — stance 1: does the stop_hook_active guard port (stop-gate.sh, deviation-log-guard.sh, role-test-claim-guard.sh, report-framing-check.sh, product-capture-stopgate.sh) contain a placement/field-shape/lost-side-effect/test-fidelity defect

Verdict: NO FINDING
Seed: uncommitted working-tree diff — on-the-record/hooks/{stop-gate,deviation-log-guard,role-test-claim-guard,report-framing-check,product-capture-stopgate}.sh (each +8/-0, the `if e.get("stop_hook_active"): sys.exit(0)` guard) plus new/updated test files test_stop_gate.py (new), test_report_framing_check_live.py (new), test_deviation_log_guard.py, test_role_test_claim_guard.py, test_product_capture_stopgate.py
cap_seconds: not provided by dispatcher (standalone invocation, no explicit cap/tier given)
tier: not provided by dispatcher
diff_stat_lines: 8 files changed, 92 insertions(+), 6 deletions(-) (tracked, `git diff --stat`) + 2 new untracked test files, 168 lines total (test_stop_gate.py 80, test_report_framing_check_live.py 88)
started_at: 2026-08-17T11:45:00Z (approx)
ended_at: 2026-08-17T12:10:53Z

Checked and ruled out, each with a run or a side-by-side read:
- Placement: in all 5 files the guard sits immediately after `if not isinstance(e, dict): ...` and before the first other `e.get(...)` read (verified by reading each file in full). role-test-claim-guard.sh's dict-guard exits 0 (not 2, unlike the other four) but the stop_hook_active guard is placed identically relative to it.
- Field shape: all 5 hooks receive the raw Stop-event stdin JSON via an env var (`STOP_PAYLOAD`/`RTCG_PAYLOAD`/`REPORT_FRAMING_PAYLOAD`) and read `stop_hook_active` top-level, same as decision-queue-stopgate.sh's own `stdin_payload.get("stop_hook_active")`. Confirmed via hooks.json that all 6 patched hooks (5 new + the reference) plus the unpatched stop-poll-rearm.sh sit in the same single "Stop" hook array, i.e. the same payload envelope — no nested/alternate shape exists for any of them. No SubagentStop registration exists for any of the 5 files.
- Lost side effects: only product-capture-stopgate.sh has real side effects under the new early-exit (a per-session dedup state-file write via `os.replace`, and doc-file bootstrap creation). Read the merged reference decision-queue-stopgate.sh: its own stop_hook_active guard is placed before its own state writes (`_save_blocked`, `_save_tier2_last_blocked_ids`) too, so skipping bookkeeping writes during a stop_hook_active turn is the established, blessed precedent, not a regression this diff introduces. The skipped product-capture-stopgate.sh bootstrap/dedup write is re-attempted on the next non-forced Stop call in the same session, so nothing is permanently lost. stop-gate.sh, deviation-log-guard.sh, role-test-claim-guard.sh, report-framing-check.sh are all read-only (no writes anywhere in the file).
- Test fidelity: every new/edited `_run()` helper does `subprocess.run(["bash", str(HOOK)], ...)` with `HOOK = HOOKS_DIR / "<real-hook-name>.sh"`, confirmed by reading each test file. Ran the exact scoped set myself: `python3 -m pytest -q -o addopts="" on-the-record/hooks/test_stop_gate.py on-the-record/hooks/test_report_framing_check_live.py on-the-record/hooks/test_deviation_log_guard.py on-the-record/hooks/test_role_test_claim_guard.py on-the-record/hooks/test_product_capture_stopgate.py on-the-record/hooks/test_decision_queue_stopgate.py` → 67 passed. Verified the new `t_stop_hook_active_emits_nothing_for_*` tests reuse the exact same trigger scenario as an existing non-stop_hook_active test in the same file that DOES assert real additionalContext/decision:block output (e.g. test_deviation_log_guard.py's `t_traceless_deviation_is_blocked` vs `t_stop_hook_active_emits_nothing_for_traceless_deviation`), so the new tests are not vacuously passing on a scenario that was already silent. Confirmed no pytest basename collision remains (`find . -name "test_stop_gate.py" -o -name "test_deviation_log_guard.py" -o -name "test_role_test_claim_guard.py" -o -name "test_product_capture_stopgate.py" -o -name "test_report_framing_check*.py"` — only gates/test_report_framing_check.py and on-the-record/hooks/test_report_framing_check_live.py share a stem, and they differ).

No reproducible defect found in this diff.
