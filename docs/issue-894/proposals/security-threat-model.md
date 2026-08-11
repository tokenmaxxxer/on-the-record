---
status: proposed
files:
  - docs/issue-894/reports/security-threat-model.md
---

## Intent

Perform a STRIDE-style retrospective review of the permission/auto-grant posture the on-the-record
session built (merge/spawn/gh-write allow-hooks, bypassPermissions-on-resume, credential handling)
and produce a severity-ranked findings record with fixes and canonical citations, per issue #894
step 1. (Step 2/3 — structural enforcement and implementation — are a separate, later work unit
this proposal does not cover; they hand off once this retrospective lands.)

## Constraints

- Phase-2 record write (docs/issue-894/reports/security-threat-model.md) waits for the Approve
  gate (contract v3 s19) — this proposal and the survey are the only writes this turn.
- canon-references in the phase-2 record cite external canon (core/warrant, sibling
  methodology-gate.sh scripts) by path/description only, never by pasting content.
- Every mitigation-list entry carries a disposition: accept/mitigate/transfer/avoid (or the
  Korean equivalents).
- Every residual-risk-note carries a post-mitigation rating plus an approver reference
  (docs/specs/approvers.md or a named approver's "Approve").
- STRIDE table findings are ranked most-severe first.

## What will be done

The phase-2 record (once approved) will build a STRIDE table over the six artifacts named in
the issue, using the survey's citations as ground truth:
- **Spoofing** — the allow-hooks' `session_id`→role-snapshot identity check
  (survey: "Identity check") against the doc-confirmed fact that `session_id` carries no
  cryptographic binding; the open gap on session-role-bind.sh's write-path trust.
- **Tampering** — whether argument text (a crafted `--body`, issue title, or repo content) can
  smuggle a command past the shlex/quoted-heredoc checks (survey: "Command-shape validation"),
  including the one deliberately narrow exception in gh-write-allow-gate.sh.
- **Repudiation** — whether an auto-granted action leaves an attributable trail (permission
  decision reason strings, transcript).
- **Information disclosure** — credential exposure paths (survey: "Credential flow") — env
  injection, subprocess capture, `docs/**`-only guard scope.
- **Denial of service** — out of scope by the issue's own framing (auto-grant/permission review,
  not availability); noted but not deep-dived unless the survey surfaces a DoS-shaped gap.
- **Elevation of privilege** — the survey's central finding: bypassPermissions-on-resume removes
  the host's own default-deny fallback for any Bash shape outside the allow-hooks' own recognized
  shapes (survey: "bypassPermissions-on-resume: in-repo claim") — this is the highest-severity
  candidate and will be rated accordingly, with the caveat (recorded in the survey) that the
  underlying hunt record was cited, not independently re-executed, in this pass.

Each STRIDE row gets a CVSS-style rating, a mitigation-list entry with a disposition, and a
canonical code citation (file:line, matching the survey's already-gathered citations — no new
unread files unless a finding requires a specific check not yet made, e.g. reading
session-role-bind.sh to close the identity-spoofing gap). The record closes with a residual-risk
note per finding class carrying a post-mitigation rating and an approver reference.

## Out of scope

- Step 2 (structural enforcement — a board-condition/gate requiring a security-threat-model
  record before a trust-boundary change can land) and step 3 (implementing the highest-severity
  fixes) — separate work units per the issue's own three-step execution plan; this proposal
  covers step 1 only and hands off explicitly at its end.
- Re-implementing or patching any of the six reviewed artifacts — this is a review, not a fix,
  in phase 1/this proposal's scope.
- Independently re-running the #886 hunt that bypassPermissions's fallback-default-deny claim
  rests on — the record will cite it as asserted, flagging that boundary explicitly rather than
  re-deriving it, unless doing so is cheap enough to fit inside the phase-2 build.

## How you will know it worked

docs/issue-894/reports/security-threat-model.md exists with: a STRIDE table ranked by severity
over the six named artifacts, each row citing real file:line evidence; a mitigation list where
every entry carries an accept/mitigate/transfer/avoid disposition; a residual-risk-note per
finding class carrying a post-mitigation rating and an approver reference; a canon-references
section citing external canon by path/description only; and the record's own required fields
(what was done, why, upstream basis, kind/loop_state, open findings) per contract v3 s19/§20.
