---
code_under_review:
  - spawn.py
  - gates/test_consult_gate_lib_env.py
type: bugfix
breaking: false
verdict: pass
loop_state: landed
---

canonical: acceptance: `python3 -m pytest gates/test_consult_gate_lib_env.py -v` -- result: 2 passed, 0 failed (fenced output below)

## What was done

canonical: spawn.py:4471-4506 (`_consult_cmd_and_env`)

Extracted `_consult_cmd_and_env(role, spec, cwd)` from `consult_cmd()`
(spawn.py:4537) as a build-then-return helper mirroring `spawn_cmd()`'s
shape (spawn.py:4344-4413): it builds argv/env/settings-path and never
calls `subprocess.run` itself. Inside the helper, `CLAUDE_PLUGIN_ROOT_CORE`
is injected from `core_plugin_dirs()` (spawn.py:4505-4506), the same
one-line fix `spawn_cmd()` carries at spawn.py:4406-4408 since issue #182.
`consult_cmd()` now calls the helper once (spawn.py:4537) and loops
`subprocess.run` over the returned `(cmd, env)` exactly as before.

Added `gates/test_consult_gate_lib_env.py`: a hermetic test (no live
`claude` process) that monkeypatches `spawn.core_plugin_dirs`/
`spawn.plugin_dirs`/`spawn.role_settings` to point at a `tmp_path`
fixture core carrying `hooks/lib/gate-lib.sh`, calls
`_consult_cmd_and_env()` directly, and asserts the returned env resolves
the gate-lib path via `resolve_core()` (reused from
`gates/test_env_resolve.py`), plus a companion case asserting the var is
omitted when `core_plugin_dirs()` returns no `core` entry.

canonical: acceptance: `python3 -m pytest gates/test_consult_gate_lib_env.py -v` -- result:
```
gates/test_consult_gate_lib_env.py::test_consult_env_injects_core_plugin_root PASSED [ 50%]
gates/test_consult_gate_lib_env.py::test_consult_env_missing_core_entry_omits_var PASSED [100%]
2 passed in 0.03s
```

## Delivery proof (executed-live)

canonical: acceptance: `python3 -c "import spawn; spawn.consult_cmd('requirements-engineering', <question>, issue=1141)"` -- result: verdict returned, see fenced output below

Ran the exact failed question from the raw-failure file found at
`/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/docs/reports/consult-raw-failures/2026-08-13T022231.0588190000-1.txt`
(that file lives in a separate checkout under
`~/.claude/plugins/marketplaces/tokenmaxxxer/`, not in this repo tree;
the role that produced it, `requirements-engineering`, was identified
from the matching `docs/reports/consult-log.md` entry in that same
checkout, timestamp `2026-08-13T02:22:31.058819+00:00`) through
`consult_cmd()` on this branch's fixed code. It returned a parsed
verdict:

```
VERDICT: {'answer': "Intended in principle (delivered != exempt from re-validation) but likely a defect in the check's current tuning: flagging R002-R004 as 'drifted' because no OPEN issue/PR cites them conflates 'needs periodic re-affirmation' with 'needs a permanently open tracking item'. The fix is to require a recent re-affirmation event (closed or open) within some staleness window, not a live open citation at all times.", 'confidence': 'medium', 'caveats': [...]}
```

canonical: docs/issue-1141/reports/consult-log.md -- trace line below, outcome starts with "ok"

Trace line for this run:
```
- 2026-08-13T02:53:34.856292+00:00 | role=requirements-engineering | issue=1141 | question="The watchdog's requirement-drift check flags requirements marked [enforced] in docs/specs/requirement-digest.md (R002-R004, delivered and gate-enforced, no open work needed) as drifted because no OPEN" | outcome="ok: Intended in principle ..."
```

## Why

Root cause of the consult-failure family (docs/issue-1141/proposals/consult-core-plugin-root-injection.md,
## Request): `consult_cmd()`'s subprocess env never carried
`CLAUDE_PLUGIN_ROOT_CORE`, so `terse.sh`'s relative-path fallback missed
under a consult session's working directory and the hook hard-blocked
with a bash "no such file" error, which then got captured as "model
output" -- no verdict JSON possible. Fix reuses `core_plugin_dirs()`
(single source of truth already proven correct for `spawn_cmd()` under
issue #182) rather than adding a second resolution strategy.

## Upstream

Based on: docs/issue-1141/proposals/consult-core-plugin-root-injection.md

## What did not work

None.

## Open findings

None outstanding at time of writing.

## closed_checks

canonical: acceptance: `python3 -m pytest gates/test_consult_gate_lib_env.py -v` -- result: pass (fenced output above)

- hermetic env-injection test (gates/test_consult_gate_lib_env.py) -- code_sha: a3b1e5c
- executed-live delivery proof (issue acceptance check 2) -- canonical: docs/issue-1141/reports/consult-log.md trace line pasted above.

## Out of scope

- `terse.sh`'s own source guard should loud-skip rather than hard-block
  on env breakage (issue requirement 2) -- lives in `tokenmaxxxer-core`,
  a separate repo outside this repo's write set. Not filed as an issue
  from this session (role-handoff contract: a role session does not
  spawn or file cross-scope work on its own initiative); flagged here as
  the needed follow-up per the proposal's `## Out of scope`.

## Next steps

None -- record is landed; remaining follow-up is the out-of-scope
cross-repo item noted above, for a human/orchestrator to file against
`tokenmaxxxer-core`.

## Resolution path

N/A -- no open finding.
