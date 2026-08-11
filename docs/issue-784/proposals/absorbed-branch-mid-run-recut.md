---
status: proposed
files:
  - spawn.py
  - on-the-record/hooks/absorbed-branch-recut-guard.sh
  - tests/test_spawn.py
---

# Recut a mid-run session's own branch when it was absorbed by a concurrent merge

#784

## Request

A multi-phase role session opens its phase-1 PR and keeps running toward
phase 2. If an orchestrator merges that phase-1 PR (`--delete-branch`)
while the session is still alive, the session's checked-out branch is
absorbed into `main` out from under it, and its later phase-2 commit/PR-open
fails with "No commits between main and issue-<n>/<role>", silently
stranding whatever work it was mid-way through. Survey which of three fix
directions is least fragile and implement it.

## Constraints

- The fix must not depend on cross-process/cross-host visibility into
  another tool's private state (spawn.py's roster lives in the
  orchestrator's own repo checkout, not necessarily reachable from wherever
  a merge is executed).
- Must never silently drop in-progress uncommitted work (same bar #732 set
  for the spawn-time absorbed-branch case: untracked files are preserved
  across a recut, not discarded).
- Must not turn into a full periodic-polling mechanism — the recheck has to
  hang off an event the session already produces, not a new background
  process/timer.

## Rationale

Considered (a): a guard in `contract-guard.sh` that refuses/warns on
merging a PR whose `(issue,role)` session shows RUNNING in spawn.py's
roster (`runs/active.json`). Rejected: `contract-guard.sh` is explicitly a
zero-install hook that ships into arbitrary consumer repos and assumes only
`gh`+`python3` on PATH (its own header comment) — everything else it reads
(`docs/specs/approvers.md`, the target repo's own `.git`) is a property of
the repo being merged into. Reading spawn.py's roster file ties a generic
merge-broker hook to one orchestration tool's private, host-local state
file that the hook has no established way to locate, and — per this
hook's own documented fail-open design for lookup failures — a merge would
proceed silently exactly when the roster isn't reachable, i.e. exactly the
case that matters. This makes (a) fragile in precisely the deployment shape
the issue is worried about (an orchestrator merging without local access to
the spawning session's process table).

Considered (c): a directive that a multi-phase session must fully finish
before its phase-1 PR is mergeable. Rejected: the survey found no existing
mechanical gate that could enforce this (no hook today reads any liveness
signal), so it would land as pure convention — exactly the "left to
orchestrator vigilance" shape issue #784 explicitly says is not acceptable
for a systematically inducible failure.

Chosen: (b) extend #732's absorbed-branch detection so a session's own
mid-run work re-runs the same 0-ahead-vs-base check `checkout_issue_branch()`
already performs at spawn, right before the point where absorption would
otherwise surface as a silent PR-create failure. This reuses tested,
already-landed detection logic operating purely on the session's own git
workspace (no roster, no cross-process lookup, no new dependency), and only
adds *when* the check re-runs, not new detection machinery.

Hook-point correction (after-proposal warrant hunt,
docs/issue-784/reports/implementation/2026-08-11-hunt-absorbed-branch-mid-run-recut.md):
the first draft of this proposal named spawn.py's `_PROGRESS_BASH_PREFIXES`
match (spawn.py:2251, matched at spawn.py:4812) as the recheck's trigger.
The hunt found that site fires inside the parent orchestrator's
`for line in proc.stdout:` transcript scan (spawn.py:4725) — a read of NDJSON
already streamed out of the child `claude` subprocess, purely for logging.
It has no way to block or precede the child's own tool execution, so a
recut attached there would race with (and could lose to) the very
`git commit`/`gh pr create` it needs to precede, leaving the session
stranded exactly as before. The session's own `PreToolUse`/Bash hook chain
— the same synchronous, in-process mechanism `contract-guard.sh` already
uses to gate/deny `gh pr merge` before it executes (spawn.py:3456 wires
this same `PreToolUse` hook type for the doctor probe) — is the correct
interposition point: it runs inside the child session itself, before the
matched Bash command executes, and can act on the session's own working
directory directly.

## What will be done

- Add a new `PreToolUse`/Bash hook, `on-the-record/hooks/absorbed-branch-recut-guard.sh`,
  matching the same `git commit`/`gh pr create` prefixes spawn.py already
  tracks via `_PROGRESS_BASH_PREFIXES` (spawn.py:2251) — but as a real
  synchronous gate running inside the session's own process, the same
  mechanism `contract-guard.sh` uses, not the parent's post-hoc transcript
  scan. It ships zero-install with the plugin like `contract-guard.sh`/
  `deliverable-guard.sh`.
- Before allowing the matched command through, the hook runs the same
  "0-ahead vs base" local/remote comparison `checkout_issue_branch()`
  already performs at spawn (spawn.py:4171-4260: `local_zero`,
  `remote_stale_only`) against the session's own current branch/workspace
  (`git -C <cwd> rev-list --count base..HEAD` / `base..origin/HEAD`). This
  reuses the existing comparison logic rather than duplicating it — factor
  it out of `checkout_issue_branch()` into a shared helper in spawn.py (or
  a small standalone script the hook shells out to) callable from both the
  spawn-time call site and the new hook.
- When absorption is detected: preserve any untracked/uncommitted work the
  same way `checkout_issue_branch()` already does (stash-push, recut,
  stash-pop, with the existing leftover-stash recovery) directly in the
  session's workspace, then let the originally-matched command (the
  session's own `git commit`/`gh pr create`) proceed against the freshly
  recut branch — so it lands with real commits ahead of `main` instead of
  failing with "No commits between main and issue-<n>/<role>".
- Add coverage in `tests/test_spawn.py` for the factored-out shared helper
  (unit-level: given an absorbed branch state, it recuts and preserves
  untracked files — mirroring the existing
  `test_checkout_recuts_when_truly_fully_absorbed_local_and_remote` /
  `test_checkout_recuts_absorbed_branch_and_preserves_untracked_files`
  shape) plus a focused test invoking the new hook script directly against
  a fixture repo in the same merged/absorbed state, asserting it performs
  the recut before exiting 0 (allow).

## Accumulation

The change factors the existing absorption-check logic in
`checkout_issue_branch()` into a shared helper called from two sites
(spawn-time checkout, mid-run pre-commit hook) instead of adding a second
inline copy of the 0-ahead-vs-base comparison — so N more call sites in the
future (e.g. a future watchdog-driven recheck) would each call the same
helper, not paste another inline `git rev-list --count` comparison. This
proposal adds exactly one new call site; it does not touch any
repeated-file/roles-list shape (`runs/active.json` is read/written by
existing roster helpers, unchanged here).

## Out of scope

- Any change to `contract-guard.sh` or other merge-time hooks (direction
  (a), rejected above).
- Any new liveness/roster-reading mechanism.
- Changing what the orchestrator is allowed to merge or when — this fix is
  entirely on the session side.
- A directive-only fallback ((c)) — not needed once (b) lands, since (b)
  gives a mechanical guarantee instead of a convention.

## How you'll know it worked

- The new test simulating "session already running, branch merged+absorbed
  underneath it" passes: the session's subsequent commit/PR-open lands on a
  re-cut branch with real commits ahead of `main`, never hits "No commits
  between main and issue-<n>/<role>".
- Existing `test_checkout_recuts_*` / `test_checkout_tracks_origin_*` tests
  (tests/test_spawn.py:1428-1557) continue to pass unchanged — the spawn-time
  path is unaffected, only reused.
- Acceptance's empty state holds: a merge of a PR whose session already
  ended produces byte-identical behavior to today (the new check only ever
  fires on the *session's own* next commit/PR-open call, never as a result
  of the merge itself).
