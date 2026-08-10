---
proposal: docs/issue-619/proposals/2026-08-10-korean-emitter-sweep.md
---

# Hunt record — korean-emitter-sweep

## after-proposal — stance 0: assume the gate/check just touched is bypassable — find the bypass

Verdict: NO FINDING
Seed: proposal docs/issue-619/proposals/2026-08-10-korean-emitter-sweep.md — checked whether any test/consumer matches on literal Korean prose (워크스페이스, 로그, 트리거, 브랜치, 사유, 상세) inside _post_crash_comment/_post_stall_comment/_post_session_end_comment/_post_stranded_push_comment bodies in spawn.py, rather than only the marker constants.
cap_seconds: 60
tier: default
diff_stat_lines: n/a (pre-implementation proposal review)
started_at: 2026-08-10T13:49:54+09:00
ended_at: 2026-08-10T13:51:30+09:00

Checked: grep -rn for the six Korean field-label/keyword strings across the whole repo (excluding gates/*, bench/* which use them only in unrelated docstrings/comments), and specifically in test_spawn.py around every call site of the four functions (lines ~3973-4968). All test call sites mock the functions out or invoke them directly but assert only on marker-constant presence, call arguments, or idempotency-key dedup behavior — none assert on the literal Korean field-label/sentence substrings inside the composed comment body. No downstream consumer (gates/*, remediation_spawn, other scripts) matches on the Korean prose either. The proposal's claim held up under this check.
