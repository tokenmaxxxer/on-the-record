---
proposal: docs/issue-1117/proposals/poll-heartbeat-delta-suppression.md
---

# Hunt record — poll-heartbeat-delta-suppression

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass.

Verdict: FINDING — the plan hashes `report` (captured watchdog stdout+stderr), not the actual printed text; when `report` is empty the printed line is the fallback `"poll tick: due, watchdog ran (rc=${watchdog_rc}, no output)"` which embeds `watchdog_rc` — so a tick where the watchdog crashes (rc changes, e.g. 0→1) after a prior empty-report tick hashes identically (both hash of "") and gets silently suppressed even though the emitted text differs, violating #90 ("any tick whose captured output differs from the last emitted tick MUST emit").
Kind: design-error
Seed: docs/issue-1117/proposals/poll-heartbeat-delta-suppression.md "What will be done" — "compute a hash of it (e.g. sha256sum)" referring to `report`, then separately "print the report (or the existing 'no output' fallback line) unchanged as today"
cap_seconds: 120
tier: size:120
diff_stat_lines: 234
started_at: 2026-08-13T09:40:00+09:00
ended_at: 2026-08-13T09:44:00+09:00

### Reproduce
```
cat > /tmp/repro.sh <<'SH'
#!/usr/bin/env bash
sim_tick() {
  local report="$1" watchdog_rc="$2" statefile="$3"
  local hash
  hash="$(printf '%s' "${report}" | sha256sum | cut -d' ' -f1)"
  local prev=""
  [ -f "${statefile}" ] && prev="$(cat "${statefile}")"
  if [ -n "${report}" ]; then printed="${report}"
  else printed="poll tick: due, watchdog ran (rc=${watchdog_rc}, no output)"; fi
  if [ "${hash}" = "${prev}" ]; then
    echo "[SUPPRESSED] would-have-printed: ${printed}"
  else
    echo "[EMITTED]    ${printed}"
  fi
  printf '%s' "${hash}" > "${statefile}"
}
STATE=$(mktemp); rm -f "$STATE"
sim_tick "" 0 "$STATE"   # tick 1: watchdog ok, no output
sim_tick "" 1 "$STATE"   # tick 2: watchdog CRASHED (rc=1), still no report text
SH
chmod +x /tmp/repro.sh && /tmp/repro.sh
```

### Observed
```
[EMITTED]    poll tick: due, watchdog ran (rc=0, no output)
[SUPPRESSED] would-have-printed: poll tick: due, watchdog ran (rc=1, no output)
```
The second tick's printed text (rc=1, a watchdog crash) differs from the first tick's (rc=0) but is suppressed because both hash the same empty `report`.

### Expected
Per #90, any tick whose emitted text differs from the last emitted tick must emit. A watchdog rc flip from 0 to 1 while `report` stays empty changes the fallback line's text and must not be suppressed. The proposal must specify hashing the final printed text (report-or-fallback-line, including rc) rather than hashing `report` alone, or explicitly fold `watchdog_rc` into the hash input for the empty-report branch.
