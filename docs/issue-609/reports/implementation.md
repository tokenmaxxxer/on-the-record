---
code_under_review: on-the-record/hooks/delegated-judgment-gate.sh, gates/role_spec_shape.py, roles/specs/requirements-engineering.spec.json
type: feature
breaking: false
verdict: builds-clean
loop_state: landed
---

# Implementation record — issue #609 (phase 2)

## Summary of work

Implemented `docs/issue-609/proposals/implementation.md` in full, inline in the
existing zero-install `on-the-record/hooks/delegated-judgment-gate.sh` heredoc:

1. `gates/role_spec_shape.py`: added `check_open_decision_item(entry)` —
   validates `item`/`source_role`/`source_path` as non-empty strings and
   `candidate_axes` as a non-empty list drawn from the closed
   `_JUDGMENT_AXES` set, following this file's existing dict-in/reason-list-out
   `check_*` convention (no I/O, no class).
2. `roles/specs/requirements-engineering.spec.json`: added `open_decision_item`
   to `required_fields` as `{"name": "open_decision_item", "type": "ref[]",
   "required": false}`.
3. `on-the-record/hooks/delegated-judgment-gate.sh`: added a new
   open-decision-triage block inside the `gh pr create` branch. For each
   `open_decision_item` entry found in a changed `docs/issue-<n>/reports/*.md`
   file: routes it to owning role(s) via `ROLES[*]["judgment_axes"] &
   candidate_axes` overlap (mechanical, reuses `ROLES`); looks up each owning
   role's latest matching `axis_evaluation` via the existing
   `latest_axis_evaluation` (reused unmodified); escalates on
   threshold-exceeded (`not (DEPTH and LOW_IMPACT)`, the existing AND-gate
   boolean, unmodified) OR panel-conflict (mixed supports/contradicts across
   owning roles) — an OR gate, deliberately looser than the candidate-decision
   AND gate; writes a `triage-<sequence>.md` audit record under this issue's
   decisions directory (created at hook runtime, mirroring the existing
   `auto-<seq>.md` record) with the four-field shape (`derivation_source`,
   `impact_grade`, `evaluating_roles`, `decision`, `timestamp`); posts the
   same `_gh` issue/PR comment pattern the existing panel path uses.
   - `load_roles`/`ROLES`/`glob_matches`/`role_scope`/
     `parse_axis_evaluations`/`role_record_path`/`latest_axis_evaluation`/
     `rfc3339` were **relocated** earlier in the same heredoc (function bodies
     unchanged) so triage can use them — and so triage still runs and writes
     its own record — even when the existing candidate-decision AND-gate would
     otherwise `sys.exit(0)` before reaching them (the empty-corpus
     degradation case). The later, now-duplicate definitions were removed.
4. Tests:
   - `gates/test_role_spec_shape_open_decision.py` — unit tests for
     `check_open_decision_item` (valid entry; each malformed field; spec-file
     integration) — new file, per repo's batch-file convention (never edit an
     existing `test_role_spec_shape_batch*.py`).
   - `on-the-record/hooks/test_delegated_judgment_gate_triage.py` — extracts
     the heredoc's Python source the same way the shell wrapper reaches it,
     runs it via `python3 -c` against constructed fixture git repos (real
     `git init`/commit history so `git diff --name-only origin/main...HEAD`
     resolves), covering: (a) empty-corpus degradation → escalated, (b)
     panel-conflict escalates despite a cleared threshold, (c) single
     owning-role `supports` → resolved.

## Why

Per architecture's proposal (PR #618) and this role's own phase-1 proposal
(PR #627, approved via `APPROVE issue-609/implementation`): extend the
deployed hook inline rather than add a new hook file or a `gates/`-package
import, to preserve the zero-install consumer surface `#573` established.

## Upstream basis

docs/issue-609/proposals/implementation.md

## What did not work

- First triage-block placement attempt kept `ROLES`/`parse_axis_evaluations`/
  `latest_axis_evaluation` at their original definition point (after the
  existing depth/impact AND-gate early exit). Expected: triage would run
  regardless of that gate's own outcome, matching the empty-corpus-degradation
  test case. Actual: the pre-existing early exit called `sys.exit(0)` before
  reaching triage at all when the corpus was empty, so no triage record was
  ever written — fixed by relocating those function definitions (bodies
  unchanged) above the early-exit check and inserting the triage block there
  too.
- First fixture-role `write_scope` values in the new hook test used the
  issue-number-substituted path directly instead of the raw `<n>` placeholder
  form. Expected: `role_record_path` would find the role's record file.
  Actual: `role_record_path` only matches globs containing the literal `<n>`
  placeholder, so `latest_axis_evaluation` returned `None` for every role and
  `evaluating_roles` stayed empty — fixed by using the `<n>`-placeholder form
  in the fixture `roles/*.json`, mirroring real role configs.

## Open findings

None.

## Verification run (this session)

- `python3 -m pytest gates/test_role_spec_shape_open_decision.py -q` — 10 passed.
- `python3 -m pytest on-the-record/hooks/test_delegated_judgment_gate_triage.py -q` — 3 passed.
- `python3 gates/role_spec_shape.py roles/specs/requirements-engineering.spec.json` — exit 0.
- `python3 -m pytest gates/ -q` — 320 passed, 1 pre-existing failure in
  gates/test_boundary.py unrelated to this write set (`remediation_spawn.py`
  not recorded in `docs/specs/enforcement-boundary.md`) — confirmed present
  identically on `HEAD` before this change via `git stash` + re-run, not
  touched by this PR.
- `python3 -m pytest on-the-record/hooks/ -q` — 106 passed.

## Doc placement ladder

- [x] Library/format choice over a named alternative → none this build (no
  new dependency or format introduced).
- [x] Changed public signature/wire format → the new `triage-<sequence>.md`
  audit-record shape is documented above in Summary of work and in the hook's
  own inline comments (`on-the-record/hooks/delegated-judgment-gate.sh`); no
  separate decision record needed beyond what the merged architecture
  proposal (PR #618) already recorded for this mechanism.
- [x] Env var/config key/new dep/migration/setup step → none introduced.
- [x] Benchmark or investigation numbers → none (no performance work in this
  build).

## What was NOT done (deferred, per proposal's Out of scope)

- `open_decision_item` on any role other than `requirements-engineering`.
- The `open_decision_triage_rate`/`open_decision_misroute_rate` effectiveness
  measurement itself (step 4, execution-observation).
- Any GitHub Actions workflow.

Delivering PR carries `Closes #609`; step 4 (execution-observation) remains,
per the orchestrator's own tracking.
