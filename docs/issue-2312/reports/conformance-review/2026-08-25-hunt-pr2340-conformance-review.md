---
proposal: docs/issue-2312/reports/conformance-review.md
---

# Hunt record — pr2340-conformance-review

## after-proposal — stance 0: assume the gate/behavior I just verified is bypassable, or that my review itself has a silent failure/composition problem

Verdict: FINDING — R2's canonical citation in conformance-review.md points to the wrong line range for the `if not d:` early-return guard it quotes
Kind: silent-failure
Seed: docs/issue-2312/reports/conformance-review.md (R2 requirement block); commit 848fd537c3738e625cd7706ab4718e3c20497f77:watchdog.py
cap_seconds: 60
tier: default
diff_stat_lines: n/a (reviewing an existing record file, not a diff)
started_at: 2026-08-25T00:00:00Z
ended_at: 2026-08-25T00:05:00Z

### Reproduce
```
git show 848fd537c3738e625cd7706ab4718e3c20497f77:watchdog.py > /tmp/wd_848.py
grep -n 'if not d:\|return anomaly_count\|state = _sp._watchdog_state_load' /tmp/wd_848.py
sed -n '1516,1518p' /tmp/wd_848.py
```

### Observed
`grep -n` shows the actual lines are:
```
1513:    if not d:
1517:        return anomaly_count
1518:    state = _sp._watchdog_state_load()
```
and `sed -n '1516,1518p'` (the exact range the record cites) prints:
```
            print("이상 신호 없음")
        return anomaly_count
    state = _sp._watchdog_state_load()
```
— i.e. the cited range 1516-1518 does not contain the `if not d:` guard line
the record quotes as the start of that citation (it's at 1513, three lines
above the cited start), and instead includes an unrelated line (1518, the
`state = _sp._watchdog_state_load()` call, which only executes on the
opposite branch — when `d` is non-empty).

The record's R2 block states:
> canonical: 848fd537c3738e625cd7706ab4718e3c20497f77:watchdog.py:1516-1518
> (`if not d: ... return anomaly_count`) — the entire new dead-entry-report
> block ... sits inside the per-entry loop reached only after this early
> return

and the R2 `evidence:` field repeats the same `1516-1518` range.

### Expected
The citation should read `1513-1517` (the `if not d:` guard through the
`return anomaly_count` line) to match the quoted text and support the
early-return claim the block is making — not `1516-1518`, which cuts off
the guard's own `if` line and instead pulls in one line from the opposite
(non-empty-roster) branch. This is a wrong file:line citation against the
review-traceability requirement that every evidence pointer cite the exact
lines its quote claims to be from; it doesn't change R2's verdict (the
underlying control-flow claim is still true — the empty-state early return
does exist, just three lines earlier than cited), but the citation as
written does not verify against the commit it names.
