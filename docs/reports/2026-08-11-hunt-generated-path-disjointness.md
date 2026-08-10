---
proposal: docs/issue-684/proposals/2026-08-11-generated-path-disjointness.md
---

# Hunt record — generated-path-disjointness

## before-landing — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list

Verdict: FINDING — delegated-judgment-gate.sh's depth axis still reads the retired global `docs/product/*.md` path, not the new issue-scoped `docs/issue-<n>/product/*.md` path product-capture-stopgate.sh was just moved to, so the depth axis is now permanently unmatched in any repo that doesn't also carry a stray legacy `docs/product/` dir.
Kind: composition
Seed: on-the-record/hooks/product-capture-stopgate.sh (write target moved to docs/issue-<n>/product/<cat>.md), docs/specs/generated-paths.md, gates/test_generated_paths.py
cap_seconds: 180
tier: default
diff_stat_lines: 203 (4 files changed, 203 insertions, 7 deletions, per `git diff --stat`)
started_at: 2026-08-10T23:49:30Z
ended_at: 2026-08-10T23:58:00Z

### Reproduce
```
grep -n 'corpus_dir\|docs.*product' on-the-record/hooks/delegated-judgment-gate.sh
```
Output includes:
```
367:    corpus_dir = TARGET / "docs" / "product"
```
No occurrence of `issue-{issue}` / `f"docs/issue-{n}/product"` anywhere in the file's `depth_match()` — confirmed by:
```
grep -n 'seg\|"product"\|docs.*product\|corpus_dir' on-the-record/hooks/delegated-judgment-gate.sh
```

Standalone repro of the reader logic (verbatim `depth_match()` body from delegated-judgment-gate.sh, lines 366-378), run against a target dir carrying only the new issue-scoped corpus location:
```python
TARGET = Path(<target>)
seg = "product"
corpus_dir = TARGET / "docs" / seg          # <- still docs/product, never docs/issue-<n>/product
if not corpus_dir.is_dir():
    return False   # <- this branch is taken for every repo after issue #684's move,
                    #    since nothing writes docs/product/ anymore
```
Executed (docs/issue-300/product/priorities.md populated with a matching entry, docs/product/ absent): `depth_match(['x.md'])` returns `False`.
Executed with a legacy `docs/product/priorities.md` (the old, no-longer-written location) instead: `depth_match(['x.md'])` returns `True` — i.e. the function's result is now driven entirely by a directory nothing in the codebase populates anymore, and is blind to the directory product-capture-stopgate.sh actually writes to post-fix.

### Expected
The proposal's completeness claim ("every write-producing generator" surveyed for disjointness, and product-capture-stopgate.sh's move validated as "safe") implicitly requires that consumers of the moved corpus be updated or at least flagged. `docs/specs/generated-paths.md` and `gates/test_generated_paths.py` only inventory *writers* (`write_text`/`open(...,"w")`/`.mkdir(`/etc.) in `on-the-record/hooks/*.sh`; they never check that a mechanism's *readers* of a relocated write target were updated to match. delegated-judgment-gate.sh's `depth_match()` — the very consumer named in its own header comment ("recorded under docs/product/*.md") and in docs/specs/enforcement-boundary.md's row for this hook — should have been updated to `docs/issue-{issue}/product/*.md` alongside the writer, or the spec/gate should have flagged the stale reference. Neither happened, so the depth axis of delegated-judgment-gate.sh is now silently and permanently unsatisfiable in ordinary use (short of a stray legacy docs/product/ directory), a build the proposal did not account for.
