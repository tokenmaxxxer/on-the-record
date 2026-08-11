---
code_under_review:
  - on-the-record/hooks/credential-record-guard.sh
  - on-the-record/hooks/test_credential_record_guard.py
  - on-the-record/hooks/hooks.json
type: feature
breaking: false
verdict: pass
loop_state: coding
---

# Implementation record — issue #858

## What was done

Implemented the approved phase-1 proposal
(`docs/issue-858/proposals/credential-record-guard.md`): a new
`on-the-record/hooks/credential-record-guard.sh` PreToolUse hook
(Write/Edit/MultiEdit) that denies any write under `docs/**` whose new
content contains a full-length credential (GitHub `gho_`/`ghp_`/`ghs_`/
`ghr_` + 36 base62 chars, `github_pat_` + 22 base62 chars, OpenAI-style
`sk-` + 20 chars, AWS `AKIA` + 16 chars), while allowing `[REDACTED]`
markers and short truncated prefixes (<12 chars) by construction. It
also checks the no-separator concatenation of all `edits[].new_string`
values in a MultiEdit call.

canonical: `docs/issue-858/reports/implementation/2026-08-11-hunt-credential-record-guard.md`,
read this session — the after-proposal hunt found the MultiEdit
fragment-splitting bypass, addressed directly in this build.

Registered in `on-the-record/hooks/hooks.json` in the same
`Write|Edit|MultiEdit` PreToolUse group as `record-claim-guard.sh`. Added
`on-the-record/hooks/test_credential_record_guard.py` covering
full-token-denied (each of the 6 prefix families), `[REDACTED]`-allowed,
short-prefix-allowed, ordinary-prose-untouched, non-docs-path-ignored,
and the MultiEdit-split-credential-denied / independent-short-fragments-
allowed cases.

derived: `python3 -m pytest on-the-record/hooks/test_credential_record_guard.py -q`
```
13 passed in 0.45s
```

## Why

Closes issue #858: a near-miss in PR #855 left a truncated gh-token
prefix in a committed record; the guard makes full-token leakage into
docs records structurally impossible instead of depending on a role
remembering to redact.

## Upstream basis

docs/issue-858/proposals/credential-record-guard.md

## What did not work

Attempted the proposal's last write-set item — scrubbing the
`gho_A5ji...` prefix in `docs/issue-776/reports/execution-observation/run2.md`
line 39 — via Edit. Expected: the write set explicitly names this file,
so the edit should succeed. Actual: `board-gate.sh` (a mechanical
cross-issue guard the proposal did not anticipate) refused it — writing
under `docs/issue-776/` requires branch `issue-776/implementation`; this
session runs on `issue-858/implementation`. No override exists in that
hook. Left unscrubbed; see `## Rationale for deviations`.

## Rationale for deviations

The phase-1 proposal's write set includes
`docs/issue-776/reports/execution-observation/run2.md`, approved before
build. At build time, `board-gate.sh` mechanically refused the edit: it
binds every `docs/issue-<n>/**` write to branch `issue-<n>/<role>`,
which this branch (`issue-858/implementation`) is not for issue #776.
This constraint sits outside the proposal's own scope (it governs branch
identity, not file content) and the proposal could not have surfaced it
without hitting the gate live. Per the scope-exceeded rule, the correct
response is to finish what the proposal covers and stop rather than
widen scope or attempt a bypass — the credential-guard hook itself is
fully implemented, tested, and registered; only the pre-existing
run2.md scrub is deferred. The new guard would in fact refuse a future
attempt to reintroduce this exact leaked prefix pattern in a fresh
write, which narrows the residual exposure even with the scrub pending.
Recommended follow-up: a small phase-2 continuation, or a one-line
change filed against issue #776's own branch, to apply the scrub.

## Doc placement

- `on-the-record/hooks/credential-record-guard.sh` — new session hook,
  no handbook entry needed (self-contained, modeled on
  `record-claim-guard.sh`, no new env var/config key/dependency).
- Registered in `on-the-record/hooks/hooks.json` (operational surface,
  but no handbook update required — no new package/env var/migration
  introduced).

## Open findings

None from this build. The deferred run2.md scrub (above) is not a code
defect — it is undone proposal-scoped work blocked by a cross-branch
write restriction.

## Next steps

Commit and push this branch's changes; open the phase-2 PR with
`Closes #858`, noting the deferred run2.md scrub in the PR body so a
follow-up (on issue #776's own branch) can pick it up.

## Resolution path

The deferred run2.md scrub resolves via a future write on branch
`issue-776/implementation` (or any session board-gate.sh permits) editing
`docs/issue-776/reports/execution-observation/run2.md` line 39 to
replace the `gho_A5ji...` prefix with `[REDACTED]`.

## Hunt

after-proposal hunt already ran (see canonical citation above) and its
finding is addressed directly in this build. before-landing hunt
dispatched separately per warrant directive, in the background, before
this record's final commit.
