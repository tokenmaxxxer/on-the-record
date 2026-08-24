---
code_under_review: HEAD
loop_state: landed
type: fix
breaking: false
verdict: pass
---

# issue-2158 — implementation record

## What was done

Build-now bypass (contract v3 s19a) fired for this session (`CORE_BUILD_NOW=1`
in the spawning environment) — no proposal round, direct delivery on
`issue-2158/implementation`.

`on-the-record/hooks/pr-preflight.sh`'s phase-determination block now
recognizes `CORE_BUILD_NOW=1` as phase-2-equivalent, mirroring
`approval-gate.sh`'s existing check (issue #2007) for the same env var:
right before the final `phase = "phase2" if phase2 else "phase1"`
assignment, if `phase2` is not already true (an actual APPROVE comment or
live delegation citation) and `os.environ.get("CORE_BUILD_NOW") == "1"`, set
`phase2 = True` and write a one-line stderr note — never a silent flip.
canonical: read on-the-record/hooks/pr-preflight.sh:220-237 (build-now bypass block, inserted between the delegation-citation loop and the final phase assignment)

Extended `on-the-record/hooks/test_pr_preflight.py:368-419` with four new
end-to-end cases driving the real hook via subprocess: a `CORE_BUILD_NOW=1`
session with no approval comment and a normal `Closes #<n>` trailer; the
identical command/fixtures with no stamp (regression guard); a genuine
two-phase session (real APPROVE comment, no stamp); and
unset/`"0"`/`"false"`/`""`/`"yes"` values. Gave `_run_preflight` (same file,
:311-329) an `extra_env` parameter mirroring `test_approval_gate.py`'s own
helper shape, and made it pop `CORE_BUILD_NOW` from the inherited
environment before running.
canonical: read on-the-record/hooks/test_pr_preflight.py:311-329 (extra_env plumbing + CORE_BUILD_NOW pop) and :368-419 (new build-now bypass test section)

## Why

The three prior occurrences (#2152, #2153, #2156 sessions, per the issue
body) all paid the same cost: `pr-preflight.sh`'s phase determination only
recognizes phase-2 via an actual APPROVE comment or delegation citation,
neither of which exists for a build-now single-phase delivery by design.
`approval-gate.sh` already carries the identical `CORE_BUILD_NOW=1`
recognition for its own phase-2-shaped-write check (issue #2007) — the
issue's own "Change" section directs mirroring that exact pattern into
`pr-preflight.sh`'s phase determination, which keeps the two gates'
build-now semantics consistent instead of inventing a second shape.
canonical: read on-the-record/hooks/approval-gate.sh:178-191 (the pre-existing CORE_BUILD_NOW check this change ports)

## Upstream basis

`on-the-record/hooks/approval-gate.sh:178-191`'s existing
`CORE_BUILD_NOW == "1"` check (issue #2007) is the pattern this change ports
into `pr-preflight.sh`'s phase-determination block. `test_approval_gate.py`'s
build-now test section (issue #2007) is the pattern the four new
`test_pr_preflight.py` cases mirror.

sha: same-commit

## What will be done

(Build-now bypass — no phase-1 proposal exists to reference; scope is the
issue's own "Change"/"Acceptance" sections, reproduced here for the record.)

- `on-the-record/hooks/pr-preflight.sh`: recognize `CORE_BUILD_NOW=1` as
  phase-2-equivalent in the phase-determination block.
- `on-the-record/hooks/test_pr_preflight.py`: extend with the
  `CORE_BUILD_NOW`-stamped path.
- Fix the ambient-`CORE_BUILD_NOW` environment leak this investigation
  surfaced in pre-existing end-to-end test helpers (see What did not work).

## Out of scope

No change to `approval-gate.sh` itself (already correct, issue #2007) or to
any other phase-determination consumer. No change to the two-phase
approval-comment/delegation-citation logic — the new check is additive and
only fires when `phase2` is not already true by the existing paths.

## What did not work

Running the full suite after the `pr-preflight.sh` change surfaced three
pre-existing test helpers that construct their subprocess `env` via
`dict(os.environ)` without popping `CORE_BUILD_NOW` — they inherited this
session's own real `CORE_BUILD_NOW=1` and started failing once the new
check legitimately honored it, since their fixtures assumed phase1 with no
way to reach that outcome under an ambient build-now stamp. Fixed each with
`env.pop("CORE_BUILD_NOW", None)`, matching the isolation
`test_approval_gate.py` and the updated `test_pr_preflight.py`'s
`_run_preflight` already had.
canonical: read on-the-record/hooks/test_pr_preflight.py:876-885 (`test_hook_denies_pr_when_issue_body_fetch_fails_fail_closed`, fixed), on-the-record/hooks/test_pr_preflight_delegation.py:78-85 (`_run`, fixed), test/test_branch_role_field.py:311-329 (`_run_preflight`, fixed)

## Rationale for deviations

Build-now carries no phase-1 proposal to diverge from, but the delivered
file set is wider than the issue's literal two-file "Change"/"Acceptance"
wording (`pr-preflight.sh` + its own test file): fixing the ambient
`CORE_BUILD_NOW` leak in `test_pr_preflight_delegation.py` and
`test/test_branch_role_field.py` (see "What did not work") was required for
the new `test_pr_preflight.py` regression cases to actually mean what they
claim — without it, the full suite fails for a reason unrelated to the
feature under test, which the issue's third acceptance bullet ("pr-preflight
tests extended for the CORE_BUILD_NOW-stamped path") does not cover on its
own. Additive, not a swap of the approach the issue describes.

## Completed items (doc-placement ladder)

This implementation record is the only docs/ output this delivery produces;
no system-design or operator-facing-contract change is involved, so no
`docs/specs/`, `docs/decisions/`, or `docs/handbooks/` entry is triggered.

## Acceptance evidence

```
$ python3 -m pytest on-the-record/hooks/test_pr_preflight.py -q 2>&1 | tail -3
.....................................
37 passed in 1.33s
```
canonical: python3 -m pytest on-the-record/hooks/test_pr_preflight.py -q — pasted live run above (executed-unit)
acceptance: python3 -m pytest on-the-record/hooks/test_pr_preflight.py -q — result: pass (37 passed, 0 failed, pasted above)

```
$ python3 -m pytest on-the-record/hooks/test_pr_preflight_delegation.py -q 2>&1 | tail -3
..
2 passed in 0.93s
```
canonical: python3 -m pytest on-the-record/hooks/test_pr_preflight_delegation.py -q — pasted live run above (executed-unit)
acceptance: python3 -m pytest on-the-record/hooks/test_pr_preflight_delegation.py -q — result: pass (2 passed, 0 failed, pasted above)

```
$ python3 -m pytest gates/ test/ on-the-record/hooks/ -q 2>&1 | tail -3
2959 passed, 10 xfailed in 17.05s
```
canonical: python3 -m pytest gates/ test/ on-the-record/hooks/ -q — pasted live run above (executed-unit), run after the three env-isolation fixes in "What did not work"
acceptance: python3 -m pytest gates/ test/ on-the-record/hooks/ -q — result: pass (2959 passed, 0 failed, 10 xfailed, pasted above)

One flaky failure was observed on an earlier `on-the-record/hooks/`-only run
before the three env-isolation fixes landed:
`test_directive_diet.py::test_injection_byte_identical_across_turns_monitor_unavailable`
(a `time.sleep`-based heartbeat-staleness race under parallel `xdist`
execution, unrelated to any file this change touches).

```
$ python3 -m pytest on-the-record/hooks/test_directive_diet.py::test_injection_byte_identical_across_turns_monitor_unavailable -q 2>&1 | tail -3
.
1 passed in 2.23s
```
canonical: python3 -m pytest on-the-record/hooks/test_directive_diet.py::test_injection_byte_identical_across_turns_monitor_unavailable -q — pasted live run above (executed-unit), confirms non-reproducing in isolation
acceptance: python3 -m pytest on-the-record/hooks/test_directive_diet.py::test_injection_byte_identical_across_turns_monitor_unavailable -q — result: pass (1 passed, 0 failed, pasted above); superseded by the combined green run above.

## Skill verdicts

None — implementation-complexity-coupling-management,
implementation-design-pattern-selection,
implementation-performance-data-structure-choice, and
implementation-blueprint were all judged not-applicable to a single
env-var-check insertion mirroring an existing sibling pattern in the same
file family, and per the current skill-obligation scoping (issue #2153) a
`skill-verdict:` line is only required for a skill actually invoked via the
Skill tool this session — none was.

## Open findings

None.

## Next steps

None — loop_state is terminal (`landed`).
