---
code_under_review:
  - gates/verdict_gate.py
  - tests/test_verdict_gate.py
type: feature
breaking: false
verdict: pending
loop_state: landed
---

# Implementation record — issue #1669 phase 2

## What was done

canonical: gates/verdict_gate.py, tests/test_verdict_gate.py (commit c3dccd18)

Built `gates/verdict_gate.py`: a pure `classify(reviewer_verdict, merge_gate_result, tests_pass)` policy function per the approved phase-1 proposal (docs/issue-1669/proposals/verdict-asymmetry-merge-policy.md, PR #1671). `_parse_verdict()` extracts a fail-closed `"MERGE" | "CHANGES" | None` from free text, hardened against injection per the binding phase-2 review condition (gh issue view 1669 --comments, latest APPROVE comment): text containing both "MERGE" and "CHANGES", "do not MERGE", or reviewer-quoted verdict markup all resolve to `None` → `HOLD`, never `ALLOW_MERGE`. `classify()` reuses `merge_gate.evaluate()`'s `{"allowed": bool, "reasons": [...]}` dict shape as-is — no gate logic re-derived. `tests/test_verdict_gate.py` covers the four acceptance-listed branches, the malformed/absent-verdict fixture, and injection-robustness red-team fixtures.

## Why

canonical: gh issue view 1669 --comments (latest APPROVE comment, binding phase-2 condition text)

Issue #1669 (northpole req#6): an LLM MERGE verdict alone must never auto-merge; only a reviewer CHANGES verdict is safe to auto-act on (respawn). MERGE requires the deterministic gate (stale-revert guard, check-runner, verification records — gates/merge_gate.py) to also allow, plus tests passing. Verdict parsing must be fail-closed since PR/verdict body text is attacker-influenceable.

## Upstream

canonical: docs/issue-1669/proposals/verdict-asymmetry-merge-policy.md; gates/merge_gate.py:158-175

- Basis: docs/issue-1669/proposals/verdict-asymmetry-merge-policy.md (merged PR #1671)
- Reuses: gates/merge_gate.py `evaluate()` return shape (gates/merge_gate.py:158-175)

## Test-tier directive

canonical: find . -maxdepth 2 -name test-tiers.json (empty result, run this session)

`.on-the-record/test-tiers.json` absent in this repo — no tiered test config applies. New test file run directly, no network.

## Confirmation run

```
$ python3 -m pytest tests/test_verdict_gate.py -v
12 passed in 0.86s
```

canonical: acceptance: python3 -m pytest tests/test_verdict_gate.py -v — result: PASS

## What did not work

None.

## Open findings

canonical: acceptance: python3 -m pytest tests/test_verdict_gate.py -v — result: PASS

None open. Binding phase-2 review condition (injection-robust `_parse_verdict`) addressed and confirmed via dedicated red-team fixtures (test_both_keywords_present_holds_not_allow_merge, test_do_not_merge_holds_not_allow_merge, test_reviewer_quoted_verdict_holds_not_allow_merge, test_injected_merge_via_pr_body_quote_holds).

Resolution path: n/a — no open findings.

## Next steps

canonical: acceptance: python3 -m pytest tests/test_verdict_gate.py -v — result: PASS

Module and tests are complete against the frozen write set. Remaining steps this same turn: commit this record, push, open PR.

## Out of scope

Wiring `classify()`'s result into the orchestrate directive or `spawn.py` — issue #1669 explicitly sequences this as a follow-up (unchanged from proposal).
