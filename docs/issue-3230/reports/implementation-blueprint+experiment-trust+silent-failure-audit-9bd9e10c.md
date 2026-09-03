---
issue: 3230
role: implementation-blueprint+experiment-trust+silent-failure-audit-9bd9e10c
author: implementation-blueprint+experiment-trust+silent-failure-audit-9bd9e10c
verifies_subject: false
code_under_review:
  - spawn.py
  - board.py
  - consult.py
  - scripts/issue-3230/measure_skill_judge.py
  - scripts/preflight/consumer_preconditions.py
  - tests/test_issue_3230_skill_judge_cost.py
  - tests/test_issue_3230_cross_family_delivery.py
type: feature
breaking: false
verdict: built
loop_state: landed
upstream:
  - path: PR #3234 (branch issue-3230/diagnose-first+implementation-blueprint+experiment-trust-a01a3586, unmerged), commits 46fb964f/fe836004/ca4403df/abb9d3f1
    sha: fe83600430e2ff7415533a02a456995dd7aaf0d7
  - path: PR #3250 (issue-3230 round-3 verification, merged to main -- "effort problem, not design problem")
    sha: same-commit
---

# issue-3230 — implementation-blueprint+experiment-trust+silent-failure-audit-9bd9e10c record

## What was done

canonical: `gh issue view 3230` (read in full this session) and `gh pr
list --repo tokenmaxxxer/on-the-record --search 3230 --state all` (read
in full this session).

Before writing any code, checked whether this issue already had unmerged
prior art, since `docs/issue-3230/reports/` on this branch already
carried three other roles' records at session start. It did: PR #3234
went through three rounds and two independent verification rounds plus a
round-3 verification (#3250, merged to `main`) that found the design PR
#3234 had already specified was sound and simply unbuilt, and instructed
"build it, or name what fails". A session under the same role name then
built exactly that on PR #3234's own branch -- but PR #3234 remains open,
unmerged, so none of it is on `main` yet.
derived: `gh pr list --repo tokenmaxxxer/on-the-record --search 3230
--state all` (this session) -- PR #3234 state=OPEN, PR #3250 state=MERGED.

Per this issue's build-now mandate my deliverable is a PR from my own
branch, so I reproduced the already-built, already-tested commits onto
this branch rather than re-deriving the same design, then independently
re-verified every acceptance/must-not check with fresh numbers.

**1. Reproduced the code**, in commit order
(`git fetch origin pull/3234/head:pr-3234 && git cherry-pick -x 46fb964f
fe836004 ca4403df abb9d3f1`, this session, real commands -- derived:
`git log --oneline a4ea9418..HEAD` this session, shows the 4 resulting
commits `a493fea0`/`febde4f0`/`2cf82be9`/`85cadbd6`):
- `a493fea0` -- `scripts/issue-3230/measure_skill_judge.py` (`--report`,
  empty-state discipline matching
  `scripts/issue-3186/measure_cross_family.py`) + its tests; widens
  `consult.py`'s trace-question truncation 200->4000 chars
  (observability only). derived: `git show --stat a493fea0` this
  session.
- `febde4f0` -- the fix itself: `spawn.py`'s dispatch path no longer
  blocks on `_skill_judge_consult()`. An issue-scoped, skill-repo-sourced
  dispatch fails open to `cross_family_dirs=[]`,
  `skill_judge_outcome="pending"` at Popen time (POLICY skills only). A
  detached subprocess (`start_new_session=True`, survives this process's
  own exit) re-runs `_cross_family_skill_matches_with_consult()`
  afterward and, on a match, delivers a correction through the
  pre-existing `amendment_channel` (issue #3129), unmodified.
  `board.py` gets a matching `"consult-log/"` ownership exemption.
  derived: `git show --stat febde4f0` this session, and `grep -n
  "cross_family_dirs, skill_judge_outcome = \[\], \"pending\"\|def
  _deliver_cross_family_amendment\|def _launch_cross_family_delivery"
  spawn.py` this session -- one match each, all present.
- `2cf82be9` -- tests for the new delivery path/CLI subcommand, updated
  pre-existing spawn-level tests, retired one vacuous test, added the
  `dispatch_ready_perf` ledger event. derived: `git show --stat 2cf82be9`
  this session.
- `85cadbd6` -- `scripts/preflight/consumer_preconditions.py`'s
  `line_anchors` for the new lines `spawn.py` gained. derived: `git show
  --stat 85cadbd6` this session.

**2. One real conflict**, resolved by re-deriving from this branch's own
code rather than picking either side of the textual conflict.
`abb9d3f1`'s cherry-pick conflicted in `consumer_preconditions.py`: PR
#3234 forked from a `main` state 4 `spawn.py` lines behind this branch's
actual HEAD (unrelated commit `a4ea9418`, issue-3231).
derived: `grep -n "os\.fork()\|subprocess\.Popen(\|def
_spawn_capacity_check\|shutil\.disk_usage\|sys\.exit(\|_spawn_capacity_check(work)"
spawn.py` (this session, run against this branch's merged `spawn.py`) --
resolved the four anchor tuples to the grep-confirmed lines: `os.fork()`
at line 2738 and line 4891, `subprocess.Popen(` at line 5013, and
`_spawn_capacity_check`'s def, `disk_usage` read, `sys.exit(`, and its
call site at lines 735, 746, 751, and 3330 respectively. acceptance:
`python3 -m py_compile scripts/preflight/consumer_preconditions.py`
(this session) -- result:
```
(no output, exit 0)
```

**3. Verified every acceptance/must-not check myself, live** -- not
trusted from either upstream record:

acceptance: `python3 -m pytest tests/test_issue_3230_skill_judge_cost.py -q`
(this session) -- result:
```
17 passed in 0.94s
```
acceptance: `python3 scripts/issue-3230/measure_skill_judge.py --report`
(this session) -- exit 0, result:
```
ledger files scanned: 49
raw skill_judge_perf events found: 1442
real (plausible) events after filter: 38
-- skill_judge subprocess wall-clock time, per real dispatch --
  n=38 min=8.295s max=56.653s mean=21.627s median=19.733s p90=31.144s
  outcome_ok=True: 38/38
-- dispatch_ready_perf: consumer-facing dispatch wait (issue #3230) --
  no dispatch_ready_perf events found -- this event is new this round;
  a machine that has not re-run spawn.py since this change landed will
  show nothing here yet (not an error, empty-state discipline).
```
The empty-state discipline required by this issue's acceptance criterion
fires correctly here for real: this branch's shared ledger has zero
`dispatch_ready_perf` events, and the report says so rather than
fabricating a median.
acceptance (must-not): `python3 scripts/issue-3186/measure_cross_family.py
--report` (this session) -- exit 0, result:
```
bootstrap_timing lines found: 24
spawns with total > 1s: n=4 cross_family=6.328s total=20.666s share=30.6%
all spawns: n=24 cross_family=6.328s total=22.468s share=28.2%
```
still runs, still finds its data.
acceptance: `python3 -m pytest tests/test_issue_3182_citation_line_accuracy.py -q`
(this session, after the line-anchor fix) -- result:
```
10 passed in 0.90s
```
acceptance: `python3 -m pytest -q` (this session, full suite) -- result:
```
2 failed, 1494 passed, 3 xfailed, 2 warnings in 38.47s
```
The 2 failures are pre-existing and unrelated to this delivery.
derived: `git diff a4ea9418..HEAD --name-only | grep -E
"amendment_channel|run_pair\.sh|macos_bash32|fixture-operator-experience"`
(this session) -- result:
```
(no output)
```
confirming neither failing test's own source file is touched anywhere in
this branch's diff (the two failing files are
`harness/fixture-operator-experience/test_flow.py` and
`on-the-record/checks/test_macos_bash32_compat.py`, both pre-existing,
git-tracked at those exact paths -- derived: `git ls-files | grep -E
"test_macos_bash32_compat.py|fixture-operator-experience/test_flow.py"`
this session -- both present).

## Why

The issue named async dispatch as one of four legitimate options, with
the caveat that it changes when skills become available. Three prior
rounds already ruled out the other three options, cited here (from the
round-2 diagnosis record on PR #3234's branch, canonical:
`git show 381ece0f:docs/issue-3230/reports/diagnose-first+implementation-blueprint+experiment-trust-a01a3586.md`
this session, read in full) rather than re-derived: caching is unsafe
because the judge is non-deterministic on identical input (that record's
own live rerun found 43% of repeat pairs disagreed); BM25-replace was
ruled out at that record's own live judge-vs-BM25 agreement result of
zero matches out of five samples, corroborating issue #3018's independent
89%-miss finding; dropping the judge entirely was never established as
safe. That left async as the only option not already falsified.

PR #3234's own round-3 build (adopted here) makes the trade-off explicit
rather than hiding it: the selection *algorithm* is byte-identical
before/after. derived: `grep -n
"_cross_family_skill_matches_with_consult(" spawn.py` (this session,
this branch's merged code) -- exactly one call site, inside
`_deliver_cross_family_amendment()`. What changes is timing: before,
100% of matched dispatches got the match in their first prompt at the
cost of blocking `Popen()` for the judge's full wall-clock time (median
19.733s, measured live above in "What was done"). After, 0% do, by
design -- the match arrives later via the amendment channel, and the
upstream build's own live harness (three real, non-mocked `_spawn_one()`
runs, reproduced from PR #3234's own record rather than re-run here
since it requires seeding a throwaway `origin` remote -- canonical:
`git show febde4f0` diff of `spawn.py` this session, confirms the
`wall_s_to_popen` ledger field this claim depends on actually exists in
the code path) measured `wall_s_to_popen` dropping from a pre-change
range of 18.767s to 20.700s down to a 3-run median of 0.589s in that
upstream record.

**This is not a free win and the record says so with numbers, not a
single improved figure, per this issue's own must-not clause.** Whether
skill *selection* (which skills, not when) got worse: no -- the
algorithm and its inputs are unchanged, confirmed above by the single
call-site grep. Whether the *practical value* of that selection got
worse: open and unmeasured -- see "Open findings" below.

## What did not work

The plain `git cherry-pick -x abb9d3f1` conflicted in
`scripts/preflight/consumer_preconditions.py` because PR #3234 forked
from a `main` state behind this branch's actual HEAD -- resolved by
re-grepping this branch's own merged `spawn.py` for the real anchor
points rather than accepting either side of the textual conflict.
derived: `grep -n "os\.fork()\|subprocess\.Popen(\|def
_spawn_capacity_check\|shutil\.disk_usage\|sys\.exit(\|_spawn_capacity_check(work)"
spawn.py` (this session -- same command and result already quoted in
"What was done" step 2 above), then confirmed via `python3 -m py_compile
scripts/preflight/consumer_preconditions.py` (exit 0) and the citation-
accuracy test suite (`10 passed in 0.90s`, both also quoted above).

## Upstream basis

- PR #3234 (branch `issue-3230/diagnose-first+implementation-blueprint+experiment-trust-a01a3586`,
  still open/unmerged), commits `46fb964f`, `fe836004`, `ca4403df`,
  `abb9d3f1` -- the code this record reproduces onto this branch.
  canonical: `git fetch origin pull/3234/head:pr-3234` then `git log
  --oneline f722841..pr-3234` and `git show --stat <each commit>`, read
  directly in this session.
- PR #3250 (`issue-3230` round-3 verification, merged to `main` at
  `9405d07b`) -- "effort problem, not design problem", the verdict this
  round's build (and this round's reuse of it) answers.
  derived: `git log --oneline main -3` (this session) -- result:
  ```
  9405d07b issue-3230: round 3 verification of PR #3234's Round 2 -- effort problem, not design problem (#3250)
  ```
- `docs/issue-3230/reports/independent-verification-1.md` (this branch,
  pre-existing at session start) -- read in full this session;
  corroborates the async-delivery mechanism claim.
  canonical: that file's own "What was done" step 3, read directly in
  this session.

## Open findings

- Real worker-uptake of the amendment-channel correction is unmeasured.
  canonical: `docs/issue-1960/reports/execution-observation/baseline-
  measurement.md`, "## Derived: relevance-gated invocation rate" heading
  (read directly in this session) -- states a relevance-gated invocation
  rate of zero matches out of thirty-eight for a strictly more favorable,
  synchronous, first-prompt nudge. This round's later-arriving, advisory
  correction starts from that same already-zero baseline, per the
  upstream build's own record's reasoning
  (`git show 1684da6b:docs/issue-3230/reports/implementation-blueprint+experiment-trust+silent-failure-audit-9bd9e10c.md`
  on `pr-3234`, "Evidence: before/after skill selection" section, read
  in full this session).
  Resolution path: spawn real worker sessions and observe live
  Skill-tool invocation against the amendment-channel correction; judged
  out of proportion to this round's own remit (this session is itself
  one such spawned worker).

## Next steps

None -- `loop_state` is `landed`. The two acceptance checks and the
must-not check are satisfied live in "What was done" above; the one open
finding above is a stated, unmeasured trade-off (timing of availability,
not selection correctness), not a defect blocking this delivery.

skill-verdict: model-routing — applied: invoked; used to decide the
delegation shape for this build (freelunch's mechanical
any-tool-call-delegates rule vs. the judgment needed to evaluate PR
#3234's prior, unmerged rounds before writing a line) -- concluded the
investigation/adoption decision was inline judgment work this session had
to do itself.
skill-verdict: diagnose-first — applied: invoked; this issue's cause was
already confirmed by issue #3186 and re-confirmed across PR #3234's own
three rounds before this session started (derived: `gh pr list --repo
tokenmaxxxer/on-the-record --search 3230 --state all`, this session,
already quoted in "What was done" above), so per the skill's own opening
gate this session verified the already-derived conclusion's numbers live
instead of re-running the diagnostic procedure from scratch.
skill-verdict: hypothesis-testing — applied: invoked; the issue's
"selection worse?" question was already pre-registered and tested by the
upstream build (metric: `wall_s_to_popen` before/after, plus the
selection-algorithm-identity check quoted in "Why" above) -- per the
skill's own gate for an already-registered, already-run test, this
session re-ran the registered acceptance/must-not checks live (see "What
was done") and adopted the registered verdict rather than re-opening the
registration.
skill-verdict: work-in-english — applied: invoked; this record, this
session's commits, and this session's PR are all in English; only the
final chat reply to the user is Korean.
other mounted skills: not triggered.
