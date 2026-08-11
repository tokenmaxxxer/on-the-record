---
proposal: docs/issue-741/proposals/2026-08-11-execution-provenance-and-phase1-closes-refusal.md
---

# Hunt record — execution-provenance-and-phase1-closes-refusal

## after-proposal — stance 0: assume the gate just proposed is bypassable — find the bypass

Verdict: FINDING — the proposal's "What will be done" text for the pr-preflight.sh phase-1 closes-check names only the bare `_CLOSES_REF` regex object (the one already used via `.search()` at pr-preflight.sh:236/241), not gates/ci.py's `_closes_ref_for_issue` helper — which exists specifically because `.search()` (first-match-only) was hunted and found to miss a real `Closes #N` reference to the PR's own issue when a decoy closing-keyword reference to a *different* issue appears earlier in the body. If implemented by reusing the file's existing `.search()` idiom (which is exactly what "기존 _CLOSES_REF … 새 정규식 아님" points at), the new phase-1 check inherits that already-documented bypass verbatim.
Kind: design-error
Seed: docs/issue-741/proposals/2026-08-11-execution-provenance-and-phase1-closes-refusal.md, "What will be done" > pr-preflight.sh section (lines ~142-153)
cap_seconds: 60
tier: default
diff_stat_lines: N/A (docs-only proposal, no code diff yet — single new proposal file)
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:05:00Z

### Reproduce

```
python3 -c "
import re
_CLOSES_REF = re.compile(r'(?i)\b(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)')
body = 'Fixes #999, unrelated context here. Closes #741'
issue = 741

# idiom already present in on-the-record/hooks/pr-preflight.sh at lines 236/241
# (the only existing usage of _CLOSES_REF the proposal points to as 'not a new regex')
mm = _CLOSES_REF.search(body)
print('search()-based (existing file idiom):', mm.group(0) if mm else None,
      '-> matches this issue:', bool(mm and int(mm.group(2)) == issue))
"
```

Cross-check against gates/ci.py's canonical `_closes_ref_for_issue` (gates/ci.py:164-176),
whose docstring states this exact scenario is why it uses `.finditer()` instead of
`.search()`:

```
grep -n "_closes_ref_for_issue" -A 12 gates/ci.py | head -20
```

### Observed

`_CLOSES_REF.search(body)` returns the match for `Fixes #999` (the decoy, a
different issue) and stops there — `int(mm.group(2)) == issue` evaluates to
`False` for `issue=741`, even though the same body plainly contains
`Closes #741` further along. Applied to the proposed pr-preflight.sh check
("phase1 이고 not bad 일 때만... 있으면 deny()"), this means a phase-1 PR body
of the PR #763 shape but with one extra decoy reference prepended —
e.g. `"Fixes #999, some other issue. Closes #741"` — would NOT be denied:
the new check finds no match for its own issue and lets the PR through,
exactly the auto-close outcome the proposal exists to block.

gates/ci.py's own docstring for `_closes_ref_for_issue` (gates/ci.py:164-173)
confirms this is not hypothetical — it documents that `.search()` was hunted
and found to miss this case, and that `.finditer()` was adopted specifically
to fix it: "`.search()`(첫 매치 하나)가 아니라 `.finditer()`(전체 매치)를 쓴다:
본문이 다른 이슈를 먼저 언급하면(...) `.search()`는 #999 매치에서 멈춰 진짜
#245 참조를 놓친다 — hunt로 실측 확인된 회피 경로".

### Expected

The proposal's "What will be done" section for pr-preflight.sh should
explicitly specify iterating all `_CLOSES_REF` matches (finditer, matching
`gates/ci.py::_closes_ref_for_issue`'s semantics) and checking each one's
issue number, not a single `.search()` call — otherwise an implementer who
follows the proposal's literal instruction ("기존 _CLOSES_REF로... 찾는다",
pointing at the file's only existing usage pattern, `.search()`) reproduces
a bypass gates/ci.py already had to fix once. The proposal's Rationale
section states `_phase1_mismatch`/`_closes_ref_for_issue` "already correct
logic" is what's being ported, but the "What will be done" section's
wording doesn't carry that helper's finditer behavior forward — only the
bare regex.
