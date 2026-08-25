---
proposal: docs/issue-2403/proposals/2026-08-26-conformance-review-issue-2403.md
---

# Hunt record — conformance-review-issue-2403

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

canonical: python3 -c "import sys; sys.path.insert(0,'/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer'); from gates import record_lint; print('violations:', len(record_lint.outcome_claim_citation_check(open('/tmp/test_bypass.md').read())))" (this session, this turn — see the Reproduce block below for the full commands)

Verdict: FINDING — record-claim-guard's outcome-claim citation check (gates/record_lint.py `outcome_claim_citation_check`) accepts the FIRST `canonical:` tag anywhere in a claim's enclosing markdown section as grounding for EVERY outcome-claim marker in that section, even when that tag's command has nothing to do with the specific claim — an unrelated, trivial `canonical: git status` earlier in the section is enough to wave through a later unsubstantiated "requirement met"/"complete" sentence.
Kind: silent-failure
Seed: transition=after-proposal, proposal=docs/issue-2403/proposals/2026-08-26-conformance-review-issue-2403.md, tier=size:>200-lines, cap=180s. Lead given in dispatch: `_CANONICAL_TAG`/`_EXECUTED_LIVE_CANONICAL` dewrap-then-first-`.search()` shape in gates/record_lint.py.
cap_seconds: 180
tier: size:>200-lines
diff_stat_lines: 287 (docs/issue-2403/proposals/2026-08-26-conformance-review-issue-2403.md + docs/issue-2403/reports/conformance-review/survey.md)
started_at: 2026-08-26T00:00:00Z
ended_at: 2026-08-26T00:09:00Z

### Reproduce
```
cat > /tmp/test_bypass.md << 'EOF'
## Some Section

canonical: git status

Unrelated later paragraph: the test suite requirement is met and all changes are complete, no further citation needed here at all.
EOF
python3 -c "
import sys
sys.path.insert(0, '/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer')
from gates import record_lint
text = open('/tmp/test_bypass.md').read()
bad = record_lint.outcome_claim_citation_check(text)
print('violations:', len(bad))
"
```
Also reproduced end-to-end through the live hook itself (same target repo, same working tree as this session):
```
PAYLOAD=$(python3 -c "
import json
content = open('/tmp/test_bypass.md').read()
print(json.dumps({
  'tool_name': 'Write',
  'tool_input': {'file_path': 'docs/issue-2403/reports/conformance-review/survey.md', 'content': content},
  'cwd': '/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2403-conformance-review'
}))
")
RCG_PAYLOAD="$PAYLOAD" RCG_GATES_DIR="/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/gates" \
  bash /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/on-the-record/hooks/record-claim-guard.sh
echo "exit code: $?"
```

### Observed

canonical: python3 -c "import sys; sys.path.insert(0,'/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer'); from gates import record_lint; print(len(record_lint.outcome_claim_citation_check(open('/tmp/test_bypass.md').read())))" — the two commands directly above, executed this turn.

The first command (direct call into `outcome_claim_citation_check`) prints `violations: 0` for content whose only `canonical:` tag (`canonical: git status`) is unrelated to the outcome claim two lines later ("requirement met ... complete"). The second command (the live hook itself, given a `Write` tool_input targeting `docs/issue-2403/reports/conformance-review/survey.md` with exactly this content) exits `0` — allow, no refusal printed.

Root cause: in `gates/record_lint.py`, `outcome_claim_citation_check` computes each outcome-claim line's enclosing section window and then does `m = _CANONICAL_TAG.search(window)` (the line right after the `_section_bounds`/`_prose_window` call) — `.search()` returns only the FIRST `canonical:` match in that dewrapped window. `_EXECUTED_LIVE_CANONICAL` then only has to match THAT one tag's content (here `git status`, which matches the `git\s` prefix) to satisfy `has_executed_live` for the outcome-claim line being checked — the code never checks that the cited command is the same one that produced the specific claim two paragraphs later, nor that it postdates/relates to it in any way. Any section that opens with a throwaway `canonical: git status`/`canonical: pytest -q --collect-only`-shaped decoy tag near the top, and later asserts an unrelated "done"/"complete"/"PASS"/"requirement met" claim with zero real citation of its own, passes this check.

### Expected
A section carrying an outcome claim with no citation that is actually about that specific claim (every `canonical:`/`derived:` tag in the section is for a different claim already consumed, or is an unrelated decoy command) should be refused. The check should anchor the citation search to the nearest tag associated with the specific claim line (e.g. tag on the same line, in the same paragraph, or immediately preceding/following it) rather than accepting any single executed-live-shaped `canonical:` tag anywhere in the whole section as blanket cover for every outcome marker the section contains.
