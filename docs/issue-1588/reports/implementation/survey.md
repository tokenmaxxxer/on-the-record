# issue-1588 survey: patrol board C1

## Write set surveyed

- gates/patrol_board.py (new) — the filer module.
- gates/test_patrol_board.py (new) — tests.

## Inputs already landed, reused as-is

- `gates/patrol_queue.py` (issue #1582, landed): `QUEUE_REL_PATH =
  ".on-the-record/findings/queue.jsonl"`, `load_queue()`, entry schema
  — `fingerprint, scanner_id, path, finding_class, excerpt, first_seen,
  last_seen, lane, promotable, status`.
  canonical: gates/patrol_queue.py read directly this session.
  Board reads queue entries with `lane == "diff"` and `status ==
  "open"` per the issue body ("diff-lane, status=open, validated
  entries only"); `verify()` in patrol_queue already dropped
  unverifiable entries before they reach the queue, so the board does
  no re-verification of its own.
- `docs/specs/patrol-channel-contract.md` (issue #1586, landed via PR
  #1591): PCC-1 permits autonomous create+edit-in-place of exactly one
  board issue per role; PCC-2/PCC-3 push checkbox-tick interpretation to
  a later layer (C2, out of scope here — this module never reads back
  which boxes are ticked); PCC-5 caps: max 2 tick-promoted issues/hour
  (C2), max 10 open patrol issues/role (C2), board edits batched to one
  edit per role per patrol run (this module's requirement).
  canonical: docs/specs/patrol-channel-contract.md read directly this
  session.
- `on-the-record/hooks/gh-write-allow-gate.sh`: `VERB_SHAPES` contains
  `("gh", "issue", "create")` and `("gh", "issue", "edit")` —
  shape-only allow, content unchecked.
  canonical: on-the-record/hooks/gh-write-allow-gate.sh read directly
  this session (VERB_SHAPES tuple and `_match_shape`, which matches on
  leading tokens only, so a `--body "..."` tail after the verb shape
  does not change the match).

## Prior-art pattern in this repo: ETag conditional read

`gates/closure_sweep.py` already implements the read shape this issue
asks for: helpers `_board_list_etag_cache_path` and
`_conditional_issue_list` call `gh api repos/{slug}/issues -f
state=all -f per_page=100 -i`, cache the response ETag under
`.git/gh-read-cache/board-list-{name}.json` (worktree-local, never
committed — same location family as `spawn._etag_cache_path`), send
`If-None-Match` on the next call, and treat a 304 response as 0 billed
API calls by returning the cached body instead.
canonical: gates/closure_sweep.py read directly this session
(`_board_list_etag_cache_path`, `_conditional_issue_list`,
`_issue_view`).
`spawn._split_gh_api_i_output` parses the `-i` combined header+body
output and is reused directly rather than reimplemented.
canonical: spawn.py read directly this session (`_split_gh_api_i_output`).
This module's read path mirrors that pattern, scoped to
`repos/{slug}/issues?labels=patrol-board,role:<x>` (narrower than
closure_sweep's whole-issue-list scan) so a single `gh api` call is
enough to locate the one board issue for a role, present or absent.

## No existing precedent for: daily write budget, edit-in-place batching

derived: `grep -rln "daily budget\|write_budget\|drop_and_record" gates/ on-the-record/`
```
gates/patrol_queue.py
on-the-record/hooks/test_patrol_queue_hook.py
```
The only hits are patrol_queue's own per-scanner enqueue cap
(`apply_budget`), which drops overflow *findings* at scan time, not
board *writes*. There is no existing global daily-write-budget
mechanism to reuse; this module introduces one, scoped to itself (board
issue create/edit calls only), state file under
`.git/patrol-board/write-budget-<date>.json` (worktree-local, same
non-committed placement family as the ETag cache).

## No existing precedent for: mocked gh calls in tests

derived: `find . -iname 'test_closure_sweep*'`
```
(no output)
```
No `test_closure_sweep.py` exists in this tree, so there is no in-repo
test-mocking convention for `gh api`/`gh issue create`/`gh issue edit`
calls to copy verbatim. This module's tests instead monkeypatch
`subprocess.run` directly (stdlib, no new dependency); the
board-rendering logic is kept as pure functions over in-memory queue
data, with the `gh`-calling shell reduced to a thin imperative layer
that is what gets monkeypatched.

## Alternative considered and rejected

Considered checking the rendered board body's checkbox state on every
run (to detect ticks) as a natural place to also implement C2's
promotion trigger. Rejected: the issue body is explicit that checkbox
interpretation is C2, not C1, and PCC-2/PCC-3 make tick-driven creation
a separate, later-gated capability (rate caps, spawn wiring) that this
module's write set does not include. Building it here would also
entangle rendering-correctness tests with promotion-trigger-correctness
tests, when the issue asks for them as independently gated
capabilities.
