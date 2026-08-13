---
proposal: docs/issue-1220/proposals/delta-only-monitor-emission.md
---

# Hunt record — delta-only-monitor-emission

## after-proposal — stance 1: does the proposed line-keyed diff scheme actually work against roster_watchdog()'s real output shapes?

Verdict: FINDING — the proposal's "single fixed key" fallback for unprefixed lines collapses multiple distinct `  - {a}` anomaly-detail bullet lines (emitted per-anomaly under `[watchdog] {key}: 이상 신호 N건`, spawn.py:2644-2769) into one dict entry, silently dropping all but the last anomaly detail line every tick.
Kind: design-error
Seed: docs/issue-1220/proposals/delta-only-monitor-emission.md (proposal-only, no code yet); cross-referenced spawn.py:2644-2769 roster_watchdog()
cap_seconds: unknown (not stated by dispatcher)
tier: default
diff_stat_lines: N/A (proposal-only commit, no diff)
started_at: 2026-08-13T00:00:00Z
ended_at: 2026-08-13T00:15:00Z

### Reproduce
```
python3 - <<'PYEOF'
import re
report = """[watchdog] issue-100/role-a: 이상 신호 2건
  - anomaly one: disk full
  - anomaly two: stale lock
[watchdog] issue-200/role-b: 정상
이상 신호 없음"""
lines = report.splitlines()
TAG_RE = re.compile(r'^\[(poll-report|watchdog|health|reconcile|orphaned)\]\s*([^:]+):')
def key_for(line):
    m = TAG_RE.match(line)
    if m:
        return f"{m.group(1)}:{m.group(2)}"
    return "__fixed__"   # proposal: "lines without a recognized prefix ... are
                          # compared as a single fixed key so they still
                          # suppress/emit correctly"
state = {}
for line in lines:
    k = key_for(line)
    state[k] = line
print(len(lines), "source lines ->", len(state), "keys")
for k, v in state.items():
    print(repr(k), "->", repr(v))
PYEOF
```

### Observed
```
5 source lines -> 3 keys
'watchdog:issue-100/role-a' -> '[watchdog] issue-100/role-a: 이상 신호 2건'
'__fixed__' -> '이상 신호 없음'
'watchdog:issue-200/role-b' -> '[watchdog] issue-200/role-b: 정상'
```
Both `  - anomaly one: disk full` and `  - anomaly two: stale lock` are gone from the map — collapsed into (and overwritten within) the same `__fixed__` key as the unrelated summary line `이상 신호 없음`. Only whichever line is processed last for that key survives.

### Expected
Every anomaly-detail bullet line that `roster_watchdog()` emits under a `[watchdog]` header should reach the operator (this is exactly the per-session anomaly content the Monitor exists to surface — req #2/#3 "always surfacing" transitions). The proposal's own worked example (option 1 rationale) only describes the fixed-key fallback for genuinely singleton lines like "이상 신호 없음", but spawn.py:2644-2769 shows the same unprefixed-line shape is also used for a variable, per-anomaly, non-singleton payload (`for a in anomalies: print(f"  - {a}")`), which the proposed scheme cannot distinguish and will silently truncate to at most one surviving bullet per tick, sitewide (not per-session-key).
