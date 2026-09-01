---
proposal: docs/issue-2980/proposals/silent-failure-audit+test-derivation-bb9209a8.md
---

# Hunt record — requirement-drift-third-state

## before-landing — stance 1: third-state distinction bypassable — lookup failure resolved as reached verdict, or retained/unknown marker skipped

Verdict: FINDING — the new `if not all_items: return` guard in delta mode also suppresses a genuine, fully-successful verdict (zero gh failure at all) whenever the only relevant cached item just closed and nothing else is cached, silently dropping a real drift violation that the equivalent full-mode state does print.
Kind: silent-failure
Seed: `git diff watchdog.py` around `def requirement_drift` (lines ~920-1090), specifically the `if not all_items: return` guard added at the end of delta mode (~line 1067-1072).
cap_seconds: 180
tier: size:>200-lines
diff_stat_lines: (git diff watchdog.py, this function only ~+70/-20)
started_at: 2026-09-01T00:00:00Z
ended_at: 2026-09-01T00:03:00Z

### Reproduce
Script (`/tmp/repro_2980.py`):
```python
import sys, os, json, tempfile
sys.path.insert(0, os.environ.get("REPO", "."))

tmp = tempfile.mkdtemp()
os.environ['MUSTER_STATE_ROOT'] = tmp
root = tempfile.mkdtemp()
os.makedirs(os.path.join(root, 'docs', 'specs'), exist_ok=True)
with open(os.path.join(root, 'docs', 'specs', 'requirement-digest.md'), 'w') as f:
    f.write('- R001: some paraphrase [open] (source: #10)\n')

import spawn  # sets watchdog._sp = spawn
import watchdog
from pathlib import Path

cache_path = Path(watchdog._requirement_drift_cache_path(root))
cache_path.parent.mkdir(parents=True, exist_ok=True)
cache_path.write_text(json.dumps({'42': {'title': 'unrelated title', 'body': 'no requirement id here', 'cached_at': '2020-01-01T00:00:00+00:00'}}))

def fake_fetch(root, number):
    return {'number': number, 'title': 'closed now', 'body': '', 'state': 'closed'}
watchdog._fetch_issue_or_pr_via_cache = fake_fetch
spawn._fetch_issue_or_pr_via_cache = fake_fetch

print('--- delta mode, changed_numbers={42}: the only ever-cached item just closed, fetch SUCCEEDED (no gh failure) ---')
watchdog.requirement_drift(Path(root), changed_numbers={42})
print('--- end ---')

print()
print('--- control: full mode, board genuinely has zero open items (same real-world state) ---')
def fake_board_read(root, force_full=None):
    return {"issues": {}, "prs": {}}, {"source": "test"}
watchdog._board_read = fake_board_read
spawn._board_read = fake_board_read
watchdog.requirement_drift(Path(root), changed_numbers=None)
print('--- end control ---')
```
Run: `REPO="$(pwd)" python3 /tmp/repro_2980.py` from the repo root.

### Observed
```
--- delta mode, changed_numbers={42}: the only ever-cached item just closed, fetch SUCCEEDED (no gh failure) ---
--- end ---

--- control: full mode, board genuinely has zero open items (same real-world state) ---
[watchdog] requirement-drift: 요구 R001 — 다이제스트: "some paraphrase" (source: #10) — 열린 이슈/PR 어디에도 인용되지 않는다.
--- end control ---
```
Delta mode prints nothing at all — not `requirement-drift:`, not `requirement-drift-lookup-failed:`, not `requirement-drift-cache-retained:`, not `requirement-drift-unknown:`. `any_fetch_ok` is `True` and `failed_numbers` is empty (the gh call for #42 fully succeeded and correctly reported it closed) — there was no lookup failure whatsoever, yet the tick produces the exact same silence as a total lookup failure.

### Expected
Given the digest has a live, `open`-status requirement (`R001`) that is cited nowhere among the currently-known-open items, and delta mode successfully confirmed (via a real, successful gh fetch) that the previously-tracked item #42 is now closed and there is nothing else in the cache, that is a genuine "zero open items reference this requirement" state — the same state full mode reaches and correctly reports via the `requirement-drift:` verdict line above. The new `if not all_items: return` guard (added by this session's #2980 fix) conflates two different reasons for `all_items` being empty — "gh lookup genuinely failed, no data available" (its stated purpose) vs. "gh lookup succeeded and confirmed there is truly nothing open left to check" (a legitimate, fully-computed verdict) — and silently discards the latter along with the former, with none of the three new distinguishing tags (or the original verdict tag) firing to say so.

### Resolution

Fixed in the same session, same commit series: the guard is now
`if failed_numbers and not all_items: return` (`watchdog.py`, delta-mode
branch of `requirement_drift`) — narrowed to fire only when `all_items` is
empty *because of* an actual fetch failure this tick, not whenever it
happens to end up empty for any reason.

canonical: re-running this finding's own `/tmp/repro_2980.py` after the
fix:
```
--- delta mode, changed_numbers={42}: the only ever-cached item just closed, fetch SUCCEEDED (no gh failure) ---
[watchdog] requirement-drift: 요구 R001 — 다이제스트: "some paraphrase" (source: #10) — 열린 이슈/PR 어디에도 인용되지 않는다.
--- end ---

--- control: full mode, board genuinely has zero open items (same real-world state) ---
[watchdog] requirement-drift: 요구 R001 — 다이제스트: "some paraphrase" (source: #10) — 열린 이슈/PR 어디에도 인용되지 않는다.
--- end control ---
```
Delta mode now matches the full-mode control exactly, as expected above.

Regression test added: `test_requirement_drift_no_failure_empty_items_still_flags_drift`
in `tests/test_requirement_drift_third_state_2980.py` (class
`TestNoFailureStillComputesVerdict`), reproducing this exact scenario
(zero failures, only-cached item confirmed closed, digest requirement must
still be flagged, none of the three new lookup-state tags may fire).

acceptance: `python3 -m pytest tests/test_requirement_drift_third_state_2980.py -v` — result:
```
============================== 7 passed in 0.80s ===============================
```
(all prior 6 cases plus this new regression case).
