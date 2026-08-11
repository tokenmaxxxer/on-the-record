---
status: proposed
files:
  - spawn.py
  - test_spawn_checkout_issue_branch.py
---

## Request

Fix the respawn deadlock described in #732: when a role's local branch
is fully absorbed into `origin/main` (0 commits ahead) and the
workspace's only unpreserved work is untracked files, the branch must
be re-cut fresh from `origin/main` with those untracked files carried
onto the new branch — instead of silently staying on the absorbed,
0-ahead branch forever.

## Constraints

- A workspace with real committable commits ahead of base must stay
  preserved exactly as today (byte-identical behavior) — this proposal
  touches only the already-fully-absorbed (`local_zero`) branch of
  `checkout_issue_branch`.
- Untracked work must never be silently dropped, in either the
  colliding-path or non-colliding-path case.
- No new dependency, no new environment variable, no change to
  `issue_workspace` or `clean`.

## Rationale

Two places could plausibly own this fix: `checkout_issue_branch`
(spawn.py:4111), which already contains the fully-absorbed re-cut
decision (spawn.py:4151-4159), or `clean` (spawn.py:3766), whose
preservation guard (spawn.py:3801-3811) is the piece of language the
issue title uses ("preservation guard").

Considered fixing `clean` instead: teach its guard to distinguish
"absorbed branch + untracked-only" from "real unpushed work" and let
`clean` reclaim the former automatically. Rejected — `clean` is a
separate, operator-invoked subcommand that never runs as part of a
normal respawn (`_spawn_one` never calls it). Fixing only `clean` would
leave the actual automatic-respawn path (`issue_workspace` ->
`checkout_issue_branch`) exactly as broken as today; the survey
confirmed the real mechanical blocker is `checkout_issue_branch`'s own
`git checkout -B <br> <base>` call failing on untracked path collisions
and falling back to a no-op re-cut (spawn.py:4157-4159), not anything in
`clean`. `checkout_issue_branch` already owns the ahead/behind
computation this fix needs (`_base`, `local_zero`) — extending it avoids
duplicating that computation in a second function.

## What will be done

In `checkout_issue_branch`'s `local_zero` branch (spawn.py:4151-4159):

1. Before calling `git checkout -B <br> <base>`, check for untracked
   files (`git status --porcelain --untracked-files=all` or
   `ls-files --others --exclude-standard`).
2. If any exist, `git stash push -u -q -m <marker>` them off first, then
   perform the existing `checkout -B <br> <base>` re-cut.
3. After a successful re-cut, `git stash pop` the preserved untracked
   files back onto the fresh branch. If the stash pop reports a
   conflict (the file collides with something now present from
   `base`'s tree), do not silently drop the stash — leave it and print a
   clear message pointing at `git stash list`/`git stash show` so a
   human/operator can resolve it manually, and continue (do not
   sys.exit) so the respawn itself doesn't hard-fail over a stash
   conflict that a plain checkout would have hard-failed on anyway
   today.
4. If there are no untracked files, behavior is unchanged (no stash
   round-trip introduced for the common case).
5. The fallback path when `checkout -B <br> <base>` itself still fails
   for an unrelated reason (spawn.py:4158-4159, `checkout -B <br>` with
   no base) is left as-is — that's a pre-existing "base not found"
   safety net, out of scope here.

## Out of scope

- `clean`'s preservation guard and its "남김 (미보존 작업 있음)" message
  — unchanged; a workspace with real unpushed commits still behaves
  exactly as before.
- The `remote_stale_only` branch (spawn.py:4142-4150) and the
  origin-tracking `checkout -b` branches (spawn.py:4162-4174) —
  untouched, not part of the absorbed-branch case.
- Any change to how squash-merge absorption itself is detected
  (`ahead = rev-list --count base..br`) — out of scope; this proposal
  only changes what happens to untracked files once `local_zero` is
  already true.

## Accumulation

This is the sixth distinct root cause in the "No commits between main
and branch" symptom family (issue text names #700, #719,
tokenmaxxxer-core#203, on-the-record#705, plus this one). Each prior fix
added its own dedicated branch inside `checkout_issue_branch` (the
`remote_stale_only` check from #719, the `local_zero` re-cut itself from
#441/#428) rather than a shared helper — `checkout_issue_branch` is
becoming a small decision tree of "if this specific absorption/staleness
shape, do this specific recovery." This proposal adds one more branch
(untracked-preserve-around-recut) to that same tree instead of
introducing a seventh standalone code path. If a seventh root cause in
this family appears, the next fix should extend the same if/elif ladder
in `checkout_issue_branch`, not add a parallel decision function — the
function is already the single place that owns "what do we do with this
reused workspace's branch," and splitting that decision across multiple
functions is what the rejected `clean`-based alternative above would
have done.

## How you'll know it worked

A new unit test (`test_spawn_checkout_issue_branch.py`) builds a fixture
repo where:
- `issue-<n>/<role>` is fully absorbed into `base` (0 commits ahead),
  and
- the workspace holds only untracked files (including one whose path
  collides with a file that exists in `base`'s tree, reproducing the
  `checkout -B` failure mode found in the survey),

then asserts, after calling `checkout_issue_branch`:
- the branch was re-cut from `base` (its tip commit now equals `base`'s
  tip), and
- the untracked files are present in the working tree on the new
  branch (still untracked, i.e. `git status --porcelain` still lists
  them, but no data was lost).

A second fixture — a workspace with real committable commits ahead of
base and untracked files — asserts the workspace is preserved exactly
as today (branch unchanged, untracked files untouched, no stash
invoked), matching the acceptance criterion's "empty state" (byte-identical
to today).
