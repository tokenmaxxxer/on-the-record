# Conformance review of PR #281 (issue-280 full closing-keyword set)
kind: record
loop_state: verdict-issued
upstream: docs/issue-280/proposals/2026-08-14-conformance-review.md
code_under_review:
- gates/pr_reference.py
- gates/ci.py
- gates/test_closes_gate_ci.py
- test_gates.py

## What was done

canonical: `gh pr diff 281 --patch`, run this session (saved to
/tmp/pr281.diff) — read the full merged diff for gates/pr_reference.py,
gates/test_closes_gate_ci.py, and test_gates.py.

derived: live regex check, run this session:
```
python3 -c "
import re
r = re.compile(r'(?i)\b(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)')
kws = ['close','closes','closed','fix','fixes','fixed','resolve','resolves','resolved']
ok = True
for kw in kws:
    for v in (kw, kw.capitalize(), kw.upper()):
        if not r.search(f'{v} #245'):
            ok = False
print('all_9x3_match=', ok,
      'false_pos_unclosed=', bool(r.search('unclosed #245 for now')),
      'false_pos_prefixes=', bool(r.search('prefixes #245 with x')))
"
```
Result: `all_9x3_match= True false_pos_unclosed= False false_pos_prefixes= False`

canonical: `grep -n "closes_only\|_phase1_mismatch" gates/ci.py`, run this
session — `_phase1_mismatch` (gates/ci.py:320) is invoked from `check()`
(gates/ci.py:388-455) whenever `closes_only=True`, itself set from the
`--closes-only` CLI flag (gates/ci.py:504,526,539); it returns a blocking
message `"phase-1 제안 PR ... 에 closing 키워드(...)가 ..."` whenever
`_CLOSES_REF` matches the body targeting the current issue, independent of
any approval marker.

canonical: `gh pr diff 281 --patch` (same fetch as above), read this
session — gates/test_closes_gate_ci.py gained
`t_phase1_mismatch_detects_full_closing_keyword_set` (sweeps all 9 keywords
x 3 case variants through `ci._phase1_mismatch`) and
`t_phase1_mismatch_ignores_near_miss_words` (word-boundary regression);
test_gates.py gained `t_pr_reference_phase2_full_closing_keyword_set` (same
9x3 sweep through `pr_reference.check_body`) and
`t_pr_reference_phase2_fenced_closing_keyword_matches` (in-code-fence case).

## Per-requirement verdicts

### Req 1 — full 9-keyword case-insensitive detection in `--closes-only`

verdict: Present
spec_ref: issue #280 acceptance bullet 1 ("Every GitHub closing keyword
form is detected in `--closes-only`")
evidence: the live regex check above (`all_9x3_match= True`) run against
the merged `_CLOSES_REF` = `(?i)\b(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)`
from gates/pr_reference.py (PR #281 diff), the single regex both
`_phase1_mismatch` and `check_body` consult (gates/ci.py:320-341
grep above).

### Req 2 — unapproved phase-1 PR body with any keyword form is BLOCKED

verdict: Present
spec_ref: issue #280 acceptance bullet 2 ("A phase-1 PR body containing
any of them without approval is BLOCKED")
evidence: `_phase1_mismatch` (gates/ci.py:320), reached from `check()`
under `closes_only=True` (gates/ci.py:402-455) with no approval-token
check in that branch, grepped this session — a match against the widened
`_CLOSES_REF` unconditionally produces a blocking message; no approval
state gates this return.

### Req 3 — regression tests cover all 9 spellings x case x code-fence

verdict: Present
spec_ref: issue #280 acceptance bullet 3 ("Regression tests cover all 9
keyword spellings, case variants, and the in-code-fence case")
evidence: `gh pr diff 281 --patch` (canonical citation above) —
`t_phase1_mismatch_detects_full_closing_keyword_set` and
`t_pr_reference_phase2_full_closing_keyword_set` each loop the 9 keywords
x (lower/capitalize/upper) = 27 cases;
`t_pr_reference_phase2_fenced_closing_keyword_matches` covers the
in-code-fence case; `t_phase1_mismatch_ignores_near_miss_words` guards the
word-boundary edge the widened alternation could have broken.

## What did not work

None.
