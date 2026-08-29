---
issue: 2742
role: adversarial-review-0598f25e
author: adversarial-review-0598f25e
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # this record is an independent verification of PR #2782's deliverable
loop_state: done
upstream:
  - path: PR #2782 (tokenmaxxxer/on-the-record), branch issue-2742/distinguish-caller-departed-spawn
    sha: 26f09b170095d7b5638554b51ab42df239557e4b
---

# issue-2742 — adversarial-review-0598f25e record

## What was done

canonical: `gh pr view 2782` output (state: OPEN, Closes #2742) and `git diff origin/main...pr-2782-review -- spawn.py` (read in full, both call sites and the handler)

Independent verification of PR #2782 (issue #2742: distinguish a caller-departed
spawn from a genuine crash). Fetched the PR branch into a worktree
(`git worktree add /tmp/pr2782-wt pr-2782-review`, HEAD
`26f09b170095d7b5638554b51ab42df239557e4b`), read the actual `spawn.py` diff,
and re-derived every claim with real forked processes and real signals — no
mocks for the signal-delivery paths. Found two real defects in the arm/disarm
boundary that PR #2782's own test file (name: test_bootstrap_signal_guard.py,
untracked in this checkout — it exists only on the PR branch at PR HEAD
`26f09b17`, so it is deliberately not cited as a backtick path below) did not
cover; everything else in the PR's claim set checked out.

**Finding 1 (high severity, confirmed) — signal landing between the
session-log record and the disarm call deletes an already-established, real
session workspace.**

canonical: `git diff origin/main -- spawn.py` (PR worktree) — `_record_spawn_outcome(attempt_id, "session-log", str(log_path))` at spawn.py:4069, followed only on the next statement by `_disarm_bootstrap_signal_guard(_bootstrap_signal_guard)` at spawn.py:4074

`spawn.py:4069` records the success outcome, and only at `spawn.py:4074` —
the *next* statement — is the guard disarmed. Between those two lines the
guard is still armed with `state["cwd"]` pointing at the real, just-cloned
workspace. A SIGTERM/SIGINT landing in that gap fires the handler
(`spawn.py:1112-1135`), which unconditionally runs
`shutil.rmtree(cwd, ignore_errors=True)` plus two `unlink(missing_ok=True)`
calls — deleting the workspace, claim, and task file for a bootstrap that
had *already succeeded*. `_record_spawn_outcome` itself is idempotent per
`attempt_id` (`_SPAWN_ATTEMPT_OUTCOME_WRITTEN` gate, spawn.py:1085-1087, read
directly), so the outcome record is not clobbered back to `"halted"` — that
idempotency guards only the log line, not the `shutil.rmtree`/`unlink`
calls, which run regardless of it. Net effect: the attempt's outcome record
still reads `"session-log"` (looks like a clean success) while the
workspace/claim/task file it points at no longer exist on disk.

derived: `cd /tmp/pr2782-wt && python3 scratch_race_probe.py` (scratch probe, not committed — forks a real child, arms the guard, records `"session-log"`, sleeps 2s to widen the real-but-tiny statement gap, sends a real `SIGTERM` mid-sleep)
```
workspace survives: False
marker survives: False
outcome: session-log - /dev/null
```
The injected `time.sleep(2.0)` between the two statements only makes the
already-real gap (the JSONL-append syscall inside `_record_spawn_outcome`,
which is not zero-cost) deterministically hittable under test — it does not
fabricate a window that isn't already there in the unmodified code.

**Finding 2 (medium severity, confirmed) — signal landing during the clone
itself leaves a partial workspace behind, unremoved.**

canonical: `git diff origin/main -- spawn.py` (PR worktree) — `cwd = issue_workspace(cwd, issue, skill)` at spawn.py:3564, `_bootstrap_signal_guard[0]["cwd"] = cwd` at spawn.py:3568 (only after the clone call returns)

`state["cwd"]` is populated only at spawn.py:3568, after `issue_workspace()`
(spawn.py:3564) returns. A signal arriving while the clone is still running
has `state["cwd"] is None`, so the handler's `if cwd:` branch
(spawn.py:1139, read directly) is false and no deletion happens — the
partially-cloned directory is left on disk. This is not a hypothetical
corner: PR #2782's own summary (`gh pr view 2782`, read above) names "the
orchestrator's own Bash-tool-call timeout mid-spawn" as one of the two real
triggers for this signal, and a slow/hung clone is exactly the kind of
thing that produces a tool-call timeout. For any decline/timeout landing in
this window, issue #2742 acceptance bullet 3 ("A declined spawn leaves no
workspace, claim, or task file behind") is not met for that window — the
outcome message is accurate (`"halted...not a crash"`), but the
storage/inode cost the issue complains about is not eliminated here.

derived: `cd /tmp/pr2782-wt && python3 scratch_midclone_probe.py` (scratch probe, not committed — forks a real child that mimics the pre-clone-return state: a physically-existing partial directory with `state["cwd"]` still unset, then sends a real `SIGTERM`)
```
partial workspace survives (LEFT BEHIND): True
outcome: halted - caller departed before bootstrap finished (received SIGTERM) — this is not a crash, no session ever started
```

**Everything else checked out**, in order of the review brief:

- Window between clone finishing and claim write (spawn.py:3568-3571):
  canonical: read spawn.py:3560-3575 directly — signal correctly deletes
  workspace/claim/task-file in this window since `cwd` is populated and
  nothing has claimed it yet. Correct.
- Disarm before the `claim_rejection` early return (spawn.py:3571):
  canonical: read spawn.py:3565-3572 directly — correct by construction,
  this attempt's own workspace is cleaned up by the pre-existing
  claim-rejection path itself (untouched by this PR), and once disarmed a
  later signal reverts to default Python SIGTERM behavior, same as before
  this PR existed.
- Second signal arriving while the handler is already running: fired
  `SIGTERM`+`SIGINT`+`SIGTERM` back to back at a handler mid-`shutil.rmtree`
  of a 3000-file directory, 3 separate runs, derived:
  `cd /tmp/pr2782-wt && python3 scratch_double_signal.py` (scratch probe, not committed), same result all 3 runs:
  ```
  exit status: 33280 exited: True code: 130
  workspace survives: False
  num outcome records written: 1
   - halted caller departed before bootstrap finished (received SIGINT)
  ```
  Exactly one outcome record written each time, clean exit, workspace
  removed exactly once, no crash, no double-write — safe by construction
  (`_record_spawn_outcome`'s idempotency, spawn.py:1085-1087, plus
  `ignore_errors=True`/`missing_ok=True` on the deletions, spawn.py:1136-1138).
- Reverse case — genuine crash must still produce the old line and leave
  the workspace: reproduced with a real `SIGKILL` (uncatchable, no Python
  code runs).
  derived: `cd /tmp/pr2782-wt && python3 scratch_watchdog_lines.py` (scratch probe, not committed — forks two real children, one `SIGTERM`'d and one real-`SIGKILL`'d mid-bootstrap, then runs the actual `roster.spawn_attempt_sweep()` over the resulting `spawn-attempts.jsonl`)
  ```
  === declined-case line ===
  [spawn-attempt] issue-2741/declined-role: spawn halted pre-workspace (attempted at 2026-08-29T21:27:38Z): caller departed before bootstrap finished (received SIGTERM) — this is not a crash, no session ever started; removing partial workspace /tmp/tmp9pcc6pa7/ws-declined
  === crash-case line ===
  [spawn-attempt] issue-2741/killed-role: spawn halted pre-workspace (attempted at 2026-08-29T21:22:13Z): no outcome recorded 330s after spawn attempt (pid 222) — process likely died before it could report why

  declined workspace survives: False
  killed workspace survives (should be True, uncatchable): True
  ```
  The two lines genuinely diverge (`SIGTERM`/`not a crash` vs. `likely
  died`), and the `SIGKILL` case genuinely leaves the workspace behind —
  the divergence is real, produced by the actual watchdog sweep code, not
  asserted.
- Coverage claim structurally (`roster.py` untouched):
  derived: `cd /tmp/pr2782-wt && git diff origin/main -- roster.py | wc -l`
  ```
  0
  ```
  Empty — the watchdog's reporting/reconciliation path (`roster.py`) is
  untouched by this PR; nothing was suppressed there to make the new line
  look clean.

**Four standing invariants:**

- **No return of the retired role axis.**
  derived: `cd /tmp/pr2782-wt && git diff origin/main -- spawn.py | grep -n '^[+-].*\brole\b' | wc -l`
  ```
  0
  ```
  The only `role` tokens the PR's diff adds anywhere are inside its own
  test file (PR-branch-only, see note above), as plain identifier text
  (`attempt_id`s like `"2742:role:1:1"`, skill-name literals
  `"declined-role"`/`"killed-role"`) — not a `roles/`-keyed lookup or any
  reintroduction of the role-based addressing scheme retired in #2537/#2539
  (canonical: `grep -rn "role axis" docs/issue-2537 docs/issue-2539` — read
  directly, confirms what "role axis" refers to). No code path in the diff
  reads from or writes to a role axis.
- **No new bug (failing-test set vs. current `origin/main`, as sets of
  names, not counts).** PR #2782's own test plan (`gh pr view 2782`, read
  above) computed its baseline against a checkout 8 commits behind the
  current `origin/main` tip.
  canonical: `git log --oneline pr-2782-review..origin/main` — 8 commits,
  including `dc48170d` which touches
  `test/test_upstream_defect_scope_guard_cross_repo_cwd.py`
  derived:
  ```
  $ cd /tmp/main-current && python3 -m pytest -q 2>&1 | tail -1
  16 failed, 553 passed, 3 xfailed in 6.46s
  $ cd /tmp/pr2782-wt && python3 -m pytest -q 2>&1 | tail -1
  16 failed, 558 passed, 3 xfailed in 6.10s
  $ diff <(cd /tmp/main-current && python3 -m pytest -q 2>&1 | grep '^FAILED' | sort) \
         <(cd /tmp/pr2782-wt && python3 -m pytest -q 2>&1 | grep '^FAILED' | sort) \
         && echo IDENTICAL SETS
  IDENTICAL SETS
  ```
  Identical 16-name failing-test set against the fresh baseline, 5 new
  tests added (558-553), 0 new failures.
- **No overhead increase** (arms on every spawn).
  derived:
  ```
  $ cd /tmp/pr2782-wt && python3 -c "
  import sys, time; sys.path.insert(0, '.'); import spawn
  N = 20000
  t0 = time.perf_counter()
  for i in range(N):
      armed = spawn._arm_bootstrap_signal_guard(f'attempt-{i}')
      armed[0]['cwd'] = None
      spawn._disarm_bootstrap_signal_guard(armed)
  print(f'{(time.perf_counter()-t0)/N*1e6:.2f}us each')"
  7.27us each
  ```
  ~7.27µs per spawn against a spawn path that clones a repo and forks a
  session (seconds). Negligible.
- **Monitor/watch machinery unbroken and NOT quieter.**
  canonical: read `roster.py:611-690` (`spawn_attempt_sweep`) and
  `spawn.py:1211-1220` (`_classify_halt_reason`) and `spawn.py:1232-1247`
  (`_halt_condition_cleared` docstring) directly. The new `"halted"`
  outcomes this PR produces flow through the exact same reporting branch
  every other halted outcome already used. `_classify_halt_reason` matches
  the new `"caller departed..."` detail string against none of the five
  known `_HALT_CLASS_PATTERNS`, so it classifies as `"unknown"`, and
  `_halt_condition_cleared()`'s own docstring states unknown classes are
  always treated as "not yet cleared" — i.e. always reported, every tick,
  until superseded by an actual later successful attempt for the same
  (issue, role) (the same supersession rule every other halt class already
  gets). No new special-casing suppresses these lines.
  canonical: read `watchdog.py:1530` directly — `anomaly_count +=
  _sp.spawn_attempt_sweep(d_all=d_all)` is untouched by this PR's diff.
  derived: `cd /tmp/pr2782-wt && git diff origin/main -- watchdog.py | wc -l`
  ```
  0
  ```
  The fix changes *what the line says* for decline/timeout events (accurate
  instead of "probable crash"); it does not reduce how often the sweep
  reports them.

## Why

derived: `cd /tmp/pr2782-wt && python3 -m pytest -q test_bootstrap_signal_guard.py`
```
5 passed
```

PR #2782's own test file ships that coverage, all real fork+signal, and it
covers the two boundaries it names explicitly in its own reasoning:
signal-before-disarm-on-claim-rejection, and signal-after-disarm-on-success.
It does not cover the two adjacent windows where the arm/disarm *timing
itself* has a gap: the statement-level race between recording success and
disarming (finding 1), and the fact that `cwd` capture happens only after
the clone call returns, not before it starts (finding 2). Adversarial
review's job is to attack the boundaries a test suite didn't think to name —
both findings above were reproduced with real forked processes and real
signals, not asserted from reading the diff.

## What did not work

None.

## Upstream basis

- PR #2782, branch `issue-2742/distinguish-caller-departed-spawn`, HEAD
  `26f09b170095d7b5638554b51ab42df239557e4b` (sha, not same-commit — this
  record lands on the reviewer's own branch, not the PR's) — the `spawn.py`
  diff (`_arm_bootstrap_signal_guard`/`_disarm_bootstrap_signal_guard`/
  `_handler`, spawn.py:1093-1157, and their four call sites at
  spawn.py:3355, 3568, 3571, 4074) and its test file (name:
  test_bootstrap_signal_guard.py, PR-branch-only, untracked in this
  checkout).
- `origin/main` at `dc48170d` (current tip at review time, matches this
  session's gitStatus) — used as the fresh baseline for the failing-test-set
  comparison, since the PR branched 8 commits behind it.

## Open findings

- Finding 1 (session-log → disarm race deletes an already-live workspace,
  spawn.py:4069-4074): open, not yet fixed on the PR branch. Resolution
  path: swap the two statements' effective order — disarm (or at minimum
  clear `state["cwd"]`) *before* `_record_spawn_outcome(..., "session-log",
  ...)` is called, so the handler can never see a populated `cwd` once the
  outcome is about to be recorded as successful. A signal in that instant
  would then fall through to default Python SIGTERM behavior (process
  dies, workspace untouched) rather than reaching the handler.
- Finding 2 (mid-clone signal leaves a partial workspace behind,
  spawn.py:3564-3568): open, not yet fixed. Resolution path: set
  `state["cwd"]` to the *target* clone path before calling
  `issue_workspace()`, not after it returns, so a signal arriving mid-clone
  still knows what to remove. Requires confirming `issue_workspace()`'s
  target path is knowable before the clone starts.
- Adhoc/auto-respawn spawns (`attempt_id is None`) are entirely outside
  this guard's coverage by design (per PR #2782's own summary, `gh pr view
  2782` read above) — not a gap against issue #2742's acceptance criteria
  (scoped to the orchestrator-approval flow, which does carry an
  `attempt_id`), noted here only as a scope boundary for a future reader.

## Next steps

canonical: this record's own "Open findings" section above (same file) —
routing Finding 1 and Finding 2 to a fix is the next session's job, not
this one's. Nothing further to do from this record.

skill-verdict: adversarial-review — applied: invoked; canonical: this
session's own Skill-tool call this turn (loaded the skill's SKILL.md before
writing any finding) — confirmed this session already occupies the
"structurally independent evaluator" role the skill describes (separate
session from PR #2782's author, no shared context), and followed its
evidence-requirement (every finding above cites file:line plus a real,
executed reproduction)
skill-verdict: work-in-english — applied: invoked implicitly by session
convention; canonical: this record itself (same file) — all prose, scratch
probes, and command output are in English
other mounted skills: not triggered (verify-finding-record,
technical-feasibility-reversibility-tag, growth-analytics-segmentation,
agent-coordination — none of their trigger conditions matched this task: no
defect-verification.md record being written, no technical-feasibility.md
probe, no funnel/segmentation claim, no concurrent multi-agent write
conflict)
