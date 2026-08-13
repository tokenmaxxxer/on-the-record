---
proposal: docs/issue-1142/proposals/2026-08-13-drift-check-enforced-exclusion.md
---

# Hunt record — drift-check-enforced-exclusion

## after-proposal — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — the digest `status:` field the proposal keys `[enforced]`/`[open]` matching on is free-text with no validator anywhere in the repo (the docstring's claimed enforcer, `gates.requirement_registry`, does not exist as a file), so any casing/spelling variant (`Enforced`, `enforced `, `proposed`, etc.) silently fails an exact-match check and the fix's citation-skip logic would misclassify it.
Kind: design-error
Seed: docs/issue-1142/proposals/2026-08-13-drift-check-enforced-exclusion.md — proposed change to spawn.py::requirement_drift() around line 2472/2478 (`_REQ_FIELD`-driven `[status]` capture in requirement-digest.md lines)
cap_seconds: 120
tier: default
diff_stat_lines: n/a (proposal not yet built; inspected gates/requirement_digest.py + docs/specs/requirement-digest.md)
started_at: 2026-08-13T00:00:00Z
ended_at: 2026-08-13T00:02:00Z

### Reproduce
```
mkdir -p /tmp/reqtest/docs/specs
cat > /tmp/reqtest/docs/specs/requirements.md <<'REQ'
## R900
quote: test requirement with unusual status casing
source_issue: 9999
check: some/path.py::test_x
status: Enforced
REQ
python3 -c "
import sys; sys.path.insert(0,'gates')
import requirement_digest as rd
from pathlib import Path
text = Path('/tmp/reqtest/docs/specs/requirements.md').read_text()
entries = rd.parse(text)
print(rd.render(entries))
"
```

### Observed
`gates/requirement_digest.py::parse()` accepts `status: Enforced` (or any other string) unvalidated, and `render()` emits it verbatim into the digest: `- R900: test requirement with unusual status casing [Enforced] (source: #9999)`. Nothing in the repo — no schema check, no enum, no `gates.requirement_registry` module (referenced only in a docstring comment, the file does not exist) — constrains `status:` to the two literals `enforced`/`open` the proposal's spawn.py logic is meant to branch on.

### Expected
The proposal assumes the digest status is always exactly `enforced` or `open` so it can gate citation-drift-flagging on that literal. Since the field is unvalidated free text, an exact-match (or even case-sensitive) comparison in the new spawn.py code would silently misroute any non-canonical status value instead of erroring or falling back safely — a state the proposal depends on but nothing maintains.

## before-landing — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: NO FINDING
Seed: spawn.py::requirement_drift() + gates/test_requirement_drift.py, ~20 net lines (issue-1142 proposal)
cap_seconds: 60
tier: default
diff_stat_lines: ~20
started_at: 2026-08-13T00:00:00Z
ended_at: 2026-08-13T00:01:00Z

Checked whether the status vocabulary the new `== "open"` filter depends on
is actually closed to `open`/`enforced`, or whether a third value (e.g.
`stale`, or free text) could reach `requirement_drift()` unhandled.
`docs/specs/requirements.md` field docs (line 14) fix the vocabulary to
exactly `open | enforced | stale`. `gates/requirement_digest.py:78`
(`live = [e for e in entries if e.get("status") != "stale"]`) filters
`stale` entries out before the digest file is ever written, so
`docs/specs/requirement-digest.md` -- the only input `requirement_drift()`
reads -- can only ever contain `open` or `enforced` in the `[status]`
position. Both are handled by the new filter (`== "open"` keeps drift
checks for open, silently and correctly excludes enforced). Also checked
the `\[(\S+)\]` capture against a paraphrase containing literal brackets
(non-greedy `.+?` anchored to line-end via `$` in MULTILINE mode still
resolves correctly via backtracking) -- confirmed no mis-capture:
`python3 -c "import re; print(re.search(r'^- (R\d+): (.+?) \[(\S+)\] \(source: #(\d+)\)$', '- R001: some paraphrase [with a bracket] more text [enforced] (source: #321)', re.M).groups())"`
-> `('R001', 'some paraphrase [with a bracket] more text', 'enforced', '321')`,
i.e. status correctly captured as `enforced`, not `with`. `pytest
gates/test_requirement_drift.py -q` -- 6 passed. No reproducible defect
found under this stance.
