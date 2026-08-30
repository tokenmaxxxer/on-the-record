---
issue: 2795
role: adversarial-review-a1341cc3
author: adversarial-review-a1341cc3
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2824's deliverable
loop_state: landed
upstream:
  - path: docs/issue-2795/reports/silent-failure-audit-3da5ceae.md
    sha: 23a0d7d5c3956b4f7e56af70e29909f991e8f423
---

# issue-2795 — adversarial-review-a1341cc3 record

## What was done

canonical: gh pr view 2824 (branch issue-2795/silent-failure-audit-3da5ceae,
tip 23a0d7d5c3956b4f7e56af70e29909f991e8f423, base origin/main), read live
this session for title/body/commits/files. Independently re-derived PR
#2824's acceptance checks and standing invariants from fresh `git
worktree`s of both the PR tip and `origin/main`, rather than trusting the
subject record's quoted numbers.

**1. Branch derivation (the way this fix most easily breaks).**
canonical: `git diff origin/main..HEAD -- board.py` on the PR-tip worktree
shows both call sites (`roster_ps()`, `roster_watchdog()`) now pass
`_sp._current_branch(Path(work))` into `_unrecovered_commit_count()`, not
`Path(work).name`. `_current_branch()` (`board.py:53`) runs `git
symbolic-ref --short HEAD` — the real checked-out ref, immune to the
directory-naming convention.

derived: constructed the exact failure this would reintroduce — a
workspace directory named `on-the-record-issue-1111-wrongname` whose real
branch is `issue-2795/adversarial-review-a1341cc3`, two commits, both
pushed:
```
BROKEN derivation branch guess: on-the-record-issue-1111-wrongname
BROKEN derivation result (would reintroduce false positive): 1
REAL derived branch via _current_branch(): issue-2795/adversarial-review-a1341cc3
FIXED result using real branch (all pushed, should be 0): 0
```
Confirms: had either call site used `Path(work).name` instead, `ls-remote`
would query a branch that doesn't exist, `_remote_branch_head()` would
return `""` (branch absent from remote), and the two already-pushed
commits would be reported as unpushed — the exact false positive #2795
exists to kill, reintroduced by a different route. Both call sites avoid
this.

**2. Three genuinely distinct states, forced side by side.**
derived: same fixture (dash-dir-name vs slash-branch, matching this
repo's real `issue_workspace()` convention), three states forced in
sequence:
```
STATE A (genuinely absent, not pushed): 1
STATE B (now pushed, present on remote): 0
STATE C (remote unreachable):            unknown | type: str

Distinctness check:
  A != B: True
  A != C: True
  B != C: True
  C is not int (never collapses into 0 or a count): True
```
State C (`UNPUSHED_STATUS_UNKNOWN`) is a string sentinel — it can never be
mistaken for `0` (healthy) or a positive int (stranded) by a caller that
does `if commit_count:` truthiness, which is exactly how `diagnose_health()`
branches (`watchdog.py:301` checks `== UNPUSHED_STATUS_UNKNOWN` explicitly,
*before* the `if commit_count:` truthiness check at `watchdog.py:328`,
canonical: read both lines directly on the PR-tip worktree) — this is the
#2792 shape (success-flag-paired-with-absent-data) correctly avoided, not
repeated.

acceptance: reproduction of the issue's third named check ("the command
the detector runs, and its output in a workspace with no upstream
configured") — result:
```
$ git -C <ws> log '@{u}..HEAD'   (OLD check's implied comparison)
exit: 128
stderr: fatal: 'issue-9500/noupstream' 브랜치에 대해 업스트림을 설정하지 않았습니다

$ git -C <ws> ls-remote --heads origin issue-9500/noupstream   (NEW detector's actual command)
exit: 0
stdout: ''
stderr: ''
```
The old comparison's implied `@{u}..HEAD` hard-errors on a workspace that
never configured a tracking ref — precisely the "no upstream" == "not
pushed" conflation the issue names. The new detector's actual command
(`git ls-remote --heads origin <branch>`) succeeds unconditionally and
returns empty stdout for a branch genuinely absent from the remote, which
`_remote_branch_head()` (`board.py:1027` on the PR-tip worktree) correctly
reads as `""`, distinct from `None` (query failure).

**3. The direction that matters most: true positive still alarms.**
acceptance: crashed-session fixture, one commit made, never pushed, run
through the real `diagnose_health()` entry point (not just
`_unrecovered_commit_count()` in isolation) — result:
```
TRUE POSITIVE (crashed with stranded commit) -- must still alarm:
  commit_count: 1
  state: DEAD-UNRECOVERED-COMMITS
  detail: issue-4242/livedemo: pid 999999998 부재, PR 없음, branch=on-the-record-issue-4242-livedemo 에 push 안 된 커밋 1개 — 복구 필요 (session_verdict='crashed')
  -> confirmed: true positive still fires, not silenced.
```
Confirmed: the fix for the false positive does not quiet the true
positive. (Note the `branch=` text in that detail line reads the
*workspace directory name*, not the real branch — see Open findings
below; it does not affect this state determination, only the displayed
text.)

**4. Standing invariants, independently re-run.**

acceptance: no return of the retired role axis —
`git diff origin/main..HEAD -- board.py spawn.py watchdog.py
test/test_unrecovered_commit_count.py | grep -inE '^\+.*\brole\b'` on the
PR-tip worktree — result: no output, exit 1. Zero matches, independently
re-run.

acceptance: no new bug, failing-test set vs `origin/main` as SETS OF
NAMES — `python3 -m pytest test/ -q` on a fresh `origin/main` worktree
(`ce1e0b47`) and on the PR-tip worktree (`23a0d7d5`) — result:
```
origin/main:  15 failed, 425 passed, 3 xfailed in 31.89s
PR tip:       15 failed, 432 passed, 3 xfailed in 31.93s
```
derived: `diff <(grep '^FAILED' main-run | sort) <(grep '^FAILED' pr-run |
sort)` — result: empty diff, both files 15 lines, identical `FAILED` test
IDs. 432 vs 425 passed is exactly the 7 new tests added by this PR (all 7
independently re-run here too, `0.91s`, all pass). No regression in the
shared set.

No overhead increase / hang risk — **this is where independent
verification surfaces a real gap** (full reproduction in Open findings,
finding 1): the subject record measured `subprocess.run` call-count
parity only ("same two calls, one now goes to the network") and never
measured latency under a stalled remote, despite the task explicitly
asking to "say whether a slow or hanging remote can stall the tick." Live
reproduction below shows it can, unboundedly.

acceptance: monitor/watch machinery unbroken and NOT QUIETER — read
`watchdog.py:1696-1697` (`roster_watchdog`'s dead-entry branch) and
`board.py:1464-1465` (`roster_ps`'s dead-entry branch) directly on the
PR-tip worktree — result: `watchdog.py` prints `[poll-report] {key}:
{dead_label} — {detail}` unconditionally for any non-`None` state,
including the new `DEAD-REMOTE-STATE-UNKNOWN`; `board.py` prints for any
state not in `(None, "DEAD-ERRORED")`, which also covers the new state.
Neither path drops or demotes any state. The full-suite comparison above
(432 passed vs 425, 0 lost) confirms no test coverage was quieted either.

## Why

canonical: gh pr view 2824 / gh issue view 2795, read live this session.
The task was to independently verify a PR's claims, not restate them — so
every acceptance command and standing invariant above was re-run from a
fresh `git worktree` of both the PR tip and `origin/main`, and two
fixtures were built from scratch (not copied from the subject record's
fixtures) to force each of the three states and the branch-mismatch
failure mode. Two things surfaced that the subject record either didn't
fully investigate or flagged as speculative, and independent verification
exists precisely to run those down rather than pass them through:

1. The overhead/hang-risk invariant was answered incompletely by the
   subject record. The task brief explicitly asked to "measure what it
   costs and say whether a slow or hanging remote can stall the tick" —
   the subject record measured cost (call count) but not hang risk. Given
   `_remote_branch_head()` runs a genuine network operation (`git
   ls-remote` against `origin`, which in production is a remote host, not
   a local bare repo) synchronously inside the roster poll tick, hang
   risk is the more consequential half of that question and was worth
   checking directly rather than assuming call-count parity implies
   bounded latency — confirmed live in Open findings finding 1 below.

2. derived: read the subject record's own Open findings section — path
   docs/issue-2795/reports/silent-failure-audit-3da5ceae.md (untracked in
   this record's own working tree; it lives on PR #2824's branch, not
   yet merged to this branch) at commit 23a0d7d5, lines 350-361,
   retrieved via `git show 23a0d7d5:docs/issue-2795/reports/silent-failure-audit-3da5ceae.md`.
   It already names the `diagnose_health()` stale-branch issue but marks
   it "unverified... a plausible separate issue, not undertaken here."
   Independent verification's job is exactly to either confirm or refute
   a hedge like that rather than pass it through unexamined — so it was
   reproduced live in Open findings finding 2 below rather than left as
   "plausible."

## What did not work

None — both investigations (hang-risk reproduction, PR-lookup
misdiagnosis reproduction) succeeded in confirming a real defect on the
first construction; no dead ends to record.

## Upstream basis

- The subject record — path docs/issue-2795/reports/silent-failure-audit-3da5ceae.md,
  untracked in this record's own working tree (it lives on PR #2824's
  branch, tip commit 23a0d7d5c3956b4f7e56af70e29909f991e8f423, not yet
  merged to this branch), retrieved via `git show
  23a0d7d5:docs/issue-2795/reports/silent-failure-audit-3da5ceae.md` — read
  for its claimed commands/results; every acceptance check and standing
  invariant it claims was independently re-run above rather than copied,
  and its own Open findings section is what finding 2 below re-derives
  from speculative to confirmed.
- canonical: `gh pr view 2824`, read live this session, for the PR's
  title/body/commits/files/state.
- `git worktree add /tmp/pr2824-check FETCH_HEAD` (PR tip, fetched via
  `git fetch origin issue-2795/silent-failure-audit-3da5ceae`) and `git
  worktree add /tmp/pr2824-main origin/main` — both removed (`git
  worktree remove --force`) after use.

## Open findings

1. **`_remote_branch_head()` (`board.py:1027` on the PR-tip worktree) has
   no timeout on its network `git ls-remote` call, unlike every other
   network git call in this codebase.** canonical: `board.py:1038-1041`
   on the PR-tip worktree —
   ```python
   c = subprocess.run(
       ["git", "-C", cwd, "ls-remote", "--heads", remote, branch],
       capture_output=True, text=True,
   )
   ```
   no `timeout=` kwarg. canonical: `plumbing.py:41-49` — this codebase
   has an established convention, `_run_net()`, that forces a `timeout=`
   on every network git subprocess call specifically because a bare
   `subprocess.run` on one can hang the orchestrator indefinitely (its
   own docstring: "`TimeoutExpired`가 그냥 새 나가면 오케스트레이터가
   무기한 걸린다(이슈 #285 P5)"). `_remote_branch_head()` calls raw
   `subprocess.run` instead of `_sp._run_net`/`plumbing._run_net`,
   bypassing that convention on a genuinely new network call site added
   by this PR.

   derived: live reproduction with a stalling fake remote (`git -c
   protocol.ext.allow=always ls-remote --heads
   "ext::/tmp/slow_upload_pack.sh"`, the script sleeps 6s then exits 1),
   driven through the real `board._remote_branch_head()` function on the
   PR-tip worktree — result:
   ```
   _remote_branch_head() call took 6.0s against a 6s-stalling fake remote
   result: None
   ```
   The call waited out the full 6s stall with no internal bound. In
   production, a stalled TCP connection to a real remote (partial
   connect, congested link, DNS hang) commonly blocks far longer than 6s
   before the OS-level TCP timeout fires — this call is invoked
   synchronously inside both `roster_ps()` and `roster_watchdog()`'s
   dead-entry diagnosis path. canonical: `board.py:1429` and the
   `roster_watchdog` equivalent, read directly — confirmed limited to
   `not alive` entries only, not every healthy tick, so blast radius is
   scoped to sessions already flagged dead, not the whole poll loop every
   tick — but a single hung dead-entry diagnosis still stalls that tick
   for as long as the remote stays unresponsive, with no bound.
   Verdict: CONFIRMED — reproduced live against the actual function, not
   inferred. Resolution path: route `_remote_branch_head()`'s
   `ls-remote` through `plumbing._run_net()` (or an equivalent explicit
   `timeout=`), the same pattern this codebase already uses for every
   other network git call — not undertaken here, per adversarial-review's
   scope (report, not fix).

2. **`diagnose_health()`'s own internal `branch = Path(work).name if
   work else None` (`watchdog.py:272` on the PR-tip worktree, unchanged
   by this PR) feeds PR-completion lookup with the same broken
   directory-name-as-branch derivation this PR fixed at its two
   `board.py` call sites — but this third site was left as-is, and it is
   reachable in the common case.** derived: the subject record's own
   Open findings section (path docs/issue-2795/reports/silent-failure-audit-3da5ceae.md,
   untracked in this record's own working tree — see Upstream basis
   above — retrieved via `git show
   23a0d7d5:docs/issue-2795/reports/silent-failure-audit-3da5ceae.md`,
   lines 350-361) names this exact line and hedges: "Whether the
   PR-lookup path is actually affected in production... is
   unverified... out of #2795's scope." Independent verification's job
   is to check that hedge, not repeat it.

   derived: live reproduction — a completed session (real workspace,
   real commits, real branch `issue-7777/completed`) with an OPEN PR
   correctly present in `pr_index`, keyed by the real branch name
   (exactly how `gates/closure_sweep.py`'s `_pr_index_all()` keys it, per
   the subject record's own citation) — result:
   ```
   Workspace dir name: on-the-record-issue-7777-completed
   Real branch: issue-7777/completed
   diagnose_health()'s internal `branch` (Path(work).name): on-the-record-issue-7777-completed
   pr_index keys: ['issue-7777/completed']

   Result state: DEAD-ERRORED
   Result detail: issue-7777/completed: pid 999999997 부재, PR 없음, 커밋 없음, session_verdict='crashed'
   ```
   `diagnose_health()` was called with `pr_index={real_branch: {"number":
   4242, "state": "OPEN"}}` — the PR genuinely exists and is open — but
   `diagnose_health()`'s internal lookup uses `branch =
   Path(work).name` (`watchdog.py:272`) to key into that same dict,
   misses it (`"on-the-record-issue-7777-completed"` is not a key), falls
   through the `pr_number is not None` completion check, and reaches
   `DEAD-ERRORED` — misdiagnosing a completed, PR-open session as needing
   recovery. `Path(work).name` vs the real branch is exactly this repo's
   standard `issue_workspace()` naming convention (dashes vs slash,
   confirmed by the subject record's own citation of
   `spawn.py::_workspace_target_path()`), so this is not an edge case —
   it is the common-case naming shape, reachable any time
   `diagnose_health()` is called with an explicit `pr_index` dict (the
   bulk-lookup path both `board.py` call sites use) rather than falling
   back to per-branch `gh` calls.
   Verdict: CONFIRMED (upgraded from the subject record's "unverified,
   plausible") — this is a real, live-reproduced misdiagnosis, not
   speculative. It predates PR #2824 (the line is untouched by this
   diff, confirmed via `git diff origin/main..HEAD -- watchdog.py` on the
   PR-tip worktree showing no hunk touching that line), and sits outside
   #2795's stated acceptance (which is about the unpushed-commit count,
   not PR-completion lookup), so it is not a regression this PR
   introduces — but it is a live defect directly adjacent to, and
   undermining confidence in, the completion-detection this fix's own
   new states are gated behind. Resolution path: a follow-up issue
   applying the same `_current_branch()` fix to `watchdog.py:272`, not
   this PR's scope.

## Next steps

derived: every acceptance command and standing invariant claimed by PR
#2824 was independently re-run this session against fresh worktrees of
both the PR tip and `origin/main` (not copied from the subject record),
and all of them corroborate the PR's claims: branch derivation holds at
both call sites (mismatch reproduction confirms this), the three states
are genuinely distinct and never collapse, the true positive still fires,
zero role-axis reintroduction, and an identical 15-name failing-test set
vs `origin/main`. `loop_state` is `landed` — no further action needed on
this record; both open findings above are fully derived and CONFIRMED,
with resolution paths named but not undertaken here (adversarial-review's
scope is verification/report, not fix). PR #2824's three named acceptance
checks and its "must not" (true positive preserved) all independently
reproduced clean. Of its four standing invariants, three (role-axis,
failing-test-set, monitor/watch-not-quieter) reproduce clean; the fourth
(no overhead increase) is only partially satisfied — call-count parity
holds, but the hang-risk half of that invariant, which the task brief
named explicitly, does not, per Open findings finding 1 above.

skill-verdict: adversarial-review — applied: invoked; loaded the skill's
SKILL.md before treating PR #2824's own record as anything other than a
claim to re-derive. Every acceptance number and invariant above was
produced by a fresh command run this session against real worktrees, not
copied from the subject record, and two investigations went beyond the
subject record's own coverage: the hang-risk half of the overhead
invariant (subject record measured call count only) and the
`diagnose_health()` stale-branch defect (subject record marked it
"unverified"; here it is reproduced live and CONFIRMED).
skill-verdict: work-in-english — applied: invoked; wrote this record and
the commit message/PR title/body in English per the skill; only the final
user-facing summary is in Korean.
