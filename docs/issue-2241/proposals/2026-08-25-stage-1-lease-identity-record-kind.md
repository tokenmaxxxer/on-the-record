---
status: proposed
subject: issue-2241
stage: 1
files:
  - roster.py
  - spawn.py
  - gates/record_lint.py
  - docs/specs/record-kind-vocabulary.md
  - docs/handbooks/record-contract.md
  - test/test_issue_scoped_lease.py
  - test/test_record_kind_field.py
---

# Stage 1 — land lease, author identity, and record-kind, roles still in place

## Request

Land the three new concepts issue #2241 introduces — an issue-scoped
lease, an append-only author-identity record field, and a record-kind
tag — while every existing role-keyed consumer keeps working unchanged.
Nothing depends on these new concepts yet; this stage only proves they
exist and behave correctly in isolation.

## Constraints

- Frozen decisions `single-skill-axis` and `single-enforcement-surface`
  apply: no new role-shaped primitive, no skill-side enforcement.
- Must not modify `board-gate.sh` (cross-repo, stage 3) or
  `merge_gate.py`'s observer logic (stage 5) — those consume these
  fields later, not now.
- Record contract must not break mid-flight: every record written
  before this stage lands stays valid; the new `author:`/`kind:` fields
  are additive, never required retroactively.

## Rationale

Chosen: generalize `roster.py`'s existing TTL lease (issue #2101 —
`lease_expires_at`, `lease_progress`, `lease_flat_renewals`, the
detector-free requeue path) so its key's second half can be an
issue-scope disambiguator instead of a role name, while every existing
`(issue, role)`-keyed caller keeps working via a compatibility shim.
Rejected alternative: build a brand-new lease primitive from scratch
instead of reusing `roster.py`'s. Rejected because the existing
mechanism (TTL, renewal, flat-progress detection, requeue) already
matches the scouted must-bes for mature lease/claim patterns (angle 1,
`docs/issue-2241/reports/architecture/scout-brief.md`) — reinventing it
would duplicate a proven mechanism for no behavioral gain and would
leave two lease implementations to keep in sync during the staged
rollout.

## What will be done

- `roster.py`: generalize the lease key to accept any
  session-disambiguator string, not only a role name; the existing
  `issue-{issue}/{role}` callers pass their role string through
  unchanged (byte-identical behavior), proving the generalized key
  shape works before anything stops passing role.
- `spawn.py`: every record a session writes gains an `author:` field —
  the session's stable identity (not the lease token, which expires;
  see `docs/decisions/2026-08-25-retire-role-axis-staging.md` Option D
  for why these stay separate fields) — populated once and never
  rewritten by a later session (append-only: a second session appends a
  new record entry or a new file, never edits another session's
  `author:` line).
- `docs/specs/record-kind-vocabulary.md`: formalizes the `kind:` field
  already used ad hoc in ~420 files (survey finding 8) into a spec'd,
  closed vocabulary (e.g. `survey`, `scout-brief`, `adr`,
  `execution-observation`, `conformance-review`, ...), and states that
  every record gains a `kind:` line going forward — additive, not
  retroactively required on existing records.
- `gates/record_lint.py` gains a lint check (advisory at this stage,
  per this repo's DEMOTE convention for new checks — see stage 3/5 for
  when a `kind:`-dependent check becomes load-bearing) that a record's
  `kind:` value is in the closed vocabulary when present.

## Out of scope

- Making `author:` or `kind:` required, or wiring any gate to refuse a
  write for their absence — that would break in-flight records; this
  stage is additive-only.
- Changing what the lease's key currently contains for any existing
  caller (role strings keep flowing through unchanged).
- `board-gate.sh` or `merge_gate.py` changes (stages 3, 5).

## How you'll know it worked

- Existing `roster.py` lease tests pass unmodified (byte-identical
  behavior for role-keyed callers).
- `test/test_issue_scoped_lease.py`: a new lease acquired with a
  non-role disambiguator string renews, expires, and requeues
  identically to a role-keyed one.
- `test/test_record_kind_field.py`: a record carrying `kind:` outside
  the closed vocabulary produces an advisory (not a denial); one inside
  the vocabulary produces no advisory.
- A sample record written this stage carries both `author:` and
  `kind:` alongside its existing `role:` field, and existing readers
  (e.g. `board.py`'s frontmatter parsing) do not error on the new keys.

## Rollback

Revert the four code/spec changes in one commit; `roster.py`'s
generalized key accepts the same role-keyed inputs it always did, so no
in-flight lease or claim is disturbed by rolling back.

## Accumulation

`spawn.py` (13 existing inline subprocess/gh call sites) gains the
`author:`-field write at the same point every record is already
written today — one call site, not a new per-record-kind branch. If
future stages needed N more record-field additions here, each should
extend the same single "stamp this record" helper this stage
introduces rather than adding N separate inline writes; this stage
establishes that helper rather than special-casing inline.
