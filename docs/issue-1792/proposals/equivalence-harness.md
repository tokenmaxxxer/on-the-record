---
status: proposed
files:
  - docs/issue-1792/proposals/equivalence-harness.md
  - docs/issue-1792/reports/implementation/survey.md
  - test/test_convention_equivalence.py
---

## Request

#1792 (skill-axis phase 5 step 0, operator hard constraint: ZERO convention
bugs): before any consumer of the `issue-N/<role>` role-name convention
is migrated to a replacement field, build (a) a per-parser inventory of
every code site that parses or emits the convention across the 6 frozen
consumers — branch names, APPROVE token grammar, approval-gate, board
records, watch/roster, rsb status board — and (b) an equivalence-test
harness (`test/test_convention_equivalence.py`) whose golden cases capture
today's parse/emit behavior on real recorded samples, passing unmodified
on current main, so every later phase-5 sub-issue can prove its migration
is behavior-preserving against this frozen baseline. No convention change,
no parser-behavior change, no record-format change happens in this issue.

## Constraints

- Zero convention changes: this issue touches no consumer's actual
  parsing/emission code — only new test file(s) and documentation.
- The harness must pass, unmodified, against current `main` — it freezes
  today's behavior, not a target behavior.
- Golden cases must be drawn from real recorded samples (branch names,
  APPROVE comments, roster/board entries) wherever the survey found them,
  not synthesized from scratch, per requirement 2's "real recorded
  samples" wording.
- The migration-order proposal is dependency-ordered and must name each
  of the 6 consumers' planned replacement field — this issue does not
  pick the replacement field's final shape, only which field each
  consumer is expected to read post-migration, sufficient to order the
  work.
- infrastructure/no-direct-requirement: this issue produces test/docs
  infrastructure, not a user-facing feature.

## Rationale

Chosen approach: one flat pytest module,
`test/test_convention_equivalence.py`, with one test class per consumer
(6 classes) plus a `test_consumer_count` sanity test asserting the module
enumerates exactly 6 consumer classes. Each per-consumer test imports the
consumer's actual parse function/regex (`spawn._HEAD_REF_SUBJECT_RE`,
`gates.flows._BRANCH_RE`, the hook scripts' embedded regex reproduced
verbatim as string literals since hooks are heredoc'd shell+Python and not
importable, etc.) and asserts parse output against the golden samples the
survey collected (`docs/issue-227/reports/implementation/survey.md`'s real
`rsb #20`/`rsb #23` APPROVE bodies, `gates/test_delegation_metrics.py`'s
fixture comments, the repo's own `issue-1792/implementation` branch name).

Alternative considered and rejected: one test file per consumer (6 files
under `test/convention_equivalence/`). Rejected because the issue's own
acceptance shape check requires "6 ordered entries" to be checkable as a
single shape — a single module with an explicit `CONSUMERS` list (or 6
`unittest.TestCase` classes counted via `pytest --collect-only`) makes the
"consumer count == 6 asserted" acceptance check a single, cheap, mechanical
assertion instead of a directory-listing convention nobody enforces. It
also matches this repo's existing convention of one test module per
subsystem (`tests/test_flows.py`, `on-the-record/hooks/test_approval_gate.py`)
rather than introducing a new per-consumer file-splitting pattern this
issue's own scope doesn't otherwise need.

A second alternative — driving each consumer's hook-embedded regex via
subprocess invocation of the actual `.sh` file (full black-box fidelity)
instead of a literal-regex reproduction — was considered and rejected for
this step: subprocess-level black-box tests already exist for 3 of the 4
hooks (`on-the-record/hooks/test_approval_gate.py`,
`on-the-record/hooks/test_pr_preflight.py`,
`on-the-record/hooks/test_contract_guard.py`, per the survey's file
listing) and duplicating them here would not be a *new* equivalence
baseline, just a slower copy of tests already gating those files. This
harness instead pins the literal regex/needle strings the survey extracted
(quoted with file:line provenance in the survey) so a future migration
that edits any of the 4 duplicate branch-regex copies or 3+ duplicate
APPROVE-needle copies fails this harness the moment ANY copy drifts from
its pinned string — which is the actual risk the issue's "ZERO convention
bugs" constraint is worried about (one file getting the new field, a
sibling copy missing it), not hook-level behavioral regression (already
covered elsewhere).

## What will be done

1. Write `test/test_convention_equivalence.py`:
   - `CONSUMERS` = ordered list of the 6 consumer names (`branch_names`,
     `approve_grammar`, `approval_gate`, `board_records`,
     `watch_roster`, `rsb_status_board`).
   - `test_consumer_count()` — asserts `len(CONSUMERS) == 6`.
   - `BranchNamesEquivalenceTest` — golden branch strings (including the
     repo's own current branch and synthetic edge cases: uppercase role,
     digit-only role, missing role) run through all 4 pinned regex
     literals (`approval-gate.sh`, `pr-preflight.sh`, `contract-guard.sh`,
     `flows._BRANCH_RE`) and `spawn._HEAD_REF_SUBJECT_RE`/
     `spawn._LEGACY_WORKSPACE_KEY_RE`; asserts each regex's real
     match/no-match/group-extraction behavior on current main, including
     the deliberate `[\w-]+` vs `[a-z0-9-]+` charset divergence the survey
     found between the hook trio and `flows.py`.
   - `ApproveGrammarEquivalenceTest` — golden APPROVE bodies (the real
     `rsb #20`/`rsb #23` conditional-approval near-misses from the
     survey, the `gates/test_delegation_metrics.py` fixture comments, a
     synthesized well-formed case) run through the pinned exact-match
     needle logic (`approval-gate.sh`/`pr-preflight.sh`/`flows.py`) and
     the pinned prefix-match logic (`gates/ci.py`/`contract-guard.sh`),
     asserting today's approved/not-approved verdict per case for both
     semantics, including the two the survey confirmed diverge on
     purpose.
   - `ApprovalGateEquivalenceTest` — invokes `approval-gate.sh` as a
     subprocess (matching that file's existing test harness pattern in
     `on-the-record/hooks/test_approval_gate.py`) over the golden
     branch/APPROVE pairs, asserting today's allow/deny outcome.
   - `BoardRecordsEquivalenceTest` — calls `spawn.board()` against a
     synthetic `docs/issue-<n>/reports/<role>.md` tree built from the
     `ROLES` tuple, asserting the zero-parse-site finding: `board()`
     returns only entries for filenames matching `ROLES`, ignoring an
     unknown role-shaped filename placed in the same directory (the
     explicit zero-site evidence row the acceptance's "empty state"
     clause requires).
   - `WatchRosterEquivalenceTest` — golden roster/workspace-index keys
     (`issue-<n>/<role>`, `<repo>/issue-<n>/<role>`) run through
     `_live_roster_matches`, `_roster_fallback_entry`,
     `_lookup_roster_entry`'s pinned split/regex logic, asserting today's
     extracted role and lookup-key reconstruction.
   - `RsbStatusBoardEquivalenceTest` — golden `headRefName` values run
     through `gates.flows._BRANCH_RE` and `_pr_approved()`, and a golden
     issue body run through `_plan_from_body()`, asserting today's parsed
     `(subject, role)` pairs and step/role lists.
   - Golden data sourced from: `on-the-record/hooks/test_approval_gate.py`,
     `gates/test_delegation_metrics.py`, `docs/issue-227/reports/implementation/survey.md`,
     `docs/issue-227/decisions/2026-08-03-conditional-approval-canonical-form.md`,
     and the repo's own `issue-1792/implementation` branch — all cited by
     file:line in `docs/issue-1792/reports/implementation/survey.md`.
2. Run the full module and paste the all-green output (with the
   consumer-count assertion result) into `docs/issue-1792/reports/implementation.md`
   once phase-2 opens.
3. In `docs/issue-1792/reports/implementation.md` (phase-2), record the
   migration-order list: board records (1st, zero-site, no dependents to
   break) -> watch/roster (2nd, independent of APPROVE grammar) -> branch
   names (3rd) -> APPROVE grammar (4th, depends on branch names already
   being read from the replacement field) -> approval-gate (5th, depends
   on both branch names and APPROVE grammar) -> rsb status board (6th,
   depends on branch names, APPROVE grammar, and board records via
   `spawn._front_role()`), each entry naming its planned replacement
   field (e.g. board records: continue reading the `ROLES` tuple/filename
   match, unaffected — replacement field is "none, already convention-free
   at the parse layer"; branch names: a `role:` field carried in the PR/
   session metadata instead of decoded from `headRefName`; APPROVE
   grammar: an explicit `role` field in a structured approval record
   instead of string-embedded in the comment body; etc. — exact field
   names finalized in each consumer's own phase-5 sub-issue, this issue
   only fixes the order and the harness those sub-issues must pass).

## Out of scope

- Any change to `spawn.py`, `gates/flows.py`, or any `on-the-record/hooks/*.sh`
  parsing/emission logic.
- Any change to the `issue-N/<role>` branch convention, the APPROVE
  comment grammar, board record file layout, or roster key shape.
- Designing the final replacement-field schema for any consumer beyond
  naming it in the migration-order list (each consumer's own phase-5
  sub-issue owns that design).
- New CI wiring beyond adding the test file to the existing pytest
  collection (it is picked up automatically by `pytest.ini`'s
  `python_functions = test_* t_*` / default `test/` collection; no
  `test-tiers.json` change needed since it runs in the default `fast`
  tier).

## How you'll know it worked

- `python3 -m pytest test/test_convention_equivalence.py -v` passes with
  0 failures on unmodified `main`, and its output shows exactly 6
  consumer test classes plus the `test_consumer_count` assertion passing
  — pasted live into the phase-2 implementation record per acceptance 1.
- The phase-2 implementation record's migration-order section lists all
  6 sub-issues in dependency order, each naming its planned replacement
  field — a shape check (6 ordered entries x named field) recorded per
  acceptance 2.
