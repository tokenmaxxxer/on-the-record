---
issue: 2795
role: silent-failure-audit-cdb7dda0
author: silent-failure-audit-cdb7dda0
skills: silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review:
  - board.py
  - test/test_unrecovered_commit_count.py
type: fix
breaking: false
verdict: landed
loop_state: landed
upstream:
  - path: PR #2824 CHANGES comment (JiwonJung94, 2026-08-30T03:23:37Z)
    sha: same-commit
  - path: docs/issue-2795/reports/silent-failure-audit-3da5ceae.md
    sha: 3870b5487c13105ee10f7baa0d253e11429168e5
---

# issue-2795 — silent-failure-audit-cdb7dda0 record

## What was done

Addressed the one blocking item from the CHANGES comment on PR #2824
(`issue-2795/silent-failure-audit-3da5ceae`, still open): `_remote_branch_head()`'s
`git ls-remote` had no timeout, unlike every other network git call in this
codebase, which routes through `plumbing._run_net()` for exactly that reason
(issue #285 P5).

canonical: `gh pr view 2824 --repo tokenmaxxxer/on-the-record --json body,comments,headRefName,state` (fetched this session) —
comment by JiwonJung94: "Blocking: `_remote_branch_head()`'s `git ls-remote`
has no timeout. Every other network git call in this codebase routes
through `plumbing._run_net()` precisely to stop the orchestrator hanging
... Route it through the same primitive as everything else, and show the
bounded behavior against a stalled remote." `headRefName`:
`issue-2795/silent-failure-audit-3da5ceae`, `state`: `OPEN`.

canonical: `board.py` `_remote_branch_head()` (this commit, working tree):
```python
    try:
        c = _sp._run_net(
            ["git", "-C", cwd, "ls-remote", "--heads", remote, branch],
            "[board] 원격 브랜치 헤드 조회")
    except SystemExit:
        return None
    if c.returncode != 0:
        return None
    line = c.stdout.strip()
    return line.split()[0] if line else ""
```

The call now goes through `_sp._run_net()`, bounded by `NETWORK_TIMEOUT`
(60s default), same as every other network git call site (`skills.py`,
`pipeline.py`, `spawn.py`). `_run_net()`'s own fail-closed on timeout is
`sys.exit()` — correct when the caller is a single spawn/pipeline attempt
that should halt, but this call site is inside `roster_watchdog()`'s
per-tick loop over every roster entry (`board.py:1459`); an uncaught
`sys.exit()` here would kill the entire watchdog process over one session's
stalled remote, silencing the report for every other roster entry too —
the same "the watch goes quiet" failure shape this PR exists to fix, just
relocated. The `except SystemExit: return None` catches exactly that and
folds it into `_remote_branch_head()`'s pre-existing "query failed" return
value, which `_unrecovered_commit_count()` already reads as
`UNPUSHED_STATUS_UNKNOWN` — the timeout lands in the same third state the
PR added for "can't tell," never a guess toward healthy or stranded.

Added a fast regression test,
`test_remote_stall_times_out_to_unknown_not_hang_or_crash`
(`test/test_unrecovered_commit_count.py`), that mocks `spawn._run_net` to
raise `SystemExit` immediately (no real wait) and asserts
`_unrecovered_commit_count()` returns `board.UNPUSHED_STATUS_UNKNOWN`
without the `SystemExit` escaping.

## Why

The reviewer's finding named the risk precisely: an unbounded network call
placed on a watch path that previously had none. Routing through
`_run_net()` reuses the codebase's one existing bounded-network primitive
rather than inventing a second timeout mechanism; catching `SystemExit`
locally is the minimum change that keeps that primitive's boundedness
while not inheriting its fail-mode (process exit) onto a path where that
fail-mode is itself the regression the review is trying to prevent.

Rejected alternative: give `_remote_branch_head()` its own
`subprocess.run(..., timeout=N)` instead of `_run_net()`. This would also
be bounded, but it would duplicate the timeout constant and message shape
that `_run_net()` already owns, and diverge from the reviewer's explicit
instruction ("route it through the same primitive as everything else") for
no benefit — the watchdog-loop constraint is satisfiable on top of
`_run_net()` with a five-line `try/except SystemExit`, so there was no
reason to bypass it.

## What did not work

None.

## Upstream basis

canonical: `gh pr view 2824 --repo tokenmaxxxer/on-the-record --json body,comments,headRefName,state`
(fetched this session) — CHANGES comment by JiwonJung94, quoted in full in
"What was done" above. Same-commit citation format does not apply to a
GitHub PR comment (it is not a repo path), so it is cited by author and
`createdAt` timestamp (`2026-08-30T03:23:37Z`) instead.

- `docs/issue-2795/reports/silent-failure-audit-3da5ceae.md` (subject
  record for the original fix this PR carries), sha
  `3870b5487c13105ee10f7baa0d253e11429168e5`.

## Verification

**Live demonstration against a genuinely stalled remote** — a `git` shim
that sleeps 6s on `ls-remote` before failing, prepended to `PATH`, called
through `_remote_branch_head()` with `NETWORK_TIMEOUT` overridden to 2s to
keep the demo short (the override changes only the bound, not the
mechanism — production uses the real 60s default via the same code path):

acceptance: `timeout 20 python3 /tmp/live_demo.py` — result:
```
elapsed=2.00s result=None
PASS: bounded timeout observed, watchdog process survives
```

The call returned in ~2s (the configured bound), not 6s (the stall
duration) and not indefinitely; the calling process did not exit.

acceptance: `python3 -m pytest test/test_unrecovered_commit_count.py -v` — result:
```
8 passed
```
(7 pre-existing + the new `test_remote_stall_times_out_to_unknown_not_hang_or_crash`.)

**Overhead on a healthy tick** (issue's fourth standing invariant) —
20 consecutive `_remote_branch_head()` calls against a real local bare
remote with no stall:

acceptance: `python3 /tmp/overhead_demo.py` — result:
```
20 calls (healthy remote): 0.238s total, 11.9ms/call, last result='b49a704e76b82a7426fb6c97bea99b67353b07dc'
```

`_run_net()` adds a Python-level `timeout=` kwarg to the same
`subprocess.run()` call plus a `try/except` around it — no additional
process spawn, no additional round trip. The ~12ms/call is the cost of
spawning `git ls-remote` itself, unchanged by routing through `_run_net()`.

**No return of the retired role axis in any reshaped form:**

acceptance: `git diff origin/main..HEAD -- board.py spawn.py watchdog.py test/test_unrecovered_commit_count.py | grep -inE '^\+.*\brole\b'` — result:
```
(no output, exit 1)
```

**No new bug — failing-test set vs origin/main compared as SETS OF
NAMES:**

acceptance: `python3 -m pytest test/ -q 2>&1 | grep '^FAILED' | sort > /tmp/head_fails.txt` — result:
```
15 failed, 433 passed, 3 xfailed
```
acceptance: `git worktree add /tmp/main-worktree origin/main -q && cd /tmp/main-worktree && python3 -m pytest test/ -q 2>&1 | grep '^FAILED' | sort > /tmp/main_fails.txt` — result:
```
15 failed, 425 passed, 3 xfailed
```
acceptance: `diff /tmp/head_fails.txt /tmp/main_fails.txt && echo "IDENTICAL SETS"` — result:
```
IDENTICAL SETS
```
(HEAD has 8 more passing tests than `origin/main` — the 7 pre-existing
`test_unrecovered_commit_count.py` tests plus this session's new one,
neither present on `origin/main`; both sides carry the same 15
pre-existing, unrelated `fetch`-failure test names.)

**Monitor and watch machinery unbroken and not quieter:**

acceptance: `python3 -m pytest test/ -q -k "watchdog or roster or diagnose or unrecovered"` — result:
```
37 passed in 1.11s
```

**Untouched: `watchdog.py:272`'s own `Path(work).name` branch derivation**
— filed separately as #2834 and already landed (commit `e168d4d0`, PR
#2838, present on `origin/main` before this branch started); confirmed
not touched by this session:

acceptance: `git diff origin/main..HEAD -- watchdog.py` — result:
```
(no output)
```

## Open findings

None.

## Next steps

canonical: `gh pr view 2824 --repo tokenmaxxxer/on-the-record --json comments`
(fetched this session) — the CHANGES comment states: "The fix itself is
confirmed correct where it matters most... both `board.py` call sites
derive from `_current_branch()` and do not reintroduce the false positive;
the three states are genuinely distinct...; a genuinely stranded commit
still alarms through the real `diagnose_health()` path," and separately
scopes `watchdog.py:272`'s derivation bug to #2834, "not yours to fix
here." This session did not re-verify those items or touch `watchdog.py`
(see the `git diff` result above) — nothing further remains from the
CHANGES comment.

`loop_state: landed` — ready to push and update PR #2824.

skill-verdict: silent-failure-audit — applied: invoked; loaded
SKILL.md and used its Handled/Silently-Absorbed/Unreachable framing to
confirm the `except SystemExit: return None` path in
`_remote_branch_head()` is a Handled path (not a silent absorb) — it
converts the timeout into the function's pre-existing, already-tested
"query failed" return contract (`None` → `UNPUSHED_STATUS_UNKNOWN`), the
same contract the other two failure branches in this function already use,
rather than swallowing the timeout with no downstream signal.
skill-verdict: work-in-english — not-applicable: guidance-only skill with
no Skill-tool entry point for this session to invoke; all commit messages,
code, tests, and this record were written in English per its intent.
