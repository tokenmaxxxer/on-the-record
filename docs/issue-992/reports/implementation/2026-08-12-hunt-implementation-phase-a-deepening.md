
## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — approval-gate.sh only guards the role's record file and src/tests/ paths, so the actual phase-2 deliverables this proposal names (roles/specs/*.spec.json, docs/handbooks/architecture-methodology.md) can be written by the implementation-role session with zero APPROVE issue-992/implementation comment, silently bypassing the very gate the proposal relies on.
Kind: composition
Seed: docs/issue-992/proposals/2026-08-12-implementation-phase-a-deepening.md, docs/issue-992/reports/implementation/survey.md (git diff 643eb32 HEAD)
cap_seconds: 120
tier: size:21-200(docs-only)
diff_stat_lines: 228
started_at: 2026-08-12T03:43:41Z
ended_at: 2026-08-12T03:44:10Z

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-992-implementation
export CLAUDE_ROLE=implementation   # branch is issue-992/implementation, no APPROVE comment posted for this role
payload=$(python3 -c 'import json,os;print(json.dumps({"tool_name":"Write","tool_input":{"file_path":"roles/specs/conformance-review.spec.json"},"session_id":"x","cwd":os.getcwd()}))')
echo "$payload" | bash on-the-record/hooks/approval-gate.sh; echo "exit=$?"

payload2=$(python3 -c 'import json,os;print(json.dumps({"tool_name":"Write","tool_input":{"file_path":"docs/handbooks/architecture-methodology.md"},"session_id":"x","cwd":os.getcwd()}))')
echo "$payload2" | bash on-the-record/hooks/approval-gate.sh; echo "exit=$?"
```

### Observed
Both writes exit 0 (allowed), with no `APPROVE issue-992/implementation` comment on the issue and no `docs/specs/approvers.md`-gated review at all — the hook's `is_record`/`is_src_test` scope check (`n == record_path` or `re.search(r"(^|/)(src|tests?)/", n)`) never matches `roles/specs/conformance-review.spec.json` or `docs/handbooks/architecture-methodology.md`, which are exactly the two file classes the proposal's "What will be done" section names as the phase-2 edits gated on approval (axis_evaluation sections in the handbook, finding_method/anti_pattern fields in the spec.json files). By contrast, a write to the role's own record file (`docs/issue-992/reports/implementation.md`) with no approval is correctly denied (exit 2).

### Expected
Either the proposal's claim that these edits "land under implementation's own two-phase gate" once `APPROVE issue-992/implementation` is posted should be false-guaranteed by the actual runtime gate (i.e. writes to `roles/specs/*.spec.json` and `docs/handbooks/*.md` should also be deny-checked when made from a role session mid-issue), or the proposal should not claim these specific out-of-scope-for-the-hook files are gated by approval-gate.sh at all.

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — gates/role_spec_shape.py never validates the new `finding_method`/`anti_pattern` fields added by this diff; any content (wrong type, empty, garbage) in those fields passes the shape gate silently.
Kind: silent-failure
Seed: roles/specs/requirements-engineering.spec.json, roles/specs/risk-management.spec.json additive `finding_method`/`anti_pattern` array fields; gates/role_spec_shape.py
cap_seconds: 180
tier: default
diff_stat_lines: (not measured — see dispatcher)
started_at: 2026-08-12T12:54:09+09:00
ended_at: 2026-08-12T12:58:30+09:00

### Reproduce
```
python3 -c "
import json
d = json.load(open('roles/specs/requirements-engineering.spec.json'))
d['finding_method'] = 'not even an array, just a string'
d['anti_pattern'] = 12345
json.dump(d, open('/tmp/bad.spec.json','w'))
"
python3 gates/role_spec_shape.py /tmp/bad.spec.json; echo "exit=$?"
grep -rn "finding_method\|anti_pattern" gates/
```

### Observed
`exit=0` — the gate passes a spec where `finding_method` is a bare string (not an array) and `anti_pattern` is an integer. `grep` across `gates/` finds zero references to either field name anywhere in the enforcement code — `check()` in role_spec_shape.py only walks `_TOP_REQUIRED` keys and `required_fields[]` entries; the new fields are never inspected.

### Expected
A gate whose stated job is shape-checking role specs should either reject malformed `finding_method`/`anti_pattern` content or the diff should not introduce these as machine-checked-looking additive fields without adding corresponding validation — as written, any future spec can carry garbage in these fields with no gate ever catching it.
