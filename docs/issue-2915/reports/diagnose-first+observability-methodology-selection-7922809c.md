---
issue: 2915
role: diagnose-first+observability-methodology-selection-7922809c
author: diagnose-first+observability-methodology-selection-7922809c
skills: diagnose-first (skill-repository(c05de12)), observability-methodology-selection (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-2915/reports/adversarial-review-a74dca2a.md
    sha: d912e17926bb6fa1b2d20b5969b3e8a93a7f3f51
  - path: docs/issue-2915/reports/diagnose-first+observability-methodology-selection-f198342c.md
    sha: e755ffea51f50d03a080fc795beb28eac39ac9f9
  - path: on-the-record/monitors/poll_heartbeat_delta.py
    sha: same-commit
  - path: docs/handbooks/monitor-liveness.md
    sha: same-commit
---

# issue-2915 — diagnose-first+observability-methodology-selection-7922809c record

## What was done

Round 2 on issue #2915, extending the still-open PR #2917
(`issue-2915/diagnose-first+observability-methodology-selection-f198342c`)
rather than opening a competing PR, in response to the independent
adversarial review of round 1 (`docs/issue-2915/reports/adversarial-review-a74dca2a.md`,
landed via PR #2921, merge sha `d912e17926bb6fa1b2d20b5969b3e8a93a7f3f51`). The
review's Finding 1 (MAJOR) held that round 1's "no code change is
warranted" conclusion conflicted with issue #2915's own acceptance bar
("any change must be shown to shorten, not lengthen, the measured
latency") and named a specific, unevaluated candidate mitigation: the
`#1220`-era ~1800s unconditional backstop `#1732` removed. Findings 2-5
(MODERATE/MINOR) were a "twelve days" arithmetic error plus an
exculpatory framing of `#2913`, an undisclosed third call site, and an
incompletely-compressed "0 of 29"/"1/30" pair. All four are addressed
below, in the weighted order the round-2 task specified.

**1. PRIMARY — evaluated the named candidate mitigation and implemented a
narrowed, content-carrying version of it (not left unevaluated, and not a
bare re-assertion of round 1's "no code change" verdict).**

Read the actual removed backstop — canonical: `git show 6361aaba --
on-the-record/monitors/poll_heartbeat_delta.py` (also cited by the
review), this turn — result: an unconditional, every-1800s "monitoring
active, N session(s) tracked, no changes" line, content-free by
construction — reintroducing it verbatim is exactly issue #2915's own
first must-not (also the exact defect `#2913` removed, 87.8% empty).
Read `poll_heartbeat_delta.py`'s current (pre-round-2) 1800s bound-check
branch directly, this turn — result: it already has this same 1800s
`last_emit_epoch` machinery, but only re-emits content when
`returned_pr_keys` (undisposed PRs) is non-empty; a non-empty *tracked
roster* with nothing pending stays silent past the bound, which is
precisely the scenario round 1's own simulation measured as unbounded.

**Root-cause dig (diagnose-first Stage 2):** the review's framing treated
"periodic" and "content-free" as the same defect. They are separable —
the removed backstop was periodic *and* content-free; issue #2915's
must-not forbids the second property, not the first. This opened a
narrower fix: reuse the *already-computed*, real per-entry `[poll-report]`
state (HEALTHY/STALLED/etc, not a static phrase) as the beacon's content,
bounded to the same existing 1800s cadence (no new, tighter polling — no
reversion to `#2905`'s near-every-tick noise `#2913` fixed).

**Implementation** — `on-the-record/monitors/poll_heartbeat_delta.py`
(diff in this same commit): in the existing `else: ... if now -
last_emit_epoch >= 1800:` branch, added a `roster_keys` computation —
every `order` key with prefix `poll-report:` except the literal
`poll-report:roster` sentinel key (`TAG_RE`'s own parse of the
`"[poll-report] roster: ..."` empty-roster line) — and, when non-empty,
emits one `[monitor-heartbeat] <entry's real current state>` line per
key, alongside the pre-existing `[returned-pr-pending]` behavior
(unchanged). A genuinely empty roster stays exactly as silent past the
bound as `#1732` left it —
`t_heartbeat_bound_with_no_returned_pr_emits_nothing`
(`on-the-record/monitors/test_poll_heartbeat.py:714`, unmodified) still
passes unchanged, confirmed — derived: `python3 -m pytest
on-the-record/monitors/test_poll_heartbeat.py -q`, this turn, result: `35
passed` (33 pre-existing + 2 new, 0 failed, 0 modified-and-broken).
**Correction (post-landing background warrant-hunter, `docs/reports/
2026-08-31-hunt-round2-heartbeat-beacon.md`):** the empty-roster
silence is *not* caused by the `poll-report:roster` sentinel-key
exclusion as first written above and in the code's own comment — the
hunter found that `watchdog.py`'s real empty-roster output
(`"돌고 있는 스킬 세션 없음"` / `"이상 신호 없음"`, `watchdog.py:1762-1766`)
carries no `[poll-report]` tag at all, so `TAG_RE` never produces a
`poll-report:`-prefixed key for it in the first place, with or without
the exclusion — confirmed live: `python3 -c "import re; TAG_RE=re.compile(r'^\[(poll-report|...)\]...'); print(TAG_RE.match('돌고 있는 스킬 세션 없음'))"` → `None`. The exclusion is inert
against real production input; it only matters for
`test_poll_heartbeat.py`'s own synthetic `EMPTY_ROSTER_REPORT` fixture
(`"[poll-report] roster: empty\n..."`), which does not itself mirror
`watchdog.py`'s real string (a pre-existing, unrelated inaccuracy in
that fixture's own comment, not introduced by this round). No wrong
observable output resulted (hunter's verdict: NO FINDING) — the code
comment was corrected in the same commit as this correction to state
the real mechanism instead of the original, causally-wrong claim.
`on-the-record/monitors/poll-heartbeat.sh`'s own comment describing the
(stale, per the review) removed backstop was corrected to describe the
new mechanism instead of the deleted one.

**Measured, before/after, side by side (issue's acceptance check 3):**
reran round 1's own 30-tick/3600s (60min) healthy-unchanging-roster
simulation shape (`_healthy_report()`'s exact Korean-clause fixture,
matching `on-the-record/monitors/test_poll_heartbeat.py`'s own helper) —
derived: `python3 /tmp/issue2915r2/sim_healthy_ticks_r2.py`, this turn:

```
tick  offset_s  emitted  sample
   0         0     True  '[poll-report] issue-500/implementation: HEALTHY...'
  15      1800     True  '[monitor-heartbeat] issue-500/implementation: HEALTHY...'
RESULT: 2/30 ticks emitted over simulated 3480s (==58min)
emitted at ticks: [0, 15]
```

Extended to 90 ticks (10800s / 3h) to confirm periodicity, not a
one-shot — derived: `python3 /tmp/issue2915r2/sim_healthy_ticks_long.py`,
this turn, result: `emitted ticks: [0, 15, 30, 45, 60, 75]`, `gaps between
emissions (s): [1800, 1800, 1800, 1800, 1800]`, `max gap: 1800s`.
Re-ran the identical harness against `EMPTY_ROSTER_REPORT` (the exact
fixture `t_heartbeat_bound_with_no_returned_pr_emits_nothing` pins) to
confirm the untouched case — derived: `python3
/tmp/issue2915r2/sim_empty_roster.py`, this turn, result: `empty-roster
emitted ticks over 3600s: [0]` — matches round 1's original finding for
that scenario exactly, unchanged.

**Before (round 1, measured against the pre-round-2 build):**
worst-case detection latency for a dead Monitor during a healthy, quiet,
tracked-roster stretch — unbounded (0 of 29 ticks after the
unconditional tick-0 emit, across a simulated hour).
**After (round 2, measured against the current build):** bounded at
~1800s (30 minutes), confirmed periodic over a 3-hour extended
simulation. **Unchanged (deliberately, disclosed rather than silently
left):** a genuinely empty tracked roster (nothing spawned, no pending
PRs) — still unbounded; the only content available for that case is a
static phrase, which is exactly what issue #2915's must-not forbids
reintroducing, so the honest lever there remains the already-documented,
out-of-scope OS-level scheduled wake.

This satisfies the issue's own acceptance bar ("must be shown to
shorten, not lengthen") for the scenario round 1 itself measured: 1800s
is strictly less than unbounded, and the empty-roster case is provably
unchanged (identical simulation output before and after), not lengthened.

**2. Corrected "twelve days" → "thirteen days" and the exculpatory
framing of `#2913`.** `docs/handbooks/monitor-liveness.md`'s "Issue
#2915" section (edited in this same commit) now states 13 days —
derived: `date -d 2026-08-31 +%s` minus `date -d 2026-08-18 +%s` =
1123200 / 86400 = 13, matching the review's own recomputation — and
explicitly attributes round 1's arithmetic error rather than silently
fixing the number. The `#2913` framing now states plainly that while
`#2913` did not *create* the turn-gated-only gap (`#1732`, 13 days
earlier, did), `#2913` is what made that pre-existing, latent gap
operationally live again by removing the accidental signal (`#2905`'s
bug) that had incidentally been covering it for one day — round 1's
"reverted an accident, not a new regression" framing is called out by
name as eliding that half of the picture.

**3. Disclosed the third call site.** `docs/handbooks/monitor-liveness.md`
now has a "Call-site scope, disclosed" paragraph naming
`tests/run-orchestrate-tests.sh:18` — confirmed directly this turn: it
execs `directive.sh` outside any `hooks.json` trigger, and since the
staleness-check function runs unconditionally near the bottom of
`directive.sh`, that invocation also exercises it (test-only, not
reachable from a live session — does not change the production-path
conclusions, but round 1's "exactly two call sites" reads as
hooks.json-scoped, not exhaustive, and is now labeled as such).

**4. Consolidated "0 of 29"/"1/30" into one number with its derivation.**
The handbook's "Measured before" paragraph now states this as one
measured run described two equivalent ways ("1 of 30 ticks emit" /,
counting only the ticks after the unconditional tick-0 emit, "0 of 29"),
rather than two separate-looking figures.

**5. Skill verdicts (this round).** `diagnose-first` — invoked this
round (not just re-cited from round 1): Stage 2's root-cause dig (above)
is what separated "periodic" from "content-free" and located the
narrower fix; Stage 3 classified the change as a reversible, two-way
door (a delta-file addition guarded by an existing, unmodified test plus
two new ones) — "stop analyzing and just try it, small, and read the
data" — which is what happened, rather than a further round of
analysis-only argument. `observability-methodology-selection` — invoked
this round: its actual rules (RED for a request-driven service boundary,
USE for a finite-resource surface, block a redundant Golden-Signals
overview on top of an existing RED/USE dashboard) do not match this
surface — the `[monitor-heartbeat]` beacon is a liveness dead-man's-switch
that reuses the *existing* `[poll-report]` per-entry state
representation rather than proposing any new RED/USE/Golden-Signals
dashboard, so none of the skill's three rules' preconditions arise;
verdict is not-applicable, now confirmed by actually invoking the skill
rather than asserted without reading it (round 1's own not-applicable
verdict did not invoke it).

## Why

The review's central finding was that round 1 argued from must-not text
("a low-frequency periodic ping... is exactly what #2913 removed") to a
"no code change" conclusion without checking whether "periodic" and
"content-free" were actually the same constraint. They are not: issue
#2915's must-not is specifically about content-free pings, not periodic
ones per se, and the existing 1800s bound-check machinery already in
`poll_heartbeat_delta.py` (added by `#1719`/`#2180` for the
`[returned-pr-pending]` case) was sitting there as a template for a
content-carrying periodic beacon that nobody had reused for the roster
case. diagnose-first's Stage 3 (reversible-decision default) is why this
was built and measured rather than argued further: the blast radius is
one delta-comparison file, guarded by the exact test
(`t_heartbeat_bound_with_no_returned_pr_emits_nothing`) that would catch
a regression of the one invariant that must not move (an empty roster
must stay exactly as silent as `#1732` left it).

## What did not work

None — the implementation, the two new tests, the full existing
`test_poll_heartbeat.py` suite (35/35), the round-1-shape simulation, and
the extended 3h periodicity simulation all ran to a clean result on
first attempt. `bash tests/run-orchestrate-tests.sh` shows 7 pre-existing
failures unrelated to this change — confirmed by running it against the
stashed (pre-round-2) tree and getting the identical 7 failures
(`directive-injects`, five `guard-*` cases, `guard-missing-file-path`),
this turn — not a regression introduced here, and out of this issue's
scope.

## Upstream basis

- `docs/issue-2915/reports/adversarial-review-a74dca2a.md` (landed via
  PR #2921, merge sha `d912e17926bb6fa1b2d20b5969b3e8a93a7f3f51`) — the
  five findings this round addresses.
- `docs/issue-2915/reports/diagnose-first+observability-methodology-selection-f198342c.md`
  (PR #2917's own round-1 record, head sha
  `e755ffea51f50d03a080fc795beb28eac39ac9f9`) — the round-1 measurement
  and conclusion this round revises.
- `on-the-record/monitors/poll_heartbeat_delta.py`,
  `docs/handbooks/monitor-liveness.md`,
  `on-the-record/monitors/poll-heartbeat.sh`,
  `on-the-record/monitors/test_poll_heartbeat.py` — edited in this same
  commit (`sha: same-commit`).
- Read directly, this turn, not restated from any record: `git show
  6361aaba -- on-the-record/monitors/poll_heartbeat_delta.py` (the
  removed `#1732` backstop), `tests/run-orchestrate-tests.sh`.
- Executed, this turn: `python3 -m pytest
  on-the-record/monitors/test_poll_heartbeat.py -q` (35 passed),
  `python3 /tmp/issue2915r2/sim_healthy_ticks_r2.py`,
  `python3 /tmp/issue2915r2/sim_healthy_ticks_long.py`, `python3
  /tmp/issue2915r2/sim_empty_roster.py`, `bash
  tests/run-orchestrate-tests.sh` (both before and after, via `git
  stash`, to isolate pre-existing failures).

## Open findings

None — all five review findings (1 MAJOR, 2 MODERATE, 2 MINOR) are
addressed above with a code change, a measurement, or a correction.

## Next steps

None — `loop_state: landed`. Code, tests, handbook correction, and this
record are all part of the same PR #2917 (branch
`issue-2915/diagnose-first+observability-methodology-selection-f198342c`),
extended rather than competed against.

skill-verdict: diagnose-first — applied: invoked; called via the Skill
tool this turn, used to structure the root-cause dig ("periodic" vs
"content-free" are separable, Stage 2) and the reversible-decision
default that led to implementing and measuring rather than arguing
further (Stage 3).
skill-verdict: observability-methodology-selection — not-applicable:
invoked; called via the Skill tool this turn — its three rules (RED for
a request-driven boundary, USE for a finite-resource surface, block a
redundant Golden-Signals overview) do not match this surface, which
reuses an existing per-entry state representation rather than proposing
any new methodology dashboard.
skill-verdict: work-in-english — applied: invoked; called via the Skill
tool this turn — followed for this session's own output (English
commits, code comments, PR title/body, this record; the final
user-facing summary reported separately in Korean per the skill's own
routing rule).
other mounted skills: not triggered
