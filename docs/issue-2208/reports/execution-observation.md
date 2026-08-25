---
issue: 2208
role: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2208/reports/execution-observation/survey.md
    sha: same-commit
  - path: docs/issue-2208/reports/implementation.md
    sha: 326506f20454c4f7ea7f662aa10720d1fa823554
subject: PR #2218 (issue-2208/implementation @ 326506f20454c4f7ea7f662aa10720d1fa823554)
test: issue #2208's three acceptance checks (abstention-rate query, tests/test_retrieval_eval.py before/after negative-clause stripping, work-in-english fail-open reproduction), each independently re-run in read-only worktrees
result: passed
assertedBy: execution-observation session, issue-2208/execution-observation, 2026-08-25
---

# issue-2208 — execution-observation record

## What was done

Independently re-verified PR #2218 (`issue-2208/implementation`, open
and not yet landed to `main` at verification time) against issue
#2208's own three acceptance checks, in read-only git worktrees outside
this repo's own working tree (`/tmp/otr-2208-verify` @
`origin/issue-2208/implementation`, `/tmp/otr-2208-main` @
`origin/main`@`443f6136`), rather than restating the implementation
role's own self-reported numbers.

canonical: acceptance: `python3 -c "<abstention query, full text in
Upstream basis>"` (this session, independent run inside
`/tmp/otr-2208-verify`) — result:
```
total 36 errors 5 ok_lines 31 abstain 18
rate_over_ok=18/31=58.1%
rate_over_all=18/36=50.0%
```
canonical: python3 -c "<same abstention query>" (same run, this
session) — the numbers above are an exact numeric match against the
implementation record's own pasted result; check 1's "number with the
query that produced it" requirement holds.

canonical: acceptance: `python3 -m pytest tests/test_retrieval_eval.py -v -o addopts=`
(this session, BEFORE in `/tmp/otr-2208-main`, AFTER in
`/tmp/otr-2208-verify`) — result:
```
BEFORE (origin/main@443f6136):              9 passed in 1.00s
AFTER  (origin/issue-2208/implementation):  9 passed in 34.39s
```
canonical: python3 -m pytest tests/test_retrieval_eval.py -v -o addopts=
(same run, this session) — both worktrees ran the full 9-item suite
with zero failures; check 2's suite-passing requirement holds.

canonical: acceptance: `python3 -m pytest tests/test_retrieval_eval.py -v -s -o addopts= -k test_bm25_recall`
(this session, both worktrees) — result:
```
BEFORE: issue-525-cross-family-off-domain-fp 0.00/1.00/1.00; work-in-english-declared-phrase-self-inflation-fp 0.00/1.00/1.00; macro MRR=0.875
AFTER:  issue-525-cross-family-off-domain-fp 0.00/1.00/1.00; work-in-english-declared-phrase-self-inflation-fp 0.00/1.00/1.00; macro MRR=1.000
```
canonical: python3 -m pytest tests/test_retrieval_eval.py -k
test_bm25_recall (same run, this session) — both frozen negative gold
cases show identical per-row fields (precision-of-nothing/recall/
precision@mount) in the BEFORE and AFTER blocks above, so neither one's
outcome changed by the negative-clause stripping; macro MRR rose
0.875->1.000 across the positives set (`dicequest-upgrade-cost-curve`
0.50->1.00), a positive-case gain, not a loss. Check 2's negative-case
stability requirement holds, and the positives gold set does not
regress (the regression-guard acceptance line).

canonical: acceptance: `grep -n "_STATIC_POLICY_SKILLS\|_ROLE_SKILLS" skills.py spawn.py`
plus a `Read` of `skills.py` lines 286-351 (this session, inside
`/tmp/otr-2208-verify`) — result:
```
skills.py:298: 'implementation': [..., 'work-in-english']
skills.py:351: _STATIC_POLICY_SKILLS = {'work-in-english'}
spawn.py:325-326: _ROLE_SKILLS / _STATIC_POLICY_SKILLS re-exports present
```
canonical: grep -n "_STATIC_POLICY_SKILLS" skills.py spawn.py (same
run, this session) — the code-level grep/Read above corroborates the
implementation record's own claimed edits to `skills.py` and
`spawn.py`.

canonical: acceptance: an independent forced fail-open reproduction —
`spawn._skill_judge_consult` mocked to raise, then
`_bm25_cross_family_scores` / `_cross_family_skill_matches_with_consult`
called for role=`implementation` against the frozen negative case's own
task text (this session, inside `/tmp/otr-2208-verify`) — result:
```
work-in-english in BM25-scored candidates: False
outcome: fail-open
picked: ['usability-eval', 'refactoring-legacy-refactoring-step-decomposition']
implementation role _ROLE_SKILLS includes work-in-english: True
```
canonical: the same fail-open reproduction script (same run, this
session) — the picked-list and outcome above are a word-for-word match
against the implementation record's own pasted result.

canonical: acceptance: the same `_bm25_cross_family_scores` call
against `origin/main`@`443f6136` (this session, inside
`/tmp/otr-2208-main`) — result:
```
work-in-english in BM25-scored candidates: True
top-8 rank: 4th/8
```
canonical: _bm25_cross_family_scores against origin/main@443f6136 (same
run, this session) — `work-in-english` ranked 4th of 8 candidates on
`main` before this change and is absent entirely from BM25-scored
candidates after it, even under a forced fail-open (the worst case for
a leak), while remaining statically resolved for the `implementation`
role via `_ROLE_SKILLS`. Check 3's requirement holds.

canonical: python3 -m pytest tests/test_retrieval_eval.py, the abstention query, and the fail-open reproduction (all six result blocks above, this session's own independent re-runs, per roles/specs/execution-observation.spec.json's worst-case-recomputation rule) — every one of the three acceptance checks succeeded under independent re-verification, so the frontmatter `result:` field reflects the worst case across all of them: passed.

## Why

The role-handoff contract treats an execution-observation record as an
independent check on a delivery role's own self-reported claims, not a
restatement of them (`roles/specs/execution-observation.spec.json`'s
gate_b_contrast: a record asserting nothing beyond the delivering
role's own numbers is schema-conformant but hollow). PR #2218 was still
open, not yet landed to `main`, at verification time, so this record
documents what was independently re-executed against a named commit
sha (`326506f20454c4f7ea7f662aa10720d1fa823554`), not an assumption
that the branch tip would stay fixed.

## Upstream basis

- `docs/issue-2208/reports/execution-observation/survey.md` @
  `same-commit` — this role's own phase-1 current-state survey; source
  of the independently re-run commands and result blocks cited above.
- `git show origin/issue-2208/implementation:docs/issue-2208/reports/implementation.md`
  @ `326506f20454c4f7ea7f662aa10720d1fa823554` (`origin/issue-2208/implementation`,
  PR #2218) — the delivery record this session re-verified against; not
  present on this role's own branch, read via the read-only worktree
  cited in this record's first section instead.
- Abstention query (item 1) full command: reproduced verbatim in the
  delivery record's own "Upstream basis" section (path above); not
  re-quoted here to avoid divergence between two copies.

## Open findings

Carried forward unresolved from the implementation record (not
re-litigated by this role — out of scope per this role's own phase-1
proposal):

- `work-in-english`'s static role-binding is evidence-based (bound only
  to `implementation`), not an exhaustive audit across all roles in
  `_ROLE_SKILLS`. Resolution path: a follow-up issue auditing which
  other roles produce Korean-language output, or leave it narrow until
  a real miss is logged.
- `model-routing` shares `work-in-english`'s policy-skill shape but has
  no `_ROLE_SKILLS` entry to pin against and was left out of scope of
  PR #2218. Resolution path: a follow-up issue to decide which roles
  should carry it statically.
- The abstention measurement (58.1%/50.0%, N=36) is a one-off query,
  not a durable metric — it will shift as more decisions accumulate.
  Resolution path: none needed for issue #2208 itself (the acceptance
  check asked for a number with its query, not a monitoring mechanism);
  out of scope unless a future issue asks for one.

## Next steps

None — `loop_state: handed-off` is terminal for this record kind. All
three open findings above carry their own resolution paths (follow-up
issues or explicit no-action-needed) and do not block this handoff.
