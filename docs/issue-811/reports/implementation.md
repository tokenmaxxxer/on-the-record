---
code_under_review:
  - gates/test_capability_gates.py
type: fix
breaking: false
verdict: pass
loop_state: landed
closed_checks:
  - canonical: "git stash && python3 -m pytest gates/test_boundary.py::t_all_gates_modules_recorded gates/test_generated_paths.py::t_all_generators_recorded_and_disjoint tests/test_gates.py::t_rulebook_version_is_recorded -q; git stash pop (executed 2026-08-11, full output in ## Test run below)"
    check: "pre-existing-failure isolation — `t_all_gates_modules_recorded`
      and `t_all_generators_recorded_and_disjoint` fail identically on a
      clean tree (no uncommitted change applied), caused by issue-810/#816's
      `merge-allow-gate.sh` landing on `main` unregistered in
      `docs/specs/enforcement-boundary.md` and
      `docs/specs/generated-paths.md`, after this proposal's survey was
      written — unrelated to this diff, out of this proposal's frozen
      write set"
    code_sha:
      - gates/test_capability_gates.py
  - canonical: "docs/issue-811/reports/implementation/2026-08-11-hunt-schema-field-orphans-real-orphan-assertion.md, section '## before-landing -- stance 1' (before-landing warrant hunt, dispatched foreground 2026-08-11)"
    check: "before-landing warrant hunt (stance 1, composition) dispatched
      and concluded — finding recorded as an open finding below, matching
      an already-declared out-of-scope item in the approved proposal, not
      a blocker for this delivery"
    code_sha:
      - gates/test_capability_gates.py
---

# Implementation record — issue #811

## Summary of work

canonical: issue #811 comment `IC_kwDOTiVhs88AAAABOP2CDg` (`gh issue view 811 --json comments`, executed 2026-08-11)

Implemented the approved phase-1 proposal
(`docs/issue-811/proposals/2026-08-11-schema-field-orphans-real-orphan-assertion.md`),
approved via the issue-level comment `APPROVE issue-811/implementation`
(single-account mode, `jjongkwann`, listed in `docs/specs/approvers.md`;
comment id `IC_kwDOTiVhs88AAAABOP2CDg`, 2026-08-11T09:00:49Z).

In `gates/test_capability_gates.py`, renamed
`t_actual_tree_schema_field_orphans_catches_alive` to
`t_actual_tree_schema_field_orphans_catches_a_real_orphan`, replaced the
hardcoded `assert any("alive" in b for b in bad), bad` with a structural
`assert bad, <message>` against `gates.schema_field_orphans(root, {})`'s
real-tree output, and rewrote the docstring to record the
`decision_queue` (issue-466) → `alive` (issue-811) exhaustion lineage,
state the test intentionally pins no field name anymore, and note the
producer-skip limitation this proposal's after-proposal warrant hunt
surfaced. The assertion message states both possible root causes for any
future failure inline: every documented `docs/specs/*.md` field is now
read somewhere (test needs a fresh case), or `schema_field_orphans()`
itself regressed to never flagging anything. Real-tree dependency is
kept — no synthetic fixture was introduced — matching the proposal's
Constraints section.

canonical: docs/issue-811/reports/implementation/survey.md, section
"## Audit: same-shaped tests elsewhere" (lines 130-163)

The proposal's own text already carries the issue's third ask (enumerate
other tests with the same live-tree-name-pinning shape): the survey's
audit section identifies `t_actual_tree_ci_reachable_gates_catches_writeset_and_record_enums`
(same file, `gates/test_capability_gates.py`) as the identical brittle
shape, recorded there as a follow-up candidate, not fixed by this
delivery — restated here per this record's requirement to carry that
audit finding.

## Why

The issue's Acceptance #1 required `main` restored to green; #2 required
any future exhaustion of this shape to be self-explanatory from the
failure message alone. The proposal's Rationale section (chosen after
weighing two rejected alternatives — swapping to another single pinned
field, or dropping the real-tree dependency entirely for a synthetic
fixture) picked the structural assertion because the test's own prior
docstring already stated its true purpose as "the gate catches a real
orphaned field in the actual tree," not "the gate catches the field
named `alive`" — asserting `bad` truthy tests that stated purpose
directly and is immune to any single field's future legitimate
consumption.

## Upstream

Based on: `docs/issue-811/proposals/2026-08-11-schema-field-orphans-real-orphan-assertion.md`

## Test run

derived: `python3 -m pytest gates/test_capability_gates.py -q`
```
.........                                                                [100%]
9 passed in 0.42s
```

derived: `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q` (full acceptance command, run against the working tree with this diff applied but not yet committed)
```
=========================== short test summary info ============================
FAILED gates/test_boundary.py::t_all_gates_modules_recorded - AssertionError:...
FAILED gates/test_generated_paths.py::t_all_generators_recorded_and_disjoint
FAILED tests/test_gates.py::t_rulebook_version_is_recorded - AssertionError: ...
3 failed, 1179 passed, 2 skipped, 1 xfailed in 163.09s (0:02:43)
```

canonical: `tests/test_gates.py`, line 100 (`assert "커밋안됨" not in v`)

The third failure (`t_rulebook_version_is_recorded`) is caused by the
tree being dirty at run time (`spawn.rulebook_version` reports
`커밋안됨` — "not committed" — whenever there is an uncommitted change,
per the assertion cited above) and resolves once this change is
committed; it is not a real failure of this fix.

derived: `git stash && python3 -m pytest gates/test_boundary.py::t_all_gates_modules_recorded gates/test_generated_paths.py::t_all_generators_recorded_and_disjoint tests/test_gates.py::t_rulebook_version_is_recorded -q; git stash pop` (isolates whether the other two failures pre-exist on a clean tree, without this diff applied)
```
FF.                                                                      [100%]
=================================== FAILURES ===================================
_________________________ t_all_gates_modules_recorded _________________________
E       AssertionError: merge-allow-gate.sh 가 docs/specs/enforcement-boundary.md 에 판정(verdict)이 기록된 행으로 없다 — 기록되지 않은 게이트가 조용히 존재한다(#441).
____________________ t_all_generators_recorded_and_disjoint ____________________
E       AssertionError: merge-allow-gate.sh 가 docs/specs/generated-paths.md 에 판정이 기록된 행으로 없다 (issue #684) — 기록되지 않은 생성기가 조용히 존재한다.
=========================== short test summary info ============================
FAILED gates/test_boundary.py::t_all_gates_modules_recorded - AssertionError:...
FAILED gates/test_generated_paths.py::t_all_generators_recorded_and_disjoint
2 failed, 1 passed in 0.15s
```

canonical: `git show --stat 3d54b72` (executed 2026-08-11)

`git show --stat 3d54b72` (commit `3d54b72`, "feat(issue-810):
default-on orchestrator merge-allow gate (#816)", the tip of `main` this
branch is based on) shows it shipped `on-the-record/hooks/merge-allow-gate.sh`
via `on-the-record/hooks/hooks.json` without a corresponding entry in
`docs/specs/enforcement-boundary.md` or `docs/specs/generated-paths.md`.

Both failures reproduce identically with and without this diff applied
and are caused entirely by issue-810's commit, which landed on `main`
after this proposal's survey was written (the survey's own repro run
recorded only the one `schema_field_orphans` failure this proposal
fixes). Fixing them needs `docs/specs/enforcement-boundary.md` and
`docs/specs/generated-paths.md`, neither of which is in this proposal's
frozen write set — per the SCOPE-EXCEEDED RULE, this delivery finishes
exactly what the proposal covers and reports rather than widening
mid-build. Full detail in `## Rationale for deviations` and
`## What did not work` below.

## Hunt

canonical: docs/issue-811/reports/implementation/2026-08-11-hunt-schema-field-orphans-real-orphan-assertion.md, section "## before-landing — stance 1"

Before-landing warrant hunt (stance 1: assume this change and another
plugin's rule/gate cancel each other), dispatched foreground, appended to
the hunt record above. Verdict: FINDING — `schema_field_orphans` and its
sibling `ci_reachable_gates` gate (both in `gates/test_capability_gates.py`)
cancel each other: `ci_reachable_gates` flags `schema_field_orphans` as
unreachable from `gates/ci.py`'s real call graph, but `ci_reachable_gates`
is itself unreachable there too, so `gates/ci.py --closes-only` passes
clean despite 5 real orphaned `docs/specs/*.md` fields currently in the
tree. See `## Open findings` for disposition.

## Rationale for deviations

The proposal's Constraints section states "the survey's repro run
already shows [`schema_field_orphans`] is the only failure on `main`
right now" and frames the issue's Acceptance #1 (`pytest ... -q` returns
zero failures) as satisfied by this fix alone. Between the survey being
written and this delivery running the acceptance command, commit
`3d54b72` (issue-810, PR #816) landed on `main` and introduced two
unrelated failures (`t_all_gates_modules_recorded`,
`t_all_generators_recorded_and_disjoint`) — see `## Test run` above for
the isolating repro. Both are caused by `merge-allow-gate.sh` shipping
without a `docs/specs/enforcement-boundary.md` /
`docs/specs/generated-paths.md` registration row, entirely outside
`schema_field_orphans` and outside this proposal's frozen write set. Per
the SCOPE-EXCEEDED RULE, this delivery finishes exactly what the
proposal's write set covers (the one test this issue names) and reports
this rather than widening into `docs/specs/enforcement-boundary.md` /
`docs/specs/generated-paths.md`, which belong to a follow-up on
issue-810's own delivery, not issue-811's.

## What did not work

canonical: `## Test run` above (this record, same file)

- Expected the full acceptance command
  (`python3 -m pytest gates/ tests/ on-the-record/hooks/ -q`) to return
  zero failures once `t_actual_tree_schema_field_orphans_catches_alive`
  was fixed, per the proposal's own stated assumption that it was the
  only failure on `main`. Actual: two additional, unrelated failures are
  present, caused by issue-810's commit landing after the proposal's
  survey was written (see `## Rationale for deviations`). This delivery's
  own scoped fix is verified working in isolation per the
  `gates/test_capability_gates.py -q` run cited above (9 passed); the
  full-suite zero-failure state described by the issue's Acceptance #1 is
  not reached by this delivery alone.

## Open findings

- The before-landing warrant hunt's composition finding (`## Hunt` above)
  — `schema_field_orphans` and `ci_reachable_gates` are both unreachable
  from `gates/ci.py`'s real call graph, so neither's refusal reaches the
  actual required CI check, which is silent about 5 currently-live
  orphaned schema fields. This is the same brittle shape already named in
  the approved proposal's Out of scope section as a follow-up candidate
  (`t_actual_tree_ci_reachable_gates_catches_writeset_and_record_enums`),
  now with a concrete live repro; `gates/ci.py`'s CI-wiring is a separate
  subsystem from this issue's scope and is not touched here. Resolution
  path: a follow-up issue wiring `schema_field_orphans` and
  `ci_reachable_gates` into `gates/ci.py`'s real call graph (or
  `--closes-only` path).
- The two pre-existing failures from issue-810's `merge-allow-gate.sh`
  registration gap (`## Test run`, `## Rationale for deviations` above).
  Resolution path: a follow-up registering `merge-allow-gate.sh` in
  `docs/specs/enforcement-boundary.md` and `docs/specs/generated-paths.md`,
  most naturally owned by issue-810's delivery, not issue-811's.
