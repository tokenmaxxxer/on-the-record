---
proposal: PR #2917 round-2 diff (on-the-record/monitors/poll_heartbeat_delta.py 1800s-bound monitor-heartbeat beacon), issue #2915
---

# Hunt record — round2-heartbeat-beacon

## after-proposal — stance 1: does `roster_keys` (`k.startswith("poll-report:") and k != "poll-report:roster"`) correctly distinguish a real tracked entry from every shape watchdog.py's genuinely-empty-roster path actually emits in production, not just the test's `EMPTY_ROSTER_REPORT` fixture?

Verdict: NO FINDING
Seed: `git diff main -- on-the-record/monitors/poll_heartbeat_delta.py on-the-record/monitors/poll-heartbeat.sh on-the-record/monitors/test_poll_heartbeat.py docs/handbooks/monitor-liveness.md`
cap_seconds: unspecified (no dispatcher cap given in prompt)
tier: default
diff_stat_lines: 4 files changed (poll_heartbeat_delta.py, poll-heartbeat.sh, test_poll_heartbeat.py, monitor-liveness.md)
started_at: 2026-08-31T00:00:00Z (not precisely tracked by tooling)
ended_at: 2026-08-31T00:00:00Z (not precisely tracked by tooling)
note: this hunt is issue-2915-scoped, but board-gate rejected writes under
docs/issue-2915/ from this session's current branch
(issue-2915/diagnose-first+observability-methodology-selection-f198342c
vs required issue-2915/diagnose-first+observability-methodology-selection-7922809c,
`CLAUDE_SKILL`) for every candidate path tried, including the sibling
role directory that already holds a prior hunt record for this same
issue — recording here as the documented non-issue-segment fallback
instead.

### canonical: production empty-roster output, watchdog.py:1762-1766 (repo root)

```
1762	    if not d:
1763	        print("돌고 있는 스킬 세션 없음")
1764	        if not anomaly_count:
1765	            print("이상 신호 없음")
1766	        return anomaly_count
```

Neither line starts with `[poll-report]`. Grepping the whole repo for any
production emitter of the fixture's literal shape:

acceptance: `grep -rn '\[poll-report\] roster' --include='*.py' --include='*.sh' .` — result:

```
./on-the-record/monitors/poll_heartbeat_delta.py:237:            # diff key (TAG_RE on "[poll-report] roster: ..."); excluding
./on-the-record/monitors/test_poll_heartbeat.py:47:EMPTY_ROSTER_REPORT = "[poll-report] roster: empty\n[poll-report] quiet, nothing in flight"
./on-the-record/monitors/test_poll_heartbeat.py:52:    "[poll-report] roster: 1 entry\n"
```

derived: only the diff's own comment and the test fixture reference this
shape; the production `[poll-report]` print sites never print a
`roster:`-keyed line —

acceptance: `grep -n 'print(f"\[poll-report\]' watchdog.py` — result:

```
1706:        print(f"[poll-report] {_pc.get('key')}: COMPLETED — issue #{_pc.get('issue')}, "
1875:                    print(f"[poll-report] {key}: {dead_label} — {dead_health['detail']}")
1946:        print(f"[poll-report] {key}: {health['state']} — {health['detail']}")
```

canonical: `EMPTY_ROSTER_REPORT`'s own preceding comment,
test_poll_heartbeat.py:45-47, claims it "mirrors roster_watchdog()'s
empty-state pair verbatim" — that claim is false against the current
`watchdog.py:1762-1766` shown above (Korean plain-text lines, no
`[poll-report]` tag at all), so the fixture the pinned regression test
uses does not correspond to any real production output.

This means the new code's own comment
(`on-the-record/monitors/poll_heartbeat_delta.py:236-239`, "excluding
[poll-report:roster] ... is what keeps a genuinely empty roster exactly as
silent as #1732 left it") misattributes causality: production's real
empty-roster text never produces any `poll-report:`-prefixed diff key at
all (no `[poll-report]` tag present), so the literal-key exclusion is
inert with respect to real input — TAG_RE simply never matches, with or
without the exclusion.

### Looking for an actual wrong observable output (not just an inaccurate comment)

acceptance: `python3 -c "import re; TAG_RE=re.compile(r'^\[(poll-report|watchdog|health|reconcile|orphaned|resume|watchdog-crash|returned-pr)\]\s*([^:]+):'); print(TAG_RE.match('돌고 있는 스킬 세션 없음')); print(TAG_RE.match('이상 신호 없음'))"` — result:

```
None
None
```

derived: the real production empty-roster lines never match `TAG_RE`, so
`roster_keys` (which is built by filtering `order`, itself populated only
from `TAG_RE`/`ENTRY_RE`/`BULLET_RE` matches) is empty for a genuinely
empty roster regardless of the `poll-report:roster` exclusion.

acceptance: 90-tick (10800s) simulation of an unchanging HEALTHY roster
against the real `on-the-record/monitors/poll_heartbeat_delta.py`,
verifying the handbook's "emits strictly every 1800s" claim and checking
for any spurious/duplicate emission — result (tick, offset-seconds, first
40 chars of stdout, only non-empty ticks shown):

```
0 0 [poll-report] issue-500/implementation: HEALTHY — issue-500/
15 1800 [monitor-heartbeat] issue-500/implementation: HEALTHY — issu
30 3600 [monitor-heartbeat] issue-500/implementation: HEALTHY — issu
45 5400 [monitor-heartbeat] issue-500/implementation: HEALTHY — issu
60 7200 [monitor-heartbeat] issue-500/implementation: HEALTHY — issu
75 9000 [monitor-heartbeat] issue-500/implementation: HEALTHY — issu
```

acceptance: combined tracked-roster + returned-pr scenario crossing the
1800s bound (both categories present in the same tick, checking for
double-emit/suppression/state corruption) — result:

```
== tick2 output (bound crossed, both returned-pr and roster present, only activity clause changed) ==
[returned-pr-pending] 1 PR(s) still awaiting review: #22
[monitor-heartbeat] issue-500/implementation: HEALTHY — issue-500/implementation: 최근 로그 성장, RUNNING — 손댄 파일 없음; 마지막 도구 호출: Read file1.py (10:01:00 UTC)
== tick2 state ==
{"lines": {"poll-report:issue-500/implementation": "...file1.py (10:01:00 UTC)", "returned-pr:issue #22 (phase1)": "..."}, "last_emit_epoch": 1700003600, "surfaced_returned_pr_issues": ["#22"]}
```

Both lines emit together, on the correct tick, and `last_emit_epoch`
advances to the tick's own `now` — no corruption, no double-emit.

canonical: `on-the-record/monitors/poll_heartbeat_delta.py:212-268` — the
new roster-beacon code only runs inside the `else` branch of `if to_emit:`
(line 213), so any tick where an always-emit category line
(STALLED/CRASHED/COMPLETED/watcher-dead, `ALWAYS_RE` line 38-41) is
present already makes `to_emit` non-empty and the new branch is
structurally unreachable that tick — no double-emit/suppression path
exists for the always-emit category by construction of the existing
`if/else`, which this diff does not restructure.

acceptance: `cd on-the-record/monitors && python3 -m pytest
test_poll_heartbeat.py -q` — result:

```
35 passed in 3.18s
```

### Conclusion

No scenario constructed above produces a `[monitor-heartbeat]` beacon for
a genuinely empty/nothing-tracked roster, nor a double-emit/suppression of
an always-emit line, nor state corruption on a mixed-emission tick. The
`roster_keys` exclusion's stated rationale (the comment crediting the
literal `poll-report:roster` key exclusion for the empty-roster silence)
is factually wrong about *why* the empty case stays silent — but the
empty case does stay silent for every production-shaped input tested,
because the real empty-roster text never produces a `poll-report:`-keyed
line in the first place. That is a misleading code comment riding on a
stale/inaccurate test-fixture comment (`EMPTY_ROSTER_REPORT`'s "mirrors
roster_watchdog()'s empty-state pair verbatim" claim, itself pre-existing
and unchanged by this diff), not a reproducible wrong output. Per this
hunt's rule, a concern without a wrong-output reproduction is not a
finding.

NO FINDING (stance: does `roster_keys` correctly distinguish real tracked
entries from every real "nothing to report" shape watchdog.py emits) —
recorded here.
