---
issue: 2742
role: adversarial-review-45418159
author: adversarial-review-45418159
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
loop_state: complete
upstream:
  - path: PR #2782 (issue-2742/adversarial-review+observability-explorability-e32be86d)
    sha: 5ee8f66007bb2d498d40a955e6656ab403c47b36
  - path: docs/issue-2742/reports/adversarial-review+observability-explorability-e32be86d.md
    sha: 26f09b170095d7b5638554b51ab42df239557e4b
---

# issue-2742 — adversarial-review-45418159 record

## What was done

Independent re-derivation of PR #2782's claims for issue #2742 (SIGTERM/SIGINT
bootstrap-signal guard in `spawn.py`), checked out to a separate worktree
(`git worktree add /tmp/wt-2782 pr-2782-review`, fetched via `git fetch origin
pull/2782/head:pr-2782-review`) and exercised with real forks and real
signals — not the PR's own test output taken on faith.

Confirmed live:

- `python3 -m pytest -q test/test_bootstrap_signal_guard.py` on the PR branch —
  `5 passed in 0.84s`, all real fork+signal (no mocked signal delivery).
- Full-suite failing-test-name-set comparison, origin/main vs. the PR branch:
  `derived: diff /tmp/main_failed.txt /tmp/pr_failed.txt` — `IDENTICAL SETS`,
  both sides list the same 16 names (`test_first_contact_fires_once_per_workspace`,
  the two `ApprovalGateEquivalenceTest`/`BranchRoleFieldDualReadEquivalenceTest`
  cases, `CallSiteWiringTest::test_origin_captured_before_workspace_reassignment`,
  the four `test_spawn_cross_family_skill_selection.py` cases, the two
  `test_spawn_artifact_skill_pairing.py` cases, and the four
  `test_spawn_skill_judge_haiku_timeout_overlap.py` cases). Pass counts:
  main `553 passed`, PR `558 passed` (the 5 new tests) — `derived:
  python3 -m pytest -q` on each worktree.
- `git diff origin/main..pr-2782-review-tmp -- roster.py | wc -l` → `0`. The
  watchdog's reporting/sweep path is untouched.
- `git diff origin/main..pr-2782-review-tmp -- spawn.py | grep -n '^[+-].*\brole\b'`
  → exit 1 (no matches). No retired role axis reappears.
- Overhead: `derived:` a 20,000-iteration loop of
  `_arm_bootstrap_signal_guard`+`_disarm_bootstrap_signal_guard` on the PR
  branch measured `8.01us/cycle` — negligible against a bootstrap that clones
  a repo.
- Live two-line divergence, produced end-to-end through the real
  `roster.spawn_attempt_sweep()` (not the PR's canned-JSONL test), from two
  actually-forked, actually-signaled child processes
  (`derived: python3 /tmp/probe_watchdog_lines.py`):
  ```
  [spawn-attempt] issue-2742/declined-role: spawn halted pre-workspace (attempted at 2026-08-29T21:24:30Z): caller departed before bootstrap finished (received SIGTERM) — this is not a crash, no session ever started; removing partial workspace /tmp/tmp5aaav_qf/ws-decline
  [spawn-attempt] issue-2742/killed-role: spawn halted pre-workspace (attempted at 2026-08-29T21:24:30Z): no outcome recorded 330s after spawn attempt (pid 2239327) — process likely died before it could report why
  ```
  Disk check after: declined/SIGTERM workspace gone (`False`), killed/SIGKILL
  workspace retained (`True`). All three acceptance-criteria checks (declined
  line, distinct kill line, zero leftover entries for the declined session)
  hold in this direct path.

Found two coverage gaps by attacking the arm/disarm boundaries directly (fork +
real signal, no mocks) rather than reading the diff for plausibility. Both
reproductions and the exact code locations they hit are quoted in full under
"Open findings" below, each with its own `derived:`/canonical citation.

Benign, checked and ruled out:

- Two identical SIGTERMs fired back-to-back at the "cwd known" stage (no gap
  injected): `derived: python3 /tmp/probe_reentrancy.py` → workspace correctly
  removed once, exactly one outcome record written. `os._exit()` inside the
  handler terminates the process before a second delivery of the same signal
  can re-enter the still-armed handler in practice.

## Why

The PR's own test suite uses real fork+signal (verified, not taken on faith),
which rules out signal-delivery-timing bugs at the two boundaries the author
designed for. But those tests only exercise the arm→cwd-known and
post-session-log-disarm call sites the author already had in mind — they
don't attack the internal non-atomicity of `_disarm_bootstrap_signal_guard`
itself, nor the window before `cwd` is populated inside the workspace-creation
step it wraps. An adversarial review whose job is to find what the builder
didn't anticipate has to construct exactly those windows directly, which is
what the fork+signal probes below do.

## What did not work

None.

## Upstream basis

- PR #2782, commit `5ee8f66007bb2d498d40a955e6656ab403c47b36` — `spawn.py`
  (tracked, present in this worktree's fetched PR branch) and
  `test/test_bootstrap_signal_guard.py` (untracked in this session's own
  checkout; present in git history only on the PR branch at this commit —
  `derived: git log --oneline --all -- test/test_bootstrap_signal_guard.py`
  shows commit `5ee8f660`) — the code under review.
- `docs/issue-2742/reports/adversarial-review+observability-explorability-e32be86d.md`,
  commit `26f09b170095d7b5638554b51ab42df239557e4b` (untracked in this
  session's own checkout; present in git history only on the PR branch) —
  the PR author's own evidence record, used only to identify which claims
  to re-derive, not taken as given.
- `canonical: gh issue view 2742` output — the three `check:` acceptance
  bullets plus the "must not: timeout heuristic" constraint, used to scope
  what "correct" means for this review.

## Open findings

1. Mid-clone/fetch cleanup gap. `canonical: spawn.py` on the PR branch —
   ```
   with _timed("workspace"):
       cwd = issue_workspace(cwd, issue, skill)
   if _bootstrap_signal_guard is not None:
       _bootstrap_signal_guard[0]["cwd"] = cwd
   ```
   `_bootstrap_signal_guard[0]["cwd"]` is populated only *after*
   `issue_workspace()` returns, and `issue_workspace()` runs a real `git
   clone`/`git fetch` subprocess. A signal landing during that call is
   correctly diagnosed ("halted ... not a crash") but the just-created
   partial workspace directory is not cleaned up, because the handler's
   `if cwd:` guard sees `None`. Reproduced with a real fork+SIGTERM landing
   in that exact window: `derived: python3 /tmp/probe_midclone.py` →
   `workspace dir still exists after SIGTERM during mid-clone window: True`
   (directory retained a partially-written marker file; outcome still
   correctly recorded as `halted`/"not a crash"). This undercuts acceptance
   criterion 3 ("0 entries for the declined session id") for declines that
   land during this specific sub-window. Resolution path: populate
   `_bootstrap_signal_guard[0]["cwd"]` with the best-effort target path
   before calling `issue_workspace()`, not only after it returns.

2. Disarm-window race. `canonical: spawn.py` on the PR branch —
   ```
   def _disarm_bootstrap_signal_guard(armed) -> None:
       if armed is None:
           return
       _, prev_handlers = armed
       for sig, handler in prev_handlers.items():
           signal.signal(sig, handler)
   ```
   This loop resets SIGTERM's and SIGINT's handlers via two separate,
   non-atomic `signal.signal()` calls. A SIGINT landing in the gap between
   them — exactly the moment right after a real session's `"session-log"`
   outcome has been recorded and a real session is about to run in that
   workspace — still hits the old guard `_handler`, which unconditionally
   runs `shutil.rmtree(cwd)` and unlinks the claim/task files regardless of
   whether `_record_spawn_outcome()` actually wrote anything new this call.
   `_record_spawn_outcome()` dedupes by `attempt_id` (returns early if
   already written), so the deletion leaves no trace in the outcome log —
   the recorded outcome still reads only `"session-log"`, with nothing
   anywhere indicating the workspace it points to was removed afterward.
   Reproduced deterministically by fault-injecting the second signal from
   inside the exact gap between the two `signal.signal()` reset calls (not
   relying on timing luck): `derived: python3 /tmp/probe_disarm_race.py` →
   `workspace exists after mid-disarm SIGINT: False`, outcome file shows
   only the original `session-log` record, no second entry, no error. This
   is precisely the failure class this review was asked to hunt for: the
   handler removing something that was not partial, silently. Resolution
   path: gate the `shutil.rmtree`/unlink block on whether
   `_record_spawn_outcome()` actually performed a write this call (check
   `attempt_id not in _SPAWN_ATTEMPT_OUTCOME_WRITTEN` before deciding to
   clean up, not just call it unconditionally), or block signal delivery
   for the duration of the two-call reset via `signal.pthread_sigmask`.

Both are genuine, reproduced-live gaps in the fix's coverage, not false
positives — but both are narrow-window races/timing gaps in the *cleanup*
path, not defects in the message-diagnosis fix itself (which is correct and
fully verified above under "What was done"), and neither reintroduces the
original "probable crash" misdiagnosis.

## Next steps

None — this record is terminal. Findings above are handed back via this
record for the PR author/maintainer to decide on and address in a follow-up,
per this role's scope (independent verification, not remediation).

skill-verdict: adversarial-review — applied: invoked; this record IS the
independent evaluator's output — structurally separate session from PR
#2782's author, re-derived every load-bearing claim (test counts, diff
emptiness, overhead, the two-line divergence) from scratch with real
forks/signals rather than accepting the PR's own transcript, and attacked
the arm/disarm boundaries the author's own tests did not target.
skill-verdict: work-in-english — applied: invoked; this record, all probe
scripts, and all commit/PR text are in English; only the final chat summary
to the user is in Korean.
other mounted skills: not triggered (verify-finding-record is for
docs/issue-<n>/reports/defect-verification.md outcome records, not this
adversarial-review record).
