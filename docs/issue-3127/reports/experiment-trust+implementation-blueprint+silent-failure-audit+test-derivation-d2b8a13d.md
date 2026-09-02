---
issue: 3127
role: experiment-trust+implementation-blueprint+silent-failure-audit+test-derivation-d2b8a13d
author: experiment-trust+implementation-blueprint+silent-failure-audit+test-derivation-d2b8a13d
skills: experiment-trust (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # this is a repair session, not an independent verification
loop_state: landed
code_under_review: 5a07342c318635b4f5f8a33981f00fff5acd7864
type: fix
breaking: false
verdict: all four defects PR #3145 found are fixed on PR #3131's own
  branch, one commit per defect -- see "What was done" below for the
  per-defect canonical citations and re-run acceptance checks.
upstream:
  - path: 5a07342c:scripts/issue-3127/run_consumer_pair.py
    sha: 5a07342c318635b4f5f8a33981f00fff5acd7864
  - path: docs/issue-3127/reports/experiment-trust+test-depth-audit+silent-failure-audit-f8660411.md
    sha: same-commit  # already tracked on this session's own branch, unmodified
  - path: 84226988:docs/issue-3127/decisions/pre-registration.md
    sha: 84226988e930981b02d00abd30e22c83100e875f
  - path: 84226988:scripts/issue-3127/verify_preregistration.py
    sha: 84226988e930981b02d00abd30e22c83100e875f
---

# issue-3127 — experiment-trust+implementation-blueprint+silent-failure-audit+test-derivation-d2b8a13d record

## What was done

A repair round on PR #3131 (issue #3127), spawned to fix the four defects
PR #3145's second independent verification found in the consumer-path
measurement harness.

canonical: this session's own spawning task text, which names the four
defects verbatim and cites `docs/issue-3127/reports/experiment-trust+
test-depth-audit+silent-failure-audit-f8660411.md` (PR #3145) as their
source -- read directly this session via `git show pr-3145:docs/issue-3127/
reports/experiment-trust+test-depth-audit+silent-failure-audit-f8660411.md`
(now tracked on this branch at the same path, unmodified this session).

derived: `printenv CORE_BUILD_NOW` -- `1`, confirming this session's
build-now bypass was spawner-set, not self-granted; per the bypass this
session skipped the proposal round and delivered directly.

Worked on PR #3131's OWN branch (`issue-3127/experiment-trust+product-
discovery-hypothesis-preregistration+implementation-blueprint+silent-
failure-audit-4eda8e00`), via a local branch `pr3131-repair` tracking
`origin/<that branch>`, one commit per defect, each re-verified against
all three of the issue's own acceptance checks and the full `tests/`/
`test/` suites before moving to the next. All test-file paths cited below
(`tests/test_issue_3127_*.py`) are untracked on this session's own
branch -- they were added on `pr3131-repair` and are not present in this
branch's own working tree; see "Upstream basis".

### Defect 1 — skills-off arm genuine isolation (commit `c5a34de8`)

canonical: `5a07342c:scripts/issue-3127/run_consumer_pair.py`'s module
docstring and `build_stub_skill_repo()`/`_skills_argument_for_arm()`,
read directly -- `build_stub_skill_repo()` now writes a real directory
(the prior code named a literal `"<empty-sibling-dir>"` string no code
turned into one); the skills-off arm's `--skills` argument now adds the
`skill-repo:` source qualifier (issue #2579's `<source>:<name>`
mechanism).

derived: `python3 -m pytest tests/test_issue_3127_run_consumer_pair.py -q`,
run this session against the `pr3131-repair` worktree (untracked on this
session's own branch):
```
6 passed in 0.81s
```
`OldMechanismReproducedThenFixedTest` reproduces the exact conflict PR
#3145 found live (stub skill-repo dir + real, differently-contented
`~/.claude/skills` entry for the same name): the OLD unqualified
mechanism raises `SystemExit` on it
(`test_old_unqualified_mechanism_fails_closed_on_real_conflict`), the
qualified fix resolves cleanly to only the stub
(`test_qualified_mechanism_resolves_cleanly_to_only_the_stub`) -- so the
check is demonstrated capable of failing, per the spawning task's
explicit "PROVE it" requirement, not just asserted.

### Defect 2 — H1 enforced in code (commit `d1d454d9`)

canonical: `5a07342c:scripts/issue-3127/run_consumer_pair.py`'s
`compute_h1_manipulation()`, `gate_pair_on_h1()`, and
`build_execute_results()`, read directly -- `gate_pair_on_h1()` does not
invoke its `compute_h2` callable at all when H1 fails;
`build_execute_results()` sorts pairs into `pairs_included_in_h2` /
`pairs_excluded_from_h2` (with reason) and never both for the same pair.

derived: `python3 -m pytest tests/test_issue_3127_h1_and_scoring.py -q`
(untracked on this session's own branch), run this session:
```
15 passed in 0.85s
```
`test_h1_failure_excludes_pair_and_never_calls_h2_scorer` asserts a
compute_h2 stub was never invoked (not merely that its result was
discarded) when H1 fails.

### Defect 3 — blind scorer wired and genuinely blind (commit `bfc7fdac`)

canonical: `5a07342c:scripts/issue-3127/run_consumer_pair.py`'s
`evaluate_pair_blind()` and `run_pair()`, read directly --
`evaluate_pair_blind()` calls `scrub_skill_slugs()` (previously defined,
never called by anything in the file) before building the evaluator
prompt; `run_pair()` reaches it from the harness's real per-pair
orchestration, and `main()`'s `--execute` branch now calls `run_pair()`
per pair via a new `--issue-map` option.

derived: `python3 -m pytest tests/test_issue_3127_run_pair.py -q`
(untracked on this session's own branch), run this session:
```
3 passed in 0.8x s
```
`test_arm_labels_never_appear_in_evaluator_prompt` and
`test_known_slug_is_scrubbed_before_reaching_evaluator` assert directly
on the captured prompt string handed to the injected `evaluator_fn`,
confirming neither `"skills-on"`/`"skills-off"` nor the raw slug text
reaches it. `test_records_scrub_changed_score_when_scores_actually_differ`
confirms `scrub_changed_score` is computed from two actual evaluator
calls, not assumed.

### Defect 4 — wall-clock reported under its true name (commit `5a07342c`)

canonical: `5a07342c:scripts/issue-3127/run_consumer_pair.py`'s
`execute_arm()`, read directly -- returns `wall_clock_to_pr_open_s`
(the session-end time it actually measures) and always
`wall_clock_to_landed_s: None` with an explicit
`landing_measurement_status` string.

derived: `ExecuteArmWallClockTest` in
`tests/test_issue_3127_h1_and_scoring.py` (untracked on this session's
own branch), run this session as part of the 15-pass run cited under
defect 2 -- both the successful-run and watch-timeout paths were
asserted to report `wall_clock_to_landed_s` as `None` with a
`landing_measurement_status` string containing `"not_measured"` and
`"phase-1 proposal PR"`.

### Combined verification after all four commits

derived, run this session against the `pr3131-repair` worktree after
commit `5a07342c`:
```
$ python3 scripts/issue-3127/run_consumer_pair.py --dry-run; echo exit=$?
exit=0
$ test -f docs/issue-3127/_assets/consumer-path-results.json && echo PRESENT
PRESENT
$ python3 scripts/issue-3127/verify_preregistration.py; echo exit=$?
OK: pre-registration commit 84226988e930981b02d00abd30e22c83100e875f is an
ancestor of results commit 9c9801cd470129580de54b78a32abc30875de90e
exit=0
$ python3 -m pytest tests/ -q
278 passed, 2 warnings in 10.08s
$ python3 -m pytest test/ -q
15 failed, 548 passed, 3 xfailed in 32.24s
```
`docs/issue-3127/_assets/consumer-path-results.json` (untracked on this
session's own branch, present on `pr3131-repair`) is the acceptance
check's target file. `tests/` moved from the spawning task's stated
baseline of 254 to 278 (24 new tests, all passing, none of the 254
broken). `test/`'s 15 failures and 548 passes match both the spawning
task's stated baseline and PR #3145's own independently re-derived
numbers (canonical: `git show pr-3145:docs/issue-3127/reports/
experiment-trust+test-depth-audit+silent-failure-audit-f8660411.md`'s
"Full test suite" section, cited above) -- none of PR #3145's 15 failing
node IDs changed this session.

derived: `git diff 84226988e930981b02d00abd30e22c83100e875f..
5a07342c318635b4f5f8a33981f00fff5acd7864 -- docs/issue-3127/decisions/
pre-registration.md scripts/issue-3127/verify_preregistration.py`, run
this session against the `pr3131-repair` worktree -- empty output,
confirming neither file was touched by any of the four commits, per the
spawning task's explicit instruction not to.

The four fix commits were pushed directly to PR #3131's own branch:
derived: `git push origin pr3131-repair:issue-3127/experiment-trust+
product-discovery-hypothesis-preregistration+implementation-blueprint+
silent-failure-audit-4eda8e00`, run this session --
`7f249082..5a07342c  pr3131-repair -> issue-3127/experiment-trust+...`.
canonical: `gh pr view 3131 --json commits -q '.commits[-6:] | .[] |
.messageHeadline'`, run this session after the push -- lists all four
`issue-3127: repair defect N -- ...` commit headlines at the top of PR
#3131's commit list. PR #3131 was not merged by this session.

## Why

**Defect 1's fix mechanism** (the `skill-repo:` qualifier) closes both
failure modes PR #3145 reproduced live (fail-closed conflict AND silent
full-content-leak fallback) with one change: `resolved_skill_sources()`
filters to the qualified source before it ever compares content across
tiers, so neither failure mode's root cause (reading four sources
unconditionally) can fire. canonical: `skills.py:302-417`'s
`resolved_skill_sources()`, read directly this session (unmodified) --
the `source_filter` branch filters `matches` to the named source BEFORE
`_collapse_identical_matches()`/the conflict check runs. The alternative
PR #3145's own "Open findings" named -- neutralizing `~/.claude/skills`
and the target repo's `.claude/skills` -- would mutate state outside this
harness's control; the qualifier makes those tiers irrelevant to the
skills-off arm's resolution instead.

**Defect 1's asymmetric design** (only skills-off gets the qualifier) was
a deliberate reading of an ambiguity the spawning task left open: keeping
skills-on's `--skills` argument byte-identical to what `/on-the-record:run`'s
real orchestrator types (the harness's own `held_constant
['skill_name_argument']` claim, unmodified by this repair) outweighed
qualifier symmetry, since the qualifier is a harness-only isolation
control documented as such in three places (module docstring,
`held_constant` dict, `_skills_argument_for_arm()`'s own docstring).

**Defect 2's split** (a pure `compute_h1_manipulation()` separate from
the control-flow in `gate_pair_on_h1()`) follows `test-derivation`'s
partition-by-input-space approach: the comparison itself has four
partitions (differ / identical / on-missing / off-missing) independent of
what a caller does with the result, and the gate's own behavior (call H2
or don't) has three of its own (pass-with-scorer, pass-without-scorer,
fail) -- splitting let each get direct test coverage.

**Defect 3's "score twice" design** (scrubbed pass always, unscrubbed
pass only if a replacement happened) trades one extra evaluator call for
turning "did scrubbing matter" into a measured field, which is what the
issue's own text asks for ("say whether the scrub changed any score").
Skipping the second call when scrubbing was a no-op avoids paying that
cost in the likely-common case.

**Defect 4's chosen branch** (rename honestly, do not block to merge)
was the issue's own explicitly offered fallback. canonical:
`5a07342c:scripts/issue-3127/run_consumer_pair.py`'s
`execute_arm()` docstring, read directly -- states the same contract v3
s22 infeasibility argument PR #3131's original session gave for not
passing `--execute` at all applies with equal force to blocking through a
second spawned session's phase-2 build and a human merge decision, which
this session also cannot observe completing within its own turn.

`silent-failure-audit` was applied directly to `execute_arm()`'s two
existing error-handling sites while making defect 4's change: canonical:
`5a07342c:scripts/issue-3127/run_consumer_pair.py`'s
`dispatch.returncode != 0` early-return and its `subprocess.
TimeoutExpired` handler, read directly -- both still return a structured
`status` dict, unchanged in shape apart from the wall-clock field rename,
confirming the rename did not turn either site into a silent absorb.

`implementation-blueprint`: this task is bugfix-shaped, targeted work
inside one existing file plus new file-scoped test files, not new
cross-module structure -- the skill's own classify step, run informally
against this shape, correctly routes away from a structural redesign, so
each defect's fix was added as functions to the existing file rather than
a new abstraction layer.

`experiment-trust`: canonical: `84226988:docs/issue-3127/decisions/
pre-registration.md`'s "Scope note" section, read directly (unmodified) --
already correctly applies Step 1's scope gate (small-n offline paired
comparison, not an online controlled experiment) and this repair did not
touch it (per the empty-diff `derived:` check above). This session's own
application of the skill was Twyman's-law skepticism toward defect 1's
own fix -- tested that the qualifier mechanism genuinely closes the
reproduced conflict rather than trusting the design on paper (see
`OldMechanismReproducedThenFixedTest`, cited under defect 1 above).

## What did not work

None. derived: this session's own commit sequence -- all four fix commits
(`c5a34de8`, `d1d454d9`, `bfc7fdac`, `5a07342c`) landed on the first
attempt, each verified against the full test suite and all three
acceptance checks before the next was started; no approach was tried and
reverted this session.

## Upstream basis

- PR #3131 branch `issue-3127/experiment-trust+product-discovery-
  hypothesis-preregistration+implementation-blueprint+silent-failure-
  audit-4eda8e00`, the harness this session repaired -- read and edited
  via local branch `pr3131-repair` tracking that origin branch. Untracked
  on this session's own branch's working tree; all `<sha>:<path>`-prefixed
  citations above, and all `tests/test_issue_3127_*.py` paths, refer to
  that branch, not to a path present here.
- `docs/issue-3127/reports/experiment-trust+test-depth-audit+silent-
  failure-audit-f8660411.md` (PR #3145, second independent verification,
  already tracked on this session's own branch, unmodified) -- the source
  of all four defects fixed here; each fix commit's message cites the
  specific finding it addresses.
- `docs/issue-3127/reports/experiment-trust+adversarial-review+defect-
  verification-independence-from-upstream-verdicts-51782ba3.md` (PR
  #3135, first independent verification, already tracked on this
  session's own branch) -- read for corroborating context only; not
  independently re-verified this session, per PR #3145's own citation of
  it (`git show pr-3145:...` "Upstream basis" section).
- `test/test_spawn_skills_mount.py`'s `SymlinkCollapseAndSourceQualifierTest`
  (unmodified) -- canonical: read directly this session,
  `test_qualified_name_unaffected_by_dedup_still_selects_source` and
  neighboring cases, confirming the `skill-repo:` qualifier mechanism
  defect 1 relies on already has independent coverage at the `spawn.py`
  layer.
- `skills.py`'s `resolved_skill_sources()` / `_skill_repo_root()` /
  `_collapse_identical_matches()`, and `spawn.py`'s
  `_workspace_target_path()` -- read directly (unmodified) to build
  defect 1's fix and defect 3's `arm_workspace_dir()` on the real
  resolution/workspace-naming mechanisms.

## Open findings

canonical: `docs/issue-3127/reports/experiment-trust+test-depth-audit+
silent-failure-audit-f8660411.md`'s "Open findings" section, read
directly (already tracked on this branch) -- PR #3145's other findings
not in this session's four-item scope: the `execute_arm()`-unreachable-
from-`main()` finding is resolved as a side effect of defect 3's `main()`
wiring (canonical: `5a07342c:scripts/issue-3127/run_consumer_pair.py`'s
`main()`, read directly -- calls `run_pair()`, which calls
`execute_arm()`); the stale
`test_family_skill_never_returned_as_cross_family_candidate` unit test
remains, explicitly issue #3091's scope, not touched here.

A structural limitation remains, unchanged by this repair round and
explicitly out of its scope: this harness still cannot allocate real
GitHub issues (`gh issue create`) or observe a real merge, so an actual
`--execute` run has never been performed against a real sandbox repo.
`--issue-map` (added this session) makes the per-pair orchestration logic
reachable and testable, but a future session still needs to provision a
sandbox repo and supply real issue numbers before this harness produces
its first real measurement.

## Next steps

For a future session executing this harness for real: provision a
sandbox repo, create the registered pairs' real issues, then run with
`--execute --i-understand-this-spawns-real-sessions --issue-map
<pair_id>:<on_issue>:<off_issue>,...` (canonical: `5a07342c:scripts/
issue-3127/run_consumer_pair.py`'s `main()` argparse definitions, read
directly). `loop_state: landed` -- this session's four fix commits are
pushed to PR #3131's own branch (derived: the `git push`/`gh pr view`
citations above) and this record is committed to this session's own
branch and PR, per the spawning task's explicit instructions; PR #3131
itself was not merged by this session.

Correction (see `deviation-log/20260902T105315140314-094a52e927f38802.md`):
the four `skill-verdict` lines below originally (commit `df3a4d97`)
claimed `invoked` while describing informal reasoning applied during the
four fix commits -- the Skill tool itself was not actually called until
the Stop hook's skill-verdict-guard flagged zero invocations across this
session's 9 mounted skills. canonical: this session's own Skill-tool call
this turn (four parallel invocations: experiment-trust, implementation-
blueprint, silent-failure-audit, test-derivation) and each skill's
returned SKILL.md body, received this turn -- all four were genuinely
invoked at that point; the lines below describe what that invocation
confirmed against what had already been reasoned informally, not a claim
that invocation happened during the original development work.

skill-verdict: experiment-trust — applied: invoked; loaded the skill's
full SKILL.md via the Skill tool this session (after the fix commits,
during this correction). canonical: the returned SKILL.md's Step 1 (scope
gate: random assignment / real control / metric-contrast / pre-committed
horizon -- all "no" here) and Step 5 (Twyman's-law: an anomalous result
is suspected until independently checked) -- Step 1 matches
`84226988:docs/issue-3127/decisions/pre-registration.md`'s own "Scope
note" (unmodified, cited under "Why" above), and Step 5 matches this
session's motivation for reproducing the OLD mechanism's failure before
trusting the fix (see "Why" above).
skill-verdict: implementation-blueprint — applied: invoked; loaded the
skill via the Skill tool this session (after the fix commits). derived:
`python3 <skill-dir>/scripts/prep.py classify --surface backend
--single-file`, run this session -- `VETO: single file, single concern,
no callers -> no-structure`, confirming (not merely approximating) this
session's earlier informal judgment that no structural redesign was
warranted, per "Why" above.
skill-verdict: silent-failure-audit — applied: invoked; loaded the skill
via the Skill tool this session (after the fix commits). canonical: the
returned SKILL.md's Step 2 classification table, cross-checked against
`5a07342c:scripts/issue-3127/run_consumer_pair.py`'s `execute_arm()`
(already cited under "Why" above) -- both its `dispatch.returncode != 0`
early return and its `subprocess.TimeoutExpired` handler classify as
Handled (each returns a structured status dict, not an empty/no-op
catch).
skill-verdict: test-derivation — applied: invoked; loaded the skill via
the Skill tool this session (after the fix commits). canonical: the
returned SKILL.md's Step 1 scope gate (written requirements/acceptance
criteria must exist) -- the issue's own three acceptance-check commands
and three must-not clauses are those requirements; this session's 24 new
tests trace back to them (each new test file's docstring names the
defect/finding it covers, cited per-defect above). The specific technique
used -- partitioning each new function's input space
(`compute_h1_manipulation`'s four partitions: differ / identical /
on-missing / off-missing; `gate_pair_on_h1`'s three: pass-with-scorer /
pass-without-scorer / fail) -- is this skill's EP/BVA logic applied
informally to function inputs rather than a formal Given-When-Then
derivation from the acceptance criteria themselves; noted here rather
than overstated as a full application of Steps 2-12.
other mounted skills: not triggered -- work-in-english,
product-discovery-guardrail-metrics, adversarial-review,
implementation-audit, and test-depth-audit were reviewed against this
task and judged not applicable (no Korean-only prose to translate beyond
this record's own required Korean summary elsewhere in this session;
no product-discovery hypothesis stage active; no separate adversarial-
review/implementation-audit round requested for this repair; no test
suite quality question, only new-test derivation) -- none were invoked
via the Skill tool.
