---
status: approved
files:
  - gates/patrol_promote.py
  - gates/test_patrol_promote.py
  - docs/issue-1589/reports/implementation.md
---

## Request

Build the C2 stage of the patrol board program: when a human ticks a
finding's checkbox on a role's patrol board (Pending Approval), promote
it to a real, structured per-finding GitHub issue exactly once
(fingerprint search before create), move the board line to
"Approved / In Progress", enforce rate caps (2 promotions/hour/role, 10
open patrol issues/role) with a "queued: rate cap" board annotation
instead of dropping, and never let patrol's own issues/edits re-trigger
patrol. Work-start orchestration itself (classification, spawn) is out
of scope — this issue ends at creating the promoted issue and moving the
board line.

## Constraints

- Depends on #1586 (contract), #1592 (C1 board), #1587/#1593 (judge
  transport, real findings) — all landed on main.
- Must reuse gates/patrol_board.py's select_board_entries for role
  scoping (scanner_id first, path-prefix second) — binding integration
  note from the #1592 review; no re-derivation.
- Must reuse gates/patrol_trigger.py for its existing file-path anti-loop
  guard rather than duplicating it.
- Contract PCC-2/PCC-3 (docs/specs/patrol-channel-contract.md): only a
  tick may create the real issue; an untriaged finding never becomes a
  standalone issue.
- No new dependency, no env var, no migration.

## Rationale

Tick detection needs a way to tell "already-ticked-and-already-promoted"
apart from "newly ticked this run," since a promoted line stays checked
forever afterward.

Considered: re-derive ticks from the live board body alone, with no
stored prior state — for every `- [x]` line, treat it as fresh unless a
promoted-issue marker with that fingerprint already exists (an
idempotence lookup against GitHub, not a local diff). Rejected: this
still requires exactly the same fingerprint-marker index the chosen
design needs for its own idempotence step, but forces it onto the hot
path for every polled tick (an extra `gh issue list` search per ticked
line, per poll) instead of an O(1) local-state check for the 99% case
of "already promoted, nothing to do." It also can't cheaply distinguish
a tick from a genuine transition versus a board line whose checked state
was carried over verbatim by patrol_board.py's own edit-in-place
(patrol_board.py never un-checks a line), so it would re-run the
idempotence search on every single poll forever, not just once at the
transition — needless load against contract PCC-5's rate-cap spirit.

Chosen instead: store the last board body patrol_promote.py itself
processed (separate small state file from patrol_board.py's own ETag
cache, since the two run independently), diff old-vs-new via
patrol_board.parse_board_body plus a line-level checkbox scan, and only
treat a line that flips `[ ]` -> `[x]` between the two stored bodies as
a fresh tick. The idempotence fingerprint-marker search still runs (as
the issue's acceptance criterion requires: "fingerprint search before
create"), but only once per detected transition, not once per poll.

## What will be done

- gates/patrol_promote.py:
  - `detect_ticks(prior_body, new_body, queue) -> list[dict]` — pure
    function: parse both bodies' Pending sections via
    patrol_board.parse_board_body, find lines whose fingerprint prefix
    was `[ ]` in prior and `[x]` in new, resolve each 12-char prefix
    back to its full queue entry (unique prefix match over `queue`).
  - `build_finding_issue_body(entry) -> str` — structured body:
    fingerprint, rule/baseline ID (scanner_id), file:line@SHA (path +
    last_seen), severity, evidence (excerpt), proposed direction
    (finding_class-derived boilerplate line), plus the anti-loop marker
    `<!-- patrol:promoted fp=<full fingerprint> -->`.
  - `find_existing_promotion(root, fingerprint) -> int | None` — `gh
    issue list --label patrol-promoted --state all --search
    <fingerprint prefix>` then grep the marker in each hit's body for
    the full fingerprint; returns the issue number if found (idempotence
    check — same tick never files twice, survives process restarts).
  - Rate-cap state: `.git/patrol-promote/<role>.json` —
    `{"promotions": [<iso8601>, ...], "open_issue_numbers": [...]}`.
    `rate_cap_ok(state, now) -> (bool, bool)` — (hourly_ok, open_ok),
    each checked independently per PCC-5.
  - `promote_tick(root, role, entry, state, now) -> dict` — orchestrates:
    idempotence search first (never re-create even under cap); if not
    found, check both caps; over either cap, return
    `{"promoted": False, "reason": "rate_cap"}` (caller annotates the
    board line "queued: rate cap" rather than dropping it, and leaves it
    ticked so the next window's poll retries); under cap, `gh issue
    create --label patrol-promoted --label "finding" --label
    "role:<role>" --label "severity:<sev>"`, record the new promotion
    timestamp + issue number into `state`, return
    `{"promoted": True, "issue": N}`.
  - `move_ticked_line(board_body, fp_prefix, issue_number, annotation=None)
    -> str` — moves the matching Pending line into Approved / In
    Progress (or re-writes it in place with a
    "(queued: rate cap)" suffix if not promoted this run, keeping it
    ticked and in Pending for retry).
  - `run_patrol_promote(root, role, dry_run) -> dict` — imperative
    shell: reads current board body (reuse
    patrol_board.find_board_issue), reads/writes the small prior-body
    state file, reads the queue, calls detect_ticks, promote_tick per
    detected tick, rewrites the board body once (respecting
    patrol_board's one-edit-per-run budget accounting via
    patrol_board.write_budget_ok/record_write), persists rate-cap state.
    A poll with zero detected ticks makes the ETag-conditional read call
    only (0 further API writes) — satisfies the acceptance criterion
    "second poll produces zero API writes."
- gates/test_patrol_promote.py: tick detection from body diff,
  promotion idempotence (fingerprint search before create — same tick
  never files twice), rate-cap deferral with "queued: rate cap"
  annotation, marker-based anti-loop (a promoted issue's own marker
  prevents re-promotion), cap accounting surviving a fresh in-process
  state reload (restart simulation), and one end-to-end test: one ticked
  finding on a fixture board -> exactly one promoted-issue body built
  with correct fields -> board line moved -> re-running detect_ticks on
  the now-identical body pair yields zero new ticks.
- docs/issue-1589/reports/implementation.md: phase-2 record.

## Out of scope

- Spawning role sessions or any classification/approval-token flow off
  the promoted issue (explicitly deferred to normal orchestration by the
  issue text).
- Any change to gates/patrol_board.py, gates/patrol_trigger.py,
  gates/patrol_queue.py, or spawn.py — C2 only calls into them.
- Live `gh` network calls in the test suite (subprocess.run to `gh` is
  monkeypatched/stubbed in tests, same pattern as the existing
  gates/test_patrol_board.py suite).
- A CLI wrapper wired into an actual polling cron/loop — `run_patrol_promote`
  is exposed as a single-run function + `python3 gates/patrol_promote.py
  run <root> <role>` entrypoint, matching patrol_board.py's own CLI
  shape; scheduling it is out of scope here (same layering used by
  patrol_board.py itself, which also has no scheduler).

## How you'll know it worked

`python3 -m pytest gates/test_patrol_promote.py -q` passes, including
the end-to-end test described above, and `python3 gates/patrol_promote.py
run <root> <role> --dry-run` runs with zero `gh` subprocess calls.
