---
proposal: docs/issue-1718/proposals/2026-08-17-decision-queue-stopgate-active-scope-fix.md
---

# Hunt record — decision-queue-stopgate-active-scope-fix

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: NO FINDING
Seed: docs/issue-1718/proposals/2026-08-17-decision-queue-stopgate-active-scope-fix.md, docs/issue-1718/reports/implementation/survey.md (docs-only diff, main...HEAD)
cap_seconds: 60
tier: docs-only / size:docs-only
diff_stat_lines: 298 (two new files, 135 + 163 lines)
started_at: 2026-08-17T09:15:00Z
ended_at: 2026-08-17T09:23:25Z

Checked three candidate bypasses, none reproduced a wrong output.

Check 1 — the `"issue"` field type across the arrays the planned filter would set-intersect.
canonical: gates/flows.py (read in full this session)
derived: `grep -n '"issue"' gates/flows.py` — `decision_queue` (gates/flows.py:381), `sessions` (gates/flows.py:430), and `ledger` (`_ledger_issue()`, gates/flows.py:195-200) all build it as plain Python `int`; no type mismatch found.

Check 2 — whether the checkout-scope gap is observable in this checkout right now.
canonical: `python3 spawn.py flows --json -C .`, this session
derived: `python3 spawn.py flows --json -C .` — `decision_queue` carried two `issue: 1712` entries next to an empty `sessions` array and an empty `ledger` array; this is the documented symptom class, reproduced live, and the planned filter (intersection against an empty set) would empty this exact queue, matching the proposal's stated acceptance line — not a gap in the planned fix.

Check 3 — record-claim-guard.sh's path scope against what actually landed.
canonical: on-the-record/hooks/record-claim-guard.sh:81 (read in full this session)
derived: `sed -n '81p' on-the-record/hooks/record-claim-guard.sh` — the scope test `re.search(r"(^|/)docs/issue-[^/]+/reports/", n)` matches `docs/issue-1718/reports/implementation/survey.md` but not the sibling `docs/issue-1718/proposals/` path.
derived: `RCG_PAYLOAD=<json> RCG_GATES_DIR=<repo>/gates python3 -c "$GUARD"` run twice against the real committed proposal content, once addressed at its real path and once addressed at a `reports/`-scoped path with identical content — exit code 0 both times, no allow/deny divergence on this content.

No reproduction cleared the bar. Not filing a finding.
