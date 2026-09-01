---
issue: 2973
role: adversarial-review-273d43cf
author: adversarial-review-273d43cf
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2984 (issue-2973/architecture-module-boundary-definition+test-derivation-61b1254f), reviewed and audited this session
code_under_review: lifecycle.py, spawn.py, tests/test_temp_root_reclaim.py
type: verification
breaking: no
verdict: pass
loop_state: terminal
upstream:
  - path: docs/issue-2973/reports/architecture-module-boundary-definition+test-derivation-61b1254f.md
    sha: 4673c385da6ded29a9cbcd18d441e092dbfeef61
---

# issue-2973 — adversarial-review-273d43cf record

## What was done

Independently verified PR #2984 (branch
`issue-2973/architecture-module-boundary-definition+test-derivation-61b1254f`,
head `4673c385da6ded29a9cbcd18d441e092dbfeef61`, base `main`). Fetched the
PR head into an isolated `git worktree` (`/tmp/review-pr-2984`, removed
before this record was written), re-ran both of issue #2973's acceptance
checks there from scratch — not by reading the PR's claimed output — and
read the full `lifecycle.py`/`spawn.py` diff line-by-line against the
issue's must-not list.

canonical: `gh pr view 2984 --json headRefName,headRefOid,baseRefName,commits` output this session — head `4673c385da6ded29a9cbcd18d441e092dbfeef61` (2 commits: code `3fe539f08c09632e6d34a5b048f07baf98363fc6` + upstream's own record `4673c385`), base `main`, state OPEN.

Acceptance checks, executed live this session against the fetched PR
branch in the isolated worktree, matching the PR body's claimed counts
exactly:

```
$ python3 -m pytest tests/ -k temp_root_is_managed -q
4 passed in 1.13s
$ python3 -m pytest tests/ -k temp_root_swept_without_session_cooperation -q
6 passed in 1.25s
```

derived: `python3 -m py_compile spawn.py lifecycle.py pipeline.py` (same worktree) — result: compiles clean, matching the PR body's claim.

derived: `python3 -m pytest tests/ -q` (same worktree, full `tests/` directory rather than the two `-k` filters alone, to catch any collection-time breakage the filters would hide) — result: `1 failed, 78 passed` — the one failure, `test_pre_existing_post_tool_use_commands_are_all_still_present` in `tests/test_spawn_gate_wiring.py` (a file untracked on this record's own branch, present only on PR #2984's branch, fetched and executed there this session), is pre-existing baseline noise unrelated to this PR. Confirmed by re-running the same file against this record's own branch (`issue-2973/adversarial-review-273d43cf`, `main` at `167cc19a`, no PR #2984 changes present): `python3 -m pytest tests/test_spawn_gate_wiring.py -q` — result: same failure, same assertion (`4 not greater than 4`), on a codebase state that never touched hooks.json.

Code-level audit against the issue's must-not list (`lifecycle.py`/`spawn.py` diff on the PR branch, read in full this session):

- **"do not sweep `/tmp` by name pattern"** — `sweep_temp_repos()` (`lifecycle.py`, new) only ever calls `base.glob("*")` where `base` defaults to `_temp_repos_base()` (`~/.tokenmaxxxer/tmp-repos`); there is no `/tmp` literal, glob, or name-pattern match anywhere in the new code. checked: full text of the added `sweep_temp_repos()`/`_temp_repos_base()` functions in `lifecycle.py` on the PR branch, read this session — no `/tmp` reference. Also covered by `test_temp_root_swept_without_session_cooperation_never_touches_slash_tmp` in `tests/test_temp_root_reclaim.py` (untracked on this record's own branch, present only on PR #2984's branch, fetched and executed there this session as part of the 6-passed run above), which plants a real, deliberately-aged canary directory directly under `/tmp` and asserts it survives the sweep.
- **"do not rely on the session deleting its own temp files as the primary mechanism; a session killed mid-run must still have its temp root reclaimed"** — `sweep_temp_repos()` never calls into session code or checks for any session-authored cleanup marker; it is a pure function of (a) directory mtime under `base` and (b) whether the corresponding roster entry's pid is currently alive. A session that dies before reaching any cleanup code leaves exactly the same on-disk state (a directory, no live roster entry) as a session that ran cleanup and simply didn't get to it — the sweep cannot distinguish the two, which is the point. `test_temp_root_swept_without_session_cooperation_reclaims_dead_entry` and `_dead_roster_entry_still_reclaimed` (same test file, same fetched-and-run status as above) both model this directly (empty/dead roster, aged directory, reclaimed), and I re-ran both in the isolated worktree.
- **"do not delete a temp root belonging to a live session"** — `sweep_temp_repos()` builds `live_names` from `roster.items()` filtered by `_alive(pid)` and skips any directory whose sanitized name is in that set, unconditionally on age (`if entry.name in live_names: kept += 1; continue` runs before the mtime check — checked: `lifecycle.py` `sweep_temp_repos()` body, read this session). `test_temp_root_swept_without_session_cooperation_spares_live_session` ages a live-session's directory to 30 days and confirms it survives — re-ran, passed.
- **"do not widen this to touch `~/.tokenmaxxxer/work` reclamation (issue #2960's scope)"** — `_temp_repos_base()` resolves to `~/.tokenmaxxxer/tmp-repos` (or `$MUSTER_TEMP_REPOS_ROOT`), a sibling of, not inside, `_workspace_base()`'s `~/.tokenmaxxxer/work`; `sweep_temp_repos()` never calls `_workspace_base()`, `auto_sweep()`'s workspace-cleanliness predicate, or anything from the issue #2960/#2963 code path — checked: `lifecycle.py` `sweep_temp_repos()`/`_temp_repos_base()` bodies, read this session, no reference to `_workspace_base` or `auto_sweep`. `test_temp_root_is_managed_distinct_from_workspace_base` asserts the two bases are unequal; re-ran, passed. `spawn.py`'s wiring adds `sweep_temp_repos()` as a third call inside the existing `_run_auto_sweep()` closure (alongside the pre-existing `auto_sweep()` and `_prune_orphaned_sidecars()` calls) rather than modifying either of those two functions or their arguments — checked: `spawn.py` diff hunk around `_run_auto_sweep()`, read this session.

Traced that `MUSTER_TEMP_ROOT` actually reaches the spawned session rather than merely being defined. checked: `spawn.py` on the PR branch, read this session — `extra_env["MUSTER_TEMP_ROOT"] = str(session_temp_root(roster_key))` is set on the same `extra_env` dict, in the same function scope (`_spawn_one()`), as the one later passed unmodified into `subprocess.Popen(cmd, cwd=cwd, ..., env={**os.environ, **extra_env}, ...)`, with no reassignment or scope break between the two points in either the bounded/fork or unbounded path. `session_temp_root()` also creates the directory eagerly (`root.mkdir(parents=True, exist_ok=True)`) before returning it, so the env var points at a directory that already exists by the time the child process starts, not merely a path string.

Confirmed the background sweep thread that calls `sweep_temp_repos()` is wired into the *existing* spawn-time auto-sweep thread rather than a new trigger point. checked: `spawn.py` `_run_auto_sweep()` on this record's own branch (pre-PR baseline) has only the workspace `auto_sweep()` + sidecar-prune calls; the same function on the PR branch adds the `sweep_temp_repos()` call as a third step in the same closure, gated by the same pre-existing `_clean_auto_enabled()` check, same daemon thread, same per-call exception-absorption pattern — no new `threading.Thread(...)` call site.

## Why

Per the loaded `adversarial-review` skill, this session's structural
independence from PR #2984's builder session (fresh context, no shared
reasoning trail, spawned separately per this repo's role-handoff
protocol) already satisfies the skill's core mechanism, so no further
nested evaluator session was spawned — the skill's mindset was applied
directly: re-deriving every acceptance number and must-not claim from a
freshly fetched worktree instead of reading the PR body's claimed output,
and specifically hunting for the failure mode the task named as the
whole point of the mechanism (a session that dies before reaching any
cleanup code) rather than accepting that the two acceptance tests'
existence implies that scenario is covered.

## What did not work

None.

## Upstream basis

- `docs/issue-2973/reports/architecture-module-boundary-definition+test-derivation-61b1254f.md` (untracked on this record's own branch — it lives only on PR #2984's branch at `4673c385da6ded29a9cbcd18d441e092dbfeef61`, fetched and read in full there this session) — sha: 4673c385da6ded29a9cbcd18d441e092dbfeef61
- `lifecycle.py`, `spawn.py`, `tests/test_temp_root_reclaim.py` (all at `3fe539f08c09632e6d34a5b048f07baf98363fc6`; the test file is untracked on this record's own branch, present only on the PR branch, read and executed in full from the fetched PR branch this session) — sha: 3fe539f08c09632e6d34a5b048f07baf98363fc6

## Open findings

None. Resolution path: not applicable — derived: see the `checked:`/
`derived:` citations under `## What was done` above (the two acceptance
re-runs, the four must-not-clause audit entries, and the
`MUSTER_TEMP_ROOT` trace); nothing surfaced there is left open to route
to a resolution path.

## Next steps

None — loop_state is terminal.

acceptance: `python3 -m pytest tests/ -k temp_root_is_managed -q; python3 -m pytest tests/ -k temp_root_swept_without_session_cooperation -q` — result:
```
4 passed in 1.13s
6 passed in 1.25s
```

skill-verdict: adversarial-review — applied: invoked; this session's
structural independence from PR #2984's builder session already
satisfies the skill's core mechanism (fresh context, no shared reasoning
trail), so no further evaluator session was spawned — the skill's
procedure was applied directly as the adversarial mindset for this
verification: re-deriving every claim from a fresh worktree instead of
reading the PR's claimed output, and treating the PR's own "test plan"
checklist as a set of claims to reproduce rather than facts to repeat.
other mounted skills: not triggered (work-in-english is guidance-only
per this session's directive stack, enforced by hook rather than invoked
via the Skill tool; this record was written in English throughout).
