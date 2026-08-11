# Remove the role-session sandbox

## Status

Accepted (2026-08-11)

## Context

`role_settings()` in `spawn.py` injected the CLI's `sandbox` boundary
(filesystem allow/deny, network `allowedDomains`, default-deny switches)
into every headless role session it launched. The boundary produced a
sustained stream of blockage bugs that made role sessions unable to
complete legitimate work without an operator intervening:

- #38 — GOMODCACHE not reachable, package installs blocked
- #58 / #65 — WebSearch/WebFetch destinations can't be enumerated in
  advance, so network `allowedDomains` couldn't be populated correctly
- #72 — default-deny sandbox switches blocked ordinary operations
- #153 — read-only tool calls (Read/Grep/Glob) hit the same
  tool-permission gap as #58/#65
- 2026-08-11 target-repo (tas) report — harness builds failed on denied
  writes to the repo's own build cache (`.muster-cache/gomod`), making
  penetration verification structurally impossible in headless role
  sessions

Each fix added more plumbing to keep the sandbox usable (registry-host
domain merge, web-access wildcard, cache mounts, switch-opening,
`tlsTerminate`), which grew role_settings() without reducing the
blockage rate — a new gap kept appearing wherever the plumbing had not
yet been extended.

## Decision

Stop the role-session sandbox from ever activating. `role_settings()`
now forces `sandbox.enabled = False` centrally, regardless of what any
`roles/*.json` file declares. This is a single enforcement point — a
future role file with `"sandbox": {"enabled": true}` still gets the
sandbox refused, rather than requiring every role spec to be edited.

The plumbing that existed only to keep the sandbox usable is removed as
unreachable now that it can never turn on:

- the registry-host / web-access domain merge into
  `sandbox.network.allowedDomains` (issues #38, #58)
- the issue #72 default-deny switch-opening block
  (`SANDBOX_OPEN_NETWORK` / `SANDBOX_OPEN_TOP_LEVEL`)
- the package-cache `allowRead` mount block (issue #38)
- the `tlsTerminate` credential-masking shim
- the `allowUnsandboxedCommands = False` pin

`permissions.allow` construction (WebSearch/WebFetch/Read/Grep/Glob,
the workspace Bash allow-patterns, `MUSTER_MCP_ALLOW`) and the
`enabledPlugins` global-plugin-off logic are untouched — that layer is
the CLI's tool-permission gate, not the sandbox, and it keeps working
exactly as before.

## Consequences

Accepted, with the risks named at decision time:

- role sessions gain read access to `~/.claude` and other credential
  paths on the host (a past incident read a denyRead-blocked
  `~/.claude` via unsandboxed re-execution; `allowUnsandboxedCommands`
  was the countermeasure, and it is gone with the sandbox)
- writes outside the isolated workspace become possible
- network egress is no longer domain-limited
- `gh` identity separation between the operator and role sessions loses
  the physical backing it leaned on when the sandbox was active

In exchange, role sessions no longer die on sandbox-boundary denials
that have no operator available to approve past (the headless failure
mode every one of the linked issues shares).

## Alternatives considered

**Keep the sandbox, add a declaration channel for what a role needs.**
Rejected: every prior fix (#38, #58, #65, #72) was exactly this shape —
declare more of what's needed, extend the boundary. The blockage rate
did not go down as the declared surface grew; it moved to whatever the
next role or workflow needed that hadn't been declared yet. The
tas report is the latest instance of the same failure mode, not a new
one — there is no evidence this channel converges.

**Weaken the sandbox to a "crown-jewels-only" reduced boundary** (deny
only a short list of clearly sensitive paths — credentials, SSH keys —
and leave everything else default-allow). Rejected at the issue-decision
level: it still requires enumerating what's sensitive in advance, which
is the same declare-ahead-of-need shape that failed above, and it adds
a second boundary concept (full sandbox vs. reduced sandbox) to reason
about without removing the failure class — a role session can still be
blocked on a path nobody added to the reduced deny-list's complement.

**Edit every `roles/*.json` to flip `sandbox.enabled` to `false` or
delete the block**, instead of forcing it centrally in
`role_settings()`. Rejected: multiplies the write set across 30+ role
files for no behavioral gain, and a future role added with
`"enabled": true` would silently re-enable the sandbox unless
`role_settings()` itself refuses to honor it.

## Revisit trigger

Revisit this decision if either holds:

- an incident occurs where a role session's access to `~/.claude`,
  another credential path, or the host filesystem/network outside its
  workspace causes real harm (the risk accepted above materializes)
- a role class emerges whose workspace is not adequately isolated by
  the harness's other boundaries (git worktree, cwd) and needs a
  filesystem/network boundary the sandbox used to provide

If revisited, re-litigate the "declaration channel" and "crown-jewels
reduced sandbox" alternatives above against whatever concrete failure
triggered the revisit, rather than restoring the removed plumbing
as-is — it grew unbounded once already.
