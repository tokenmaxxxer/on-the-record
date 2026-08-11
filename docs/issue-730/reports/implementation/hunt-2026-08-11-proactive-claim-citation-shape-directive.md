---
proposal: docs/issue-730/proposals/2026-08-11-proactive-claim-citation-shape-directive.md
---

# Hunt record — proactive-claim-citation-shape-directive

NOTE: board-gate.sh (implementation role) refused a write to
docs/issue-730/reports/hunt-2026-08-11-proactive-claim-citation-shape-directive.md
("belongs to another role. implementation writes only implementation.md,
implementation/** — never a foreign record"), so this record is filed
under reports/implementation/ instead, at the same slug.

## before-landing — stance 0: assume the gate/directive just touched is bypassable — find the bypass

Verdict: FINDING — a rename/refactor of any of the four record_lint.py check functions silently kills the entire directive with no output and no error, contradicting the header comment's claim that it "changes what this directive states too, with no second copy to keep in sync"
Kind: silent-failure
Seed: on-the-record/hooks/record-claim-shape-directive.sh, on-the-record/gates/record_lint.py
cap_seconds: 120
tier: default
diff_stat_lines: ~130 (new hook + hooks.json wiring + 3 tests)
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:25:00Z

### Reproduce
```
cd on-the-record
cp gates/record_lint.py /tmp/record_lint.py.bak
python3 - <<'EOF2'
p = "gates/record_lint.py"
s = open(p).read()
open(p, "w").write(s.replace("def bare_count_claim_check", "def bare_count_claim_check_renamed", 1))
EOF2
cd hooks
echo '{}' | CLAUDE_ROLE=worker bash record-claim-shape-directive.sh; echo "EXIT=$?"
cp /tmp/record_lint.py.bak ../gates/record_lint.py
```

### Observed
```
Traceback (most recent call last):
  File "<stdin>", line 21, in <module>
AttributeError: module 'record_lint' has no attribute 'bare_count_claim_check'. Did you mean: 'bare_count_claim_check_renamed'?
EXIT=0
```
No `<record-claim-citation-directive>` block is printed at all — the hook produces zero output and exits 0 (the same as its documented "role unset / record_lint not importable" no-op path), so a spawned role session gets no proactive directive and nothing anywhere signals that the directive generator broke. The only `except` in the Python payload catches `ImportError`; any other error from touching `record_lint.<check_fn>` (rename, signature change, deletion) falls through to bash's blanket `|| { trap - EXIT; exit 0; }`, which is indistinguishable from every legitimate fail-open path (no CLAUDE_ROLE, no python3, no gates dir, ORCHESTRATE_OFF, module genuinely missing).

### Expected
The header comment claims the generated-not-hand-typed design means "a future change to the check logic's docstring changes what this directive states too, with no second copy to keep in sync" — implying safety against drift. In reality, any refactor that renames one of the four hard-coded `record_lint.<fn>` references (not just docstring edits) silently disables the directive for every future role session with no diagnostic, no test failure signal in production, and no distinguishable exit code from the intentional no-op paths. Sibling `record-claim-guard.sh` (the actual enforcement gate this directive describes) keeps working unaffected, so the directive can silently go stale/blank while the gate it's supposed to preview keeps firing — the two drift apart exactly the way the design claims to prevent.
