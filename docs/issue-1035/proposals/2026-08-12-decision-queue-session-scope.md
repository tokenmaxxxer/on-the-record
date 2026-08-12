---
status: proposed
files:
  - gates/flows.py
  - spawn.py
  - tests/test_flows.py
  - docs/specs/flows-schema.md
---

## Request
`gates/flows.py`'s `decision_queue` is built from every open PR
repo-wide, with no session-ownership filter. On one machine running
several `on-the-record` sessions against the same repo, a foreign
session's aged decision-queue item repeatedly trips this session's
`decision-queue-stopgate.sh` Stop hook — items this session does not
own and must not act on. #1013 scoped roster/watchdog/PR-gate/
auto-respawn to a session's own items via `_roster_own`; `flows.py`'s
`decision_queue` was left out of that scoping.

## Constraints
- Reuse #1013's ownership convention (`spawn._roster_own`'s predicate:
  roster entry `session_id` == own session, or either side `None`)
  rather than inventing a second one.
- Keep a global (`--all`) escape — the existing shared `--all` CLI flag,
  already used by `watch`/`watchdog`.
- A session with no owned aged items must get no block and no advisory
  from foreign items — i.e. the *filtering* happens before
  `decision_queue` is returned, not downstream in the stopgate hook.
- Acceptance cases live in `tests/test_flows.py` (per the issue body):
  foreign-session aged item excluded by default; own aged item still
  included; `--all` lists both.

## Rationale
Chosen approach: join each `decision_queue` item to a roster entry by
the shared `issue-<n>/<role>` key (identical shape to
`spawn.py`'s `roster_key = f"issue-{issue}/{role}"`), and apply
`_roster_own`'s exact ownership predicate per item, filtering
`decision_queue` (not `flows[]` or `sessions[]`) inside
`flows_payload()`.

Alternative considered and rejected: filtering downstream in
`decision-queue-stopgate.sh` (the hook that reads `flows --json` and
raises the block) instead of upstream in `flows_payload()`. Rejected
because `decision_queue` is a shared read-only data contract consumed
by more than one caller (the stopgate hook today, potentially the
status board or other consumers later per `flows.py`'s own docstring
"read-only ... matches `status()`'s own invariant"); scoping only one
consumer would leave every other reader of `flows --json` still seeing
foreign items as if owned, reproducing the same confusion issue #1013
fixed for the roster paths by scoping the shared data source itself,
not each caller individually.

A second alternative considered — attributing ownership by branch name
alone (session-less, e.g. matching the current session's own
`issue-<n>/<role>` branch) — was rejected because it cannot distinguish
two *different* sessions both working the *same* issue/role (unlikely
but not excluded by anything in this codebase), and it discards the
`session_id` attribution `_roster_own` already established and that
#1013 chose deliberately; reusing the existing predicate keeps one
ownership convention across the whole codebase instead of two
similar-but-different ones.

## Accumulation
This change adds one ownership check inside `flows_payload()`'s
existing single `decision_queue` build loop — it does not add a new
per-item `gh`/subprocess call (the roster lookup is an in-memory dict
read from the already-loaded `_roster_load()` result) and does not
touch any repeated per-role file (`roles/*.json`). If more scoped
fields are added to `flows --json` later (e.g. `flows[]`,
`unapproved_open_prs`, explicitly out of scope here), each would reuse
this same in-memory `_roster_own`-style predicate rather than adding
another `gh` call per field — N more fields stays O(1) additional
subprocess calls, not O(N).

## What will be done
- `gates/flows.py`: in `flows_payload()`, add an `all_scope: bool =
  False` parameter. Before appending an item to `decision_queue`, look
  up the roster entry for that item's `f"issue-{issue_n}/{role}"` key
  and apply the same predicate as `_roster_own` (own session_id, or
  either side `None`) unless `all_scope`. `flows()` (the CLI wrapper)
  gains a matching `all_scope: bool = False` parameter and threads it
  through.
- `spawn.py`: the `flows` role's CLI dispatch passes the existing
  `--all` flag's parsed value (`a.all`) into `flows.flows(...)` as
  `all_scope`. No new `argparse` flag — `--all` is already registered
  on the shared top-level parser.
- `tests/test_flows.py`: three cases against `flows_payload()` —
  foreign-session aged item excluded by default; own-session aged item
  still included by default; both listed under `all_scope=True`.
- `docs/specs/flows-schema.md`: after-proposal hunt finding — this is
  `decision_queue`'s versioned contract doc (§2.1 documents its default
  contents; the doc notes it is mirrored by the external
  `repo-status-board` consumer and needs sync on change). Update §2.1
  and any surrounding prose to state the default session-ownership
  scoping and the `--all` escape.

## Out of scope
- Changing `decision-queue-stopgate.sh` itself (it already reads
  whatever `flows --json` returns — no hook-side change needed once the
  payload is scoped).
- Scoping `flows[]`, `sessions[]`, `unapproved_open_prs`, or any other
  `flows --json` field — the issue and acceptance cases name
  `decision_queue` only.
- Any change to `_roster_own` itself or to roster/watchdog/PR-gate/
  auto-respawn paths (#1013's own scope, already landed).

## How you'll know it worked
`python3 -m pytest tests/test_flows.py -k decision` — three new cases
green — and a manual `spawn.py flows --json` run inside a repo with
roster entries for two different `session_id`s shows only the caller's
own aged items in `decision_queue` by default, both under `--all`.
