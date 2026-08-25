---
proposal: (none — build-now bypass mode, issue #2312, no proposal file exists for this delivery)
---

# Hunt record — dead-active-json-retire

## before-landing — stance 1: assume the gate/behavior just touched is bypassable — find the bypass

Verdict: FINDING — an unrelated roster entry's unhandled exception in the same tick discards the whole tick's in-memory `reported_terminal` flags (state is only persisted once, at the very end of `roster_watchdog()`), so the just-added "report once" gate resets every tick and the dead-entry status line reprints forever again, exactly like the original bug.
canonical: python3 -u /tmp/repro_2312b.py — run this turn against this checkout (`/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2312-implementation`); output quoted verbatim in the Observed block below.
Kind: composition
Seed: `git diff -- watchdog.py` (issue #2312 fix, `roster_watchdog()` lines ~1577-1620): adds `state[f"{key}:{pid}:reported_terminal"]` gate around the dead-entry `[poll-report]` print, and calls `roster_remove(key)` when nothing is left to watch.
cap_seconds: 60
tier: size:diff<=20-lines
diff_stat_lines: 17
started_at: 2026-08-25T00:00:00Z
ended_at: 2026-08-25T00:20:00Z

### Reproduce
canonical: python3 -u /tmp/repro_2312b.py — run this turn against this checkout (`/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2312-implementation`), only `diagnose_health`/board-sweep/PR-lookup helpers monkeypatched, `roster_watchdog()` itself untouched; stdout captured verbatim in the Observed block below.

Script (`/tmp/repro_2312b.py`, sandbox tmp, not part of the repo): a two-entry roster (`issue-1/a`, dead, `issue: 1`, `expects_pr: True` — stays in roster, not retired by the fix) and (`issue-2/b`, dead, `expects_pr: True`), run through the real `spawn.roster_watchdog()` four times, with only `diagnose_health` monkeypatched to raise `RuntimeError` for `issue-2/b` on every tick (any transient per-entry failure — gh hiccup, malformed entry, etc. — reproduces the same thing) and `ledger_check_and_stamp` forced `True` (simulates the TTL having elapsed, which happens every ~15 min in real operation regardless):

```python
import spawn
from unittest import mock
spawn.ROSTER = roster_path        # {"issue-1/a": {...dead, issue:1, expects_pr:True...},
                                   #  "issue-2/b": {...dead, issue:2, expects_pr:True...}}
spawn.WATCHDOG_STATE = state_path
def fake_diagnose_health(key, entry, *a, **k):
    if key == "issue-2/b":
        raise RuntimeError("simulated persistent failure diagnosing issue-2/b")
    return {"state": "COMPLETED", "detail": "fake completion", "next_action": "none"}
with mock.patch.object(spawn, "_board_wide_sweep", return_value=0), \
     mock.patch.object(spawn, "standing_red_check", return_value=[]), \
     mock.patch.object(spawn, "_undispositioned_role_prs", return_value=([], True)), \
     mock.patch.object(spawn, "lease_reconcile_sweep", return_value=0), \
     mock.patch.object(spawn, "reconcile", return_value=[]), \
     mock.patch.object(spawn, "ledger_check_and_stamp", return_value=True), \
     mock.patch.object(spawn, "diagnose_health", fake_diagnose_health):
    for tick in range(1, 5):
        try:
            spawn.roster_watchdog(root=Path(td))
        except RuntimeError:
            pass  # tick "crashes" on issue-2/b, same as any real unhandled per-entry error
```

### Observed
canonical: python3 -u /tmp/repro_2312b.py — same run as above, this turn, against this checkout.
```
tick 1: crashed=True 'issue-1/a: COMPLETED' printed 1x state_on_disk=None
tick 2: crashed=True 'issue-1/a: COMPLETED' printed 1x state_on_disk=None
tick 3: crashed=True 'issue-1/a: COMPLETED' printed 1x state_on_disk=None
tick 4: crashed=True 'issue-1/a: COMPLETED' printed 1x state_on_disk=None
```
The `[poll-report] issue-1/a: ...` dead-entry status line prints once *per tick*, every tick, forever — the exact "re-printed every tick forever" symptom issue #2312 was filed to fix. `watchdog_state.json` never gets written (`state_on_disk=None` throughout) because `_sp._watchdog_state_save(state)` sits unconditionally at the very end of `roster_watchdog()` (watchdog.py:1654) with no `try`/`finally` around the per-entry loop — `issue-1/a`'s `state[f"{key}:{pid}:reported_terminal"] = True` mutation (set in memory while processing `issue-1/a`) is silently discarded the moment a *later* entry in the same tick (`issue-2/b`) raises, because the function never reaches the save call. Root cause sits in `diagnose_health()`/its caller having no per-entry isolation, not in the new gate logic itself — but it fully defeats the new gate: nothing about the fix survives an unrelated entry's failure in the same tick.

### Expected
`issue-1/a`'s `reported_terminal` flag, once set, should survive regardless of what happens to any other roster entry processed later in the same tick — i.e. the fix's "report exactly once, ever" contract should hold even when one dead entry's health diagnosis throws (a realistic occurrence: `gh` hiccups, malformed `work`, network blips are exactly the kind of per-entry failure `roster_watchdog()` is supposed to tolerate one entry at a time). The single end-of-function `_watchdog_state_save(state)` call, with no incremental persistence and no exception isolation per entry, makes the entire fix as fragile as the state it depends on.
