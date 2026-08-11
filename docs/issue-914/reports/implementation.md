---
code_under_review:
  - on-the-record/hooks/live-fire-test-guard.sh
  - on-the-record/hooks/test_live_fire_test_guard.py
  - on-the-record/hooks/acceptance-command-real-run-guard.sh
  - on-the-record/hooks/test_acceptance_command_real_run_guard.py
  - on-the-record/hooks/hooks.json
  - docs/specs/acceptance-commands.md
  - docs/specs/enforcement-boundary.md
  - docs/specs/generated-paths.md
type: feature
breaking: false
canonical: python3 -m pytest -q gates/test_boundary.py gates/test_generated_paths.py on-the-record/hooks/test_gate_registration_guard.py on-the-record/hooks/test_live_fire_test_guard.py on-the-record/hooks/test_acceptance_command_real_run_guard.py
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

## Next steps (superseded below — mechanism (a) now landed in this same record)

Stage mechanisms (a) (target-repo deliverable acceptance-command
re-run) and (c) (general outcome-claim gate citation-shape widening)
per the phase-1 proposal's dependency order (b) before (a) before (c).

## Resolution path

None open — no findings to resolve.

# Addendum — issue #914 step 2, mechanism (a): target-deliverable acceptance-command real-run

## What was done

Implemented mechanism (a) from the approved phase-1 proposal
(`docs/issue-914/proposals/2026-08-12-standing-real-build-and-use-verification.md`,
"Artifact type 1"), generalizing #870 candidate-b. Enforcement point is
`PreToolUse`+`Bash` on `git commit` (this turn's instruction — the
sibling-to-existing-acceptance-gates/#918-live-fire-guard shape —
rather than the phase-1 proposal's originally-sketched `Stop`/
`SubagentStop` point; both close the same gap at commit time instead of
turn-end).

- New `on-the-record/hooks/acceptance-command-real-run-guard.sh`: for a
  staged file whose content carries an `acceptance: <command> —
  result: X` citation line (X one of the three tokens `#892`'s
  `outcome_claim_citation_check` already recognizes as executed-live),
  requires the cited command to have a row in
  `docs/specs/acceptance-commands.md`, then actually re-runs it
  (`shlex.split` argv, no shell interpolation, 180s bound) against the
  real current target and refuses the commit when the real exit status
  does not match the claimed token. The "no re-run, always allowed"
  token is the degrade path. Escape hatch: `Acceptance-recheck-N/A:
  <reason>` commit trailer.
- New `docs/specs/acceptance-commands.md`: the one-time-recorded
  acceptance-command registry, mirroring #831's remote-preflight setup
  pattern — canonical: docs/issue-831/decisions/2026-08-11-setup-preflight-remote-gate.md
  (re-read this session, "Decision" section, step 3's `ledger_write`
  event). A stateless `PreToolUse` hook cannot reach spawn.py's
  orchestrator-side `ledger_write`/`runs/ledger.jsonl`, so the setup
  event is instead a durable, git-tracked row in this file — adding the
  row is the one-time setup step, discoverable the same way
  `docs/specs/approvers.md` rows already are. One row seeded for this
  repo's own target (`self`): `python3 -m pytest -q gates/
  on-the-record/hooks/`.
- New `on-the-record/hooks/test_acceptance_command_real_run_guard.py`:
  this new guard's own required live-fire test (mechanism (b),
  `live-fire-test-guard.sh`, landed earlier this issue and dogfoods
  itself here) — drives the guard as its own caller, real git repo
  fixture, crafted `PreToolUse`/`Bash` stdin payloads.
  canonical: python3 -m pytest -q on-the-record/hooks/test_acceptance_command_real_run_guard.py
  ```
  8 passed in 0.50s
  ```
  Function-name mapping, derived: python3 -m pytest -q --collect-only on-the-record/hooks/test_acceptance_command_real_run_guard.py:
  `t_no_acceptance_citation_allows_commit` (no citation, no-op),
  `t_unregistered_command_denies_commit` (unregistered command,
  refused), `t_registered_command_that_actually_passes_and_claims_pass_allows_commit`
  (real exit status matches a claimed matching-outcome token, allowed),
  `t_registered_command_that_actually_fails_but_claims_pass_denies_commit`
  (real exit status does NOT match a claimed matching-outcome token,
  refused), `t_registered_command_that_actually_fails_and_claims_fail_allows_commit`
  (real exit status matches a claimed non-matching-outcome token
  honestly, allowed), `t_unmeasured_result_never_re_run_and_always_allowed`
  (the no-re-run degrade token, always allowed),
  `t_acceptance_recheck_n_a_trailer_exempts_commit` (the trailer
  escape), `t_non_commit_command_no_ops` (a non-`git commit` command,
  no-op). Names spell out the issue's own three required scenarios: a
  recorded acceptance command that actually fails is refused, one that
  actually succeeds is allowed, and no acceptance command on record
  degrades honestly rather than a false allow.
- Registered the new hook: `on-the-record/hooks/hooks.json` (sibling
  entry to `live-fire-test-guard.sh`), `docs/specs/enforcement-boundary.md`
  (new row), `docs/specs/generated-paths.md` (`n/a` row — no
  `write_text`/`.mkdir(`/etc. call in its own staged text; it re-runs a
  recorded command via `subprocess.run`, not a file write).

## Why

canonical: docs/issue-870/proposals/2026-08-11-generalized-fake-success-detection.md
(re-cited from the phase-1 proposal's own "Evidence cited" section) —
four independent incidents where a prior finished-implementation
verdict did not survive fresh re-execution. #892 (candidate-a, already
shipped) only checks that an outcome claim's citation LOOKS like an
executed-live reference — a stale or fabricated matching-outcome
citation satisfies it identically to a genuine one. This mechanism
closes that gap by making the citation true: the recorded acceptance
command is actually re-run against the real current target at commit
time, and a mismatch between the claim and the real exit status
refuses the commit. The phase-1 proposal's own composition note
("(b) before (a) before (c) is meaningful") is satisfied — this
addendum lands after mechanism (b), in the same record, same branch.

## Basis

- upstream: docs/issue-914/proposals/2026-08-12-standing-real-build-and-use-verification.md
- upstream: this turn's own instruction (issue #914 step 2, mechanism
  (a): "Enforcement at PreToolUse on git commit, sibling to the
  existing acceptance gates and #918's live-fire guard") — the concrete
  enforcement-point choice for this addendum, narrower than and
  compatible with the phase-1 proposal's own artifact-type-1 design.
- canonical: gh issue view 914 --comments
  Approval, single-account mode: `APPROVE issue-914/implementation`
  posted as an issue #914 comment by account `JiwonJung94`, listed in
  `docs/specs/approvers.md` (same approval this record's earlier
  mechanism-(b) section already cites — one phase-2 approval covers the
  whole issue's remaining execution-plan steps).

## Acceptance verification

canonical: python3 -m pytest -q gates/test_boundary.py gates/test_generated_paths.py on-the-record/hooks/test_gate_registration_guard.py on-the-record/hooks/test_live_fire_test_guard.py on-the-record/hooks/test_acceptance_command_real_run_guard.py
```
49 passed in 2.39s
```

This session's own terminal output, re-run against the current staged
tree (includes both this addendum's own new cases and all prior
mechanism-(b)/registration/boundary/generated-paths suites, confirming
no regression).

## What did not work

None.

## Open findings

None.

## Next steps

Stage mechanism (c): general outcome-claim gate citation-shape
widening — recognize the `acceptance: ... — result: ...` shape this
addendum's guard now actually verifies, and the `live-fire: <hook path>
— result: allow|deny|log` shape mechanism (b) produces, as privileged
executed-live citations in `gates/record_lint.py`'s accepted
vocabulary. Per the phase-1 proposal's dependency order, (c) is
meaningful only once (a) and (b) exist to produce the citation shapes
it should recognize — both now do.

## Resolution path

None open — no findings to resolve.
