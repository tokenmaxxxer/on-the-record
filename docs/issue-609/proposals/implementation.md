---
status: proposed
files:
  - docs/issue-609/reports/implementation/survey.md
  - docs/issue-609/proposals/implementation.md
  - on-the-record/hooks/delegated-judgment-gate.sh
  - gates/role_spec_shape.py
  - gates/test_role_spec_shape_open_decision.py
  - roles/specs/requirements-engineering.spec.json
  - on-the-record/hooks/test_delegated_judgment_gate_triage.py
---

# Proposal — issue #609: spec-stage open-decision triage (implementation, phase 1)

Phase 1 only: no code changes land in this PR. Grounded in
`docs/issue-609/reports/implementation/survey.md` and, per architecture's proposal (merged PR
#618), extends `on-the-record/hooks/delegated-judgment-gate.sh` inline rather than adding a new
hook file or a `gates/`-package import.

**Scout skip record**: scouting skipped this phase. Reason: the spec (architecture's proposal, its
own scout skip record for the identical reason) already fixes every design-relevant choice this
role would otherwise scout for — component boundary, reused `axis_evaluation`/two-axis-AND-gate
mechanics, OR-escalation, the four-field audit record shape, zero-install deployment surface —
leaving implementation with only a placement/wiring decision inside an already-scouted,
already-merged internal pattern (#573's own implementation, itself scouted at build time), not a
new external category needing a fresh field survey.

## Request

Build the open-decision triage step architecture designed: a thin `open_decision_item` shape a role
records when it declines to settle a spec-stage ambiguity, mechanical axis-matrix routing to the
owning role(s) (reusing #586's completed axis table), the owning role's evaluation as an
`axis_evaluation` entry verbatim, an OR-escalation gate (threshold-exceeded per #573's own AND
check, OR panel-conflict), a four-field audit record per item, and degradation to full escalation
when the judgment-capture corpus is empty (confirmed still empty by this survey) — all as inline
Python inside the existing zero-install `delegated-judgment-gate.sh` heredoc, not a new hook file.

## Constraints

- Zero-install: no `gates/`-package import and no on-the-record checkout resolution inside the
  deployed hook's heredoc (architecture proposal section 7, carried forward from #573).
- No new firing event: triage runs inside the existing `gh pr create` branch of the hook, over the
  same `paths`/`issue`/`pr_ref` the candidate-decision path already resolves (survey confirms these
  are in scope at the insertion point).
- Reuse, not re-derive: `check_axis_evaluation_entry`, `parse_axis_evaluations`,
  `reversibility_grade`/`LOW_IMPACT`, `load_roles`/`role_scope`/`glob_matches`, and the two-axis AND
  gate must not change (survey's write-surface boundary section).
- No GitHub Actions (repo standing constraint #566, restated by both prior phase-1 proposals).
- Batch-file convention: new tests live in new files, never editing an existing
  `test_role_spec_shape_batch*.py` file (survey, confirmed repo-wide convention).

## Rationale

**Chosen**: extend the deployed hook's existing heredoc with a new triage code block, inserted
before the existing panel-synthesis block, sharing its already-computed `paths`/`DEPTH`/
`LOW_IMPACT`/`ROLES` state; extend `gates/role_spec_shape.py` with one new `check_*` function
following the file's existing pattern; add the `open_decision_item` field only to
`requirements-engineering`'s spec, the role the issue's own live-evidence case names.

**Alternative considered and rejected — extend `open_decision_item` to every role's
`spec.json` in this same PR.** Rejected: the write set architecture's proposal froze never
enumerated "every role," and the survey found no existing role, other than
`requirements-engineering` per the issue's own cited incident, with a concrete need for the field
today. Widening to all ~40 role specs turns a scoped triage build into an unbounded schema
migration with no per-role evidence behind each edit, which is exactly the kind of scope growth the
scope-exceeded rule exists to prevent rather than absorb mid-build. Other roles gain the field as
their own follow-up proposals, each with its own evidence, the same way `axis_evaluation` itself was
rolled out to `architecture` first and extended role-by-role afterward (confirmed:
`roles/specs/*.spec.json` do not all carry `axis_evaluation` today).

## What will be done

1. **Thin item shape validator** — `gates/role_spec_shape.py`: add `check_open_decision_item(entry,
   owning_axes)` mirroring `check_axis_evaluation_entry`'s shape (module-level function, dict in,
   reason-list out): `item` non-empty string, `source_role` non-empty string, `source_path`
   resolvable path reference, `candidate_axes` a non-empty list drawn from the closed
   `_JUDGMENT_AXES` set already defined in this file.
2. **Schema field** — `roles/specs/requirements-engineering.spec.json`: add `open_decision_item` to
   `required_fields` as `{"name": "open_decision_item", "type": "ref[]", "required": false}`,
   mirroring `axis_evaluation`'s own declaration mechanism (same field-type, same optional-presence
   convention).
3. **Triage code path** — `on-the-record/hooks/delegated-judgment-gate.sh`: insert a new block in
   the `gh pr create` branch, after `ROLES`/`paths`/`DEPTH`/`LOW_IMPACT` are computed and before the
   existing candidate-decision panel-synthesis logic runs. For each `open_decision_item` entry found
   in the PR's changed role-record file(s): resolve `candidate_axes` against `ROLES[*]
   ["judgment_axes"]` to the owning role(s) (mechanical lookup, reusing `role_scope`-style matching,
   no new fan-out algorithm per architecture section 2); look up each owning role's latest matching
   `axis_evaluation` via the existing `latest_axis_evaluation`; apply the OR-escalation gate —
   escalate when `not (DEPTH and LOW_IMPACT)` (threshold-exceeded, reusing the existing boolean) OR
   the owning roles' verdicts conflict (mixed `supports`/`contradicts` on the same item); write
   `docs/issue-<n>/decisions/triage-<sequence>.md` with the four-field shape (derivation_source,
   impact_grade, evaluating_roles, decision, timestamp) per architecture section 5; post the same
   `_gh` issue/PR comment pattern the existing panel path already uses.
4. **Tests**:
   - `gates/test_role_spec_shape_open_decision.py`: unit tests for `check_open_decision_item`
     (valid entry passes; missing/empty `item`, invalid `candidate_axes` entry, missing
     `source_path` each fail with a reason) and for `requirements-engineering.spec.json` passing the
     existing `check()` shape test with the new field present.
   - `on-the-record/hooks/test_delegated_judgment_gate_triage.py`: extracts the hook's heredoc
     Python and execs it against constructed fixture repos (git worktree temp dirs), covering: (a)
     empty-corpus degradation — an `open_decision_item` present, `docs/product` absent or empty,
     asserting the item's `triage-*.md` record shows `decision: escalated` for the threshold reason;
     (b) OR-escalation via panel-conflict — non-empty corpus made to clear depth/impact, two owning
     roles with conflicting verdicts, asserting escalation despite threshold clearing; (c) resolution
     path — non-empty corpus clearing depth/impact, single owning role with `supports`, asserting
     `decision: resolved` and no operator-facing escalation comment.

## Accumulation

`gates/role_spec_shape.py` gains one more `check_*` function
(`check_open_decision_item`), following the same module-level,
dict-in/reason-list-out pattern as `check`, `check_role_judgment_axes`,
`check_axis_ownership`, and `check_axis_evaluation_entry` before it. At N
more additions this file stays a flat, uniform set of independent shape
checks — there is no shared mutable state between them and no call-site
fan-out, so the file's size grows linearly with the number of record
shapes this repo defines, not with any per-call accumulation. If this
pattern ever exceeds roughly a dozen `check_*` functions, the follow-up is
splitting them into a `gates/shape_checks/` package by concern (schema vs.
role-config vs. record-entry), not rewriting this proposal's mechanism.

## Out of scope

- Extending `open_decision_item` to any role other than `requirements-engineering` (Rationale,
  above) — each additional role is its own follow-up proposal.
- The pre-registered effectiveness metric measurement itself (issue's third acceptance criterion,
  `open_decision_triage_rate`/`open_decision_misroute_rate`) — that is step 4
  (execution-observation), not implementation; this PR only builds the mechanism the metric will
  later measure.
- Any change to `check_axis_evaluation_entry`, `parse_axis_evaluations`, `reversibility_grade`,
  `load_roles`, `glob_matches`, or the existing candidate-decision panel-synthesis logic — all
  reused unmodified (survey's write-surface boundary section).
- Backfilling `triage-*.md` records for any prior PR — the mechanism is prospective only, per the
  same posture #573's own `auto-*.md`/`remediation-*.md` records take (gate-written at decision
  time, never retrofitted).
- Any GitHub Actions workflow (repo standing constraint #566).

## How you'll know it worked

- `python3 -m pytest gates/test_role_spec_shape_open_decision.py -q` passes: `check_open_decision_item`
  correctly accepts a valid entry and rejects each of the malformed cases with a reason;
  `requirements-engineering.spec.json` still passes the existing `check()` function with the new
  field present.
- `python3 -m pytest on-the-record/hooks/test_delegated_judgment_gate_triage.py -q` passes,
  demonstrating all three fixture paths live (executed, not just described): empty-corpus
  degradation escalates every item, panel-conflict escalates despite a cleared threshold, and a
  clean single-role-supports case resolves without an operator-facing escalation comment while
  still writing a `triage-<sequence>.md` audit record carrying the evaluating role's verdict.
- `python3 gates/role_spec_shape.py roles/specs/requirements-engineering.spec.json` exits 0.
- No existing test file under `gates/` or `on-the-record/hooks/` changes behavior (existing suite,
  `python3 -m pytest gates/ -q`, stays green) — confirms the reused functions were not modified.
