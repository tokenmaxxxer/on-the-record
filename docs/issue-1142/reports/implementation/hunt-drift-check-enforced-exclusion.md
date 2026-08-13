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
