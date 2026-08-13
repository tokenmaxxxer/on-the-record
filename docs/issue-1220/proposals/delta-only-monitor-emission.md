---
status: proposed
files:
  - on-the-record/monitors/poll-heartbeat.sh
  - gates/test_poll_heartbeat_delta.py
---

## Request

The 60s watchdog Monitor prints something every tick — a "skipped (within
TTL)" line on non-due ticks, and (per #1117) a whole-text hash comparison
on due ticks that re-emits the FULL report on any single-byte diff. #1220
asks for true delta-only emission: no output at all when nothing changed
(no "skipped" lines, no all-healthy dumps), only the delta when something
did change, with crash/respawn/new-PR/drift-appear/watcher-dead
transitions always surfacing, and a bounded ~30min aliveness heartbeat
allowed as the quiet-period signal. Observation cadence and machinery
(spawn.py polling, roster scan, respawn) stay untouched — presentation
only.

## Constraints

- Observation unchanged: `spawn.py poll-due` / `watchdog --auto-respawn`
  keep running every tick exactly as today; nothing about polling cadence,
  state files, respawn, or crash detection may change (issue req #2,
  watch-coverage inviolable).
- A regression test must assert a crashed-session tick still emits under
  delta suppression (issue req #2, explicit acceptance check).
- Composes with #1219 (target anchoring) — that session is in flight on
  the same monitor file family; this proposal's diff is scoped to
  `poll-heartbeat.sh`'s printing logic only, not `roster_watchdog()`'s
  scan logic, to minimize overlap. Rebase before landing if #1219 lands
  first.
- Must stay inside the existing `gates/test_poll_heartbeat_delta.py`
  fake-spawn.py harness (`POLL_HEARTBEAT_MAX_TICKS`,
  `POLL_HEARTBEAT_SLEEP_SECONDS`, `FAKE_WATCHDOG_REPORT`) — no new test
  infra.

## Rationale

Two structural options were on the table:

1. **Line-level diff inside `poll-heartbeat.sh`** (chosen): split the
   captured watchdog report text into lines, keyed by session/entry
   prefix (`[poll-report] {key}:`, `[watchdog] {key}:`, `[health] {key}:`,
   `[reconcile] {key}:`, `[orphaned] {key}:`), and diff that keyed set
   against the previous tick's keyed set (persisted as JSON next to the
   existing `runs/poll_heartbeat_last_hash` sibling-file convention).
   Unchanged keys print nothing; new/changed/vanished keys print their
   line. A fixed set of line-prefixes is always emitted regardless of
   diff outcome: `[watchdog]` lines are already emitted per-session by
   `roster_watchdog()`, so the always-emit set is expressed as key
   *categories* (dead/STALLED/orphaned/resume labels), not by adding new
   parsing of `roster_watchdog()` internals.

2. **Push the diffing into `spawn.py:roster_watchdog()` itself**
   (rejected): have the Python scan compare against a persisted prior
   snapshot and only `print()` changed lines. This would centralize the
   diff logic next to the state it diffs (arguably cleaner), but it
   changes `roster_watchdog()`'s stdout contract — that function's output
   is also written verbatim to
   `${HOME}/.claude/tokenmaxxxer/poll-watchdog.log` for audit/history and
   consumed by other callers (`spawn.py watchdog` CLI, direct operator
   invocation) that expect the full per-tick report, not a suppressed
   one. Diffing there would silently thin the audit log and any
   non-Monitor caller's view, not just the Monitor's. Keeping the diff at
   the presentation edge (`poll-heartbeat.sh`, which already owns the
   #1117 hash-suppression precedent) preserves `roster_watchdog()` as the
   full-fidelity source of truth and confines "visibility only" to
   exactly the layer the issue names as in scope.

Line-level diffing (option 1) also directly satisfies "a snapshot with a
new drift item emits exactly the delta" — a whole-text hash (current
state) cannot express partial change; a keyed line diff can.

## What will be done

- In `poll-heartbeat.sh`'s due branch, replace the whole-text SHA-256
  hash compare with: split `printed_text` into lines, extract each
  line's leading `[tag] key:` prefix as its diff key. A line without a
  recognized prefix is keyed relative to the nearest preceding tagged
  line plus its own ordinal offset under that line (e.g. `roster_watchdog()`'s
  `  - {a}` anomaly-detail bullets under a `[watchdog] {key}: 이상 신호
  N건` header key as `{parent_key}#0`, `{parent_key}#1`, ... — not a
  single shared key, since anomaly counts vary tick to tick and a shared
  key would silently drop all but one bullet). A true singleton line with
  no tagged parent at all (e.g. "이상 신호 없음", "돌고 있는 역할 세션
  없음") keys to a fixed constant. Diff the resulting `{key: line}` map
  against the previous tick's (JSON, persisted at
  `runs/poll_heartbeat_last_state.json` alongside the existing
  `poll_heartbeat_last_hash` file — both kept during transition, old hash
  file becomes unused once the new state file lands).
  - Unchanged keys: emit nothing for that key.
  - New or changed keys: emit that key's line.
  - Keys tagged as always-emit categories — `[resume]`, dead-session
    labels (STALLED/COMPLETED/CRASHED-style `[poll-report]` lines for
    entries that are `!_alive()`), `[orphaned]` — always print even when
    unchanged from the previous tick, per issue req #3.
  - First-ever tick (no prior state file) emits everything once (issue
    Acceptance "empty state" check).
- Remove the unconditional `echo "poll tick: skipped (within TTL)"` in
  the non-due branch — that branch becomes silent (no stdout) on a normal
  within-TTL tick.
- Add a bounded periodic heartbeat: track last-heartbeat timestamp in the
  same state file; if >=30 minutes have elapsed since the last emission
  of any kind, print one bounded aliveness line ("monitoring active, N
  sessions healthy, no changes") and update the timestamp — this fires
  even on an otherwise-fully-suppressed due tick.
- Extend `gates/test_poll_heartbeat_delta.py` with: (a) a test that two
  consecutive due ticks with a single changed session line emit only that
  session's line, not the full report; (b) a test that a `FAKE_WATCHDOG_REPORT`
  containing a dead/STALLED-labeled line emits every tick even when
  unchanged (the req #2 regression guard); (c) a test that the non-due
  branch produces empty stdout; (d) a test that the very first tick emits
  the full initial state once; (e) a test that a `[watchdog] {key}: 이상
  신호 N건` header followed by multiple `  - {a}` bullet lines round-trips
  through the diff intact across two identical ticks (all bullets present
  on tick 1, none dropped, none re-emitted on tick 2) — the ordinal-key
  regression guard for the warrant-hunt finding on this proposal (variable
  bullet counts must not collapse onto one shared key).

## Out of scope

- Any change to `spawn.py:roster_watchdog()`'s scan logic, `_board_wide_sweep()`,
  `diagnose_health()`, or the `ledger_check_and_stamp()` escalation-dedup
  path — those compute state; this proposal only changes what
  `poll-heartbeat.sh` chooses to print from the text they already produce.
- #1219's target-anchoring fix — coordinated by file-scope only (this
  proposal touches `poll-heartbeat.sh`'s printing branch and the delta
  test file; #1219 is expected to touch a different concern in the same
  monitor family, per the issue's own note to rebase).
- Consumer-session-side wiring beyond the shared `poll-heartbeat.sh`
  script itself (issue req #4 "applies to both" is satisfied by both
  dev-session and consumer-session monitors invoking the same script).

## How you'll know it worked

- Hermetic: `python3 gates/test_poll_heartbeat_delta.py` — the new and
  existing cases all pass, including two identical ticks emitting nothing
  on the second, a changed-entry tick emitting only that entry's line, a
  crashed-session tick always emitting, and the first-ever tick emitting
  the full initial state once.
- Live: after this lands, an idle window of 10+ minutes in a session with
  the Monitor running produces no visible monitor messages beyond at most
  one bounded heartbeat, and an induced state change (e.g. a new PR
  appearing) surfaces within one tick.
