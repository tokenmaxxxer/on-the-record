---
proposal: docs/issue-930/proposals/requirement-digest-drift-guard.md
---

# Hunt record — requirement-digest-drift-guard

## after-proposal — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — the digest/drift-guard design's `open`/`enforced` vs `stale` filtering (step 3: "read the live requirement IDs from `requirement-digest.md` (status `open`/`enforced`, excluding `stale`)") depends on a `status: stale` value that no component in the repo, old or new, ever writes — `docs/specs/requirements.md`'s own field doc claims "`stale` is computed by `gates.requirement_registry`", but that gate only appends to a CI failure list (`bad`) when a `check` path is missing; it never mutates the `status:` field in the file. The proposal inherits this dead status value as the discriminator for what the digest/drift-guard treats as "no longer live", without adding any mechanism (in the digest generator, the preflight hook, or `requirement_drift()`) that actually computes or writes it. The result: an entry whose `check` artifact has been deleted keeps `status: enforced` forever, the digest keeps listing it as live, and `requirement_drift()` keeps comparing open issues/PRs against a requirement that is factually dead — silently, because the CI gate failure (which does fire) is a separate, disconnected signal that never updates the field the digest/drift-guard actually reads.
Kind: design-error
Seed: docs/issue-930/proposals/requirement-digest-drift-guard.md; docs/specs/requirements.md; gates/gates.py::requirement_registry; gates/spec_index.py; on-the-record/hooks/spec-index-preflight.sh
cap_seconds: 120
tier: default
diff_stat_lines: proposal-only (no code diff; new proposal file ~150 lines)
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:10:00Z

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-930-product-discovery
grep -n "stale" gates/gates.py gates/spec_index.py docs/specs/requirements.md
python3 - <<'PY'
import sys; sys.path.insert(0, "gates")
import gates as g
text = """## R999

quote: test
source_issue: 1
check: gates/does_not_exist.py::foo
status: enforced
"""
entries, bad = g._parse_requirements(text)
print("entries:", entries)
print("bad:", bad)
PY
```

### Observed
`grep -n "stale" gates/gates.py gates/spec_index.py` returns no matches at all — the string "stale" (the third `status` value the digest/drift-guard design filters on) does not exist anywhere in the code that is supposed to compute it. The reproduction script shows `requirement_registry`'s parser leaves `status: 'enforced'` untouched on an entry whose `check` path is missing; the only output is a `bad` CI-failure line, not a status mutation — so a dead requirement's `status` field never becomes `stale` and the digest generator (which per the proposal derives "one condensed line per entry currently in `requirements.md`") would keep emitting it as `[enforced]`, and `requirement_drift()`'s exclusion of `stale` entries never triggers for it.

### Expected
For the digest's `open`/`enforced`-vs-`stale` filter and the drift guard's "excluding stale" rule to mean anything, some component (existing or newly proposed) must actually transition an entry's `status` to `stale` when its `check` artifact stops existing. The proposal names no such mechanism — it only reuses the pre-existing (and itself broken) claim that `gates.requirement_registry` computes it.
