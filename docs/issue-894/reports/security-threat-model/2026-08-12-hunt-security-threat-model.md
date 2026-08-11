---
proposal: docs/issue-894/proposals/security-threat-model.md
---

# Hunt record — security-threat-model

## after-proposal — stance: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — approval-gate.sh and record_lint.py both key on the literal path
docs/issue-894/reports/<role>.md; the survey file this proposal introduced,
docs/issue-894/reports/security-threat-model/survey.md, lives one directory deeper and matches
neither gate's pattern, so it can be edited post-proposal to carry a full severity-ranked STRIDE
table (phase-2-shaped content) with zero gating — defeating the phase-1/phase-2 boundary the
proposal's own "Constraints" section claims to hold ("Phase-2 record write ... waits for the
Approve gate ... this proposal and the survey are the only writes this turn").
Kind: composition
Seed: docs/issue-894/proposals/security-threat-model.md, docs/issue-894/reports/security-threat-model/survey.md, on-the-record/hooks/approval-gate.sh, gates/gates.py (RECORD_PATH regex)
cap_seconds: 120
tier: default
diff_stat_lines: 2 files (proposal + survey), ~180 lines total
started_at: 2026-08-12T05:12:51+09:00
ended_at: 2026-08-12T05:20:00+09:00

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-894-security-threat-model
export CLAUDE_ROLE=security-threat-model   # branch is issue-894/security-threat-model
payload='{"tool_name":"Edit","tool_input":{"file_path":"docs/issue-894/reports/security-threat-model/survey.md"},"session_id":"testsess","cwd":"'"$PWD"'"}'
echo "$payload" | ORCHESTRATE_OFF=0 on-the-record/hooks/approval-gate.sh
echo "EXIT=$?"
```
Also: `gates.RECORD_PATH = re.compile(r"^docs/issue-[^/]+/reports/([^/]+)\.md$")` — this never
matches a path with a `/` under `reports/`, so `gates/record_lint.py` / `record-claim-guard.sh`
never inspects survey.md's content either (bare-count-claim, canonical-tag, outcome-claim checks
all silently skip it).

### Observed
`EXIT=0` — the Edit is allowed unconditionally, no approval-comment check performed, even though
the write targets an issue-894/security-threat-model-role file that is functionally a phase-2
threat-model draft.

### Expected
Any write under docs/issue-894/reports/security-threat-model/** that contains phase-2-shaped
verdict/severity content should require the same Approve-gate check as
docs/issue-894/reports/security-threat-model.md itself — or record_lint.py's checks should apply
to it — so smuggling the STRIDE table one directory level down cannot silently skip both gates.
