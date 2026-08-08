---
code_under_review:
  - roles/specs/api-design.spec.json
  - roles/specs/architecture.spec.json
  - roles/specs/data-engineering.spec.json
  - roles/specs/data-modeling.spec.json
  - roles/specs/technical-feasibility.spec.json
  - roles/specs/ml-engineering.spec.json
  - roles/specs/refactoring-legacy.spec.json
  - roles/specs/performance-engineering.spec.json
  - roles/specs/release-engineering.spec.json
  - roles/specs/test-authoring.spec.json
  - roles/specs/observability.spec.json
  - roles/specs/implementation.spec.json
  - roles/specs/incident-response.spec.json
  - roles/specs/capacity-planning.spec.json
  - roles/specs/knowledge-management.spec.json
  - roles/specs/technical-writing.spec.json
  - roles/specs/issue-retrospective.spec.json
  - roles/specs/devrel.spec.json
  - roles/specs/customer-support.spec.json
  - roles/specs/content-design.spec.json
  - roles/specs/brand-design.spec.json
  - roles/specs/localization.spec.json
  - roles/specs/ux-engineering.spec.json
  - roles/specs/sales.spec.json
  - roles/specs/marketing.spec.json
  - roles/specs/partnerships-bd.spec.json
  - roles/specs/risk-management.spec.json
  - roles/specs/finance-unit-economics.spec.json
  - roles/specs/growth-analytics.spec.json
  - roles/specs/pricing.spec.json
  - roles/specs/legal-compliance.spec.json
  - roles/specs/market-analysis.spec.json
  - roles/specs/pr-communications.spec.json
  - roles/api-design.json
  - roles/architecture.json
  - roles/data-engineering.json
  - roles/data-modeling.json
  - roles/technical-feasibility.json
  - roles/ml-engineering.json
  - roles/refactoring-legacy.json
  - roles/performance-engineering.json
  - roles/release-engineering.json
  - roles/test-authoring.json
  - roles/observability.json
  - roles/incident-response.json
  - roles/capacity-planning.json
  - roles/knowledge-management.json
  - roles/technical-writing.json
  - roles/issue-retrospective.json
  - roles/devrel.json
  - roles/customer-support.json
  - roles/content-design.json
  - roles/brand-design.json
  - roles/localization.json
  - roles/ux-engineering.json
  - roles/sales.json
  - roles/marketing.json
  - roles/partnerships-bd.json
  - roles/risk-management.json
  - roles/finance-unit-economics.json
  - roles/growth-analytics.json
  - roles/pricing.json
  - roles/legal-compliance.json
  - roles/market-analysis.json
  - roles/pr-communications.json
  - gates/test_role_spec_shape_batch3.py
  - gates/test_role_spec_shape_batch4a.py
  - gates/test_role_spec_shape_batch4b.py
  - gates/test_role_spec_shape_batch5.py
  - gates/test_role_spec_shape_batch6a.py
  - gates/test_role_spec_shape_batch6b.py
  - gates/test_role_spec_shape_batch7.py
  - gates/test_role_spec_shape_batch8a.py
  - gates/test_role_spec_shape_batch8b.py
loop_state: landed
---

# implementation record — issue-525 phase 2

Subject: issue-525. Phase 2 (contract v3 s19): opened after `APPROVE issue-525/implementation`
(single-account mode, exact-string match, posted by `JiwonJung94`, listed in `docs/specs/approvers.md`)
on the issue-525 thread. The thread carries two prior comments: a scope-clarification comment (not
approval-shaped — states the rulebook-side alignment-plan requirement, already answered in phase 1's
proposal) and the exact-string `APPROVE issue-525/implementation` match itself. No near-miss
approval-shaped comment found.

## What was done

Executed the approved phase-1 proposal
(`docs/issue-525/proposals/2026-08-09-batch-3-plus-family-split-and-order.md`) end to end, landing every
sub-batch its "What will be done" section enumerated across the build, ops/knowledge, and
commercial/risk families (full per-sub-batch role list is this proposal file's own "What will be done"
section — see `derived: grep -c '^- batch-'
docs/issue-525/proposals/2026-08-09-batch-3-plus-family-split-and-order.md` → `9`, while that same
section's own prose states "Total: 8 delivery sub-batches": an arithmetic slip in the proposal's own prose
count, not a scope change — see Rationale for deviations) as sequential commits on this one branch, per the
issue's "may split into multiple delivery PRs" being optional, not mandatory, and per this session's
headless/single-shot constraint (contract v3 s22 — no delegated work may cross a turn boundary unconsumed,
which rules out spawning separate PR-opening sessions from here):

1. New `roles/specs/<name>.spec.json` files, one per remaining role
   (`derived: ls roles/specs/*.spec.json | wc -l` → `43` total; the `code_under_review:` list above names
   every file newly added this session), each `source_standard` grounded in the role's scout-brief citation
   (`docs/issue-525/reports/implementation/scout-brief-build.md`,
   `docs/issue-525/reports/implementation/scout-brief-ops-knowledge.md`,
   `docs/issue-525/reports/implementation/scout-brief-commercial-risk.md`) — e.g. `api-design` (Spectral),
   `architecture` (MADR), `data-engineering` (dbt model contracts), `incident-response` (SRE Postmortem),
   `knowledge-management` (KCS Solve loop, `capture_point` field encoding the capture-at-resolution
   invariant), `sales` (MEDDPICC checklist), `risk-management` (NIST SP 800-161r1), `pricing` (Van
   Westendorp PSM). The scout-brief-flagged sourcing gaps (`data-modeling`, `devrel`,
   `finance-unit-economics`, `growth-analytics`) were each resolved by a one-line re-scout decision recorded
   directly in the spec's own `source_standard` field (Kimball dimensional-modeling conventions for
   `data-modeling`, with the Data Contract Specification named and rejected as duplicating
   `data-engineering`'s scope; Keystone DevRel metrics + DevRel-Qualified-Lead for `devrel`; SaaS
   unit-economics convention for `finance-unit-economics`; AARRR + North Star for `growth-analytics` — each
   spec's `source_standard` states explicitly that the field is convention/convergent-practice, not a
   ratified standard, matching the scout-briefs' own gap language rather than asserting a fabricated
   citation).
2. The corresponding `roles/<name>.json` files updated: real non-empty `write_scope` (each role's own
   `docs/issue-<n>/reports/<role>.md`, plus a role-specific artifact glob where the must-be implies a real
   artifact — `CHANGELOG.md` for `release-engineering`, `docs/decisions/*.md` for `architecture`,
   `design-tokens/*.json` for `brand-design`), 4-bucket `loop_state` (`progress`/`terminal`/`refusal`/
   `error`), and a `spec` pointer to the sibling `roles/specs/<name>.spec.json`. `roles/implementation.json`
   itself was left untouched — see Rationale for deviations.
3. Per-sub-batch `gates/test_role_spec_shape_batch<N>.py` files
   (`derived: ls gates/test_role_spec_shape_batch*.py` → the `code_under_review:` list above names each one,
   mirroring earlier batches' own `gates/test_role_spec_shape.py`/`gates/test_role_spec_shape_batch2.py`
   pattern — never editing an earlier batch's test file), each with its own `BATCH<N>_ROLES` tuple.

## Why

Issue #525 (follow-up E of #515, batch-3+), approved on the issue thread: realize the remaining role specs
the same #515 template earlier batches (#521, #524) already realized part of, per the phase-1 proposal's
own family split, scouting, and delivery order. Phase 2's job is executing the approved proposal; nothing
here introduces scope beyond what the proposal committed to on the contracts-repo side.

## Upstream basis

- `docs/issue-525/proposals/2026-08-09-batch-3-plus-family-split-and-order.md` (this branch, phase 1)
- `docs/issue-525/reports/implementation/survey.md`,
  `docs/issue-525/reports/implementation/scout-brief-build.md`,
  `docs/issue-525/reports/implementation/scout-brief-ops-knowledge.md`,
  `docs/issue-525/reports/implementation/scout-brief-commercial-risk.md`
  (phase-1 current-state survey + three-family scout pass)
- `docs/issue-515/reports/requirements-engineering.md` (the realization template this issue instantiates),
  `docs/issue-521/reports/implementation.md` (prior-batch precedent this batch mirrors: 4-bucket
  `loop_state`, non-empty `write_scope` over `report_only: true`, no-invented-enum)
- Issue #525 body + comments (scope-clarification comment, `APPROVE issue-525/implementation`)
- Commit `c29f439` (phase-1 HEAD this record reviews against)

## Acceptance mapping

- **all 43 roles have a spec file, `ls roles/specs/*.spec.json | wc -l` equals 43** — confirmed:
  `derived: ls roles/specs/*.spec.json | wc -l` → `43`.
- **same schema-validation pytest pattern over all new specs** — confirmed:
  `derived: python3 -m pytest gates/ -q -k "spec"` → `37 passed, 239 deselected`.
- **no `roles/*.json` retains empty `write_scope` without an explicit `report_only` contract, and none
  retains a single-state `loop_state`, verified by a `python -c` sweep exiting 0** — confirmed: a
  standalone sweep script over all `roles/*.json` (both list- and dict-shaped `record_fields.loop_state`
  handled) printed `derived: OK: no violations`, no failures.
- **full suite regression check** — `derived: python3 -m pytest gates/ -q` → `276 passed` (pre-existing
  baseline count, confirmed unchanged before/after this batch's edits via a `git stash`/`git stash pop`
  bisection — see Rationale for deviations for the one file that bisection caught).
- **provenance: executed-unit for sweeps; spec substance is human PR review per delivery PR** — the checks
  above were run directly in this session (executed-unit); this record does not itself judge whether each
  role's field list/enum is the *right* domain choice — that is the PR reviewer's job, same as prior
  batches' own provenance note.
- **rulebook-side alignment plan (issue-525 thread scope comment)** — already satisfied by the phase-1
  proposal's own "Rulebook-side alignment plan" section (per-family methodology-doc/hook/gate categories);
  executing it is separate sessions against each `<role>-rulebook` repo's own board, explicitly out of this
  session's write access per the proposal's own "Out of scope" section and per this role's own interaction
  protocol (never files issues or opens sessions in another repo from here).

## Rationale for deviations

The proposal's own "What will be done" section states "Total: 8 delivery sub-batches" in prose, but its own
bulleted enumeration lists more:
`derived: grep -c '^- batch-' docs/issue-525/proposals/2026-08-09-batch-3-plus-family-split-and-order.md`
→ `9` — an arithmetic slip in the proposal's own prose count, not a scope change. Built against the
bulleted enumeration (the frontmatter `files:` list and the family-split role assignments trace to that
enumeration, not the prose total), since the enumeration is what actually partitions the 33 roles with no
omission or duplicate; the prose total mismatch has no effect on which roles got a spec or which test file
owns them.

Separately: while authoring `roles/implementation.json` (one of the 33 target roles), the mechanical
write_scope/loop_state update that worked cleanly for the other roles broke the live pytest suite —
`derived: python3 -m pytest gates/ -q` → `10 failed, 266 passed` (across `test_gates_refusal.py`,
`test_record_lint.py`, `test_closes_gate_ci.py`), bisected via `git stash`/`git stash pop` to exactly this
one file. Root cause: `gates/gates.py`'s `record_enums` function (issue-377,
`CLAIM-CHECK: enum-subset roles/implementation.json:record_fields.loop_state
docs/issue-*/reports/*.md:loop_state`) reads `roles/implementation.json`'s `record_fields.loop_state` as
the live enforced enum of valid `loop_state` frontmatter values for every
`docs/issue-*/reports/implementation.md` record repo-wide — including this very record. Replacing its
existing flat list (the contract v3 progress/refusal/error/terminal vocabulary this very record's own
`loop_state:` frontmatter line draws from) with the batch's generic 4-bucket dict shape made the
`value not in allowed` check compare against dict *keys* instead of the real state vocabulary, so this
record's own terminal state would have failed enum validation repo-wide. `roles/implementation.json` was
reverted to its original, untouched content (`git checkout -- roles/implementation.json`) — its existing
`write_scope` (`["src/**", "test/**"]`, non-empty) and `loop_state` (a multi-item list, not single-state)
already satisfy issue-525's own acceptance sweep with no edit needed, so nothing here is missing
acceptance-wise. `roles/specs/implementation.spec.json` (a separate file, judged only against
`docs/specs/role-spec-template.schema.json` — no gate cross-checks it against `roles/implementation.json`)
was kept as authored.

## What did not work

- Expected the same mechanical write_scope/loop_state-dict update pattern used for the other roles to be
  safe for `roles/implementation.json` too. Actual: it silently broke `gates/gates.py`'s live enum
  enforcement (`record_enums`) for every `docs/issue-*/reports/implementation.md` record repo-wide
  (`derived: python3 -m pytest gates/ -q` → `10 failed, 266 passed`), because that one role's
  `record_fields.loop_state` is read as a real enforced vocabulary by issue-377's `CLAIM-CHECK`, not just
  descriptive metadata the way the other roles' `record_fields.loop_state` currently is (unreferenced by
  any currently-running test). Caught by running the full `gates/` suite before committing, not by the
  batch's own `-k spec` subset. Reverted the one file; see Rationale for deviations.
- Noted, not fixed (pre-existing, not introduced by this batch): the same dict-shaped
  `record_fields.loop_state` pattern already landed for earlier batches' roles (e.g.
  `roles/secure-coding.json`) carries the identical `record_enums` key-vs-value mismatch latent defect — it
  just isn't caught because no test currently exercises `record_enums` against those particular role names.
  This batch's newly dict-shaped roles (every one except `implementation`) carry the same latent gap. Not
  fixed here: `gates/gates.py` is a distinct, pre-existing module outside this issue's frozen write set (the
  proposal names `docs/specs/role-spec-template.schema.json`, `gates/role_spec_shape.py`,
  `on-the-record/hooks/role-spec-reference-guard.sh` as the unchanged shared infrastructure, not
  `gates/gates.py`), and the gap does not block this issue's own two acceptance clauses (spec-file count,
  write_scope/loop_state sweep).

## Open findings

The latent `record_enums` dict-vs-list mismatch noted above (affecting every role now carrying a
dict-shaped `record_fields.loop_state` other than `implementation`, both from prior batches and this one)
is a real gap in `gates/gates.py`'s issue-377 enum-enforcement check: it silently stops enforcing
`loop_state` value correctness for any role whose `record_fields.loop_state` is dict-shaped rather than
list-shaped, because `value not in allowed` degrades to checking dict keys instead of the real vocabulary.
It did not block this issue's acceptance (confirmed: `roles/implementation.json` — the one role this check
is actually exercised against by a live test — was reverted, keeping list-shaped `loop_state` and full
enforcement intact) but it means the same defect class exists for every other role's records the moment
anyone writes a `docs/issue-<n>/reports/<role>.md` for one of them with a `loop_state:` frontmatter value
that should be rejected. Resolution path: a follow-up issue against `gates/gates.py`'s `record_enums`
function, to flatten dict-shaped `loop_state` (union of the bucket values) before the
`value not in allowed` membership check, closing the gap for every affected role at once rather than
per-role.

Warrant-hunter dispatch: this phase-2 delivery executes an already-approved role-handoff-contract proposal
(contract v3 s19), a distinct mechanism from the warrant-directive's own proposal-approval loop — no
additional hunter dispatch was run this turn. The `record_enums` finding above was found directly by
running the acceptance and regression checks in this session, not by a hunter agent. The phase-1 proposal
turn's own before-landing hunt record is `docs/reports/2026-08-09-hunt-batch-3-plus-family-split-and-order.md`,
referenced in commit `c29f439`.
