---
status: proposed
files:
  - spawn.py
  - test_spawn.py
  - docs/issue-558/reports/implementation/survey.md
---

## Request

A spawned role session is headless — nobody can answer an interactive
approval prompt. The 2026-08-09 soongsil-course-registration run hit
`harness-refusal: This command requires approval` twice during a
phase-2 technical-feasibility session (likely venv/pip install and/or
running the live PoC script), and the watch event carries only the fixed
denial text, never the refused command — so the orchestrator cannot tell
a genuinely-needed, not-pre-allowed refusal apart from the model simply
choosing not to run something. Fix: (1) include the refused command text
in the harness-refusal watch event; (2) extend the spawn-time permission
allowlist so legitimate role work inside the isolated workspace (venv
creation/pip install, running committed workspace `test/` scripts) is
pre-allowed — scoped to that spawn's own workspace path, never global.

## Constraints

- Pure bugfix / hardening — no new design decision opens beyond which
  concrete command shapes to pre-allow, and those are named directly by
  the issue body and its run evidence (confirmed in the survey; scouting
  skipped, second skip condition).
- The new `Bash(...)` allow entries must be generated per-spawn, anchored
  to that spawn's own isolated workspace path (`cwd` as already computed
  by `issue_workspace()` before `role_settings()` is called) — never a
  fixed pattern baked into `spawn.py` that would apply outside any one
  workspace.
- The existing fixed-tool-name allow loop (`WebSearch`/`WebFetch`/`Read`/
  `Grep`/`Glob`) and its stated reason for excluding a global Bash
  subpattern (spawn.py:577-578) stay untouched — this proposal adds a
  separate, path-scoped Bash allow, not a change to that reasoning.
- Refusal-event correlation (`_flush_correlated_refusals`,
  `_flush_unverified`) keeps its existing dedup/correlation behavior;
  only the emitted `detail`/fields gain the command text, nothing about
  when an event fires changes.
- Existing refusal-classifier and permission-allowlist tests
  (`WebToolPermissionAccess`, `MustMcpAllowEnv`, `PackageRegistryAccess`,
  the `test_..._is_not_labeled_gate_refusal` family) keep passing
  unchanged.

## Rationale

For scoping the new Bash allow, two approaches were weighed:

- **A fixed set of Bash prefix patterns hard-coded into `spawn.py`**
  (e.g. always allow `Bash(python3 -m venv *)`, `Bash(pip install *)`
  regardless of directory). Rejected: this is exactly the shape the
  existing comment at spawn.py:577-578 already rules out for the
  tool-name loop — a Bash subpattern with no path anchor "can't be
  safely scoped to read-only" (or, here, to the isolated workspace at
  all); it would allow the same pip/venv invocation anywhere the role
  session's cwd happened to be, not just inside its isolated workspace,
  failing acceptance check 3 outright.
- **Per-spawn, workspace-path-anchored Bash allow entries generated
  inside `role_settings(role, cwd)`** (chosen). `cwd` is already the
  concrete, unique isolated workspace path for this one spawn
  (`issue_workspace(cwd, issue, role)`, computed at spawn.py:3902 before
  `role_settings(role, cwd)` is called at spawn.py:3932) — so the
  allow entries can be built as full, specific command-prefix patterns
  that embed `cwd` (e.g. `Bash(cd {cwd} && python3 -m venv venv:*)`,
  `Bash({cwd}/venv/bin/pip install:*)`), written once into that spawn's
  own `settings.json`. A warrant-hunt pass on this proposal (stance 0,
  after-proposal) flagged a bare trailing-wildcard shape like
  `Bash(cd {cwd}*)` as unsafe — it pre-approves any command starting
  with `cd {cwd}` regardless of what follows (e.g.
  `cd {cwd} && rm -rf ~`), reproducing the exact unanchored-Bash-subpattern
  failure this proposal's own rejected alternative names. Entries
  actually generated must each fully specify the command shape after the
  workspace path (the concrete venv/pip/test-script invocation itself,
  not a bare `cd`-then-wildcard) — `cwd` narrows *where*, the rest of
  the pattern narrows *what*; a `cd`-only prefix with a trailing wildcard
  is explicitly excluded from what gets built. No code path exists where
  a correctly-built entry could match a command outside the intended
  shape or workspace; a different spawn gets a different,
  differently-anchored settings.json.

For threading the command into refusal events, the alternative was
**re-deriving the command from the raw transcript at report time**
(scan backward from the refusal line for the nearest preceding
`tool_use` `Bash` block, done ad hoc wherever an event is displayed).
Rejected: the stream loop already parses `Bash` `tool_use` blocks and
extracts `command` in-line (spawn.py:4215-4216) for an unrelated
purpose (`_PROGRESS_BASH_PREFIXES` matching); re-deriving it again
downstream would duplicate that parsing and could drift out of sync with
which `tool_use` id a given refusal actually correlates to. Threading
the already-extracted `command` through the same `tool_use_names`-style
map that already correlates refusals to tool names is the minimal
change and can't disagree with the correlation the refusal path already
performs.

## What will be done

- In the stream-processing loop (near spawn.py:4193-4221), change what's
  threaded forward for `Bash` tool_use blocks from name-only to
  `(name, command)`, so the refusal-correlation call sites already
  reading that map (`_flush_correlated_refusals` spawn.py:2168,
  `_flush_unverified` spawn.py:2183-2184) have the command text
  available when a refusal correlates to a `Bash` tool_use.
- Extend `_classify_refusal_text` (spawn.py:2107-2140) and its call site
  to accept the correlated command text and include it (or its
  statically-analyzable prefix, truncated the same way `detail` already
  is) in the emitted harness-refusal event's fields — additive to the
  existing `detail` (denial message text), not a replacement.
- In `role_settings(role, cwd)` (spawn.py:467-621), after the existing
  `permissions.allow` tool-name loop, add workspace-path-scoped
  `Bash(...)` entries covering: venv creation and pip install inside
  `cwd` (e.g. `python3 -m venv`, `pip install`, invoked via or anchored
  to `cwd`), and running committed scripts under `cwd`'s `test/`
  directory. Entries are built only when `cwd` is not `None` (matching
  the existing `cwd is not None` guard already used later in the same
  function for self-hosted hooks).
- Extend `_tool_use_line(tool_use_id, name)` in `test_spawn.py`
  (test_spawn.py:2211-2218) to accept an optional command so fixture
  refusal payloads can carry one.
- Add tests to `test_spawn.py`:
  1. A fixture harness-refusal log entry (`tool_use` with a `Bash`
     command immediately followed by a `tool_result` denial) asserts
     the emitted event includes the refused command text — fails on
     current `main` (event carries only the denial text), passes on
     this branch.
  2. `role_settings(role, cwd)` for a role with sandbox enabled, given a
     concrete `cwd`, asserts the generated `permissions.allow` covers
     venv creation, pip install, and workspace-`test/`-script execution
     shapes — fails on current `main` (no such entries), passes on this
     branch.
  3. Same generated allow list asserts every added entry contains the
     given `cwd` (or is otherwise unreachable outside it) — i.e. scoped,
     not a fixed global pattern; and a second `role_settings` call with
     a different `cwd` produces differently-anchored entries, not the
     same fixed strings.

## Out of scope

- Changing `_HARNESS_REFUSAL_PATTERNS` itself (which denial messages
  count as a harness-refusal) — untouched, only what accompanies an
  already-classified event changes.
- The fixed-tool-name `permissions.allow` loop
  (`WebSearch`/`WebFetch`/`Read`/`Grep`/`Glob`) and `MUSTER_MCP_ALLOW` —
  unaffected, referenced only as the existing pattern this proposal adds
  alongside.
- `sandbox.filesystem`/`sandbox.network` provisioning — unaffected; this
  proposal only adds to `permissions.allow`.
- Any command shape beyond venv/pip-install and workspace-`test/`-script
  execution — if a future run surfaces a different refused shape, that
  is a new issue, not a widening of this one.

## Accumulation

The new workspace-scoped `Bash(...)` entries are generated by a small
loop/helper inside `role_settings`, keyed off the same `cwd` the
function already threads through — not one inline `permissions.allow`
edit per command shape. If a future issue surfaces another legitimate
command shape to pre-allow, it extends that same loop's shape list (one
more entry), not a new inline block; the count of *distinct code sites*
doing this scoping stays at one regardless of how many command shapes
accumulate. Likewise, the command-threading change touches the single
existing `tool_use_names`-style correlation map, not a new per-call-site
copy — refusal correlation call sites keep reading from the one map.

## How you'll know it worked

- The three new/extended tests in `test_spawn.py` fail against current
  `main` (reproducing the issue: refusal event lacks command text; venv/
  pip-install/test-script command shapes are refused; no scoping to
  verify) and pass on this branch.
- Existing refusal-classifier tests
  (`test_harness_permission_denial_is_not_labeled_gate_refusal`,
  `test_sandbox_denial_is_not_labeled_gate_refusal`,
  `test_git_lock_masquerade_is_classified_as_sandbox_refusal`, etc.) and
  permission-allowlist tests (`WebToolPermissionAccess`,
  `MustMcpAllowEnv`, `PackageRegistryAccess`) keep passing unchanged.
