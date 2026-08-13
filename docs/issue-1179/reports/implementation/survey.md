---
name: survey
description: issue-1179 current-state survey — spawn.py workspace lifecycle, clean/reconcile safety, spawn-time entry point
---

# Current-state survey — issue-1179

## Existing safe-delete logic (reused, not rebuilt)

canonical: spawn.py:4894-4979 (`roster_clean()`)
`spawn.py clean [--issue N]` is manual-only. Per candidate workspace directory (`<work_base>/*` with a
`.git`) it: skips live sessions (roster PID alive, spawn.py:4930-4936), skips dirty/unpushed trees
(`git status --porcelain` or `git log --branches --not --remotes`, spawn.py:4937-4947), then
`shutil.rmtree` with a chmod-retry `onexc` (spawn.py:4911-4921, issue #229) and archives sibling logs
whose ledger outcome is outside `LANDED_OUTCOMES` to `<work_base>/.archived-logs/` instead of deleting
them (spawn.py:4956-4968, issue #1124). This is exactly the "safe" half of the issue's requirement 1 —
it already implements "uncommitted/unpushed work never deleted" and "non-landed logs archived".

canonical: spawn.py:1682 (`LANDED_OUTCOMES`), spawn.py:1685-1706 (`_ledger_log_outcomes()`)
`LANDED_OUTCOMES = {"progressed", "progressed-dirty-tree"}`. `_ledger_log_outcomes()` reads
`runs/ledger.jsonl` and returns an empty dict if the file is missing — clean already tolerates a
ledger-less state.

## What "terminal-outcome" means for an entry today

canonical: spawn.py:1640-1677 (`classify()`), spawn.py:1707-1754 (`session_end_verdict()`)
The roster (`ROOT/runs/active.json` via `_roster_load`/`_roster_save`, spawn.py:1937-1948) tracks live
role sessions keyed by pid. An entry stops being live when its pid dies; `roster_clean()` does not
consult roster "outcome" fields at all — it re-derives safety purely from git state (dirty/unpushed) at
sweep time, plus the separate `roster_watchdog()`/reconcile machinery that updates ledger/roster
entries as sessions finish. There is no separate "terminal" flag `roster_clean()` needs beyond
"not live + git-clean" — that already implies the session's fate is settled one way or another (either
its work landed and got pushed, in which case history lives on origin and the local clone is
disposable, or it never had anything worth keeping).

## Where cleanup is invoked today (manual only — the gap)

canonical: spawn.py:5165-5168 (CLI dispatch, `a.role == "clean"`)
`clean` is a top-level CLI verb (`spawn.py clean`), only reachable if a human or orchestrator runs it.
Nothing calls `roster_clean()` automatically. This is the entire gap requirement 1 closes.

canonical: spawn.py:5765-5811 (`_spawn_one()`), spawn.py:5332-5342 (`issue_workspace()`)
`_spawn_one()` is the single spawn-time chokepoint both `main()` and `drive()` funnel through
(docstring at spawn.py:5771-5772 states this explicitly: "드라이버가 따로 스폰 경로를 들고 있으면 둘이
갈라진다"). When `issue is not None` it calls `issue_workspace(cwd, issue, role)`
(spawn.py:5803-5804) before creating the new workspace clone — this is the natural
"session-start"/spawn-time point to run an automatic sweep before adding one more workspace to the
pile, matching the issue's suggested trigger ("spawn-time/session-start sweep").

canonical: spawn.py:5364-5366 (workspace base resolution inside `issue_workspace()`), spawn.py:5166-5167
(same resolution repeated inside the `clean` CLI branch)
Workspace base directory resolution (`MUSTER_WORK_DIR` env override, default
`~/.tokenmaxxxer/work`) is duplicated verbatim in two places already; a third call site (the new
auto-sweep) should reuse one shared helper rather than triplicate the same four lines again.

## Regression coverage already in place

canonical: gates/test_clean_reconcile_safety.py:1-60
`gates/test_clean_reconcile_safety.py` hermetically overrides `spawn.ROOT`/`spawn.ROSTER`/
`spawn.WORKSPACE_INDEX` to a tmpdir. It builds bare git workspaces via `_bare_workspace()` and asserts
reconcile/clean safety invariants. New automatic-sweep tests belong in this same file, reusing
`_bare_workspace()` and the same override pattern, so #1124's existing assertions and the new ones run
under one hermetic harness.

## Env var documentation home

canonical: docs/handbooks/setup.md:75-148
`MUSTER_STATE_ROOT` (and, by the same pattern though not itself defined there, `MUSTER_WORK_DIR`) are
the existing precedent for where spawn.py env vars get written up — bilingual (Korean then English)
sections in `docs/handbooks/setup.md`. New env vars for the auto-sweep bound policy belong there.

## Write set (frozen for this proposal)

- `spawn.py` — extract a shared "safe to delete" check + deletion routine out of `roster_clean()`, add
  a bound-based `auto_sweep()` that reuses it, wire one call into `_spawn_one()`'s `issue is not None`
  branch, add a shared `_workspace_base()` helper to stop the third duplication.
- `gates/test_clean_reconcile_safety.py` — new tests for auto-sweep (age bound, size bound, live/dirty
  exemption, #1124 regressions still green).
- `docs/handbooks/setup.md` — document the new env vars (default-on flag, age/size bounds).
- docs/issue-1179/decisions/shared-checkout-dedup.md (to be written) — requirement 4's accept/reject record.
- docs/issue-1179/proposals/*.md — this proposal.
- docs/issue-1179/reports/implementation.md (to be written) — phase-2 record.
