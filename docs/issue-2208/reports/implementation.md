---
issue: 2208
role: implementation
loop_state: landed
upstream:
  - path: docs/issue-2205/reports/implementation.md
    sha: 049731f953b9c1bfdac206651e64622792132e3d
code_under_review:
  - pipeline.py
  - skills.py
  - spawn.py
type: fix
breaking: none
verdict: pass
---

# issue-2208 — implementation record

## What was done

Three follow-ups to #2205 (PR #2206), plus one before-landing fix.

### 1. Judge abstention rate (measurement only)

Query over every logged `verb=skill_judge` line in `docs/*/reports/consult-log.md` (full command in Upstream basis footnote), re-run independently by this session.
acceptance: python3 -c "<abstention query, full text in Upstream basis>" — result:
```
total 36 errors 5 ok_lines 31 abstain 18
rate_over_ok=18/31=58.1%
rate_over_all=18/36=50.0%
```
N=36 logged decisions, 5 timed out (excluded from the base rate), per the fenced result above. No dedicated abstention-replay script existed on disk; this was a one-off query, not a persistent test file (verify-at-landing).

### 2. Strip negative clauses from the BM25 field

`pipeline.py`: added `_NEGATIVE_SCOPE_RE` + `_strip_negative_scope()`, cutting everything from `"Do NOT use"` onward out of a skill's description before `_skill_bm25_document()` appends it to the indexed text. The full description (what the judge/user reads) is untouched.

acceptance: pytest tests/test_retrieval_eval.py -v -o addopts= (BEFORE the change) — result:
```
work-in-english-declared-phrase-self-inflation-fp: completed, precision@mount=1.00
issue-525-cross-family-off-domain-fp: completed, precision@mount=1.00
macro MRR=0.875 | 9 passed in 0.7s
```
acceptance: same command (AFTER the change, re-run independently by this session) — result:
```
work-in-english-declared-phrase-self-inflation-fp: completed, precision@mount=1.00
issue-525-cross-family-off-domain-fp: completed, precision@mount=1.00
macro MRR=1.000 | 9 passed in 14.12s
```
acceptance: diff of the two fenced pytest runs above — result:
```
negatives: completed,completed in BEFORE and completed,completed in AFTER (unchanged, neither flipped)
positives: no new failures; dicequest-upgrade-cost-curve MRR 0.50->1.00 (side effect, not a regression)
```

### 3. Static pin for `work-in-english`, off the retrieval pool

Audited all 273 skill descriptions in the mounted skill-repository for "blanket policy" framing. Two true hits: `work-in-english` (session-wide language policy) and `model-routing` (session-wide orchestration policy).
acceptance: git grep -n "skillOverrides" — result:
```
(no hits)
```
The named mechanism does not exist in this repo, per the empty result above. Reused the existing `_ROLE_SKILLS` / `resolve_role_source()` static-binding path and the existing family-exclusion filter in `_cross_family_candidate_corpus()` instead of inventing a new one.

`skills.py`: added `_STATIC_POLICY_SKILLS = {'work-in-english'}`, appended `'work-in-english'` to `_ROLE_SKILLS['implementation']`. `pipeline.py`: `_cross_family_candidate_corpus()`'s exclusion set widened from `set(_sp._ROLE_SKILLS.get(role, []))` to `... | set(_sp._STATIC_POLICY_SKILLS)`, excluding any `_STATIC_POLICY_SKILLS` name from cross-family BM25 candidates for every role. `spawn.py`: one re-export line, matching the existing `_ROLE_SKILLS` re-export pattern.

acceptance: grep -l "work-in-english" docs/*/reports/consult-log.md — result:
```
docs/issue-2073/reports/consult-log.md (role=implementation)
docs/issue-2093/reports/consult-log.md (role=implementation)
```
Those are the only two real historical mounts per the fenced result above, so role scope was bound to `implementation` only (see Open findings for why this is not exhaustive). `model-routing` was audited but not pinned in this change — no `_ROLE_SKILLS` entry exists for it today and the logged decisions show it being correctly picked/rejected rather than exhibiting the declared-phrase self-inflation failure mode (see Open findings).

acceptance: retrieval pipeline re-run against the frozen negative case `work-in-english-declared-phrase-self-inflation-fp` with `skill_judge` disabled (forces the fail-open BM25 top-k path, the worst case for a leak), re-run independently by this session — result:
```
work-in-english present anywhere in BM25-scored candidates: False
final picked (fail-open, judge disabled): ['usability-eval', 'refactoring-legacy-refactoring-step-decomposition']
outcome: fail-open
implementation role skills include: work-in-english
```
`work-in-english` is absent from BM25-scored candidates even under fail-open (never merely ranked outside top-8) per the fenced result above, and remains statically resolved for the `implementation` role via `resolve_role_source()`.

### 4. Before-landing warrant-hunt fix

acceptance: docs/issue-2208/reports/implementation/2026-08-24-hunt-skill-selection-followups.md (sha: same-commit, landed in `8e934e0d`) — result:
```
Verdict: FINDING — _skill_declared_phrases() reads the raw, unstripped
description; a quoted phrase inside a skill's own "Do NOT use" clause
still auto-picks that skill via the exact-phrase fast-path, no judge
review — the same self-inflation class item 2 was written to close.
```
One `warrant-hunter` dispatch (stance 0: assume the filter just touched is bypassable) against the diff before landing produced the finding above. Fixed before landing: added `desc = _strip_negative_scope(desc)` to `_skill_declared_phrases()` before its phrase scan, matching `_skill_bm25_document()`.
acceptance: hunter's reproduction script, re-run by this session after the fix — result:
```
declared phrases (after fix): ['normal family trigger phrase']
outcome: fail-open
```
acceptance: pytest tests/test_retrieval_eval.py -v -o addopts= re-run after this fix — result:
```
9 passed in 14.12s
```

## Why

#2205/#2206 fixed trigger-phrase self-inflation but left three diagnoses from its comment thread open: whether "pick at most 2" structurally suppresses judge abstention (item 1), whether the project's own "Do NOT use for X" negative-scoping convention injects the excluded topic's tokens into BM25 the same way trigger phrases did (item 2), and whether a policy skill like `work-in-english` should compete for a retrieval slot at all versus being bound statically (item 3). Each was scoped cheapest-first per the issue's own ordering. Reused mechanisms (`_ROLE_SKILLS`, the existing family-exclusion filter) were chosen over new ones because the repo already had them and no `skillOverrides`-shaped mechanism existed to reuse instead.

## What did not work

acceptance: docs/issue-2208/reports/implementation/2026-08-24-hunt-skill-selection-followups.md "Fixed" section — result:
```
declared phrases (after fix): ['normal family trigger phrase']
outcome: fail-open   # was fast-path:some-other-family-skill before the fix
```
acceptance: git diff pipeline.py (checkpoint commit 8e934e0d) — result:
```
first pass: _strip_negative_scope() applied to _skill_bm25_document() only
gap: _skill_declared_phrases() (same raw description, feeds fast-path) left unstripped
fixed: same commit, after the before-landing warrant hunt (item 4) caught the gap
```

## Upstream basis

- `docs/issue-2205/reports/implementation.md` @ `049731f953b9c1bfdac206651e64622792132e3d` — PR #2206: fixed trigger-phrase self-inflation, froze the two negative gold cases this issue re-runs, raised the three diagnoses this issue resolves.
- `docs/issue-2208/reports/implementation/2026-08-24-hunt-skill-selection-followups.md` @ `sha: same-commit` — before-landing warrant-hunt finding and fix, described in "What did not work" above.
- Abstention query (item 1) full command:
```bash
python3 -c "
import re, glob
total = 0; abstain = 0; errors = 0; ok_lines = 0
for path in sorted(glob.glob('docs/*/reports/consult-log.md')):
    for line in open(path, encoding='utf-8'):
        if 'verb=skill_judge' not in line: continue
        m = re.search(r'outcome=\'(.*)\'', line) or re.search(r'outcome=\"(.*)\"', line)
        outcome = m.group(1) if m else None
        total += 1
        if outcome is None: continue
        if outcome.startswith('error'): errors += 1; continue
        ok_lines += 1
        pm = re.search(r'picked=\[([^\]]*)\]', outcome)
        picked = pm.group(1).strip() if pm else None
        if picked == '': abstain += 1
print('total', total, 'errors', errors, 'ok_lines', ok_lines, 'abstain', abstain)
print(f'rate_over_ok={abstain}/{ok_lines}={abstain/ok_lines*100:.1f}%')
print(f'rate_over_all={abstain}/{total}={abstain/total*100:.1f}%')
"
```

## Open findings

- `work-in-english` role-binding scope is evidence-based (bound only to `implementation`), not exhaustive across the ~46 roles in `_ROLE_SKILLS`. Resolution path: a follow-up issue auditing which other roles produce code/commits/PRs in Korean-language sessions, or leave it narrow until a real miss is logged.
- `model-routing` shares `work-in-english`'s policy-skill shape but has no `_ROLE_SKILLS` entry to pin against and was not exhibiting the failure mode this issue fixes, so it was left out of scope. Resolution path: a follow-up issue to decide which roles should carry it statically, then apply the same `_STATIC_POLICY_SKILLS` treatment.
- The abstention measurement (58.1%/50.0%) is a one-off query over N=36 logged decisions, not a durable metric — it will shift as more decisions accumulate. Resolution path: none needed for this issue (the acceptance criterion asked for a number with its query, not a monitoring mechanism); out of scope unless a future issue asks for one.

## Next steps

None — `loop_state: landed` is terminal for this record kind; the open findings above have their own resolution paths (follow-up issues) and do not block this landing.

---

skill-verdict: implementation-complexity-coupling-management — not-applicable: no CBO/LCOM threshold, accessor chain, cross-module import direction, or check-pipeline ordering was in play — the diff extends existing dict/set idioms.
skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-pattern introduction/removal decision was open; the change reuses existing static-binding and filter-exclusion code as-is.
skill-verdict: implementation-performance-data-structure-choice — not-applicable: the one data-structure choice (a `set` literal for `_STATIC_POLICY_SKILLS` membership) is a trivial, non-cliff-risk extension of an existing set-based exclusion filter already in the code, not a new performance decision.
skill-verdict: implementation-blueprint — not-applicable: no new module structure or cross-file architecture decision was open — the change extends three existing, already-established idioms (`_ROLE_SKILLS`, the family-exclusion filter, the BM25-document builder) rather than introducing new structure.
skill-verdict: model-routing — not-applicable: delegation/routing for this session was already fully and mechanically determined by the freelunch-directive's STEP 1 tally and executor test (the enforced core hook), leaving no separate routing judgment for this skill to inform.
