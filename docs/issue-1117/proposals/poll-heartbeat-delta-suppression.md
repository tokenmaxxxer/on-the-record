---
status: proposed
files:
  - on-the-record/monitors/poll-heartbeat.sh
  - gates/test_poll_heartbeat_delta.py
  - docs/product/priorities.md
---

# poll-heartbeat delta-suppression (issue #1117)

## Request

The plugin Monitor heartbeat (on-the-record/monitors/poll-heartbeat.sh,
via monitors/monitors.json, when: always) wakes an idle session every
~60s due tick and, since issue #922, echoes the captured watchdog report
verbatim on stdout even when byte-identical to the previous tick — this
produces a repeated "대기중입니다" waiting-turn interject and Monitor
noise while zero role sessions are running. Suppress emission on a due
tick whose captured output is unchanged from the previous emitted tick,
while any changed output must still emit (#90 watch-coverage is
inviolable). Also record the operator's stated priority ordering as a
structured entry in docs/product/priorities.md.

## Constraints

- #90 watch-coverage inviolable: any tick whose captured output differs
  from the last emitted tick MUST emit — zero coverage regression.
- First-ever tick (no stored hash yet) MUST emit.
- A change arriving right after a run of suppressed identical ticks
  MUST emit (change-after-suppression case).
- New test file at gates/test_poll_heartbeat_delta.py, driving
  monitors/poll-heartbeat.sh via POLL_HEARTBEAT_MAX_TICKS /
  POLL_HEARTBEAT_SLEEP_SECONDS, per the issue's Acceptance section.
- The operator's priority ordering (watch-coverage inviolable #90 >
  delta-suppression noise reduction > ORCHESTRATE_OFF=1 full-off, last
  resort only) must land in docs/product/priorities.md as a structured
  entry — this is the path the issue names verbatim to discharge a
  product-capture-stopgate flag the orchestrator cannot write itself.
- Kill switch (ORCHESTRATE_OFF=1) and existing not-due/error branches of
  poll-heartbeat.sh must keep their current behavior unchanged.

## Rationale

Chosen approach: compute a hash of each due tick's captured watchdog
report inside poll-heartbeat.sh itself, compare it against a hash
persisted in a plain sibling file next to the existing poll TTL stamp
(runs/poll_state.json), and skip the `printf` of the report when it
matches — emit and update the stored hash otherwise.

Alternative considered and rejected: extend spawn.py's `poll_due()` (or
`POLL_STATE`/poll_state.json itself) to also carry the last-report hash,
keeping ALL poll-cadence state in the one Python-owned, `fcntl`-locked
JSON file. Rejected because `poll_due()`'s lock protocol exists to
serialize TTL check-and-stamp across three independent bash callers
(directive.sh, stop-poll-rearm.sh, poll-heartbeat.sh itself) that all
call it as a subprocess — teaching bash to also read-modify-write a
field inside that same locked JSON file from poll-heartbeat.sh (the only
caller that would ever write the hash) means either adding a new Python
subcommand to spawn.py just to wrap that one write, or hand-rolling JSON
mutation in bash against a file another process locks — both a larger,
riskier write surface than a plain hash file bash can write directly,
for no shared benefit (nothing else ever needs to read the hash).

Alternative considered and rejected for the "zero role sessions ...
cadence may be relaxed" requirement: add a live roster-session count
check to poll-heartbeat.sh (e.g. shelling out to a `spawn.py roster`-
style read) so the loop's sleep interval itself lengthens when zero
sessions are running. Rejected for this change: the requirement is
phrased permissively ("may be relaxed"), is not covered by the
Acceptance section's three named test cases, and its observable
effect — fewer interjects when nothing is happening — is already
delivered by delta suppression alone, since an idle, zero-session board
produces the watchdog's own stable empty-roster report, which hashes
identically tick to tick and is suppressed after the first tick. Adding
a second, independent roster-read mechanism widens the write set for no
additional acceptance coverage and risks a bash/roster coupling that is
easy to get wrong under #90. This is a scope decision, not a silent
drop — recorded here and in the survey.

## What will be done

- In on-the-record/monitors/poll-heartbeat.sh's due-tick branch: after
  capturing `report`, compute a hash of it (e.g. `sha256sum`), compare
  against the contents of a sibling state file
  (`$(dirname "${CHECKOUT}/runs/poll_state.json")/poll_heartbeat_last_hash`,
  i.e. `${CHECKOUT}/runs/poll_heartbeat_last_hash`). If the file is
  absent (first-ever tick) or its contents differ from the new hash:
  print the report (or the existing "no output" fallback line)
  unchanged as today, and write the new hash to the state file. If the
  file exists and matches: skip the `printf`/echo entirely (no stdout
  for that tick) while still appending to the existing
  poll-watchdog.log file as today (log coverage is untouched — only the
  Monitor-surfaced stdout is suppressed).
- Not-due ticks, poll-due-crash ticks, and the ORCHESTRATE_OFF kill
  switch keep their exact current behavior — the hash logic only wraps
  the due-tick captured-report branch.
- Add gates/test_poll_heartbeat_delta.py reusing the fake-spawn.py /
  POLL_HEARTBEAT_MAX_TICKS / POLL_HEARTBEAT_SLEEP_SECONDS harness
  pattern from on-the-record/monitors/test_poll_heartbeat.py, covering:
  (a) two consecutive identical due ticks against the same checkout/HOME
  — second tick's stdout carries no report text; (b) a due tick with
  different report text from any prior state — emits; (c) an identical
  tick followed by a changed tick — the changed one still emits; and the
  empty-state case (fresh HOME/checkout, first tick) — always emits.
- Add docs/product/priorities.md with a structured entry recording the
  operator's priority ordering quoted in the issue: watch-coverage
  inviolable (#90) > delta-suppression noise reduction (this issue) >
  full off via ORCHESTRATE_OFF=1 (last resort only), with a one-line
  rationale per tier and a source pointer back to issue #1117.

## Out of scope

- Any change to spawn.py, poll_due(), poll_state.json, or the `fcntl`
  lock protocol.
- A live roster/session-count read to relax the sleep cadence itself
  (see Rationale) — delta suppression is the only mechanism this change
  adds.
- Changes to directive.sh or stop-poll-rearm.sh (the other two
  poll_rearm_arm_if_due() callers) — untouched, as today.
- Any change to on-the-record/monitors/test_poll_heartbeat.py itself —
  the new delta-suppression coverage lands in its own new file per the
  issue's Acceptance section, not folded into the existing one.

## How you'll know it worked

- `python3 gates/test_poll_heartbeat_delta.py` (or pytest collection of
  it) passes, exercising all three named Acceptance cases plus the
  fresh-state (first-tick-always-emits) case.
- `python3 on-the-record/monitors/test_poll_heartbeat.py` still passes
  unchanged (no regression to due/not-due/kill-switch/report-passthrough
  coverage).
- Manual read of the diff confirms the not-due, poll-due-crash, and
  ORCHESTRATE_OFF branches of poll-heartbeat.sh are byte-identical to
  before this change.
- docs/product/priorities.md exists and states the three-tier ordering
  from the issue in a structured (not narrative-only) form.

Proposal: docs/issue-1117/proposals/poll-heartbeat-delta-suppression.md
