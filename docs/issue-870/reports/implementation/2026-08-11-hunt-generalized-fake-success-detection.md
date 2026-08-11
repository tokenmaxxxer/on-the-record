---
proposal: docs/issue-870/proposals/2026-08-11-generalized-fake-success-detection.md
---

# Hunt record — generalized-fake-success-detection

## before-landing — stance 2: assume this guard goes silent when its own input is malformed — make it go silent

Verdict: FINDING — `_EXECUTED_LIVE_CANONICAL`'s "acceptance:\s" branch accepts any free text after "acceptance:", not just an actually-executed `acceptance: <command> — result: ...` line, so a `canonical:` tag reading `canonical: acceptance: <any prose>` silently satisfies the OUTCOME-claim citation requirement with zero execution evidence.
Kind: silent-failure
Seed: gates/record_lint.py `_EXECUTED_LIVE_CANONICAL` / `outcome_claim_citation_check`, mirrored in on-the-record/gates/record_lint.py
cap_seconds: 120
tier: default
diff_stat_lines: ~150
started_at: 2026-08-12T00:34:37+09:00
ended_at: 2026-08-12T00:38:00+09:00

### Reproduce
```
python3 -c "
import sys
sys.path.insert(0,'gates')
import record_lint as rl

text = '''canonical: acceptance: reviewer says it looks fine
All requirements met, task complete.
'''
print(rl.outcome_claim_citation_check(text))
"
```

### Observed
`[]` — the check reports no violation. The `canonical:` cited text is `acceptance: reviewer says it looks fine`, which matches `_EXECUTED_LIVE_CANONICAL` purely because it starts with the literal string `acceptance:`, even though nothing resembling a command or `— result:` transcript follows it. Any record author can write this exact pattern to make an "requirement met / done / PASS / complete" claim pass the guard without ever running anything.

### Expected
The `acceptance:` branch of `_EXECUTED_LIVE_CANONICAL` should require the cited text to actually look like an executed acceptance check (e.g. `acceptance: <command> — result: ...`, matching the docstring's own description), not match on the bare prefix alone — otherwise the OUTCOME-claim check is trivially satisfiable by any text starting with the word "acceptance:".
