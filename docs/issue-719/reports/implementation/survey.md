# Survey: branch-collision paths in spawn.py (issue-719)

## Existing claim (issue-223, merged 2026-08-03, PR #249)

`_acquire_spawn_claim()` / `_rewrite_spawn_claim_pid()` / `_release_spawn_claim()`
(spawn.py:4245-4329) already implement a one-writer-per-(issue,role) claim:
an `O_CREAT|O_EXCL`-via-`os.link()` claim file at `<work>.spawn-claim`, PID
liveness check (`_alive()`, spawn.py:1762) for staleness, one retry after
stale cleanup.

derived: `gh issue view 719` body text (the issue author's own field-log
summary, quoted verbatim, not independently re-derived here): "issue-289:
three `session-end` events with ... non-fast-forward" and "issue-319: 8
sequential respawns in an 11-minute window". The issue dates these events
2026-08-11. `git log -1 --format=%ad 48266e7` shows #223 merged
2026-08-03 — i.e. the claim already existed when these collisions were
observed. So the claim exists but does not cover the actual collision
window — the survey below traces where.

## Claim lifecycle vs. the actual git-mutation window

In `_spawn_one()` (spawn.py:4331-4913):

- `cwd = issue_workspace(...)` (4370) — clone/reuse workspace.
- `_acquire_spawn_claim(cwd, issue, role)` (4371) — claim taken.
- `checkout_issue_branch(cwd, issue, role)` (4376) — branch cut/reuse/re-cut.
- ... session runs (subprocess, `proc.wait()` at 4712) ...
- `roster_remove(roster_key)` (4713)
- `_release_spawn_claim(cwd, os.getpid())` (4715) — **claim released here**
- `finally:` unlink settings tempfile (4716-4718)
- ... (uncommitted-work check, `_git_head`, `git status`) ...
- `push_result = ensure_pushed(cwd, issue, role)` (4745) — **push + `gh pr
  create` happen here, after the claim is already gone**

`ensure_pushed()` (spawn.py:4161-4228) does the actual `git push origin
<branch>` (4192) and `gh pr create --head <branch>` (4214) — these are the
exact two operations whose failure signatures match the issue (`[rejected]
... non-fast-forward` and `No commits between main and branch`).

**Gap**: the claim's protected window ends at `proc.wait()`, but the git
mutations the collision reports are about (push, PR-create) happen ~30-80
lines later, unprotected. Any second spawn for the same (issue,role) that
acquires the claim in that gap — a self-triggered respawn
(`_self_trigger_respawn`, spawn.py:2662, itself routed through
`_spawn_one(..., bounded=True)` at spawn.py:2618, i.e. it re-enters the
same claim/checkout path) or a manual/orchestrator-driven respawn racing
the first session's tail — can:

1. Reuse the same workspace (issue_workspace reuses `<work>` if
   `.git` exists, spawn.py:4042-4064), run `checkout_issue_branch()` while
   session 1's `ensure_pushed()` push is in flight or has already advanced
   `origin/<branch>`, and add its own commits on top of a HEAD that is
   about to be superseded by session 1's own late push — two `git push`
   calls against the same remote ref from two different local histories.
   This matches the non-fast-forward rejection pattern.
2. If session 1's `ensure_pushed()` has not yet run its `gh pr create`
   check (has_open computed from `gh pr list --head <branch> --state
   open`, 4203-4206) when session 2 starts and quickly ends
   with no new commits of its own (e.g., a respawn that finds the branch
   already fully delivered locally but hasn't seen the just-pushed
   remote state — `_fetch_or_halt` in `checkout_issue_branch` happens
   before session 1's `ensure_pushed` push lands), `ensure_pushed`'s own
   ahead-count check (`git rev-list --count origin/<branch>..<branch>`,
   4188) can read `0` and skip the push, then the immediately following
   `gh pr create` step still races the other session's own PR-create call.

## `checkout_issue_branch()` re-cut logic (spawn.py:4111-4158)

The "fully absorbed → re-cut" branch (4122-4144): when the local branch
ref exists, it compares `rev-list --count base..branch`; if `0` (fully
merged into base) it force-resets the local branch from base
(`checkout -B br base`) — discarding the local ref, never the remote one.
This path is only reachable while holding the claim (`_acquire_spawn_claim`
runs at 4371, strictly before `checkout_issue_branch` at 4376), so a
*second live session* cannot trigger this specific re-cut concurrently
with a first live session — the claim already serializes entry into
`checkout_issue_branch`. The re-cut's blast radius is real but narrower
than advertised: it only fires when local `branch` is 0-ahead of `base`,
which cannot be true for a session mid-flight with committed-but-unpushed
work (that work makes it >0-ahead). So the re-cut itself does not appear
to be the mechanism behind the field-log collisions — the claim-release
timing gap above is the better-supported cause given the log signatures
(non-fast-forward / no-commits are push/PR-create symptoms, not
checkout-time re-cut symptoms).

However the re-cut check has its own latent gap worth naming: it trusts
*local* ahead-count only. If `origin/<branch>` carries commits ahead of
`base` that this workspace's local `branch` ref does not yet know about
(e.g., another *host's* workspace pushed to `origin/<branch>` and this
workspace has stale local refs for `branch` itself, e.g. because
`checkout_issue_branch`'s earlier `_fetch_or_halt` updates
`origin/<branch>` in the fetch but the local branch ref `<branch>` is only
updated by an explicit checkout/reset, not by fetch alone), the local
`rev-list --count base..branch` can read `0` and re-cut a branch that is
NOT actually fully absorbed on the remote — only locally stale. This is a
cross-workspace (cross-host) scenario the claim (a local file next to
`<work>`) cannot detect at all, since two different hosts/work-dirs never
see each other's claim file.

## Claim scope: local filesystem only

`_spawn_claim_path()` (4241-4242) returns `Path(str(work) + ".spawn-claim")`
— a sibling path next to the workspace directory on the *same filesystem*.
`work` is derived from `MUSTER_WORK_DIR` / `~/.tokenmaxxxer/work` (issue_workspace,
4031-4037), i.e. per-host. Two spawn.py processes on two different hosts
(or two different `MUSTER_WORK_DIR` roots on the same host) for the same
(issue,role) never see each other's claim file — nothing prevents that
collision today. The issue text's "field logs from a consumer repo" is
consistent with a deployment where more than one host/environment can
spawn against the same GitHub repo; the claim as built is silent about
that case entirely (no remote-side marker exists to check).

## Write set this proposal will use

- `spawn.py` — widen the claim's held window to cover `ensure_pushed()`,
  and add a re-cut guard that checks remote (`origin/<branch>`) ahead-count
  in addition to the existing local ahead-count.
- `test_spawn.py` — unit coverage for the widened claim window and the
  re-cut guard (both named in the issue's Acceptance).

## Alternatives visible from this survey (for the proposal's Rationale)

- **A. Widen the local claim's held window** to also cover `ensure_pushed()`
  (release after push+PR-create, not after `proc.wait()`). Cheap, no new
  dependency, fixes the exact race traced above. Does not fix cross-host
  collision, but no field-log signature in the issue requires cross-host
  coverage to explain (single-claim-file races inside one host's respawn
  loop already reproduce every quoted symptom).
- **B. Add a remote-side claim** (e.g. a `refs/claims/issue-<n>/<role>`
  ref checked before `checkout_issue_branch`/`ensure_pushed`), in addition
  to A. Would also cover true cross-host collision, but adds a new
  remote-visible primitive and a network round-trip on every spawn for a
  scenario the current field logs do not establish is in play. Deferred:
  worth a follow-up issue if cross-host spawning is confirmed to happen,
  not bundled into this fix.
- **C. Serialize `ensure_pushed()` itself with `git push --force-with-lease`**
  instead of widening the claim, accepting rejections as the concurrency
  mechanism and having the loser retry. Rejected: this is what already
  happens today (plain `git push`, 4192) and produces exactly the
  field-log failure signature — it is the problem, not a fix.
