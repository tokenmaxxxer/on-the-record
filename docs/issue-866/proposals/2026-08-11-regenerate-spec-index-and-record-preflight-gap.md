---
status: approved
files:
  - docs/specs/reconciled-index.md
  - on-the-record/hooks/spec-index-preflight.sh
  - on-the-record/hooks/test_spec_index_preflight.py
  - docs/issue-866/reports/implementation/survey.md
  - docs/issue-866/reports/implementation/2026-08-11-hunt-regenerate-spec-index-and-record-preflight-gap.md
  - docs/issue-866/reports/implementation/resolution.md
  - docs/issue-866/proposals/2026-08-11-regenerate-spec-index-and-record-preflight-gap.md
---

Note (this session): `docs/issue-866/reports/implementation.md` — the
phase-2 record path — is mechanically blocked by
`on-the-record/hooks/approval-gate.sh` without a real
`APPROVE issue-866/implementation` GitHub comment from a
`docs/specs/approvers.md`-listed account, which does not exist yet for
this issue. `approval-gate.sh` does not gate
`on-the-record/hooks/spec-index-preflight.sh` or its test (its own
scope is exactly the role's record file plus `src/`/`test(s)/` paths),
so this session's fix to that file is committed; the summary that would
otherwise live in `implementation.md` lives in
`docs/issue-866/reports/implementation/resolution.md` instead, a
phase-1-legal path. This PR is a phase-1 delivery (survey, proposal,
hunt records, resolution write-up) plus the one hook fix the mechanical
gate does not block — not a phase-2 delivery — and its body carries a
plain `#866` reference, no `Closes`.

# Proposal — issue #866, implementation

## Request

Issue #866: `origin/main` is red — `tests/test_spec_index.py::t_baseline_repo_passes`
fails because PR #863 (`issue-857`) added 22 lines to `docs/handbooks/setup.md`
without regenerating `docs/specs/reconciled-index.md` in the same change, and
`on-the-record/hooks/spec-index-preflight.sh` — the `PreToolUse` gate that
exists specifically to catch this — didn't stop it. Two things are asked:
(1) regenerate the index, unconditionally, and decide whether the
regeneration touches anything "Resolved ambiguities" needs to say; (2)
reproduce — not statically reason about — why the gate didn't fire, and
either fix it with a test, or record the reproduction and reasoning if it
can't be fixed.

## Constraints

- `spawn.py` and `docs/handbooks/setup.md` are not touched (out of scope
  per the issue — PR #863's `MUSTER_STATE_ROOT` change already landed and
  is not being reverted).
- `on-the-record/hooks/retry-loop-bound.sh` and its test are not touched
  (concurrent issue-846 session owns that file).
- `on-the-record/hooks/pr-preflight.sh` is not touched (separate issue
  #854, under investigation elsewhere).
- The full `gates/ tests/ on-the-record/hooks/` suite must show no new
  failures versus `origin/main`, compared via isolated worktrees (this
  repo's own `t_rulebook_version_is_recorded` fails against a dirty
  working tree, so a direct in-place run is not a valid comparison
  method).

## Rationale

Considered fixing `spec-index-preflight.sh` itself — e.g. widening its
matcher, or adding a defensive re-check — on the theory that a gate that
let a real drift through must have a bug. Rejected: the survey's live
reproduction (staging the exact same change-set PR #863 landed, in an
isolated worktree, and running the unmodified hook against it) shows the
hook's own comparison logic denies this exact drift (exit 2), and its
existing 6-case pure-logic unit suite already agrees. There is nothing
wrong with the comparison logic to fix. The actual landing commit
(`502981d`) carries committer `GitHub <noreply@github.com>`, is
GPG-signed, and has a single parent — the signature of a GitHub
server-side squash-merge, not a local `git commit`. A `PreToolUse` hook
only ever sees Bash tool calls a Claude Code session issues; it cannot be
made to see a commit GitHub's own server fabricates during a PR merge.
Editing this script cannot close that gap — the fix that gap would
actually need (a CI required-status-check, or an equivalent server-side
mechanism) is out of scope for this issue and already tracked separately
under #460.

Considered leaving `docs/specs/reconciled-index.md`'s "Resolved
ambiguities" section untouched without checking it, since the issue
frames the regen as "do it unconditionally." Rejected as too shallow: the
issue explicitly asks to *read* whether the change requires an update,
not skip the question. Read in full: PR #863's `setup.md` diff is a pure
addition (two new paragraphs describing `MUSTER_STATE_ROOT`) that neither
edits nor contradicts the file's one existing resolved-ambiguity entry
(ledger storage location) or any other tracked document's claims. No new
entry is needed — recorded as a checked decision, not a default.

## What will be done

1. Run `python3 gates/spec_index.py --update` against
   `docs/specs/reconciled-index.md`, regenerating exactly the one drifted
   row (`docs/handbooks/setup.md`'s hash). No other row changes.
2. Leave "Resolved ambiguities" unedited, per the Rationale's read of
   PR #863's actual diff.
3. Leave `on-the-record/hooks/spec-index-preflight.sh` and its test
   unedited — the survey's reproduction found the gate's own logic
   correct; the actual gap (GitHub server-side merge, outside any
   `PreToolUse` hook's reach) is not fixable at this file. No test is
   added, matching the issue's own acceptance escape hatch for the
   not-fixing branch.
4. Run `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q` in two
   isolated `git worktree` checkouts — one at this branch's tip, one at
   `origin/main` — and diff the failure sets.
5. Write `docs/issue-866/reports/implementation/resolution.md` recording
   the fix, the reproduction, the decision not to edit the hook, and the
   verification transcripts. (Superseded in part — see the Note above
   the Request section: the after-proposal hunt reversed step 3 for
   `spec-index-preflight.sh` itself, and the write landed at
   `resolution.md` rather than `implementation.md` because the latter is
   mechanically approval-gated and no approval exists for this issue.)

## Out of scope

- `spawn.py`, `docs/handbooks/setup.md`, `retry-loop-bound.sh`,
  `pr-preflight.sh` — per Constraints.
- Building CI / a branch-protection required-status-check to close Gap B
  (the structural blind spot this survey found) — tracked separately
  under #460, not this issue.
- Determining why the original branch commit (`ac8156d6`) itself wasn't
  denied locally (Gap A in the survey) — no session transcript exists to
  settle it; recorded as an open unknown, not guessed at with a code
  change.

## How you'll know it worked

- `python3 -m pytest tests/test_spec_index.py -q` passes on this branch.
- The branch-vs-`origin/main` worktree comparison shows the branch's
  failure set is `origin/main`'s failure set minus exactly
  `t_baseline_repo_passes`, with no new failure introduced.
- `docs/issue-866/reports/implementation.md` records why
  `spec-index-preflight.sh` was left unmodified, backed by the survey's
  reproduction.
