---
issue: 2915
role: adversarial-review-708b12ce
author: adversarial-review-708b12ce
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2917 round 2's own deliverable
loop_state: landed
upstream:
  - path: PR #2917 (head sha 93e674941e6fe291fe745f12a38028f7a31d77d9)
    sha: 93e674941e6fe291fe745f12a38028f7a31d77d9
  - path: docs/issue-2915/reports/adversarial-review-a74dca2a.md
    sha: same-commit
---

# issue-2915 — adversarial-review-708b12ce record

## What was done

Independent verification of PR #2917 round 2 (a response to round 1's
adversarial review, `docs/issue-2915/reports/adversarial-review-a74dca2a.md`,
landed via PR #2921). canonical: `gh pr view 2921` — result: `state:
MERGED`, this turn. Re-derived every claim from primary sources, not
the PR's own record or body — canonical: `git worktree add /tmp/pr2917wt
pr2917-head` and `git worktree add /tmp/mainwt origin/main`, both run
this turn, giving independent checkouts of the PR head
(`93e674941e6fe291fe745f12a38028f7a31d77d9`) and `origin/main` to diff
and execute code from directly.

other mounted skills: not triggered — both mounted skills
(adversarial-review, work-in-english) were reviewed against this task;
neither was invoked via the Skill tool this session (this session's own
work already followed both skills' intent by construction — structurally
independent evaluation against primary sources, and English-only
authoring — without a separate Skill-tool call), so no `skill-verdict:
applied` line is claimed for either.

### Verified true (no defect)

- **Boundary exactness of the 1800s check** — canonical:
  `on-the-record/monitors/poll_heartbeat_delta.py:218`
  (`if now - last_emit_epoch >= 1800:`). Drove the script directly (not
  the PR's own simulation scripts) with a state file forced to
  `last_emit_epoch=1000` — derived: `python3 /tmp/verify_delta.py`,
  this turn, result:
  ```
  now=2799 (delta 1799) stdout: ''
  last_emit_epoch: 1000
  now=2800 (delta 1800) stdout: '[monitor-heartbeat] issue-500/implementation: HEALTHY ...'
  last_emit_epoch: 2800
  ```
  No off-by-one at the bound: 1799s silent, 1800s fires, on a from-scratch
  harness independent of the PR's own `/tmp/issue2915r2/*.py`.
- **Periodicity over a long horizon** — derived: `python3
  /tmp/verify_periodic.py` (my own script, 90 ticks × 120s = 3h), result:
  `emit ticks: [0, 1800, 3600, 5400, 7200, 9000]`, gaps `[1800, 1800, 1800,
  1800, 1800]` — matches the PR's own 90-tick claim, independently
  reproduced.
- **Realistic multi-entry roster volume is bounded, not explosive** —
  derived: `python3 /tmp/verify_delta.py` `scenario_multi_entry_roster_volume`,
  this turn, result: a 5-entry roster at the 1800s bound emits exactly 5
  `[monitor-heartbeat]` lines (one per tracked entry), not a combinatorial
  or repeated blow-up.
- **A normally-changing roster never reaches the beacon branch** —
  derived: same script, `scenario_changing_roster_never_uses_beacon`,
  this turn: four consecutive ticks with a changing workspace-summary
  each emit via the pre-existing `to_emit` path (`[poll-report] ... 손댄
  파일 N건`), never touching the `else` 1800s branch at all — structurally
  guaranteed by the `if to_emit: ... else: ...` shape
  (`poll_heartbeat_delta.py:212-218`), confirmed by reading the control
  flow directly.
- **#2913's suppression logic is byte-identical** — derived: `diff <(cd
  /tmp/mainwt && sed -n '1,216p' on-the-record/monitors/poll_heartbeat_delta.py)
  <(cd /tmp/pr2917wt && sed -n '1,216p' on-the-record/monitors/poll_heartbeat_delta.py)`,
  this turn, result: no output (identical). Everything through the
  `if to_emit:` branch — the entire `#2913` delta-suppression path — is
  untouched; round 2's diff is confined to the pre-existing `else` branch.
- **Content is real, not a fixed string** — derived: same script,
  `scenario_content_changes_with_state`, this turn: two beacon emissions
  with different `마지막 도구 호출` timestamps in the input produce
  `[monitor-heartbeat]` lines with different text (`Bash
  (...T00:00:01Z...)` vs `Read (...T05:00:00Z...)`), confirming
  `curr[k].split("] ", 1)[1]` (poll_heartbeat_delta.py:273) carries the
  entry's real current line, not a static phrase.
- **Post-landing correction (claim g) is factually correct** — canonical:
  `watchdog.py:1762-1766` (repo root, PR worktree `/tmp/pr2917wt`):
  ```
      if not d:
          print("돌고 있는 스킬 세션 없음")
          if not anomaly_count:
              print("이상 신호 없음")
          return anomaly_count
  ```
  derived: `python3 -c "import re; TAG_RE=re.compile(r'^\[(poll-report|watchdog|health|reconcile|orphaned|resume|watchdog-crash|returned-pr)\]\s*([^:]+):'); print(TAG_RE.match('돌고 있는 스킬 세션 없음')); print(TAG_RE.match('이상 신호 없음'))"`,
  this turn, result: `None` / `None`. Real production empty-roster output
  never carries a `[poll-report]` tag, so `TAG_RE` never keys it. This
  independently reproduces the same conclusion as the warrant-hunt the PR
  discloses (`docs/reports/2026-08-31-hunt-round2-heartbeat-beacon.md` —
  untracked here on this repo's `main`, PR-branch only; read via
  `/tmp/pr2917wt`). The corrected comment
  (`poll_heartbeat_delta.py:236-241`) is right; the original comment it
  replaced was wrong about *why* (crediting the `poll-report:roster`
  exclusion, which is inert against real input and only matters for the
  test's own synthetic fixture).
- **Test count** — derived: `cd /tmp/pr2917wt && python3 -m pytest
  on-the-record/monitors/test_poll_heartbeat.py -q`, this turn, result:
  `35 passed`; `cd /tmp/mainwt && python3 -m pytest
  on-the-record/monitors/test_poll_heartbeat.py -q`, this turn, result:
  `33 passed`. 35 = 33 + 2, matching the claimed "33 pre-existing + 2 new"
  exactly.
- **Thirteen-day arithmetic** — derived: `echo $(( ($(date -d 2026-08-31
  +%s) - $(date -d 2026-08-18 +%s)) / 86400 ))`, this turn, result: `13`.
  Correction is right.
- **Third call site is real and test-only** — canonical:
  `tests/run-orchestrate-tests.sh:18` (PR worktree):
  ```
  out=$(env -u CLAUDE_SKILL /bin/bash "$H/directive.sh" | head -1)
  ```
  confirmed this execs `directive.sh` directly outside `hooks.json`'s
  wiring; the staleness-check function runs unconditionally near the
  bottom of `directive.sh`, so this test invocation also exercises it,
  as disclosed.
- **`run-orchestrate-tests.sh` failure count is pre-existing** — derived:
  `bash tests/run-orchestrate-tests.sh 2>&1 | grep -c '^FAIL'`, this
  turn, result: `7` on both `/tmp/pr2917wt` and `/tmp/mainwt` — identical
  count on both trees, so not a regression.
- **No overhead/no monitor-watch breakage** — canonical:
  `poll_heartbeat_delta.py:200-218`'s `if/else`: the new code only
  executes inside the already-rare branch (`to_emit` empty *and* 1800s
  elapsed); `ALWAYS_RE`-matching lines (STALLED/CRASHED/COMPLETED/
  watcher-dead) make `to_emit` non-empty, so the new branch is
  structurally unreachable whenever an always-emit anomaly is present —
  this diff does not restructure that `if/else`. No revival of any
  retired role axis — the diff touches only `poll_heartbeat_delta.py`'s
  1800s branch, its test file, and two handbook/comment files (`gh pr
  diff 2917 --name-only`, this turn).

### Finding 1 (MAJOR) — the "~1800s dead-Monitor detection latency" bound measures silence-while-alive, not detection-after-death, and contradicts the handbook's own adjacent, unmodified section

canonical: `docs/handbooks/monitor-liveness.md:120-127` (PR worktree;
pre-existing, **unmodified** by round 2's diff — confirmed: this text
sits above the diff's insertion point at line 138, and `gh pr diff 2917`'s
hunk only adds content starting at that line):

```
## Structural limit: full-idle death cannot self-heal

Both `directive.sh` and `stop-poll-rearm.sh` are **turn-driven** — they
only fire on a UserPromptSubmit or Stop event, i.e. when the session
receives or finishes handling a user turn. If the Monitor dies during a
fully idle stretch (no user turn arriving at all, and no Monitor left to
tick), nothing in this repo observes that death or emits the re-arm
directive until the next turn actually happens.
```

canonical: `docs/handbooks/monitor-liveness.md`'s new "Issue #2915"
section (PR worktree), round 2's own addition, ~15 lines below the above:

```
**Worst-case detection latency for a dead Monitor during a healthy,
quiet, tracked-roster stretch is now bounded at ~1800s (30 minutes) from
the build's own turn-independent tick loop, down from round 1's
unbounded measurement**
```

These two claims describe the *same* failure mode (the Monitor process
dying during a stretch where nothing else forces a turn) and reach
opposite conclusions (unbounded vs. bounded at 1800s), twenty lines
apart in the same file, without round 2 reconciling them.

The reconciliation the PR does not attempt: the `[monitor-heartbeat]`
beacon can only be emitted *by the Monitor's own tick loop*. A tick loop
that has actually died cannot emit one more beacon to announce its own
death — the same structural fact the "Structural limit" section states
in general terms. What round 2 actually measures and bounds (verified
above, independently reproduced) is *how long a still-alive, healthy,
content-suppressed Monitor can go without producing any stdout* — a real
and useful property (it restores the "channel doesn't go dark while
alive" guarantee `#1220` originally provided and `#1732`/`#2913` each
removed, in content-carrying form this time). It is not the same
quantity as "elapsed wall-clock from actual death until surfaced to an
orchestrator," which is what issue #2915's acceptance check literally
asks to measure. For the instant the Monitor actually stops running,
detection still depends entirely on some unrelated event (a real user
turn) happening next — exactly as unbounded as before this PR, on both
round 1 and round 2, and exactly as the "Structural limit" section
already says.

Supporting evidence that the claimed detection path (an "external
orchestrator watching the Monitor's stdout stream") has no built
consumer — derived: `grep -rn "monitor-heartbeat" --include="*.py"
--include="*.sh" --include="*.md" .` (PR worktree), this turn: the only
hits are the emitting code, its own comments, the two new tests, and the
handbook's own prose describing the intended consumer. No code anywhere
in the repository (checked `relay.py`, `hook_fires.py`, `watchdog.py`,
`spawn.py`, all of `on-the-record/hooks/*.sh`) reads a
`[monitor-heartbeat]` line, tracks "time since the last one," or emits an
alert on its absence — unlike the pre-existing `poll_heartbeat_alive.json`
+ staleness-check mechanism, which *does* have a real, coded
check-and-alert consumer (`directive.sh`/`stop-poll-rearm.sh`, printing
`[MONITOR-DEAD]`). The claim that "presence on this ~1800s cadence is
legible to an external orchestrator ... as 'still alive'" is asserted,
not built or demonstrated in this diff.

There is independent, previously-established evidence (from a *different*,
already-merged review) that non-empty Monitor stdout does correlate with
a forced turn while the Monitor is alive — canonical:
`docs/issue-2906/reports/adversarial-review-30a89443.md:196-198,208-211`
(read in this repo's own `main`, this turn):
```
`printf` only runs `if [ -n "${diff_output}" ]` — a fully-suppressed
tick produces zero stdout, so no Monitor task-notification fires for
that tick at all (not merely a quiet notification; no notification).
...nearly every tick emitted, nearly every tick forced a turn, and each
turn re-ran the turn-driven staleness check for free.
```
This corroborates that round 2's beacon likely *does* force turns while
the Monitor is alive (restoring pre-`#2913` cadence, narrower in scope).
It does not, and cannot, extend that forcing past the instant the
Monitor itself dies — which is the specific quantity the issue asks to
bound. Round 2's record and the handbook's new section should have
scoped the claim to "silence-while-alive" rather than headlining it as
"dead-Monitor detection latency... bounded," which is what a reader
acting on the must-not ("must not let a session be unobserved for longer
... any change must be shown to shorten ... the measured latency") would
take away.

This also means round 2's own "what remains unbounded" disclosure draws
too sharp a line between the empty-roster case (disclosed unbounded) and
the non-empty tracked-roster case (claimed bounded): for the literal
failure mode of *the Monitor process itself dying*, both are equally
unbounded, for the same reason, independent of roster content.

### Finding 2 (MINOR) — the true worst-case gap is 1800s plus up to one tick interval, not exactly 1800s

canonical: `poll_heartbeat_delta.py:218`, `now - last_emit_epoch >= 1800`
— this fires on the first tick where elapsed time is *at least* 1800s,
so with real, non-tick-aligned timing the gap can exceed 1800s by up to
one inter-tick interval. Derived: `python3 /tmp/verify_jitter.py` (my own
script, irregular tick spacing averaging ~131.75s, not a divisor of
1800), this turn, result: `emit times: [0, 1852, 3689, 5541, 7378, 9230,
11067]`, `gaps: [1852, 1837, 1852, 1837, 1852, 1837]`, max gap `1852`.
canonical: `poll-heartbeat.sh:184`,
`sleep_seconds="${POLL_HEARTBEAT_SLEEP_SECONDS:-120}"` — with the real
120s tick loop, worst case is up to `1800 + 120 = 1920s` (~32 min), not
exactly 1800s/30min. This does not change the order-of-magnitude
conclusion ("roughly 30 minutes" is still a fair characterization) and is
not a bug in the check — it is inherent to any `>=`-threshold check
against a tick interval that doesn't evenly divide the bound — but the
record's "~1800s (30 minutes)" phrasing slightly understates the real
worst case.

### Finding 3 (confirmed non-issue) — attack point 3's "new spawn into a dead-Monitor roster" scenario

canonical: `grep -n "poll_rearm_arm_if_due\|monitor_liveness" spawn.py`
(PR worktree), this turn — no hits: spawning does not itself invoke the
staleness check. However, issuing a new spawn command is, by
construction, part of an active orchestrator turn, and `directive.sh`
(UserPromptSubmit) already fires at the start of any such turn and
`stop-poll-rearm.sh` (Stop) at its end — so a new spawn arriving is
itself a turn-inducing event that triggers the pre-existing staleness
check, regardless of round 2. This is unchanged, pre-existing behavior,
not broken or improved by this PR — consistent with Finding 1's
conclusion that round 2 does not touch the actual Monitor-death detection
path at all.

## Why

The task named five specific attack points; the review above resolves
each. (1) The 1800s bound is exact and reproducible on independent
construction — canonical: the boundary and periodicity results in
"Verified true" above, derived this turn from my own scripts, not the
PR's — with a real (minor) tick-interval slack noted in Finding 2. (2)
The inverse re-noise risk is checked and clean — bounded per-entry
volume, structural inability to fire on a changing roster, and
byte-identical `#2913` suppression logic, all derived above. (3) The
empty-roster disclosure is accurate as far as it goes, but investigating
it surfaced a larger point in Finding 1 — the non-empty case round 2
claims to have *fixed* is, for actual Monitor death, in the same
unbounded position as the empty case. (4) The content-carrying property
is real, verified above by varying input and observing the emitted text
change. (5) canonical: the `TAG_RE.match(...)` → `None`/`None` result
derived above, this turn, against the real `watchdog.py:1762-1766` text —
the post-landing correction is confirmed correct by that independent
re-derivation, not merely by reading the PR's own account of it.

## What did not work

None — every scripted verification in this review ran to a clean,
reproducible result on scripts I wrote myself (`/tmp/verify_delta.py`,
`/tmp/verify_periodic.py`, `/tmp/verify_jitter.py`), independent of the
PR's own `/tmp/issue2915r2/*.py` harness.

## Upstream basis

- PR #2917 (round 2), head sha `93e674941e6fe291fe745f12a38028f7a31d77d9`
  — read via `gh pr diff 2917`, `gh pr view 2917`, and a `git worktree
  add` checkout at `/tmp/pr2917wt`, this turn.
- `origin/main` at `6db165ce` — `git worktree add` checkout at
  `/tmp/mainwt`, this turn, used for all before/after diffs and test-count
  comparisons.
- `docs/issue-2915/reports/adversarial-review-a74dca2a.md` (round 1's
  independent review) — canonical: `gh pr view 2921` this turn, result:
  `state: MERGED` — read for what round 2 claims to respond to; not
  treated as authoritative for round 2's own claims.
- `docs/issue-2906/reports/adversarial-review-30a89443.md` (present in
  this repo's own `main`) — cited above as independent, pre-existing
  evidence for the stdout-forces-a-turn mechanism.

## Open findings

- **Finding 1 (MAJOR)**: round 2's "dead-Monitor detection latency ...
  bounded at ~1800s" claim, and the handbook section stating it,
  conflate "silence duration during a live, healthy, suppressed stretch"
  with "wall-clock time from actual death to detection." The two are
  different quantities; the PR measures and bounds the first, the
  issue's acceptance check and the PR's own headline claim the second.
  Resolution path: rescope the claim in `docs/handbooks/monitor-liveness.md`'s
  "Issue #2915" section to state plainly what is actually bounded
  (silence-while-alive), reconcile it explicitly with the adjacent,
  unmodified "Structural limit: full-idle death cannot self-heal"
  section rather than leaving the two in unacknowledged tension, and — if
  detecting actual Monitor *death* via this channel is still wanted —
  either build a real consumer that tracks "time since last
  `[monitor-heartbeat]`" (this PR does not), or drop the "detection
  latency" framing for this mechanism and describe it only as an
  aliveness/observability improvement.
- **Finding 2 (MINOR)**: state the worst-case bound as "~1800s plus up to
  one tick interval" (≈1920s with the real 120s loop) rather than a flat
  1800s/30min, or leave as-is with a footnote — low priority, does not
  change the order-of-magnitude conclusion.
- No other open findings; verified-true items above require no follow-up.

## Next steps

None from this record — per role scope, this session evaluates PR #2917
round 2 and does not fix it. `loop_state: landed`.
