---
issue: 2293
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: "GitHub issue #2293 body + consumer scope-addition comment (2026-08-25)"
    sha: same-commit
  - path: "prior delivery PR #2306 / execution-observation PR #2361 (both closed, no commit on main)"
    sha: same-commit
code_under_review:
  - pipeline.py
  - spawn.py
  - watchdog.py
  - tests/test_admission_checklist.py
  - tests/test_spawn_gate_wiring.py
  - tests/test_spawn_pipeline.py
type: feat
breaking: none
verdict: pass
---

# issue-2293 — implementation record

## What was done

canonical: `gh pr view 2306 --json state,mergeable,baseRefName` (state
`CLOSED`, mergeable `CONFLICTING`, base `main`) and `gh pr view 2361
--json state` (state `CLOSED`) — both read live at the start of this
session, before any code change.

Re-delivered issue #2293 from current `main` (46da1c8a19...) after the
prior delivery (PR #2306, independently execution-observed clean in PR
#2361) was closed unmerged by the 2026-08-25 history rewrite. This
redelivery also folds in the consumer's scope-addition comment posted
after PR #2306 landed, so it covers all three asks in one PR:

1. **Admission-time refusal of degenerate tasks** (`pipeline.py`): a new
   `ADMISSION_CHECKS` row, `("degenerate-task", _admission_check_degenerate_task)`
   — table-driven, per the issue #2100 machinery, no new gate loop.
   Refuses when the positional `task` is bare-numeric, `#`-prefixed
   numeric, or `-`-prefixed numeric (the last via argparse's own
   negative-number handling, which lets a leading-dash digit string
   through as a plain positional when no option string looks like a
   negative number) and `--issue` was not given. The refusal message
   names the almost-certain intent: `did you mean: spawn.py <role>
   "<task>" --issue <n>`. A new `--force-adhoc-task` CLI flag
   (threaded through `_spawn_one`'s ctx as `force_adhoc_task`) overrides
   for the rare legitimate numeric-task case.

2. **Adhoc isolation** (`spawn.py`): `issue_workspace()` now accepts
   `issue: int | None` and, when `issue is None`, clones into
   `<repo>-adhoc-<role>-<pid>` under the same managed work base an
   issue-scoped spawn uses, instead of the caller running directly in
   `-C` cwd. `_spawn_one` calls this for every adhoc spawn right where
   the issue-scoped branch already does its own workspace setup (both
   gated on `issue is None` / `issue is not None` respectively, same
   `if` level). Keyed by pid rather than issue number, since an adhoc
   task has no stable identity to resume across respawns — it always
   takes the fresh-clone path, never the two reuse branches
   `issue_workspace()` already had: a stale leftover directory found at
   the pid-keyed path (e.g. a crashed prior adhoc spawn, or a reused
   pid) is wiped before the fresh clone runs. See "What did not work"
   for the shape this took before this record's final revision.

3. **Timestamped+PID fallback log** (`spawn.py`): removed the
   `ROOT / "runs" / "last-session.log"` shared fallback and unified
   `log_path = _session_log_path(cwd)` for both issue-scoped and adhoc
   spawns — since `cwd` is now isolated and pid-unique for adhoc too,
   the existing `_session_log_path()` precedent (`pipeline.py`, issue
   #192: `<work>.session.<ts>.<pid>.log`) already produces a
   collision-free path without any adhoc-specific branch.

4. **Watchdog adhoc-visibility** (`watchdog.py`): `diagnose_health()`'s
   `_diagnosis()` wrapper — the single point every return path in the
   function already goes through — now prefixes `detail` with
   `ADHOC task="<first 60 chars>"` (or `ADHOC (no task recorded)`) when
   `entry.get("issue") is None`, before the existing per-state text. The
   always-printed `[poll-report]` line (`watchdog.py` roster-poll loop)
   therefore can never read a degenerate-task adhoc session's HEALTHY as
   "your issue-N spawn is fine". The roster entry written in
   `_spawn_one` now carries `"task": task if issue is None else None` so
   the watchdog has something to show.

## Why

Table-driven admission (issue #2100) was the existing, tested mechanism
for exactly this class of defect — "cheap to detect at admission,
expensive to detect after an agent is live" is the issue's own framing,
and it's the same shape as the existing `board-validity` item (#2123):
a deterministic local check, refuse-named, never fail-open, with the
predicate's own `print()` carrying the specific remediation text before
`admission_gate()`'s generic refusal message. No new gate code was
needed — one row.

For isolation, reusing `issue_workspace()` (rather than writing a
parallel adhoc-only clone routine) keeps the origin-normalization,
protected-path check, and credential-exclude logic in one place instead
of forking it. Keying the adhoc directory name by pid instead of trying
to invent a stable adhoc identity avoids scope creep — the issue only
asks for isolation and a distinct log path, not a resume/reuse story
for one-shot adhoc tasks, and the existing reuse branches in
`issue_workspace()` naturally never trigger for a pid-unique name.

Unifying the log path (rather than adding an adhoc-specific timestamped
path formatter) was possible only because isolation landed first: once
`cwd` is pid-unique, `_session_log_path(cwd)` already does exactly what
issue #192 built it for, with no new code.

Tagging `detail` inside `_diagnosis()` (rather than in each of the
five-ish individual return branches in `diagnose_health()`) was chosen
because it is the one point every return path already funnels through
(it already merges in `ckpt_fields` uniformly) — adding the ADHOC
prefix there is the same "single injection point" shape rather than a
fifth near-duplicate branch.

## What did not work

The first version of the adhoc isolation (item 2 above) claimed in its
own docstring that an adhoc spawn "always takes the fresh-clone path
... rather than the reuse branches" in `issue_workspace()`, but the
code did not actually skip the reuse-by-existing-directory branch for
`issue is None` — only the naming differed. A before-landing
warrant-hunt agent (record:
`docs/issue-2293/reports/implementation/2026-08-25-hunt-2293-implementation.md`)
reproduced the gap: with `os.getpid()` mocked to collide across two
calls (simulating the OS reusing a pid once its number wraps, or a
crashed prior adhoc spawn leaving its clone behind), the second adhoc
spawn silently inherited the first one's committed branch and leftover
file — no error, no divergent log line. Fixed by wiping any stale
directory at the pid-keyed adhoc path before falling through to the
fresh-clone code, so the docstring's claim now holds in code, not just
prose. Regression test:
`AdhocIsolationAndLogPath.test_stale_pid_keyed_workspace_is_wiped_not_reused`
in `tests/test_spawn_pipeline.py`.

## Upstream basis

canonical: `gh issue view 2293 --comments` (issue body + 4 comments,
read live at the start of this session) and `gh pr view 2306`/`gh pr
view 2361 --json state,mergeable,baseRefName,title,body` (both closed,
no commit landed on `main`).

- GitHub issue #2293 body (admission-refusal ask, Acceptance section)
  and the consumer's scope-addition comment (isolation + timestamped
  log ask).
- Prior delivery PR #2306 (`issue-2293/implementation`, closed,
  `mergeable: CONFLICTING`) and its independent execution-observation
  PR #2361 (closed, no discrepancies found) — read for the exact shape
  of the previously-verified fix, before reimplementing it fresh
  against current `main` (46da1c8a19...) since neither PR's commits
  exist on this branch (`git log --oneline -5` at session start showed
  no issue-2293 commits; `git diff main --stat` showed zero code diff
  before this session's edits).

## Open findings

None.

## Next steps

None — `loop_state: landed`. Acceptance evidence (live CLI refusal,
override, and unaffected-normal-spawn runs; full `degenerate-task` gate
suite) is below.

## Acceptance evidence (executed-live)

Gate: `tests/test_spawn_pipeline.py` (per issue's Acceptance line),
plus the two suites that carry the admission-table and watchdog
coverage for this change.

acceptance: `python3 -m pytest tests/test_admission_checklist.py -n0 -q` — result (re-run after the warrant-hunt fix below):
```
...............................
31 passed in 0.44s
```

acceptance: `python3 -m pytest tests/test_spawn_pipeline.py -n0 -q` — result (re-run after the warrant-hunt fix below, +1 test vs the pre-fix run: the new stale-workspace regression test):
```
........................................................................
.................
89 passed in 4.90s
```

acceptance: `python3 -m pytest tests/test_spawn_gate_wiring.py -n0 -q` — result:
```
...
FAILED tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace
1 failed, 70 passed in 87.35s
```

canonical: the one failure above is pre-existing and unrelated —
reproduced identically (same `AssertionError`, same env-path mismatch)
by running the exact same test with this branch's diff `git stash`-ed
away (clean `main`, 46da1c8a19...):
```
$ git stash && python3 -m pytest tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace -n0 -q; git stash pop
...
FAILED tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace
1 failed in 29.18s
```

Live CLI repro 1 — the exact consumer incident, post-fix:

acceptance: `python3 spawn.py implementation 538; echo "RC=$?"` — result:
```
[admission] degenerate-task: task '538' looks like an issue number; did you mean: spawn.py implementation "<task>" --issue 538? Pass --force-adhoc-task to admit this literal task anyway.
[implementation] admission refused: missing precondition 'degenerate-task' (issue #2100) — no session created, no workspace left behind. This refusal is deterministic and non-retryable: publish the missing precondition, then dispatch again.
RC=1
```

Also verified `-538` (the before-landing-warrant-hunt bypass shape from
the prior delivery, PR #2306) and `#538` refuse identically with RC=1
and identical did-you-mean text, and neither run created a roster entry
(`~/.tokenmaxxxer/state/active.json` grep for `538`/`adhoc` empty
afterward).

Live CLI repro 2 — override path (direct predicate call, same choice
PR #2361's execution-observation made: `--force-adhoc-task` on the full
CLI path forks a real nested live session, so the direct-call form is
used instead — `--force-adhoc-task` itself is exercised end-to-end by
`test_force_adhoc_task_admits_and_no_workspace_change` in
`tests/test_admission_checklist.py`, which goes through
`admission_gate()` and confirms no refusal ledger event):

acceptance: direct predicate call with `force_adhoc_task=True` — result:
```
override admits: True
```

Live CLI repro 3 — adhoc-labeled watchdog line (direct
`diagnose_health()` call against a synthetic live entry, same choice
PR #2361 made for the same reason):

acceptance: direct `watchdog.diagnose_health()` call on a synthetic
`issue: None, task: "538"` entry — result:
```
[poll-report] adhoc/implementation/3426747: HEALTHY — ADHOC task="538" — adhoc/implementation/3426747: 최근 로그 성장, RUNNING
```

Live CLI repro 4 — normal spawn shows no change (empty-state
acceptance: byte-identical behavior, no new prompts):

acceptance: `python3 spawn.py implementation "normal real task text" --issue 2293 --dry-run; echo $?` — result:
```
{
  "sandbox": { "enabled": false, "network": { ... } },
  "decides": "승인된 범위 → 동작 코드 (신규 구현)",
  ...
}
0
```

acceptance: direct predicate calls for a real adhoc task text and an
issue-scoped numeric task text — result:
```
True
True
```
confirming a real task text (adhoc, no `--issue`) and a numeric task
text with `--issue` given both admit unaffected — the new check only
fires on the exact degenerate shape the issue names.
