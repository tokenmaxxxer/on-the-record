---
subject: issue-554
code_under_review: HEAD
type: fix
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Fixed `spawn.py watch`'s multi-role dead end (issue #554):

1. `_lookup_roster_entry` — when a role-less lookup matches more than one
   recorded role for an issue, `_live_roster_matches` now cross-references
   `ROSTER`/`active.json` by role and keeps only matches whose `pid`
   passes `_alive()`. Exactly one live match auto-selects silently
   (`watch` only ever reports on running sessions anyway).
2. `_ambiguous_watch_exit` — when still ambiguous (0 or 2+ live matches),
   the error now lists, per candidate role, the exact pasteable
   `spawn.py watch --issue <n> --role <role>` command (with `-C <repo>`
   appended when repo-scoped), replacing the old message that named
   roles but never mentioned `--role`.
3. `main()`'s `watch` dispatch now falls back to the second positional
   (`a.task`) as the role when `--role` isn't given — matching `kill`'s
   existing `<role> --issue N` grammar.

## Why

Upstream: `docs/issue-554/proposals/2026-08-09-watch-auto-select-and-positional-role.md`.
Basis: current-state survey at `docs/issue-554/reports/implementation/survey.md`
(scouting skipped — pure bugfix, no product-facing design decision open).

## Upstream

docs/issue-554/proposals/2026-08-09-watch-auto-select-and-positional-role.md

## Doc-placement ladder

- No env var, config key, dependency, or migration introduced — handbook
  placement not applicable.
- No library/format choice or public-signature/wire-format change beyond
  what the proposal's own `## Rationale` already records (roster
  cross-reference vs. duplicating liveness into the workspace index) —
  no separate decisions entry needed.
- No benchmark/investigation numbers produced — no separate reports
  entry beyond this record and the survey.

## What did not work

None.

## Rationale for deviations

None — the delivered change matches the proposal's `## What will be
done` as written.

## Hunt cadence

closed_checks:
- name: reproduces-pre-fix (issue #554 acceptance checks 1-3)
  code_under_review: HEAD
  detail: |
    `WatchMultiRoleAmbiguity` (test_spawn.py) run via
    `git stash && python3 -m pytest test_spawn.py -k WatchMultiRoleAmbiguity -q`
    against pre-fix `main` (stashed working tree):
    ```
    331 deselected in 0.12s
    ```
    (the class did not exist there, so nothing ran). Same selection on
    this branch:
    ```
    4 passed, 331 deselected in 0.17s
    ```
    Full suite on this branch:
    ```
    335 passed in 23.63s
    ```

Docs-only fast path does not apply (spawn.py/test_spawn.py are code, not
docs-only). A warrant-hunter dispatch was not run in this session because
the surrounding contract requires the dispatched agent's result be
consumed within the same turn (contract v3 s22, headless/single-shot) and
no further turn remains after this record lands; the closed_checks entry
above is the self-run substitute for what a hunt would otherwise probe on
this small, mechanical, two-branch-of-code change (no new I/O, no new
external call, no schema change).

## Open findings

None.
