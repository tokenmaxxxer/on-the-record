---
status: proposed
files:
  - gates/patrol_board.py
  - gates/test_patrol_board.py
---

## Request

Build the C1 patrol-board filer: maintain one living GitHub issue per
active role, rendered from `.on-the-record/findings/queue.jsonl`
(diff-lane, status=open, validated entries), edited in place and
batched to one `gh issue edit` per role per run. Checkbox interpretation
and per-finding issue spawn are explicitly out of scope (C2, issue
#1589).

## Constraints

- Depends on #1586 (contract amendment, landed) for the
  edit-in-place/create permission, and #1582 (queue schema, landed).
- No checkbox interpretation, no per-finding issue creation, no spawn
  call anywhere in this module.
- Write shapes limited to exactly `gh issue create` and `gh issue edit`
  (the two shapes `gh-write-allow-gate.sh` already permits).
- Reads must be ETag-conditional; 304 counts as 0 API calls.
- Writes serialized, one edit per role per run, bounded by a daily
  write budget with drop-and-record on cap.
- `--dry-run` must make 0 API calls.

## Rationale

Two options for the read/write layer: (a) call the `gh` CLI via
`subprocess`, mirroring `gates/closure_sweep.py`'s existing
`_conditional_issue_list`/ETag-cache pattern; (b) call the GitHub REST
API directly over `requests`/`urllib`, using a token from the
environment. Rejected (b): it needs a new HTTP dependency (or hand-rolled
auth-header/urllib boilerplate) this repo does not already carry for
this purpose, and it duplicates ETag-cache and header-parsing logic
`closure_sweep.py`/`spawn.py` already have working and tested in this
repo. Chose (a): reuse `_split_gh_api_i_output`-shaped parsing and the
`.git/gh-read-cache/` cache-file convention, keeping this module
dependency-free and consistent with the only existing gh-calling code
in this repo's gates/ tree.

For the daily write budget, considered tracking it as an in-memory
counter reset per process invocation (simplest). Rejected: a patrol run
is a fresh process each time (per the trigger-guard pattern in
`gates/patrol_trigger.py`), so an in-memory counter would never
actually cap anything across runs in the same day — it would look
implemented but be a no-op. Chose a small JSON state file under
`.git/patrol-board/write-budget-<date>.json` (worktree-local, same
non-committed placement family as the ETag cache), incremented on every
committed write and checked before each write attempt.

## What will be done

- `gates/patrol_board.py`:
  - Pure rendering functions over an in-memory queue-entry list and a
    prior board state (parsed sections): `select_board_entries(queue,
    role)` (diff-lane + status=open filter, scoped to a role via the
    entry's `path` prefix — same role-scoping convention as
    `docs/issue-1582/proposals/2026-08-15-tier1-role-patrol-pilot.md`
    subject-path scoping), `render_board_body(pending, approved,
    recently_closed)` (three markdown sections: `## Pending Approval`
    checkbox list — fingerprint prefix, rule/finding_class, `path` with
    a synthetic line marker, severity placeholder, excerpt; `##
    Approved / In Progress`; `## Recently Closed`), `diff_board(old_body,
    new_pending_fingerprints)` (absence-close: any fingerprint present
    in the old Pending section but absent from the new pending set moves
    to Recently Closed), `dedup_fingerprints(existing_fps,
    new_entries)` (a fingerprint already anywhere on the board is never
    re-added — counter bump only, tracked via a `(seen N times)` suffix
    on the existing line).
  - Imperative shell: `find_board_issue(root, slug, role)` (ETag
    conditional `gh api repos/{slug}/issues -f labels=patrol-board,role:{role}
    -f state=all -i`, cache under `.git/gh-read-cache/patrol-board-{role}.json`,
    mirrors `closure_sweep._conditional_issue_list`), `write_budget_ok(root,
    date)` / `record_write(root, date)` (JSON counter file, default cap
    configurable, drop-and-record appends a line to
    `docs/issue-1588/reports/write-budget-drops.md` when a run is
    skipped for budget), `run_patrol_board(root, role, queue_path,
    dry_run)` (orchestrates: load queue -> select entries -> find/read
    existing board issue (ETag) -> render new body -> if unchanged, 0
    writes; if changed and dry_run, print body and return with 0 API
    calls; if changed and not dry_run, check budget, then either `gh
    issue create` (first run for this role) or one `gh issue edit`
    (subsequent runs) -> record_write).
  - CLI: `python3 gates/patrol_board.py run <repo-root> <role>
    [--dry-run] [--queue PATH]`.
- `gates/test_patrol_board.py`: fixture-queue rendering, edit-in-place
  idempotence (identical queue state twice -> second run makes 0 `gh`
  calls beyond the read), fingerprint dedup on board, absence-close
  section move, write-budget drop-and-record, ETag 304 handling (mocked
  `subprocess.run`), `--dry-run` making 0 subprocess calls that are
  writes.
- Record: `docs/issue-1588/reports/implementation.md`, including a
  dry-run demonstration against the real queue regenerated by running
  `python3 gates/patrol_queue.py scan . --lane sweep` (reproducing
  #1582's 183-entry measurement) followed by `python3
  gates/patrol_board.py run . <role> --dry-run`.

## Out of scope

- Checkbox-tick detection/interpretation and any resulting per-finding
  issue creation or spawn call (issue #1589 / C2).
- The two rate caps that depend on tick-driven promotion (max
  2 tick-promoted issues/hour, max 10 open patrol issues/role) — PCC-5
  items 1 and 2, deferred to C2 since they gate promotion, not board
  rendering. This module implements PCC-5 item 3 (one board edit per
  role per run) only, which is the cap this module's own writes are
  subject to.
- Any change to `gates/patrol_queue.py`, `gates/patrol_trigger.py`, or
  `on-the-record/hooks/gh-write-allow-gate.sh` (all already landed and
  sufficient for this module's needs).

## How you'll know it worked

- `python3 -m pytest gates/test_patrol_board.py -q` passes, covering
  every item in the issue's acceptance list.
- `python3 gates/patrol_queue.py scan . --lane sweep` regenerates a
  queue, then `python3 gates/patrol_board.py run . <role> --dry-run`
  prints a rendered body and makes 0 API calls, demonstrated in the
  phase-2 record with pasted command output.
