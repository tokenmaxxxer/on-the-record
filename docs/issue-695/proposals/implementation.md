---
status: proposed
files:
  - spawn.py
  - test_spawn.py
  - docs/decisions/2026-08-11-remove-role-session-sandbox.md
---

## Request

Operator decision recorded in issue #695: stop `role_settings()` from
enabling the role-session sandbox in `spawn.py`, and remove the
sandbox-only plumbing that becomes unreachable once it is off
(registry/web-domain merge into `sandbox.network`, the issue-#72
switch-opening block, package-cache `allowRead` mounts, the
`tlsTerminate` shim, the `allowUnsandboxedCommands` pin). Every
`permissions.allow` rule and the plugin/rulebook/`enabledPlugins`
machinery stay untouched. Record the decision as an ADR under
`docs/decisions/` with rejected alternatives and a revisit trigger.

## Constraints

- `permissions.allow` construction (WebSearch/WebFetch/Read/Grep/Glob,
  workspace Bash allow-patterns, `MUSTER_MCP_ALLOW`) must be byte-for-byte
  unchanged — it does not read or write the `sandbox` key.
- `enabledPlugins` global-plugin-off logic must be byte-for-byte
  unchanged.
- Role spec files under `roles/*.json` are not edited — the fix is
  applied once, centrally, in `role_settings()`, not per-role.
- The acceptance check (issue body) is a unit test asserting
  `role_settings()` output for a representative role has no *enabled*
  sandbox and retains today's `permissions.allow` entries; the test must
  fail if either regresses.

## Rationale

Two shapes were available for "stop enabling the sandbox":

1. **Chosen — force `sandbox.enabled` false (or drop the block) inside
   `role_settings()`, centrally.** One code path, one place to audit,
   works regardless of what any given `roles/*.json` declares, and
   matches the issue's own phrasing ("`role_settings()` stops enabling
   the sandbox").
2. **Rejected — edit every `roles/*.json` to flip `sandbox.enabled` to
   `false` or delete the block.** Rejected because it multiplies the
   write set across 30+ role files for no behavioral gain (the enforcement
   point is `role_settings()`, not the spec files — a future role added
   with `"enabled": true` would silently re-enable the sandbox unless
   `role_settings()` itself refuses to honor it), and it conflicts with
   the "keep every `permissions.allow` rule... untouched" scope line,
   which implies the fix belongs in the shared function, not scattered
   across specs.

A third option — **weaken the sandbox to a "crown-jewels-only" reduced
boundary instead of removing it outright** — was considered at the
issue-decision level (operator weighed it) and rejected there, not by
this proposal; it is recorded as a rejected alternative in the ADR rather
than re-litigated here, since the issue text already settles it in favor
of full removal.

## Accumulation

No repeated per-file edits across `roles/*.json` are made by this
proposal — that pattern is explicitly rejected in Rationale in favor of
one central fix in `role_settings()`. If a future role adds a `sandbox`
block expecting it to activate, `role_settings()`'s forced-disable still
applies uniformly with no per-role edit needed; the role file's
`sandbox` key simply becomes inert documentation of what used to be
declared, and nothing about this change accumulates cost as roles are
added. If a later issue wants the `sandbox` key removed from every
`roles/*.json` for cleanliness (not required for this fix to work), that
is a separate, explicitly-scoped follow-up, not something this proposal
starts piecemeal.

## What will be done

- In `spawn.py::role_settings()`: after the `sandbox` block is read from
  the role spec, force it to a disabled state (`sandbox.enabled = False`,
  or the block is dropped entirely — decided at build time by whichever
  reads simplest against the surrounding code) so the CLI sandbox never
  activates for a role session.
- Remove the four items of now-unreachable sandbox-only plumbing
  identified in the survey: the registry/web-domain merge into
  `sandbox.network.allowedDomains` (issues #38/#58), the `SANDBOX_OPEN_*`
  switch-opening block (issue #72), the package-cache `allowRead` mount
  (issue #38), and the `tlsTerminate` shim. The `allowUnsandboxedCommands
  = False` pin is removed as sandbox-only plumbing per the issue's
  explicit scope list; if any non-sandbox code path is found at build
  time to depend on it, that dependency is noted in the record rather
  than silently preserved.
- Any now-unused module-level constants feeding only the removed blocks
  (e.g. `PACKAGE_REGISTRY_HOSTS`, `WEB_ACCESS_DOMAINS`,
  `SANDBOX_OPEN_NETWORK`, `SANDBOX_OPEN_TOP_LEVEL`, `PACKAGE_CACHE_DIRS`
  helper functions) are removed only if the build confirms, by grep, that
  nothing else in `spawn.py` or its test file references them — left in
  place otherwise, with that fact noted in the record.
- Update `test_spawn.py`: remove or rewrite the sandbox-enabled
  assertions identified in the survey (domain-merge, switch-opening,
  cache-mount, `test_open_switches_set_for_every_sandboxed_role`) so the
  suite reflects the new behavior, and add the acceptance test named in
  the issue (representative role -> no enabled sandbox, `permissions.allow`
  entries retained).
- Write `docs/decisions/2026-08-11-remove-role-session-sandbox.md` as an
  ADR: context (blockage history #38/#58/#65/#72/#153 + 2026-08-11 tas
  report), decision (remove sandbox from role sessions), accepted risks
  (as listed in the issue), rejected alternatives (keep + declaration
  channel; weakened crown-jewels-only sandbox), and a revisit trigger
  (e.g. a credential-read or cross-workspace-write incident in an
  unsandboxed role session).

## Out of scope

- `permissions.allow` rules and headless approval-death handling
  (#58/#65/#153/#558) — explicitly out of scope per the issue.
- The plugin/rulebook/`enabledPlugins` machinery.
- Editing `roles/*.json` per-role.
- `sandbox-refusal` event-classification tests unless the build confirms
  they assert on `role_settings()` output (survey flagged this as
  unconfirmed; if confirmed in-scope it stays a small addition to the
  already-listed `test_spawn.py` file, not a new file).
- Any change to `gates/test_hooks_parity.py` beyond what's needed to keep
  it passing if it turns out to depend on sandbox-enabled output.

## How you'll know it worked

- `python3 -m pytest test_spawn.py -k sandbox` (or equivalent unittest
  invocation) passes, including the new acceptance test.
- `python3 -c "import spawn; print(spawn.role_settings('implementation'))"`
  shows no enabled sandbox and an unchanged `permissions.allow` list
  containing today's entries (WebSearch, WebFetch, Read, Grep, Glob, plus
  the role's declared entries).
- Full `test_spawn.py` suite run once, self-confirmed before landing.
