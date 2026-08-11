---
proposal: docs/issue-731/proposals/2026-08-11-proactive-call-shape-and-report-framing.md
---

# Hunt record — proactive-call-shape-and-report-framing

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: NO FINDING
Seed: docs/issue-731/proposals/2026-08-11-proactive-call-shape-and-report-framing.md, docs/issue-731/reports/implementation/survey.md (~143 lines, docs-only)
cap_seconds: 60
tier: default (docs-only diff)
diff_stat_lines: ~143
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:05:00Z

Checked wiring: both `call-shape-guard.sh` (PreToolUse, matcher
`Write|Edit|MultiEdit`) and `report-framing-check.sh` (Stop) are
registered in `on-the-record/hooks/hooks.json`, which is picked up by
the plugin manifest convention (no separate settings.json override
found repo-root). Ran a live repro against `call-shape-guard.sh`:
seeded a repo with `a.py` calling `subprocess.run(["git","log","-X","foo"])`,
committed it, then fed the hook a synthetic PreToolUse `Write` payload
for `b.py` calling `subprocess.run(["git","log","--method","bar"])` (same
`(argv[0], argv[1])`, different flag shape). The hook denied with exit 2
and the expected `flag 모양이 다르다` message — the check fires as the
proposal's target prose would describe it, not dead code. Did not find
a condition (kill-switch aside, which is already documented in the
hook's own header) under which the hook silently no-ops while still
being described as enforced. No reproduction of a bypass found within
cap.
