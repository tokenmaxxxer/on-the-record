---
status: proposed
files:
  - docs/issue-1712/reports/conformance-review.md
---

# Proposal: conformance review of issue #1712 (consult-ordering, Korean neutrality, banner)

Subject: issue-1712

## Scope
This proposal covers writing exactly one file,
`docs/issue-1712/reports/conformance-review.md`, once phase-2 approval
is granted. No code under `on-the-record/hooks/` or `gates/` is edited —
conformance-review only asserts a per-requirement verdict against what
implementation already landed at commit
`04a77592963c94770d04f61e4ebe4caee6129bfa` (merged to `main` via PR
#1715).

## Plan
Verify each of issue #1712's three Acceptance bullets against
`on-the-record/hooks/directive.sh` and
`gates/test_scope_option_directive.py`, following the same
verdict-per-check structure the sibling issue-1707 conformance-review
record used
(`docs/issue-1707/reports/conformance-review.md`):

1. **Consult-ordering check** — confirm the SCOPE-OPTION PROPOSAL
   section states the #1024 validity consult runs on the vague ask
   first, before any option exists, that the option block derives from
   that consult's output (per-option `consult-trace:` citing the same
   run), and that the post-confirmation #1024 consult may reference the
   same trace when the ask is unchanged. Cross-check against
   `t_states_consult_runs_on_vague_ask_before_options`.
2. **Korean neutrality + banner check** — confirm the neutrality rule
   bars `권장`/`추천` as substrings inside the option block, and the
   first-contact banner mentions the design-bearing/scope-ambiguous
   option path. Cross-check against
   `t_states_neutrality_rule_forbids_korean_synonyms` and
   `t_states_banner_mentions_option_path`.
3. **Empty-state check** — confirm the REQUIREMENT ELICITATION block and
   the VALIDITY CONSULT (#1024) section body are otherwise unchanged, via
   the pre-existing tests (`t_states_trigger_subclass`,
   `t_states_non_overlap_with_1006_req4`,
   `t_states_option_block_count_and_order`, `t_states_option_fields`,
   `t_states_neutrality_rule_forbids_recommended_token`) still passing.

Each verdict will cite `file:line` evidence plus a `derived:` run of
`python3 gates/test_scope_option_directive.py`.

## Expected verdicts (preview, not binding until phase 2)
Based on the phase-1 survey, all three checks are expected to verdict
Present: the shipped test suite (9/9 passing, confirmed this session)
already asserts every substring/ordering condition the three Acceptance
bullets name, and the directive text quoted in
`docs/issue-1712/reports/implementation.md` matches those assertions.

## Accumulation
This is a single-commit, single-file conformance-review record with no
code change and no dependency chain — no accumulation-cost concerns
apply.
