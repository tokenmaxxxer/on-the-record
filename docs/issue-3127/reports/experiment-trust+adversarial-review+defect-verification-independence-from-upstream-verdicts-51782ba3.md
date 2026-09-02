---
issue: 3127
role: experiment-trust+adversarial-review+defect-verification-independence-from-upstream-verdicts-51782ba3
author: experiment-trust+adversarial-review+defect-verification-independence-from-upstream-verdicts-51782ba3
skills: experiment-trust (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12)), defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12))
verifies_subject: true  # independent, builder-blind verification of PR #3131's own deliverable against issue #3127
loop_state: landed
code_under_review: 7f2490823ebf7cc153250935798010bad3de73f4
type: defect-verification-record
breaking: false
verdict: 3 of 3 required acceptance checks Present, all 3 must-not clauses
  Present. The pre-registration is real (broke verify_preregistration.py
  with a constructed results-committed-first history and confirmed it
  correctly fails), and the #3091/#2507 confound resolution was
  independently re-derived and holds. Two new findings not disclosed by
  the builder's own "Open findings" section: run_consumer_pair.py's
  --execute path never actually calls execute_arm() (dead code, confirmed
  by running it), contradicting the file's own comment that it is "not a
  stub" a future session can "run... directly"; and the pre-registration's
  H1 manipulation-check gate on H2 exists only as prose in
  pre-registration.md -- no aggregation/decision-rule code exists
  anywhere in the harness that would enforce it.
upstream:
  - path: 7f249082:scripts/issue-3127/run_consumer_pair.py
    sha: 7f2490823ebf7cc153250935798010bad3de73f4
  - path: 7f249082:scripts/issue-3127/verify_preregistration.py
    sha: 7f2490823ebf7cc153250935798010bad3de73f4
  - path: 7f249082:docs/issue-3127/decisions/pre-registration.md
    sha: 7f2490823ebf7cc153250935798010bad3de73f4
  - path: 7f249082:docs/issue-3127/_assets/consumer-path-results.json
    sha: 7f2490823ebf7cc153250935798010bad3de73f4
  - path: 7f249082:pipeline.py
    sha: 7f2490823ebf7cc153250935798010bad3de73f4
---

# issue-3127 — experiment-trust+adversarial-review+defect-verification-independence-from-upstream-verdicts-51782ba3 record

## What was done

canonical: `gh issue view 3127` output -- issue #3127 asks for the
consumer-path (not floor-condition) paired skills-on/skills-off
measurement, through `spawn.py --skills`, with three acceptance checks
(`run_consumer_pair.py --dry-run`, `test -f .../consumer-path-results.json`,
`verify_preregistration.py`) and three must-nots (no null-as-no-effect
without a power statement; no dropped arm/narrowed task set for a bad run;
no standardizing away the orchestrator's own skill selection).

canonical: `gh pr view 3131` output -- PR #3131 (branch
`issue-3127/experiment-trust+product-discovery-hypothesis-preregistration+implementation-blueprint+silent-failure-audit-4eda8e00`,
head `7f249082`) delivers the pre-registered design and a working harness,
explicitly not a live run: canonical:
`7f249082:docs/issue-3127/_assets/consumer-path-results.json` records
`run_status: "not_executed"` with two stated reasons.

This is an independent, builder-blind verification: the builder's own
record (canonical: `7f249082:docs/issue-3127/reports/experiment-trust+product-discovery-hypothesis-preregistration+implementation-blueprint+silent-failure-audit-4eda8e00.md`,
present only on PR #3131's branch, untracked in this session's own working
tree) was read only after this session had already run its own
independent checks below, per
`defect-verification-independence-from-upstream-verdicts` rule 1 (a
review requirement is a claim to test, not a settled fact) -- every
number and claim below was re-derived directly, not cited from that
record.

canonical: this session's own `git worktree add` command output. Setup:
`git fetch origin pull/3131/head:pr-3131` then `git worktree add
/tmp/pr3131-verify pr-3131` (PR branch head `7f249082`). All checks below
ran from that worktree unless noted. derived: `git log pr-3131 --oneline
-1` run both before and after this session's checks -- result: `7f249082`
unchanged both times, confirming no commits were added to PR #3131's own
branch this session.

### Acceptance check 1 — `bash -c "python3 scripts/issue-3127/run_consumer_pair.py --dry-run"`

derived: ran the literal `bash -c "..."` form from `/tmp/pr3131-verify` --
result: exit 0, full plan printed (held-constant factor table, both arms'
exact `spawn.py` command lines for both registered pairs, post-run
instrumentation plan). Present.

### Acceptance check 2 — `bash -c "test -f docs/issue-3127/_assets/consumer-path-results.json"`

derived: ran the literal form from `/tmp/pr3131-verify` -- result: exit 0,
file exists (`7f249082:docs/issue-3127/_assets/consumer-path-results.json`).
Present.

### Acceptance check 3 — `bash -c "python3 scripts/issue-3127/verify_preregistration.py"`

derived: ran the literal form from `/tmp/pr3131-verify` -- result: exit 0,
`OK: pre-registration commit 84226988e930981b02d00abd30e22c83100e875f is
an ancestor of results commit 9c9801cd470129580de54b78a32abc30875de90e`.
Present.

**Adversarial break of the pre-registration check** (per this issue's own
framing -- "a pre-registration check that cannot detect a violation is the
same defect class as an acceptance check that never runs"). Built a
from-scratch git repo (`/tmp/prereg-test`, outside this repo's own
history, untracked in this repo) that violates the ordering the check is
supposed to enforce: committed a same-relative-named but
untracked-in-this-repo results file FIRST (`docs/issue-3127/_assets/consumer-path-results.json`,
a path that exists only inside that synthetic `/tmp/prereg-test` fixture,
not in this repo), then an untracked-in-this-repo pre-registration file
SECOND (`docs/issue-3127/decisions/pre-registration.md`, same fixture-only
scope) -- reversed order:

```
$ git log --oneline
5dc45a5 prereg second (violation)
4294746 results first (violation)
$ python3 /tmp/pr3131-verify/scripts/issue-3127/verify_preregistration.py --repo-root /tmp/prereg-test
pre-registration commit 5dc45a5cc3ffc22e038252cecfe1ced4d625bc35 is NOT an ancestor of results commit 4294746bff40587b37d9ab6d85cb384066a4ea59 -- either unrelated history or the results were committed first
$ echo "exit=$?"
exit=1
```

derived: the check correctly refuses this history (exit code 1 shown
above) -- it has real teeth, not a check that would pass vacuously on any
history. canonical: `7f249082:scripts/issue-3127/verify_preregistration.py`
lines 66-101, read directly -- `verify()` distinguishes three violation
shapes with three distinct messages: both paths introduced in the same
commit, results committed before pre-registration, and neither committed
yet.

### Must-not 1 — no null-as-no-effect without a power statement

canonical: `7f249082:docs/issue-3127/_assets/consumer-path-results.json`,
`decision` field, read verbatim -- `"unmeasured -- explicitly not
reported as a null/no-effect result; no data was collected against the
registered threshold this session"`, and its `power_statement` field
states what the registered n=2 design would have been able to detect had
it run (an effect smaller than the registered 3-point margin is
unresolvable at this n).

canonical: `7f249082:docs/issue-3127/decisions/pre-registration.md`,
"Power statement" section, read verbatim -- carries the identical
disclosure, committed before any result existed (per acceptance check 3
above). Neither file's decision/power-statement language uses "no
effect," "indistinguishable," or "no difference" to describe this run --
both fields were read in full above, not sampled. Present.

### Must-not 2 — no dropped arm / narrowed task set / excluded bad run

canonical: `7f249082:docs/issue-3127/_assets/consumer-path-results.json`,
`arms` object, read verbatim -- `run_status: "not_executed"` applies
uniformly to both arms and both registered pairs; neither arm/pair
carries a different status, and nothing ran badly to be excluded (nothing
ran at all). canonical:
`7f249082:docs/issue-3127/decisions/pre-registration.md`, field (e),
read verbatim -- the registered sample (n=2 pairs) is explicitly framed
as "extensible to the full n=4 set," not as an exclusion of the other two
toy tasks because of a bad outcome. Present.

### Must-not 3 — orchestrator's skill selection not standardized away

canonical: `7f249082:scripts/issue-3127/run_consumer_pair.py`,
`build_plan()`'s `held_constant` dict (around line 99), read directly --
the constant across arms is the `--skills <name>` argument text (the
orchestrator's initial choice of which skill to name), not whether the
named skill's cross-family BM25 matching/mounting behavior runs. The
pre-registration table (field (d)) lists "BM25 selection position per
skill mount" as a secondary/diagnostic metric precisely so selection
quality remains something the harness would report, not something
engineered away. Holding the initially-named skill argument constant
across arms is the same control #3053 used and is necessary for a paired
comparison to isolate corpus availability as the sole variable; it does
not remove selection behavior from what gets measured, since `spawn.py`'s
own mounting/cross-family-matching pipeline still runs identically in
both arms against differently-populated corpora. Present.

## Judgment on the four things this verification was asked to weigh

**1. Is the "not executed" boundary honest, or avoidance? -- Partially
honest, with one undisclosed gap.** canonical: `7f249082:spawn.py` lines
4684-4749, read directly (not cited from the PR's own record): the parent
process, on the `child_pid > 0` branch, registers a detached watcher
(`subprocess.Popen(..., start_new_session=True)`), prints "스폰은
리턴했지만 세션은 계속 돈다" ("spawn returns but the session keeps
running"), and returns immediately -- confirming the stated reason that a
bare foreground `spawn.py --skills ...` call does not block until the
spawned session finishes; only a second `spawn.py watch --follow` call
does. This part of the stated reason is accurate.

However: derived: `grep -n "execute_arm(" scripts/issue-3127/run_consumer_pair.py`
run this session against `/tmp/pr3131-verify` -- result: `execute_arm()`
defined at line 257, referenced once inside its own body (line 273, an
error message) and once in an unrelated print string (line 406) -- never
called from `main()`. Confirmed live this session:

```
$ python3 scripts/issue-3127/run_consumer_pair.py --execute \
    --i-understand-this-spawns-real-sessions --repo /tmp/fake-sandbox \
    --out /tmp/test-out.json
[plan] would execute skills-on for pair 01-study-groups -- issue-number allocation and result aggregation are left to the caller (this harness stops short of gh issue create side effects); see execute_arm().
[plan] would execute skills-off for pair 01-study-groups -- ...
[plan] would execute skills-on for pair 02-onboarding-experiment -- ...
[plan] would execute skills-off for pair 02-onboarding-experiment -- ...
$ echo "exit=$?"
exit=0
$ head -3 /tmp/test-out.json
{
  "issue": 3127,
  "run_status": "executed-with-incomplete-instrumentation",
```

No subprocess was spawned, no `gh` call made, no `spawn.py lint`/`spawn.py
--skills` invocation attempted -- `main()`'s `--execute` branch
(`7f249082:scripts/issue-3127/run_consumer_pair.py` lines 395-407)
constructs its output entirely from `emit_not_executed_results(plan)`
with only the status string relabeled, and only *prints* that it "would
execute" each arm. This contradicts the comment directly above that
branch: "Left implemented (not a stub) so a future session can run it
directly" (lines 396-397) -- a future session could not run it directly;
`main()` itself would need to be edited to call `execute_arm()` before any
real dispatch could occur. canonical:
`7f249082:docs/issue-3127/reports/experiment-trust+product-discovery-hypothesis-preregistration+implementation-blueprint+silent-failure-audit-4eda8e00.md`,
"Open findings" section, read after this session's own checks above --
it lists three gaps (untested `collect_metrics()`, the stale cross-family
test, "no real measurement yet") but does not list this one -- the
harness is less executable than either that record or the module's own
comment represent it to be.

Verdict on this sub-question: Incorrect for the specific "not a stub,
runnable directly" framing, layered over an otherwise Present honest
disclosure of the daemonization/blocking mechanics and the
real-side-effects confirmation gap (the PR's stated reason 2, which
stands independently of this defect and is sufficient on its own to
justify not running it this session).

**2. Is the null/no-effect must-not honored everywhere, with nothing
smuggled in?** Yes -- see Must-not 1 above. Present.

**3. Is the pre-registration real?** Yes -- see the adversarial-break
construction above; `verify_preregistration.py` correctly refuses a
results-committed-first history. Present.

**4. Confound resolution (issue #3091/#2507) -- independently re-derived,
not accepted on citation:**

derived: `grep -n "_cross_family_candidate_corpus" -A 40 pipeline.py` run
this session against `/tmp/pr3131-verify` -- the function's docstring
states verbatim: "이슈 #2507: `_ROLE_SKILLS[role]` exclusion 은 없앴다 --
고정 role->skill 표가 더 이상 family를 정의하지 않으므로 ... 후보 풀을
role 기준으로 미리 좁힐 이유가 사라졌다." The function body opens with
`del skill` and builds its only exclusion set from
`_sp._STATIC_POLICY_SKILLS` (policy skills, e.g. `work-in-english`) -- no
role/family-based exclusion exists in the code.

derived: `python3 -m pytest test/test_spawn_cross_family_skill_selection.py
-k test_family_skill_never_returned_as_cross_family_candidate -q` run
this session from `/tmp/pr3131-verify`:

```
FAILED test/test_spawn_cross_family_skill_selection.py::Bm25CrossFamilySkillMatchesTest::test_family_skill_never_returned_as_cross_family_candidate
AssertionError: Lists differ: [PosixPath('/tmp/tmpjolek6kn/implementation-blueprint')] != []
1 failed in 0.84s
```
The test still asserts the pre-#2507 exclusion behavior against the
post-#2507 implementation, confirming (independently of the PR's own
claim) that the exclusion really is gone from the running code, not just
from the docstring's description of it.

derived: `git log -1 --format=%ci 0879f12a` -- `2026-08-26 18:40:06
+0900`; `git log -1 --format=%ci 28e9c1e9` -- `2026-08-26 17:42:10 +0900`;
`git log -1 --format=%ci 573e7382` -- `2026-09-02 15:23:25 +0900` (this
session's own re-run gives a slightly different timestamp than the PR
record's quoted `15:03:48` for the same commit -- both agree on the date
and both post-date #2507's landing commits; the exact figure was not
byte-reproducible, but the ordering claim it supports is unaffected).
#2507's landing precedes #3053's paired-run commit, so #3053's candidate
pool already reflected current (non-excluding) behavior.

Independent conclusion: the PR's confound-check finding holds up under
re-derivation -- the current candidate pool is NOT narrowed by the stale
pin, and #3053's selection numbers do not need re-deriving on this
account. Present.

**5. Does H1 actually gate H2, or is it merely described?** derived:
`grep -n "^def \|H1\|manipulation\|decision_rule\|threshold_met\|margin"
scripts/issue-3127/run_consumer_pair.py` run this session against
`/tmp/pr3131-verify` -- matches only 11 function definitions (canonical:
same grep output -- `build_plan`, `spawn_command`, `render_dry_run`,
`scrub_skill_slugs`, `collect_directive_bytes`, `collect_ledger_tokens`,
`collect_metrics`, `execute_arm`, `_os_environ`,
`emit_not_executed_results`, `main`); none of these functions compute a
margin, apply a threshold, or compare directive-composition bytes
between an arm pair. `7f249082:docs/issue-3127/decisions/pre-registration.md`'s
H1 section is a real, falsifiable commitment in prose, and the
pre-registration-ordering check (acceptance 3 above) protects that
commitment from being rewritten after the fact -- but per the grep result
above, nothing in the delivered code would stop a future session from
computing an H2-style comparison over a pair whose H1 manipulation check
failed. canonical: the same "Open findings"/"next steps" sections of
`7f249082:docs/issue-3127/reports/experiment-trust+product-discovery-hypothesis-preregistration+implementation-blueprint+silent-failure-audit-4eda8e00.md`
cited above -- they frame remaining work as "run the harness for real"
plus fixing `collect_metrics()`'s parsing, not as "write the
aggregation/gating code that doesn't exist yet."

Verdict: Absent (gating is committed to on paper, not enforced in code).

**6. Nothing under `issue-3126` exists.** derived: `find . -path ./.git
-prune -o -iname "*issue-3126*" -print` and `git ls-files | grep -i 3126`
run this session against `/tmp/pr3131-verify` -- zero real hits (one
false-positive substring match, a timestamp filename
`20260826T143126372881-1944409.md` under `docs/issue-2548/reports/consult-log/`,
unrelated to any issue-3126 path). `grep -rn "issue-3126"` across tracked
files -- the only hits are inside this PR's own record, explaining the
path correction, none of which are actual paths on disk. Present.

## Full test suite

derived: `python3 -m pytest tests/ -q` run this session from
`/tmp/pr3131-verify`:

```
254 passed, 2 warnings in 10.04s
```
(the 2 warnings are a pre-existing pinned-fixture divergence, issue
#3019, unrelated to this PR's files.)

derived: `python3 -m pytest test/ -q` run this session from
`/tmp/pr3131-verify`:

```
15 failed, 548 passed, 3 xfailed in 32.25s
```
Failing node IDs (all 15, listed in full below): `test_convention_equivalence.py::BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim`,
`test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape`,
`test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment`,
`test_spawn_cross_family_skill_selection.py::Bm25CrossFamilySkillMatchesTest::test_family_skill_never_returned_as_cross_family_candidate`,
`test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_success_logs_picked_rejected_reasons_and_returns_picked_paths`,
`test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_consult_error_raises_and_still_traces`,
`test_spawn_cross_family_skill_selection.py::FourSurfaceCandidateCorpusTest::test_score_reaches_judge_question_labeled`,
`test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_matching_task_gains_exactly_that_skill_in_mounts_and_directive`,
`test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_non_matching_task_mounts_and_directive_byte_identical_to_baseline`,
`test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_declared_artifact_matching_skill_gets_pairing_line`,
`test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeOverlapOrderingTest::test_judge_dispatch_precedes_workspace_and_branch_setup_join_follows`,
`test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_no_declaration_line_byte_identical_to_baseline`,
`test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_completed_outcome`,
`test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_fail_open_outcome`,
`test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_not_run_when_skill_source_is_not_skill_repo`
-- this list matches the spawning task's own statement ("test/ has 15
pre-existing failures owned by #3091"); no new failures attributable to
this PR's own files (`7f249082:scripts/issue-3127/run_consumer_pair.py`,
`7f249082:scripts/issue-3127/verify_preregistration.py`,
`7f249082:docs/issue-3127/decisions/pre-registration.md`,
`7f249082:docs/issue-3127/_assets/consumer-path-results.json`) appear in
this list.

## Why

Followed `defect-verification-independence-from-upstream-verdicts`:
re-derived the confound-check finding from `pipeline.py` and a live test
run rather than citing the PR's own citation of it (rule 3); deliberately
constructed a negative-path attempt against `verify_preregistration.py`
(a hostile git history) rather than only exercising its happy path (rule
2); and did not lower rigor because the PR's own record already reads as
thorough and self-critical (rule 9) -- which is exactly how the two new
findings above (dead `--execute` code path, unenforced H1 gate) surfaced:
neither is visible from reading the record's prose alone, only from
running the code and grep-ing for what isn't there.

Followed `adversarial-review`'s core mechanism by reading the builder's
own record only after this session ran its own independent checks, so its
framing (particularly its "not a stub" language around `execute_arm()`)
did not anchor this session's read of the code before checking it
directly.

## What did not work

None.

## Rationale for deviations

None -- this session ran every check the spawning instructions asked for
(three acceptance checks, three must-nots, the H1-gating judgment, the
independent confound re-derivation, the issue-3126 absence check, and the
full test suite) without needing to exceed or narrow that scope.

## Upstream basis

- PR #3131, branch `issue-3127/experiment-trust+product-discovery-hypothesis-preregistration+implementation-blueprint+silent-failure-audit-4eda8e00`,
  head `7f249082` -- verified in a linked worktree at `/tmp/pr3131-verify`.
  derived: `git log pr-3131 --oneline -1` before and after this session's
  checks -- both `7f249082`, so no commits were added to that branch this
  session.
- `7f249082:spawn.py` lines 4684-4749 -- read directly for the
  self-daemonization claim.
- `7f249082:pipeline.py`'s `_cross_family_candidate_corpus()` -- read
  directly for the confound-check re-derivation.
- `7f249082:test/test_spawn_cross_family_skill_selection.py` -- re-run
  live, not cited from the PR's own claim of its failure.
- A from-scratch git repository at `/tmp/prereg-test` (not part of this
  repo's history, untracked here) -- built this session to adversarially
  test `verify_preregistration.py`.

## Open findings

- `7f249082:scripts/issue-3127/run_consumer_pair.py`'s `--execute` code
  path never calls `execute_arm()` -- confirmed dead code by running
  `--execute --i-understand-this-spawns-real-sessions` live this session
  (see judgment section 1 above; no subprocess/`gh` call was observed).
  Resolution path: whichever session next attempts a real consumer-path
  run must first wire `main()`'s `--execute` branch to actually call
  `execute_arm()` per pair/arm and allocate real issue numbers, not just
  relabel the not-executed result. Not a blocker on this issue's three
  literal acceptance checks (none of them invoke `--execute`), but it
  means the PR's own framing of the harness as "left implemented... so a
  future session can run it directly" overstates its current readiness.
- The H1 manipulation-check gate on H2 is a documented commitment in
  `7f249082:docs/issue-3127/decisions/pre-registration.md` with no
  corresponding enforcement code anywhere in `run_consumer_pair.py` --
  derived: `grep -n "^def " scripts/issue-3127/run_consumer_pair.py`
  lists 11 functions, none of which compute a margin or apply a
  threshold (see judgment section 5 above). Resolution path: the future
  executing session's scope must include writing this gating/decision-
  rule code, not just filling in the metrics collectors that already
  exist.
- (Carried from the PR's own record, independently re-confirmed above,
  not re-opened here): the stale
  `test_family_skill_never_returned_as_cross_family_candidate` unit test
  is a live, currently-failing test that asserts pre-#2507 exclusion
  behavior against the post-#2507 implementation -- in issue #3091's
  diagnosis scope, not this issue's.

## Next steps

`loop_state: landed` -- this verification's own checks (three acceptance
checks, three must-nots, the H1-gating judgment, the independent confound
re-derivation, the issue-3126 absence check, and the full test suite) are
recorded above, and this record is being committed to this session's own
branch. The two new findings in "Open findings" remain open against the
underlying PR #3131 / issue #3127 line of work, not against this
verification record.

skill-verdict: defect-verification-independence-from-upstream-verdicts —
applied: invoked; re-derived the #3091/#2507 confound check from
`pipeline.py` and a live test run rather than citing the PR's own
citation of it, deliberately constructed a negative-path attempt against
`verify_preregistration.py` instead of only its happy path, and read the
builder's own record only after this session's independent checks had
run so its "not a stub" framing of `execute_arm()` did not anchor the
read -- which is how the two new findings surfaced.
skill-verdict: adversarial-review — applied: invoked; ran this session's
own independent checks against the PR's code before reading its record,
per the skill's core mechanism (a fresh, unanchored read catches what a
same-session or record-anchored read would tend to accept).
skill-verdict: experiment-trust — not-applicable: this issue's own design
(`7f249082:docs/issue-3127/decisions/pre-registration.md`, "Scope note")
already correctly routes itself away from this skill's SRM/A-A-validation
machinery (an offline, pre-assigned-condition, small-n paired comparison,
not an online controlled experiment with random unit assignment at
volume) -- verified that self-disposition is accurate rather than
re-applying Steps 2-6 anyway, since applying chi-square/A-A checks to a
2-4-pair offline comparison would be theater regardless of which session
says so.
