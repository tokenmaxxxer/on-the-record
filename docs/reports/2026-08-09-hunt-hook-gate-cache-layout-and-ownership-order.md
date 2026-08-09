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
