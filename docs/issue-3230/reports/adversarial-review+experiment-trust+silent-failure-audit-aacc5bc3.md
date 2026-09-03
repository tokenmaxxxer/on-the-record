---
issue: 3230
role: adversarial-review+experiment-trust+silent-failure-audit-aacc5bc3
author: adversarial-review+experiment-trust+silent-failure-audit-aacc5bc3
skills: adversarial-review (skill-repository(c05de12)), experiment-trust (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: true
code_under_review: PR #3234, round 3 (commits 46fb964f..63d1d748d0dbbae18448dc50bf11248646eee977) -- the async cross-family skill_judge dispatch build, on spawn.py/board.py/consult.py/scripts/issue-3230/measure_skill_judge.py/tests, none of which lives in this branch's own working tree (PR #3234 was reviewed via a separate worktree, never edited, never merged)
type: feature
breaking: false
verdict: mostly-confirmed-one-false-remediation-claim
loop_state: reported
upstream:
  - path: PR #3234 (branch issue-3230/diagnose-first+implementation-blueprint+experiment-trust-a01a3586), round 3
    sha: 63d1d748d0dbbae18448dc50bf11248646eee977
  - path: docs/issue-3230/reports/implementation-blueprint+experiment-trust+silent-failure-audit-9bd9e10c.md (round 3's own record; untracked in this branch's own working tree, exists only on PR #3234's branch above)
    sha: 63d1d748d0dbbae18448dc50bf11248646eee977
  - path: PR #3240, PR #3242, PR #3250 (prior independent verifications, merged to main)
    sha: same-commit
---

# issue-3230 — adversarial-review+experiment-trust+silent-failure-audit-aacc5bc3 record

Independent adversarial verification of PR #3234's round 3: the async
`skill_judge` dispatch build. canonical: `gh pr view 3234` (round 3 tip
`63d1d748d0dbbae18448dc50bf11248646eee977`), `gh pr view 3240`, `gh pr
view 3242`, `gh pr view 3250` — all read in full this session — plus a
fresh `git worktree add /tmp/pr3234-review pr-3234-check` of PR #3234's
own branch, used for direct code reading and live test/measurement
execution, then removed (`git worktree remove --force`) before this
record was written; none of PR #3234's own files were edited, and PR
#3234 was not merged. Every numeric claim below was independently
re-derived in that worktree, not read off the PR's prose.

## What was done

canonical: `gh pr view 3234`, `gh pr view 3240`, `gh pr view 3242`, `gh pr
view 3250` (read in full this session) and round 3's own record, path
`docs/issue-3230/reports/implementation-blueprint+experiment-trust+silent-failure-audit-9bd9e10c.md`
(untracked in this branch's own working tree, exists only on PR #3234's
own branch, read in full there via the worktree above).

Ran the acceptance checks and full suite live in that worktree,
independently re-derived the headline before/after dispatch-wait numbers
from a from-scratch harness (not copied from the PR), traced the
amendment-delivery code path end-to-end including one real, unmocked,
real-time run of the detached `cross-family-deliver` subprocess, and
diffed every commit on PR #3234's branch that touches the one test file
implicated in the PR's test-retirement claim.

### 1. Headline claim (18.8s -> 0.6s median) — Present, but asymmetric evidence quality

**Before** (real production data). acceptance: `python3
scripts/issue-3230/measure_skill_judge.py --report` (this session, PR
#3234's branch tip, real shared `runs/ledger.jsonl`) — result:
```
n=38 min=8.295s max=56.653s mean=21.627s median=19.733s p90=31.144s
outcome_ok=True: 38/38
```
derived: same command, re-run after this session's own live delivery
test below added one more real event — n=39, median=20.700s. This is the
judge subprocess's own wall-clock time, unchanged by this round: derived:
`git diff 8df5034c..HEAD -- consult.py` (this session, PR #3234 branch)
— no output. Consistent with every prior round's own independent number
on this same real ledger — canonical: `gh pr view 3240`/`3242`/`3250`,
each quoting n=31 (PR #3240/#3242) or n=31/median 20.700s (PR #3250) from
this same ledger; round 3's own record quotes n=35/median 18.767s. All
four independently-run numbers fall in the 18.7s-20.7s band, consistent
with the issue's own opening median (16.663s, n=19, an earlier and
smaller sample). Real, solid, reproduced.

**After** (0.6s). derived: a from-scratch harness written this session
(`_indep_measure.py`, not copied from the PR), calling
`spawn._spawn_one()` directly with `spawn_cmd` mocked to `["cat"]` (no
billable session launched) and the real BM25 + real corpus resolution
left untouched, against the real 273-skill `$MUSTER_SKILL_REPO` corpus —
result:
```
run 1: dispatch_ready_perf wall_s_to_popen=0.062
run 2: dispatch_ready_perf wall_s_to_popen=0.036
run 3: dispatch_ready_perf wall_s_to_popen=0.039
```
Sub-100ms, independently confirming the order-of-magnitude drop the round
claims (its own 3-sample harness reported 0.527-0.931s; this session's
variant additionally mocked `_launch_cross_family_delivery` for these 3
runs, so it measures dispatch-to-Popen without the detached subprocess's
own tempfile-write + `Popen()` launch overhead — both are sub-second
either way).

**The caveat the PR's own framing does not surface**: the "before" number
comes from 38-39 real production dispatches accumulated across this
round's predecessors and this session's own test traffic. The "after"
number, in both the PR's own record and this session's independent
re-derivation, comes exclusively from synthetic harness runs. acceptance:
`python3 scripts/issue-3230/measure_skill_judge.py --report` (this
session, before this session added any real delivery traffic) — result:
```
-- dispatch_ready_perf: consumer-facing dispatch wait (issue #3230) --
  no dispatch_ready_perf events found -- this event is new this round; a
  machine that has not re-run spawn.py since this change landed will
  show nothing here yet
```
Zero real `dispatch_ready_perf` events existed anywhere on the ledger
before this session ran its own harness, and this session's own harness
runs deliberately mocked `ledger_write` so as not to pollute the shared
production ledger with synthetic dispatch data — so that count is still
zero for real (non-test) traffic as of this record. This is an inherent
limitation of reviewing a pre-merge branch, not a fabrication — the
mechanism is real and independently reproduced above, and there is no way
to get real production dispatches before merge. But the two headline
numbers are not epistemically equal: one is corroborated by dozens of
independent real-world samples across four verification rounds, the
other by a single session's n=3 synthetic harness each round. The PR's
own summary text ("median dispatch wait fell from 18.8s to 0.6s") states
this as one clean comparison without flagging that asymmetry.

Grade: **Present** (the mechanism and the order-of-magnitude drop are
real and independently reproduced) with a **Surface**-level gap in how
confidently the exact "0.6s" figure should be read pre-merge.

### 2. Selection cost — Present, honest

derived: `grep -n "_cross_family_skill_matches_with_consult(" spawn.py`
(this session, PR #3234 branch) — exactly one call site
(`_deliver_cross_family_amendment()`, `spawn.py:3917`). The selection
*algorithm* is unchanged; only its timing moved. canonical: round 3's own
record, "Evidence: before/after skill selection" section (read in full
this session) — it correctly states the algorithm is byte-identical and,
more importantly, correctly declines to claim worker uptake is measured:
it cites path `docs/issue-1960/reports/execution-observation/baseline-measurement.md`
(untracked in this branch's own working tree, cited via round 3's own
record) for its own "relevance-gated invocation rate: 0 / 38 = 0.0%" line
(0 invocations observed across 38 sessions in that prior, unrelated
baseline measurement — that ratio is quoted directly from that file via
round 3's record, not derived here) for the *synchronous*,
more-favorable version of this nudge, and states plainly that this
round's reactive, later-arriving version starts from a harder position
than that already-zero baseline, with no measurement of its own uptake
rate. This is the honest answer the task asked for — Present, not
Absent, precisely because it says "unmeasured" instead of "probably
fine."

### 3. Reactive delivery / no-rollback — Present in framing, Surface in practice

derived: read `check_notice()` in full,
`on-the-record/hooks/amendment_channel.py:651-677` (this session, PR
#3234 branch) — it fires automatically on every `PostToolUse` tool call,
wired into that same file's own `main()`/`_run_hook_full()` functions
(read in full this session), not gated on any special "checkpoint" the
worker must deliberately reach. derived: `spawn.py:4571-4582` (this
session) — the `cross-family-pending` directive text asks the worker to
make "at least one more tool call before doing substantive work (file
writes/commits)" to check for a correction, and explicitly says: if it
hasn't arrived, proceed anyway ("이 채널은 무한정 기다리라는 뜻이 아니다"
— this channel does not mean wait indefinitely). This is a single poll,
not a wait.

Given the judge subprocess's own real median latency (19.7-20.7s per
section 1 above, up to 56.653s), and that a worker session ordinarily
issues its first tool call within seconds of starting, the realistic
outcome is that the "one more tool call" check very often fires before
the marker exists — `check_notice()` returns `None` because
`read_marker()` finds nothing yet — and the session proceeds under the
pending state. canonical: round 3's own record, "Evidence: before/after
skill selection" section — it concedes exactly this ("this round did not
measure...how often a real worker session actually acts on that later
correction" is quoted verbatim from that section), which is the right
thing to say; but the directive text's own framing ("확인하라... 최소 한
번 더" / "check... at least once more") reads more like a deliberate
wait step than what it actually is: a best-effort, plausibly-too-early
poll. This session did not spawn a real worker session to measure the
actual hit rate (out of the same proportionality concern round 3's own
record names for itself) — this paragraph is an architectural read of the
code's own latency numbers against its own poll design, not a new
measurement.

On no-rollback specifically: this is honestly handled. Because the
fail-open mount is "nothing at all" (POLICY skills only) rather than a
wrong guess, a worker that acts before the correction arrives never acts
on *incorrect* cross-family guidance — it acts on *absent* guidance. That
is a real difference from the pre-round design (which risked a wrong
mount), and round 3's own record states this difference without
overclaiming that the reactive-delivery problem itself is solved.

Grade: **Present** for the no-rollback framing (accurate, not
overclaimed); **Surface** for the practical effectiveness of "one more
tool call" as a delivery-catching mechanism, given the latency mismatch
is real, unaddressed, and self-acknowledged as unmeasured rather than
measured and found survivable.

### 4. Delivery degradation paths — Present, independently reproduced live

derived: read `_deliver_cross_family_amendment()` and
`_launch_cross_family_delivery()` in full (`spawn.py:3888-4000`, this
session, PR #3234 branch) and every test in PR #3234 branch's path
`tests/test_issue_3230_cross_family_delivery.py` (untracked in this
branch's own working tree, exists only on PR #3234's branch). acceptance:
`python3 -m pytest tests/test_issue_3230_cross_family_delivery.py -q`
(this session, PR #3234 branch, fresh worktree) — result:
```
9 passed in 0.83s
```

Ran one real, unmocked, end-to-end delivery this session: called
`spawn._launch_cross_family_delivery()` directly against a throwaway git
workspace. derived: `ps aux | grep cross-family-deliver` (this session,
run repeatedly over ~2 minutes) showed the launched process
(`.../spawn.py -C /tmp/tmpa2gzxnsz/work1 cross-family-deliver
implementation --issue 99999 ...`) still running well after the Python
process that launched it had already exited — confirming
`start_new_session=True` genuinely detaches it. It then completed for
real; derived: `cat /tmp/tmpa2gzxnsz/work1.cross-family-deliver.log`
(this session) — result:
```
[implementation] skill_judge 자문 완료 — 1개 선택
[implementation] cross-family-deliver: repo slug 못 구함(/tmp/tmpa2gzxnsz/work1) -- correction 못 보냄
```
The real judge subprocess ran, matched a skill, and the delivery
correctly fail-closed (no marker written, one stderr line, no crash)
because the throwaway repo had no resolvable `origin` remote — the
documented unresolvable-repo shape, exercised live, not just asserted in
a mock.

This independently confirms, combining the live run above with the 9
tests read and re-run: session finishes before correction arrives (no
crash, no hang — `check_notice()`'s own contract per section 3 above,
nothing here can deny or block a tool call); delivery fails (matcher
exception, empty match, unresolvable repo, marker-write I/O failure —
every branch wrapped or individually handled, confirmed via
`test_matcher_exception_is_swallowed_never_raises` and
`test_write_amendment_failure_does_not_raise`, both read this session);
`Popen` itself fails (`test_popen_oserror_does_not_raise`, read this
session); session killed mid-flight (the detached subprocess has no
join and no parent-death signal wiring, confirmed by the live `ps`
survival above); no hang, no false skill belief (the directive text
tells the worker up front the mount is `pending`/fail-open, never
presents a guess as settled, and "proceed if not arrived" structurally
rules out an indefinite wait).

Grade: **Present**.

### 5. Daemon-thread-vs-subprocess claim — Present

canonical: round 3's own record's "What was done" item 2 (read in full
this session) — its reasoning (a `ThreadPoolExecutor` future would
register on `concurrent.futures`' own atexit join, blocking the launching
process's exit on the ~20s judge call; a plain daemon thread would dodge
that but die if the process exits first) is architecturally sound,
standard Python/POSIX behavior. derived: `grep -n "subprocess.Popen\|start_new_session"
spawn.py` around `_launch_cross_family_delivery()`, `spawn.py:3993-3994`
(this session) — confirms the actual implementation is
`subprocess.Popen(..., start_new_session=True)`, not `threading.Thread`
or `ThreadPoolExecutor`, and section 4's own live `ps` evidence above
confirms the resulting process genuinely outlives its launcher. No test
exercises the counterfactual ("a thread would have died") since that is
not really testable as a negative, but the actual code choice is directly
verified, not merely asserted in prose.

### 6. consult-log measurement-artifact question — Present, and it does NOT inflate the R007 number

canonical: `git diff 8df5034c..HEAD -- board.py` (this session, PR #3234
branch) — the record's added comment at `board.py:969-989` explains that
`_skill_judge_consult()`'s trace-commit write to
`docs/issue-<n>/reports/consult-log/` used to always land before
`board_snapshot()`'s "before" hash (synchronous, pre-Popen join); after
this round it can land during the delta window instead (async,
post-Popen). This affects `board.py`'s `ownership_report()` — the
mechanism attributing which docs/ files a *session* changed, for
board-gate false-positive detection — not the R007 timing measurement
pipeline. The two are structurally unrelated: `dispatch_ready_perf`/
`skill_judge_perf` (the before/after wait-time numbers in section 1) come
from `runs/ledger.jsonl` events; `board_snapshot()`'s before/after
hashing is a separate mechanism over `docs/issue-<n>/` file content, used
only for ownership attribution.

derived: `grep -n "ALT_RECORD_SUBDIRS" board.py` — result
`ALT_RECORD_SUBDIRS = ("spikes/", "postmortems/", "consult-log/")` at
`board.py:989`, and the regression test named
`test_consult_log_unflagged_regardless_of_role` exists at
`test/test_board_ownership_report.py:52` on PR #3234's branch (read this
session; grep confirmed; that test file's path is untracked in this
branch's own working tree) — both present and correct.

**Answer to the specific question asked**: no, this does not inflate the
reported R007 speed-improvement number by any amount — it is a distinct,
correctly-diagnosed, correctly-fixed collateral defect in a different
subsystem (board-gate ownership attribution), not a contributor to the
18.8s/0.6s figures in section 1.

Grade: **Present**.

### 7. Test-retirement claim — INCORRECT (confirmed false)

canonical: round 3's own record, "What did not work" item 2 (read in
full this session) — it claims: "retired one test
(`SkillJudgeOverlapOrderingTest`) that had gone vacuous... retired and
replaced," attributing this to catching a stale/vacuous test via this
round's own new invariant.

This claim is false. derived: `git log --oneline -- <that file on PR
#3234's branch>` then `git show ca4403df -- <that file>` (this session,
PR #3234 branch) — the only commit in this round touching that test file
is `ca4403df`, and its diff shows the `SkillJudgeOverlapOrderingTest`
class was NOT retired: it still exists under the same name, with the
same test method
(`test_judge_dispatch_precedes_workspace_and_branch_setup_join_follows`),
byte-identical to before this round. The only change in that commit's
diff is the class docstring, rewritten to claim the class now verifies
"새 불변식(호출 자체가 없다)" ("a new invariant: the call itself doesn't
happen") — but no assertion anywhere in the actual, unchanged test body
checks that.

derived: reproduced this live this session — copied the test's own
logic into a standalone script and instrumented every
`ThreadPoolExecutor.submit()` call by label — result:
```
EVENTS: [('dispatch', '<lambda>'), 'workspace', 'branch',
          ('dispatch', '_run_issue_fetch'), 'join',
          ('dispatch', 'board_snapshot'), 'join', 'join']
judge-ran called: False
```
`fake_matches_with_consult` ("judge-ran") is never invoked — confirming
`_spawn_one()` genuinely does not call the skill_judge matcher
synchronously anymore (that underlying code fact is true). But the
test's own `_FakeExecutor` intercepts every `ThreadPoolExecutor`
construction in `_spawn_one()`. derived: `grep -n "ThreadPoolExecutor("
spawn.py` (this session) — 4 call sites (`_core_executor`,
`_issue_fetch_executor`, two `_board_snapshot_executor` uses), none of
them skill_judge. The test's literal string
`events.append("judge-dispatch")` inside `_FakeExecutor.submit()` fires
for any submitted callable, so `assertIn("judge-dispatch", events)` and
the ordering assertions all pass in the reproduction above — driven
entirely by `_core_executor`'s and `_board_snapshot_executor`'s unrelated
submissions, exactly the defect shape the docstring itself correctly
diagnoses for the *old* version of this test and claims to have fixed for
the new one. The class remains exactly as vacuous as described, under an
updated description that says otherwise.

This is a real defect in the round's own self-audit, not a nitpick: a
reader relying on `SkillJudgeOverlapOrderingTest` passing green as
evidence "the async invariant is tested" is relying on a test that would
pass identically whether or not the invariant held, for the same reason
the pre-round-3 version did, per the live reproduction above. The actual
invariant (matcher never called synchronously) is genuinely true (per the
`judge-ran called: False` result above) and genuinely covered elsewhere —
indirectly, via two other tests on PR #3234's branch this session read:
one asserting the directive text never mentions the matched skill name
and the mount list stays empty when a match exists, and one asserting the
ledger always logs `skill_judge_outcome="pending"` even when the stubbed
matcher is made to return a hit. So the codebase is not undertested for
this invariant overall — but the specific class named in round 3's own
"what did not work" as having been "retired and replaced" was not, and
still isn't.

Grade: **Incorrect** (the record's remediation claim, not the underlying
code behavior, which is fine).

## Why

Two consecutive prior rounds (PR #3234's own Round 1/Round 2, PR #3240's
independent verification) specified the async design without attempting
it; PR #3250's round-3 verification named this an effort problem and
instructed: build it or name what failed. Round 3 built it. This
verification's job is to check the build against its own claims with
independently re-derived numbers rather than trust the record's prose —
per this task's own framing, a number this large deserves independent
derivation rather than confirmation. Re-derivation surfaced one false
claim (the test-retirement item, section 7) that a prose-only read would
have missed, since the class name legitimately does still appear with an
updated, plausible-sounding docstring.

## Upstream basis

canonical: `gh pr view 3234` (round 3 tip
`63d1d748d0dbbae18448dc50bf11248646eee977`), `gh pr view 3240`, `gh pr
view 3242`, `gh pr view 3250` — all read in full this session. `git
worktree add /tmp/pr3234-review pr-3234-check` (PR #3234's branch), `git
worktree add /tmp/main-baseline main` — both used for direct code
reading, live test execution, and independent measurement this session;
both removed (`git worktree remove --force`) before this record was
written.

## Open findings

1. **Test-retirement claim is false** (Incorrect, section 7 above).
   Resolution path: the missing invariant test would assert, e.g.,
   `assertFalse(matcher_called)` via a spy on
   `_cross_family_skill_matches_with_consult` directly, not via a generic
   `ThreadPoolExecutor` fake shared with unrelated submissions — or
   delete the class outright since its invariant is already covered
   indirectly by the two other tests named in section 7. A future round
   should fix the test itself, not just its docstring, and should not
   claim a fix that only touched prose.

2. **Reactive-delivery uptake is genuinely unmeasured, and the directive
   text's "check once" framing likely undersells how often it will be
   too early** (Surface, section 3 above). Both round 3's own record and
   this verification agree this is open; resolution path is spawning
   real worker sessions and observing Skill-tool invocation against real
   marker-arrival timing, as round 3's own "Next steps" already names.

3. **The "0.6s after" headline has zero real-production corroboration
   yet** (Surface, section 1 above) — inherent to reviewing a pre-merge
   branch, not fixable by this verification round; resolution path is
   simply merging and letting real `dispatch_ready_perf` events
   accumulate, then re-running `measure_skill_judge.py --report`.

## Acceptance checks, this round (independently re-run, fresh worktree, PR #3234 branch)

acceptance: `python3 -m pytest tests/test_issue_3230_skill_judge_cost.py -q` -- result:
```
17 passed in 0.99s
```
acceptance: `python3 scripts/issue-3230/measure_skill_judge.py --report` -- result (excerpt):
```
n=38 min=8.295s max=56.653s mean=21.627s median=19.733s p90=31.144s
outcome_ok=True: 38/38
no dispatch_ready_perf events found -- this event is new this round...
```
acceptance (must-not): `python3 scripts/issue-3186/measure_cross_family.py --report` -- result:
```
log files scanned: 165
bootstrap_timing lines found: 30
spawns with total > 1s: n=4 cross_family=6.328s total=20.666s share=30.6%
```
exit 0, still finds its data.

acceptance: `python3 -m pytest tests/test_issue_3230_cross_family_delivery.py -q` -- result:
```
9 passed in 0.83s
```

acceptance: `python3 -m pytest -q` (full suite, this session, independent
run, PR #3234 branch) -- result:
```
4 failed, 1446 passed, 3 xfailed, 2 warnings in 44.44s
```
Same 4 failures as round 3's own record and PR #3250's baseline: path
`on-the-record/hooks/test_hook_classification.py` x2, path
`harness/fixture-operator-experience/test_flow.py::test_first_contact_fires_once_per_workspace`,
path `on-the-record/checks/test_macos_bash32_compat.py::test_current_head_is_clean`
(all three paths untracked in this branch's own working tree; those
files exist only on PR #3234's branch and on `main`, checked below).

derived: went one step further than round 3's own `git stash` check —
verified all 4 against a separate `main`-branch worktree (`git worktree
add /tmp/main-baseline main`, tip `a4ea9418`, this session), not just PR
#3234's own prior commit. acceptance: `python3 -m pytest
on-the-record/hooks/test_hook_classification.py
harness/fixture-operator-experience/test_flow.py
on-the-record/checks/test_macos_bash32_compat.py -q` (on `main`, this
session) -- result:
```
2 failed, 12 passed in 0.90s
```
`test_macos_bash32_compat` and `test_first_contact_fires_once_per_workspace`
fail identically on `main` (same root causes: `amendment_channel.py`'s
pre-existing `/proc` dependency from issue #3129, and the
fixture-operator-experience flow gap) — genuinely pre-existing, unrelated
to this PR. The two `test_hook_classification.py` failures do not
reproduce on `main` at all (6 passed, 0 failed for that file alone on
main). derived: traced this to branch staleness, not a round-3
regression — `git merge-base HEAD main` (PR #3234 branch vs main, this
session) followed by `git diff <merge-base>..main --
on-the-record/hooks/hooks.json on-the-record/hooks/hook_classification.json`
shows PR #3234's branch predates an unrelated `main` commit (issue #3231)
that added a `hook_classification.json` entry for `amends-landing-apply.sh`
plus two new hooks; the PR branch's own `hooks.json`/
`hook_classification.json` are simply older than what those tests now
expect on `main`. Unrelated to this round's diff either way — correctly
excluded from the 4-failure baseline by every round including this one.

## Skill verdicts

skill-verdict: adversarial-review — applied: invoked; this entire
verification is that skill's protocol — read PR #3234/#3240/#3242/#3250
and round 3's own record cold, then independently re-derived every
numeric claim from a fresh worktree rather than trusting the PR's prose,
which is what surfaced the false test-retirement claim in section 7.
skill-verdict: experiment-trust — applied: invoked; the headline
"18.8s -> 0.6s" claim is exactly the kind of large, decision-driving
number this skill exists to gate before trusting it — checked whether
"before" and "after" were measured the same way (they are not: dozens of
real production samples vs. a synthetic n=3 harness each round) and
reported the asymmetry explicitly (section 1) rather than accepting a
single clean comparison at face value. Not a formal A/B/SRM check (no
randomized variant assignment exists here), but the skill's core
discipline — distrust a big win until its measurement provenance is
verified — applied directly.
skill-verdict: silent-failure-audit — applied: invoked; enumerated every
error-handling path in `_deliver_cross_family_amendment()` and
`_launch_cross_family_delivery()` (matcher exception, empty match,
unresolvable repo, marker-write failure, `Popen` `OSError`) against both
their tests and one live, unmocked, end-to-end run of the real detached
subprocess (section 4) — classified every branch Handled (caught,
logged, never raised), none Silently Absorbed, none left Unreachable in
this session's own testing.
other mounted skills: not triggered (implementation-blueprint,
technical-feasibility-spike-report, product-discovery-guardrail-metrics —
this session verified a build, it did not build or plan one;
work-in-english/implementation-audit riders from spawn-time skill
configuration are reflected in this record's own English-language
authorship, not separately invoked).

## Next steps

loop_state is terminal (`reported`) for this verify-record. The open
findings above (test-retirement fix, uptake measurement, post-merge
production corroboration of the 0.6s figure) are the natural next round's
work, not this one's.
