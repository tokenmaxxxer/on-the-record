---
proposal: docs/issue-1044/proposals/panel-cli-dispatch.md
---

# Hunt record — panel-cli-dispatch

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the new `spawn.py panel` CLI dispatch never checks `role_a != role_b`, so a self-panel call is accepted, executed for real, and reported as a normal (non-degraded) two-role verdict
Kind: silent-failure
Seed: spawn.py main() new `if a.role == "panel":` branch (mirrors consult branch)
cap_seconds: 120
tier: default
diff_stat_lines: spawn.py +12, on-the-record/hooks/directive.sh +5/-1, tests/test_spawn.py +29
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:20:00Z

### Reproduce
```
python3 -c "
import spawn
def fake(role, peer, q, cwd):
    return {'turns': ['pos'], 'verdict': {'answer': role}}
r = spawn.panel_cmd('accessibility', 'accessibility', 'q?', issue=None, cwd='.', run_session=fake)
print(r)
"
```
Also end-to-end through the just-added CLI entry point (no mock, real subprocess):
```
python3 spawn.py panel accessibility accessibility "should X ship?"
```

### Observed
`panel_cmd()` returns `{'degraded': False, 'verdict_a': {'answer': 'accessibility'}, 'verdict_b': {'answer': 'accessibility'}, 'record_path': '...'}` — i.e. a clean, non-degraded two-verdict result, even though both "sides" are the same role talking to itself. The panel record and JSON output are byte-for-byte the same shape as a genuine two-independent-role panel; nothing marks this as degenerate. Before this diff `panel_cmd()` had no CLI entry (orphan capability per the proposal's own survey), so this path was unreachable from the CLI; the newly-added dispatch branch (`if a.role == "panel": ... if not a.task or not a.consult_question or not a.panel_question:`) is the first place a caller can trigger this, and it validates only presence/non-emptiness of the three positional args, never that role_a and role_b differ.

### Expected
The CLI dispatch gate added in this diff (or `panel_cmd` itself) should reject `role_a == role_b` before spawning any session — a "concurrent judgment, two roles arguing it out" contract (per `panel_cmd`'s own docstring: "판정자가 둘이고 서로 대화한다") cannot hold when both slots are the same role; at minimum the result should be marked degraded/flagged rather than silently returned as a normal two-verdict panel.
