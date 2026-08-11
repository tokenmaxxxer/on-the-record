---
proposal: docs/issue-793/proposals/verify-before-claim.md
---

# Hunt record — verify-before-claim

## after-proposal — stance 0: assume the gate just proposed is bypassable — find the bypass.

Verdict: FINDING — the described claim-marker vocabulary (`halted|merged|closed|found|confirms?|is (running|gone|stale)`) is a small fixed word list, so a state/PR/role-output claim phrased with any synonym (shipped, wrapped up, died, present, done) never matches and the gate never fires — no `canonical:` tag is required and none is written, letting a fabricated claim through with zero citation.
Kind: design-error
Seed: docs/issue-793/proposals/verify-before-claim.md, section "Gate extension" — marker vocabulary `halted|merged|closed|found|confirms?|is (running|gone|stale)`; sibling precedent gates/record_lint.py bare_count_claim_check's fixed regex (_COUNT_RATIO/_COUNT_NOUN)
cap_seconds: 180
tier: size:>200-lines-2-files
diff_stat_lines: 258 (2 files)
started_at: 2026-08-11T16:51:32+09:00
ended_at: 2026-08-11T16:58:00+09:00

### Reproduce
```
python3 -c "
import re
_MARK = re.compile(r'halted|merged|closed|found|confirms?|is (running|gone|stale)')
claims = [
  'PR 790 has shipped to main.',
  'The session died mid-run.',
  'Role X wrapped up successfully.',
  'The defect is present.',
  'Board state: everything is done.',
]
for c in claims:
    print(bool(_MARK.search(c)), '-', c)
"
```

### Observed
All five state/defect claims (the exact taxonomy rows 1/2 the proposal targets: role-output claim, session/PR state claim, defect claim) print `False` — the marker regex does not match, so under the design as described the gate never detects these as claim-marker sentences, never requires a `canonical:` tag, and a fabricated/unverified claim ships with no tag and no refusal.

### Expected
A gate meant to close the "false claim from a summary" gap should not be defeated by trivial verb-choice (using "shipped" instead of "merged", "died" instead of "gone", "wrapped up" instead of "found/closed") — the proposal's own motivating incident ("consumer session traced 5 wrong judgments... asserting on role-summary/partial-observation") is exactly the kind of natural-language claim this fixed vocabulary will miss.
