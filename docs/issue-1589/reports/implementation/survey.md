# issue-1589 (C2 promotion) — current-state survey

## Write set (projected)

- gates/patrol_promote.py (new file, not yet created) — tick detection,
  promotion (fingerprint search before create), board line move, rate
  caps, marker anti-loop integration.
- gates/test_patrol_promote.py (new file, not yet created).
- docs/issue-1589/proposals/2026-08-15-patrol-board-c2-promotion.md (new).
- docs/issue-1589/reports/implementation.md (new, this session's record).

No dependency-manifest, env var, or migration touch. No .env.example
change.

## Integration surface (read directly, not from memory)

### gates/patrol_board.py (#1592, landed)
- PENDING_HEADING/APPROVED_HEADING/CLOSED_HEADING, SECTION_HEADINGS.
- canonical: gates/patrol_board.py:38 — `_CHECKBOX_LINE = re.compile(r"^- \[( |x)\] \`([0-9a-f]+)\` (.*)$")`.
  Checkbox line shape: "- [ ] `<fp12>` <rest>". Fingerprint on the line
  is a 12-char prefix (entry["fingerprint"][:12]), not the full
  fingerprint.
- parse_board_body(body) -> {heading: [lines]} — reusable for reading
  both the prior-poll body and the freshly-fetched body to diff.
- canonical: gates/patrol_board.py:47-64 — select_board_entries(queue, role):
  role scoping is `scanner_id == "judge:<role>"` first, path prefix
  (roles/<role>/ or <role>/) second. C2 must call this function, not
  re-derive the scoping rule (binding integration note, PR #1592 review).
- find_board_issue(root, role) — ETag-conditional read, returns
  (issue_dict_or_None, ok, billed_calls). C2's poll step reuses this for
  304-free reads.
- _etag_cache_path, _budget_path, record_write, write_budget_ok —
  board-edit write budget is per-role-per-day; C2's board-line-move edit
  shares this same budget accounting (same board issue, same run).
- Board body's "## Approved / In Progress" section is opaque free-text
  lines (sections[APPROVED_HEADING]) carried over verbatim by
  build_next_body — C2 owns writing real content into that section for
  the first time (promoted-issue links); C1 only copy-through it.

### gates/patrol_trigger.py (#1584, landed)
- canonical: gates/patrol_trigger.py:33-45 — should_fire(event) /
  _is_patrol_artifact(path): path-set-based anti-loop keyed off
  _PATROL_ARTIFACT_PATHS / _PATROL_ARTIFACT_PREFIXES. This only guards
  file-path commits (queue file, measurement reports); it has no notion
  of a GitHub issue marker. C2 does not duplicate this logic — C2's own
  anti-loop concern (never re-promote the same tick, never treat a
  promoted issue's own activity as a fresh patrol source) is a different
  axis, handled inside patrol_promote.py via a body marker + label.

### spawn.py judge_cmd (#1587/#1593, landed)
- canonical: spawn.py:5741-5744 — enqueues findings with
  scanner_id = f"judge:{role}", lane="diff", fingerprint via
  patrol_queue.fingerprint(f"judge:{role}", vf["path"],
  [vf.get("excerpt", "")]). This is exactly what select_board_entries
  matches via by_scanner. No direct call from C2 into judge_cmd is
  needed — C2 only reads the board/queue that C1 + judge already
  populate.

### gates/patrol_queue.py
- load_queue/save_queue, fingerprint(). Queue entries carry the full
  fingerprint; board lines carry only the 12-char prefix. C2's
  promotion must resolve a ticked 12-char prefix back to its full queue
  entry (prefix match over queue, unique in practice since
  _finding_line always derives the same 12-char prefix from the same
  entry).

### Rate caps (contract PCC-5)
- canonical: docs/specs/patrol-channel-contract.md PCC-5 — max 2
  tick-promoted issues/hour/role; max 10 open patrol issues/role; board
  edits batched to one edit/role/run — already enforced by
  patrol_board.run_patrol_board's single edit-or-create call; C2's
  board-line-move reuses the same one-shot body write, not a second call.

### gh-write-allow-gate (#1591, landed)
- canonical: on-the-record/hooks/gh-write-allow-gate.sh:10-11,148-149 —
  already allows `gh issue create`, `gh issue edit`, `gh issue comment`
  shape-only for orchestrator-session callers. No gate change needed —
  C2 issues its create/edit calls the same way patrol_board.py does
  (subprocess, cwd=root), inheriting the existing allow shape.

## Design decision needed (why this proposal exists)

Two candidate designs for tick detection:

1. ETag-diff against the last-known board body C2 itself last processed
   (separate small state file), diff old vs new via parse_board_body +
   line-level checkbox compare.
2. Re-derive "ticked" from GitHub's live body only, no stored prior
   state: treat every "- [x]" line with no matching promoted-issue
   marker as a fresh tick.

Design 1 is chosen (see proposal Rationale) — it directly detects a
transition (was unchecked, now checked), which is what the issue's
"tick — and only a tick" (PCC-2) requires; design 2 can't distinguish
"still ticked from three runs ago, already promoted" from "newly ticked
this run" without still needing a promoted-fingerprint index, so it
collapses to design 1 plus a needless second data source.

## Marker / anti-loop mechanism

- canonical: grep -rn "patrol-promoted" gates/ on-the-record/ docs/specs/
  (run during this survey) — no existing hit, confirming no prior
  "patrol-promoted"-shaped label/marker convention exists in this repo.
  C2 introduces label patrol-promoted + a body marker line
  (`<!-- patrol:promoted fp=<fingerprint> -->`) on every issue it
  creates. Idempotence search (fingerprint search before create) lists
  issues with that label and greps the marker for the full fingerprint
  (full fingerprint, not the 12-char board prefix, to avoid prefix
  collisions).

## Rate-cap state storage

Following patrol_board.py's own precedent (_budget_path under
.git/patrol-board/), C2 stores its per-role hourly/open-count state
under .git/patrol-promote/<role>.json — local, restart-durable via the
working copy's .git dir, mirroring the existing write-budget file shape
({"count": N}) extended to {"promotions": [...timestamps]}.
