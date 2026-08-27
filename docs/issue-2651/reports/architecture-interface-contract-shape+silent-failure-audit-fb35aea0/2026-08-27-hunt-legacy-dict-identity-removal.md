---
proposal: (build-now bypass, no phase-1 proposal file)
---

# Hunt record — legacy-dict-identity-removal

## before-landing — stance 0: assume the gate/mechanism just touched is bypassable — find the bypass

Verdict: NO FINDING
Seed: spawn.py LEGACY dict (role-identity -> filename) replaced by LEGACY_FILES tuple (filenames only); board.py:826 updated from `sorted(r for r, name in _sp.LEGACY.items() if ...)` to `sorted(name for name in _sp.LEGACY_FILES if ...)`.
cap_seconds: 60
tier: size:small
diff_stat_lines: 13
started_at: 2026-08-27T19:01:01+09:00
ended_at: 2026-08-27T19:01:15+09:00

### Reproduce
```
grep -rn "spawn\.LEGACY\b\|_sp\.LEGACY\b" .        # only match is board.py:826, already using LEGACY_FILES
python3 -c "import spawn; print(hasattr(spawn, 'LEGACY'))"   # -> False
grep -rln "LEGACY_FILES\|review-record.md\|feasibility-record.md\|product-record.md" test/
```

### Observed
- `grep -rn "spawn\.LEGACY\b|_sp\.LEGACY\b"` across the repo finds only `board.py:826`, and that line already reads `_sp.LEGACY_FILES` (the new tuple name), not `_sp.LEGACY`.
- `hasattr(spawn, 'LEGACY')` is `False` — the old dict attribute is fully gone, not just deprecated or aliased, so nothing can resurrect the identity-keyed shape by reading it back.
- No test file references the old `LEGACY` dict or does `.items()`/`.keys()` on it; no test file needed updating for this rename.
- board.py:826's message-building code only ever binds `name` (the tuple element) into the printed string — there is no remaining code path where a role name flows into `stale`/the printed message.

### Expected
(this is the NO-FINDING case — expected and observed match: no other importer of the dict shape exists, no retired identity name can reach the printed message, and `spawn.LEGACY`/`spawn.LEGACY_FILES` cannot be used to reconstruct the old dict shape since the dict is deleted, not aliased.)
