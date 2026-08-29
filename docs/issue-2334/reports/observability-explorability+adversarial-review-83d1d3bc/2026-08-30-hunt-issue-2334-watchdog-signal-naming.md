---
proposal: none (build-now bypass, no phase-1 proposal)
---

# Hunt record — watchdog signal-naming breakdown

## before-landing — stance 0: assume the change just touched is bypassable/skippable/defeatable — find the bypass

Verdict: NO FINDING
Seed: watchdog.py roster_watchdog(), lines ~1723-1732 (the class_counts/breakdown block added to the `[watchdog] {key}: 이상 신호 N건` summary line)
cap_seconds: 60
tier: size:<=20-lines, one stance
diff_stat_lines: 8 (net +12/-1)
started_at: 2026-08-30T00:00:00Z
ended_at: 2026-08-30T00:04:00Z

Investigated whether `cls = a.split(":", 1)[0]` grouping could be defeated or
made to lie: checked every anomaly-string producer that feeds `anomalies`
(spawn.py:watchdog_check_one — signals 1,2,3,5,6,7 — and
roster.py:lease_renew's `flat-progress` string). All of them use a
fixed literal prefix immediately followed by `:` (`log-silence:`,
`background-delegation-phrasing:`, `denied-tool-calls:`,
`heartbeat-only-growth:`, `no-commits-late:`, `watcher-missing:`,
`watcher-dead:`, `watcher-silent:`, `flat-progress:`), so the first `:` in
each string always lands at the intended class boundary regardless of what
variable data (paths, keys, repr'd indicators) follows it — grouping cannot
be fooled into misattributing or hiding a signal class. Each signal type is
appended at most once per `watchdog_check_one()` call (no loop appends the
same class twice), so `sum(class_counts.values()) == len(anomalies)` always
holds; the breakdown cannot under- or over-report the total already printed
in `이상 신호 {len(anomalies)}건`.

Traced the one real cross-file consumer of this print output —
on-the-record/monitors/poll_heartbeat_delta.py's line-keyed delta-dedup
(TAG_RE/ALWAYS_RE). Confirmed (by grep + a standalone regex replay) that
`ALWAYS_RE` contains the bare substring `watcher-dead`, and the new
breakdown can inject that substring into the summary line's own text (e.g.
`... 이상 신호 2건 (log-silence: 1, watcher-dead: 1)`), which now always-emits
the summary line too. But the corresponding bullet line
(`  - watcher-dead: ...`, unchanged by this diff) already always-emitted
independently before this change, under its own dedup key — so this is at
most redundant emission of already-surfaced information, never a
suppression or a false-negative. No path found where the new code causes a
real anomaly to go unreported, undercounted, or silently dropped, and no
path found where the summary line can report normalcy while `anomalies` is
non-empty (the `if anomalies:` / `else:` split guarding this block is
untouched by the diff). No reproduction of a wrong output.
