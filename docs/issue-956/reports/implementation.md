---
code_under_review:
  - on-the-record/hooks/product-capture-stopgate.sh
  - on-the-record/hooks/test_product_capture_stopgate.py
  - harness/fixture-target/scenario.py
type: feature
breaking: false
# canonical: python3 -m pytest on-the-record/hooks/test_product_capture_stopgate.py -v — result: PASS
verdict: pass
loop_state: landed
---

# Record — issue #956 phase-2: target-project requirement-capture build

canonical: gh pr view 957 — result: PASS (state MERGED, this session's own run)

Built exactly the write set frozen in docs/issue-956/proposals/implementation.md, PR #957 above.

## What was done

- on-the-record/hooks/product-capture-stopgate.sh: when the current branch does not match
  `issue-<n>/<role>`, the hook no longer exits 0. It now derives `issue_n = None` and falls back to
  a fixed, non-issue-scoped write/advisory path (repo-root product docs, no issue segment) instead
  of the issue-scoped one. All other logic (category regexes, transcript walk, git-diff
  already-recorded check, empty-state early return, CLAUDE_ROLE/ORCHESTRATE_OFF kill switches) is
  unchanged.
- on-the-record/hooks/test_product_capture_stopgate.py: replaced the now-stale
  `t_off_issue_branch_is_noop` (asserted silence off an issue branch — no longer true) with
  `t_off_issue_branch_falls_back_to_repo_root_doc_path` (asserts the advisory fires, references the
  fallback path and not the issue-scoped one, and bootstraps the fallback requirements doc) and
  `t_off_issue_branch_empty_state_is_silent` (asserts the empty-state guard still holds on a
  non-issue branch).
- harness/fixture-target/scenario.py (new): mirrors harness/fixture-requirement-digest/scenario.py's
  no-live-session pattern. Seeds a scratch git repo on branch `main` and invokes the hook against it
  via subprocess with a synthetic Stop-event transcript on stdin. Two scenarios: capture-fires (one
  flagged requirement sentence -> advisory + bootstrap) and empty-state (no flagged sentences -> no
  writes, no advisory).

## Why

northpole req#2/#6/#7 (issue #956 body): a capture path that only works against on-the-record's own
repo is a band-aid. Issue #955's record documents a prior, correctly narrower refusal under #566's
scope; #956 authorizes the wider extension explicitly. The proposal's chosen design (re-affirmed
here, unchanged in build): requiring target projects to adopt on-the-record's own `issue-<n>/<role>`
branch convention as a capture precondition would still be the band-aid the issue names, since
ordinary target-project branches never take that shape — so capture must default-fire off a fixed
fallback path when the branch doesn't match, while leaving the issue-scoped path (and #684's
concurrent-issue collision fix) untouched on `issue-<n>/<role>` branches.

canonical: docs/issue-956/proposals/implementation.md ## Rationale (read this session)

## Upstream / basis

docs/issue-956/proposals/implementation.md, PR #957, approved via the issue-956 thread's
`APPROVE issue-956/implementation` comment from a docs/specs/approvers.md account (single-account
mode).

canonical: gh issue view 956 --comments — result: PASS (comment body confirmed, this session's own run)

## Acceptance

- canonical: python3 -m pytest on-the-record/hooks/test_product_capture_stopgate.py -v — result: PASS
  (9 passed, 0 skipped; full pytest summary pasted below)

```
on-the-record/hooks/test_product_capture_stopgate.py::t_no_flagged_sentence_is_silent PASSED
on-the-record/hooks/test_product_capture_stopgate.py::t_flagged_requirement_with_no_doc_change_gets_additional_context PASSED
on-the-record/hooks/test_product_capture_stopgate.py::t_bootstrap_creates_missing_file_on_first_flag PASSED
on-the-record/hooks/test_product_capture_stopgate.py::t_flagged_requirement_with_matching_doc_diff_is_silent PASSED
on-the-record/hooks/test_product_capture_stopgate.py::t_claude_role_set_is_noop PASSED
on-the-record/hooks/test_product_capture_stopgate.py::t_orchestrate_off_is_noop PASSED
on-the-record/hooks/test_product_capture_stopgate.py::t_off_issue_branch_falls_back_to_repo_root_doc_path PASSED
on-the-record/hooks/test_product_capture_stopgate.py::t_off_issue_branch_empty_state_is_silent PASSED
on-the-record/hooks/test_product_capture_stopgate.py::t_missing_transcript_path_fails_closed_silently PASSED
9 passed in 0.50s
```

- canonical: python3 harness/fixture-target/scenario.py — result: PASS (both scenario rows, exit 0;
  output pasted below)

```
[PASS] capture-fires: advised + bootstrapped docs/product/requirements.md
[PASS] empty-state: no docs/product/* writes, no advisory
```

## What did not work

None.

## Doc placement

- This record file is the phase-2 record, per contract v3 s19.
- No env var, config key, new dependency, or migration was introduced by this change, so no
  handbook update applies.
- No new library-or-format choice or changed public signature/wire format beyond what phase-1's
  proposal already recorded as its Rationale — no new decisions/ entry under this issue's tree.

## Open findings

None open. Warrant-hunter dispatch: per the headless/single-shot subordination rule (contract v3
s22), this session does not dispatch a background hunter it cannot consume within the same turn —
no later turn exists in this invocation for an async hunt result to land in. No hunt record was
produced this phase.

## Out of scope (per proposal, unchanged)

gates/requirement_digest.py, requirement-digest-preflight.sh, docs/specs/requirements.md
auto-writing, and on-the-record's own issue-scoped capture output shape were not touched.
