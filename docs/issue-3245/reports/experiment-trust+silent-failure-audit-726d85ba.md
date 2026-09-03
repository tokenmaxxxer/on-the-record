---
issue: 3245
role: experiment-trust+silent-failure-audit-726d85ba
author: experiment-trust+silent-failure-audit-726d85ba
skills: experiment-trust (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false
code_under_review: scripts/consumer-path/run_pair.py (2598f674fdea1a556b91e925c919f8e473d17de2)
loop_state: scope-undeclared
type: measurement
breaking: false
verdict: partial -- both fresh pairs this round (1 and 2) reached H1 for the first time in four rounds of this issue and both returned a genuine, well-evidenced manipulation-check FAILURE, not a pass: the off arm's isolation does not hold at runtime. Both pairs are correctly UNSCORED, never a tie and never fabricated. Three unrelated synthesis-path bugs that were blocking H1 from ever running are fixed and tested; the isolation leak itself is fully diagnosed with a named root cause but deliberately not patched this round (core infra, own issue). n=0 of 5 formally scored, same as every prior round, but for a newly-understood, structural reason rather than an unexplained one.
upstream:
  - path: docs/issue-3245/reports/experiment-trust+silent-failure-audit+implementation-blueprint-3edbb1a6.md
    sha: d1f769fe852f9087363825b32827f2223be6422b
  - path: scripts/consumer-path/run_pair.py
    sha: 2598f674fdea1a556b91e925c919f8e473d17de2
---

# issue-3245 — experiment-trust+silent-failure-audit-726d85ba record

## What was done

canonical: `gh issue view 3245 --comments` and `gh pr view 3270` (this
session, this turn) -- read the issue body, round 3's reopen comment
(2026-09-03T03:54:39Z), the mid-round amendment about scoring PR bodies
instead of brief content (2026-09-03T04:23:01Z), and PR #3270's own
record before starting.

### 1. Fixed three real, previously-unexercised bugs in `run_pair()`'s post-dispatch synthesis

Dispatched pair 1 fresh (`--execute`, study-companion issues 19 and 20 --
derived: `gh pr list --repo JiwonJung94/study-companion --state all`,
this session, this turn) instead of trusting the spawning prompt's "the
harness is fixed; nothing about it should need rebuilding this round."
Both arms reached `watched-to-completion` for the first time in this
issue's rounds so far -- study-companion PR #32 (on) and PR #33 (off).
`run_pair()` itself then crashed before writing `result.json`, on a bug
never exercised before because no prior real dispatch had ever reached
this line (every earlier attempt failed at watch, credential seeding,
or cleanup ordering first).

acceptance: `python3 -m pytest tests/test_issue_3245_pair_results.py
tests/test_consumer_path_trust_root.py tests/test_issue_3127_h1_and_scoring.py
tests/test_issue_3127_run_consumer_pair.py tests/test_issue_3127_run_pair.py -q`
(this session, after all three fixes below) -- result:
```
80 passed in 0.96s
```
4 new regression tests this round: one per bug below, plus 3 cases for
`_github_slug_from_local_repo`.

**Bug 1 -- class-body self-referential assignment (`NameError`).**
derived: this session's own crash traceback, this turn --
```
File "scripts/consumer-path/run_pair.py", line 442, in _P
    skill_name = skill_name
NameError: name 'skill_name' is not defined
```
`class _P: sandbox_repo = repo; skill_name = skill_name` -- Python
resolves a name ASSIGNED within a class body via the still-empty class
namespace (`LOAD_NAME`), never falling back to the enclosing function's
local scope for that same name, even though the OTHER name (`repo`) on
the line above resolves fine via closure since it is never assigned
inside the class body. Fixed in `2598f674fdea1a556b91e925c919f8e473d17de2:
scripts/consumer-path/run_pair.py`: the `_P` shim now sets attributes
after construction (`plan_shim.skill_name = skill_name`) instead of in
the class body. Regression test added in
`tests/test_issue_3245_pair_results.py`:
`test_run_pair_success_path_builds_plan_shim_without_nameerror`.

**Bug 2 -- local clone path passed where `gh -R` needs `owner/repo`.**
derived: this session's own repro, this turn, after fixing bug 1 --
`_discover_arm_branch()`'s `gh pr list -R '/home/jwjung/study-companion'`
failed outright: `expected the "[HOST/]OWNER/REPO" format`.
`run_pair()`'s own `--repo` CLI argument is documented as "a local
clone of the target sandbox repo" (correctly used elsewhere in this
same module as `cwd=repo` for `collect_verification_rounds()`/
`collect_cost()`/`execute_arm()`) but was passed straight through to
`gate_pair_on_h1()` -> `_discover_arm_branch()`, whose own existing
unit tests (`tests/test_issue_3127_h1_and_scoring.py`, written in round
3) already assumed an `owner/repo` slug. Fixed: new
`_github_slug_from_local_repo()` resolves the slug from `git -C <repo>
remote get-url origin` (handles both `https://github.com/...` and
`git@github.com:...` forms), used only for this one call site.
Regression tests added in `tests/test_issue_3245_pair_results.py`:
`test_github_slug_resolves_from_https_origin`,
`test_github_slug_resolves_from_ssh_origin`,
`test_github_slug_returns_none_not_fabricated_when_remote_lookup_fails`.

**Bug 3 -- guessed workspace rooted in the orchestrator's HOME, not the
arm's isolated HOME.** derived: this session's own repro, this turn,
after fixing bug 2 -- H1 still came back `unknown` for both arms even
though `_discover_arm_branch()` now correctly found both real PRs.
`rcp.arm_workspace_dir()` computes its guess via `spawn.py`'s
`_workspace_target_path()` -> `_workspace_base()` -> `Path.home()` --
always THIS orchestrating process's own HOME (or `MUSTER_WORK_DIR`),
never the dispatched arm's own isolated HOME `prepare_arms.py` builds.
`collect_skill_invocation()`'s own discovery-fallback reconstructs the
real workspace under `workspace.parent`, so as long as `workspace.parent`
is wrong the fallback is wrong too, regardless of how correct the
branch discovery itself is. Confirmed live: derived: `find
/tmp/consumer-path-on-home-zflb8501 -name "*.session.*.log"` (this
session, this turn) -- the on arm's real session log sat under the
arm's isolated HOME (`/tmp/consumer-path-on-home-zflb8501/
.tokenmaxxxer/work/study-companion-issue-19-product-discovery-
hypothesis-preregistration-f8d6c6a2.session.20260903T135443.2063513.log`),
never under `$MUSTER_WORKSPACE_ROOT`. Fixed: new
`_rebase_workspace_to_arm_home()` swaps the HOME prefix on the
already-computed leaf name; correct because `_clean_base_env()` already
strips `MUSTER_WORK_DIR` from every arm's env (it matches the
`MUSTER_*` leak-prone regex), so an arm always falls back to its own
HOME's default `.tokenmaxxxer/work`. Regression tests added in
`tests/test_issue_3245_pair_results.py`:
`test_rebase_workspace_to_arm_home_swaps_home_prefix`,
`test_rebase_workspace_to_arm_home_passes_through_none`.

Round 3's own comment sitting directly above this code already made
almost exactly this diagnosis in prose ("each arm's own
`$HOME/.tokenmaxxxer/work/...`, not this orchestrating session's
`$MUSTER_WORKSPACE_ROOT`") but it never turned into a code change,
because round 3's own pair-2 attempt never reached this line either (it
failed at the `--session`/cleanup-order bugs one step earlier).

silent-failure-audit (invoked via Skill tool this session): all three
bugs above match this skill's target shape -- an operation that looks
like it succeeded (returns a `Path`, no exception at the call site) but
is silently wrong, discovered only by tracing what the returned value
is actually used for downstream. None of the three were caught by round
3's own unit tests because those tests mocked exactly the pieces this
round's bugs live in.

### 2. Pair 1: H1 fired for the first time, found a real off-arm isolation leak

With bugs 1-3 fixed, pair 1's H1 gate successfully read BOTH arms' real
session logs (first time this round) and returned a genuine
manipulation-check FAILURE.

derived: off arm's session log
(`/tmp/consumer-path-off-home-fciaymq1/.tokenmaxxxer/work/study-
companion-issue-20-product-discovery-hypothesis-preregistration-
106af0d0.session.20260903T140029.2090156.log`), read this session:
```
{"type":"assistant","message":{...,"content":[{"type":"tool_use","id":"toolu_01U8YPPC2pdfBpMwjgeArvsg","name":"Skill","input":{"skill":"product-discovery-hypothesis-preregistration"}...
{"type":"user","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"toolu_01U8YPPC2pdfBpMwjgeArvsg","content":"Launching skill: product-discovery-hypothesis-preregistration"}]},...,"tool_use_result":{"success":true,"commandName":"product-discovery-hypothesis-preregistration"}}
{"type":"user","message":{"role":"user","content":[{"type":"text","text":"Base directory for this skill: /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-3245-experiment-trust+silent-failure-audit-726d85ba/runs/rulebooks/skill-repository/skills/product-discovery-hypothesis-preregistration\n\n# Hy...
```
-- a real, SUCCESSFUL `Skill` tool_use call for the pinned skill,
served from THIS orchestrator's own repo checkout, not the off arm's
isolated HOME or its (deliberately absent) `MUSTER_SKILL_REPO` path.

derived: `python3 -c "import json,os; m=json.load(open('docs/issue-3245/
_assets/01-study-groups/manifest.json')); off=[a for a in m['arms'] if
a['arm']=='off'][0]; print(off['skills_root'],
os.path.exists(off['skills_root']))"` (this session, this turn) --
result: `/tmp/consumer-path-off-skills-absent-834a4827a73b48b0af99f5600a0873d4
False` -- confirmed absent exactly as `prepare_arms.py` intends.

Root cause: `/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/
skills.py:197-211` (`_skill_repo_root()`), read directly this session:
```
def _skill_repo_root() -> Path | None:
    env_value = os.environ.get("MUSTER_SKILL_REPO")
    if env_value:
        p = Path(os.path.expanduser(os.path.expandvars(env_value)))
        if p.is_dir():
            return p
    sibling = os.path.expandvars("$TOKENMAXXXER_RULEBOOKS/skill-repository")
    if "$" not in sibling:
        p = Path(os.path.expanduser(sibling))
        if p.is_dir():
            return p
    return _sp._skill_repo_managed_root()
```
resolution order is `MUSTER_SKILL_REPO` env (returned only `if
p.is_dir()`) -> sibling clone -> `_skill_repo_managed_root()` (a
SHARED, repo-owned, always-populated clone this orchestrator's own
checkout materializes at SessionStart, per this session's own startup
hook output: `[ensure-skills] skill-repository corpus`). When
`MUSTER_SKILL_REPO` is explicitly set but points at a path that does
not exist -- exactly `prepare_arms.py`'s off-arm strategy -- the
`is_dir()` check fails and the function silently falls through to the
next tier, indistinguishable from "never set at all." The off arm's
dispatch resolved the pinned skill from the shared managed clone,
bypassing the isolated-HOME/env-var trust root PR #3185 built.

Confirmed this is not an unconditional pass-through: the SAME off-arm
session's second, unrelated `Skill` call (the model reaching for
`hypothesis-testing` on its own, not pinned) correctly failed --
derived: same session log, this session, this turn --
```
{"type":"assistant",...,"content":[{"type":"tool_use",...,"name":"Skill","input":{"skill":"hypothesis-testing"}}]}...
{"type":"user",...,"content":[{"type":"tool_result","content":"<tool_use_error>Unknown skill: hypothesis-testing</tool_use_error>","is_error":true,...}]},...,"tool_use_result":"Error: Unknown skill: hypothesis-testing"}
```
-- the managed-clone fallback only serves skills actually present in
that shared clone; the pinned target skill happens to be present there
because every session on this machine bootstraps that same managed
clone at SessionStart, unrelated to this measurement's isolation.

Per the issue's own must-not ("do not score a pair whose manipulation
check failed; exclude it and say why"), pair 1 is UNSCORED -- full
finding recorded in `docs/issue-3245/_assets/01-study-groups/
result.json`'s `root_cause_finding` field.
acceptance: `python3 -m pytest tests/test_issue_3245_pair_results.py
tests/test_consumer_path_trust_root.py -q` (this session, after
assembling result.json) -- result:
```
24 passed in 0.87s
18 passed in 0.87s
```
acceptance: `python3 scripts/consumer-path/verify_manipulation.py --report`
(this session, this turn) -- result: exit 0, `"pairs_found": 2,
"pairs_excluded": [], "status": "reported"` (this pre-dispatch
argv/env check is a DIFFERENT, narrower check than H1 -- it correctly
still passes, since the off arm's argv/env genuinely matched the
manifest; the leak happens at runtime, inside the dispatched process,
which is exactly why H1 exists as a separate post-dispatch check).

**Not fixed this round**: `skills.py` is shared, core infrastructure
used by every `--skills skill-repo:` dispatch across the whole repo,
not scoped to this issue's consumer-path scripts. Fixing it correctly
deserves its own review and its own test suite, not a same-PR patch
bundled into a measurement round already carrying three other fixes.

### 3. Pair 2: dispatched fresh under the now-fixed synthesis path -- confirms the leak is structural

acceptance: `python3 scripts/consumer-path/run_pair.py --pair-id
02-onboarding-experiment --repo /home/jwjung/study-companion --skill
product-discovery-hypothesis-preregistration --on-issue 21 --off-issue
22 --out-dir docs/issue-3245/_assets/02-onboarding-experiment
--watch-timeout 900 --execute
--i-understand-this-spawns-real-sessions` (this session, this turn) --
ran cleanly end to end this time, no crash, and wrote `result.json`
itself (unlike pair 1, no manual synthesis replay was needed).

canonical: `docs/issue-3245/_assets/02-onboarding-experiment/result.json`
(this session's own real dispatch, this turn) -- both arms
`watched-to-completion` (`dispatch_returncode: 0`, `watch_returncode:
0`), real PRs confirmed via `gh pr list --repo JiwonJung94/study-companion
--state all` (this session, this turn): PR #34 (on, issue 21, branch
`issue-21/product-discovery-hypothesis-preregistration-8cd5e4a9`) and
PR #35 (off, issue 22, branch
`issue-22/product-discovery-hypothesis-preregistration-2cf819e7`). H1
reproduces §2's exact failure signature: off arm `mounted: []`,
`invoked: true`, `invoked_but_not_mounted: true`, same
`"reason": "the skills-off arm's session log ALSO recorded a Skill
tool_use call naming 'product-discovery-hypothesis-preregistration' --
the corpus leaked through despite the skill-repo: source-qualifier
isolation"`. Pair 2 is UNSCORED for the identical, now-confirmed-
structural reason.

Ran this second real dispatch (rather than stopping at pair 1's single
data point) specifically to distinguish "pair-1-specific fluke" from
"deterministic code path" before reporting the finding as systemic --
the identical failure signature on a different pair/skill-repo
materialization is that confirmation.

### Pairs 3-5

Not run. derived: `gh issue list --repo JiwonJung94/study-companion
--state all --json number -q 'sort_by(.number) | .[-1].number'` (this
session, this turn) -- result: `22`, confirming the six follow-up
issues pairs 3-5 need (drafted in `docs/issue-3245/decisions/drafted-
followup-issues.md`, carried forward unmodified from earlier rounds)
are still not filed. derived: `printenv CLAUDE_SKILL` (this session,
this turn) -- non-empty, the same condition `gh-guard.sh` denies `gh
issue create` under; this session cannot file them either. Unchanged
from the prior round's finding.

## Why

canonical: `docs/issue-3245/decisions/pinning-and-sample-size.md`
(carried forward unmodified, read this session) -- the pre-registered
decision rule this round's interpretation must not deviate from.

Dispatching pair 1 fresh (rather than trusting the spawning prompt's
"the harness is fixed") was the only way to find bugs 1-3: they live
exactly at the boundary no prior round's unit tests exercised (the
first successful `watched-to-completion` on both arms), and no amount
of re-reading round 3's own prose diagnosis would have surfaced them
without an actual execution reaching that code path.

Fixing bugs 1-3 but NOT the `_skill_repo_root()` isolation leak is a
deliberate scope line: the first three are local to this issue's own
launcher script, low blast radius, and directly block this issue's
stated deliverable (a scored pair requires H1 to even run). The fourth
is shared core infrastructure with a much larger blast radius (every
`--skills skill-repo:` dispatch on this machine) -- patching it
correctly needs its own review, not a rushed addition to a PR whose
primary job is producing a scored pair. Running pair 2 to confirm the
leak is structural, rather than stopping at one data point, follows the
same discipline this issue's own must-nots apply to results: a single
observation of an unusual failure gets independent confirmation before
being reported as systemic, the same posture experiment-trust's
Twyman's-law step applies to an unusual WIN.

experiment-trust (invoked via Skill tool this session): Step 1's scope
gate routes this measurement away from SRM/A-A -- a pre-assigned,
small-n paired offline comparison, not random assignment of live
traffic; `docs/issue-3245/decisions/pinning-and-sample-size.md` governs
interpretation instead, unchanged from the prior round's own routing.
Step 5 (Twyman's law): pair 1's result is not an anomalous win to
second-guess -- it is a manipulation-check FAILURE, and this skill's
own discipline for an SRM-equivalent failure applies by analogy (Step
4: "never report a treatment win or loss from a run that failed [the
gate]") -- neither pair reports an effect estimate, only the failed
gate and its investigation.

silent-failure-audit (invoked via Skill tool this session): the
`_skill_repo_root()` finding in §2 is this skill's own catalogued
"default-value substitution without recording" pattern -- `MUSTER_
SKILL_REPO` set-but-invalid is treated identically to unset, and the
function falls through to a different, unstated source without ever
recording that the explicit override was ignored. The three synthesis-
path bugs in §1 are the "operation looks like it succeeded, is silently
wrong" shape this skill's trace-forward procedure exists to catch.

## What did not work

Pair 1's first dispatch attempt (before this round's three fixes
existed) crashed mid-synthesis with the class-body `NameError` --
diagnosed in §1, not re-attempted from scratch: the real dispatch (both
arms' PRs #32/#33) was salvageable and salvaged by replaying only the
post-dispatch synthesis against the arm homes still on disk (uncleaned,
since the crash happened before `prepare_arms._cleanup()`), rather than
burning a second real dispatch to reproduce the same data.

## Upstream basis

canonical: this session's own tool transcript, this turn, for every
citation above.

- `docs/issue-3245/reports/experiment-trust+silent-failure-audit+
  implementation-blueprint-3edbb1a6.md` (PR #3270, merged, sha
  `d1f769fe852f9087363825b32827f2223be6422b`) -- the prior round's own
  record; its "each arm's own `$HOME/.tokenmaxxxer/work/...`" comment
  (already in the code as prose) is the diagnosis bug 3 above turns
  into an actual fix.
- `scripts/consumer-path/run_pair.py`
  (`2598f674fdea1a556b91e925c919f8e473d17de2`, this round's fix commit)
  -- the file all three bugs and their fixes live in.
- `/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/skills.py`
  (read, not modified, this session) -- `_skill_repo_root()`'s fallback
  chain, the root cause of §2/§3's finding.
- `docs/issue-3245/decisions/pinning-and-sample-size.md`,
  `drafted-followup-issues.md` -- the pre-registration and n<=2
  ceiling from earlier rounds, carried forward unmodified.

## Open findings

canonical: this session's own tool transcript, this turn -- the H1
findings, root-cause trace, and acceptance runs cited in full in §2-3
above.

1. **`skills.py::_skill_repo_root()` does not fail closed on an
   explicitly-invalid `MUSTER_SKILL_REPO`** -- confirmed independently
   on both pairs this round (§2, §3). Resolution path: a dedicated
   issue against `skills.py`, scoped to distinguishing "env unset" from
   "env set but invalid" and failing closed on the latter (return
   `None`/raise, never silently fall through to the managed clone).
   canonical: `/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/
   skills.py:197-211`, read and quoted in full in §2 above -- until this
   lands, no off-arm result from this consumer-path launcher (or any
   other `--skills skill-repo:` caller relying on an absent-path
   override) is expected to pass H1, and any past off-arm result that
   relied on this isolation should be treated as unverified for this
   specific guarantee.
2. **Pairs 3-5 remain unfiled.** canonical: `gh issue list --repo
   JiwonJung94/study-companion --state all` (this session, this turn,
   cited in full in "Pairs 3-5" above) -- resolution path unchanged
   from the prior round: the orchestrator files the six drafted issues
   on `JiwonJung94/study-companion` (`docs/issue-3245/decisions/drafted-
   followup-issues.md`), then a future round runs them -- though per
   finding 1, running them before the `skills.py` fix lands would only
   reproduce the same unscored result again.
3. **`collect_verification_rounds()` guesses the bare (non-
   disambiguated) branch name**, the same class of bug as bugs 1-3
   above, not yet fixed -- correctly self-reports `measured: false`
   with a reason rather than fabricating a count (canonical:
   `docs/issue-3245/_assets/{01-study-groups,02-onboarding-experiment}/
   result.json`'s `verification` fields, this session's own real
   output), so it is not a silent failure by this session's own audit
   criteria, just an unfilled metric. Resolution path: apply the same
   `_discover_arm_branch()` fallback already used for H1 to this
   collector too, in a future round.

## Next steps

canonical: `docs/issue-3245/_assets/01-study-groups/result.json` and
`docs/issue-3245/_assets/02-onboarding-experiment/result.json`, this
session's own real dispatch output, cited in full in §2-3 above.

Tally, plainly, per the round's own instruction:

| pair | H1 | H2 | tally |
|---|---|---|---|
| 01-study-groups | FAILED -- off arm invoked the pinned skill via a shared managed-clone fallback despite an absent MUSTER_SKILL_REPO | not computed (never reached; H1 gates H2) | unscored |
| 02-onboarding-experiment | FAILED -- identical signature, confirming the leak is structural | not computed | unscored |
| 03-06 | not run (issues unfiled) | -- | not attempted |

Wins: 0. Ties: 0. Losses: 0. Unscored: 2 (both pairs this round attempted
real, fresh dispatches; both correctly excluded by H1, never scored,
never called a tie). n=0 of the registered n>=5 floor formally scored
this round -- the same headline as every prior round, but the first
round to know precisely why: not a harness that cannot observe its own
arms (the prior rounds' problem, now fixed), but a trust root whose
off-arm isolation does not hold against the shared skill-repository
clone this same machine keeps warm for every other session. The
question the issue poses ("does skills-on win, and by how much") still
has no answer; this round's contribution is finding the SPECIFIC reason
no answer has ever been possible, with a named, reproducible root cause
and a resolution path (Open finding 1) that the next round -- or a
dedicated `skills.py` issue -- can act on directly, rather than
re-running the same broken isolation again.

`loop_state: scope-undeclared` -- this round's fixes are landed and
tested (§1), two pairs reached a real, honestly-reported (if unscored)
result for the first time (§2-3), and the reason nothing has ever
scored is now a specific, evidenced code defect rather than an open
question. What remains (pairs 3-5, the `skills.py` fix itself) belongs
to future rounds per the resolution paths above, not an open loop this
session is still working.

## Skill verdicts

canonical: this session's own tool transcript, this turn -- every Skill
tool invocation and its result cited below happened this session, this
turn.

- skill-verdict: silent-failure-audit — applied: invoked; used to trace
  and classify both the three synthesis-path bugs (§1) and the
  `_skill_repo_root()` fallback leak (§2) as silent-failure shapes, per
  its own catalog -- see "Why" above for the specific pattern match.
- skill-verdict: experiment-trust — applied: invoked; Step 1's scope
  gate routed this measurement away from SRM/A-A, and Step 5's
  Twyman's-law framing shaped how both pairs' manipulation-check
  failures are reported (a failed gate, never an effect estimate) --
  see "Why" above.
- other mounted skills: work-in-english applied throughout (record,
  commits, code comments in English; this end-of-turn summary in
  Korean per its own routing rule). model-routing (skill_judge's
  post-dispatch amendment pick, matched non-deterministically -- issue
  #3230's own self-disagreement measurement) attempted via Skill tool
  this session, result `Unknown skill: model-routing` -- present under
  `$MUSTER_SKILL_REGISTRY_ROOT` but not registered in this session's
  harness skill list, so it could not be loaded, same as the prior
  round's `prose-modes` precedent.
