---
subject: issue-558
kind: survey
---

## Scope

Pure bugfix / hardening on already-existing `spawn.py` refusal-classification
and permission-provisioning machinery — no new design decision opens beyond
which concrete command shapes to pre-allow, which the issue body and its
run evidence already name (venv/pip install, running committed workspace
scripts). Scouting is skipped per the scout-directive's second skip
condition: the spec leaves no product-facing design decision open.

## Current state

**1. Refused command text is dropped at classification time.**

`_classify_refusal_text(text)` (spawn.py:2107-2140) turns a harness
`tool_result` denial message into an event via
`_HARNESS_REFUSAL_PATTERNS` (spawn.py:2074-2079: `"requires approval"`,
`"Permission to use \S+ has been denied"`, `"cannot be statically
analyzed"`, `"simple_expansion"`). The emitted `detail` (spawn.py:2132-2135)
is only the truncated denial message text itself — e.g. literally `"This
command requires approval"` — never the command that was refused.

The refused command IS available earlier in the same stream loop: when the
preceding `assistant`/`tool_use` block is parsed (around spawn.py:4193-4221),
`Bash` tool_use blocks have their `command` extracted
(`command = str(inp.get("command") or "")`, spawn.py:4215-4216) — but this
is only used to check `_PROGRESS_BASH_PREFIXES` for unrelated `progress`
events. `tool_use_names` (spawn.py:4206-4207) threads only `id -> name`
(e.g. `"Bash"`) forward to refusal correlation
(`_flush_correlated_refusals` at spawn.py:2168,
`_flush_unverified` at spawn.py:2183-2184) — never the command text itself.
So the fix for acceptance check 1 is: thread the command text alongside
the name (e.g. `id -> (name, command)`), and fold it into the emitted
event's fields when a refusal correlates to a `Bash` tool_use.

**2. Spawn-time permission allowlist shape.**

`role_settings(role, cwd)` (spawn.py:467-621) builds the per-spawn
`.claude/settings.json`-shaped dict. Its `permissions.allow` list
(spawn.py:577-582) already exists and is populated with plain tool names
(`WebSearch`, `WebFetch`, `Read`, `Grep`, `Glob`) via a fixed loop, plus
`MUSTER_MCP_ALLOW`-derived `mcp__`-prefixed entries (spawn.py:584-603),
plus whatever `roles/<role>.json` itself declares under
`permissions.allow` (preserved, not replaced — confirmed by
`test_role_declared_permissions_allow_entries_preserved`,
test_spawn.py:607-621). A comment at spawn.py:577-578 explicitly notes
Bash subpatterns were excluded from this fixed-tool-name loop because a
**global** Bash allow can't be safely scoped to read-only.

That reasoning does not block a **path-scoped** Bash allow: `role_settings`
already receives the concrete, unique-per-spawn isolated workspace path as
`cwd` — `cwd = issue_workspace(cwd, issue, role)` is computed before
`role_settings(role, cwd)` is called (spawn.py:3902, spawn.py:3932) — so
`Bash(...)` allow entries can be generated at spawn time anchored to that
one spawn's own workspace path (e.g. `Bash(cd {cwd}*)`,
`Bash({cwd}/venv/bin/pip install:*)`), never a fixed pattern baked into
`spawn.py` itself. This keeps the allow scoped per-instance to one
isolated workspace, never global — satisfying acceptance check 3.

Claude Code's `permissions.allow` already supports this prefix-pattern
shape today: `test_spawn.py:612` shows a role declaring
`{"allow": ["Bash(git *)"]}` and spawn.py preserving it verbatim.

**3. Which command shapes were actually refused (this run's evidence).**

Per the issue body: the phase-2 technical-feasibility session for the
soongsil-course-registration run hit `harness-refusal: This command
requires approval` twice, "likely venv/pip install and/or running the live
PoC script" — i.e. `python3 -m venv`, `pip install` (inside the isolated
workspace), and running a committed script under the workspace's `test/`
directory. These are exactly the shapes acceptance check 2 names.

## Existing tests / conventions

- `spawn.py` and `test_spawn.py` live at repo root (not under `src/`/
  `test/`) — established convention, confirmed by issue-554/issue-555's
  own landed changes touching `spawn.py`/`test_spawn.py` at root.
- Permission-allowlist tests: `WebToolPermissionAccess`
  (test_spawn.py:581-621), `MustMcpAllowEnv` (test_spawn.py:624-705),
  `PackageRegistryAccess` (test_spawn.py:708-739+).
- Refusal-classifier tests, same file: e.g.
  `test_harness_permission_denial_is_not_labeled_gate_refusal`
  (test_spawn.py:2272-2296), using fixture denial strings verbatim from
  issue #232 (`"This command requires approval"`,
  `"Permission to use Bash has been denied"`, etc.) via helper
  `_tool_use_line(tool_use_id, name)` (test_spawn.py:2211-2218) — which
  currently builds `tool_use` blocks with `"input": {}`, i.e. no command
  captured in the fixtures either; this helper needs a command parameter
  to drive the new test.
- Test framework: stdlib `unittest` (`unittest.TestCase` classes,
  `unittest.main()` at test_spawn.py:6121-6122).

## Write set

- `spawn.py` — thread `command` alongside `tool_use_names`, fold it into
  the emitted harness-refusal/sandbox-refusal event fields; extend
  `role_settings` to add workspace-path-scoped `Bash(...)` allow entries
  for venv/pip-install and workspace-`test/`-script execution.
- `test_spawn.py` — new tests for (1) refused command text surfaced in
  the emitted event, (2) the generated allow list covering the observed
  command shapes, (3) those entries being scoped to the spawn's own
  workspace path, not global/fixed.
- This survey and the phase-1 proposal that follows it.

No `.env.example`, dependency-manifest, or migration surface is touched —
in-process Python logic over already-existing structures.
