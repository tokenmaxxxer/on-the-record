---
issue: 2915
role: diagnose-first+observability-methodology-selection-f198342c
author: diagnose-first+observability-methodology-selection-f198342c
skills: diagnose-first (skill-repository(c05de12)), observability-methodology-selection (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-2906/reports/adversarial-review-30a89443.md
    sha: fed2e78d1e4e9f75e37384752d58dce3a249e586
  - path: docs/handbooks/monitor-liveness.md
    sha: same-commit
---

# issue-2915 — diagnose-first+observability-methodology-selection-f198342c record

## What was done

Answered issue #2915's measurement question — how long can a dead
`poll-heartbeat.sh` Monitor now go unnoticed during a healthy, quiet
stretch, post-#2913 — against the current build (main @ `85d9f61d`,
which already contains #2913).

**1. Enumeration (executed-live, bounded search stated).** Grepped the
whole tracked tree for the staleness function name and its stamp path
(`_monitor_liveness_check_and_notify`, `poll_heartbeat_alive.json`,
`MONITOR_LIVENESS_STALE_SECONDS`) — derived:
`grep -rn "_monitor_liveness_check_and_notify\|poll_heartbeat_alive.json\|MONITOR_LIVENESS_STALE_SECONDS" --include=*.sh --include=*.py .`,
this turn, result: exactly two call sites, `on-the-record/hooks/
directive.sh:272` and `on-the-record/hooks/stop-poll-rearm.sh:133`, both
inside a verbatim-duplicated function (the handbook already documents
why: `stop-poll-rearm.sh` does not source `directive.sh`). Cross-checked
against the plugin's actual hook wiring — canonical: `on-the-record/
hooks/hooks.json`, read in full, this turn — which registers exactly six
event types: `SessionStart` (2 command entries), `UserPromptSubmit` (1),
`PreToolUse` (2), `PostToolUse` (4), `Stop` (3) — derived: direct count
of the `hooks.json` array entries read this turn. Only the
`UserPromptSubmit` entry (`directive.sh`) and one `Stop` entry
(`stop-poll-rearm.sh`) reach the staleness check. No `PreToolUse`/
`PostToolUse`/`SessionStart` hook, no CLI subcommand in `spawn.py`, and
no other script in the repo calls it — population reached is "every
hook this plugin registers," not a sampled subset; the three empty-state
categories (`PreToolUse`, `PostToolUse`, `SessionStart`) are named
explicitly, not omitted. `spawn.py deadman-check` (also called from
`stop-poll-rearm.sh`, issue #2140) is a **different** check (watch-layer
external dead-man detection, not the poll-heartbeat liveness stamp) —
read directly, confirmed distinct, not double-counted as a third call
site.

**2. Dead-monitor scenario, constructed and measured against current
build (executed-live).** Two separate, complementary measurements,
since "does a turn fire" and "does the check work once it fires" are
different questions (issue's own must-not #4):
- Simulated 30 ticks of the real, unmodified
  `on-the-record/monitors/poll_heartbeat_delta.py` (current build) fed
  an unchanging `HEALTHY` `[poll-report]` line whose only per-tick
  change is the last-tool-activity timestamp (the exact #2904/#2905
  shape) — derived: `python3 /tmp/issue2915/sim_healthy_ticks.py`, this
  turn:
  ```
  tick 0: EMITTED: '[poll-report] issue-9999/some-role: HEALTHY — no dirty files; 마지막 도구 호출: Bash (1000120 UTC)'
  RESULT: 1/30 ticks emitted any stdout over a simulated 3600s (60min)
  healthy, unchanging-except-activity-clause stretch
  ```
  Only tick 0 (the unconditional first-tick emit) produced output; the
  remaining 29 ticks over a simulated 3600s (60-minute) span produced
  zero stdout — zero notifications, zero forced turns, for the full
  simulated hour.
- Timed the staleness check itself (the exact python body embedded in
  `directive.sh`) against a synthetic 1000s-stale stamp with the 360s
  threshold — derived: python subprocess-timed driver, this turn:
  ```
  check invocation latency: 28.8ms
  stdout: [orchestrate][MONITOR-DEAD] poll-heartbeat monitor dead since ... (age=1000.9s, threshold=360.0s)
  ```
  This isolates: total detection latency = (wait for some turn to fire)
  + (check cost, measured 28.8ms here). The first term is what #2915
  asks about; the second is negligible and was already known to work
  (#2906's own verification, cited by the issue as insufficient evidence
  on its own).

**3. Root-cause dig (diagnose-first Stage 2, evidence not opinion).**
Dated the actual mechanism that determined whether the documented bound
ever held, via `git log --diff-filter=A --date=short` on each issue's
first record commit:
- `#1220` (2026-08-13): delta-only monitor emission ships, including
  (per `on-the-record/monitors/poll-heartbeat.sh`'s own comment, read
  directly) a 1800s fully-suppressed-tick fallback that forced one no-op
  notification every 30 minutes.
- `#1497` (2026-08-14): the 360s/180s staleness check and this handbook
  ship — one day after #1220, i.e. under a regime whose only forced
  cadence was already the 1800s fallback above (5-10x looser than the
  number being documented), not a ~60-180s cadence.
- `#1732` (2026-08-18, `docs(issue-1732)` and `fix(issue-1732)` same
  day) — read the proposal in full, this turn — removes the 1800s
  fallback outright: "monitor liveness is already covered by the
  separate alive marker." That claim is true only if something reads
  the marker on a bounded cadence; nothing does except the same
  turn-driven hooks this whole mechanism already depends on. From this
  commit forward, a healthy/unchanging roster entry forces zero ticks to
  print anything.
- `#2905` (2026-08-30) to `#2913` (2026-08-31): the one-day window issue
  #2915 was filed about. `#2905` accidentally defeated delta suppression
  (an ever-changing timestamp clause), forcing near-every-tick emission
  at the Monitor's own ~120s cadence; `#2913` correctly removed that
  noise (87.8% empty, per `docs/issue-2906/reports/
  silent-failure-audit-c7e19e1e.md`, cited by the issue). Removing it
  reverted the system to the **#1732-onward state** — a 12-day-older,
  longer-standing condition — not a newly introduced one.
- Amdahl-style share check: the #2905→#2913 window this issue is framed
  around was one day out of the 18 days since #1732 actually removed the
  only real bound — derived: `date -d 2026-08-31 +%s` minus
  `date -d 2026-08-18 +%s` = 13 days from #1732 to #2913, plus the
  ~5 days from #2913's landing back to today (2026-08-31, same day) —
  fixing "what #2913 broke" would move the needle by at most that one
  day's accidental behavior, while the other ~13+ days of exposure
  (both before #2905 and, per the verdict below, after #2913) remain
  untouched. The real lever is the #1732 assumption, not the #2913 diff.

**4. Verdict, stated side by side with the documented bound and the
historical failure**, per the issue's third acceptance check:
- **Documented bound (pre-edit)**: `directive.sh` 360s /
  `stop-poll-rearm.sh` 180s (`docs/handbooks/monitor-liveness.md`).
- **Measured**: 0 forced notifications across a 60-minute healthy,
  unchanging-roster simulation on the current build (section 2 above);
  the check itself resolves in 28.8ms once invoked (section 2 above).
  Worst-case detection latency during a healthy, quiet stretch with no
  other live Monitor/watch traffic is **unbounded** by any mechanism in
  this repository — it is whatever time elapses until an unrelated
  turn-triggering event occurs.
- **#1497/#2182 failure**: 388 idle minutes unobserved — canonical:
  issue #2915's own body (`gh issue view 2915`, fetched this turn),
  which states this figure; not independently re-derivable from
  `docs/issue-1497/reports/implementation.md` or
  `docs/issue-2182/reports/implementation.md`'s own text (checked,
  `grep -rn 388 docs/issue-1497/ docs/issue-2182/` returns nothing this
  turn) — the number is the issue's own citation, used here as given,
  not re-verified against a primary incident log that no longer states
  it in that form.
- **Stated verdict: the bound never held as a code-enforced guarantee
  since 2026-08-18 (#1732) — 12 days before the #2905/#2913 episode this
  issue was filed to examine — and has not held since #2913 either,
  because #2913 correctly reverted an accidental, buggy forcing cadence
  back to that same pre-existing #1732 state.** It is not worse than the
  388-minute incident (any turn, whenever it arrives, still catches it),
  but it is not the 360s/180s the handbook implied, and was not for all
  but one of the roughly 18 days preceding this record.

**5. Handbook correction (the fix this issue's Acceptance authorizes
only if the measurement is unacceptable — it is).** Edited
`docs/handbooks/monitor-liveness.md`:
- Disambiguated the "180 seconds (3x the 60s poll interval)" line: `60s`
  is `watchdog.POLL_INTERVAL_SEC` (the unrelated `spawn.py poll-due()`
  TTL gate both hooks also arm), not `on-the-record/monitors/
  poll-heartbeat.sh`'s own 120s tick sleep — a different-but-
  similarly-named interval, not a math error, but ambiguous as
  previously worded — checked directly: `grep -n
  "POLL_INTERVAL_SEC\s*=" watchdog.py` returns `60` this turn.
- Added a new subsection ("Issue #2915: the 360s/180s numbers were never
  an enforced upper bound") under "Structural limit," carrying the
  dated timeline and measured numbers from sections 3-4 above, and
  stating plainly that 360s/180s bound check-execution latency, not
  invocation frequency.
- Did **not** add any periodic content-free notification (the issue's
  first must-not) — the correction is prose-only; no code path changed,
  no watch-family signal touched, no overhead added.

## Why

**Diagnose-first was applicable and was invoked** (see skill-verdict
below): this is precisely "decide whether a documented bound holds" with
the reflex-to-fix already gated by the issue's own "only if the measured
answer is unacceptable" clause. Stage 0 (problem statement, no
solution/blame baked in) was already given by the issue text; Stage 1
(baseline) is section 2 above; Stage 2 (root cause, narrow-dig-verify,
Amdahl share) is section 3; Stage 3 (decision: is a mechanism fix
reversible/worth it) concluded **no** — both structural fixes are either
explicitly forbidden (a low-frequency periodic ping, the issue's own
must-not #1, and the exact defect #2913 just removed) or already
documented as an out-of-scope platform boundary (an OS-level scheduled
wake, pre-existing in this same handbook file before this edit) —
leaving "measure and document honestly, file a follow-up" as the correct
weight of response, matching the issue's own "only if unacceptable" gate
and its four standing invariants (no revived role axis, no new bugs, no
overhead increase, no monitor/watch breakage) trivially, since nothing
in the fix touches code.

**observability-methodology-selection was judged not applicable** and
was not invoked (see skill-verdict below): its trigger is choosing
exactly one signal methodology (RED/USE/Golden Signals) for a touched
*service surface*, or blocking a redundant methodology dashboard. This
issue diagnoses an existing turn-driven detection mechanism's actual
invocation cadence — no new signal surface is being added and no
methodology dashboard was proposed, so the skill's precondition never
arises.

## What did not work

None — every measurement in this record ran to a conclusion on the first
attempt; the enumeration, the two constructed measurements, and the
timeline dig all reproduced cleanly against the live tree with no
approach abandoned mid-way.

## Upstream basis

- `docs/issue-2906/reports/adversarial-review-30a89443.md` (verified,
  landed, sha `fed2e78d1e4e9f75e37384752d58dce3a249e586` merge into
  main) — established the qualitative "unbounded, until some other
  turn-driver fires" finding this record quantifies and dates precisely
  (the #1732-vs-#2905/#2913 timeline was not in that record; added
  here).
- `docs/handbooks/monitor-liveness.md` — edited in this same commit
  (`sha: same-commit`).
- Read directly, this turn, not restated from any record:
  `on-the-record/hooks/directive.sh`,
  `on-the-record/hooks/stop-poll-rearm.sh`,
  `on-the-record/hooks/poll-rearm.sh`,
  `on-the-record/hooks/hooks.json`,
  `on-the-record/monitors/poll-heartbeat.sh`,
  `on-the-record/monitors/poll_heartbeat_delta.py`,
  `watchdog.py` (`POLL_INTERVAL_SEC`),
  `docs/issue-1220/reports/implementation.md`,
  `docs/issue-1497/reports/implementation.md`,
  `docs/issue-1732/proposals/2026-08-18-drop-monitoring-active-heartbeat-line.md`,
  `docs/issue-2182/reports/implementation.md`.
- `gh issue view 2915` (fetched this turn) — source of the 388-minute
  #1497/#2182 figure cited in section 4 above.

## Open findings

- **Follow-up issue: a genuine bound requires an OS-level scheduled
  wake, which this repo cannot self-grant.** Drafted body: "Both
  structural fixes to the now-unbounded healthy-quiet detection gap are
  foreclosed inside a single session/hook model: a periodic
  content-free ping is the exact defect #2913 removed (issue #2915
  must-not #1), and no plugin-shipped `settings.json` permissions key
  grants a session-independent wake (`docs/issue-801/proposals/
  technical-feasibility.md`'s Hard boundary, restated in
  `docs/handbooks/monitor-liveness.md`). If a real bound is wanted, it
  needs an OS-level cron/launchd/systemd timer external to the session,
  invoking something like `spawn.py deadman-check` on its own schedule
  independent of any turn — scoped as its own issue since it is an
  operator/install-time concern, not a repo-code change." Not filed by
  this session (scribe-never-inventor invariant: filing issues is the
  orchestrator's job, not a spawned role's) — named here for the
  orchestrator to pick up.
- None other — the threshold-drift ambiguity (60s vs 120s "poll
  interval") issue #2915 asked to be checked was resolved in the
  handbook edit itself (section 5 above), not left open.

## Next steps

None — `loop_state: landed`. The measurement is complete, cited side by
side with the documented bound and the historical failure, and the
correction it authorized (documentation only, no code) has landed in
this same commit.

skill-verdict: diagnose-first — applied: invoked; called via the Skill
tool this turn before drafting the diagnosis — canonical: Skill tool
call this turn returned the full SKILL.md body. The measurement above
follows its Stage 0-3 shape (problem statement given by the issue,
numeric baseline in section 2, root-cause dig with Amdahl share in
section 3, and a Stage-3 reversibility check in "Why" concluding a
mechanism fix is not the right lever given the must-not list and the
pre-existing platform boundary).
skill-verdict: observability-methodology-selection — not-applicable: no
new signal surface or methodology dashboard is being added; this issue
diagnoses an existing detection mechanism's invocation cadence, not a
choice between RED/USE/Golden Signals for a touched service surface.
other mounted skills: not triggered
