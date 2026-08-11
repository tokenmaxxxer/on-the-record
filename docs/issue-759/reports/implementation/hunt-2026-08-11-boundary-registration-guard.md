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

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — a rename/copy of an existing tracked file into a gates/*.py or on-the-record/hooks/*.sh path is never classified as git diff --cached --name-status status "A" (it reports as "R100"/"R<pct>" instead), so the guard's status == "A" filter never treats it as a target, and a genuinely new, unregistered gate module can land through two ordinary commit invocations (rename-only, then edit) without the hook ever returning non-zero.
Kind: silent-failure
Seed: on-the-record/hooks/gate-registration-guard.sh (lines 81-92: if status == "A": added.append(path) -- no handling of an "R100"/"C100"/"R<NN>" row, whose last tab-separated field is the destination path)
cap_seconds: 180
tier: size:200+
diff_stat_lines: ~439
started_at: 2026-08-11T06:04:53Z
ended_at: 2026-08-11T06:16:00Z

### Reproduce
Scratch repo only, not the real repo's git state. run_test2.sh (written
to a tmp dir, quoted here in full so the exact byte-for-byte commands are
reproducible):
```bash
D=$(mktemp -d)
GUARD=on-the-record/hooks/gate-registration-guard.sh   # this repo's copy
rm -rf "$D/repo2"; mkdir -p "$D/repo2"; cd "$D/repo2"
git init -q
git config user.email t@example.com; git config user.name t
mkdir -p gates on-the-record/hooks docs/specs
printf "| mechanism | verdict | reason |\n|---|---|---|\n" > docs/specs/enforcement-boundary.md
printf "| mechanism | classification | verdict |\n|---|---|---|\n" > docs/specs/generated-paths.md
printf 'def helper():\n    return 1\n' > gates/dead_stub.py   # some pre-existing, unrelated tracked file
git add -A
git -c core.hooksPath=/dev/null commit -q -m seed

# STEP 1: pure rename of the unrelated file into a brand-new gate module path
git mv gates/dead_stub.py gates/new_gate.py
git diff --cached --name-status
# -> R100  gates/dead_stub.py  gates/new_gate.py   (NOT "A")

python3 -c 'import json;print(json.dumps({"tool_name":"Bash","cwd":".","tool_input":{"command":"g""it com""mit -m step1"}}))' \
  | ORCHESTRATE_OFF= bash "$GUARD"; echo "guard exit=$?"
git -c core.hooksPath=/dev/null commit -q -m step1

# STEP 2: now freely edit the never-registered module -- it's tracked, so this is plain "M"
cat >> gates/new_gate.py <<'PYEOF'

def new_gate_check(payload):
    if not payload:
        return False
    return True
PYEOF
git add -A
git diff --cached --name-status   # -> M  gates/new_gate.py
python3 -c 'import json;print(json.dumps({"tool_name":"Bash","cwd":".","tool_input":{"command":"g""it com""mit -m step2"}}))' \
  | ORCHESTRATE_OFF= bash "$GUARD"; echo "guard exit=$?"

grep -c "new_gate" docs/specs/enforcement-boundary.md || echo "0 rows found"
```

### Observed
Both invocations of the guard print nothing and exit 0. Concretely:
```
R100    gates/dead_stub.py     gates/new_gate.py
guard exit=0
M       gates/new_gate.py
guard exit=0
0 rows found
```
gates/new_gate.py (scratch repo only, never a path in this real repo)
now exists on that branch with a real gate-shaped function
(new_gate_check), reachable through two ordinary commit invocations
that would fire under hooks.json's real PreToolUse Bash matcher, and
it has zero rows in docs/specs/enforcement-boundary.md naming it --
i.e. it is exactly the "newly-added, unregistered gate module" issue
#759 says this hook exists to catch, and it landed without the hook
ever returning non-zero or emitting a denial message. This is the
guard's own explicit "editing an already-registered module's
internals... is untouched" design (comment lines 21-23) misfiring on
a module that was never registered in the first place -- the design
assumes "already tracked" implies "already registered", which a
rename-then-edit sequence breaks.

### Expected
The guard should treat a rename/copy whose destination basename is a
target path (gates/*.py sans test_*/__init__, on-the-record/hooks/*.sh,
.github/workflows/*.yml) the same as an "A" row for registration-check
purposes -- i.e. also collect the destination path from any
status.startswith(("R", "C")) line (using parts[-1] as it already
does for path, since a git diff --name-status R/C row is
<status>\t<old>\t<new>) -- so gates/new_gate.py: no row in
docs/specs/enforcement-boundary.md is reported and the commit is
denied at STEP 1, instead of silently succeeding at both steps.
