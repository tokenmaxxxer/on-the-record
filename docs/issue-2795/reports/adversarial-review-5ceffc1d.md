---
issue: 2795
role: adversarial-review-5ceffc1d
author: adversarial-review-5ceffc1d
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review:
  - board.py
  - watchdog.py
  - spawn.py
  - ffb4aabb:test/test_unrecovered_commit_count.py
type: review
breaking: false
verdict: no-blocking-findings
loop_state: landed
upstream:
  - path: PR #2843 (tokenmaxxxer/on-the-record, headRefName issue-2795/silent-failure-audit-cdb7dda0)
    sha: ffb4aabbaa9ce35ae17e15d6c08503d2ee01b584
---

# issue-2795 — adversarial-review-5ceffc1d record

## What was done

Independent, round-2 adversarial review of PR #2843 (supersedes closed PR
#2824; carries that work plus a timeout fix for `_remote_branch_head()`'s
`git ls-remote`). Re-derived every claim live against a checked-out copy of
the PR branch (`ffb4aabb`) and a separate worktree of `origin/main`
(`81a628df`) rather than trusting either the delivery's record or #2824's
own prior verification. No blocking findings; one pre-existing, out-of-scope
cosmetic finding noted below.

canonical: `gh pr view 2843 --repo tokenmaxxxer/on-the-record --json headRefName,baseRefName,commits,files` (fetched this session) — headRefName
`issue-2795/silent-failure-audit-cdb7dda0`, 5 commits, HEAD
`ffb4aabbaa9ce35ae17e15d6c08503d2ee01b584`, files touched: `board.py`,
`spawn.py`, `watchdog.py`, plus the delivery's own records and a new test
file.

**1. The timeout fold — constructed live, not read from the diff.**
`board._remote_branch_head()` now routes its `git ls-remote --heads`
through `_sp._run_net()` and catches `SystemExit` (`_run_net()`'s own
fail-closed on `TimeoutExpired`), folding a timeout into the function's
existing "query failed" `None` return, which `_unrecovered_commit_count()`
maps to `UNPUSHED_STATUS_UNKNOWN`.

Constructed both failure shapes against the real, unmodified functions
(only `plumbing._run_net.__defaults__` was shrunk from `(60,)` to `(3,)` to
keep the stall bounded to 3s of real wall-clock instead of the production
60s — the function under test was not mocked):

- Remote that **stalls past the bound** (`git://10.255.255.1/repo.git`,
  a non-routable/black-holed address — real TCP-level silence, not a
  simulated exception): `subprocess.run(timeout=3)` raised
  `TimeoutExpired` at 3.0s, `_run_net()` converted it to `sys.exit()`,
  `_remote_branch_head()`'s `except SystemExit: return None` caught it —
  the calling process **did not exit**. Result: `_unrecovered_commit_count()`
  returned `'unknown'` (`board.UNPUSHED_STATUS_UNKNOWN`) at 3.0s elapsed.
  derived: `python3 /tmp/pr2843review/../timeout_repro.py` (this session,
  against the real `board._remote_branch_head`/`plumbing._run_net`, only
  the timeout default patched) — result:
  ```
  === CASE 1: remote stalls past bound (non-routable IP, real subprocess timeout) ===
  elapsed=3.0s result='unknown' (process survived, no sys.exit propagated)
  ```
- Remote that is **unreachable** (`git://127.0.0.1:1/repo.git`, connection
  refused immediately — the fast-fail shape, distinct from the stall
  above): same outcome, `'unknown'`, at 0.0s (`returncode != 0` path, never
  reaches the timeout branch at all).
  derived: same script, result:
  ```
  === CASE 2: remote unreachable, fails fast (connection refused) ===
  elapsed=0.0s result='unknown' (process survived, no sys.exit propagated)
  ```

Both are what the code *does*, not what the delivery's record claims it
does: the process survives a real stalled remote inside the exact call
path `roster_watchdog()`'s per-tick loop uses (`board._unrecovered_commit_count`
→ `board._remote_branch_head` → `_sp._run_net`), and the per-entry loops in
both `roster_ps()` (`ffb4aabb:board.py:1447`) and `roster_watchdog()`
continue to the next roster entry instead of dying — confirmed by reading
that neither loop wraps this call in a broader `except SystemExit`, so the
catch has to happen exactly where the delivery placed it (inside
`_remote_branch_head()` itself) or the process really would die; it does
not.

**2. The timeout result is genuinely the third state, not a guessed
healthy/stranded.** `UNPUSHED_STATUS_UNKNOWN` (`'unknown'`, a `str`) is
type- and value-distinct from `0` (healthy, no alarm) and any positive
`int` (stranded count) — `_unrecovered_commit_count()` cannot return it by
accident through the same code path as either of those. `diagnose_health()`
branches on it explicitly *before* the `if commit_count:` truthy check that
would otherwise catch it (a bare `if commit_count:` on the string
`'unknown'` is truthy, so the ordering matters and is correct — the
`commit_count == _sp.UNPUSHED_STATUS_UNKNOWN` branch is checked first).
Verified live with my own constructed workspaces (see acceptance checks
below): the timeout/unreachable case never produced `DEAD-ERRORED` or
`DEAD-UNRECOVERED-COMMITS`, only `DEAD-REMOTE-STATE-UNKNOWN`.

**3. Branch derivation (re-derived, not trusted from #2824's own
verification).** Both `ffb4aabb:board.py:1476` (`roster_ps()`) and
`ffb4aabb:watchdog.py:1675` (`roster_watchdog()`) pass
`_sp._current_branch(Path(work))` — a real `git symbolic-ref --short HEAD`
— to `_unrecovered_commit_count()`, not `Path(work).name`. Constructed my
own directory/branch mismatch (workspace dir `on-the-record-issue-8123-rev`,
real branch `issue-8123/rev`, different strings) and drove it through the
*real* `_unrecovered_commit_count()` + `diagnose_health()` — see acceptance
check 1 below; the `ls-remote` query correctly resolved against the real
branch, not the directory's basename.

**4. Three states genuinely distinct, and a real stranded commit alarms
through the real `diagnose_health()` path.** Constructed two independent
workspaces (issue 8123 = pushed-clean, issue 8124 = genuinely-unpushed,
different naming from the shipped test file) and drove both through
`board._unrecovered_commit_count()` → `watchdog.diagnose_health()` with no
mocking:

derived: `python3 /tmp/pr2843review/final_repro.py` (this session, real
`board`/`watchdog`/`spawn` modules from the `ffb4aabb` checkout, no
mocking) — result:
```
=== ACCEPTANCE CHECK 1: crash AFTER a successful push -> no DEAD-UNRECOVERED-COMMITS ===
workspace dir name='on-the-record-issue-8123-rev'  real branch='issue-8123/rev'
commit_count=0  health.state='DEAD-ERRORED'
[poll-report] issue-8123/rev - DEAD-ERRORED - issue-8123/rev: pid 888800001 부재, PR 없음, 커밋 없음, session_verdict='crashed'

=== ACCEPTANCE CHECK 2: crash AFTER commit, BEFORE push -> still alarms ===
commit_count=1  health.state='DEAD-UNRECOVERED-COMMITS'
[poll-report] issue-8124/rev - DEAD-UNRECOVERED-COMMITS - issue-8124/rev: pid 888800001 부재, PR 없음, branch=on-the-record-issue-8124-rev 에 push 안 된 커밋 1개 — 복구 필요 (session_verdict='crashed')
```
Acceptance check 3 (the detector's command, no-upstream workspace) also
reproduced directly in the same run:
```
git rev-parse @{u} on this workspace: returncode= 128 stderr= fatal: 'issue-8125/no-upstream-yet' 브랜치에 대해 업스트림을 설정하지 않았습니다
NEW detector command: git -C <work> ls-remote --heads origin issue-8125/no-upstream-yet
output: returncode= 0 stdout= ''
```
This is the exact bug the issue describes (old detector's `@{u}` blind, new
detector's `ls-remote` sees the truth) reproduced against the current
`_remote_branch_head()` implementation, not against the pre-fix code.

**5. Overhead — measured, not argued by placement.** The only two
production call sites (`ffb4aabb:board.py:1476`, `ffb4aabb:watchdog.py:1675`)
both sit inside `if not _sp._alive(pid):` branches — confirmed by reading
the surrounding loop structure in both files, and cross-checked there are
no other call sites.
derived: `grep -rn "_unrecovered_commit_count\|_remote_branch_head" --include="*.py" . | grep -v "^./test/"` (this
session, in the `ffb4aabb` checkout) — result: only definitions/docstrings
plus the two `_sp.` call sites above; no third production call site exists.

A tick where every roster entry is alive invokes `_remote_branch_head()`
**zero times** — no network call is added to that path at all, so there is
nothing to attribute overhead to on a genuinely healthy tick. Separately
measured the delta the PR's own change (routing through `_run_net()`
instead of a bare `subprocess.run()`) adds *when the call does fire* (dead
entry, reachable remote, N=200 calls, `timeit`, this session):
derived: `python3 /tmp/pr2843review/overhead_measure.py` — result:
```
bare subprocess.run (old, pre-#2843): 7.671 ms/call
_run_net-wrapped   (new, #2843):      6.809 ms/call
delta: -0.8622 ms/call, -11.24% relative
```
Negative/noise-level — the `_run_net()` wrapper (a `try/except` and two
`kwargs.setdefault` calls around the same `subprocess.run`) adds no
measurable cost. Unlike #2834 (placement argued but 3 of 4 sites were
actually on the hot path), here the placement claim holds up under direct
inspection of the loop guards, not just an assertion about intent.

**6. Four standing invariants — each re-derived with a command + output.**

- No return of the retired role axis in any reshaped form:
  derived: `git diff origin/main..HEAD -- board.py spawn.py watchdog.py
  test/test_unrecovered_commit_count.py | grep -inE '^\+.*\brole\b'` (this
  session, `ffb4aabb` checkout against `origin/main`) — result:
  ```
  (no output, exit 1)
  ```
- No new bug — failing-test set vs `origin/main`, compared as **sets of
  names**, not counts. derived: `python3 -m pytest -q` run separately in
  the `ffb4aabb` worktree and in a fresh `origin/main` (`81a628df`)
  worktree, this session — result:
  ```
  main:  16 failed, 572 passed, 3 xfailed in 32.78s
  PR:    16 failed, 580 passed, 3 xfailed in 32.69s   (+8 = PR's own new test file)
  ```
  derived: `diff <(pytest -q 2>&1 | grep '^FAILED' | sort)` between the two
  worktrees — result: no output — IDENTICAL SETS, same 16 test names on
  both sides (pre-existing, environment-dependent failures unrelated to
  this change; none newly introduced, none newly fixed).
  The PR's own 8 new tests pass: derived: `python3 -m pytest
  ffb4aabb:test/test_unrecovered_commit_count.py -v` — result: `8 passed in
  0.94s`.
- No overhead increase, measured: see point 5 above (-0.86ms/call, and zero
  calls on a fully-healthy tick).
- Monitor and watch machinery unbroken and **not quieter**: pass count
  went from 572 to 580 (the 8 new tests), zero new skips (`0 skipped` both
  sides per the same `pytest -q` runs above), and the constructed scenarios
  in point 4 show `[poll-report]` lines printing for all three terminal
  states (`DEAD-ERRORED`, `DEAD-UNRECOVERED-COMMITS`, and —
  `DEAD-REMOTE-STATE-UNKNOWN` via my own timeout construction in point 1
  routed through `diagnose_health()`) — none of the three states is
  silently swallowed.

## Why

The prior review round confirmed the remote-aware branch-derivation fix on
PR #2824; this round's only new code is the timeout bound on
`_remote_branch_head()` added on top in PR #2843. canonical: `gh pr view
2824 --repo tokenmaxxxer/on-the-record --json state,headRefName` (fetched
this session) — `state`: `CLOSED`, `headRefName`:
`issue-2795/silent-failure-audit-3da5ceae`, superseded by #2843 per the
task brief; #2824's branch-derivation logic is carried into #2843
byte-for-byte and independently re-verified here (point 3 above), not
merely cited from #2824's own record. The highest-risk failure mode named
in the review brief — `_run_net()`'s `sys.exit()` fail-closed escaping into
`roster_watchdog()`'s polling loop and silently killing monitoring for the
whole roster over one stalled remote — is exactly the kind of defect that
only shows up under a *real* timeout, not a mocked one, so I constructed
real stalls (non-routable IP) and real fast-fails (connection refused)
against the unmodified production functions (point 1 above) rather than
trusting the shipped test's `mock.patch.object(spawn, "_run_net", ...)`
unit test, which correctly tests the fold-to-unknown logic but not whether
`_run_net()` itself, unmocked, actually raises somewhere the `except
SystemExit` doesn't reach.

## What did not work

None.

## Upstream basis

- PR #2843 (tokenmaxxxer/on-the-record), branch
  `issue-2795/silent-failure-audit-cdb7dda0`, HEAD
  `ffb4aabbaa9ce35ae17e15d6c08503d2ee01b584` — read via `gh pr view/diff
  2843` and a local checkout (`git fetch origin pull/2843/head` + `git
  worktree add`).
- `origin/main` at `81a628df4bdcb8b00524c418f17c4f6063654c65` — separate
  worktree, used as the comparison baseline for the failing-test-set and
  overhead measurements.

## Open findings

1. **Minor, pre-existing, out of scope for this PR.**
   `watchdog.diagnose_health()`'s `branch = Path(work).name if work else
   None` is used only for the human-readable `detail` string's
   `branch=...` field, not for the `_unrecovered_commit_count()` query
   itself (that correctly receives `_current_branch()` from both call
   sites, per point 3 above).
   derived: `git diff origin/main..HEAD -- watchdog.py` (this session,
   `ffb4aabb` checkout) — result: the `branch = Path(work).name ...` line
   at `ffb4aabb:watchdog.py:266` does not appear inside any `+`/`-` hunk in
   this diff; only the `commit_count` docstring and the new
   `DEAD-REMOTE-STATE-UNKNOWN` branch below it changed.
   Effect: a printed `DEAD-UNRECOVERED-COMMITS`/`DEAD-REMOTE-STATE-UNKNOWN`
   line can show the workspace's directory name instead of the real branch
   to an operator reading `[poll-report]` output — reproduced live in
   acceptance check 2 above (`branch=on-the-record-issue-8124-rev`
   printed, real branch was `issue-8124/rev`). Cosmetic only — does not
   affect which state fires or whether the alarm is correct — and predates
   both #2824 and #2843, so not a blocking finding on this PR. Worth its
   own follow-up issue if the printed detail text is meant to be
   operator-actionable as-is.

## Next steps

None — review complete. canonical: this record's point 6 above (all four
standing invariants re-derived this session with commands and pasted
output: role-axis grep, failing-test-set diff, overhead `timeit` measurement,
and the poll-report constructions) is the execution-live basis for this
verdict — no blocking findings survived independent re-derivation. The
cosmetic branch-display finding above is a candidate for a small separate
issue, not a required follow-up on #2795/#2843. `loop_state: landed`.

skill-verdict: adversarial-review — applied: invoked; this record is a full
adversarial-review pass on PR #2843 per the skill's protocol (independent
re-derivation of every claim, no shared context with the delivery session)
other mounted skills: not triggered
