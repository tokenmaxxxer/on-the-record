---
proposal: docs/issue-1033/proposals/credential-example-allowlist.md
---

# Hunt record — credential-example-allowlist

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: NO FINDING
Seed: docs/issue-1033/proposals/credential-example-allowlist.md (phase-1, docs only, commit 0157c4d); on-the-record/hooks/credential-record-guard.sh and on-the-record/hooks/credential-network-guard.sh (PATTERNS/CRED_PATTERNS + find_credentials, on disk, unchanged)
cap_seconds: 60
tier: default
diff_stat_lines: 2 files added (proposal.md, survey.md), 0 code changed
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:05:00Z

Attempted to construct a string that would pass the planned `m.group(0) in
EXAMPLE_ALLOWLIST` exact-match skip while carrying a real, distinct secret.
Reproduced the current find_credentials() logic from both guards in an
isolated python3 script and tried:
- gluing a real AKIA-shaped key directly onto the allowlisted AWS example
  (both orderings, no separator) — both real and example matches are found
  independently by re.finditer since AKIA[0-9A-Z]{16} is a fixed-length
  (non-greedy-tail) pattern, so the real key's own match never coincides
  with, or gets absorbed into, the example's match span;
- gluing real extra characters onto the unbounded gh[oprs]_{36,} pattern
  after the allowlisted GitHub PAT example — the greedy quantifier extends
  the match to include the real suffix, so m.group(0) no longer equals the
  allowlist entry and the whole glued string is still flagged.
In both directions the real secret's match text is never string-equal to
either allowlisted example, and finditer's non-overlapping scan does not
let one match's skip decision swallow a genuinely different credential.
The exact full-span string-equality design (not prefix/substring, not
regex-folded) forecloses the straightforward "look like the example,
carry a different secret" smuggle. No composition or silent-failure bug
found in the mechanism as specified; did not find a reproducible bypass
within budget.
