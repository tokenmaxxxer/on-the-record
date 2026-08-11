---
code_under_review:
  - spawn.py
  - test_spawn.py
  - docs/decisions/2026-08-11-remove-role-session-sandbox.md
type: refactor
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Phase 2 delivery for issue #695, upstream: docs/issue-695/proposals/implementation.md
(approved via `APPROVE issue-695/implementation`).

- `spawn.py::role_settings()`: after building `s`, force `s["sandbox"]["enabled"] = False`
  when a `sandbox` key exists, regardless of what `roles/*.json` declares.
  `permissions.allow` construction (WebSearch/WebFetch/Read/Grep/Glob,
  `_workspace_bash_allow`, `MUSTER_MCP_ALLOW`) and `enabledPlugins` are untouched.
- Removed unreachable sandbox-only plumbing: the registry/web-domain merge
  into `sandbox.network.allowedDomains` (`PACKAGE_REGISTRY_HOSTS`,
  `WEB_ACCESS_DOMAINS`), the issue-#72 switch-opening block
  (`SANDBOX_OPEN_NETWORK`, `SANDBOX_OPEN_TOP_LEVEL`), the package-cache
  `allowRead` mount block, the `tlsTerminate` shim, and the
  `allowUnsandboxedCommands = False` pin.
- Additionally removed `go_proxy_layer()`/`playwright_cache_layer()` and
  their call site — with the cache-mount block gone, their gate
  (`host_path in sandbox.filesystem.allowRead`) can never be true, so they
  always returned `None` and silently dropped the GOPROXY/PLAYWRIGHT
  cache-redirect optimization with no error or log (found by the
  before-landing warrant hunt below, stance 3). This left `PACKAGE_CACHE_DIRS`
  unused too, so it was removed as well.
- `test_spawn.py`: replaced the obsolete `PackageRegistryAccess` and
  `SandboxDefaultOpenAccess` classes (domain-merge, cache-mount,
  `go_proxy_layer`/`playwright_cache_layer`, switch-opening assertions —
  all asserted behavior that no longer exists) with `RoleSessionSandboxRemoved`,
  including the acceptance test named in the proposal
  (`test_sandbox_never_enabled_regardless_of_role_declaration`).
- `docs/decisions/2026-08-11-remove-role-session-sandbox.md`: ADR with
  rejected alternatives (declaration channel, crown-jewels-only reduced
  sandbox, per-role-file edits) and a revisit trigger.
- `docs/issue-695/reports/implementation/hunt-implementation.md`: before-landing
  hunt record (see Open findings).

Doc placement: ADR under `docs/decisions/` (system design / hard-to-reverse
choice) — done, listed above.

## Why

Basis: docs/issue-695/proposals/implementation.md

## What did not work

None.

## Open findings

Before-landing warrant hunt (stance 3, `docs/issue-695/reports/implementation/hunt-implementation.md`)
found `go_proxy_layer()`/`playwright_cache_layer()` silently going dead —
addressed in this same commit (see What was done); no open findings remain.

## Verification

`python3 -m pytest test_spawn.py -q` — 377 passed.
```
$ python3 -m pytest test_spawn.py -q
377 passed in 31.33s
```
