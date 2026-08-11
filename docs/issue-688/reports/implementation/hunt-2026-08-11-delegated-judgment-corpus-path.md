---
proposal: docs/issue-688/proposals/2026-08-11-delegated-judgment-corpus-path.md
---

# Hunt record — delegated-judgment-corpus-path

## after-proposal — stance 4: assume the write set this proposal froze cannot carry the work — find a path the build will actually need that the proposal's `files:` list does not include.

Verdict: FINDING — on-the-record/hooks/test_delegated_judgment_gate_triage.py (not in the frozen `files:` list) writes its depth-axis-clearing fixture at the retired flat docs/product/priorities.md path, and will fail once `depth_match`'s `corpus_dir` moves to the issue-scoped path as the proposal describes.
Kind: silent-failure
Seed: docs/issue-688/proposals/2026-08-11-delegated-judgment-corpus-path.md (files: on-the-record/hooks/delegated-judgment-gate.sh, on-the-record/hooks/test_delegated_judgment_gate.py)
cap_seconds: 60
tier: default
diff_stat_lines: 157 (docs-only proposal diff; reproduction applied against the hook script)
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:15:00Z

### Reproduce
```
grep -rln 'docs/product' --include=*.sh --include=*.py .
# -> lists on-the-record/hooks/test_delegated_judgment_gate_triage.py among the hits,
#    a file the proposal's files: list does not include.

# Apply the proposal's described corpus_dir change directly to the hook:
python3 - <<'PY'
p = "on-the-record/hooks/delegated-judgment-gate.sh"
s = open(p).read()
s = s.replace('corpus_dir = TARGET / "docs" / "product"',
              'corpus_dir = TARGET / "docs" / f"issue-{issue}" / "product"')
open(p, "w").write(s)
PY

python3 -m pytest on-the-record/hooks/test_delegated_judgment_gate_triage.py -q -k single_owner_supports
```

### Observed
```
FAILED on-the-record/hooks/test_delegated_judgment_gate_triage.py::test_single_owner_supports_resolves
AssertionError: assert 'decision: resolved' in "...decision: escalated..."
```
The test writes to docs/product/priorities.md intending to clear the depth axis (comment: "clear the depth axis: docs/product corpus mentions a changed basename"), but the fixture no longer lands where `depth_match` reads once `corpus_dir` becomes issue-scoped, so the depth axis stays unmatched and the panel escalates instead of resolving.

### Expected
The proposal's write set should include on-the-record/hooks/test_delegated_judgment_gate_triage.py (or note it as a required follow-up edit), since it independently exercises the same retired flat corpus path with real assertions that break once the reader moves — not just the two files (delegated-judgment-gate.sh, test_delegated_judgment_gate.py) it lists.
