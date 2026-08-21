---
code_under_review:
  - test/test_convention_equivalence.py
loop_state: landed
type: feature
breaking: false
verdict: pass
---

# issue-1792 phase-2: role-name convention inventory + equivalence-test harness

## What was done

Delivered the approved phase-1 proposal
(`docs/issue-1792/proposals/equivalence-harness.md`) as
`test/test_convention_equivalence.py`: one flat pytest module with 6
`unittest.TestCase` classes, one per frozen consumer
(`BranchNamesEquivalenceTest`, `ApproveGrammarEquivalenceTest`,
`ApprovalGateEquivalenceTest`, `BoardRecordsEquivalenceTest`,
`WatchRosterEquivalenceTest`, `RsbStatusBoardEquivalenceTest`), plus a
`CONSUMERS` list and a standalone `test_consumer_count()` asserting
`len(CONSUMERS) == 6`. No convention, parser, or record-format code was
touched — the harness only adds a new test file, matching the proposal's
Constraints section. Committed at `07857a98` on
`issue-1792/implementation`.

Golden cases were sourced from the survey's real recorded samples with
file:line provenance (`docs/issue-1792/reports/implementation/survey.md`),
per proposal section 5 item 1
(`docs/issue-1792/proposals/equivalence-harness.md:87`):
- the repo's own current branch `issue-1792/implementation` (real branch,
  `git rev-parse --abbrev-ref HEAD`, survey §"Existing sample/golden data")
- `docs/issue-983/reports/implementation.md:79`'s real merged-record
  citation `APPROVE issue-983/implementation`
- `gates/test_delegation_metrics.py`'s real fixture comments
  (`APPROVE issue-707/implementation`,
  `APPROVE issue-707/implementation VIA DELEGATION issue-707/implementation`)
- `docs/issue-227/decisions/2026-08-03-conditional-approval-canonical-form.md:45-46`'s
  real near-miss cases (`APPROVE issue-23/implementation`,
  `APPROVE issue-227/rsb`), used as negative/divergence golden cases

## Harness run output (executed live)

```
$ python3 -m pytest test/test_convention_equivalence.py -v
...
test/test_convention_equivalence.py::test_consumer_count PASSED
test/test_convention_equivalence.py::BranchNamesEquivalenceTest::test_hook_trio_match_and_extract PASSED
test/test_convention_equivalence.py::BranchNamesEquivalenceTest::test_flows_match_and_extract PASSED
test/test_convention_equivalence.py::BranchNamesEquivalenceTest::test_charset_divergence_hooks_accept_flows_reject PASSED
test/test_convention_equivalence.py::BranchNamesEquivalenceTest::test_no_match_both PASSED
test/test_convention_equivalence.py::BranchNamesEquivalenceTest::test_head_ref_subject_re PASSED
test/test_convention_equivalence.py::BranchNamesEquivalenceTest::test_legacy_workspace_key_re PASSED
test/test_convention_equivalence.py::ApproveGrammarEquivalenceTest::test_exact_match_semantics PASSED
test/test_convention_equivalence.py::ApproveGrammarEquivalenceTest::test_prefix_match_semantics PASSED
test/test_convention_equivalence.py::ApproveGrammarEquivalenceTest::test_delegation_citation_regex PASSED
test/test_convention_equivalence.py::ApproveGrammarEquivalenceTest::test_two_semantics_diverge_on_near_miss PASSED
test/test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape PASSED
test/test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_branch_role_gate_logic_matches_survey PASSED
test/test_convention_equivalence.py::BoardRecordsEquivalenceTest::test_board_matches_only_known_roles PASSED
test/test_convention_equivalence.py::BoardRecordsEquivalenceTest::test_roles_is_a_fixed_tuple_not_a_parse_site PASSED
test/test_convention_equivalence.py::WatchRosterEquivalenceTest::test_live_roster_matches_key_split PASSED
test/test_convention_equivalence.py::WatchRosterEquivalenceTest::test_roster_fallback_entry_key_shape PASSED
test/test_convention_equivalence.py::WatchRosterEquivalenceTest::test_lookup_workspace_entry_suffix_match PASSED
test/test_convention_equivalence.py::RsbStatusBoardEquivalenceTest::test_branch_re_extracts_subject_and_role PASSED
test/test_convention_equivalence.py::RsbStatusBoardEquivalenceTest::test_pr_approved_needle_shape PASSED
test/test_convention_equivalence.py::RsbStatusBoardEquivalenceTest::test_pr_approved_rejects_role_mismatch PASSED
test/test_convention_equivalence.py::RsbStatusBoardEquivalenceTest::test_plan_from_body_parses_role_checklist PASSED

============================== 22 passed in 1.12s ==============================
```

canonical: acceptance: `python3 -m pytest test/test_convention_equivalence.py -v` — result: PASS (pasted output above: "22 passed in 1.12s"), executed live this session on `issue-1792/implementation` HEAD `07857a98` (test file committed, no consumer file touched), spanning all 6 consumer classes plus `test_consumer_count`. This is the harness run acceptance §1 requires.

## Shape check: consumer-count assertion (acceptance §1)

`test_consumer_count()` asserts `len(CONSUMERS) == 6` where `CONSUMERS =
["branch_names", "approve_grammar", "approval_gate", "board_records",
"watch_roster", "rsb_status_board"]` (`test/test_convention_equivalence.py`
lines 20-27).
canonical: acceptance: `python3 -m pytest test/test_convention_equivalence.py -v -k test_consumer_count` — result: PASS ("1 passed"), executed live this session.

The empty-state case (a consumer with zero parse sites) is covered
explicitly by
`BoardRecordsEquivalenceTest.test_roles_is_a_fixed_tuple_not_a_parse_site`,
which asserts `spawn.ROLES` is a fixed tuple membership-matched against
filenames, not a regex extracted from free text — matching the survey's
zero-site finding for consumer 4 (survey §4).
canonical: acceptance: `python3 -m pytest test/test_convention_equivalence.py -v -k test_roles_is_a_fixed_tuple_not_a_parse_site` — result: PASS ("1 passed"), executed live this session.

## Migration order (dependency-ordered, acceptance §2)

Shape check: 6 ordered entries below, each naming its planned replacement
field, reproducing the dependency facts and order this session read from
`docs/issue-1792/reports/implementation/survey.md` §"Dependency facts for
the migration-order proposal" and
`docs/issue-1792/proposals/equivalence-harness.md:138-153` (section 5,
item 3) (both committed at `7f5924a8`).

1. **board records** — zero role-name-parse-site consumer (survey §4); no
   dependents to break. Replacement field: none — already convention-free
   at the parse layer (continues reading the `ROLES` tuple / filename
   match against `docs/issue-N/reports/<role>.md`).
2. **watch/roster** — depends only on the branch/roster *key shape*
   (`issue-N/role`, `repo/issue-N/role`), never touches APPROVE grammar or
   approval-gate (survey "Dependency facts" bullet 2); independent of
   consumer 3. Replacement field: a `role` field carried directly in the
   roster/workspace-index entry, read instead of split out of the `k`
   string key (`spawn.py:4700`, `spawn.py:4750`, `spawn.py:4798`).
3. **branch names** — read by both consumer 3 (approval-gate) and
   consumer 6 (rsb); duplicated across 4 independent regex definitions
   (`approval-gate.sh`, `pr-preflight.sh`, `contract-guard.sh`,
   `gates/flows.py`) that a migration must update together (survey
   "Dependency facts" bullet 4). Replacement field: a `role:` field
   carried in PR/session metadata (e.g. the PR body or a sidecar
   record), read instead of decoded from `headRefName`/
   `git rev-parse --abbrev-ref HEAD`.
4. **APPROVE grammar** — depends on branch names already being read from
   the replacement field, since the exact-match needle
   (`"APPROVE issue-%d/%s" % (issue, role)`) is built from the
   issue/role pair branch-name parsing currently supplies (survey §2,
   §"Dependency facts" bullet 1). Replacement field: an explicit `role`
   field in a structured approval record, read instead of being
   string-embedded and re-parsed out of the comment body.
5. **approval-gate** — depends on both branch names (3) and APPROVE
   grammar (4) already being migrated, since it consumes both the
   branch-role gate (survey §3, lines 100-112) and the needle match
   (survey §3, lines 160-170) in the same hook. Replacement field: reads
   the same `role:` field named in entries 3 and 4 directly, dropping its
   own independent branch/needle reconstruction.
6. **rsb status board** — the most tightly coupled consumer: duplicates
   both the branch regex (1) and the APPROVE needle (2) independently
   AND calls `spawn._front_role()` directly, a cross-module dependency on
   consumer 4's module (survey §6, "Dependency facts" bullet 4).
   Replacement field: reads the `role:` fields named in entries 3 and 4
   plus board records' existing `ROLES`-tuple membership (entry 1,
   unchanged), replacing its own `_BRANCH_RE`/`_pr_approved()` needle
   reconstruction.

## What did not work

None.

## Why

The issue's operator hard constraint is ZERO convention bugs across the 6
frozen parser consumers during phase 5's later migration. That constraint
is only enforceable if every later parser-by-parser sub-issue has a frozen
behavioral baseline to diff against and a settled order that respects
which consumer reads which other consumer's output. This issue (step 0)
builds exactly those two things — the equivalence harness and the
migration order — and nothing else, per its own "no convention changes"
scope.

## Upstream

Based on the approved proposal
`docs/issue-1792/proposals/equivalence-harness.md` and survey
`docs/issue-1792/reports/implementation/survey.md`, both committed at
`7f5924a819e98037083f3f2e7477097c9481fa05`, with the harness code
committed at `07857a98`.

## loop_state

landed

## Open findings

None.
