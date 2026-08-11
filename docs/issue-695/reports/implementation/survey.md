# Survey: issue #695 — remove role-session sandbox

## Skip record
Scout (product-exemplar sweep) skipped: this is infra removal of an
in-house sandbox mechanism inside `spawn.py`, driven by an operator
decision already recorded in the issue text (blockage history + explicit
risk acceptance), not a product-shaped surface with external exemplars to
benchmark against. No design decision is open on "how a sandbox should
work" — the decision is "stop enabling ours." Scouting an unrelated
category would not inform this change.

## Write surface

`role_settings()` in `spawn.py` (lines 487-660ish) is the sole place that
turns a role's declared `sandbox` block into the settings passed to the
Claude Code CLI. It does five sandbox-only things, each gated on
`sb0.get("enabled")` or unconditional once a `sandbox` key exists:

1. **Registry/web-domain merge into `sandbox.network.allowedDomains`**
   (lines 539-553, issues #38/#58) — only runs `if sb0.get("enabled")`.
2. **`SANDBOX_OPEN_NETWORK` / `SANDBOX_OPEN_TOP_LEVEL` switch-opening**
   (lines 554-561, issue #72) — same `enabled` guard.
3. **Package-cache `allowRead` mount** (lines 568-577, issue #38) — same
   `enabled` guard.
4. **`tlsTerminate` shim** (lines 638-641) — unconditional whenever
   `sandbox.credentials.envVars` is set, independent of `enabled`.
5. **`allowUnsandboxedCommands = False` pin** (lines 643-647) —
   unconditional; always sets `s["sandbox"]["allowUnsandboxedCommands"]`
   and re-assigns `s["sandbox"] = sb` even when no sandbox key existed on
   the spec (this line currently *creates* `sandbox: {allowUnsandboxedCommands:
   false}` on any role, sandboxed or not, since `sb = s.get("sandbox", {})`
   defaults to `{}`).

Role spec files (`roles/*.json`) declare `"sandbox": {"enabled": true,
"network": {"allowedDomains": [...]}}` per-role (30+ files). Some roles
(none checked) may omit `sandbox` entirely, in which case today's
`allowUnsandboxedCommands` block (item 5) still fires and manufactures a
`sandbox` key.

`permissions.allow` construction (lines 599-636: WebSearch/WebFetch/Read/
Grep/Glob, workspace Bash allow-patterns, `MUSTER_MCP_ALLOW`) is entirely
independent of the `sandbox` block — it reads/writes `s["permissions"]`,
never `s["sandbox"]`, and must be left untouched per issue scope.

## Test surface

`test_spawn.py` has sandbox-behavior tests that assert `enabled: True`
and exercise items 1-3 (domain merge, switch-opening, cache mounts):
`test_open_switches_set_for_every_sandboxed_role` (line ~874, asserts
`sandbox.enabled is True` for every role that declares it), plus tests
around lines 750-902 for domain merge and cache-mount behavior — all
gated on `spec.get("sandbox", {}).get("enabled")`, so once
`role_settings()` stops enabling the sandbox these assertions go
permanently false and must be removed/rewritten, not left to bit-rot.
Tests referencing `sandbox-refusal` classification (~line 2362-2479)
exercise a different code path (event classification when the harness
itself reports a sandbox denial) and are not about `role_settings()`
enabling anything — out of this write set unless they turn out to assert
on `role_settings()` output, which a full read will confirm before
editing.

`gates/test_hooks_parity.py` references `role_settings` — needs a check
during build whether it depends on sandbox-enabled output; not confirmed
yet, flagged as an unknown for the write set.

## Decisions already on record

No prior ADR on the sandbox boundary itself exists under `docs/decisions/`
— the issue is the first place the removal decision is recorded (in the
issue body, dated 2026-08-11, attributed to the operator). This proposal's
ADR will be the first `docs/decisions/` entry for the sandbox boundary.

## Open unknowns for the build (phase 2)

- Exact line ranges shift once earlier edits land; the build reads
  current line numbers rather than trusting this survey's line refs.
- Whether any role in `roles/*.json` omits `sandbox` entirely (affects
  whether the "representative role" acceptance test needs to special-case
  that).
- Full diff shape of `test_spawn.py` changes (removal vs rewrite per
  assertion) — decided at build time against actual current test bodies.
