---
proposal: docs/issue-2166/proposals/2026-08-24-conformance-review-issue-2166.md
---

# Hunt record — conformance-review-issue-2166

## after-proposal — stance 1: sanity-check REQ-8's rank claim, verdict-logic consistency, and staleness in the phase-1 conformance-review survey/proposal for issue #2166

Verdict: FINDING — the proposal's step 4 sets the overall `result: failed` field by treating REQ-8's `Incorrect` finding-verdict as if it were the EARL `result` value `failed`, which is the exact 1:1 substitution `conformance-review-finding-record` rule 3.3 says not to do, and no per-requirement `result` field is populated anywhere in the plan for the recomputation rule's worst-case to run over.
Kind: design-error
Seed: docs/issue-2166/reports/conformance-review/survey.md, docs/issue-2166/proposals/2026-08-24-conformance-review-issue-2166.md (phase-1 conformance-review session for issue #2166, transitioning to commit/push/PR)
cap_seconds: not stated in dispatch prompt
tier: not stated in dispatch prompt
diff_stat_lines: 2 new files (survey.md 311 lines, proposal 230 lines); no numeric diff-stat given by dispatcher
started_at: 2026-08-24T07:40:00Z
ended_at: 2026-08-24T08:25:00Z

Sub-check on REQ-8's rank claim (per the dispatch instruction to
independently re-derive rather than trust the survey's own paste),
re-run in a fresh worktree of `origin/issue-2166/implementation`:

```
$ git worktree add /tmp/wt-2166-impl origin/issue-2166/implementation
$ cd /tmp/wt-2166-impl && gh issue view 525 --json body -q .body > /tmp/issue525.txt
$ python3 -c "
from unittest import mock
import spawn
body = open('/tmp/issue525.txt').read()
with mock.patch.object(spawn, '_installed_plugin_skill_dirs', lambda: {}):
    scored = spawn._bm25_cross_family_scores(body, 'implementation', spawn._skill_repo_root())
for i, (score, name, d, source) in enumerate(scored):
    if name in ('market-analysis-mece-proposal', 'work-in-english'):
        print(f'{name} rank {i+1} of {len(scored)} score {score:.3f}')
"
market-analysis-mece-proposal rank 10 of 269 score 21.507
work-in-english rank 13 of 269 score 20.477
$ git show cd4c59a3 -- consult.py | grep -n 47위
+47위여도(재현: 이슈-525 과제
$ grep -n 47 tests/test_retrieval_eval.py
231:        is low/irrelevant (measured rank 47 of 269 for a real on-the-record
```
canonical: this session's own live run above (executed-unit), against
`origin/issue-2166/implementation` commit `64c5c571` — rank 13, matching
the survey's §3 replay and the implementer's own `derived:` block in
`git show origin/issue-2166/implementation:docs/issue-2166/reports/implementation.md`
exactly; the shipped `consult.py` comment and
`tests/test_retrieval_eval.py:231` docstring still cite "47" for the
same named input under this independent re-run. REQ-8's rank claim
(13 reproduces, 47 does not, same input) holds and is not the finding
below — the finding is in how the proposal's `result` computation uses
that already-correct REQ-8 verdict.

### Reproduce

```
$ grep -n "map 1:1\|not a swap\|vocabulary alignment" /home/jwjung/tokenmaxxxer/rulebooks/skill-repository/skills/conformance-review-finding-record/references/rules.md
72:   cardinality; the value sets do not map 1:1, this is vocabulary
73:   alignment, not a swap.

$ grep -n '"result"' -A3 roles/specs/conformance-review.spec.json
8:      "name": "result",
9-      "type": "enum",
10-      "enum": ["passed", "failed", "cantTell", "inapplicable", "untested"],
11-      "required": true

$ grep -n "drives this to" docs/issue-2166/proposals/2026-08-24-conformance-review-issue-2166.md
127:`failed`; the record will state plainly, next to that value, that the
```
canonical: this session's own live run above (executed-unit) — grep of
`references/rules.md` (the `conformance-review-finding-record` skill
this proposal's own "Skill verdicts" section marks `applied: invoked`),
`roles/specs/conformance-review.spec.json` (this repo's checked-in role
spec), and the phase-1 proposal file itself.

### Observed

The proposal's step 1 ("1. **The record**", `docs/issue-2166/proposals/2026-08-24-conformance-review-issue-2166.md`
lines 100-107, this session's read) lists each finding block's field set
as `requirement`/`spec_ref`/`verdict`/`evidence`/`rationale` (plus
`spec_vs_built` for REQ-8) — never `result`. Step 4 ("4. **Overall
`result`**", same file lines 124-132, this session's read) then states
REQ-8's `Incorrect` verdict "drives this to `failed`" for the record's
single required top-level `result` field. `references/rules.md` line
69-73 above (`conformance-review-finding-record` rule 3.3) states in
the same skill this proposal marks invoked: "the value sets do not map
1:1, this is vocabulary alignment, not a swap." No finding block in the
plan is ever assigned an EARL `result` value, so `roles/specs/conformance-review.spec.json`'s
`recomputation.rule` ("overall verdict = the worst-case result across
all cited test entries") has no per-entry `result` inputs anywhere in
this plan to take a worst-case across.

### Expected

Either the plan states an explicit, argued mapping from each of the
five `verdict` values to the five `result` values and populates a
`result` per finding so the worst-case rule has real inputs, or it
states plainly that the top-level `result` field is asserted directly
rather than recomputed (which would itself contradict the role spec's
"never a standalone summary field asserted independently of the cited
results" clause) — not silently perform the 1:1 swap the record's own
governing skill names and disclaims as unsound.
