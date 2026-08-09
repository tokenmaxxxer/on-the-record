---
status: proposed
files:
  - spawn.py
  - test_spawn.py
  - docs/issue-554/reports/implementation/survey.md
---

## Request

`spawn.py watch` becomes a dead end once an issue has records for two
roles: it exits 1 with a message that lists the ambiguous roles but never
tells the caller `--role` is the fix, and the natural retry
(`watch <role> --issue N`) fails identically because `watch` never reads
the positional role argument `kill` already supports. Fix: (1) auto-select
when exactly one recorded role has a live session, (2) print the exact
runnable command (including `--role`) when still ambiguous, (3) accept
`watch <role> --issue N`.

## Constraints

- Pure bugfix — no new design decision opens (confirmed in the survey:
  scouting skipped, second skip condition).
- Liveness must reuse the existing `_alive()`/roster primitives already
  used for this purpose elsewhere in `spawn.py`, not a new definition.
- The 0-live and 2+-live cases both stay ambiguous — auto-select applies
  only to the exactly-one-live case (issue body, check 1).
- No behavior change when `--role` is already given, or when only one
  role is recorded at all (today's non-ambiguous path).

## Rationale

Two ways to resolve "is a match live" were weighed:

- **Add a `pid`/liveness field into the workspace index entries
  themselves** (written alongside `work`/`log` in
  `_workspace_index_put`). Rejected: liveness is already tracked in a
  separate, purpose-built store (`ROSTER`/`runs/active.json`, keyed by
  `issue-<n>/<role>`, already carrying `pid`) that `_alive()` already
  reads elsewhere in this file. Duplicating that into the workspace index
  would mean keeping two liveness records in sync for no benefit — the
  roster is already authoritative for "is this session live" and the
  workspace-index entry's role suffix is enough to key into it.
- **Cross-reference the existing roster by role suffix, checking
  `_alive()` on each candidate's `pid`** (chosen). No new state, reuses
  the exact liveness primitive (`_alive`, spawn.py:1720) already trusted
  for this question by `roster_watchdog`/`clean`/etc.

## What will be done

- Add `_live_roster_matches(matches, issue)`: given the ambiguous
  workspace-index `(key, entry)` matches, look each one's role suffix up
  in `_roster_load()` under `issue-<issue>/<role>` and keep only entries
  whose `pid` passes `_alive()`.
- Add `_ambiguous_watch_exit(issue, matches, repo)`: builds and raises the
  actionable error — for each candidate role, a directly-pasteable
  `spawn.py watch --issue <n> --role <role>` command (with `-C <repo>`
  appended when repo-scoped), joined with the candidate list.
- In `_lookup_roster_entry`'s two role-less ambiguous branches
  (repo-scoped and unscoped), when there is more than one match: compute
  `_live_roster_matches`; if exactly one, proceed with it silently
  (auto-select); otherwise call `_ambiguous_watch_exit` instead of the
  current bare `sys.exit()`.
- In `main()`'s `watch` dispatch: when `a.watch_role` (`--role`) is not
  given, fall back to the second positional (`a.task`) as the role,
  matching `kill`'s existing `<role> --issue N` grammar.
- Add tests to `test_spawn.py` (extending `WatchRegistrationRace` for the
  `_lookup_roster_entry`-level checks and `WatchFollow` for the
  `main()`/argv-level checks) covering the issue's three acceptance
  checks.

## Out of scope

- `watch --all` (spawn.py `_watch_all`) — unaffected, already
  multiplexes across all live entries with no role argument.
- Changing how liveness itself is defined (`_alive`'s bare
  `os.kill(pid, 0)` probe, or the fuller `_watcher_looks_real` check used
  for watcher-specific staleness) — out of scope, reused as-is.
- The `kill` subcommand's own positional grammar — already correct,
  referenced only as the pattern to match.

## How you'll know it worked

- The new/extended tests in `test_spawn.py` fail against current `main`
  (reproducing the issue: no auto-select, message lacks `--role`,
  positional role rejected for `watch`) and pass on this branch.
- Existing `WatchRegistrationRace`/`WatchFollow`/`WatchAll` tests keep
  passing unchanged — the single-match and `--role`-given paths are
  untouched.

## Accumulation

`_ambiguous_watch_exit` and `_live_roster_matches` are each a single
shared helper called from both of `_lookup_roster_entry`'s ambiguous
branches (repo-scoped and unscoped) instead of inlining the message
construction and roster-scan twice — so this change *reduces* the
duplicate-branch count already present in `_lookup_roster_entry`, rather
than adding to it. No inline `subprocess`/`gh` call sites are added (this
touches only in-process index/roster dict lookups), and no `roles/*.json`
-style repeated-file pattern is touched. If this ambiguous-lookup shape
needs to recur (e.g. a future `kill --role`-less ambiguity), the same two
helpers are reusable as-is rather than needing a third inline copy.
