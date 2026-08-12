---
proposal: docs/issue-1000/proposals/implementation.md
---

# Hunt record — external-burden-axis-wiring

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the proposal's acceptance criterion ("gates/role_spec_shape.py shape checks ... must keep passing") is satisfied by construction and proves nothing about the `gate_c_axis_evaluation` content, because `gate_c_axis_evaluation` is never validated by `gates/role_spec_shape.py` — it is absent from `_TOP_REQUIRED` and from every `check_*` function. Any string (or no key at all) still passes the gate, so phase-2 could land a wrong, empty, or unrelated `gate_c_axis_evaluation` sentence for `external_burden` and the stated "how you'll know it worked" (`role_spec_shape.py` exits 0) would still hold.
Kind: silent-failure
Seed: docs/issue-1000/proposals/implementation.md, docs/issue-1000/reports/implementation/survey.md (git show 802cffa --stat)
cap_seconds: 60
tier: default
diff_stat_lines: 197 (96+101 across two new files)
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:05:00Z

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-1000-implementation
python3 - <<'PY'
import json
p = "roles/specs/performance-engineering.spec.json"
spec = json.load(open(p))
spec.pop("gate_c_axis_evaluation", None)
spec["axis_evaluation_bogus_test"] = "totally unrelated garbage, not even a real key"
json.dump(spec, open(p, "w"), indent=2)
PY
python3 gates/role_spec_shape.py roles/specs/performance-engineering.spec.json; echo "exit=$?"
# revert with git checkout -- roles/specs/performance-engineering.spec.json
```

### Observed
`exit=0` — the gate passes even with `gate_c_axis_evaluation` deleted entirely and replaced by a nonsense key. `grep -n "gate_c_axis_evaluation" gates/role_spec_shape.py` returns no matches: the key is written into every landed spec (architecture, security-threat-model, conformance-review, performance-engineering) but is not part of `_TOP_REQUIRED` or checked by any `check_*` function.

### Expected
If `gate_c_axis_evaluation` is meant to be load-bearing for the axis-evaluation wiring (as the proposal's rationale and "Constraints" section imply by naming it alongside `check_axis_evaluation_entry`/`check_axis_ownership` as something the gate must keep validating), the gate should fail when the key is missing, empty, or doesn't point at a real handbook section — otherwise "gate passes" gives no actual signal that the `external_burden` wiring text is correct, and the proposal's own acceptance test ("how you'll know it worked") is not a real check on the one field phase-2 is actually adding.
