---
code_under_review:
  - on-the-record/hooks/live-fire-test-guard.sh
  - on-the-record/hooks/test_live_fire_test_guard.py
  - on-the-record/hooks/hooks.json
  - docs/specs/enforcement-boundary.md
  - docs/specs/generated-paths.md
type: feature
breaking: false
canonical: python3 -m pytest -q gates/test_boundary.py gates/test_generated_paths.py on-the-record/hooks/test_gate_registration_guard.py on-the-record/hooks/test_live_fire_test_guard.py
verdict: pass
loop_state: landed
---

Subject: issue-914

# Implementation record — issue #914 step 2, mechanism (b): mandatory live-fire test for plugin gates/hooks

## What was done

Implemented mechanism (b) from the approved phase-1 proposal
(`docs/issue-914/proposals/2026-08-12-standing-real-build-and-use-verification.md`,
"Artifact type 2"), the highest-RICE candidate per that proposal's own
scoring table.

- New `on-the-record/hooks/live-fire-test-guard.sh`: `PreToolUse`+`Bash`
  hook, sibling to `gate-registration-guard.sh` on the same `git commit`
  interception point. For a newly-staged (`A`/`R`/`C`)
  `on-the-record/hooks/*.sh` or `gates/*.py` module that is (or is
  becoming, in the same commit) registered in
  `docs/specs/enforcement-boundary.md`, requires the same commit to also
  stage a live-fire test: a hook script's test must pipe a crafted
  payload via `subprocess.run(..., input=...)` into the script by name
  and assert two or more distinct exit-code outcomes (allow vs. deny); a
  gate module's test must reference and call the module from two or
  more distinct test functions. A test file merely existing (importing
  the module, asserting it exists) is refused. Escape hatch:
  commit-message trailer `Live-fire-N/A: <reason>` for a module with no
  lifecycle-event surface to live-fire. Defers the missing-registration-
  row condition to `gate-registration-guard.sh` (fails open there, no
  double-refusal). Fails open on environment gaps.
- New `on-the-record/hooks/test_live_fire_test_guard.py`: drives the
  new guard as its own caller (real git repo fixture, `bash
  live-fire-test-guard.sh` with a crafted `PreToolUse`/`Bash` stdin
  payload), the same convention `test_gate_registration_guard.py` uses.
  Covers: no-test refusal, import-only/non-live-fire test refusal, a
  genuinely live-firing test allowed, the `Live-fire-N/A` escape, an
  unregistered module left to `gate-registration-guard.sh`, and the same
  shapes for `gates/*.py` modules. This test file IS
  `live-fire-test-guard.sh`'s own required live-fire test — the new
  gate dogfoods itself.
- Registered the new hook: `on-the-record/hooks/hooks.json` (a
  `PreToolUse`/`Bash` command entry, sibling to
  `gate-registration-guard.sh`), `docs/specs/enforcement-boundary.md`
  (new row), `docs/specs/generated-paths.md` (`n/a` row — reads/
  validates only, no write call).

## Why

canonical: docs/issue-909/reports/conformance-review/survey.md
(re-cited from the approved phase-1 proposal's own "Evidence cited"
section) — `on-the-record/hooks/absorbed-branch-recut-guard.sh`: its
own test file present, doc row claiming it ships live, but no
`hooks.json` row, so it never fired in any installed session. A test
existing did not catch this; requiring the test to actually invoke the
module as a real lifecycle event closes that gap. The phase-1
proposal's RICE table ranks this mechanism at 0.48, the highest of the
three candidates, and states composition order "(b) before (a) before
(c) is meaningful" — this turn's instruction ships (b) first per that
ordering.

## Basis

- upstream: docs/issue-914/proposals/2026-08-12-standing-real-build-and-use-verification.md
- canonical: gh issue view 914 --comments
  Approval, single-account mode: `APPROVE issue-914/implementation`
  posted as an issue #914 comment by account `JiwonJung94`, listed in
  `docs/specs/approvers.md`.

## Acceptance verification

canonical: python3 -m pytest -q gates/test_boundary.py gates/test_generated_paths.py on-the-record/hooks/test_gate_registration_guard.py on-the-record/hooks/test_live_fire_test_guard.py
```
41 passed in 2.06s
```

canonical: python3 -m pytest -q on-the-record/hooks/test_live_fire_test_guard.py
```
8 passed in 0.84s
```

Both runs are this session's own terminal output, re-run against the
current staged tree.

Per-case mapping (all six functions below are collected and executed as
part of the 8-case run fenced immediately above):

- New gate/hook, no live-fire test staged -> refused:
  `t_new_hook_script_with_no_test_denies_commit`,
  `t_new_gate_module_with_no_test_denies_commit`.
- The #909 orphan shape (test file present, never live-firing) ->
  refused: `t_new_hook_script_with_non_live_fire_test_denies_commit`,
  `t_new_gate_module_with_import_only_test_denies_commit`.
- Genuinely live-firing test -> allowed:
  `t_new_hook_script_with_passing_live_fire_test_passes`,
  `t_new_gate_module_with_live_fire_test_passes`.
- `Live-fire-N/A: <reason>` escape exercised:
  `t_live_fire_n_a_trailer_exempts_commit`.
- Unregistered module deferred to `gate-registration-guard.sh` (no
  double-refusal): `t_unregistered_hook_script_left_to_gate_registration_guard`.

## What did not work

Wrote the fixture's meta-assertion
(`t_new_hook_script_with_passing_live_fire_test_passes`'s inner
`pytest` re-run of the fixture's own live-fire test) assuming this
repo's `python_functions = test_* t_*` `pytest.ini` setting would apply
inside the temp fixture directory too — it does not (`pytest.ini` is
only discovered from the real repo root), so the inner run reported "no
tests ran" instead of executing the fixture's `t_allow`/`t_deny`.

canonical: python3 -m pytest -q on-the-record/hooks/test_live_fire_test_guard.py
(first attempt, before the fix below)
```
1 failed, 7 passed in 0.89s
AssertionError: no tests ran in 0.00s
```

Fixed by passing `-o python_functions=test_* t_*` explicitly to the
inner `pytest` invocation; the corrected 8-of-8 run is fenced under
"Acceptance verification" above.

## Open findings

None.

## Next steps

Stage mechanisms (a) (target-repo deliverable acceptance-command
re-run) and (c) (general outcome-claim gate citation-shape widening)
per the phase-1 proposal's dependency order (b) before (a) before (c).

## Resolution path

None open — no findings to resolve.
