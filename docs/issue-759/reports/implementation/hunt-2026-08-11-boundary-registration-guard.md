---
proposal: docs/issue-759/proposals/2026-08-11-boundary-registration-guard.md
---

# Hunt record — boundary-registration-guard

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list.

Verdict: FINDING — the frozen write set never sets (and no listed test checks) the executable bit on the new `on-the-record/hooks/gate-registration-guard.sh`, so a green `pytest` run gives false confidence that the guard actually fires from `hooks.json`
Kind: silent-failure
Seed: docs/issue-759/proposals/2026-08-11-boundary-registration-guard.md, docs/issue-759/reports/implementation/survey.md
cap_seconds: 120
tier: default
diff_stat_lines: proposal+survey+scout-brief, ~21-200 range
started_at: 2026-08-11T14:40:00
ended_at: 2026-08-11T15:02:00

### Reproduce

```
# 1. hooks.json invokes every hook by its raw path, no interpreter prefix:
python3 -c "
import json
d = json.load(open('on-the-record/hooks/hooks.json'))
print(d['hooks']['PreToolUse'][2]['hooks'][4])
"
# -> {'type': 'command', 'command': '${CLAUDE_PLUGIN_ROOT}/hooks/spec-index-preflight.sh'}
# i.e. the literal path is executed directly, not run as `bash <path>`.

# 2. a file created the way the Write tool creates one (no chmod) is not
#    executable, and running it the way hooks.json's raw command does fails:
cd /tmp && python3 -c "
open('demo2.sh','w').write('#!/usr/bin/env bash\necho ran\n')
"
ls -la demo2.sh                 # -rw-r--r--  (no +x)
./demo2.sh; echo "direct exit=$?"    # -> permission denied, direct exit=126

# 3. but the sibling test file shape the proposal is told to mirror
#    (on-the-record/hooks/test_spec_index_preflight.py,
#    on-the-record/hooks/test_role_axis_completeness_guard.py, and by
#    extension the proposal's own new
#    on-the-record/hooks/test_gate_registration_guard.py) invokes the
#    script as `subprocess.run(["bash", str(script)], ...)`, which
#    succeeds regardless of the +x bit:
python3 -c "
import subprocess
r = subprocess.run(['bash', 'demo2.sh'], capture_output=True, text=True)
print('bash-prefixed exit=', r.returncode, 'stdout=', r.stdout.strip())
"
# -> bash-prefixed exit= 0 stdout= ran
```

### Observed

`git ls-tree HEAD` shows every existing hook script checked in at mode
`100755`:
```
100755 blob eb0d5a0... on-the-record/hooks/record-claim-shape-directive.sh
100755 blob 9e365c6... on-the-record/hooks/role-axis-completeness-guard.sh
100755 blob 476c6e2... on-the-record/hooks/spec-index-preflight.sh
```
Neither the proposal file nor the survey mentions `chmod`/`+x`/`755`
anywhere (`grep -in "chmod\|execut\|+x\|755"` on both returns nothing),
even though the survey's own cited precedent — issue #459, the closer of
the two named prior-art hooks — hit exactly this gap: its merge commit
(`9be65e8`) states verbatim "Before-landing hunt caught missing execute
bits on both new scripts (would have made hooks.json's direct invocation
fail with exit 126); fixed and re-confirmed via the hunter's own repro."
That fix is not itself a pytest assertion anywhere in the repo — no test
file greps for `os.access(..., os.X_OK)` or `S_IXUSR` on a hook script
path (checked `on-the-record/hooks/*.py`, `gates/*.py`, `tests/*.py`).
Every sibling test — including the shape the proposal is explicitly told
to mirror step-for-step — drives the script through `subprocess.run(["bash",
str(script)])`, which never depends on the file's own execute permission.

### Expected

The write set (or the "What will be done" steps) should name the
executable-bit requirement explicitly for `gate-registration-guard.sh`
— e.g. an explicit `chmod +x` / `git add --chmod=+x` step or a new
assertion added to `test_gate_registration_guard.py` that checks
`os.access(SCRIPT, os.X_OK)` — so `python3 -m pytest gates/ tests/
on-the-record/hooks/test_gate_registration_guard.py -q` reporting 0
failures actually implies the guard fires when `hooks.json` invokes it
directly, instead of silently no-op'ing (exit 126, permission denied)
the first time a real `git commit` triggers it, the same gap issue #459
already hit once and that only a before-landing hunt (not the pytest
suite) caught.
