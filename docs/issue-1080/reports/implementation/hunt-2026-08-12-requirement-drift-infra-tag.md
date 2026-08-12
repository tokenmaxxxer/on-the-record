---
proposal: docs/issue-1080/proposals/2026-08-12-requirement-drift-infra-tag.md
---

# Hunt record — requirement-drift-infra-tag

## after-proposal — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — the proposed `_INFRA_TAG` skip applies to PRs (via the shared `issues + prs` loop in `requirement_drift`), but `_INFRA_TAG` is only ever enforced/maintained as a meaningful marker on issue bodies — `require_requirement_linkage` (the sole enforcer) returns immediately when `issue is None`, so nothing stamps or checks the tag on PRs. "Mirroring `check_issue_body`'s existing exception" onto PR text extends the exemption into state nothing maintains, silently widening the false-negative class the proposal exists to shrink.
Kind: design-error
Seed: docs/issue-1080/proposals/2026-08-12-requirement-drift-infra-tag.md (plan: skip appending to `unreferenced_open` when item title/body contains `_INFRA_TAG`, applied uniformly to `for item in issues + prs` in `spawn.py::requirement_drift`)
cap_seconds: 60
tier: default
diff_stat_lines: 0 (docs-only proposal, no code diff yet)
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:05:00Z

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-1080-implementation
python3 -c "
import sys, re
sys.path.insert(0, 'gates')
import requirement_linkage as _requirement_linkage

pr = {'number': 9999, 'title': 'Some refactor PR', 'body': 'Closes #745, which used the infrastructure/no-direct-requirement tag.'}
text = f\"{pr.get('title','')}\n{pr.get('body','') or ''}\"
raw_ids = set(re.findall(r'\bR\d+\b', text))
tagged = _requirement_linkage._INFRA_TAG in text
print('cites a requirement?', raw_ids)
print('would be exempted under proposed fix?', tagged)
"
```
Also confirmed the tag's only enforcer is issue-scoped:
```
grep -n "def require_requirement_linkage" -A 5 spawn.py   # shows `if issue is None: return`
grep -n "def check\b" -A 6 gates/requirement_linkage.py   # `check(repo, issue)` uses `gh issue view`, PR-blind
```

### Observed
`cites a requirement? set()` and `would be exempted under proposed fix? True` — a PR that cites no requirement ID and was never subject to the `_INFRA_TAG` gate (PRs are exempt from `require_requirement_linkage` entirely) is nonetheless silently dropped from `unreferenced_open` merely because its text contains the tag substring incidentally (e.g. quoting another issue's justification).

### Expected
The skip condition should not extend to PRs (or the proposal should state, and the implementation enforce, why a marker that is never applied/required on PRs is nonetheless trusted there) — otherwise `unreferenced_open`'s PR coverage silently degrades with no corresponding invariant backing the exemption.
