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

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — role-spec-reference-guard.sh's hardcoded `_VERIFICATION_FAMILY_ROLES` allowlist (in both the shell script's embedded Python and gates/role_spec_shape.py) does not include `capacity-planning`, so a `capacity-planning.md` record containing an axis_evaluation entry with a nonexistent citation path is silently allowed through (exit 0) with no reference-resolution check performed at all — while the identical content under `conformance-review.md` (an allowlisted role) is correctly denied (exit 2). This is the same gap the issue-999 (performance-engineering) hunt record previously flagged, still unfixed for capacity-planning.
Kind: silent-failure
Seed: roles/specs/capacity-planning.spec.json axis_evaluation + gate_c_axis_evaluation wiring (diff vs origin/main)
cap_seconds: 60
tier: default
diff_stat_lines: ~10 (JSON additions to capacity-planning.spec.json)
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:05:00Z

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-1000-implementation
python3 - <<'PYEOF'
import json, subprocess, os

def run(target):
    payload = json.dumps({
      "tool_name": "Write",
      "tool_input": {
        "file_path": target,
        "content": "axis_evaluation cites `docs/handbooks/nonexistent-file-xyz.md` as evidence"
      },
      "cwd": os.getcwd()
    })
    env = dict(os.environ)
    env["RSRG_PAYLOAD"] = payload
    env["RSRG_GATES_DIR"] = os.path.join(os.getcwd(), "gates")
    r = subprocess.run(["bash", "on-the-record/hooks/role-spec-reference-guard.sh"], input=payload, capture_output=True, text=True, env=env)
    print(target, "-> rc=", r.returncode, "stderr=", r.stderr.strip())

run("docs/issue-1000/reports/conformance-review.md")
run("docs/issue-1000/reports/capacity-planning.md")
PYEOF
```

### Observed
```
docs/issue-1000/reports/conformance-review.md -> rc= 2 stderr= role-spec-reference-guard: ... references a path that does not exist ...: `docs/handbooks/nonexistent-file-xyz.md`
docs/issue-1000/reports/capacity-planning.md -> rc= 0 stderr=
```
capacity-planning's record is accepted with an unresolvable citation reference — the reference_resolution.rule the newly-added capacity-planning.spec.json clause claims to enforce is not actually checked for this role by the hook.

### Expected
Either the same rc=2 denial as conformance-review (if capacity-planning's axis_evaluation records are meant to be reference-checked), or the spec's reference_resolution clause and gate_c_axis_evaluation field should not claim enforcement that the hook doesn't perform — `_VERIFICATION_FAMILY_ROLES` should include every role whose spec.json declares this rule.
