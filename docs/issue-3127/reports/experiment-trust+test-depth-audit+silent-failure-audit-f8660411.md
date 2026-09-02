---
issue: 3127
role: experiment-trust+test-depth-audit+silent-failure-audit-f8660411
author: experiment-trust+test-depth-audit+silent-failure-audit-f8660411
skills: experiment-trust (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: true  # independent, builder-blind verification of PR #3131's own deliverable against issue #3127
loop_state: landed
code_under_review: 7f2490823ebf7cc153250935798010bad3de73f4
type: defect-verification-record
breaking: false
verdict: 3 of 3 literal acceptance checks Present, 3 of 3 must-not clauses
  Present, confound-check re-derived and holds Present. The harness's core
  manipulation is Incorrect, reproduced live in this environment -- the
  skills-off arm's MUSTER_SKILL_REPO override does not make the corpus
  present-but-empty as documented; it either fail-closes on a real
  multi-source conflict, or (using the harness's own default CLI value)
  silently resolves through ~/.claude/skills to the full real corpus,
  a source the override never touches. The H1 manipulation-check gate is
  Absent as enforcement (prose only, corroborating PR #3135). The blind
  quality scorer described in the harness's own dry-run text is Absent
  from the code entirely. Wall-clock-to-landed is Incorrect: the only
  wall-clock code stops at the spawned session's own session-end event,
  which under the unmodified two-phase protocol is at most a phase-1
  proposal PR opening, not a merge. Second independent verification of PR
  #3131; disagrees with the first (PR #3135) on scope, not on the 3+3
  literal checks -- PR #3135 did not probe the resolver mechanism, the
  blind scorer's absence, or the landing-definition gap.
upstream:
  - path: 7f249082:scripts/issue-3127/run_consumer_pair.py
    sha: 7f2490823ebf7cc153250935798010bad3de73f4
  - path: 7f249082:scripts/issue-3127/verify_preregistration.py
    sha: 7f2490823ebf7cc153250935798010bad3de73f4
  - path: 7f249082:docs/issue-3127/decisions/pre-registration.md
    sha: 7f2490823ebf7cc153250935798010bad3de73f4
  - path: 7f249082:docs/issue-3127/_assets/consumer-path-results.json
    sha: 7f2490823ebf7cc153250935798010bad3de73f4
  - path: skills.py
    sha: same-commit  # read at this session's own HEAD; unmodified
  - path: events.py
    sha: same-commit  # read at this session's own HEAD; unmodified
---

# issue-3127 — experiment-trust+test-depth-audit+silent-failure-audit-f8660411 record

## What was done

Second independent, builder-blind verification of PR #3131 (branch
`issue-3127/experiment-trust+product-discovery-hypothesis-preregistration+implementation-blueprint+silent-failure-audit-4eda8e00`,
head `7f249082`) against issue #3127.

canonical: `gh issue view 3127` output, read this session -- three
acceptance checks (`run_consumer_pair.py --dry-run`,
`test -f .../consumer-path-results.json`, `verify_preregistration.py`)
and three must-nots (no null-as-no-effect without a power statement; no
dropped arm/narrowed task set for a bad run; no standardizing away the
orchestrator's own skill selection).

canonical: `gh pr view 3131` output, read this session -- delivers the
pre-registered design and harness, `run_status: "not_executed"` by the
PR's own description, for two stated reasons (spawn.py's dispatch
self-daemonizes; real execution has real side effects this headless
session cannot confirm).

A first verification already exists (PR #3135,
`docs/issue-3127/reports/experiment-trust+adversarial-review+defect-verification-independence-from-upstream-verdicts-51782ba3.md`)
and graded all three acceptance checks and all three must-nots Present.
canonical: `gh pr diff 3135` output, read this session, after this
session's own independent checks below had already run, so its framing
did not anchor my read. Per this task's brief, my emphasis differs: not
whether the three literal checks pass, but whether the harness would
produce a valid measurement if the orchestrator actually ran it.

Setup: `git worktree add /tmp/pr3131-verify origin/issue-3127/experiment-trust+product-discovery-hypothesis-preregistration+implementation-blueprint+silent-failure-audit-4eda8e00
--detach` (head `7f249082`). All command output below ran from that
worktree unless stated otherwise. `git log --oneline -1` on that worktree
before and after this session's checks: both `7f249082` -- no commits were
added to PR #3131's own branch this session.

### The three literal acceptance checks

canonical: this session's own terminal output, run against
`/tmp/pr3131-verify`:

```
$ python3 scripts/issue-3127/run_consumer_pair.py --dry-run; echo exit=$?
=== issue-3127 consumer-path pair plan (dry run; nothing executed) ===
...
exit=0
$ test -f docs/issue-3127/_assets/consumer-path-results.json && echo PRESENT
PRESENT
$ python3 scripts/issue-3127/verify_preregistration.py; echo exit=$?
OK: pre-registration commit 84226988e930981b02d00abd30e22c83100e875f is an
ancestor of results commit 9c9801cd470129580de54b78a32abc30875de90e
exit=0
```
All three: Present.

### The three must-not clauses

canonical: `7f249082:docs/issue-3127/_assets/consumer-path-results.json`,
read directly against the PR worktree this session (not the PR's own
citation of it) -- `decision` field reads `"unmeasured -- explicitly not
reported as a null/no-effect result"`, with a `power_statement` field
naming the registered n=2's resolving power (an effect smaller than the
registered 3-point margin, "roughly one grade-band shift per pair," is
unresolvable at this n). `arms` object shows `run_status: "not_executed"`
applied uniformly to both arms and both registered pairs, not narrowed to
exclude a bad outcome.

canonical: `7f249082:docs/issue-3127/decisions/pre-registration.md`,
read directly against the PR worktree -- its "Power statement" section
carries the identical disclosure, committed before any result (per the
commit-order acceptance check above); field (e) frames n=2 as "extensible
to the full n=4 set," not an exclusion.

canonical: `7f249082:scripts/issue-3127/run_consumer_pair.py`'s
`build_plan()` function, read directly -- the `held_constant` dict's
`skill_name_argument` entry holds the `--skills <name>` argument text
itself constant (which skill the orchestrator names), not whether
`spawn.py`'s own BM25/mounting machinery runs differently per arm; the
pre-registration's field (d) lists "BM25 selection position per skill
mount" as a reported diagnostic metric, not something engineered away.

All three must-nots: Present.

### Confound check (issue #3091/#2507) -- independently re-derived, holds

derived: `python3 -m pytest test/test_spawn_cross_family_skill_selection.py -k test_family_skill_never_returned_as_cross_family_candidate`,
run this session against `/tmp/pr3131-verify`:

```
FAILED test/test_spawn_cross_family_skill_selection.py::Bm25CrossFamilySkillMatchesTest::test_family_skill_never_returned_as_cross_family_candidate
AssertionError: Lists differ:
  [PosixPath('/tmp/tmprubuneq5/implementation-blueprint')] != []
1 failed in 0.88s
```
canonical: `7f249082:pipeline.py`'s `_cross_family_candidate_corpus()`,
read directly -- the function body opens with `del skill` and its only
exclusion set is built from `_sp._STATIC_POLICY_SKILLS` (policy skills
such as `work-in-english`); no role/family exclusion exists in the
running code, confirming the docstring's own claim about itself against
the code, not just against its own description.

derived: `git log -1 --format=%ci 0879f12a` -- `2026-08-26 18:40:06
+0900` (issue #2507's landing); `git log -1 --format=%ci 573e7382` --
`2026-09-02 15:03:48 +0900` (issue #3053's paired-run commit). #2507
precedes #3053, so #3053's candidate pool already reflected the current
(non-excluding) behavior -- the confound resolution holds. Present.

### issue-3126 absence

derived: `git ls-files | grep -i issue-3126`, run in both
`/tmp/pr3131-verify` and this session's own working tree -- zero hits
in each. Present.

### Full test suite

derived: `python3 -m pytest tests/ -q`, run against `/tmp/pr3131-verify`:

```
254 passed, 2 warnings in 10.32s
```
(the 2 warnings are a pre-existing pinned-fixture divergence, issue
#3019, unrelated to this PR's own four files.)

derived: `python3 -m pytest test/ -q`, run against `/tmp/pr3131-verify`:

```
15 failed, 548 passed, 3 xfailed in 32.33s
```
The 15 failing node IDs match the spawning task's stated baseline
("test/ has 15 pre-existing failures owned by #3091"), including the
`Bm25CrossFamilySkillMatchesTest` failure already re-derived above; none
of PR #3131's own four delivered files appear as a cause in this list.

## The deeper question: will this harness produce a valid measurement?

This is where my emphasis diverges from PR #3135, which graded the 3+3
checks Present without tracing these four points against the code.

### 1. Does the skills-off arm genuinely get an unresolvable-but-present corpus?

canonical: `7f249082:scripts/issue-3127/run_consumer_pair.py` lines 10-17
(module docstring), read directly -- claims both arms call
`spawn.py --skills <same-name>`, differing only in `MUSTER_SKILL_REPO`,
pointed at either the real skill-repository checkout or "an empty sibling
directory containing nothing but a placeholder for the named skill," so
"the `--skills` resolver's fail-closed unknown-skill rejection... never
fires in the skills-off arm; the corpus is present but empty."

canonical: `skills.py:302-417`'s `resolved_skill_sources()` (this
session's own HEAD, the function `spawn.py --skills` actually calls),
read directly -- checks four sources: `skill-repo` (`MUSTER_SKILL_REPO`
env, or a sibling/managed-clone fallback per `_skill_repo_root()`,
`skills.py:96-117`, when that env is absent or invalid), `plugin`,
`local-user` (`~/.claude/skills`, `skills.py:338`), and `local-repo`
(target repo `.claude/skills`, `skills.py:339-340`). Only the first is
touched by the harness's `MUSTER_SKILL_REPO` override; the other three
are read unconditionally. If a name resolves in more than one source with
different content, `_collapse_identical_matches()` (`skills.py:273-286`)
does not collapse them and `resolved_skill_sources()` calls `sys.exit()`
(`skills.py:402-408`) -- a different, and here undocumented-for, rejection
than the "unknown skill" one the harness's docstring addresses.

derived: reproduced live this session, against this session's own actual
environment (`$MUSTER_SKILL_REGISTRY_ROOT` populated, `~/.claude/skills`
a real symlink to it):

```
$ mkdir -p /tmp/stub-skill-repo/product-discovery-hypothesis-preregistration
$ head -5 $MUSTER_SKILL_REGISTRY_ROOT/skills/product-discovery-hypothesis-preregistration/SKILL.md \
    > /tmp/stub-skill-repo/product-discovery-hypothesis-preregistration/SKILL.md
$ python3 -c "
import spawn, skills
from pathlib import Path
skills.resolved_skill_sources('product-discovery-hypothesis-preregistration',
                               Path('/tmp/stub-skill-repo'))"
SYSTEM EXIT (fail-closed): --skills: product-discovery-hypothesis-preregistration
가 둘 이상의 소스에서 겹친다 -- skill-repository(?), ~/.claude/skills
(/home/jwjung/.claude/skills/product-discovery-hypothesis-preregistration)
(precedence 는 검색 순서일 뿐 충돌을 가리지 않는다 -- ...)
```
Building the genuine empty-stub directory the harness's docstring
describes, and pointing `MUSTER_SKILL_REPO` at it, does not produce
"corpus present but empty" in this environment -- it produces a hard
fail-closed exit before the workspace/branch step, for the exact skill
name this run's pre-registration registers
(`product-discovery-hypothesis-preregistration`, per
`7f249082:docs/issue-3127/decisions/pre-registration.md`'s `--skill`
default, cross-checked against
`7f249082:scripts/issue-3127/run_consumer_pair.py`'s own
`--skill` argparse default of the same name).

canonical: `7f249082:scripts/issue-3127/run_consumer_pair.py` lines
360-366 (the `--skill-repo-off` argparse definition), read directly -- its
default value is the literal string `"<empty-sibling-dir>"`, not a real
path, and no function in this file creates such a directory (derived:
`grep -n "mkdir\|empty-sibling-dir" scripts/issue-3127/run_consumer_pair.py`
run this session against `/tmp/pr3131-verify` -- only the one argparse
default line and its help text match; no directory-creation call exists).
canonical: `skills.py:102-105`'s `_skill_repo_root()`, read directly -- an
env value that fails `Path(...).is_dir()` (true for the literal string
`"<empty-sibling-dir>"`, since no such path exists) is treated as absent,
falling through to the sibling-clone/managed-clone fallback at
`skills.py:107-117`. If either fallback resolves to the real, populated
skill-repository (plausible on a machine that has already used
`spawn.py --skills`, as this one has -- derived: this session's own
earlier `find / -maxdepth 6 -iname "*product-discovery-hypothesis*"`
output listed multiple `/tmp/skill-repo*`/`/tmp/skill-repository*`
checkouts already present on this machine), tier1 and tier3 both carry
byte-identical real content, `_collapse_identical_matches()` collapses
them, and the resolver succeeds silently with a fully populated corpus
for the "skills-off" arm. Neither failure mode (crash, or silent
full-content leak) produces the one-variable manipulation the harness's
docstring claims, and neither is caught by anything in the harness --
see finding 2.

### 2. Is H1 (directive-composition bytes differ between arms) enforced as a gate, or only computed/logged?

derived: `grep -n "^def " scripts/issue-3127/run_consumer_pair.py`, run
this session against `/tmp/pr3131-verify` -- 11 matches: `build_plan`,
`spawn_command`, `render_dry_run`, `scrub_skill_slugs`,
`collect_directive_bytes`, `collect_ledger_tokens`, `collect_metrics`,
`execute_arm`, `_os_environ`, `emit_not_executed_results`, `main`. None
compares directive-composition bytes between a pair's two arms, applies a
threshold, or refuses to count a pair toward H2/H3 if a manipulation
check fails. canonical:
`7f249082:scripts/issue-3127/run_consumer_pair.py` lines 217-221
(`collect_directive_bytes()`), read directly -- reads one workspace's
directive-directory size; nothing calls it against a pair and compares.
Given finding 1, this absence matters concretely: the silent
full-content-leak failure mode reproduced above would produce no error
signal anywhere the harness currently checks. (Corroborates PR #3135's
independent finding on the same point, not novel to this session.)

### 3. Is the blind scorer genuinely blind, with skill slugs scrubbed first?

canonical: `7f249082:scripts/issue-3127/run_consumer_pair.py` lines
196-214 (`scrub_skill_slugs()`), read directly -- implemented, redacts
only a registered known-slug list via case-insensitive exact match, not
every hyphenated token.

derived: `grep -n "scrub_skill_slugs\|evaluate_pair" scripts/issue-3127/run_consumer_pair.py`,
run this session against `/tmp/pr3131-verify`:

```
196:def scrub_skill_slugs(text: str, known_slugs: list[str]) -> tuple[str, int]:
187:                  "evaluate_pair.py, scored against the pair's own rubric")
```
`scrub_skill_slugs` is defined once and called nowhere else in the file;
`evaluate_pair` appears only inside that one dry-run comment string at
line 187, never imported, never invoked. No blind-evaluator function
exists anywhere in this PR's four delivered files. canonical:
`7f249082:docs/issue-3127/_assets/consumer-path-results.json`'s
`slug_scrub.applied_this_session: false` field, read directly -- honest
that the scrub was not run, but there is no code path in this harness
that would run it even under `--execute`: both
`emit_not_executed_results()` and the `--execute` branch's own result
dict hardcode `quality_blind_score: null` with no scoring call anywhere
in between. The blind-scoring half of the design is not partially built.

### 4. How is wall-clock-to-landed measured, and does the harness wait for landing?

canonical: `7f249082:scripts/issue-3127/run_consumer_pair.py` lines
286-318 (`execute_arm()`), read directly -- `t0 = time.monotonic()` set
before dispatch (line 287), `wall_clock_s = time.monotonic() - t0`
computed (line 310) immediately after the `spawn.py watch --follow`
subprocess call (lines 299-304) returns.

canonical: `events.py` lines 774-776 (this session's own HEAD,
unmodified), read directly:

```python
            if ev.get("type") != "session-end":
                banner_shown = True
            if ev.get("type") == "session-end":
                return rc
```
This is `_watch(..., follow=True)`'s stop condition -- it returns only
when a `session-end` event fires for the spawned session, i.e. when the
spawned session's own turn ends. canonical: `7f249082:scripts/issue-3127/run_consumer_pair.py`'s
`spawn_command()` (lines 130-140), read directly -- passes no
`--single-phase`, `--checkpoint`, or build-now signal, so the spawned
session runs under the unmodified two-phase default: a session-end at
most corresponds to a phase-1 proposal PR opening, not a merge to `main`.
Landing a phase-2 delivery needs a separate human-approval step and a
second spawned session's own session-end, and merging even that PR is a
`gh pr merge` action outside `spawn.py`'s scope. derived:
`grep -n "gh pr\|merged\|mergedAt\|pr view" scripts/issue-3127/run_consumer_pair.py`,
run this session against `/tmp/pr3131-verify` -- zero matches; no PR/board
state poll exists anywhere in the file, and `collect_metrics()`
(`7f249082:scripts/issue-3127/run_consumer_pair.py` lines 242-254) reads
only directive-directory sizes and `runs/ledger.jsonl` entries, neither
of which observes PR state.

canonical: `7f249082:scripts/issue-3127/run_consumer_pair.py` line 184
(the dry-run instrumentation-plan text), read directly -- states "wall-
clock to landed: time from spawn dispatch to the arm's PR reaching a
merged/landed state, not first output," a behavior the code traced above
does not implement. If a future session executes this harness as coded,
the H3 wall-clock figures it would report measure time-to-session-end
(at most a proposal-PR opening under the default protocol), not
time-to-landed, while the harness's own printed instrumentation plan
describes the opposite; resolution path for that gap is recorded in
"Open findings" below.

(PR #3135 independently found, and this session did not need to
re-verify live, that `execute_arm()` is additionally unreachable from
`main()`'s `--execute` branch -- canonical:
`docs/issue-3127/reports/experiment-trust+adversarial-review+defect-verification-independence-from-upstream-verdicts-51782ba3.md`
"Judgment" section 1, read this session via `gh pr diff 3135`. That
finding compounds rather than mitigates the wall-clock mismeasurement
above: the mismeasurement is currently latent, reachable only once a
future session wires `main()` to call `execute_arm()`.)

### The power question

canonical: `7f249082:docs/issue-3127/decisions/pre-registration.md`'s
"Power statement" section, read directly -- states a binary per-pair
win/loss/tie read at n=2 "has no meaningful statistical power to
distinguish a true small effect from noise under any reasonable
significance convention," frames the decision rule as a directional
threshold against fixed bars (±3-point combined margin, 50% wall-clock
guardrail, 1-round guardrail), never a significance claim, and states
what an "indistinguishable" result would and would not mean: the sample
could not resolve an effect smaller than the registered 3-point margin
("roughly one grade-band shift per pair") -- not that no such effect
exists. This is committed before any result existed, per the same
commit-order check verified in acceptance check 3 above. This satisfies
the issue's must-not clause (no null without stating the power) with a
concrete, correctly-scoped number, not boilerplate. Present.

## Why

Read every file this PR delivers directly, and traced
`resolved_skill_sources()` and `_watch()` in their actual dependency
modules (`skills.py`, `events.py`, both at this session's own unmodified
HEAD) rather than trusting the harness's own docstrings about what those
functions do -- the docstrings describe intended behavior more
optimistically than the code delivers in two places (findings 1 and 4
above). Reproduced the skill-source conflict live against this session's
real environment, because the task brief specifically asked whether the
harness would work when the orchestrator runs it, and an environment
assumption baked into a docstring is exactly the kind of claim that needs
an actual run to falsify.

Per `test-depth-audit`'s classification: `run_consumer_pair.py`'s
`--dry-run` path exercises real code and asserts a real exit code
(Genuine Assertion for what it covers); `execute_arm()`,
`collect_metrics()`, `scrub_skill_slugs()`, and the blind-scoring path it
never reaches are Dead by that skill's definition -- written, never
executed or asserted against by anything shipped in this PR. derived:
`7f249082:scripts/issue-3127/run_consumer_pair.py`'s `--execute` branch,
lines 391-408, read directly -- writes a relabeled
`emit_not_executed_results()` dict and prints "[plan] would execute," it
never calls `execute_arm()`. This matters because the harness's own
docstrings describe these paths as working, which is exactly the gap
`test-depth-audit` targets: what a codebase's comments claim to cover
versus what any execution in this PR actually backs.

Per `silent-failure-audit`: checked whether the fail-closed conflict path
in finding 1 above is itself silently absorbed on the way to
`execute_arm()`. canonical: `7f249082:scripts/issue-3127/run_consumer_pair.py`
lines 286-297, read directly:

```python
    dispatch = subprocess.run(cmd, cwd=ROOT, env={**_os_environ(), **env_override},
                               capture_output=True, text=True)
    if dispatch.returncode != 0:
        # Do not fall through to `watch` -- a session that never dispatched
        # has nothing to watch, and blocking for watch_timeout_s anyway
        # would silently absorb the dispatch failure as if it were just a
        # slow-starting session.
        return {"arm": arm.name, "issue": issue, "status": "dispatch-failed",
                "dispatch_returncode": dispatch.returncode,
                "dispatch_stderr": dispatch.stderr}
```
It is not silently absorbed -- a nonzero `spawn.py --skills` exit (the
`sys.exit()` conflict path from finding 1) is caught and reported as
`"status": "dispatch-failed"`. The actual gap is the *other* failure mode
from finding 1 -- the silent full-content leak, which produces
`dispatch.returncode == 0` (genuine success), indistinguishable in this
code from a real skills-off run, because finding 2's manipulation-check
gate is absent from the code (derived this session: the same `grep -n
"^def " scripts/issue-3127/run_consumer_pair.py` cited in finding 2
above, 11 functions, none comparing arms).

`experiment-trust` correctly routes this measurement's design away from
its SRM/A-A machinery -- canonical:
`7f249082:docs/issue-3127/decisions/pre-registration.md`'s "Scope note"
section, read directly: an offline, pre-assigned-condition, small-n
paired comparison, not an online randomized experiment at volume, so
Steps 2-6 do not apply and Step 1's own scope gate correctly routes past
them. Its Twyman's-law discipline (be more suspicious of a clean-looking
result, not less) is what motivated tracing the resolver and watch
stop-condition instead of accepting the harness's own docstrings, which
describe a clean one-variable manipulation and a landing-aware wall
clock that the code does not actually deliver.

## What did not work

None -- every check above ran to completion; no approach was attempted
and abandoned this session.

## Rationale for deviations

None. canonical: `git log --oneline -1` on `/tmp/pr3131-verify`, run both
before and after this session's checks -- `7f249082` unchanged both
times, confirming this session did not modify PR #3131's own branch, did
not merge it, and made no repository writes outside this record file. No
scope was exceeded and no approach here was swapped for another
mid-session.

## Upstream basis

- PR #3131, branch `issue-3127/experiment-trust+product-discovery-hypothesis-preregistration+implementation-blueprint+silent-failure-audit-4eda8e00`,
  head `7f249082` -- verified in a linked worktree at `/tmp/pr3131-verify`
  (untracked in this session's own working tree; all `7f249082:`-prefixed
  paths above refer to that worktree, not to a path present here).
- `skills.py` (this session's own HEAD, unmodified) -- `resolved_skill_sources()`/
  `_skill_repo_root()`/`_collapse_identical_matches()`, read and executed
  directly for finding 1.
- `events.py` (this session's own HEAD, unmodified) -- `_watch()`, read
  directly for finding 4's stop-condition.
- `7f249082:pipeline.py`'s `_cross_family_candidate_corpus()` -- read and
  cross-checked against a live test run for the confound-check
  re-derivation.
- `7f249082:test/test_spawn_cross_family_skill_selection.py` -- re-run
  live this session, not cited from the PR's own claim.
- PR #3135
  (`docs/issue-3127/reports/experiment-trust+adversarial-review+defect-verification-independence-from-upstream-verdicts-51782ba3.md`,
  untracked in this session's own working tree, read via `gh pr diff
  3135`) -- read after this session's own independent checks, for
  cross-reference only; its H1-enforcement and `execute_arm()`-dead-code
  findings are corroborated above, its skills-off-resolver, blind-scorer,
  and wall-clock-to-landed findings are new to this session.

## Open findings

canonical: this session's own findings 1-4 above (skills-off resolver
reproduction, H1-gate grep, blind-scorer grep, wall-clock stop-condition
trace), each independently derived this session as cited in place.

- The skills-off arm's corpus-emptying manipulation does not work as
  documented in this actual environment (finding 1 above). Resolution
  path: a future session executing this harness for real must first make
  `--skill-repo-off` create a real empty-stub directory (not the current
  literal-string default) AND neutralize or account for
  `~/.claude/skills` and the sandbox target repo's own `.claude/skills`,
  or use the `<source>:<name>` qualifier (`skill-repo:<name>`) to force
  resolution through only the overridden source -- none of which this PR
  implements.
- H1 is not enforced as a gate (finding 2 above; corroborates PR #3135's
  independent finding). Resolution path: write the aggregation/threshold
  code before any `--execute` run is trusted, not just fill in the
  metrics collectors that already exist.
- The blind quality scorer does not exist in code (finding 3 above).
  Resolution path: wire `scrub_skill_slugs()` into an actual evaluator
  call before H2 can be measured at all.
- Wall-clock-to-landed measures time-to-session-end, not time-to-merge
  (finding 4 above). Resolution path: add a post-watch poll against PR/
  board merged state (e.g. `gh pr view --json state,mergedAt`) before
  trusting any H3 wall-clock figure this harness reports.
- `execute_arm()` is unreachable from `main()`'s `--execute` branch
  (carried from PR #3135's independent finding, cited above as
  corroborating context, not re-verified live by this session).
- The stale `test_family_skill_never_returned_as_cross_family_candidate`
  unit test (confound-check section above) is a live, currently-failing
  test -- in issue #3091's diagnosis scope, not this issue's.

## Next steps

derived: this session's own checks -- `python3 scripts/issue-3127/run_consumer_pair.py --dry-run`
(exit 0), `test -f docs/issue-3127/_assets/consumer-path-results.json`
(present), `python3 scripts/issue-3127/verify_preregistration.py` (exit
0), `python3 -m pytest tests/ -q` (254 passed), `python3 -m pytest test/
-q` (15 pre-existing failures, 548 passed) -- all run this session
against `/tmp/pr3131-verify` and quoted in full above, plus the four
deeper-question findings and the power-statement check, all completed
this session. `loop_state: landed` -- this record commits them to this
session's own branch and this session opens a PR carrying it, per the
spawning instructions (does not merge PR #3131, does not edit PR #3131).
The open findings above remain open against PR #3131 / issue #3127, not
against this verification record.

skill-verdict: experiment-trust — applied: invoked; loaded the skill via
the Skill tool this session and applied Step 1 (scope gate: confirmed
this is not an online controlled experiment -- no random assignment --
so the SRM/A-A machinery of Steps 2-6 correctly does not apply, matching
canonical: `7f249082:docs/issue-3127/decisions/pre-registration.md`'s
"Scope note" section, read directly) and Step 5's Twyman's-law
skepticism (be more suspicious of a clean-looking result, not less) to
motivate tracing the resolver and watch stop-condition against the
harness's own optimistic docstrings instead of accepting them at face
value (see "Why" above).
skill-verdict: test-depth-audit — not-applicable: loaded the skill via
the Skill tool this session; its own first gate reads "Does a test suite
exist? No tests = nothing to audit. Route to test-derivation." PR #3131
adds zero test files (derived this session: `gh pr diff 3131
--name-only`, seven files, none under `test/` or `tests/`) -- there is no
test suite here to classify with the GA/EO/MD/HP/D taxonomy. The
record's earlier framing of `execute_arm()`/`scrub_skill_slugs()` as
"Dead" borrowed this skill's vocabulary informally for untested
application code, which is not what the skill audits (it classifies test
functions, not the code under test); that framing is corrected here to
not-applicable rather than restated as a genuine application.
skill-verdict: silent-failure-audit — applied: invoked; loaded the skill
via the Skill tool this session and applied Steps 1-3 against
`run_consumer_pair.py`'s two error-handling sites -- the
`dispatch.returncode != 0` check (Step 2: Handled, not silently
absorbed, quoted above in "Why") and the `watch` subprocess's
`TimeoutExpired` handler (`7f249082:scripts/issue-3127/run_consumer_pair.py`
lines 298-309, read directly: caught and returned as a structured
`"status": "watch-timed-out"` result, also Handled). The actual gap this
audit surfaced is not a silently-absorbed catch block but an entire
missing check (finding 2/finding 1's silent-full-content-leak path) that
no error-handling site exists to guard, since the resolver's success case
(`returncode == 0`) is not itself distinguished from the manipulation
having silently failed.
