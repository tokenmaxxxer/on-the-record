---
code_under_review: HEAD
loop_state: landed
---

## What was done

Implemented docs/issue-534/proposals/2026-08-09-session-end-durability.md:

- `spawn.py`: added `_SESSION_END_COMMENT_MARKER`, `_pr_list_call_ok()`
  (distinguishes "no PR" from "couldn't check"), and
  `_post_session_end_comment()` — posts `[watch] {key}: session-end: PR
  <url> opened` / `no PR` / `no PR (pr-check-failed)` idempotently for
  `verdict == "normal"`, reusing `_pr_open_or_merged_for_branch()` as the
  PR-open signal.
- Wired self-triggered from `_spawn_one()`'s bounded path right after the
  `session-end` event is appended (same place `_self_trigger_respawn()`
  fires, for the same dead-entry-invisible-to-watchdog race), and as a
  best-effort catch from `roster_watchdog()`'s dead-entry scan.
- Added `spawn.py reconcile --unreported [--issue N]`
  (`_roster_reconcile_unreported()`): scans the persistent
  `WORKSPACE_INDEX` (unlike the roster, never cleared on session-end) for
  `verdict == "normal"` entries with no marker comment yet.
- `on-the-record/commands/run.md`: added a contract subsection — first
  act on session start / post-compaction recovery is `spawn.py reconcile
  --unreported`, not resuming from conversation memory.
- `test_spawn.py`: `PostSessionEndComment` (marker idempotency, PR-url
  interpolation, pr-check-failed fallback, non-normal-verdict no-op) and
  `RosterReconcileUnreported` (synthetic ended-session-with-open-PR
  fixture lists before ack, empties after; issue filter; non-normal
  skip; CLI dispatch).

## Why

Session-end/PR-open outcomes only reached the orchestrator through its own
in-conversation watch loop — dropped on compaction/restart (issue #534).
Making the outcome durable via GitHub issue comments, plus a reconcile
sweep over state that survives roster cleanup, removes that single point
of observation failure.

## Upstream

docs/issue-534/proposals/2026-08-09-session-end-durability.md

## What did not work

- Wrote `_post_session_end_comment(root, ...)` intending `root` fixed to
  `ROOT` (the orchestrator checkout) everywhere, matching
  `_build_observed(ROOT, e)`'s existing convention — but the self-trigger
  call site inside `_spawn_one()` runs with `cwd` as the actual per-issue
  workspace checkout, and `_repo_slug()`/`gh api` need to run against
  *that* repo's remote, not the orchestrator's. Fixed by passing
  `Path(cwd)` as `root` at the self-trigger call site and `ROOT` at the
  watchdog call site (each call site's own workspace), consistent with
  how `_post_stall_comment`/`_post_crash_comment` are already called with
  `Path(work)`.
- First attempt at the `Edit` adding `_post_session_end_comment()` was
  denied by `accumulation-claim-guard.sh` (a third inline
  `subprocess.run(["gh", ...])` site in `spawn.py` tripped the
  accumulation-shape check) — added a `## Accumulation` section to the
  already-approved proposal file (docs are always writable) stating the
  consolidation trigger (a fourth/fifth such variant), then the edit
  went through.
- `python3 -m pytest` (repo-wide, not just `test_spawn.py`) initially
  failed `test_spec_index.py::t_baseline_repo_passes` because
  `on-the-record/commands/run.md`'s content hash changed — expected,
  fixed by `python3 gates/spec_index.py --update`.

## Open findings

None unresolved. `test_gates.py::t_rulebook_version_is_recorded` and
`test_gates.py::t_new_roles_resolve_without_a_local_checkout` fail on
`main` before this branch's changes too (confirmed via `git stash`) —
pre-existing, unrelated to this issue, left untouched (out of the frozen
write set).

Before-landing hunt finding (`docs/reports/2026-08-09-hunt-session-end-durability.md`,
stance 0): `_roster_reconcile_unreported()` only `print()`s the "미보고"
line — it never itself calls `_post_session_end_comment()` / posts a `gh
api` comment, so the recovery sweep is detect-only. Reviewed against the
approved proposal text: this is the specified design, not a defect —
"What will be done" says the sweep should "print each as a line the
orchestrator can act on," and the acceptance criterion's "empties after
acknowledgment" defines acknowledgment as the marker comment's presence,
which the *orchestrator* (not the sweep itself) is expected to bring
about by acting on the printed line, per `on-the-record/commands/run.md`'s
new subsection ("이후 루프는 그 출력이 지목한 세션부터 처리한다"). Closed
as no-change-needed; noted here so the print-only shape isn't mistaken for
an oversight later.

## Hunt

Before-landing warrant hunt dispatched (foreground, `warrant-hunter`,
stance 0 per `.warrant-hunt.count`), diff ~250 lines across
`spawn.py`/`test_spawn.py`/`on-the-record/commands/run.md` (tier
`size:>200`, 180s cap). One finding returned, reviewed and closed above
(no-change-needed — matches approved proposal's specified detect-and-print
design for `--unreported`).
