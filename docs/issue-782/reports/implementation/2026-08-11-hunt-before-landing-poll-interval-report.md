---
proposal: docs/issue-782/reports/implementation.md
---

# Hunt record — poll-interval-report

## before-landing — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — dropping POLL_INTERVAL_SEC to 60s combined with the new unconditional not-alive-branch `diagnose_health()` call multiplies live `gh pr list` subprocess calls per dead-but-registered roster entry 15x, with no cooldown/cache/ledger gating the call itself (only the derived `[health]` anomaly line is ledger-gated) — and dead entries are known to persist in the roster indefinitely unless `_auto_respawn_check()` classifies them as `crashed` (stalled/normal verdicts leave the entry untouched, and plain `watchdog` calls without `--auto-respawn` never call `_auto_respawn_check` at all).
Kind: design-error
Seed: spawn.py POLL_INTERVAL_SEC 15*60 -> 60; roster_watchdog() not-alive branch gained `dead_health = diagnose_health(key, e, state=state)` before the unconditional `[poll-report]` print
cap_seconds: 120
tier: default
diff_stat_lines: 12 (spawn.py) + 40 (docs)
started_at: 2026-08-11T08:16:29Z
ended_at: 2026-08-11T08:24:00Z

### Reproduce
Trace the call graph directly in spawn.py:

```
grep -n "dead_health = diagnose_health" spawn.py   # spawn.py:2289, in the `not _alive()` branch
sed -n '2171,2181p' spawn.py                        # diagnose_health(): not-alive path calls
                                                     # session_end_verdict() and
                                                     # _pr_open_or_merged_for_branch()
sed -n '1066,1084p' spawn.py                        # _pr_open_or_merged_for_branch() shells out to
                                                     # `gh pr list --head <branch> --state all ...`
                                                     # unconditionally, no cache/cooldown
sed -n '2908,2942p' spawn.py                        # _auto_respawn_check(): only removes/replaces
                                                     # the roster entry when verdict == "crashed";
                                                     # "stalled" and other verdicts return without
                                                     # touching the roster, so the dead entry survives
                                                     # to the next tick
```

No dedup/ledger key gates the `diagnose_health()` call or the `gh pr list` subprocess call itself in
the not-alive branch — `ledger_check_and_stamp` is only used later, to gate the *derived*
`[health]`/anomaly print in the alive branch (spawn.py:2306-2309), and the not-alive branch has no
equivalent gate around its `diagnose_health()` call at all.

### Observed
Every `roster_watchdog()` tick (now every 60s via `poll_due()`/`directive.sh`'s `UserPromptSubmit`
hook, instead of every 900s pre-change) re-invokes `diagnose_health()` — and therefore a fresh
`gh pr list` API call — for every dead-but-registered roster entry that hasn't yet been classified
`crashed` and respawned. A `stalled` dead entry (or any watchdog run without `--auto-respawn`, which
never calls `_auto_respawn_check()` to age it out) sits in the roster and re-triggers this `gh` call
on every 60s tick indefinitely — a 15x increase in unthrottled outbound GitHub API traffic per such
entry versus the pre-change 900s cadence, with no new state (cache/cooldown/ledger key) added to
bound it.

### Expected
Either the not-alive branch's diagnostic `gh pr list` lookup should be ledger-gated/cached the same
way the alive branch's anomaly report is (so re-diagnosing a persistently-dead entry doesn't refire
a live API call every 60s), or POLL_INTERVAL_SEC's 15x increase in tick frequency should have been
paired with an explicit note/adjustment acknowledging the resulting 15x increase in `gh` call volume
for entries that never get respawned.
