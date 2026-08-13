# issue-1117 current-state survey

Skip condition: this is a scoped bugfix/behavior-change to one existing
script (monitors/poll-heartbeat.sh) plus one new test file and one new
structured doc entry — the issue's own Requirements/Acceptance already
fix the design (hash-based delta suppression, persisted beside the
existing TTL stamp, first-tick-always-emits, changed-output-always-emits).
No open design decision remains beyond "where does the hash live" and
"how is cadence relaxed", both resolved below. Scout is skipped under
the scout-directive's "spec leaves no design decision open" condition —
the field here is one existing repo, not an external product category.

## Write surfaces

- `on-the-record/monitors/poll-heartbeat.sh` — the due-tick branch
  (canonical: on-the-record/monitors/poll-heartbeat.sh:76-84, read this
  session) captures
  `report="$(python3 "${CHECKOUT}/spawn.py" watchdog --auto-respawn 2>&1)"`
  and unconditionally `printf`s it to stdout (the Monitor notification
  channel) every due tick, even when byte-identical to the prior tick.
  This is the interject the issue reports.
- TTL stamp precedent: `spawn.py:2112` `POLL_STATE = ROOT / "runs" /
  "poll_state.json"`, written by `poll_due()` (canonical: spawn.py:2116-2140,
  read this session) under an `fcntl` lock. The issue asks for a hash
  "persisted next to the poll TTL stamp" — bash cannot safely
  read-modify-write that JSON file concurrently with `poll_due()`'s own
  lock without importing that lock protocol into bash. Decision:
  persist the delta hash in a sibling file at
  `${CHECKOUT}/runs/poll_heartbeat_last_hash` (same `runs/` directory as
  `poll_state.json`, i.e. "next to" it) rather than adding a field
  inside `poll_state.json` itself — this avoids touching spawn.py's
  locked read-modify-write path at all, keeping the write set to the
  bash script only.
- A new test file at gates slash test_poll_heartbeat_delta.py is named
  verbatim by the issue's Acceptance section; canonical: this session
  ran `find . -iname "test_*heartbeat*"` against the repo root
  (/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-1117-implementation)
  and it returned only `on-the-record/monitors/test_poll_heartbeat.py` —
  the named acceptance path is new work, not an edit. That existing
  sibling test's `_run_heartbeat`-style harness pattern (fake
  `spawn.py`, `POLL_HEARTBEAT_MAX_TICKS`/`POLL_HEARTBEAT_SLEEP_SECONDS`)
  is the pattern to reuse.
- A new doc at docs slash product slash priorities.md is named verbatim
  by the issue's Requirements section; canonical: this session ran
  `ls docs` against the repo root and it listed no `product/` entry
  (only `decisions`, `handbooks`, `issue-*`, `proposals`, `reports`,
  `specs`) — so the named path is a new file, not an edit. This path
  sits outside the six standing docs/ buckets (_assets, decisions,
  handbooks, proposals, reports, specs) the role-handoff contract
  names — it is what the issue itself calls out as discharging a
  "product-capture-stopgate flag from the 2026-08-13 session, which the
  orchestrator cannot write itself per deliverable-guard". The issue
  text names this exact path verbatim, so it is followed as stated;
  this is flagged here as a placement-ladder edge case, not silently
  normalized into `docs/specs/`.

## Zero-role-session / relaxed-cadence requirement

The issue's third requirement ("When zero role sessions are running AND
board signals are unchanged, cadence may be relaxed") is phrased as
permissive ("may"), not mandatory, and is explicitly subordinate to
watch-coverage inviolability (#90) per the operator's own stated
ordering (delta-suppression noise reduction ranks below #90 and above
`ORCHESTRATE_OFF=1`, and cadence-relaxation is not separately ranked —
it reads as an elaboration of the delta-suppression mechanism itself,
not an independent third mechanism). Determining "zero role sessions
running" from bash would require a new roster read (e.g. shelling out to
`spawn.py roster` or equivalent), which is a materially larger and
riskier write-surface addition than hash-based output suppression, for
a soft ("may") requirement whose actual observable effect — fewer
interjects when nothing changes — is already delivered by delta
suppression alone: when zero sessions are running, the watchdog's own
report text is typically the stable empty-roster line, so the hash
comparison already suppresses repeat emission without any session-count
check. Decision: implement delta suppression only; do not add a
separate roster-count relaxed-cadence path in this change. This is
recorded as a scope decision in the proposal's Rationale, not a silent
drop — the observable acceptance criteria (suppress-unchanged,
emit-changed, emit-after-suppression, emit-first-ever) are all satisfied
by hash suppression alone, and #90 coverage is never touched by this
choice since hashing only ever suppresses byte-identical repeats.

## Existing test harness pattern (for the new gates/ test file)

Canonical: on-the-record/monitors/test_poll_heartbeat.py (read this
session). It fakes `spawn.py` via `FAKE_SPAWN_MARKER`/`FAKE_POLL_DUE`/
`FAKE_WATCHDOG_REPORT` env vars, runs `bash monitors/poll-heartbeat.sh`
as a subprocess with `POLL_HEARTBEAT_MAX_TICKS=1`/
`POLL_HEARTBEAT_SLEEP_SECONDS=0`, and reads `r.stdout`. The three
acceptance cases (identical-suppresses, changed-emits,
change-after-suppression-emits) map naturally to three separate test
functions, each running `poll-heartbeat.sh` twice in sequence against
the same `TOKENMAXXXER_CHECKOUT`/`HOME` (so the persisted hash file
carries state across the two invocations) rather than one
multi-tick script run — this matches the existing file's per-scenario
test-function shape.
