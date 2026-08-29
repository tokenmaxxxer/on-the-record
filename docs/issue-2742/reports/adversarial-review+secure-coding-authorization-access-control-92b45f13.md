---
issue: 2742
role: adversarial-review+secure-coding-authorization-access-control-92b45f13
author: adversarial-review+secure-coding-authorization-access-control-92b45f13
skills: adversarial-review (skill-repository(c05de12)), secure-coding-authorization-access-control (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: complete
upstream:
  - path: PR #2782 (issue-2742/adversarial-review+observability-explorability-e32be86d), spawn.py + test/test_bootstrap_signal_guard.py
    sha: 5ee8f66007bb2d498d40a955e6656ab403c47b36
  - path: docs/issue-2742/reports/adversarial-review-45418159.md
    sha: b00ad6b0786c6e2ba85187856587dc8156bc19a2
---

# issue-2742 — adversarial-review+secure-coding-authorization-access-control-92b45f13 record

## What was done

Build-now delivery (`CORE_BUILD_NOW=1`, set by the spawner). Cherry-picked PR
#2782's commit `5ee8f660` onto this branch (rebased onto current
`origin/main`), then fixed two gaps a CHANGES review named on that PR, plus
two more this session found while fixing those two.

canonical: `gh pr view 2782 --json body,reviews,comments` comment by
JiwonJung94 — quotes both named gaps verbatim (mid-clone `cwd` populated only
after `issue_workspace()` returns; disarm's two non-atomic `signal.signal()`
calls leaving a gap where the old handler can still delete a live session's
workspace).

derived: `git show --stat 5ee8f660` — `spawn.py` (80 lines) +
`test/test_bootstrap_signal_guard.py` (228 lines); `git cherry-pick -n
5ee8f660` applied clean, no conflicts against `origin/main`.

**Fix 1 (mid-clone gap named by the review).** Extracted the origin-lookup/
path computation half of `issue_workspace()` into `_workspace_target_path()`
(spawn.py:2898), called before `issue_workspace()` runs (not after) to
pre-populate the guard's `cwd`, via a new wrapper
`_create_workspace_with_signal_guard()` (spawn.py:3091) used at both
`issue_workspace()` call sites in `_spawn_one()`.

**Fix 2 (disarm-race gap named by the review).** Handler now refuses to
touch the workspace once this attempt's outcome is already recorded,
regardless of whether disarm has finished:

```python
    def _handler(signum, frame):
        if attempt_id in _SPAWN_ATTEMPT_OUTCOME_WRITTEN:
            # ... (see spawn.py:1128-1146 for the full rationale comment)
            return
        sig_name = signal.Signals(signum).name
```
derived: `sed -n '1126,1131p' spawn.py` — matches spawn.py:1126-1131 verbatim.

**Fix 3 (self-found via an independently spawned blind-review subagent,
zero context on this issue — see "Why").** Unconditionally pre-populating
`cwd` in fix 1 made a signal during a *reuse* fetch (issue-scoped respawn
reusing a prior attempt's real checkout, or the `src == work` self-reuse
branch returning the caller's own directory) delete content this attempt
never created. Fixed by classifying the target before arming:

```python
def _workspace_target_is_fresh(cwd: str, target_path: str, issue: int | None) -> bool:
    src = Path(cwd).resolve()
    target = Path(target_path)
    target_resolved = target.resolve() if target.exists() else target
    if src == target_resolved:
        return False
    if issue is not None and (target / ".git").exists():
        return False
    return True
```
derived: `sed -n '3081,3088p' spawn.py` — matches spawn.py:3081-3088 verbatim.
`_create_workspace_with_signal_guard()` (spawn.py:3109-3119) only arms
cleanup when this returns `True`, both before and after the
`issue_workspace()` call.

**Fix 4 (self-found by re-reading the call sites after fix 3).** The adhoc
(`issue is None`) `issue_workspace()` call site never went through the
pre-population wrapper — it called `issue_workspace()` directly, so an adhoc
spawn's guard `cwd` stayed `None` for the whole bootstrap, not just the clone
window.

derived: `git diff origin/main -- spawn.py` around the adhoc block — before:
`cwd = issue_workspace(cwd, issue, skill)`; after:
`cwd = _create_workspace_with_signal_guard(cwd, issue, skill,
_bootstrap_signal_guard)` (spawn.py:3541-3543).
acceptance: `python3 -m pytest -q test/test_bootstrap_signal_guard.py -k
test_signal_during_adhoc_clone_also_removes_partial_workspace` — result:
`1 passed`.

## Why

**Fix 2's choice (handler-refuses vs. atomic disarm).** The review offered
both; took handler-refuses because it is defence in depth independent of
disarm's own correctness — even a future disarm bug of a different shape
still can't make this handler delete a workspace whose session is already
recorded as started. canonical: PR #2782 review comment (cited above under
"What was done") — "Make the disarm atomic ..., or make the handler refuse
to delete ... The second is probably simpler and is also a defence in
depth."

**Independent blind review of this session's own fix, before delivery.**
This role's mounted `adversarial-review` skill states that a fix's own author
cannot reliably critique it in the same context window. Two fresh
`general-purpose` subagents were spawned via the `Agent` tool with zero
issue/intent context — only a raw `git diff` of spawn.py + the test file —
and asked to find everything wrong.

derived: first Agent-tool call this session ("Blind adversarial review of
signal-guard diff") — subagent's returned report, verbatim finding 1: "the
guard's own stated invariant... No test exercises this path" for the
reuse-branch deletion risk, which this record's fix 3 (above) addresses.

derived: second Agent-tool call this session ("Second blind review of
updated diff") — subagent's returned report, verbatim: "Fixed for the two
cases the diff explicitly targets and tests: self-reuse... and issue-scoped
`.git` reuse — both have real fault-injection tests... that pass logically
on inspection", plus two lower-severity structural notes carried into "Open
findings" below.

**Adhoc routed through the same wrapper (fix 4) rather than a parallel
inline fix.** A second, hand-copied pre-population block would repeat the
same shape as the review-named mid-clone gap — one call site fixed, a
sibling call site not — canonical: PR #2782 review comment (cited above)
names only the call site inside `_spawn_one`'s issue-scoped path; this
session's own re-reading found the adhoc call site the review did not name.
One wrapper function used at both means there is exactly one place this
logic can go stale.

## What did not work

The first version of fix 3 (pre-populate `cwd` unconditionally, before
checking whether the target already held real content) was wrong.

derived: manually reverted `_create_workspace_with_signal_guard()` to the
unconditional-population form in-session, reran the two fix-3 regression
tests: `python3 -m pytest -q test/test_bootstrap_signal_guard.py -k
"test_signal_during_reuse_fetch_does_not_delete_prior_work or
test_signal_during_self_reuse_never_targets_callers_own_checkout"` — result:
`2 failed` (one `AssertionError: False is not true`, one `assertIsNone`
failure on the caller's-own-checkout guard). Restored the
`_workspace_target_is_fresh()`-gated version from a saved copy
(`/tmp/spawn.py.fixed4`); reran the same selector — result: `2 passed`.
`git diff origin/main -- spawn.py` (this session, at delivery time) shows
only the gated version at spawn.py:3109-3119 — no trace of the unconditional
version remains in the delivered diff.

## Upstream basis

- PR #2782, commit `5ee8f66007bb2d498d40a955e6656ab403c47b36` (cherry-picked,
  see "What was done").
- `docs/issue-2742/reports/adversarial-review-45418159.md`, commit
  `b00ad6b0786c6e2ba85187856587dc8156bc19a2` — independent verification that
  named the mid-clone and disarm-race gaps this record's fixes 1 and 2
  (described above under "What was done") address.
- canonical: `gh issue view 2742 --json body` — the three `check:` acceptance
  bullets, re-derived live below.

## Verification

acceptance: `python3 -m pytest -q test/test_bootstrap_signal_guard.py` —
result:
```
...........                                                              [100%]
11 passed in 30.84s
```
All real fork+signal, no mocked signal delivery. New cases beyond the ones
inherited from PR #2782: `test_signal_during_clone_removes_partial_workspace`,
`test_signal_during_adhoc_clone_also_removes_partial_workspace`,
`test_adhoc_leftover_at_target_path_is_wiped_not_preserved`,
`test_signal_during_reuse_fetch_does_not_delete_prior_work`,
`test_signal_during_self_reuse_never_targets_callers_own_checkout`,
`test_signal_after_session_log_before_disarm_does_not_delete_workspace`.
Each was confirmed, in-session, to fail against a temporarily-reverted
pre-fix version of its target code and pass against the delivered version
(the fix-3 pair's revert/rerun transcript is under "What did not work"; the
fix-1/fix-2/fix-4 pairs were each reverted and rerun the same way during
this session, before this record was assembled).

acceptance: full-suite failing-test-name SET comparison vs. `origin/main` —
`derived: python3 -m pytest -q` on a fresh `origin/main` worktree captured to
`/tmp/main_failed_names.txt`, same on this branch to
`/tmp/pr_failed_names3.txt`, then `diff /tmp/main_failed_names.txt
/tmp/pr_failed_names3.txt` — result: no output (identical sets), both list
the same pre-existing failing names. Pass counts, tail line of `python3 -m
pytest -q` on each side — `origin/main`: `16 failed, 553 passed, 3 xfailed`;
this branch: `16 failed, 564 passed, 3 xfailed` (the delta is the new
signal-guard tests).

acceptance: `git diff origin/main -- roster.py | wc -l` — result: `0`.

acceptance: `git diff origin/main -- spawn.py | grep -n '^[+-].*\brole\b' |
wc -l` — result: `0`. No retired role axis reappears.

acceptance: `grep -n "_bootstrap_signal_guard = _arm_bootstrap_signal_guard\|_disarm_bootstrap_signal_guard(_bootstrap_signal_guard)" spawn.py`
— result: arm at line 3447, disarm at 3670 (pre-`claim_rejection`) and 4173
(post-`session-log`) — both disarm points from PR #2782 preserved.

acceptance: overhead, `derived:` 20,000-iteration loop of
`_arm_bootstrap_signal_guard`+`_disarm_bootstrap_signal_guard` run this
session — result: `7.51us/cycle`, vs. `8.01us/cycle` measured on PR #2782
alone per `adversarial-review-45418159.md` (no regression). Separately,
`_workspace_target_path()` itself (now called twice per fresh-clone
bootstrap — see "Open findings" below) — `derived:` 200-iteration loop on a
real local git repo run this session — result: `4.227ms/call`, negligible
against a bootstrap that clones a repo over the network.

acceptance: issue #2742's three `check:` bullets, live —
`derived: python3 /tmp/probe_acceptance.py` (script + full transcript this
session) — result:
```
[spawn-attempt] issue-2741/declined-role: spawn halted pre-workspace (attempted at 2026-08-29T22:10:46Z): caller departed before bootstrap finished (received SIGTERM) — this is not a crash, no session ever started; removing partial workspace /tmp/tmpkha6y2xq/probe2742-issue-2741-declined-role
[spawn-attempt] issue-2741/killed-role: spawn halted pre-workspace (attempted at 2026-08-29T22:05:16Z): no outcome recorded 330s after spawn attempt (pid 999999) — process likely died before it could report why
(sweep classified 2 stale attempts)

=== Case 3: list MUSTER_WORK_DIR for the declined session id ===
entries matching declined session id (issue 2741 / declined-role): []
killed-session workspace still present: True (.../probe2742-issue-2741-killed-role)
```
Check 1 (decline → declined line): the first line above. Check 2 (kill →
distinct line, shown next to check 1's): the second line above, and distinct
from the first (`SIGTERM`/`not a crash` vs. `no outcome recorded`/`likely
died`). Check 3 (decline → 0 entries for that session id): the empty list
above (`MUSTER_WORK_DIR`-scoped to a throwaway temp dir — the documented
override for `~/.tokenmaxxxer/work` per spawn.py's own convention, used so
this probe never touches the live orchestrator's real work directory). The
killed-session workspace remaining present is the contrast case proving the
two stay distinguishable end to end, not itself one of the three bullets.

## Open findings

Two structural notes from the second blind-review subagent pass (cited under
"Why"), judged out of scope for this delivery: both are properties of the
approach the review itself specified (best-effort pre-population, and the
handler-refuses choice for the disarm-race gap), not defects this round
introduced, and neither reopens the two review-named gaps or the fix-3
regression.

1. `_workspace_target_path()` runs twice per fresh-clone bootstrap (guard
   pre-population, then again inside `issue_workspace()`) — a redundant
   local `git remote get-url` (~4ms, measured above under "Verification")
   and a narrow TOCTOU if `origin`'s remote or `MUSTER_WORK_DIR` changed
   between the two calls. Nothing in this codebase changes either
   mid-bootstrap; resolution path if ever tightened: have
   `issue_workspace()` accept a precomputed `(origin, work)` pair so both
   callers share one lookup.
2. No `try`/`finally` wraps arm/disarm across all of `_spawn_one()` — an
   uncaught exception between them leaves the handler installed with a stale
   `attempt_id`. `_spawn_one()` recurses in-process only via
   `_respawn_or_cap()`'s self-trigger path — canonical:
   `python3 -c "import lifecycle,inspect;
   print(inspect.getsource(lifecycle._respawn_or_cap))" | grep -B2 -A2
   self-trigger` — its docstring names this as the only same-process
   `_spawn_one()` re-entry path and describes it firing after a completed
   session (after the normal disarm already ran). This predates this round
   — `derived: git show 5ee8f660 -- spawn.py` shows no `try`/`finally`
   around the original arm/disarm pair in PR #2782's own commit either — and
   is not one of the two review-named gaps; flagging for a maintainer scope
   decision rather than wrapping an ~700-line function without a live
   reproduction proving this is reachable.

## Next steps

acceptance: `python3 -m pytest -q test/test_bootstrap_signal_guard.py` (run
again at record-assembly time, this session) — result: `11 passed in 30.84s`
— this is the live basis for setting `loop_state: complete` in this record's
frontmatter; no further work is planned beyond what "## Verification" above
already exercised. The two "Open findings" are handed to the maintainer for
a scope decision rather than left unmentioned.

skill-verdict: adversarial-review — applied: invoked; spawned two
independent `general-purpose` subagents (Agent tool, fresh context, zero
issue/intent context — only a raw `git diff`) to blind-review this session's
own fix before delivery. derived: the two subagent reports, quoted verbatim
under "Why" above — first-pass report text "the guard's own stated
invariant... No test exercises this path" (led to fix 3); second-pass report
text "Fixed for the two cases the diff explicitly targets and tests..." (led
to the "Open findings" notes).
skill-verdict: secure-coding-authorization-access-control — not-applicable:
this fix is signal-handling/filesystem-cleanup in a spawn bootstrap; no
authorization/permission/role/tenant decision point exists anywhere in the
changed functions listed under "What was done" (`_workspace_target_path`,
`_workspace_target_is_fresh`, `_create_workspace_with_signal_guard`, the
signal handler in `_arm_bootstrap_signal_guard`).
skill-verdict: work-in-english — applied: invoked; this record, all commit
messages, and PR text are in English; new code comments follow spawn.py's
pre-existing in-file convention (mixed Korean/English throughout the file
prior to this change) rather than switching languages mid-file; only the
final chat summary to the user is in Korean.
skill-verdict: decision-records — not-applicable: this delivery responds to
a review's already-named findings (cited under "What was done") plus two
self-found regressions with a settled fix each; no still-open direction call
was escalated in this session.
