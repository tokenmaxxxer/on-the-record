---
code_under_review:
  - spawn.py
  - test_spawn.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record: issue-719

## Summary of work

Widened `_spawn_one()`'s branch-scoped spawn claim so `_release_spawn_claim()`
now fires after `ensure_pushed()` (push + `gh pr create`) completes, instead
of right after `proc.wait()`. Previously the claim was released before the
git-mutating push/PR-create calls ran, leaving a window where a respawn
could acquire the claim and race the first session's own tail push —
producing the field-log's non-fast-forward rejections and "No commits"
PR-create failures (per the issue's own quoted logs).

Added a re-cut guard to `checkout_issue_branch()`'s fully-absorbed check: it
now reads both the local `base..branch` ahead-count and the remote
`base..origin/branch` ahead-count. Re-cut from `base` only fires when both
are zero. When local reads zero but remote is ahead (local ref merely stale,
not the branch itself fully absorbed), the branch is instead fast-tracked to
`origin/branch` rather than reset to `base`, so a commit another workspace
already pushed is never silently dropped.

A before-landing warrant hunt (stance 0, see Hunt record below) found that
widening the claim's held window introduced a regression: an uncaught
exception inside `ensure_pushed()` would skip `_release_spawn_claim()`,
leaking the claim until stale-timeout — worse than the pre-fix code, which
released before `ensure_pushed()` ran at all. Fixed by wrapping the
`ensure_pushed()` call in `try/finally` so the claim releases on every exit
path, including an exception.

Regression tests added in `test_spawn.py`:
- `SpawnOneIssueRoleClaim.test_claim_still_held_during_ensure_pushed` — claim
  file still exists at the moment `ensure_pushed()` runs.
- `SpawnOneIssueRoleClaim.test_second_spawn_refused_while_first_still_pushing`
  — a second `_acquire_spawn_claim()` call during that window is refused.
- `SpawnOneIssueRoleClaim.test_empty_state_no_prior_claim_acquires_unchanged`
  — empty-state regression pin (no prior claim → acquire succeeds unchanged).
- `SpawnOneIssueRoleClaim.test_claim_released_when_ensure_pushed_raises` —
  hunt-driven fix: claim releases even when `ensure_pushed()` raises.
- `WorkspaceSyncFailClosed.test_checkout_tracks_origin_instead_of_recut_when_locally_stale_only`
  — local 0-ahead but remote ahead → tracks `origin/branch`, commit not lost.
- `WorkspaceSyncFailClosed.test_checkout_recuts_when_truly_fully_absorbed_local_and_remote`
  — empty-state regression pin (local and remote both 0 → re-cut from base,
  unchanged behavior).

## Why

Basis: `docs/issue-719/proposals/one-writer-claim-and-recut-guard.md`
(approved via `APPROVE issue-719/implementation`,
https://github.com/tokenmaxxxer/on-the-record/issues/719#issuecomment-5248642609).
The proposal's Rationale, backed by the survey
(`docs/issue-719/reports/implementation/survey.md`), traced the field-log
collision signatures to the release-before-push race, not to the
checkout-time re-cut path (already serialized by the issue-223 claim).
Widening the held window closes that race with no new primitive; the re-cut
guard closes the narrower but real staleness gap the survey also found
(local ref not updated by fetch alone).

## Doc placement ladder

- No env var, config key, new dependency, or migration introduced — no
  handbook update required.
- No library-or-format choice over a named alternative and no changed public
  signature/wire format beyond what the proposal's own Rationale already
  recorded — no new decisions entry needed.
- No benchmark/investigation numbers produced beyond the survey already on
  disk — no new report entry needed beyond this record and the hunt record
  below.

## What did not work

- Initial fix released the claim with a plain `_release_spawn_claim()` call
  right after `ensure_pushed()` returned (no `try/finally`) — the
  before-landing warrant hunt found this leaks the claim on any exception
  inside `ensure_pushed()`. Replaced with the `try/finally` wrap described
  above.

## Hunt record

Dispatched `warrant-hunter` before landing (stance 0: assume the gate just
touched is bypassable — find the bypass), cap 120s (diff ~197 lines,
`21-200` tier). Finding: claim leaked on `ensure_pushed()` exception — fixed
(see above). Full record at
`docs/issue-719/reports/implementation/hunt-one-writer-claim-and-recut-guard.md`.

## closed_checks

- full `test_spawn.py` suite, `code_under_review` as listed above.
  derived: `python3 -m pytest test_spawn.py -q` → `394 passed`

## Open findings

None — the one finding from the before-landing hunt was fixed in this same
commit (see What did not work / Hunt record above).
