---
kind: decision
date: 2026-08-12
status: landed
subject: issue-1102
---

# `obligation_status` trigger reads the obligation file shape directly

## Context

`roles/specs/*.spec.json` triggers (`gates/roles_due.py`) already support
`path_patterns`/`content_patterns` as small structured predicates.
Northpole req#5 (#1102) asks for a third predicate that fires when a
landing obligation is `failing`, mapping to the `defect-verification`
role. The obligation-writer module this would eventually key on
(`gates/landing_obligation.py`, `.landing-obligations/` — named in
PR #1101's proposal step 4) does not exist yet in this tree.

## Decision

Add `obligation_status` as a new predicate inside `_trigger_matches` that
reads `.landing-obligations/*.json` record files directly (the
`{status, pr, sha, issue, role, opened_at}` shape already documented in
#1101's proposal), matching on `status` and `issue`. `roles_due.py`
depends on that JSON file shape, not on any function signature from
`landing_obligation.py`.

## Alternatives considered

- **Wait for `landing_obligation.py` and call its exported helpers.**
  Rejected: that module is unbuilt phase-2 work behind its own
  unapproved proposal, so blocking #1102 on it would leave this issue
  undeliverable for an indefinite time, and would couple `roles_due.py`
  to an internal API that is not yet frozen.

## Consequences

- `roles_due.py` keeps its existing pattern of depending on stable file
  formats (`roles/specs/*.spec.json` itself is the precedent) rather than
  importing another module's Python.
- When `landing_obligation.py` is eventually built, it only has to keep
  writing the same record shape — no coupling in either direction.
- `.landing-obligations/` must stay untracked worktree state for the
  existing commit-ancestry suppression logic in `roles_due()` to treat an
  obligation record as fresh; enforced by adding it to `.gitignore`
  alongside the existing `.reexecution/` entry.
