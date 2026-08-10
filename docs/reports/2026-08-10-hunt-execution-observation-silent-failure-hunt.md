
## after-proposal — stance 0: assume the gate/process just touched is bypassable — find the bypass

Verdict: FINDING — the proposal's "evidenced absence" / "fenced fixture-drive output" requirement has no mechanical enforcement anywhere in the repo, so an executor can hand-type a plausible-looking fenced block (or invoke step 4's "legitimately unreachable" escape hatch) without ever building/driving a fixture, and the document will still satisfy every item in "How you'll know it worked" (table row present, citation adjacent, independence statement present, loop_state terminal) — all of which are checkable by shape/grep, not by confirming a real fixture drive occurred.
Kind: silent-failure
Seed: docs/issue-628/proposals/2026-08-10-execution-observation-silent-failure-hunt.md, docs/issue-628/reports/execution-observation/survey.md
cap_seconds: 120
tier: default
diff_stat_lines: 2 files added (docs-only)
started_at: 2026-08-10T13:56:41+09:00
ended_at: 2026-08-10T13:58:30+09:00

### Reproduce
```
grep -rln "fixture-drive\|fixture drive" on-the-record/hooks/ on-the-record/gates/ gates/
# -> no matches: no hook/gate inspects fixture-drive output for authenticity

# Compare to the parallel case the repo DOES enforce mechanically:
sed -n '1,25p' on-the-record/hooks/role-test-claim-guard.sh
# -> a Stop hook structurally cross-checks pasted pytest output against
#    the claim text (skip-vs-pass conflation, hand-typed vs derived counts)
#    for TEST-RUN claims specifically. No sibling exists for fixture-drive claims.
```

### Observed
The proposal's constraints text ("Absence of a finding must be evidenced (fixture built, entrypoint invoked, what fired) — never asserted as 'looks fine'") and step 4's "legitimately unreachable ... record the concrete blocker" clause are both self-attested prose with zero automated check anywhere in `on-the-record/hooks/`, `on-the-record/gates/`, or `gates/`. The "How you'll know it worked" completion criteria (table row present, citation adjacent, independence statement present, loop_state terminal) are all satisfiable by the document's textual shape alone.

### Expected
Given the repo already has precedent for exactly this failure mode (role-test-claim-guard.sh exists specifically because a Stop hook "cannot re-run pytest itself" so it structurally cross-checks the claim), the fixture-drive claims this proposal licenses should have an equivalent structural check (e.g. requiring the fenced block to contain markers only a real invocation would produce, or requiring a session transcript reference) — otherwise the phase-2 hunt can silently degrade into "asserted as fine" for every hard-to-reach surface via the "legitimately unreachable" clause, exactly the failure mode issue #628 is trying to close.
