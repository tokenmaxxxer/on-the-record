---
status: proposed
files:
  - spawn.py
  - gates/test_clean_reconcile_safety.py
---

## Request

`spawn.py clean` deletes a session's log file even when that session's
ledger outcome is non-landed (e.g. `refused`), destroying the only
durable record of why it refused (observed: session 581a8f7e). Separately,
`spawn.py reconcile --unreported` crashes with `FileNotFoundError` when a
workspace-index entry points at a workspace `clean` already removed —
exactly the state reconcile exists to recover from. Fix both, add a
regression suite.

## Constraints

- Workspace directory deletion in `clean` stays as-is (per the issue) —
  only the session-log deletion behavior changes.
- No new dependency, no schema/CLI-flag change, no new environment
  variable — this is a pure bugfix with no open design surface, so
  scouting was skipped (recorded in `docs/issue-1124/reports/
  implementation/survey.md`).
- `reconcile --unreported` must keep reporting every other entry it can
  reach; a missing workspace must degrade to a skipped note, not abort
  the whole sweep.

## Rationale

Two designs were considered for telling `clean` which logs are safe to
delete:

1. **Consult `runs/ledger.jsonl` by log path** (chosen): `ledger_write`
   already records `{"log": <path>, "outcome": <outcome>}` per session —
   reading it back and keying on the exact sibling path `clean` is about
   to touch needs no new state and no change to any other code path.
2. **Add an explicit "landed" marker file per workspace, written at the
   point a session's PR merges** — rejected: merging happens on GitHub,
   outside any of this repo's session processes, so nothing in this
   codebase currently observes "PR merged" to write such a marker. Adding
   that observation point (e.g. a poll or webhook) is a materially larger
   change than this bugfix's scope, and the issue's acceptance criteria
   are satisfiable from ledger data already being written on every
   `ledger_write()` call.

For `reconcile`, the fix is a plain existence check before the crashing
`subprocess.run(cwd=...)` call — no alternative was weighed because the
issue only asks for a skip-with-note, and Python's own contract (`cwd`
must exist) leaves nothing else to design.

## What will be done

- Add `LANDED_OUTCOMES = {"progressed", "progressed-dirty-tree"}` next to
  `classify()` — the two outcomes where `fail_closed_downgrade` confirms
  a commit reached origin (spawn.py:1726).
- Add `_ledger_log_outcomes()` reading `runs/ledger.jsonl` into
  `{log path: last outcome}`, returning `{}` when the file is absent.
- Extract `clean`'s inline `main()` branch into a standalone
  `roster_clean(wb: Path, issue: int | None) -> int` (same behavior,
  now testable) and change its sibling-file loop: before unlinking a
  sibling that matches a `runs/ledger.jsonl` log path with a non-landed
  outcome, move it to `<work-base>/.archived-logs/` instead of deleting
  it. Siblings with no ledger entry (pre-fix logs, or non-log siblings
  like `.events.jsonl`) keep today's unconditional-delete behavior.
- In `_roster_reconcile_unreported`, check `Path(work).exists()` right
  after reading the entry's `work` path; if missing, print a skip note
  and `continue` instead of calling into `session_end_verdict`/
  `_issue_comments`.
- Add `gates/test_clean_reconcile_safety.py` covering: (a) reconcile over
  an index entry whose workspace is missing completes without raising and
  reports the skip; (b) `clean` over a `refused`-outcome session archives
  the log while still removing the workspace directory; (c) `clean` over
  a `progressed`-outcome session deletes the log as today; (d) empty
  state — no `runs/ledger.jsonl`, empty work dir, empty roster/workspace
  index — both commands no-op cleanly.

## Out of scope

- Any change to what `clean` does with the workspace directory itself.
- Retroactively archiving logs already deleted before this fix.
- Adding a "landed" outcome literal to `classify()` itself, or wiring a
  PR-merge observer — the ledger's existing `progressed`/
  `progressed-dirty-tree` outcomes already answer "did a commit reach
  origin," which is what `clean` needs.
- Any change to `_workspace_index_put`/`WORKSPACE_INDEX` pruning — the
  crashing entry staying in the index after `clean` is what makes
  reconcile's recovery path exist; removing it is a separate design
  question the issue does not raise.

## Accumulation

`_ledger_log_outcomes()` reads the whole `runs/ledger.jsonl` on every
`clean` invocation and holds it as one in-memory dict — that file grows
one line per session forever (it is already read in full nowhere else in
`spawn.py` today, so this is a new O(ledger-size) cost, not a widening of
an existing one). At thousands of sessions this becomes a real per-`clean`
cost; the fix stays correct at that size but not free. If this needs
bounding later (e.g. sessions beyond N days old), that is a follow-up,
not part of this bugfix — flagging it here so a future N-times-more
`ledger.jsonl` growth has a named place to land. `.archived-logs/` is the
other accumulating artifact this proposal introduces: it only grows
(nothing in this change prunes it), by design — pruning what to do with
archived, already-non-landed logs is an operator/retention decision, not
one this bugfix should make unilaterally.

## How you'll know it worked

`python3 gates/test_clean_reconcile_safety.py` passes all cases listed
above (to be executed once phase 2 opens); the fix will also be run
through `python3 -m pytest gates/test_clean_reconcile_safety.py` for the
project's standard test invocation.
