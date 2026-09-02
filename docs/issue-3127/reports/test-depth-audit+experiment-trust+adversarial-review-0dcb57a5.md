---
issue: 3127
role: test-depth-audit+experiment-trust+adversarial-review-0dcb57a5
author: test-depth-audit+experiment-trust+adversarial-review-0dcb57a5
skills: test-depth-audit (skill-repository(c05de12)), experiment-trust (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent, builder-blind verification of PR #3131's repair round 2 (commits 0db89918, 411a2140, c928cba4) against PR #3158's three open findings
loop_state: landed
code_under_review: c928cba466a25c0cbb2220eecb6603d5072f0feb
type: defect-verification-record
breaking: false
verdict: All three of PR #3158's findings are Present -- each independently
  reproduced this session by running the code, not by reading the repair
  record's own claims. (1) Reachability -- reverted the module-level
  import spawn as _spawn_mod and reproduced the exact original NameError;
  restored it and independently called run_pair() with only
  subprocess.run stubbed at the python3 spawn.py ... boundary (not
  arm_workspace_dir, per the round's own must-not) -- it reached
  gate_pair_on_h1() and evaluate_pair_blind() without raising. All 11
  arm_workspace_dir references in PR-3131-branch:tests/
  test_issue_3127_run_pair.py classified (derived: grep -c below): 3 are
  mock.patch.object calls confined to round 1's pre-existing RunPairTest
  class (intentionally unchanged, still Mock-Dominated on that seam by
  design); the other 8 are docstring/comment prose, not mocks; the
  round's own 2 new RunPairRealReachabilityTest tests do not mock it.
  (2) Skeleton -- regenerated the not-yet-run results skeleton via
  --emit-not-executed and diffed byte-for-byte against the committed
  file: zero diff; both arms carry wall_clock_to_pr_open_s,
  wall_clock_to_landed_s, and landing_measurement_status. (3) Dry-run
  parity -- ran --dry-run live, confirmed the printed watch line carries
  -C <sandbox-repo-not-yet-chosen> matching execute_arm()'s real spawn.py
  watch call; mutation-removed the -C addition and confirmed
  RenderDryRunMatchesExecuteArmTest fails on the original defect shape.
  Decisive question: a non-dry --execute run now DOES proceed past
  workspace setup for both arms, gate on H1, and score blind H2 -- the
  crash this round fixed is gone. But it would NOT emit a results JSON
  with every pre-registration field: build_execute_results() has no code
  path for verification-round count/defect counts, token cost, or BM25
  selection position (fields (c)/(d)) -- these remain computed only
  inside the still-separate emit_not_executed_results()/dead
  collect_metrics() -- and wall-clock-to-landed-PR is permanently None by
  design. This gap was already open in PR #3158 and explicitly out of
  scope for this round; not newly introduced or newly closed here.
upstream:
  - path: docs/issue-3127/reports/experiment-trust+adversarial-review+test-depth-audit-88b28bc4.md
    sha: same-commit  # PR #3158, already tracked on this branch; source of the three findings re-graded here
  - path: docs/issue-3127/reports/implementation-blueprint+test-depth-audit+silent-failure-audit-4cf4e602.md
    sha: same-commit  # repair round 2's own record, already tracked on this branch, unmodified
  - path: PR-3131-branch:scripts/issue-3127/run_consumer_pair.py
    sha: c928cba466a25c0cbb2220eecb6603d5072f0feb  # untracked on this session's own branch; lives only on PR #3131's branch, read/exercised via git worktree
  - path: PR-3131-branch:tests/test_issue_3127_run_pair.py
    sha: c928cba466a25c0cbb2220eecb6603d5072f0feb  # untracked here, same basis
  - path: PR-3131-branch:tests/test_issue_3127_h1_and_scoring.py
    sha: c928cba466a25c0cbb2220eecb6603d5072f0feb  # untracked here, same basis
  - path: PR-3131-branch:tests/test_issue_3127_run_consumer_pair.py
    sha: c928cba466a25c0cbb2220eecb6603d5072f0feb  # untracked here, same basis
  - path: PR-3131-branch:docs/issue-3127/decisions/pre-registration.md
    sha: 84226988e930981b02d00abd30e22c83100e875f  # untracked here, unmodified since this sha
  - path: PR-3131-branch:docs/issue-3127/_assets/consumer-path-results.json
    sha: 9c9801cd470129580de54b78a32abc30875de90e  # untracked here, unmodified by this round -- confirmed by regenerating and diffing this session
---

# issue-3127 — test-depth-audit+experiment-trust+adversarial-review-0dcb57a5 record

## What was done

Independent, builder-blind verification of repair round 2 on PR #3131's
own branch (`issue-3127/experiment-trust+product-discovery-hypothesis-
preregistration+implementation-blueprint+silent-failure-audit-4eda8e00`,
head `c928cba4` -- three commits `0db89918`, `411a2140`, `c928cba4`), which
claims to close the three findings PR #3158's independent verification
left open. Per this task's spawning brief, graded each item by running
the harness this session, not by citing the repair record's own claims.

canonical: `git show 17751209:docs/issue-3127/reports/experiment-trust+
adversarial-review+test-depth-audit-88b28bc4.md` (PR #3158), read this
session -- the three findings: `PR-3131-branch:scripts/issue-3127/
run_consumer_pair.py`'s `run_pair()` raised `NameError: name
'_spawn_mod' is not defined` in `arm_workspace_dir()` before ever
reaching `gate_pair_on_h1()` or `evaluate_pair_blind()`; all three
`RunPairTest` tests in `PR-3131-branch:tests/test_issue_3127_run_pair.py`
passed only because each mocked exactly that broken function; and
`PR-3131-branch:docs/issue-3127/_assets/consumer-path-results.json` was
never regenerated by round 1's repair, so it never carried the corrected
wall-clock schema.

canonical: `git show c3fc6e13:docs/issue-3127/reports/implementation-
blueprint+test-depth-audit+silent-failure-audit-4cf4e602.md` (repair
round 2's own record, already on this branch), read this session -- the
round's own claims for each of the three fixes, graded below against
live reproduction rather than trusted.

Setup: `git fetch origin issue-3127/experiment-trust+product-discovery-
hypothesis-preregistration+implementation-blueprint+silent-failure-
audit-4eda8e00 && git worktree add /tmp/pr3131-repair2-verify origin/
issue-3127/...-4eda8e00 --detach` -- derived: `git log --oneline -8` in
the worktree, resolved head `c928cba4`, showing `c928cba4`/`411a2140`/
`0db89918` directly atop round 1's four commits and the original build,
matching all three commits this round claims. canonical: `gh pr view
3131 --json state,headRefName` at setup and re-checked at the end of
this session -- `state: OPEN`, `headRefName` unchanged; PR #3131 was not
merged and not edited by this session (worktree removed with `--force`
at the end, no commits added, no push performed).

### Item 1 — reachability: Present

canonical: `PR-3131-branch:scripts/issue-3127/run_consumer_pair.py:82`,
`import spawn as _spawn_mod  # noqa: E402 -- see arm_workspace_dir()` --
present at module scope; `:690-692`, `arm_workspace_dir()`'s body now
resolves `_spawn_mod` from that import.

derived: this session's own live reproduction, written as a standalone
script (not reusing the repair's own test file), calling `rcp.run_pair()`
directly with a real throwaway git repo (`git init` + `git remote add
origin`) and `MUSTER_WORK_DIR` pointed at a temp dir. Per the round's own
must-not, `arm_workspace_dir()` itself was left completely unmocked; only
`subprocess.run` was stubbed, and only for commands whose first two
tokens are literally `["python3", "spawn.py"]` -- every other call
(including the real `git remote get-url origin` inside spawn.py's own
`_workspace_target_path()`) ran for real:

```
REACHED WITHOUT CRASH
excluded_from_h2: False
h1_manipulation_ok: True
h2 is not None: True
scorer_calls: 1
```

Mutation test: deleted the `import spawn as _spawn_mod` line from the
worktree's copy and re-ran the identical script -- reproduced the exact
original defect:

```
NameError: name '_spawn_mod' is not defined
```

at the same call site (`arm_workspace_dir()` inside `run_pair()`),
confirming the import is the actual causal fix, not a coincidental pass.
Restored the file immediately after (`diff` against the pre-mutation
backup showed no residual change).

**Every `arm_workspace_dir` reference in `PR-3131-branch:tests/
test_issue_3127_run_pair.py`, classified individually.** derived: `grep
-n "arm_workspace_dir" tests/test_issue_3127_run_pair.py`, run against
the worktree -- 11 hits:

| line | text | classification |
|---|---|---|
| 14 | docstring, "every test below this docstring mocks `arm_workspace_dir()`" | prose, not a mock |
| 15 | docstring, "...and it was not [reachable]" | prose, not a mock |
| 19 | docstring, "`RunPairRealReachabilityTest` below calls `run_pair()` without mocking `arm_workspace_dir()`" | prose, not a mock |
| 21 | docstring, "...so `arm_workspace_dir()`'s real body...actually executes" | prose, not a mock |
| 68 | `mock.patch.object(rcp, "arm_workspace_dir") as m_ws` inside `RunPairTest.test_h1_pass_reaches_and_calls_the_blind_scorer` | **mock, bypasses the function** -- round 1, unchanged |
| 102 | `mock.patch.object(rcp, "arm_workspace_dir") as m_ws` inside `RunPairTest.test_h1_failure_excludes_pair_and_scorer_is_never_called` | **mock, bypasses the function** -- round 1, unchanged |
| 122 | `mock.patch.object(rcp, "arm_workspace_dir") as m_ws` inside `RunPairTest.test_missing_deliverable_leaves_h2_none_with_reason_not_h1_reason` | **mock, bypasses the function** -- round 1, unchanged |
| 142 | class docstring, "Round 2's must-not: do not mock `arm_workspace_dir()`" | prose, not a mock |
| 145 | class docstring, "...`arm_workspace_dir()` itself, and the `git remote get-url...`" | prose, not a mock |
| 174 | code comment, "...it relies on `arm_workspace_dir()`'s real call..." | prose, not a mock |
| 215 | code comment, "...from `run_pair()`'s real, unmocked `arm_workspace_dir()` flow" | prose, not a mock |

derived: `grep -c 'mock.patch.object(rcp, "arm_workspace_dir")'
tests/test_issue_3127_run_pair.py`, run against the worktree -- `3`,
matching the 3 table rows marked "mock, bypasses the function" above;
11 - 3 = 8 rows are prose. All 3 mock occurrences are confined to round
1's original `RunPairTest` class, which this round's own record states
was left unchanged by design (isolated H1/scorer-wiring logic tests, not
reachability tests). derived: reading `RunPairRealReachabilityTest`'s
own 2 methods directly in the worktree file (both methods quoted in
full above, `test_run_pair_real_flow_reaches_h1_gate_and_blind_scorer`
and `test_run_pair_real_flow_h1_failure_still_excludes_and_skips_
scorer`) -- neither mocks `arm_workspace_dir` anywhere; only
`rcp.subprocess.run`, filtered to `python3 spawn.py ...` commands. This
does not repeat PR #3158's finding: round 1's tests proving reachability
by mocking the function under test was the defect; round 2 adds tests
that prove reachability without that mock, alongside (not instead of)
round 1's narrower isolated-logic tests.

derived: `python3 -m pytest tests/test_issue_3127_run_pair.py -v`, run
against the worktree:
```
5 passed in 0.86s
```
(3 round-1 `RunPairTest` + 2 `RunPairRealReachabilityTest`), matching the
round's own claimed count.

### Item 2 — results skeleton regenerated from code, not hand-edited: Present

canonical: `PR-3131-branch:scripts/issue-3127/run_consumer_pair.py:978-
1014` -- `--emit-not-executed` argparse flag wired into `main()`, calling
`emit_not_executed_results(plan)` and writing its output to `--out`.

derived: ran `python3 scripts/issue-3127/run_consumer_pair.py --emit-
not-executed --out /tmp/regenerated-results.json` against the worktree,
then `diff /tmp/regenerated-results.json docs/issue-3127/_assets/
consumer-path-results.json` -- **zero-byte diff, exit 0**. The committed
`PR-3131-branch:docs/issue-3127/_assets/consumer-path-results.json` is
the literal output of the function, not a hand-maintained copy that
happens to agree with it.

derived: parsed the committed file directly this session (`python3 -c
"import json; d=json.load(open('docs/issue-3127/_assets/consumer-path-
results.json')); ..."` against the worktree) -- both `arms.skills-on` and
`arms.skills-off` carry `wall_clock_to_pr_open_s` (present, `None`),
`wall_clock_to_landed_s` (present, `None`), and a non-empty
`landing_measurement_status` string naming the specific reason ("this
harness observes only the spawned session's own session-end event...at
most a phase-1 proposal PR opening...not a merge...contract v3 s22").
This is the exact schema PR #3158 found the committed file was missing.

acceptance: `python3 scripts/issue-3127/verify_preregistration.py` — run
against the worktree, against the unregenerated, still-committed file
(matching what the acceptance check inspects) — result:
```
OK: pre-registration commit 84226988e930981b02d00abd30e22c83100e875f is an ancestor of results commit 9c9801cd470129580de54b78a32abc30875de90e
exit=0
```

### Item 3 — --dry-run parity, the `-C <repo>` fix: Present

canonical: `PR-3131-branch:scripts/issue-3127/run_consumer_pair.py:655-
660` (`execute_arm()`'s real `spawn.py watch` subprocess call) --
`["python3", "spawn.py", "watch", "--issue", str(issue), "--session",
plan.skill_name, "--follow", "--self-heal", "-C", plan.sandbox_repo]`.
canonical: `PR-3131-branch:scripts/issue-3127/run_consumer_pair.py:259-
264` (`render_dry_run()`'s printed "blocking watch" line) -- now
includes `f"--follow --self-heal -C {plan.sandbox_repo}  "`.

acceptance: `python3 scripts/issue-3127/run_consumer_pair.py --dry-run`
— run live against the worktree — result: exit 0, full output read.
Every printed `python3 spawn.py watch --issue ...` line carries `-C
<sandbox-repo-not-yet-chosen>`, matching what `execute_arm()` actually
runs. Cross-checked every other step in the printed plan (held-constant
factor table, per-pair `spawn.py --skills ...` command lines, the
preflight `lint` line, the H1-gate/blind-scorer description in "Post-run
instrumentation") against `build_plan()`, `spawn_command()`,
`execute_arm()`, `gate_pair_on_h1()`, `run_pair()` directly (all read
this session in the worktree) -- no further mismatch found between what
is printed and what the code does for the parts these functions cover.

Mutation test: edited the worktree's copy to drop the `-C
{plan.sandbox_repo}` segment from the printed watch line (leaving the
real `execute_arm()` call unchanged), re-ran
`RenderDryRunMatchesExecuteArmTest` -- failed with `AssertionError: '-C
<sandbox-repo-not-yet-chosen>' not found in "...--follow --self-heal
(timeout 1800s)"`, reproducing the original defect shape exactly.
Restored the file immediately after.

derived: `python3 -m pytest tests/test_issue_3127_run_consumer_pair.py::
RenderDryRunMatchesExecuteArmTest -v`, run against the worktree
(post-restore):
```
1 passed in 0.80s
```

## The deciding question: can the orchestrator run this harness now?

**Yes, past the crash this round fixed.** derived: this session's own
"Item 1" reproduction above -- `rcp.run_pair()`, called directly with
only the `spawn.py` dispatch boundary stubbed, reached
`gate_pair_on_h1()` and `evaluate_pair_blind()` (via `compute_h2()`)
without raising, printing `REACHED WITHOUT CRASH` / `h2 is not None:
True` / `scorer_calls: 1`.

**No, not with every pre-registration field populated.** canonical:
`PR-3131-branch:scripts/issue-3127/run_consumer_pair.py:526-556`,
`build_execute_results()` (the function `main()`'s `--execute` branch
actually calls), read directly this session in the worktree -- it
assembles `pairs`, `pairs_included_in_h2`, `pairs_excluded_from_h2`, and
a `decision` string from `pair_results`. Each per-pair result includes
`h1` (carrying `on_bytes`/`off_bytes`, i.e. field (d)'s
"directive-composition bytes alone") and `h2` when scored. It does NOT
include: verification-round count or verification-round defect counts
(field (d)/(c)), token cost (field (d)), or BM25 selection position per
skill mount (field (d)). derived: `grep -n "verification_rounds\|
verification_defects_found\|bm25_selection_position\|collect_metrics("
scripts/issue-3127/run_consumer_pair.py`, run against the worktree --
`verification_rounds`/`verification_defects_found`/`bm25_selection_
position` appear only inside `emit_not_executed_results()` (lines
801-805), hardcoded to `None`, not inside `build_execute_results()` or
anywhere `run_pair()`'s return value flows through; `collect_metrics()`
is called from nowhere except its own `def` line and one line of
`render_dry_run()`'s printed prose (line 266) -- it is still dead code,
unchanged by this round. Wall-clock-to-landed-PR (field (c)'s other
guardrail metric) is permanently `None` by design, per `execute_arm()`'s
own documented reasoning (unchanged this round, read directly in the
worktree, confirmed under "Item 2" above).

canonical: `git show 17751209:docs/issue-3127/reports/experiment-trust+
adversarial-review+test-depth-audit-88b28bc4.md`'s "The deciding
question" section (PR #3158), re-read this session -- states this gap as
"regardless of the crash -- no code path computes them." canonical:
`git show c3fc6e13:docs/issue-3127/reports/implementation-blueprint+
test-depth-audit+silent-failure-audit-4cf4e602.md`'s "Why" section
(repair round 2's own record), re-read this session -- states this was
deliberately out of scope: its spawn instructions named exactly the
three items graded above, not the four-field/one-guardrail gap. This
session's own greps above (run against the current worktree, not
recalled from either prior record) found no evidence the gap was
touched, worsened, or newly closed by this round's three commits -- it
remains exactly as PR #3158 described it.

## Test Depth Audit on the round's 5 new tests

Skill-tool run this session (`test-depth-audit`), applied directly
against the tests this round added (derived: Step 1's enumeration
immediately below lists all of them by name, 5 total), all read and
executed live against the worktree.

**Step 1 — enumerate**: derived: `python3 -m pytest tests/
test_issue_3127_run_pair.py::RunPairRealReachabilityTest tests/
test_issue_3127_h1_and_scoring.py::EmitNotExecutedResultsTest tests/
test_issue_3127_h1_and_scoring.py::CliEmitNotExecutedTest tests/
test_issue_3127_run_consumer_pair.py::RenderDryRunMatchesExecuteArmTest
-v`, run against the worktree -- 5 collected, 5 passed:
1. `RunPairRealReachabilityTest::test_run_pair_real_flow_reaches_h1_gate_and_blind_scorer`
2. `RunPairRealReachabilityTest::test_run_pair_real_flow_h1_failure_still_excludes_and_skips_scorer`
3. `EmitNotExecutedResultsTest::test_arms_carry_both_wall_clock_fields_with_a_reason`
4. `CliEmitNotExecutedTest::test_cli_writes_file_matching_the_function_output`
5. `RenderDryRunMatchesExecuteArmTest::test_watch_line_carries_the_same_repo_flag_as_the_real_watch_call`

**Step 2 — classify** (each read directly this session in the worktree,
quoted in "Item 1"/"Item 3" above for tests 1-2 and 5):
- Test 1: asserts `excluded_from_h2 is False`, `h1_manipulation_ok is
  True`, `h2 is not None`, `len(scorer_calls) == 1` against a real
  (unmocked) `run_pair()`/`arm_workspace_dir()` call -- **Genuine
  Assertion**, and specifically not Mock-Dominated on the seam that
  matters (this is the seam PR #3158 found insufficiently tested).
- Test 2: same shape, opposite path (`excluded_from_h2 is True`, `h2 is
  None`, `scorer_calls == []`) -- **Genuine Assertion**.
- Test 3: calls `emit_not_executed_results()` directly, asserts both
  wall-clock fields present with a truthy reason string for both arms --
  **Genuine Assertion**.
- Test 4: `subprocess.run`s the real CLI end-to-end (`--emit-not-
  executed --out <tmp>`), asserts exit 0, file exists, `run_status ==
  "not_executed"`, both wall-clock fields present per arm -- **Genuine
  Assertion**, zero mocking of any kind (strongest of the 5: proves the
  CLI wiring itself, not just the function in isolation).
- Test 5: asserts every printed watch line contains `-C <repo>`,
  `--follow`, `--self-heal`, `--session <skill>` against `render_dry_
  run()`'s real (unmocked) output -- **Genuine Assertion**.

**Step 3 — verification density**: 5/5 = 100% (derived: Step 2
immediately above classifies all 5 enumerated tests as Genuine
Assertion; zero Execution-Only, Mock-Dominated, Happy-Path-Only, or Dead
among them).

**Step 4 — mutation confirmation**: derived: performed live this session
for test 1 and test 2 (reverting the `_spawn_mod` import -- both
`RunPairRealReachabilityTest` tests reproduced the original `NameError`
and failed; restored, both passed again -- same transcript quoted under
"Item 1" above, which mutation-tested `run_pair()` directly rather than
through the test file, then confirmed via `pytest ... -v` showing `5
passed` post-restore) and test 5 (removing `-C {plan.sandbox_repo}` from
the printed line -- failed with the exact original mismatch, quoted
under "Item 3" above; restored, passed again, quoted as `1 passed` under
"Item 3"). Tests 3 and 4 were not separately mutation-tested this
session (the underlying claim -- the file and the function agree -- was
instead verified by the stronger method of regenerating the actual
committed artifact and diffing it byte-for-byte, under "Item 2" above).

Round 1's 3 pre-existing `RunPairTest` tests remain **Mock-Dominated**
specifically on the `arm_workspace_dir` seam, unchanged by design (per
this round's own record's "Why" section, confirmed by the classification
table under "Item 1" above) -- they still prove H1/scorer-wiring logic
correctly in isolation, not reachability from the real per-pair flow;
that gap is now covered by the 2 new `RunPairRealReachabilityTest`
tests, not by fixing the existing 3.

## Acceptance checks and full suite -- reproduced this session, all pass

```
$ python3 scripts/issue-3127/run_consumer_pair.py --dry-run; echo exit=$?
...
exit=0
$ test -f docs/issue-3127/_assets/consumer-path-results.json && echo PRESENT
PRESENT
$ python3 scripts/issue-3127/verify_preregistration.py; echo exit=$?
OK: pre-registration commit 84226988... is an ancestor of results commit
9c9801cd...
exit=0
$ python3 -m pytest tests/ -q
283 passed, 2 warnings in 10.41s
$ python3 -m pytest test/ -q
15 failed, 548 passed, 3 xfailed in 32.22s
```
All run against the worktree this session. `tests/`'s 283 matches the
repair round's own claimed count (derived: round 1's 278 plus this
round's 5 new tests, `278 + 5 = 283`). `test/`'s 15 failing node IDs
(listed in the raw pytest output captured this session, e.g.
`Bm25CrossFamilySkillMatchesTest`) match PR #3158's own reported
baseline exactly -- derived: name-for-name comparison of this session's
own failure list against `git show 17751209:docs/issue-3127/reports/
experiment-trust+adversarial-review+test-depth-audit-88b28bc4.md`'s
"Acceptance checks" section, re-read this session -- same 15 names, all
owned by issue #3091, none in the issue-3127 harness's own test files.

## Why

canonical: this session's own reproduction transcripts under "Item 1"/
"Item 3" above (the standalone `run_pair()` script and the two mutation
tests) -- ran every claim in the repair round's record against the
actual code rather than citing its own assertions, per this task's
spawning brief and `adversarial-review`'s blindness-to-intent mechanism:
this session did not accept the `283 passed` count alone as evidence the
reachability gap closed; it independently wrote its own standalone
reproduction script, calling `run_pair()` the way `main()`'s `--execute`
branch actually calls it rather than reusing the repair's own test
file's choices, and mutation-tested the two structural fixes (the
import, the `-C` flag) by reverting each and confirming (via the exact
tracebacks/assertion-failures quoted under "Item 1"/"Item 3") that the
original failure mode reappears verbatim.

`experiment-trust`'s Twyman's-law framing (Step 5) applied directly:
canonical: `git show c3fc6e13:docs/issue-3127/reports/implementation-
blueprint+test-depth-audit+silent-failure-audit-4cf4e602.md`'s `verdict:`
frontmatter, re-read this session -- reports "all three findings closed,
283 passing" as a clean result following two prior rounds (PR #3145, PR
#3158) that each found real problems; that shape is exactly the
reassuring-after-scrutiny result Twyman's law says should be checked
hardest, not credited because the prior rounds already did the finding
-- addressed by this session's own independent mutation tests above
rather than by re-reading the claim.

`test-depth-audit`'s execution-vs-verification distinction separated
"these tests pass" (derived: the `pytest -v` runs quoted under "Item 1"/
"Item 3"/"Test Depth Audit" above) from "the claim they prove is true"
-- Step 4's mutation-testing check on tests 1, 2, and 5 (same
transcripts) is what actually establishes that, not the passing count
alone.

The one place this session did not find a new problem beyond what PR
#3158 already named -- the four-field/one-guardrail gap in `--execute`'s
real output -- is reported as an open, not newly-introduced or
newly-closed, finding under "The deciding question" above: canonical:
the repair round's own "Why" section (`git show c3fc6e13:...`, cited
above) already disclaims this as out of scope, and this session's own
`grep`/direct-read of `build_execute_results()`/`collect_metrics()` in
the worktree (quoted under "The deciding question" above) confirms that
disclaimer is accurate rather than evasive.

## What did not work

None this session. derived: this session's own sequence of live
reproductions -- the standalone `run_pair()` reachability script, the
two mutation tests (import revert, `-C` flag removal), the skeleton
regeneration-and-diff, the dry-run live run, and the two full
test-suite runs (`tests/` 283 passed, `test/` 15 failed matching
baseline, both cited under "Acceptance checks" above) -- every one
produced a clear result on the first attempt; nothing was tried and
abandoned. The worktree was removed cleanly at the end (`git worktree
remove /tmp/pr3131-repair2-verify --force`), confirmed by `gh pr view
3131 --json state,headRefName` showing no new commits, cited under "What
was done" above.

## Upstream basis

- PR #3131 branch `issue-3127/experiment-trust+product-discovery-
  hypothesis-preregistration+implementation-blueprint+silent-failure-
  audit-4eda8e00`, head `c928cba4` -- the harness graded here, read and
  exercised via `git worktree add ... --detach` at that commit. Not
  merged, not edited by this session (canonical: `gh pr view 3131 --json
  state,headRefName` re-checked at the end of this session -- `state:
  OPEN`, `headRefName` unchanged, no new commits pushed by this
  session).
- `docs/issue-3127/reports/experiment-trust+adversarial-review+test-
  depth-audit-88b28bc4.md` (PR #3158) -- the source of the three
  findings re-graded above.
- `docs/issue-3127/reports/implementation-blueprint+test-depth-audit+
  silent-failure-audit-4cf4e602.md` (repair round 2's own record,
  landed via PR #3162, already on this branch) -- its per-item claims
  are what this session independently re-derived rather than cited.
- Issue #3127 (`gh issue view 3127`, read this session).

## Open findings

1. canonical: `PR-3131-branch:scripts/issue-3127/run_consumer_pair.py:
   526-556` (`build_execute_results()`) and its dead `collect_metrics()`/
   `collect_ledger_tokens()`, both read directly this session in the
   worktree, cited under "The deciding question" above -- a real
   `--execute` run's output has no code path that could ever populate
   verification-round count, verification-round defect counts, token
   cost, or BM25 selection position (field (d), and half of field (c)'s
   two guardrail metrics); `emit_not_executed_results()`'s hardcoded
   `None`s for these fields and `collect_metrics()`'s dead status are
   unchanged by this repair round. This is the same gap PR #3158 already
   named as separately scoped and out of this round's own stated
   instructions (canonical: `git show c3fc6e13:...`'s "Why" section,
   cited above) -- not newly found here, not closed here. Resolution
   path unchanged from PR #3158's own: either wire these collectors into
   `run_pair()`'s return value and `build_execute_results()`'s output
   shape, or amend `PR-3131-branch:docs/issue-3127/decisions/pre-
   registration.md` to mark these fields as not collected by this
   harness version.
2. canonical: `PR-3131-branch:scripts/issue-3127/run_consumer_pair.py:
   618-627` (`execute_arm()`'s `landing_status` string), read directly
   this session in the worktree -- wall-clock-to-landed-PR (field (c)'s
   other guardrail metric) is permanently unmeasurable by this harness's
   design, unchanged this round. Pre-registration's guardrail rule (c)
   can never be mechanically evaluated from a real run. Not a defect in
   this round's own scope; carried over from PR #3158's own finding
   (canonical: `git show 17751209:...`'s "The deciding question"
   section, cited above).

## Next steps

None for this session -- `loop_state: landed`, this record is committed
to this session's own branch and PR. For a future session: see "Open
findings" above for the two carried-over resolution paths (both
pre-existing, neither introduced nor closed by repair round 2). PR
#3131 itself was neither merged nor edited by this session (canonical:
`gh pr view 3131 --json state,headRefName` cited under "Upstream basis"
above).

skill-verdict: test-depth-audit — applied: invoked; loaded the skill's
full SKILL.md via the Skill tool this session, then applied Steps 1-4
directly against the round's 5 new tests (per-test classification,
verification-density computation, and live mutation confirmation on
tests 1, 2, and 5), under "Test Depth Audit on the round's 5 new tests"
above.
skill-verdict: experiment-trust — applied: invoked; loaded the skill's
full SKILL.md via the Skill tool this session. Step 1's scope gate
correctly routes this session's own defect-grading work away from Steps
2-4 (SRM/A-A/pre-commit checks -- no live online-controlled experiment
ran this session; this is a code-verification task, not an A/B result).
Step 5's Twyman's-law framing (an anomalous or reassuring result is
suspected until independently checked) directly motivated re-deriving
all three verdicts from this session's own live execution and mutation
tests rather than accepting the repair round's "all three closed, 283
passing" claim at face value, per "Why" above.
skill-verdict: adversarial-review — applied: invoked; loaded the skill's
full SKILL.md via the Skill tool this session. This record is an
independent evaluator pass built from running the code directly against
PR #3158's original finding descriptions rather than reading the repair
round's own record as ground truth -- the standalone reachability
reproduction script and both mutation tests were written the way
`main()` actually calls the affected functions, not the way the repair's
own test file chose to call them, per "Item 1"/"Item 3" and "Why" above.
other mounted skills: not triggered -- none beyond the three above were
mounted for this task.
