---
proposal: docs/issue-1160/proposals/step3-machinery.md
---

# Hunt record — step3-machinery

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list

Verdict: FINDING — modifying the three pilot specs (step 2 of the plan) trips this repo's own `spec_index.py` commit-time gate, which requires `docs/specs/reconciled-index.md` to be regenerated in the same commit, but that file is not in the proposal's frozen write set.
Kind: design-error
Seed: docs/issue-1160/proposals/step3-machinery.md, commit 396729d (diff vs 6baf542)
cap_seconds: 120
tier: size:21-200
diff_stat_lines: ~370 (3 new docs files, proposal-only)
started_at: 2026-08-13T00:00:00Z
ended_at: 2026-08-13T00:05:00Z

### Reproduce
```
grep -n '^| `' docs/specs/reconciled-index.md
# shows roles/specs/{brand-design,content-design,market-analysis}.spec.json tracked with pinned SHA256 hashes

python3 - <<'PY'
import json
p = "roles/specs/brand-design.spec.json"
d = json.load(open(p))
d.setdefault("use_when", {}).setdefault("need_detector", {})["present_patterns"] = ["**/*.tsx"]
open(p, "w").write(json.dumps(d, indent=2) + "\n")
PY
git add roles/specs/brand-design.spec.json
python3 gates/spec_index.py .
echo "exit: $?"
```

### Observed
```
게이트 차단:
  - roles/specs/brand-design.spec.json: 내용이 바뀌었는데 docs/specs/reconciled-index.md 의 기록된 해시와 다르다 (기록=782f48a1b14d…, 실제=8b9e9ba3784b…) — 의도된 변경이면 `python3 gates/spec_index.py --update` 로 재생성하고 관련 있다면 "Resolved ambiguities" 도 갱신하라
exit: 1
```
`spec-index-preflight.sh` (docs/specs/generated-paths.md, docs/specs/enforcement-boundary.md) enforces exactly this at commit time: a staged spec-index-tracked file whose content changed without a matching index regen in the same staged set is denied.

### Expected
The proposal step 2 changes to `roles/specs/{brand-design,content-design,market-analysis}.spec.json` (adding `present_patterns`/`absent_patterns` under `use_when.need_detector`) are exactly the kind of content change `spec_index.py` tracks for these three files. The commit implementing step 2 will therefore be blocked unless `docs/specs/reconciled-index.md` is also regenerated (`python3 gates/spec_index.py --update`) and staged in the same commit — but `docs/specs/reconciled-index.md` does not appear anywhere in the proposal's frozen `files:` write set.
