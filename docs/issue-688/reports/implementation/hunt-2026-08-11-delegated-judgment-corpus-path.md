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

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: NO FINDING
Seed: on-the-record/hooks/delegated-judgment-gate.sh depth_match(paths, issue_n) scoping change from docs/product to docs/issue-<n>/product; call site DEPTH = depth_match(paths, issue); issue is derived at line 340-343 via `bm = re.match(r"^issue-(\d+)/([\w-]+)$", branch); issue = int(bm.group(1))`, anchored on the current branch name and requiring digits only. issue_n is an `int`, so the f-string `TARGET / "docs" / f"issue-{issue_n}" / "product"` cannot be traversed — no attacker-controlled non-digit content reaches the path. The same `issue` variable is reused consistently for the PR comment, the depth-axis corpus lookup, and derivation_source; there is no second, independently-derived issue number anywhere in the diff that could disagree with it. Checked: (1) path traversal in the f-string — impossible, issue_n is always `int`; (2) falsy/None issue reaching an unintended glob — `if not bm: sys.exit(0)` guards before `issue` is ever assigned, so DEPTH is unreachable with issue undefined or None; (3) branch name producing an issue value diverging from the "real" issue — the branch name is the sole source of `issue` for the whole script (also used as the `gh issue comment` target), so no divergence path exists within this diff; (4) empty/absent corpus still returns False (lines 368-372, short-circuit unchanged) so the AND-composition/escalation invariant holds exactly as before. This diff narrows the corpus from a shared flat `docs/product` (matchable by ANY issue's PR) to a per-issue `docs/issue-<n>/product` — it tightens rather than loosens scope. No reproduction found letting an attacker plant `docs/issue-<n>/product/*.md` content to force a DEPTH match for an issue `n` other than the one on their own branch.
cap_seconds: 120
tier: default
diff_stat_lines: ~15 (delegated-judgment-gate.sh diff hunk)
started_at: 2026-08-11T00:04:00Z
ended_at: 2026-08-11T00:08:30Z
