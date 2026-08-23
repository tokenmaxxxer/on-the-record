---
code_under_review: tests/test_spawn_pipeline.py
loop_state: committing
type: fix
breaking: false
verdict: PASS
---

# Implementation record — issue #2086

Basis: 06f190b2bdbef8f24a30961a2c593b99ee012524 (branch tip at session
start). Build-now bypass (contract v3 s19a, `CORE_BUILD_NOW=1` set by
the spawning orchestrator): delivered directly, no phase-1 proposal
round.

## What was done

Added `GateRefusalExitCodeTest` to `tests/test_spawn_pipeline.py`
covering the Acceptance's four named refusal paths plus one non-refused
control:

1. `test_no_task_exits_nonzero` — `spawn.py <role>` with no task arg
   (real subprocess) asserts `returncode != 0`.
2. `test_skills_unknown_exits_nonzero` — `spawn.py <role> <task> --skills
   <unknown>` (real subprocess) asserts `returncode != 0`.
3. `test_requirement_linkage_refusal_exits_nonzero` — calls
   `spawn.require_requirement_linkage()` directly with `gates.ci
   ._approved_roles_on_issue` mocked to `set()` (phase-1) and
   `gates.requirement_linkage.check` mocked to return a violation;
   asserts `SystemExit` with `cm.exception.code != 0`.
4. `test_acceptance_shape_refusal_exits_nonzero` — same shape for
   `spawn.require_acceptance_gate()`, with `_approved_roles_on_issue`
   mocked non-empty (phase-2) and `gates.acceptance_gate.check` mocked
   to return a violation.
5. `test_dry_run_non_refused_spawn_exits_zero` — a control case: a real
   subprocess call passing every gate (`--dry-run --no-contract`, no
   `--issue`).

## Why

canonical: spawn.py:7488, spawn.py:761, spawn.py:712, spawn.py:5198,
spawn.py:9211 — read directly this session (`sys.exit("맡길 일이
없다...")`, `require_requirement_linkage`'s `sys.exit(...)`,
`require_acceptance_gate`'s `sys.exit(...)`,
`resolved_skill_sources`'s unknown-skill `sys.exit(...)`, and
`sys.exit(main())` at module `__main__` respectively).

Issue #2086 (gh issue view, this session) reported every gate refusal
('맡길 일이 없다', requirement-link, acceptance-shape, `--skills`
unknown/duplicate) printing its reason and exiting 0. The five cited
lines above show all four named refusal paths already routed through
`sys.exit(<message string>)`, propagated by `sys.exit(main())` — a
plain string argument to `sys.exit` already yields a nonzero process
exit code today.

canonical: python3 spawn.py implementation — result: FAIL (exit 1, as expected — no task arg supplied)

canonical: python3 spawn.py implementation "t" --skills bogus-skill --no-contract -C <tmp git repo> — result: FAIL (exit 1, as expected — unknown skill name)

No production code changed; the repo lacked the Acceptance's own
regression pinning this contract, so a future edit that swapped a
`sys.exit(str)` for a `print(...); return None`-style refusal would
silently regress the exit code to 0. `GateRefusalExitCodeTest` is that
pin.

## Open findings

None. (The Test-tier note below flags two slow-tier test failures in
files outside this change's write set — tracked there as scope-out,
not as an open finding here.)

## What did not work

None.

## Doc placement

- Test file: `tests/test_spawn_pipeline.py` (existing regression file
  named by the Acceptance `check:` line) — appended, not a new file.
- Record: this file, at the standard phase-2 implementation-record path
  for this issue.

## Test-tier note (issue #1518)

`.on-the-record/test-tiers.json` is present in this repo. Both tiers
apply (`spawn.py`/`tests/test_spawn_pipeline.py` are in
`trigger_change_classes`).

canonical: python3 -m pytest -q -m "not slow" (run 1, this branch) — result: FAIL, one failure under pytest-xdist parallel scheduling: tests/test_spawn_gate_wiring.py, WebToolPermissionAccess, test_read_only_tools_allowed_for_every_role. Tail of that run:

```
1 failed, 2616 passed, 18 xfailed, 3 xpassed in 37.97s
```

canonical: python3 -m pytest -q -m "not slow" (run 2, this branch, no code change between runs) — result: PASS. Tail of that run:

```
2617 passed, 18 xfailed, 3 xpassed in 39.04s
```

canonical: python3 -m pytest -q tests/test_spawn_gate_wiring.py -k test_read_only_tools_allowed_for_every_role (unmodified main, via git stash) — result: PASS. Tail of that run:

```
1 passed in 0.81s
```

Taken together — one flake under a parallel worker split, a clean
back-to-back rerun with zero code changes, and a clean standalone run
on unmodified `main` — this reads as a pre-existing worker-isolation
flake rather than something this branch's diff introduces.

canonical: python3 -m pytest -q -m slow (this branch, dispatched as a background job, same session/turn) — result: FAIL. Tail of that run:

```
FAILED tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
FAILED tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace
2 failed, 114 passed, 2 xfailed in 404.77s (0:06:44)
```

Neither failing file (`tests/test_spawn_directive_assembly.py`,
`tests/test_spawn_gate_wiring.py`) is in this change's write set, and
neither test exercises the exit-code paths this change adds coverage
for. The Ledger test's own spawned-session log (visible in the
background job's captured output) shows an internal `git diff
origin/main...HEAD` step erroring on an ambiguous-argument message,
consistent with this sandbox's detached/no-upstream git layout rather
than with anything `tests/test_spawn_pipeline.py`'s new test class
touches. A same-scope check against unmodified `main` was started but
ran past this session's remaining time and was not observed live —
this paragraph states that gap explicitly rather than asserting the
two failures are pre-existing outright.

## Next steps

Open the PR carrying this test-file change. Separately re-run the two
named slow-tier tests against unmodified `main` to close the gap noted
above, since that run did not finish inside this session.

## Resolution path

If a same-branch cause for the two slow-tier failures above turns up:
fix on this branch, push to the same PR. If they reproduce identically
on unmodified `main`: no action on this branch.

## Skill-verdicts

skill-verdict: implementation-complexity-coupling-management — not-applicable: no coupling/cohesion threshold, accessor chain, or import-direction change here — pure test-file addition against an existing file.
skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-pattern decision involved; the change adds unit tests, no new abstraction.
skill-verdict: implementation-performance-data-structure-choice — not-applicable: no data structure/algorithm/comms-scheme choice in this change.
skill-verdict: implementation-blueprint — not-applicable: single-file test addition, not multi-module structure needing an architecture decision.
skill-verdict: technical-feasibility-build-vs-buy-dependency-health — not-applicable: no dependency/vendor comparison involved.
skill-verdict: test-derivation — invoked; applied: used to shape the four Acceptance-named refusal paths plus the exit-0 control into concrete `GateRefusalExitCodeTest` cases (equivalence classes: refused-via-argparse, refused-via-requirement-linkage, refused-via-acceptance-gate, refused-via-skills-resolution, not-refused).
