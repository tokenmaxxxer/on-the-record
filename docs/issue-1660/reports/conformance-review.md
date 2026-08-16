---
kind: conformance-review
loop_state: findings-open
---

# Conformance review — issue #1660

Subject: issue-1660

## What was done

Verified requirement-1660 (northpole req#6: wire the requirement-fidelity
program into the co-injected orchestrate directive) against the landed
implementation commits on `issue-1660/implementation`
(`003e7b3f` feat, `f07adf75` docs), diffed against `origin/main`
(`7b2f774a`).

code_under_review:
- on-the-record/hooks/directive.sh
- on-the-record/hooks/test_directive_content.py
- gates/requirement_met.py
- gates/test_requirement_met.py

## Why

conformance-review role board condition (issue-521): an implementation
commit landed on `issue-1660/implementation` and no conformance-review
record exists yet for this commit sha.

## Upstream basis

003e7b3f6fd9875f5b6f79f328a7ae73b675cbf5

## Per-requirement verdicts

### check 1 — directive.sh carries the three obligations, each naming its gate module; unit/text test asserts their presence alongside #1024/#310

Verdict: **Present**.

canonical: `git show 003e7b3f -- on-the-record/hooks/directive.sh` — adds
"DESIGN-RESEARCH INTAKE (issue #1653)" naming `gates/design_research_consult.py`,
"LANDING REQUIREMENT-MET GRADE (issue #1651)" naming `gates/requirement_met.py`,
and "SCOPE ADHERENCE AT LANDING (issue #1658)" naming `gates/scope_adherence.py`,
alongside the pre-existing `VALIDITY CONSULT (issue #1024)` and
`ACCEPTANCE FORMAT` (#310) blocks.

`on-the-record/hooks/test_directive_content.py` (new file, same commit)
asserts presence of all five blocks plus an ordering check.

acceptance: `python3 on-the-record/hooks/test_directive_content.py` —
result:
```
ok  t_design_research_intake_obligation_present_and_names_gate_module
ok  t_existing_1024_validity_consult_block_present
ok  t_existing_310_acceptance_format_block_present
ok  t_landing_requirement_met_grade_obligation_present_and_names_gate_module
ok  t_new_obligations_appear_after_existing_1024_block_before_full_procedure
ok  t_scope_adherence_obligation_present_and_names_gate_module
6/6 passed
```

### check 2 — live: design-bearing issue without design-research trace blocks; builder-blind requirement_met grader gates a real landing PR; out-of-declared-scope PR flagged

Verdict: **Unverifiable**.

unverifiable: this is a live-orchestration claim (the orchestrator actually
following the directive text mid-session against a real design-bearing
issue and a real landing PR). This review session only has the diff and
the gate modules' own unit tests available; it did not observe (and
cannot, from a static diff review, fabricate) an actual orchestrator run
exercising the directive text end-to-end. The gate modules' deterministic
logic is unit-tested (see check 1 and check 3 evidence), but that is not
the same claim as "the orchestrator, live, actually blocked/spawned/
flagged" — no such live transcript exists in the reviewed materials.

### check 3 — requirement_met artifact-presence tighten: red test (prose-only path name fails) and green test (real hunk addition passes)

Verdict: **Present**.

canonical: `git show 003e7b3f -- gates/test_requirement_met.py` —
`t_red_artifact_named_only_in_diff_header_prose_fails` (diff --git/---/+++
header lines only, no matching `+` hunk line → `grade()` returns
`blocked: True`) and `t_green_artifact_in_added_hunk_line_passes` (artifact
string present in an actual `+`-prefixed hunk line → `blocked: False`).
Implementation: `gates/requirement_met.py` `_artifact_in_diff_hunk()`
only matches lines starting with `+` (excluding `+++` file headers),
replacing the prior `artifact in diff` substring-anywhere check.

acceptance: `python3 gates/test_requirement_met.py` — result:
```
ok  t_check_surfaces_per_criterion_advisory_record
ok  t_empty_state_no_acceptance_section_is_distinct_result
ok  t_empty_state_no_check_bullets_is_distinct_result
ok  t_green_artifact_in_added_hunk_line_passes
ok  t_multiple_criteria_one_blocking_one_not
ok  t_no_verdict_never_blocks_even_without_artifact
ok  t_red_artifact_named_only_in_diff_header_prose_fails
ok  t_semantic_verdict_is_advisory_only_recorded_not_blocking_by_itself
ok  t_unknown_verdict_never_blocks
ok  t_yes_with_artifact_absent_from_diff_fails
ok  t_yes_with_artifact_present_in_diff_passes
ok  t_yes_with_no_cited_artifact_at_all_blocks
12/12 passed
```

### empty state — mechanical issue (design-research-skip) and undeclared-scope PR proceed byte-identical to today; asserted

Verdict: **Surface**.

canonical: `git show 003e7b3f -- on-the-record/hooks/directive.sh` — the
directive text states the skip literal (`design-research-skip: mechanical`,
"no other skip reason is accepted") and the undeclared-scope carve-out
("an undeclared scope is ADVISORY only (consumer repos with no `scope:`
field proceed exactly as today)"). This wiring commit does not add new
empty-state tests of its own for these two gates — the underlying
empty-state behavior is unit-tested in the pre-existing gate modules
(`gates/test_design_research_consult.py`, `gates/test_scope_adherence.py`,
landed under #1653/#1658, unchanged by this commit).

derived:
```
$ python3 gates/test_design_research_consult.py
ok - t_arbitrary_skip_reason_rejected
ok - t_neither_flagged
ok - t_research_trace_passes
ok - t_skip_mechanical_passes
4/4 passed
$ python3 -m pytest gates/test_scope_adherence.py -q
............                                                             [100%]
12 passed in 1.28s
```
Marked Surface rather than Present because this commit's own diff carries
no test that exercises the empty-state path *through the newly-added
directive text specifically* — only the directive's prose commits to the
behavior, verified indirectly via the (unchanged) underlying gate
modules' own suites.

## Open findings

1. check 2 (live orchestrator behavior) is Unverifiable from a static
   diff review — no live-run transcript exists to cite. Resolution path:
   next real design-bearing issue drafted without a `design-research:`
   trace, and next real landing PR, should have the orchestrator's actual
   block/spawn/flag behavior captured (e.g. in that PR's own record) so a
   future review can cite an executed-live source instead of leaving this
   Unverifiable.
2. empty-state coverage (criterion 4) is Surface, not Present: no test in
   this commit exercises the empty-state path through the new directive
   wiring itself. Resolution path: addressed_to implementation — a
   follow-up could add a directive-text-level assertion (or an
   integration test) that the skip/undeclared-scope literals actually
   round-trip through the wired obligations, not just through the
   standalone gate modules.

Both findings are addressed_to the implementation role (issue-1660/
implementation) and/or a follow-up issue; this review does not fix
either.

## Next steps

- Capture a live-run transcript (design-bearing issue block, builder-blind
  grader spawn + merge gate, out-of-scope PR flag) the next time these
  paths actually fire, so open finding 1 can move from Unverifiable to a
  cited verdict.
- Optionally add a directive-wiring-level empty-state test (open finding
  2) as a follow-up in the implementation role's scope.
