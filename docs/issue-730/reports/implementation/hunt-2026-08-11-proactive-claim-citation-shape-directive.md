---
proposal: docs/issue-730/proposals/2026-08-11-proactive-claim-citation-shape-directive.md
---

# Hunt record — proactive-claim-citation-shape-directive

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — record_lint.orphaned_path_reference_check's path regex is a directory allow-list (`src|test|tests|docs|gates|on-the-record`) that omits real top-level repo directories (`bench/`, `ledger/`, `roles/`, `scripts/`, `.claude-plugin/`), so a fabricated/nonexistent path cited under any of those prefixes never gets matched, and record-claim-guard.sh's #330 check silently lets the orphaned reference through.
Kind: silent-failure
Seed: on-the-record/hooks/record-claim-guard.sh (existing PreToolUse gate this proposal's planned UserPromptSubmit hook is meant to proactively warn about) + on-the-record/gates/record_lint.py's orphaned_path_reference_check
cap_seconds: 180
tier: size:>200-lines
diff_stat_lines: 238 (docs/issue-730/proposals/2026-08-11-proactive-claim-citation-shape-directive.md +117, docs/issue-730/reports/implementation/survey.md +121)
started_at: 2026-08-11T04:12:57Z
ended_at: 2026-08-11T04:20:00Z

### Reproduce
```
cd /Users/jk/.tokenmaxxxer/work/on-the-record-issue-730-implementation

# Control: orphaned reference under an allow-listed prefix (docs/) — denied as expected.
PAYLOAD='{"tool_name":"Write","cwd":"'"$PWD"'","tool_input":{"file_path":"docs/issue-730/reports/implementation/fake-test-record2.md","content":"See `docs/totally-fake-nonexistent-file.md` for the details.\n"}}'
RCG_PAYLOAD="$PAYLOAD" bash on-the-record/hooks/record-claim-guard.sh <<< "$PAYLOAD"; echo "exit: $?"

# Same fabricated-path pattern, only the prefix changes to a real repo dir the regex doesn't cover.
PAYLOAD2='{"tool_name":"Write","cwd":"'"$PWD"'","tool_input":{"file_path":"docs/issue-730/reports/implementation/fake-test-record.md","content":"See `scripts/totally-fake-nonexistent-file.sh` for the script that does this.\n"}}'
RCG_PAYLOAD="$PAYLOAD2" bash on-the-record/hooks/record-claim-guard.sh <<< "$PAYLOAD2"; echo "exit: $?"
```

### Observed
Control (docs/ prefix) is denied, exit 2:
```
record-claim-guard: 레코드가 존재하지 않는 경로를 참조한다 (issue #330): `docs/totally-fake-nonexistent-file.md` — 리치(reach)가 끊긴 참조다.
exit: 2
```
Test (scripts/ prefix, otherwise byte-identical fabrication pattern) is allowed through silently, exit 0, no stderr at all:
```
exit: 0
```
Confirmed at the regex level too — `record_lint._PATH_REF` simply never captures these paths:
```
python3 -c "
import re
_PATH_REF = re.compile(r'\`((?:src|test|tests|docs|gates|on-the-record)/[^\`\s]+)\`')
print(_PATH_REF.findall('See \`scripts/fake.sh\` and \`bench/fake.py\` and \`roles/fake.md\` and \`ledger/fake.json\` here.'))
"
# -> []
```
`scripts/`, `bench/`, `roles/`, `ledger/`, `.claude-plugin/` are all real, populated top-level directories in this repo (verified with `ls scripts bench roles`), so a fabricated path under any of them is a legitimate, on-topic orphaned reference a record author could plausibly type — it is not an edge case outside the check's intended domain.

### Expected
A role writing a record under `docs/issue-*/reports/**` that cites a nonexistent path in backticks should be denied by the same #330 orphaned-path-reference rule regardless of which real top-level directory the fabricated path sits under — the check's own docstring says it should catch "a backtick-quoted relative path that resolves nowhere in the working tree," with no stated prefix restriction. Instead the directory allow-list means the gate's coverage silently depends on which prefix the author happens to type, and this gap is invisible to record-claim-guard.sh's caller (exit 0, same as a genuinely clean write) — exactly the kind of silent-failure this hunt is scoped to. This matters for issue-730's phase-2 build: the planned proactive directive text can only ever restate what the gate *does* check, so a hole in the gate's own path-prefix coverage is not something directive text at the UserPromptSubmit layer can close.

## before-landing — stance 1: assume this change and another plugin's rule cancel each other — find the pair

Verdict: NO FINDING
Seed: on-the-record/hooks/record-claim-shape-directive.sh (new UserPromptSubmit hook, ~137-line diff across record-claim-shape-directive.sh, hooks.json, test_record_claim_guard.py); full on-the-record/hooks/hooks.json UserPromptSubmit/PreToolUse/Stop arrays and referenced scripts (directive.sh, record-claim-guard.sh, role-spec-reference-guard.sh, claim-scan-preflight.sh, product-capture-stopgate.sh, role-test-claim-guard.sh, session-role-bind.sh)
cap_seconds: 120
tier: size:21-200-lines
diff_stat_lines: ~137
started_at: 2026-08-11T04:19:25Z
ended_at: 2026-08-11T04:22:05Z

Checked and ruled out, with reproductions:

1. UserPromptSubmit array (directive.sh + record-claim-shape-directive.sh): the
   two are gated on opposite `CLAUDE_ROLE` polarity (directive.sh:
   `[ -z "${CLAUDE_ROLE:-}" ]`, orchestrator-only; record-claim-shape-directive.sh:
   `[ -n "${CLAUDE_ROLE:-}" ]`, role-only), so they are strictly mutually
   exclusive per session — never both fire, never both stay silent. Ran both
   directly with `CLAUDE_ROLE=` unset and with `CLAUDE_ROLE=implementation`:
   exactly one of the pair produced output in each case (directive.sh: 7636
   bytes / shape-directive: 0 bytes when unset; inverse when set), confirming
   no stdout collision or suppression between them.
2. Kill switches: `ORCHESTRATE_OFF` case pattern
   (`""|0|false|no|off` → pass-through, else → off) is byte-identical across
   record-claim-guard.sh, directive.sh, and record-claim-shape-directive.sh.
   Ran both record-claim-shape-directive.sh and record-claim-guard.sh with
   `ORCHESTRATE_OFF=1` and `CLAUDE_ROLE=implementation`: both exit 0 silently
   (shape-directive prints nothing, guard does not deny a violating write) —
   they go out of sync together, not apart.
3. Rule content/order: the new hook's CHECKS list
   (unverifiable_reason_check, checked_claim_reason_check,
   bare_count_claim_check, orphaned_path_reference_check) matches both
   record-claim-guard.sh's call order and gates/record_lint.py's
   `lint_record()` call order exactly — no drift in the set or the order
   between the proactive directive and the enforcing gate.
4. No other UserPromptSubmit/PreToolUse/Stop hook prints or parses the same
   claim-citation vocabulary: `grep -rln "unverifiable\|derived:\|checked:.*result\|bare.*count\|orphaned"` across on-the-record/hooks/*.sh returns only
   record-claim-shape-directive.sh and record-claim-guard.sh. claim-scan-preflight.sh
   checks a disjoint vocabulary (PR-body "reproduced/verified" claims vs.
   Repro:/Verify: markers, not report-record `unverifiable:`/`derived:`/count
   claims) and a disjoint path scope (gh pr create/edit body, not
   docs/issue-*/reports/** writes). role-spec-reference-guard.sh and
   role-test-claim-guard.sh are also disjoint in scope/vocabulary.
   product-capture-stopgate.sh is orchestrator-only (`CLAUDE_ROLE` unset),
   so it can never see a role session's transcript entries.

No pair found whose rule/behavior cancels, suppresses, or contradicts this
hook's effect within the 120s budget. Went a little over (~160s wall) to
finish the empirical stdout/kill-switch checks rather than stop mid-run.
