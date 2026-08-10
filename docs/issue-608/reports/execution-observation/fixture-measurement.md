# Issue #608 step 1 — fixture measurement of approval-gate efficacy

## Scope

Subject: issue-608. Role: execution-observation, step 1 (findings only — step
2 implements a fix). Target: the deployed plugin hook surface shipped at
`on-the-record/hooks/` (this repo, HEAD of branch
`issue-608/execution-observation`) — the same surface a plugin-installed
consumer repo (e.g. tailor) actually runs. Not tested: this repo's own
`gates` directory python modules — those are dev-time pytest tooling, not
what installs into a consumer repo, which is exactly candidate cause (c)'s
question.

## Method

Read the full source of every `PreToolUse` hook in `on-the-record/hooks/hooks.json`
that could plausibly gate a phase-2 act: `deliverable-guard.sh`,
`contract-guard.sh`, `pr-preflight.sh`, `delegated-judgment-gate.sh`,
`record-claim-guard.sh`, `role-spec-reference-guard.sh`, `call-shape-guard.sh`,
`accumulation-claim-guard.sh`. Grepped each for the strings `APPROVE`,
`approv`, and `phase` to find every place approval state is consulted —
`derived: grep -rn "APPROVE\|approvers.md\|phase-2\|phase2" on-the-record/hooks/*.sh`.

Then built a disposable fixture target repo (a fresh `git init` under this
session's scratch directory, no relation to this repo's board) and invoked
`on-the-record/hooks/deliverable-guard.sh` directly — the real shipped
script, unmodified — given the same JSON stdin payload shape Claude Code's
PreToolUse hook protocol sends for a `Write` call, across the 2-by-2 matrix:
`approvers.md` present/absent, times acting session as orchestrator
(`CLAUDE_ROLE` unset) or role (`CLAUDE_ROLE=execution-observation`, the
actual phase-2 actor). Target write in every cell: a phase-2 record path
under this issue's docs tree — the shipped act the issue's live evidence
says was not blocked.

The approved/unapproved axis from the issue's acceptance matrix collapses
here: grep confirmed no `PreToolUse` hook matching `Write` or `Edit` reads an
`APPROVE issue-<n>/<role>` comment or checks `approvers.md` membership
against a live GitHub lookup at all (that check exists only in
`contract-guard.sh` and `pr-preflight.sh`, both scoped to `Bash` commands
matching `gh pr merge` / `gh pr create|edit` — see Finding 2). So for a
`Write`/`Edit` act, approval state is unreachable — the approved and
unapproved cells route through the identical code path, which is itself
part of the finding.

## Fixture run (fenced, unmodified script)

```
$ bash run_fixture.sh
approvers=present role=<none/orchestrator> -> rc=2
orchestrate: this is an orchestrator session and docs/issue-608/reports/execution-observation.md is a
deliverable path in a board repo. Deliverables are role work: draft the issue, get the user's
confirmation, and spawn the role (spawn.py <role> ... --issue <n>). You author only confirmed
issues, PR comments, and docs/specs/approvers.md.
---
approvers=absent role=<none/orchestrator> -> rc=0

---
approvers=present role=execution-observation -> rc=0

---
approvers=absent role=execution-observation -> rc=0

---
```

(`run_fixture.sh` builds the fixture repo, toggles the presence of
`docs/specs/approvers.md`, and pipes a `Write` tool_input payload targeting a
deliverable path in this issue's docs tree into the unmodified
`deliverable-guard.sh`, once per cell, with `CLAUDE_ROLE` explicitly set or
unset per cell — not inherited from this session's own env, which does carry
`CLAUDE_ROLE=execution-observation` and would otherwise silently corrupt the
orchestrator-role cells.)

## Findings

**Finding 1 — candidate (a), CONFIRMED, but only reachable for the
orchestrator session, not the role.** deliverable-guard.sh has a branch that
reads: when `approvers.md` is absent, the guard allows the write with no
message at all — not the refuse-and-instruct/bootstrap-offer the issue's
acceptance criterion requires ("a repo without approvers.md should
refuse-and-instruct ... never silently fail open"). See the file at
on-the-record/hooks/deliverable-guard.sh, the `if root is None or not
os.path.isfile(...)` branch. Fixture row 2 above reproduces this: rc=0,
empty stderr, for approvers=absent / orchestrator.

**Finding 2 — candidate (c), CONFIRMED, and this is the dominant cause.** No
`PreToolUse` hook on `Write`/`Edit`/`MultiEdit` ever checks approval state for
the *acting role* session at all. deliverable-guard.sh short-circuits
immediately, before any path or approvers.md check, whenever `CLAUDE_ROLE` is
set — i.e. for a role session, which is exactly the session that carries out
a phase-2 act. Fixture rows 3-4 above show this directly:
`role=execution-observation` returns rc=0 regardless of `approvers.md`
state. The only two hooks that read an `APPROVE issue-<n>/<role>` comment are
contract-guard.sh (gates `gh pr merge` only) and pr-preflight.sh (gates `gh
pr create`/`gh pr edit` only) — both `Bash`-matcher hooks that fire on a `gh`
subcommand, not on the file writes or `git commit` that make up the actual
phase-2 act. A role can write its phase-2 record, run its implementation, and
commit it, all without ever invoking `gh`, and therefore without ever
touching an approval check — the deployed surface's own enforcement is
confined to the two `gh pr` verbs. This matches the tailor hunt note's
"procedural only, no technical blocking" exactly: the procedure is real (the
two `gh pr` hooks are not stubs) but nothing stops the underlying act, only
downstream paperwork about it.

**Finding 3 — candidate (b), NOT CONFIRMED — insufficient evidence to assess
from this repo alone.** This survey had no access to the tailor repo's
installed plugin version or lockfile, so "predating today's merges" cannot be
checked directly. It is also not needed to explain the observed gap:
Findings 1-2 reproduce "procedural only, no technical blocking" against the
current HEAD of this repo's hook surface, so a version-lag explanation is not
required, and even if partly true would only compound rather than cause the
gap. Recommend step 2 not spend effort chasing plugin-version skew — the gap
is structural in the current source, not a staleness artifact.

## Recommendation for step 2 (not performed here — findings only)

The missing enforcement is a `PreToolUse` hook (matching `Write`/`Edit`/
`MultiEdit`, and probably `Bash` for `git commit`), scoped to role sessions
(`CLAUDE_ROLE` set), that: resolves the acting role and subject issue from
`CLAUDE_ROLE`/branch name the same way pr-preflight.sh already does; reads
`docs/specs/approvers.md` and the issue's `APPROVE issue-<n>/<role>` comments
the same way contract-guard.sh/pr-preflight.sh already do; denies a
phase-2-shaped write (a role's own record path, or any `src`/`test` write for
that issue) when no matching approval is found; and, when `approvers.md`
itself is absent, denies with a refuse-and-instruct message (bootstrap
offer) instead of a silent allow — closing Finding 1 in the same unit, per
the issue's explicit acceptance line.

## Independence

This survey read but did not edit any file under `on-the-record/hooks/`,
`gates`, or any other role's src/test/docs-issue path. The fixture repo is a
disposable throwaway outside this repo's board, and the
`deliverable-guard.sh` copy it invoked was read, not modified, from this
repo's own checkout.
