---
proposal: docs/issue-729/proposals/2026-08-11-consolidate-test-homes.md
---

# Hunt record — consolidate-test-homes

Note: the dispatch prompt named the record path as
`docs/issue-729/reports/hunt-2026-08-11-consolidate-test-homes.md` (flat,
directly under `reports/`). This repo's `board-gate.sh` R5 rule refuses
that path for a role-scoped session (`implementation` writes only
`implementation.md` or `implementation/**`), and every existing
`hunt-*.md` in this repo's own history lives under
`reports/<role>/hunt-*.md` — so this record is filed at
`docs/issue-729/reports/implementation/hunt-2026-08-11-consolidate-test-homes.md`
instead, matching the repo's actual convention.

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the proposal's "Zero broken references" acceptance check and its file-location documentation constraint both miss `docs/handbooks/test-fixture-shape-contracts.md`, a live (non-historical) handbook that hard-codes `shape_contracts.py`'s location as "repo root" — the move makes this claim false and nothing in the plan or its verification step would catch or fix it.
Kind: silent-failure
Seed: docs/issue-729/proposals/2026-08-11-consolidate-test-homes.md (+ docs/issue-729/reports/implementation/survey.md, docs/issue-729/reports/implementation/scout-brief.md)
cap_seconds: 60
tier: size:docs-only
diff_stat_lines: 487 insertions, 3 files (all docs, commit d9f6741)
started_at: 2026-08-11T13:40:00+09:00
ended_at: 2026-08-11T13:56:00+09:00

### Reproduce
```
cd /Users/jk/.tokenmaxxxer/work/on-the-record-issue-729-implementation

# 1. The proposal's own "Zero broken references" check text:
grep -n "Zero broken references" -A3 docs/issue-729/proposals/2026-08-11-consolidate-test-homes.md
# -> scopes the grep to: spawn.py, every file under gates/, every file
#    under on-the-record/ only.

# 2. shape_contracts.py is in the move set (proposal's own files: front
#    matter and "What will be done" list it as one of the nine files
#    git-mv'd from root into tests/).

# 3. A live handbook makes a location claim about it, outside the
#    proposal's checked scope:
grep -n "shape_contracts.py.*repo root" docs/handbooks/test-fixture-shape-contracts.md
grep -n "test_spawn.py" docs/handbooks/test-fixture-shape-contracts.md

# 4. The proposal never names or touches this handbook:
grep -n "test-fixture-shape-contracts" docs/issue-729/proposals/2026-08-11-consolidate-test-homes.md
echo "exit=$?"   # 1 -> no match anywhere in the proposal
```

### Observed
`docs/handbooks/test-fixture-shape-contracts.md:7` reads `` `shape_contracts.py` (repo root) ``,
and line 40 references `test_spawn.py` by its current bare name in a
doc-comment example. The proposal's `files:` front matter (19 entries),
"What will be done" section, and "Zero broken references" verification
step (grep of `spawn.py` + `gates/` + `on-the-record/` only) none mention
or cover `docs/handbooks/`. `grep -n "test-fixture-shape-contracts"` over
the proposal returns nothing (exit 1) — the document doesn't know this
handbook exists. If phase-2 executes exactly as written, this handbook
ends up asserting a false location for `shape_contracts.py` and no listed
acceptance check would fail because of it — it's outside every check's
scope by construction, not despite it.

### Expected
Either the handbook is added to the proposal's `files:` list and "What
will be done" (parallel to how `docs/handbooks/operations.md` was
handled), or the "Zero broken references" check's scope is widened to
include `docs/handbooks/` (not just `spawn.py`/`gates/`/`on-the-record/`),
so a stale location claim in a live handbook can't survive the move
undetected. The proposal explicitly claims "the placement rule must end
up recorded in exactly one document a new test author can read" — but
this second handbook, which also states a location, is left with no
update path and no check that would surface its staleness.
