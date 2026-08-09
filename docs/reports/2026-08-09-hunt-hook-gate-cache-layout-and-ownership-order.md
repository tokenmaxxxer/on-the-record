---
proposal: docs/issue-556/proposals/2026-08-09-hook-gate-cache-layout-and-ownership-order.md
---

# Hunt record — hook-gate-cache-layout-and-ownership-order

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — when `gates_dir` fails to resolve (the exact packaging scenario this proposal is fixing), both hooks' `sys.path.insert(0, os.environ["<X>_GATES_DIR"])` inserts an empty string, which makes Python search the process's own `cwd` for the gate module; a same-named file planted at the repo's cwd (`role_spec_shape.py` / `record_lint.py`) is imported instead of the real gate — silently, with no `ImportError` — so the proposed `try/except ImportError: deny()` guard around the gates import never fires and a bad write to an owned path is allowed through.
Kind: composition
Seed: docs/issue-556/proposals/2026-08-09-hook-gate-cache-layout-and-ownership-order.md, docs/issue-556/reports/implementation/survey.md (commit 74e550b)
cap_seconds: 60
tier: default (docs-only, small diff)
diff_stat_lines: 2 files changed (proposal + survey), docs-only
started_at: 2026-08-09T00:00:00Z
ended_at: 2026-08-09T00:20:00Z

### Reproduce

```
D=$TMPDIR/bypassdemo
mkdir -p "$D/fakehooks"
cp on-the-record/hooks/role-spec-reference-guard.sh "$D/fakehooks/"
cd "$D"

# attacker-controlled file shadowing the real gate module, sitting in cwd
cat > role_spec_shape.py <<'PY'
def record_path_role(p):
    return "execution-observation"   # always claim "owned"
def reference_resolution_check(content, root):
    return []                        # always claim "no violation"
PY

# payload: a Write to an owned verification-family record path, whose
# content contains a backtick-quoted path that does NOT exist -- a real
# gate would deny this.
python3 - <<'PY'
import json, os
D = os.getcwd()
obj = {"tool_name": "Write",
       "tool_input": {"file_path": "docs/issue-1/reports/execution-observation.md",
                       "content": "Result references `nonexistent/made-up-path.md` which does not exist anywhere."},
       "cwd": D}
open("payload.json", "w").write(json.dumps(obj))
PY

cat payload.json | bash fakehooks/role-spec-reference-guard.sh
echo "EXIT CODE: $?"
```

### Observed

`cd "$script_dir/../../gates"` fails (no `gates/` two levels up from the
fake `hooks/` dir — reproducing the deployed-cache layout this proposal
targets), so `gates_dir=""`. `RSRG_GATES_DIR` is then set to the empty
string and `sys.path.insert(0, os.environ["RSRG_GATES_DIR"])` inserts `""`
into `sys.path`, which Python resolves as the process's cwd. `import
role_spec_shape` succeeds — against the attacker's shadow file in cwd, not
the real gate — with no exception raised. The hook printed no error and
exited:

```
EXIT CODE: 0
```

A write carrying an orphaned/bogus backtick reference to a genuinely owned
verification-family record path was silently allowed.

### Expected

Either the write should have been denied (fail-closed: the real gate
module was unreachable, so the check that should have caught the orphaned
reference never ran), or the import should have raised `ImportError` so a
`try/except ImportError: deny()` guard (as the proposal specifies for the
post-fix design) could catch it. Instead, because `sys.path` was seeded
with an empty-string entry from the same "leave gates_dir unset" fallback
the proposal calls for, the import silently resolves against
attacker-influenced cwd content and returns a fabricated "no violation"
answer. The proposal's "if neither [gates path] exists, leave it unset"
plan does not address that an *unset/empty* `RSRG_GATES_DIR`/`RCG_GATES_DIR`
still gets threaded into `sys.path.insert(0, ...)` as `""`, reintroducing
exactly the kind of accidental-pass-through the ownership-reordering work
is meant to close off — but for the gates import itself, not the ownership
check. The fix needs to treat an empty/unset gates dir as an explicit
"module unavailable" condition (e.g. skip the `sys.path.insert` and let
`import` raise `ModuleNotFoundError` cleanly, or explicitly `deny()`
before attempting import) rather than passing `""` through to
`sys.path.insert`.

## before-landing — stance 1: assume this change and another plugin's rule cancel each other — find the pair

Verdict: FINDING — the new `../gates` (packaged on-the-record/gates/) resolution priority makes record-claim-guard.sh / role-spec-reference-guard.sh silently read a copy of gates/record_lint.py that diverges from repo-root gates/record_lint.py once someone edits the root source without also updating the packaged copy; no hook or test detects the drift, so the two guard-family hooks enforce stale/inconsistent rule text against the same repo tree.
Kind: composition
Seed: on-the-record/hooks/record-claim-guard.sh, on-the-record/hooks/role-spec-reference-guard.sh gates_dir resolution (../gates before ../../gates); on-the-record/gates/*.py packaged copies vs repo-root gates/*.py
cap_seconds: 180
tier: size:large
diff_stat_lines: 1943 insertions across 8 files (commit cc9feff)
started_at: 2026-08-09T11:48:39+09:00
ended_at: 2026-08-09T12:03:00+09:00

### Reproduce
```
# copy of the repo tree in a scratch dir, then edit ONLY root gates/record_lint.py:
sed -i "s/이유가 없다/FIXED-MESSAGE-marker/" gates/record_lint.py
diff gates/record_lint.py on-the-record/gates/record_lint.py   # now differ

# feed record-claim-guard.sh a payload that trips unverifiable_reason_check
# (an owned docs/issue-NNN/reports/implementation.md write, body "unverifiable:\n")
bash on-the-record/hooks/record-claim-guard.sh < payload.json
```

### Observed
```
Exit code 2
record-claim-guard: `unverifiable:` 줄에 이유가 없다 (issue #310) — ...
```
The guard still emits the *unedited* Korean message string — it resolved
gates_dir to `../gates` (on-the-record/gates/record_lint.py), never
touching the edited root-level `gates/record_lint.py` at all, even though
the guard's own header comment says it calls "into gates/record_lint.py's
functions" without distinguishing which copy is authoritative.

### Expected
Either a single source of truth (no second copy able to diverge) or some
mechanism (test, sync check, or doc) that fails loudly when
on-the-record/gates/*.py and repo-root gates/*.py disagree. Currently
nothing detects or prevents the drift; test_hook_cache_layout.py only
checks import success and ownership-order, not copy parity — so a fix
landed in the root `gates/` tree (the place every other hook, e.g.
impact-guard.sh's `os.path.join(checkout, "gates")`, still reads from)
silently fails to reach record-claim-guard.sh / role-spec-reference-guard.sh
once the packaged copy exists and is preferred.

### Disposition
Not a blocking regression: the proposal's `## Out of scope` section
already names this exact tradeoff ("A general drift-prevention mechanism
keeping the packaged `gates/` copies in sync with the repo-root
originals automatically ... noted as a follow-up, not built here"). The
hunt confirms the drift is real and currently silent, which sharpens why
that follow-up matters — filed as a candidate for a future issue
(sync-check CI/test), not addressed in this branch.
