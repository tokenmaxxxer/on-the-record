---
code_under_review:
  - gates/patrol_board.py
  - gates/test_patrol_board.py
type: feature
breaking: false
# canonical: acceptance: python3 -m pytest gates/test_patrol_board.py -q — result: PASS (15 passed)
verdict: pass
loop_state: landed
---

## What was done

canonical: gates/patrol_board.py, as committed on this branch this
session (commit 1875747d).

Built `gates/patrol_board.py`, the C1 patrol-board filer: it maintains
one living GitHub issue per active role, rendered from
`.on-the-record/findings/queue.jsonl` (diff-lane, status=open entries,
issue #1582 schema) into three sections: Pending Approval (checkbox
lines — fingerprint prefix, finding_class, path@last_seen, severity,
excerpt), Approved / In Progress, and the third, most-recent-history
section.
canonical: gates/patrol_board.py (`render_board_body`,
`SECTION_HEADINGS`), read directly this session.

Rendering is pure functions (`select_board_entries`, `render_board_body`,
`parse_board_body`, `dedup_fingerprints`, `diff_board`,
`build_next_body`) over in-memory queue/board-body data; the `gh`-calling
shell (`find_board_issue`, `write_budget_ok`/`record_write`/
`record_drop`, `run_patrol_board`) is a thin imperative layer mirroring
`gates/closure_sweep.py`'s ETag-conditional read pattern
(`_conditional_issue_list`) and reusing `spawn._split_gh_api_i_output`
and `spawn._repo_slug` directly rather than reimplementing them.
canonical: gates/patrol_board.py, read directly this session.

Behavior delivered, matching the issue's acceptance list:
- Edit-in-place, batched to one write (`gh issue create` first run, `gh
  issue edit` thereafter) per `run_patrol_board` call; an unchanged
  rendered body triggers 0 write calls.
- Fingerprint dedup: a fingerprint already on the board is never
  re-added; `dedup_fingerprints` bumps a `(seen Nx)` counter only when
  the fresh render for that fingerprint actually differs from the
  stored line (a genuine re-detection, e.g. `last_seen` moved).
- Absence-close: `diff_board` moves any prior Pending-section line whose
  fingerprint is absent from the current selection into the third
  section and ticks its checkbox.
- ETag conditional reads: `find_board_issue` caches the response ETag
  under `.git/gh-read-cache/patrol-board-<role>.json` (worktree-local,
  uncommitted — same placement family as `spawn._etag_cache_path`); a
  304 response reuses the cached issue and bills 0 API calls.
- Daily write budget with drop-and-record: `write_budget_ok`/
  `record_write` track a per-day JSON counter under
  `.git/patrol-board/write-budget-<date>.json`; a run that would write
  past the cap calls `record_drop` instead, which appends one line to
  a report under docs/issue-1588/reports/ (not present in this
  delivery since the budget was never exceeded against the real queue
  below) and skips the write.
- `--dry-run` renders the body without calling `subprocess` at all.
- NO issue creation for individual findings, NO spawn call, NO
  checkbox-tick interpretation anywhere in this module — deferred to
  #1589 (C2) per the issue body.
canonical: gates/patrol_board.py and gates/test_patrol_board.py, both
read directly this session and exercised by the pytest run cited in
frontmatter above.

## Why

Basis: docs/issue-1588/proposals/2026-08-15-patrol-board-c1.md
(this session's own phase-1 proposal, committed this session as commit
1875747d). Approved via the issue-level comment "APPROVE
issue-1588/implementation" from JiwonJung94, an approvers.md account —
single-account-mode approval per contract v3 s19, present on issue
#1588 before this session opened a PR.
canonical: `gh issue view 1588 --comments` output read this session
(author JiwonJung94, body "APPROVE issue-1588/implementation").

Rationale for the two structural choices (full detail in the
proposal's own Rationale section): reused the `gh` CLI plus `spawn`'s
existing ETag/header-parsing helpers instead of a direct REST client,
to avoid a new HTTP dependency and duplicate logic `closure_sweep.py`/
`spawn.py` already carry working in this repo. Used a JSON state file
for the daily write budget instead of an in-memory counter, because a
patrol run is a fresh process each time and an in-memory counter would
never actually cap anything across runs in the same day.

## Dry-run demonstration against the real queue

Regenerated the real queue via the same command #1582's own measurement
used:

derived: `time python3 gates/patrol_queue.py scan . --lane sweep`
```
{
  "lane": "sweep",
  "scanner": "record_lint",
  "raw_findings": 3022,
  "verified": 2928,
  "verify_dropped": 94,
  "enqueued": 200,
  "budget_truncated_scanners": 1,
  "queue_size": 183
}

real	2m38.134s
user	1m40.574s
sys	1m11.735s
```
canonical: this fenced command output, produced by this session's own
run above.

`queue_size: 183` reproduces the queue size in
docs/issue-1582/reports/implementation/patrol-measurement-2026-08-15.md
Run 1 (`raw_findings` differs by one — 3023 there vs. 3022 here —
consistent with normal record-count drift between the two measurement
dates; both land at queue_size 183).
canonical: docs/issue-1582/reports/implementation/patrol-measurement-2026-08-15.md,
read directly this session, compared against this session's own fenced
output immediately above.

That regenerated queue is `--lane sweep` (the pilot's own scan mode),
but this board module only surfaces `lane == "diff"` entries per the
issue's own acceptance wording ("diff-lane, status=open, validated
entries only"). Running the dry-run against the real sweep-lane queue
as-is renders an empty Pending section, recorded here rather than
substituted with a more favorable result:

derived: `python3 gates/patrol_board.py run . "" --dry-run`
```
{
  "dry_run": true,
  "api_calls": 0,
  "wrote": false
}
## Pending Approval

_none_

## Approved / In Progress

_none_

## Recently Closed

_none_
```
canonical: this fenced command output, produced by this session's own
run above.

To also demonstrate the budget-capped-body rendering path the
acceptance list names ("183 entries -> budget-capped board body"), the
same 183-entry queue was copied to a scratch path outside this
module's write set, with `lane` set to `"diff"` on every entry (no
other field changed), and read via `--queue`:

derived: `python3 gates/patrol_board.py run . "" --dry-run --queue /tmp/diff-lane-queue.jsonl`
```
{
  "dry_run": true,
  "api_calls": 0,
  "wrote": false
}
## Pending Approval

- [ ] `00e53e107f80` record-lint-violation docs/issue-831/reports/architecture.md@scan (unspecified): loop_state: done
... (183 checkbox lines total)

## Approved / In Progress

_none_

## Recently Closed

_none_
```
canonical: this fenced command output, produced by this session's own
run above.

derived: `python3 gates/patrol_board.py run . "" --dry-run --queue /tmp/diff-lane-queue.jsonl | grep -c '\- \[ \]'`
```
183
```
canonical: this fenced command output, produced by this session's own
run above.

`api_calls: 0` in both runs above is the `--dry-run` acceptance item
("0 API calls"); `gates/test_patrol_board.py`'s own
`test_dry_run_makes_zero_subprocess_calls` independently pins this by
making `subprocess.run` raise if invoked during a dry run.
canonical: gates/test_patrol_board.py (`test_dry_run_makes_zero_subprocess_calls`),
read directly this session, part of the pytest run cited in frontmatter
above.

## Test run

canonical: acceptance: `python3 -m pytest gates/test_patrol_board.py -q` — result: PASS
```
...............                                                          [100%]
15 passed in 0.83s
```

Covers: render from fixture queue, edit-in-place idempotence (identical
queue state -> 0 write calls), fingerprint dedup on board (unchanged
entry not re-added/not bumped; genuine re-detection bumps the counter),
absence-close section move, write-budget drop-and-record, ETag handling
(mocked `subprocess.run`, both the 304-reuse and 200-refresh paths),
`--dry-run` making 0 subprocess calls.

## Test-tier directive note

derived: `test -f .on-the-record/test-tiers.json && echo present || echo absent`
```
absent
```
Per the test-tier directive's observe-only posture, this note records
that gap rather than silently absorbing it. The full repo suite was not
run in this session — only the new module's own test file, plus the
pre-existing `gates/patrol_queue.py` CLI invoked live for the dry-run
demonstration above.

## What did not work

Initial `dedup_fingerprints` design bumped a `(seen Nx)` counter on
every call where the fingerprint already existed, regardless of whether
the entry's content had changed. Expected: re-running
`run_patrol_board` twice against an unchanged queue would trigger 0
write calls.
canonical: this session's own local pytest run against the pre-fix
version of gates/patrol_board.py, before the fix described next.
Actual: the second run's rendered body differed from the first (counter
bumped from unset to `(seen 2x)`), so
`test_same_queue_state_produces_identical_body_no_new_writes` (in
gates/test_patrol_board.py) tripped a `gh issue edit` call the test
asserted should never happen. Fixed by comparing the freshly rendered
line (minus the `(seen Nx)` suffix) against the stored line before
bumping — a bump now only fires when the fresh render actually differs
(a genuine re-detection), not on every re-render of unchanged data.

## Open findings

None.

## Rationale for deviations

None — the delivered write set and behavior line up with the approved
proposal's build section.
canonical: docs/issue-1588/proposals/2026-08-15-patrol-board-c1.md
build section, compared this session against gates/patrol_board.py as
committed (commit 1875747d).
The dry-run demonstration needed one adaptation, recorded above: a
`lane: "diff"` copy of the real 183-entry queue at a scratch path,
since the actually-regenerated real queue is sweep-lane — a
demonstration-input choice, not a scope or design deviation from the
proposal.
