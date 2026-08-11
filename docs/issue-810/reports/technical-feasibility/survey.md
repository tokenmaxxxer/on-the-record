# issue-810 — research survey: plugin-only default-on orchestrator merge capability

market_argument_supplied: false

Scout: skipped — this is a platform-capability question about what Claude Code plugins can
self-grant, not a product/UX decision with comparable exemplars to survey. One-line reason per
scout-directive's mandatory skip record: "no design decision open — the spec (northpole req #4/#7)
fixes the goal; the open question is a platform schema/hook-semantics fact, answered by primary
docs, not by surveying comparable products."

This reads the specification (issue #810: ship, plugin-only, a mechanism that makes the
orchestration session's `gh pr merge` of a READY PR reliably permitted, default-on at install,
while role sessions stay blocked per contract v3 s10) without the market/product argument that
motivated it. No verdict here — the proposal (docs/issue-810/proposals/technical-feasibility.md)
converges the four probes below.

## Current-state survey

`find . -iname "settings.json" -not -path "*/node_modules/*"` returns zero results anywhere in
this repo, including under `on-the-record/` — <source: shell check, this repo, executed live
2026-08-11>. canonical: shell check output above. This repo ships no project-level
`.claude/settings.json` at all; the only permission surface a user could hand-add today is a
`.claude/settings.local.json` this repo does not create for them, which is exactly what the issue
calls "manual permission grant" and rules out as the default path.

`on-the-record/hooks/hooks.json` wires ten `PreToolUse` hooks against the `Bash` matcher already
(path:on-the-record/hooks/hooks.json — see `PreToolUse` → matcher `Bash`):
`contract-guard.sh`, `pr-preflight.sh`, `delegation-post-gate.sh`, `claim-scan-preflight.sh`,
`spec-index-preflight.sh`, `role-axis-completeness-guard.sh`, `gate-registration-guard.sh`,
`impact-guard.sh`, `plan-order-guard.sh`, `delegated-judgment-gate.sh` — <source:
on-the-record/hooks/hooks.json>. canonical: python parse of on-the-record/hooks/hooks.json,
executed live 2026-08-11. All ten follow the same convention: a `deny(msg)` helper that prints
JSON and calls `sys.exit(2)` (the hook-level "block this tool call" exit code), and `sys.exit(0)`
everywhere else (no-op, defer to the normal permission flow) — <source:
on-the-record/hooks/contract-guard.sh:48-50,57; on-the-record/hooks/impact-guard.sh:64-66,71;
on-the-record/hooks/plan-order-guard.sh:65-67,72>. None of the ten ever emits an *allow* signal —
every one of them is deny-or-silent. That is the architecture's current capacity: it can refuse a
`gh pr merge`, never pre-approve one. contract-guard.sh's own header already frames this exact gap:
"This gates a PR MERGE... the worst thing that can happen is silently approving a merge this
script positively determined should not happen" — the file was written to prevent bad merges, not
to guarantee good ones reach main — <source: on-the-record/hooks/contract-guard.sh:22-27>.

`gates/landing_readiness.py` already defines a `classify` function (path:gates/landing_readiness.py
line 31) that computes the READY/NOT-READY verdict this issue's mechanism must gate on — PR state,
checks, record presence, approval presence — canonical: `grep -n "^def " gates/landing_readiness.py`
output, executed live 2026-08-11, so "is this PR landing_readiness=READY" is not new logic to
invent; it is an existing importable function.

Role-vs-orchestrator identity is already load-bearing throughout the hook set via the
`CLAUDE_ROLE` env var, snapshotted at `SessionStart` by session-role-bind.sh so a session cannot
flip its own identity mid-turn by unsetting the var later — <source:
on-the-record/hooks/session-role-bind.sh:5-24>. Every existing role-scoped hook (approval-gate.sh,
deliverable-guard.sh, retry-loop-bound.sh, decision-queue-stopgate.sh, and others) reads this same
snapshot the same way — <source: on-the-record/hooks/approval-gate.sh:73-79>. This is the existing,
already-tested identity primitive any new merge-authorization mechanism should reuse rather than
inventing a second one.

Deploy/runtime config surface: none applicable — no new env var is implied by any candidate below;
`CLAUDE_ROLE` already exists and is already the identity signal in use.

## Probe 1 — technical (spike-report + reversibility)

**Question (spike_goal):** can a plugin ship, install-only with zero user action, a mechanism that
makes the orchestration session's `gh pr merge` of a READY PR reliably permitted, without granting
that same capability to role sessions?

**Findings**, gathered live 2026-08-11 via direct fetch of the canonical docs
(code.claude.com/docs) plus this repo's own hook inventory above:

1. Plugin-shipped `settings.json` supports **only** the `agent` and `subagentStatusLine` keys today
   — "Currently, only the `agent` and `subagentStatusLine` keys are supported... Unknown keys are
   silently ignored" — <source: https://code.claude.com/docs/en/plugins.md>, fetched live
   2026-08-11. This reconfirms the #801/PR#804 prior finding is still current: there is no
   `permissions` field a plugin's `settings.json` can carry. A bundled `permissions.allow` rule for
   `gh pr merge` is not merely blocked by the classifier — the schema has no field to place it in.
2. The `agent` key activates one of the plugin's custom agents as the **main thread** (system
   prompt, tool restrictions, model) — but a plugin-defined agent's `permissionMode` frontmatter
   field is explicitly stripped: "For security reasons, plugin subagents don't support the `hooks`,
   `mcpServers`, or `permissionMode` frontmatter fields. These fields are ignored when loading
   agents from a plugin... You can also add rules to `permissions.allow`... in `settings.json`, but
   these rules apply to the entire session, not only the plugin subagent" — <source:
   https://code.claude.com/docs/en/sub-agents>, fetched live 2026-08-11. This closes candidate (a)
   from the issue two ways at once: no `permissions` key to ship (finding 1), and even routing
   through a plugin-shipped `agent` cannot carry a `bypassPermissions` mode (finding 2) — a plugin
   cannot self-grant `bypassPermissions` for its main-thread agent either.
3. `PreToolUse` hooks — which a plugin **can** ship, via `hooks/hooks.json`, exactly as this repo
   already does for its ten deny gates — can set `hookSpecificOutput.permissionDecision: "allow"`
   in their JSON stdout to auto-approve the matched tool call, bypassing the interactive
   permission classifier for that call: `"allow": auto-approves the tool call, bypassing the
   permission prompt"` — <source: https://code.claude.com/docs/en/hooks>, fetched live 2026-08-11.
   The same fetch states plugin-shipped hooks carry this capability identically to project-level
   hooks — no plugin-specific restriction on `permissionDecision` (unlike finding 2's
   `permissionMode` restriction, which is agent-frontmatter-specific, not hook-specific) — <source:
   https://code.claude.com/docs/en/hooks>. This is the mechanism candidate (b) in the issue was
   reaching for ("headless bypassPermissions merge-executor... does gh-guard block it") except it
   does not require a separate headless bypass-permissions process at all — an ordinary
   plugin-shipped `PreToolUse` hook, running inside the same interactive orchestration session, can
   emit the allow decision directly.
4. canonical: live WebFetch of https://code.claude.com/docs/en/hooks on this exact precedence
   question, executed 2026-08-11. **Open gap, not closed by documentation:** when several
   `PreToolUse` hooks match the same tool call, the docs state "All matching hooks run in parallel"
   but do not document a precedence rule for conflicting `permissionDecision` values (one hook
   `"deny"`, another `"allow"`) — <source: https://code.claude.com/docs/en/hooks>. The explicit
   fetch on this exact question returned no documented precedence (unverifiable beyond this: the
   public docs simply do not state the rule, so this finding is reported as an absence, not a
   resolved fact). unverifiable: no published precedence rule exists to cite for the
   exit-code-2-vs-JSON-allow interaction; resolving it requires an empirical, in-product test, not
   another documentation read. This repo's existing ten deny gates do not use the JSON
   `permissionDecision` channel at all — they use the separate, older exit-code-2 "block"
   convention (`deny(msg): sys.exit(2)`), which is a hard stop on the tool call independent of what
   any other hook returns — <source: on-the-record/hooks/contract-guard.sh:48-50>. A new allow-hook
   using the JSON `permissionDecision` channel is therefore additive on a different channel, not a
   competing vote against the existing deny gates' exit-code-2 blocks — but the *cross-channel*
   interaction (does exit-2 from one hook still block the call when another hook's JSON says
   `"allow"`) is exactly as undocumented as same-channel conflicts. This is the one load-bearing
   fact this probe could not resolve from documentation alone.

**Reversibility tag:** two-way / low-cost — a new hook file plus one `hooks.json` entry is a
plugin-only change, removable in one revert; no schema migration, no data written, no external
system touched.

**Result:** `pass: <findings 1-3>` for "a plugin-only, install-only, default-on mechanism exists" —
`PreToolUse`'s `permissionDecision: "allow"` channel is real, plugin-shippable, and requires zero
user action beyond install. `blocked: <finding 4>` for "verified safe against the existing deny
gates without an empirical check" — the exit-2-vs-JSON-allow precedence is undocumented and must be
demonstrated live (this is exactly the issue's own step-3 execution-observation ask) before this
graduates from `feasible-with-conditions` to unconditional `go`.

## Probe 2 — prior_art (build-vs-buy)

No third-party dependency is being selected — the candidates are all first-party Claude Code
platform mechanisms (plugin `settings.json`, plugin `agent` activation, plugin `PreToolUse` hooks)
already exercised elsewhere in this repo (on-the-record/hooks/hooks.json's existing ten gates).
Framed as build-vs-buy across the platform surfaces available:

| Option | Health evidence | Verdict |
|---|---|---|
| **Buy**: plugin `settings.json` permission grant | Would be first-party and zero-maintenance if it existed — but the schema does not carry a `permissions` key (probe 1 finding 1) — <source: https://code.claude.com/docs/en/plugins.md> | Not buildable today — nothing to buy |
| **Buy**: plugin `agent` activation with `bypassPermissions` | First-party mechanism, but `permissionMode` is explicitly stripped from plugin-defined agents (probe 1 finding 2) — <source: https://code.claude.com/docs/en/sub-agents> | Not buildable today |
| **Build**: plugin-shipped `PreToolUse` hook emitting `permissionDecision: allow` | Already the pattern this repo uses for every deny gate (path:on-the-record/hooks/hooks.json); the allow channel is documented and plugin-shippable (probe 1 finding 3) | Buildable now, reuses this repo's own hook conventions and `CLAUDE_ROLE`/landing-readiness primitives |

**Result:** `pass: <evidence above>` — the third option is the only buildable one, and it is a
same-shape extension of machinery this repo already maintains (ten existing `PreToolUse` Bash
hooks), not a new dependency class.

## Probe 3 — legal_regulatory (license-scan + DPIA-before-processing)

No new third-party dependency is introduced by any candidate — all are first-party Claude Code
plugin primitives (`hooks.json`, `settings.json`, `agents/`) already vendored into this repo's own
license, or first-party product behavior documented at code.claude.com. No personal data is
processed; the new hook would read PR/issue state (numbers, branch names, CI check state) already
public on this repo's own GitHub remote, not end-user data. DPIA-before-processing does not
trigger.

**Result:** `pass: no new dependency, no new data category — no license or regulatory surface
introduced by any candidate` — <source: on-the-record/.claude-plugin/plugin.json (no added deps)>.

## Probe 4 — threat_model (STRIDE, one row per element/category/trust boundary)

| Element | Trust boundary | STRIDE category | Threat | Disposition |
|---|---|---|---|---|
| New `PreToolUse` allow-hook (candidate, this issue) | orchestration session → `gh pr merge` execution | Elevation of Privilege | The allow-hook mis-identifies a role session as the orchestrator (e.g. a bug in reading `CLAUDE_ROLE`) and grants merge to a role session, breaking contract v3 s10 | **mitigated** — reuse session-role-bind.sh's existing snapshot-at-`SessionStart` identity read (path:on-the-record/hooks/session-role-bind.sh:5-24), the same primitive approval-gate.sh already trusts for the equivalent "is this the orchestrator" question; do not invent a second identity check |
| New allow-hook | READY-verdict computation → merge execution | Tampering | The hook computes its own ad-hoc "is this PR ready" check that drifts from gates/landing_readiness.py's actual definition of READY, allowing a merge that the canonical classifier would have called NOT-READY | **mitigated** — call the existing `classify` function in gates/landing_readiness.py (path:gates/landing_readiness.py line 31) directly rather than reimplementing the READY predicate in the new hook |
| Cross-channel precedence (exit-code-2 deny vs. JSON `permissionDecision: allow`) | existing ten deny gates → new allow-hook, same `PreToolUse` event | Elevation of Privilege | canonical: live WebFetch of https://code.claude.com/docs/en/hooks, 2026-08-11 (see probe 1 finding 4). Undocumented precedence means, in the worst case, the new hook's `allow` could silently override a sibling hook's `deny` for the same `gh pr merge` call, defeating the existing deny gates in one step | **deferred** — this is the proposal's blocking condition; must be resolved by a live empirical check (deliberately construct a call one existing gate denies and confirm the new hook still does not cause it to execute) before shipping default-on, per this repo's own reversibility-scaled-evidence convention for a change that is otherwise two-way but touches a not-fully-documented platform interaction |
| `gh pr merge` command construction inside the new hook (target-repo/PR-number resolution) | untrusted PR/issue text → shell command | Tampering (injection) | An issue/PR title or body containing shell metacharacters gets interpolated into a command the hook runs to check READY-ness | **mitigated** — reuse contract-guard.sh's already-hardened target-repo/PR-number resolution (path:on-the-record/hooks/contract-guard.sh:66-79), which already passes values through env and quotes rather than interpolating into a shell string, per protocol.md invariant 5 |
| Orchestration session identity itself | user's machine → plugin-granted merge capability | Spoofing | A process outside any real Claude Code session claims to be "the orchestrator" and somehow triggers the hook | **accepted** — out of scope: `PreToolUse` hooks only fire inside an actual Claude Code tool-call lifecycle; a script outside that lifecycle cannot trigger `hookSpecificOutput` processing at all, and if the user's own machine is already compromised to that degree, standing user-level GitHub credentials are already a bigger exposure than this hook |

## Grading summary

| Probe | Result |
|---|---|
| technical | pass on mechanism existence (`permissionDecision: allow` is real and plugin-shippable); blocked on cross-channel precedence, resolvable only by a live empirical check |
| prior_art | pass — the hook-based option is the only buildable one and reuses this repo's existing pattern |
| legal_regulatory | pass — no new dependency, no new data category |
| threat_model | 3 rows mitigated (reusing existing, already-trusted primitives), 1 deferred to the empirical check the technical probe also names, 1 accepted (out of scope) |
