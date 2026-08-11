# issue-732 survey — absorbed-branch respawn deadlock

## Scope of this survey

Read spawn.py's workspace-reuse and branch-checkout logic end to end
(`issue_workspace`, `checkout_issue_branch`, and the separate `clean`
subcommand's preservation guard), and reproduced the git mechanic that
actually causes the deadlock.

## Current flow (per-spawn, not `clean`)

`_spawn_one` (spawn.py:4386-4393) on every spawn with `--issue`:

1. `issue_workspace(cwd, issue, role)` (spawn.py:3998) — reuses the
   existing isolated clone directory if one already exists for
   `(issue, role)`, `git fetch`-ing it. It never inspects working-tree
   state; a reused workspace can carry untracked files from a prior
   session.
2. `checkout_issue_branch(cwd, issue, role)` (spawn.py:4111) — this is
   where the "fully-absorbed -> re-cut" logic already lives
   (spawn.py:4122-4161), added for issue-441/#428/#719:
   - if the local branch `issue-<n>/<role>` exists and is 0 commits
     ahead of `base` (`origin/main`) — "완전 흡수" — it re-cuts:
     `git checkout -B <br> <base>` (spawn.py:4157).
   - if that `checkout -B` fails (`r.returncode != 0`), the only
     fallback is `git checkout -B <br>` with **no** starting point
     (spawn.py:4158-4159) — i.e. reset the branch ref to whatever HEAD
     already is. This is a no-op re-cut: the branch stays exactly where
     it was (still 0 commits ahead of base).

`clean` (spawn.py:3766-3837) is a separate, operator-invoked subcommand.
Its preservation guard (spawn.py:3801-3811, "남김 (미보존 작업 있음)")
only decides whether to `rmtree` a workspace *directory* outright; it is
not on the per-spawn path and does not itself block `checkout_issue_branch`
from running. The issue's "preservation guard" language maps to this
`clean` logic in spirit (untracked work is why nothing gets discarded),
but the actual mechanical blocker on the respawn path is inside
`checkout_issue_branch`'s own `git checkout -B` fallback, not `clean`.

## Reproduced failure mechanic

`git checkout -B <br> <base>` does **not** touch untracked files that
don't collide with `base`'s tree — but it refuses outright (exit 1) when
an untracked file's path also exists in `base`'s tree with different
content ("이 파일을 옮기거나 제거하십시오" / "would be overwritten by
checkout"). Reproduced locally:

```
$ git checkout -B feature3 main
error: 체크아웃 때문에 추적하지 않는 다음 작업 폴더의 파일을 덮어씁니다:
        fileA.txt
브랜치를 전환하기 전에 이 파일을 옮기거나 제거하십시오.
중지함
exit: 1
```

When this happens inside `checkout_issue_branch`, the code falls back to
`git checkout -B <br>` (no base) — branch ref stays put, still 0 ahead of
`base`. The workspace is never actually re-cut. Every subsequent respawn
re-runs the same 0-ahead branch, the next PR attempt finds "No commits
between main and branch", and the operator's manual fix (back up
untracked files, `spawn.py clean`, respawn) is required to break the
loop — exactly the symptom the issue reports.

Even when there's no path collision (a genuinely new untracked
filename), the re-cut *does* succeed today — `checkout -B` doesn't
discard non-colliding untracked files. The deadlock is specifically the
path-collision case, but the issue's acceptance criteria describe the
general contract ("workspace whose branch is absorbed into main and
holds only untracked files is re-cut fresh with the untracked files
preserved onto the new branch") without carving out the collision case,
so the fix should hold for both.

## Write set implied by this survey

- `spawn.py` — `checkout_issue_branch`'s local_zero re-cut branch
  (spawn.py:4151-4159): stash/preserve untracked files before `checkout
  -B`, restore them after, instead of relying on plain `checkout -B`
  succeeding by luck.
- A test file covering `checkout_issue_branch` (none exists today for
  this function specifically — confirmed via grep below; the closest
  prior coverage is the issue-441/#428/#719 fixtures referenced in
  spawn.py's own comments, likely in a `test_spawn*.py` file).

```
$ grep -rln "checkout_issue_branch" --include='*.py' .
spawn.py
```

No existing test file imports/exercises `checkout_issue_branch`
directly — confirmed no pre-existing unit test would need modification,
only a new one added.

## Alternatives visible from this survey

- **Fix at `checkout_issue_branch`** (chosen in the proposal): stash
  untracked files (`git stash -u`) before the re-cut `checkout -B`, pop
  them after. Localizes the fix to the exact function that already owns
  the absorbed-branch re-cut decision; no new call site, no change to
  `issue_workspace` or `clean`.
- **Fix at `issue_workspace`**: detect the absorbed+untracked-only case
  earlier (before `checkout_issue_branch` runs) and clear the working
  tree there. Rejected — `issue_workspace` doesn't currently know about
  branch-vs-base ahead/behind state at all (that's computed inside
  `checkout_issue_branch` via `_base`), so this would duplicate the
  ahead-count logic across two functions instead of extending the one
  that already has it.
- **Fix at `clean`**: teach the preservation guard to distinguish
  "absorbed + untracked-only" from "real work" and auto-reclaim in that
  case. Rejected as the primary fix — `clean` is operator-invoked, not
  on the automatic respawn path; fixing only `clean` would still leave
  every *automatic* respawn deadlocked, which is the actual reported
  symptom.
