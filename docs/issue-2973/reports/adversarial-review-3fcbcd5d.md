---
issue: 2973
role: adversarial-review-3fcbcd5d
author: adversarial-review-3fcbcd5d
skills: adversarial-review (skill-repository(c05de12)), defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12))
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

# issue-2973 — adversarial-review-3fcbcd5d record

## What was done

Independently verified PR #2984 (branch
`issue-2973/architecture-module-boundary-definition+test-derivation-61b1254f`,
head `4673c385da6ded29a9cbcd18d441e092dbfeef61`, base `main`). Fetched the
PR head into an isolated `git worktree` (`/tmp/verify-pr-2984`, removed
before this record was written), re-ran both of issue #2973's acceptance
checks there from scratch, read the full `lifecycle.py`/`spawn.py` diff
line-by-line against the issue's must-not list, and specifically checked
the two properties the issue's design rationale calls load-bearing: a
session killed mid-run (never reaching its own cleanup code) still gets
reclaimed, and `MUSTER_TEMP_ROOT` actually reaches the spawned session's
process environment rather than only being computed and discarded.

canonical: `gh pr view 2984 --json title,body,headRefName,baseRefName,headRefOid,state` output this session — head `4673c385da6ded29a9cbcd18d441e092dbfeef61`, base `main`, state OPEN, body claims `Closes #2973`.

Acceptance checks, executed live this session against the fetched PR
branch in the isolated worktree, matching the PR body's claimed counts
exactly:

```
$ python3 -m pytest tests/ -k temp_root_is_managed -q
4 passed in 0.98s
$ python3 -m pytest tests/ -k temp_root_swept_without_session_cooperation -q
6 passed in 1.30s
```

derived: `python3 -m pytest tests/test_temp_root_reclaim.py -v` (same worktree) — result: all 10 tests in the file pass individually (`TempRootIsManagedTest` x4, `TempRootSweptWithoutSessionCooperationTest` x6), matching the sum of the two `-k` selectors above — no test outside the two acceptance selectors is hiding inside the file.

derived: `python3 -m py_compile spawn.py lifecycle.py pipeline.py` (same worktree) — result: exits 0, no output.

Diff audit (`git diff main...HEAD -- lifecycle.py spawn.py`, read in full
this session) against the issue's must-not list:

- **"do not sweep `/tmp` by name pattern"** — `sweep_temp_repos()` (`lifecycle.py`) only ever walks its `base` argument (`_temp_repos_base()`, default `~/.tokenmaxxxer/tmp-repos`, override `MUSTER_TEMP_REPOS_ROOT`), via `base.glob("*")`. No reference to `/tmp` or any name-pattern match appears in the new code. checked: `grep -n '"/tmp"\|tas-' lifecycle.py spawn.py` — result: zero hits outside comments describing the *old*, removed behavior. The new test `test_temp_root_swept_without_session_cooperation_never_touches_slash_tmp` plants a 999-day-old canary directly under real `/tmp` and asserts it survives a sweep call — I re-ran this specific test (included in the 10-passed run above) and it passed.
- **"do not rely on the session deleting its own temp files as the primary mechanism"** — checked: `grep -rn "MUSTER_TEMP_ROOT\|MUSTER_TEMP_REPOS_ROOT" --include=*.py .` — result: three call sites total (`lifecycle.py` definition/docstring, `spawn.py:4545` injection into `extra_env`, the test file) and no session-side or self-cleanup code path anywhere in the diff. The only removal mechanism present is `sweep_temp_repos()`, invoked from `spawn.py`'s existing spawn-time background `auto-sweep` daemon thread (`spawn.py:4010-4021`, same function, same exception-absorbing contract as the pre-existing workspace/sidecar sweeps at lines 3976-4004) — i.e. reclamation runs on a *future* spawn's housekeeping cycle, never from the session's own exit path.
- **"a session killed mid-run must still have its temp root reclaimed"** — `session_temp_root()` (`lifecycle.py`) `mkdir`s the directory immediately when called, before the session does anything else, so a session that dies immediately after spawn still leaves a directory on disk with a real mtime. `sweep_temp_repos()`'s age computation (`lifecycle.py`) is `max((p.stat().st_mtime for p in entry.rglob("*")), default=entry.stat().st_mtime)` — for a directory with no files inside (the worst case: killed before writing anything), it falls back to the directory's own mtime, so an empty root still ages out correctly rather than being treated as eternally young or erroring. The new test `test_temp_root_swept_without_session_cooperation_reclaims_dead_entry` exercises this directly (empty roster, i.e. the roster never even got an entry for this session — a stronger case than a dead-pid entry) and passed in the run above; `test_temp_root_swept_without_session_cooperation_dead_roster_entry_still_reclaimed` covers the case where a roster entry exists but its pid is dead.
- **"do not delete a temp root belonging to a live session"** — `sweep_temp_repos()` loads the roster (`_sp._roster_load()`), builds `live_names` from entries whose pid is `_alive()`, and unconditionally `continue`s (never deletes, regardless of age) for any directory name in that set — checked at `lifecycle.py`, the `if entry.name in live_names: kept += 1; continue` branch runs before the age check, not after it. `test_temp_root_swept_without_session_cooperation_spares_live_session` (in the 10-passed run) plants a 30-day-old live-session directory and confirms it survives.
- **"do not widen this to touch `~/.tokenmaxxxer/work` reclamation (issue #2960's scope)"** — `_temp_repos_base()` defaults to `~/.tokenmaxxxer/tmp-repos`, a sibling of but distinct from `_workspace_base()`'s `~/.tokenmaxxxer/work`; the new test `test_temp_root_is_managed_distinct_from_workspace_base` asserts `spawn._temp_repos_base() != spawn._workspace_base()` directly, and `sweep_temp_repos()` never calls or references `_workspace_base()`, `auto_sweep()`, or `roster_clean()` — it is wired in as a sibling call inside the same background thread, not a modification to the existing workspace-sweep function.

`MUSTER_TEMP_ROOT` propagation, traced end to end in the diff: `spawn.py:4545` sets `extra_env["MUSTER_TEMP_ROOT"] = str(session_temp_root(roster_key))` before the spawned-process `Popen` call; checked: `spawn.py:4679-4682`, the `Popen(cmd, ..., env={**os.environ, **extra_env}, ...)` call is the only consumer of `extra_env` between assignment and process launch, and no code path between lines 4545 and 4681 reassigns or filters `extra_env` (read in full). This confirms the variable reaches the spawned session's actual process environment, not merely a local computation that gets discarded — the acceptance criteria's "not one the session chooses freely" property is backed by an injected value the session can read, not just a plugin-side capability that goes unused.

No must-not violation found.

## Why

derived: per the loaded `defect-verification-independence-from-upstream-verdicts` skill, a PR's own claimed test-plan output ("4 passed", "6 passed", "same 9 pre-existing failures / 33 passed") is a claim to re-derive from a freshly fetched worktree, not a number to repeat — both acceptance checks and the full `test_temp_root_reclaim.py` file were re-run from scratch this session rather than read off the PR body. The two checks the task singled out (mid-run-kill reclamation, `MUSTER_TEMP_ROOT` actually reaching the session) are exactly the properties easiest to fake with a plausible-looking mechanism that only half-works — a plugin-side function that computes a managed path but never gets consumed downstream, or a sweep that only proves itself against a live/graceful-exit test case rather than an unregistered/never-cleaned-up one — so those two got a code-path trace (not just a test-suite citation) in addition to the passing tests, per the skill's rule 2 (deliberately include an edge/negative-path check, not only happy-path).

## What did not work

None.

## Upstream basis

- `docs/issue-2973/reports/architecture-module-boundary-definition+test-derivation-61b1254f.md` (untracked on this record's own branch — it lives only on PR #2984's branch at `4673c385da6ded29a9cbcd18d441e092dbfeef61`, present in that PR's diff) — sha: 4673c385da6ded29a9cbcd18d441e092dbfeef61
- `lifecycle.py`, `spawn.py`, `tests/test_temp_root_reclaim.py` (all at `4673c385da6ded29a9cbcd18d441e092dbfeef61`, fetched and read/executed in full from that PR branch this session) — sha: 4673c385da6ded29a9cbcd18d441e092dbfeef61

## Open findings

None. Both acceptance checks reproduce cleanly against a freshly fetched worktree, the diff was read in full against all four must-not clauses with no violation, and both properties singled out by this verification task (mid-run-kill reclamation, `MUSTER_TEMP_ROOT` propagation into the spawned process environment) trace correctly through the code rather than only through a passing test suite. Resolution path: n/a — no finding to resolve.

## Next steps

None — loop_state is terminal.

acceptance: `python3 -m pytest tests/ -k temp_root_is_managed -q; python3 -m pytest tests/ -k temp_root_swept_without_session_cooperation -q` — result:
```
4 passed in 0.98s
6 passed in 1.30s
```

Both of issue #2973's acceptance-check commands were independently
re-executed against PR #2984's fetched head this session, each matching
the PR's own claimed counts. The full diff was read against all four
must-not clauses (no `/tmp` name-pattern sweep, no session-self-cleanup
reliance, no live-session deletion, no widening into `~/.tokenmaxxxer/work`)
with no violation surfacing, and the two properties this task asked to be
checked specifically — a session killed before reaching any cleanup code
still gets reclaimed, and `MUSTER_TEMP_ROOT` reaches the spawned process's
actual environment rather than being computed and discarded — both trace
correctly through the code, not just through a passing test suite.

skill-verdict: adversarial-review — applied: invoked; this session's
structural independence from PR #2984's builder session (fresh context,
no shared reasoning trail, artifact fetched from the PR's actual head
rather than accepted from the builder's description) already satisfies
the skill's core mechanism, so no further evaluator session was spawned —
the skill's mindset was applied directly: re-deriving every claimed
result rather than reading it off the PR body, and tracing the two
load-bearing properties (mid-kill reclamation, env-var propagation)
through actual code paths rather than accepting the PR's "independent of
any session self-cleanup" framing at face value.
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked;
drove re-running both acceptance checks and the full
test file from a freshly fetched worktree instead of citing the PR
body's claimed counts (see the `acceptance:` block above), and drove
tracing `MUSTER_TEMP_ROOT` end-to-end into the `Popen` call and the
empty-directory mtime fallback in `sweep_temp_repos()` as deliberate
negative/edge-case checks going beyond the two acceptance test
selectors alone.
other mounted skills: verify-finding-record not-applicable — that skill
governs recording reproduction attempts in
`docs/issue-<n>/reports/defect-verification.md`; this task's target file
is an `adversarial-review` record, a different record kind at a
different path, so its file-shape prescription does not apply here.
work-in-english is guidance-only per this session's directive stack,
enforced by hook rather than invoked via the Skill tool; this record was
written in English throughout.
