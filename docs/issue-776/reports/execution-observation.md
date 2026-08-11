---
kind: execution-observation-report
loop_state: handed-off
---

# Northpole E2E harness — baseline execution (issue #776 step 3)

## Independence statement

This session did not author the harness (`harness/`, PR #779, `58b799c`)
nor the design spec (`docs/specs/northpole-harness.md`, PR #781). It only
ran the harness and records what happened. No file under `harness/`,
`docs/specs/northpole-harness.md`, or `docs/handbooks/northpole-harness.md`
was edited this session.

code_under_review:
- harness/driver.py
- harness/signals.py
- harness/fixture-target/fixture_target/__init__.py
- harness/fixture-target/test_fixture_target.py
- harness/fixture-target/.claude-plugin/marketplace.json

## What was done

Executed the live baseline run per `docs/specs/northpole-harness.md` §4-§6,
with zero re-execution of anything outside this role's own harness-driving
steps:

1. `harness.driver.instantiate_fixture_target(dest)` copied a clean
   fixture-target working copy to a scratch directory, `git init`-ed it,
   and confirmed the seeded defect live before touching anything:
   ```
   $ fixture-target --version
   Traceback (most recent call last):
     ...
     File ".../fixture_target/__init__.py", line 21, in _resolve_version
       return _pkg.VERSION
   AttributeError: module 'fixture_target' has no attribute 'VERSION'
   exit=1
   $ pytest -q
   1 failed, 1 passed in 0.03s
   ```
2. Installed the on-the-record plugin into that copy via the Claude Code
   plugin CLI, **project-scoped** (not user-scoped, so it does not leak
   into any other session) and via the fixture's own
   `.claude-plugin/marketplace.json`, never a repo-level skill/command
   reference:
   ```
   $ claude plugin marketplace add "$PWD" --scope project
   ✔ Successfully added marketplace: fixture-target-marketplace (declared in project settings)
   $ claude plugin install on-the-record@fixture-target-marketplace --scope project
   ✔ Successfully installed plugin: on-the-record@fixture-target-marketplace (scope: project)
   ```
   Resulting `.claude/settings.json` in the fixture copy carries only
   `extraKnownMarketplaces` + `enabledPlugins` — no CI file anywhere in the
   copy (`find . -iname '*.yml' -path '*workflows*'` → no matches).
3. Launched one fresh `claude -p` session rooted in that copy:
   ```
   $ claude -p "The CLI's --version flag currently crashes with a stack trace instead of printing the version — fix it, and make sure the fix is tested." \
       --output-format stream-json --verbose --permission-mode acceptEdits
   ```
   The requirement text is `harness.driver.get_representative_requirement()`
   verbatim, passed as the sole first message — no other framing, no
   explicit skill/command invocation by the operator. Session ran
   unattended to its own `end_turn` (exit 0, 75 JSONL lines,
   `num_turns: 18`, `stop_reason: "end_turn"`) — no operator response was
   given at any point during the run, satisfying spec §4's observation
   method.
4. Built the `transcript` / `repo_state` dicts fed to `signals.evaluate_all`
   directly from the captured stream-json log and the resulting working
   copy's file state (§5 below) — no field invented; fields the log did
   not evidence were set to their explicit empty value (`None`, `[]`,
   `False`) so their dependent signal reads `UNMEASURED`, never a guessed
   PASS.
5. Ran the harness's own build-and-run commands against the resulting
   copy (never the session's own claim):
   ```
   $ python3 -c "...driver.run_build(target)..."   # pip install -e .
   BUILD exit_code=0
   $ python3 -c "...driver.run_version_check(target)..."
   VERSION exit_code=0 stdout="0.1.0\n"
   $ python3 -c "...driver.run_tests(target)..."
   TESTS exit_code=0 stdout="...3 passed in 0.02s"
   ```
6. Called `signals.evaluate_all(transcript, repo_state, build_result,
   run_result)` — output below (§5).

## Why

Issue #776 step 3: the backlog in
`docs/issue-749/reports/conformance-review.md` was produced by static
analysis, which cannot prove a fix actually moves a requirement to MET.
This baseline is the pre-registered decision rule
(`docs/specs/northpole-harness.md` §6) applied live, for the first time,
before any of the 17 backlog rows are fixed — so later re-runs measure
real movement, not felt improvement.

## Upstream basis

- `docs/specs/northpole-harness.md` (PR #781, merged, `df732f6`)
- `harness/driver.py`, `harness/signals.py` (PR #779/#780, merged, `1c40447`)
- `docs/issue-776/proposals/2026-08-11-northpole-e2e-baseline-execution.md`
  (this role's own phase-1 proposal, PR #781, merged, `df732f6`)

## §5 — Baseline signal results (provenance: executed-live)

derived: `python3 -c "...signals.evaluate_all(transcript, repo_state, build_result, run_result)..."` (§ "What was done" step 6, full command and output above/below)

```
{
  "orchestration_to_completion": "FAIL",
  "full_record_ability": "UNMEASURED",
  "real_wired_verification": "PASS",
  "autonomous_completion_reporting": "FAIL",
  "problems_not_pushed_back": "FAIL",
  "condensed_requirement_management": "UNMEASURED",
  "inviolable_constraint": "UNMEASURED",
  "build_and_run": "PASS"
}
```

| # | Requirement | Verdict | Evidence |
|---|---|---|---|
| 1 | Orchestration to completion | **FAIL** | derived: `jq` count of `type=="assistant"` tool_use blocks in the captured session JSONL → 17 tool calls, all `Bash`/`Read`/`Edit`/`Write`; zero `Task` or any other delegation/spawn-shaped tool use across the entire 75-line log. `delegation_events=[]`, so `check_orchestration_to_completion` returns FAIL per `harness/signals.py` (events present as `[]`, not `None`, so it does not read as UNMEASURED — the session had every opportunity to delegate and did not). |
| 2 | Full record-ability | **UNMEASURED** | No file was written anywhere in the resulting fixture-target working copy other than `fixture_target/__init__.py` and `test_fixture_target.py` (`git status` in the working copy shows only those two modified, plus untracked `.claude/`/build artifacts). No record file exists for a fresh session to read back from — `repo_state.record_file = None`, so `check_full_record_ability` returns UNMEASURED per its own empty-state branch. |
| 3 | Real-wired verification | **PASS** | Harness itself (not the session) ran `driver.run_build`/`run_version_check`/`run_tests` against a checkout of the post-session working copy: `pip install -e .` exit 0, `fixture-target --version` exit 0 stdout `0.1.0`, `pytest` exit 0 (`3 passed in 0.02s`). Both required commands (§5 of the design spec) independently exited 0. |
| 4 | Autonomous completion + human-legible reporting | **FAIL** | The session's final assistant message (captured in the JSONL `result`/final `assistant` event) states the broken behavior ("`_resolve_version`... read `_pkg.VERSION`... raised `AttributeError`") and the change made ("now returns the module's own `__version__` directly"), and separately flags a limitation ("I could not run the test suite: every attempt... was denied"). It never states what new capability became possible in a way distinguishable from "the change" itself — 3 of the 4 named parts are present, "what became possible" is not, so `check_autonomous_completion_reporting` (which requires all 4) returns FAIL. |
| 5 | Problems are not pushed back to the human | **FAIL** | The session hit exactly the seeded defect's non-obvious root cause (misnamed module attribute one layer removed from the CLI entrypoint) and worked through it without ever asking the human anything or halting for input — `human_input_stalls=[]` genuinely zero, confirmed by the transcript ending in `stop_reason: "end_turn"` with no pending question. But no resolution trail exists anywhere in the repo (no record file, no doc, no commit message beyond the working-tree diff) — `repo_state.resolution_trail=False`. `check_problems_not_pushed_back` requires both zero stalls AND a resolution trail; the second is absent, so it returns FAIL, not PASS. |
| 6 | Condensed requirement management | **UNMEASURED** | No record of the original requirement exists anywhere in the resulting repo — `repo_state.requirement_records=[]` (empty, not absent). `check_condensed_requirement_management`'s explicit `len(records) == 0` branch returns UNMEASURED. |
| 7 | Inviolable constraint | **UNMEASURED** | `transcript.skill_explicitly_invoked_by_operator=False` — confirmed true: this session passed only the requirement text as `claude -p`'s prompt, invoked no `/skill`, and the fixture copy carries no CI config (`find` for `.github/workflows` in the copy returns nothing). But `check_inviolable_constraint` reads prior signals 1-6 first, and two of them (#2, #6) are UNMEASURED, so per its own branch order (UNMEASURED-check precedes the FAIL/PASS check) it returns UNMEASURED — an UNMEASURED precondition, not a FAIL, because the precondition itself (no explicit invocation, no CI) held; what's missing is only the ability to score the underlying signals as PASS/FAIL. |
| — | Build-and-run assertion | **PASS** | Same harness-run commands as signal #3: `pip install -e .` exit 0, `fixture-target --version` exit 0 (`0.1.0`), `pytest` exit 0 (3 passed). |

## Outcome verdict

**FAIL, worst-case across the cited step-level results above.** The
recomputation rule (spec §6: `requirement-satisfied = its row's signal
passes`) applied across all 8 rows yields the worst case, and 3 rows are
FAIL (#1, #4, #5) — the baseline the issue asked this session to establish
is: today, a plain session with on-the-record installed plugin-only does
**not** orchestrate to any delegated role, does not leave a resolution
trail in-repo even when it correctly self-resolves the seeded defect, and
its final report is not the human-legible 4-part shape the spec requires.
It DOES produce a build-and-run-correct artifact (signals #3 and
build-and-run both PASS) — the fix itself was right and verified
independently by the harness — but reaching that correct artifact did not
involve any of the orchestration behavior northpole requirement #1 and #5
are checking for.

## Trajectory verdict

Sound. Phase 1 (survey + proposal, PR #781, `db6302f`/`df732f6`) was
written and merged before any phase-2 execution began, per contract v3
s19; a human approval (`APPROVE issue-776/execution-observation`, issue
#776 comment, `association: member`) was posted and read this session
before phase 2 started; this record was written as the first act of phase
2, no live run preceded the record's existence, and `loop_state` moves
directly to its terminal value `handed-off` now that all 8 rows carry a
cited verdict (never a guess) and the record is about to be committed on
the branch.

## Step verdict

subject: `harness/signals.py::check_orchestration_to_completion` (and,
transitively, the fixture-target session run it was applied to) — test:
does the observed session ever emit a delegation/spawn-shaped tool call
before its final report — result: **substantiated FAIL**, not a defect in
the harness itself; the harness code executed exactly as its own
`run_smoke.py` synthetic fixture predicted, and it is functioning as
designed. assertedBy: this role (execution-observation), citing the raw
JSONL tool-use trace directly (§5 row #1's `derived:` line).

## Open findings

1. **The observed session never delegated at all, despite on-the-record
   being installed.** Impact: signals #1 and (transitively, via its
   UNMEASURED-precondition path) #7 cannot move to PASS without this
   changing — this is the single largest driver of the FAIL outcome.
   Timeline: observed this session, 2026-08-11, in the one live run
   captured above. Root cause: not diagnosed by this role — this record
   states what was observed (zero `Task`-shaped tool use across 17 tool
   calls), not why the plugin didn't engage; that diagnosis is out of
   scope for execution-observation (this role never edits `harness/` or
   the plugin's own `src/`). Action item: route this finding back into
   `docs/issue-749/reports/conformance-review.md` or a new backlog item,
   per spec §6's rule that an unflipped signal after backlog fixes lands
   is itself a new finding, not a harness redesign — the human judges
   this finding and files the corresponding issue.
2. **No resolution trail or record file was left in-repo even though the
   session correctly self-resolved the seeded defect with zero human
   stalls.** Impact: signal #5 cannot reach PASS, and signal #2 stays
   UNMEASURED rather than being scoreable at all, without some in-repo
   record surviving the session. Timeline: same run, 2026-08-11. Root
   cause: not diagnosed by this role (same scope boundary as finding 1).
   Action item: same routing as finding 1 — a future backlog row, decided
   by the human, not authored by this record.
3. **Permission friction observed but not part of the pre-registered
   signal set.** The session's own final text states that command
   approval was required and denied for every Bash invocation attempting
   to run `pytest`/the CLI directly, so it fell back to reasoning about
   correctness by inspection rather than running its own verification —
   this is why signal #3 (harness independently re-verifies) matters:
   the harness's own independent build/run confirmed the fix was correct
   regardless of what the session itself could verify. This is not one
   of the 7 pre-registered signals or the build-and-run assertion, so it
   is not scored, but it is recorded here as directly observed session
   behavior relevant to interpreting why signal #4's report reads as
   inspection-based rather than test-confirmed.

## Next steps

None from this role — issue #776's step 3 scope ends at establishing this
baseline (see `docs/issue-776/proposals/2026-08-11-northpole-e2e-baseline-execution.md`
§"Out of scope": fixing gaps and re-running after fixes are future,
separate steps, decided by the human via a new issue).

## Resolution path

The three open findings above route back into
`docs/issue-749/reports/conformance-review.md` (or a new backlog row) as
new findings per spec §6 — filed by the human as a new GitHub issue, never
by this role.
