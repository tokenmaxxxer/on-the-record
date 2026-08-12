---
proposal: docs/issue-1024/proposals/2026-08-12-requirement-intake-validity-consult.md
---

# Hunt record — requirement-intake-validity-consult

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the planned check accepts any string as trace ref or skip reason, so a fake trace ref or an arbitrary (non-trivial, self-serving) skip reason on a risk-bearing ask passes unchanged
Kind: design-error
Seed: docs/issue-1024/proposals/2026-08-12-requirement-intake-validity-consult.md, "What will be done" item 2 (gates/requirement_intake_consult.py check_issue_body spec)
cap_seconds: 60
tier: default
diff_stat_lines: docs-only (proposal + survey, no code yet)
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:02:00Z

### Reproduce
Implemented `check_issue_body` exactly per the spec text ("pass-through when
the body carries a validity-consult trace reference (a distinct greppable
tag, e.g. `validity-consult: <ref>`) or the literal skip tag
`validity-consult-skip: trivial` (or another named, non-prose reason)"):

```python
import re
_TRACE = re.compile(r"^\s*[-*]?\s*validity-consult\s*:\s*\S", re.IGNORECASE | re.MULTILINE)
_SKIP = re.compile(r"^\s*[-*]?\s*validity-consult-skip\s*:\s*\S", re.IGNORECASE | re.MULTILINE)
def check_issue_body(issue, body):
    body = body or ""
    if _TRACE.search(body) or _SKIP.search(body):
        return []
    return [f"issue #{issue}: missing validity-consult trace/skip"]

body1 = "## Acceptance\nvalidity-consult: none\n"
print(check_issue_body(1024, body1))

body2 = ("## Request\nDelete all user credentials and disable auth checks "
         "on external API calls.\n\nvalidity-consult-skip: not-now\n")
print(check_issue_body(1024, body2))
```

### Observed
Both calls return `[]` (pass): a `validity-consult: none` line satisfies the
"trace reference" branch with no verification the ref points to a real
consult trace, and a plainly risk-bearing ask (deletes credentials, disables
auth) is skipped with an arbitrary reason `not-now` — the spec explicitly
allows "another named, non-prose reason" beyond `trivial`, with no allowlist
and no runtime step that verifies the reason is actually trivial or that
`requirements-engineering`/`risk-management` were genuinely inapplicable.

### Expected
A gate meant to guarantee a validity consult happened (or was legitimately
skipped only for trivial asks) should not be satisfiable by an unverified
placeholder trace value, and the skip path — per the proposal's own
constraint ("Trivial asks must have a first-class skip path") — should not
accept arbitrary named reasons for asks that are self-evidently
risk-bearing. As specified, both the trace-ref and skip-tag branches are
pure string-presence checks with no constraint tying the reason to
triviality or the ref to a genuine consult record, so the check can be
satisfied on every drafted issue regardless of actual consult status.

## before-landing — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — `validity-consult: <ref>` accepts any non-whitespace token as the "trace reference"; no store/log of actual consults exists for it to be checked against, so the gate cannot distinguish a real feasibility-consult trace from an arbitrary string typed to satisfy the regex.
Kind: design-error
Seed: gates/requirement_intake_consult.py (check_issue_body, _CONSULT_REF)
cap_seconds: 120
tier: default
diff_stat_lines: ~150
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:05:00Z

### Reproduce
```
python3 -c "
from gates.requirement_intake_consult import check_issue_body
print(check_issue_body(1, 'validity-consult: asdfasdf-not-a-real-ref'))
"
```

### Observed
`[]` (gate passes) — no violations reported for a fabricated, meaningless reference.

### Expected
The gate's own docstring claims it checks "타당성 자문이 실행됐거나" (that a validity consult actually ran), i.e. it is meant to gate on a real trace of a consult having happened. Since no such trace store is maintained or consulted anywhere in the repo, the "trace reference" check is unenforceable as written — any string satisfies it, so the gate cannot actually verify the claimed condition.
