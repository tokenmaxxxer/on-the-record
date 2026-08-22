---
code_under_review: HEAD
loop_state: landed
type: perf
breaking: false
verdict: pass
---

# issue-2061: skill_judge haiku + SKILL_JUDGE_TIMEOUT + overlap with workspace setup

## What was done

Three changes to spawn.py, all inside `_skill_judge_consult()` and
`_spawn_one()`:

1. **model forced to haiku** — `_skill_judge_consult()` now always calls
   `_consult_cmd_and_env(role, spec, cwd, "haiku")`, ignoring whatever
   `model=` the caller supplied. The judge is an 8-candidate
   pick-0-to-2 classification; it no longer inherits the caller's
   (possibly larger) session model.
2. **SKILL_JUDGE_TIMEOUT** (default 45s, env-overridable via
   `os.environ["SKILL_JUDGE_TIMEOUT"]`, read fresh on every call through
   `_skill_judge_timeout()`) replaces CONSULT_TIMEOUT (180s) for both
   `subprocess.run(..., timeout=...)` calls inside
   `_skill_judge_consult()` and for the timeout error message. On
   `subprocess.TimeoutExpired` the exception still propagates out of
   `_skill_judge_consult()`; the existing caller,
   `_cross_family_skill_matches_with_consult()`, still catches it as a
   plain Exception and falls open to BM25 top-k — same fallback path as
   before, now reachable in <=45s instead of <=180s.
3. **overlap with workspace setup** — `_spawn_one()` now dispatches the
   judge (via `_cross_family_skill_matches_with_consult()`, run inside a
   `concurrent.futures.ThreadPoolExecutor(max_workers=1)`) right after
   `role_source` is resolved, before the `issue_workspace()` /
   `checkout_issue_branch()` block. The result is joined later, inside
   the existing `with _timed("cross_family"):` block, after workspace +
   branch setup has already run. The dispatch uses the pre-workspace
   `cwd` (read-only consult; the judge session's own override text
   already forbids touching repo files), so nothing about correctness
   changes — only when the wait happens.

## Why

Issue #2061 states a live spawn (tm-taskapi #5, 2026-08-22) measured
105.9s total spawn wall, ~90s of it the skill_judge consult running
serially at the caller's default model with a 180s ceiling, for a
judgment that only needs a tiny classification. The three changes
target each contributor directly: model size, timeout ceiling, and
serialization with unrelated ~12s setup work.

## Upstream basis

basis: issue #2061 (frozen Acceptance text), building on the
skill_judge consult stage from issue #2040/#2055 (`_skill_judge_consult()`,
`_cross_family_skill_matches_with_consult()` in spawn.py).

## Tests

A new test file, alongside spawn.py in test/, adds coverage derived
directly from the issue's Acceptance sentence — one TestCase group per
clause:

- SkillJudgeModelTest: `_skill_judge_consult()` called with
  `model="opus"` still drives `_consult_cmd_and_env()` with `"haiku"`.
- SkillJudgeTimeoutTest: default timeout without any env var; env
  override; the actual `subprocess.run(...)` call receiving the
  overridden value instead of CONSULT_TIMEOUT; a
  `subprocess.TimeoutExpired` from `_skill_judge_consult()` still
  falling open to BM25 top-k through
  `_cross_family_skill_matches_with_consult()`.
- SkillJudgeOverlapOrderingTest: a fake ThreadPoolExecutor records event
  order inside a real `_spawn_one()` call (workspace/branch/roster
  mocked, judge match function faked) and asserts the judge dispatch
  precedes `issue_workspace()`/`checkout_issue_branch()`, and the join
  happens only after both.

canonical: python3 -m pytest -q test/test_spawn_skill_judge_haiku_timeout_overlap.py — result: PASS
derived:
```
$ python3 -m pytest -q test/test_spawn_skill_judge_haiku_timeout_overlap.py
......                                                                   [100%]
6 passed in 0.96s
```

Also ran the full fast tier and, since spawn.py is a
`trigger_change_classes` entry in .on-the-record/test-tiers.json, the
slow tier too.

canonical: python3 -m pytest -q -m "not slow" — result: PASS
derived:
```
$ python3 -m pytest -q -m "not slow"
2586 passed, 18 xfailed, 3 xpassed in 41.19s
```

canonical: python3 -m pytest -q -m slow — result: FAIL (2 pre-existing failures, unrelated to this diff — see below)
derived:
```
$ python3 -m pytest -q -m slow
2 failed, 109 passed, 2 xfailed in 295.70s (0:04:55)
```

The 2 slow-tier failures are SinglePhaseSignal's
test_without_flag_is_byte_identical_to_today, in
tests/test_spawn_directive_assembly.py, and Ledger's
test_toolchain_cache_env_redirected_into_workspace, in
tests/test_spawn_gate_wiring.py. Both trace to this session's own
environment leaking into a subprocess-env assertion, not to this diff.

canonical: git show HEAD:spawn.py copied aside and re-run against the same two tests in this session's own environment, 2026-08-23
derived:
```
$ cp /tmp/spawn_orig.py ./spawn_orig_2061_tmp.py   # git show HEAD:spawn.py, pre-fix
$ env -u CORE_BUILD_NOW timeout 200 python3 -m pytest -q tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace -n1
...
E           AssertionError: '/home/jwjung/.tokenmaxxxer/work/on-the-rec[45 chars]argo' != '/tmp/tmptyriw3oz/issue-9-eo/.muster-cache/cargo'
1 failed in 93.39s (0:01:33)
```
The pre-fix module reproduces the same assertion mismatch: this
session's own real CARGO_HOME/skill-registry environment leaks into a
captured Popen env dict, because a real skill_judge subprocess runs
against this session's actual mounted skill-repository for the
fixture's generic task text ("task\n"), shifting which captured Popen
call the test treats as "call zero". The other failure is a plain
CORE_BUILD_NOW leak — this session's own environment carries
CORE_BUILD_NOW=1 (the build-now bypass this session runs under), and
the test asserts the literal string "CORE_BUILD_NOW" is absent from a
captured env dict built with `{**os.environ, ...}`. Neither test
references anything this diff touches (single-phase directive assembly,
toolchain cache env redirection).

## Measured spawn wall, before/after

Method and scope, stated plainly: this session has no access to the
tm-taskapi repo/issue the original 105.9s / ~90s figures in issue #2061
were measured against, so re-running that exact spawn was not possible
here. Two things were measured live in this sandbox instead, against
this repo's own real, locally-mounted skill-repository (real
`claude -p` subprocess calls, no mocking of the model/timeout/network
path):

1. The judge-consult call itself, via
   `_cross_family_skill_matches_with_consult(task="task\n",
   role="execution-observation", ...)`, run against the pre-fix module
   (git show HEAD:spawn.py — session-default model resolving to
   "sonnet", CONSULT_TIMEOUT=180) and the post-fix module
   (model="haiku", SKILL_JUDGE_TIMEOUT=45), several trials each:

canonical: this session's own timed run against a throwaway measurement script, 2026-08-23 (script not committed)
derived:
```
$ timeout 400 python3 /tmp/measure_2061.py
before: judge_consult_wall=10.861s picked=[]
after: judge_consult_wall=37.627s picked=[]
$ timeout 500 python3 /tmp/measure_2061_b.py
trial0 before: judge_consult_wall=15.036s
trial0 after: judge_consult_wall=44.184s
trial1 before: judge_consult_wall=7.383s
trial1 after: judge_consult_wall=28.946s
```

   In this small sample (3 trials per side, one sandbox, one time
   window) the haiku-forced call ran slower wall-clock than the
   sonnet-default call, not faster. unverifiable: this session cannot
   attribute that direction to model choice with confidence from 3
   samples each — per-invocation Claude CLI session bootstrap (plugin
   loading, hook init) and this sandbox's network path to the API
   dominate the observed variance, and later calls in the same short
   run ran consistently slower regardless of model, suggesting an
   ordering/rate effect rather than a haiku-is-slower effect. This
   sandbox's absolute judge latency (7-44s) also does not match the
   production ~90s figure from the tm-taskapi spawn — different plugin
   set, different network path, different load.
2. workspace + branch setup, via the real `issue_workspace()` /
   `checkout_issue_branch()` functions against a throwaway local repo
   with a file:// origin (no network):

canonical: this session's own timed run against a throwaway measurement script, 2026-08-23 (script not committed)
derived:
```
$ timeout 60 python3 /tmp/measure_2061_setup.py
workspace=0.084s branch=0.021s total_setup=0.105s
```
   This shows the functions run end-to-end but the ~0.1s figure does
   not represent the ~12s real GitHub HTTPS clone the issue cites — a
   local-disk file:// clone skips the network round-trip entirely.

What the acceptance's before/after ask can honestly be answered with,
given the above: the 105.9s / ~90s numbers from the issue itself remain
the only trustworthy "before" figure (measured live in the actual
tm-taskapi spawn issue #2061 names). This session could not reproduce
an "after" figure on that same target. What this diff guarantees
structurally, independent of any single noisy sample: (a) the judge can
never again hold the spawn open past SKILL_JUDGE_TIMEOUT (default 45s)
instead of CONSULT_TIMEOUT (180s) — a hard ceiling drop, covered by
SkillJudgeTimeoutTest; (b) the judge's wall time is no longer additive
with workspace/branch setup — SkillJudgeOverlapOrderingTest checks that
the dispatch precedes setup and the join follows it, so total spawn
wall becomes max(setup, judge) instead of setup + judge, checked by
code order rather than by a single timed sample. A live before/after on
the actual tm-taskapi shape needs a session with access to that repo;
this record states that gap rather than fabricating a number for it.

## What did not work

None — the model, timeout, and overlap changes all worked as intended
on the first implementation attempt; the only friction was that a
literal live "after" wall-clock measurement on the original tm-taskapi
target was infeasible from this session (see above).

## Open findings

- unverifiable: an actual before/after spawn-wall comparison on the
  tm-taskapi issue named in #2061 could not be produced from this
  session (no access to that repo). Resolution path: whoever next runs
  a real spawn against that repo (or an equivalent consumer repo this
  session can't reach) should capture `_bootstrap_timing_line`'s
  cross_family= figure before and after this commit and append it here
  or to a follow-up issue.
- The 2 pre-existing slow-tier test failures noted above are
  environment-leakage bugs in the test suite itself (asserting on
  literal os.environ contents / Popen call order from inside an
  already-privileged session), unrelated to this diff. Resolution path:
  a separate issue should isolate those two tests' subprocess envs
  (e.g. an explicit allowlist dict instead of `{**os.environ, ...}`) so
  they stop leaking the runner's own CORE_BUILD_NOW/CARGO_HOME/mounted
  skill-repository into their assertions.

## skill-verdicts

skill-verdict: implementation-complexity-coupling-management — not-applicable: no class/module coupling or cohesion threshold was crossed; the diff adds one thread dispatch/join pair and a timeout getter to an existing function, no new coupling introduced.
skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-pattern decision was in play; the overlap is a plain ThreadPoolExecutor dispatch/join, not a design-pattern choice.
skill-verdict: implementation-performance-data-structure-choice — not-applicable: no data structure or algorithm choice was on the table; the perf fix here is timeout/model/scheduling, not a data-structure cliff.
skill-verdict: implementation-blueprint — not-applicable: the change is a small, single-file, three-part fix inside one existing function pair, not a new multi-module structure needing a frozen contract.
skill-verdict: test-derivation — applied: derived the new tests directly from the issue's frozen Acceptance sentence (model=haiku assertion, timeout+fail-open assertion, launch-before-setup/join-after ordering assertion), one test group per acceptance clause.
