---
proposal: docs/issue-731/proposals/2026-08-11-proactive-call-shape-and-report-framing.md
---

# Hunt record — proactive-call-shape-and-report-framing

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: NO FINDING
Seed: docs/issue-731/proposals/2026-08-11-proactive-call-shape-and-report-framing.md, docs/issue-731/reports/implementation/survey.md (~143 lines, docs-only)
cap_seconds: 60
tier: default (docs-only diff)
diff_stat_lines: ~143
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:05:00Z

Checked wiring: both `call-shape-guard.sh` (PreToolUse, matcher
`Write|Edit|MultiEdit`) and `report-framing-check.sh` (Stop) are
registered in `on-the-record/hooks/hooks.json`, which is picked up by
the plugin manifest convention (no separate settings.json override
found repo-root). Ran a live repro against `call-shape-guard.sh`:
seeded a repo with `a.py` calling `subprocess.run(["git","log","-X","foo"])`,
committed it, then fed the hook a synthetic PreToolUse `Write` payload
for `b.py` calling `subprocess.run(["git","log","--method","bar"])` (same
`(argv[0], argv[1])`, different flag shape). The hook denied with exit 2
and the expected `flag 모양이 다르다` message — the check fires as the
proposal's target prose would describe it, not dead code. Did not find
a condition (kill-switch aside, which is already documented in the
hook's own header) under which the hook silently no-ops while still
being described as enforced. No reproduction of a bypass found within
cap.

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — call-shape-guard.sh's subprocess_call_shape_divergence check only recognizes an `ast.List` literal as the first positional arg to subprocess.run/check_output/check_call/Popen; the same divergent call written with a tuple literal (functionally identical at runtime) is silently invisible to the guard, and the new run.md text ("위 (1) subprocess_call_shape_divergence 는 이걸 사후에 기계로 잡을 뿐이다") asserts machine enforcement with no caveat about this literal-shape restriction.
Kind: silent-failure
Seed: on-the-record/commands/run.md (lines ~541-557, new "flag 모양 일관성 규칙(#726 row 7)" paragraph); gates/test_call_shape_and_report_framing_docs.py
cap_seconds: 120
tier: default (size:21-200-lines bucket)
diff_stat_lines: doc-only change to run.md + new test file (per dispatcher description)
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:02:00Z

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-731-implementation
python3 - <<'PY'
import json, subprocess, os
repo_root = os.getcwd()
hook = os.path.join(repo_root, "on-the-record/hooks/call-shape-guard.sh")

payload_list = json.dumps({"tool_name": "Write", "cwd": repo_root, "tool_input": {
    "file_path": os.path.join(repo_root, "gates/_csg_repro_list.py"),
    "content": "import subprocess\nsubprocess.run(['gh', 'api', 'repos/x/y', '-X', 'GET'])\n"}})
r1 = subprocess.run(["bash", hook], input=payload_list, capture_output=True, text=True)
print("LIST literal rc:", r1.returncode, r1.stderr.strip())

payload_tuple = json.dumps({"tool_name": "Write", "cwd": repo_root, "tool_input": {
    "file_path": os.path.join(repo_root, "gates/_csg_repro_tuple.py"),
    "content": "import subprocess\nsubprocess.run(('gh', 'api', 'repos/x/y', '-X', 'GET'))\n"}})
r2 = subprocess.run(["bash", hook], input=payload_tuple, capture_output=True, text=True)
print("TUPLE literal rc:", r2.returncode, r2.stderr.strip())
PY
```

### Observed
```
LIST literal rc: 2 call-shape-guard: 명령 'gh api' 의 호출부들이 flag 모양이 다르다 (...) — ... (issue #419).
TUPLE literal rc: 0
```
The tuple-literal write, which diverges from the existing `-f`-style `gh api` call at gates/closure_sweep.py:307-308 exactly the same way the list-literal write does, is silently permitted.

### Expected
Either the guard should recognize tuple literals (and other equivalent call shapes) alongside list literals, or the doc's claim that check (1) mechanically catches flag-shape divergence should be qualified to note it only fires for list-literal argv construction — otherwise the doc overclaims coverage the gate does not actually provide.
