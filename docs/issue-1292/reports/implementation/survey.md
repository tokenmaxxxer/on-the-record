Subject: issue-1292

Skip condition: pure bugfix. The required change mirrors an already-landed
pattern (#1282's demotion of the #1245 non-board `exit 1` to a
sweep-exclusion path) applied to the #1275 non-git `exit 1` in the same
file. No new design decision is open — the shape of the fix is dictated by
the existing non-board branch already in
`on-the-record/monitors/poll-heartbeat.sh`.

## Write set

- `on-the-record/monitors/poll-heartbeat.sh` — replace the non-git
  `exit 1` block (lines 55-64 pre-change) with a non-crashing `is_git`
  check that feeds into the existing `is_board` gate, so a non-git
  arm-root is forced to `is_board=0` without exiting.
- `tests/test_spawn.py` — new named cases under
  `PollHeartbeatMarkerRelocationTest` and the `_board_wide_sweep_all`
  test group covering: non-git root arms silently with an alive marker,
  non-git root + roster board target still sweeps that target, non-git
  root + empty roster is silent (empty-state case named in Acceptance).

## Existing spawn.py behavior

canonical: spawn.py:2659-2690, read this turn
`_board_wide_sweep_all` already excludes any arm-root lacking
`docs/specs/approvers.md` from the sweep, silently, regardless of git
status — a non-git root simply never has that marker file, so no
separate non-git branch is needed inside `spawn.py`.

canonical: spawn.py:1101-1120, read this turn
`_repo_slug` already catches `FileNotFoundError` from a missing cwd
(#1283) and treats any non-zero `gh` return as `None` — it does not
special-case "not a git repo" because it doesn't need to: `gh repo view`
simply fails non-zero there, same as any other `gh` auth/lookup failure,
and the cached `None` is handled by every caller already.

canonical: spawn.py:3619-3630, read this turn
`_repo_identity` falls back to the directory basename when `git remote
get-url origin` fails, by its own docstring's design. No change needed
there either.

canonical: shell command `grep -n "is_board"
on-the-record/monitors/poll-heartbeat.sh`, run this turn
That grep returns 3 hits, all inside the variable's own declaration
block (no other read site in the file). The shell-side `is_board`
variable exists purely so the loop's shape mirrors the #1280 non-board
fix; the actual sweep-exclusion enforcement lives in
`_board_wide_sweep_all`'s own `docs/specs/approvers.md` existence check.

Given the above, the fix is a single localized shell edit: remove the
`exit 1` and let the existing non-board gate absorb the non-git case.
