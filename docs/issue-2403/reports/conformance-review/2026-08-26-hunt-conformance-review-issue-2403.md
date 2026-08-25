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

## before-landing — stance 0: the record's own conclusion doesn't compose with the mechanism it cites

Verdict: FINDING — requirement 5b's Present verdict ("nothing is auto-merged on the basis of a rebase alone") rests on evidence that misstates what `gates/merge_gate.py`'s `required_verification_missing()` actually checks: the record claims the execution-observation spec's per-sha `use_when.trigger` "already requires a fresh execution-observation record before evaluate()'s required_verification_missing() check ... stops blocking a merge on the new sha," but `required_verification_missing()` (via `spawn_on_pr.applicable_roles()`) only checks whether `docs/issue-<n>/reports/execution-observation.md` exists at all for the subject — it never compares that record's own cited sha against the current PR head. A pre-rebase observation record silently continues to satisfy the check after a mechanical rebase mints a new, unobserved head sha.
Kind: silent-failure
Seed: docs/issue-2403/reports/conformance-review.md (before-landing delivery for PR #2462), specifically requirement 5b's evidence block, cross-checked against a6ffa970:gates/merge_gate.py, a6ffa970:gates/spawn_on_pr.py, a6ffa970:board.py, a6ffa970:gates/roles_due.py, a6ffa970:gates/test_merge_gate.py (worktree /tmp/wt-2403, sha a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5, same PR #2452 head the record cites).
cap_seconds: not specified by dispatcher for this transition (prior after-proposal dispatch on this unit used 180s / tier size:>200-lines; carried forward as the closest reference point)
tier: size:>200-lines (record under review is 414 lines, new file)
diff_stat_lines: 414 (docs/issue-2403/reports/conformance-review.md, new file, this work unit's own delivery)
started_at: 2026-08-25T23:10:00Z
ended_at: 2026-08-25T23:26:00Z

### Reproduce
```
cd /tmp/wt-2403   # worktree of PR #2452 head a6ffa970, same sha the record cites throughout
python3 - <<'EOF'
import subprocess, tempfile, sys
from pathlib import Path
sys.path.insert(0, "gates")
import merge_gate

tmp = Path(tempfile.mkdtemp())
repo = tmp / "repo"
repo.mkdir()
subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
docs = repo / "docs" / "issue-9999" / "reports"
docs.mkdir(parents=True)
(docs / "implementation.md").write_text("---\nloop_state: landed\n---\nbody v1\n")
(docs / "execution-observation.md").write_text(
    "---\nloop_state: reported\nresult: passed\ncode_under_review:\n"
    "  - path: foo.py\n    sha: OLDSHA_BEFORE_REBASE\n---\nbody v1 observation\n")
subprocess.run(["git", "add", "."], cwd=repo, check=True)
subprocess.run(["git", "commit", "-q", "-m", "init: implementation + old observation"], cwd=repo, check=True)
before_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout.strip()
print("missing before rebase-equivalent new commit:",
      merge_gate.required_verification_missing(repo, "issue-9999"))

# Simulate exactly what a6ffa970:spawn.py:2286 _mechanical_rebase() does:
# mint a NEW commit on the branch (new head sha) -- the execution-observation
# record is never touched or re-written.
(docs / "implementation.md").write_text("---\nloop_state: landed\n---\nbody v1, rebased onto new base\n")
subprocess.run(["git", "add", "."], cwd=repo, check=True)
subprocess.run(["git", "commit", "-q", "-m", "mechanical rebase: new head sha, no new observation"], cwd=repo, check=True)
after_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout.strip()
print("before_sha:", before_sha)
print("after_sha (new head, post-rebase):", after_sha)
print("missing after new head sha with NO fresh observation record:",
      merge_gate.required_verification_missing(repo, "issue-9999"))
EOF
```

### Observed
```
missing before rebase-equivalent new commit: ['conformance-review']
before_sha: 5ded2b13210c50cde07249cbe184facf48b731cf
after_sha (new head, post-rebase): fbc6e32113339a47a0c6f3681d1f39b4879edc73
missing after new head sha with NO fresh observation record: ['conformance-review']
```
`required_verification_missing()` returns the identical list before and after the head sha changes — the pre-rebase `execution-observation.md` record (still citing `OLDSHA_BEFORE_REBASE` in its own frontmatter) continues to satisfy the check for the new, never-observed sha. Confirmed structurally: `a6ffa970:gates/spawn_on_pr.py:70-74` `applicable_roles()` is `[r for r in roles if r not in subject_board]` — presence-only, no sha comparison; `a6ffa970:board.py:723-748` `board()` reads one `<role>.md` file per subject (whichever record was last written, overwritten in place) with no per-sha keying; `a6ffa970:gates/merge_gate.py` contains exactly one occurrence of the string `sha` in the whole file (a comment on an unrelated line, `grep -n sha a6ffa970:gates/merge_gate.py`, this session) — no sha-comparison code exists anywhere in the actual merge-blocking path. `a6ffa970:gates/test_merge_gate.py:98-107`'s own fixtures for `required_verification_missing_none`/`_some` write records with no `sha` field at all, confirming the function was never designed to check one. The record's cited `use_when.trigger` (`roles/specs/execution-observation.spec.json:46-50`) is consumed only by `gates/roles_due.py` — a separate, advisory *spawn-trigger* evaluator (compares the record file's own last-touching commit against the trigger-matched file's last-touching commit) that decides whether to recommend spawning a fresh observation role; it is not wired into `merge_gate.evaluate()` at all and does not gate the merge.

### Expected
Requirement 5b's Present verdict, if grounded in "the per-sha observer trigger... requires a fresh execution-observation record before evaluate()'s required_verification_missing() check stops blocking a merge on the new sha," should have been checked against `required_verification_missing()`'s actual behavior (as its own line-range citation, `a6ffa970:gates/merge_gate.py:130-145`, already points at) rather than against the separate `roles_due.py`/`use_when.trigger` spawn-recommendation mechanism the evidence block actually quotes. Either the verdict needed to name this gap (a mechanical rebase can silently ride on a stale pre-rebase observation record to pass `evaluate()`, since the merge-blocking check is presence-only, not sha-scoped) or cite a different, real enforcement point that does compare shas — none exists in `a6ffa970`.
