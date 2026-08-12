
## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the new pre-registration write (`roster_register()` -> `_roster_save()`) is non-atomic; a death exactly mid-write corrupts `active.json`, and `_roster_load()`'s broad `except (OSError, ValueError): return {}` silently discards the whole roster (not just the dying entry) for every future watchdog read, reopening a silent-death gap wider than the one issue #908 closes.
Kind: silent-failure
Seed: git diff main...issue-908/implementation -- spawn.py tests/test_spawn.py (spawn.py:5075-5163); root cause lives at spawn.py:1796-1805 (`_roster_load`/`_roster_save`), invoked from the new pre-registration call at spawn.py:5088.
cap_seconds: 180
tier: default
diff_stat_lines: spawn.py ~large (broad diff vs stale main), fix-relevant span ~90 lines (5075-5163)
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:03:00Z

### Reproduce
```
python3 -c "
import json
valid = {'issue-1/coding': {'pid': 111}, 'issue-2/review': {'pid': 222}}
open('active.json','w').write(json.dumps(valid, indent=2))
full_text = json.dumps({**valid, 'issue-3/product': {'pid': 333}}, indent=2, ensure_ascii=False)
with open('active.json','w') as f:
    f.write(full_text[:20])  # simulate SIGKILL mid write_text() during roster_register()
try:
    d = json.loads(open('active.json').read())
except (OSError, ValueError) as e:
    d = {}
    print('roster_load exception ->', repr(e))
print('roster_load result after mid-write death ->', d)
"
```
(mirrors spawn.py's `_roster_save` = `ROSTER.write_text(json.dumps(...))` at spawn.py:1805 and `_roster_load`'s `except (OSError, ValueError): return {}` at spawn.py:1799-1800, both unchanged by this diff and both reached by the new pre-registration call.)

### Observed
```
roster_load exception -> JSONDecodeError("Expecting ':' delimiter: line 2 column 19 (char 20)")
roster_load result after mid-write death -> {}
```
Two previously-registered, still-live entries (`issue-1/coding`, `issue-2/review`) vanish from every subsequent roster read alongside the dying entry — `roster_watchdog()` now sees an empty roster and flags nothing for any of them.

### Expected
A death during the pre-registration write should, at worst, lose visibility into the one entry being written (the case issue #908 already accepts as unavoidable at the very first instant), not corrupt the shared roster file for all other concurrently-registered sessions. `_roster_save` should write atomically (temp file + `os.replace`) so a mid-write death cannot leave `active.json` in a state that `_roster_load` treats as "no one is running."
