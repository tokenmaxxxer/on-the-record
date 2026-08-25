---
id: retire-role-axis-staging
status: active
date: 2026-08-25
subject: issue-2241
---

# Retire the role axis: re-base spawn/board/record on skills

## Status

Active (2026-08-25). Architecture-role decision for issue #2241, an
operator-authored program issue. This record documents the design
decomposition behind the seven-stage proposal set in
`docs/issue-2241/proposals/`; it does not itself land code — each
stage carries its own future implementation issue.

**Disposition**: this decision's scope intersects two frozen decisions
in this registry — `reaffirms single-skill-axis` and `reaffirms
single-enforcement-surface`. See "Frozen-decision disposition" below.

## Context

Issue #2241's own body (operator decision, 2026-08-25) identifies that
the `role` string in this repo's spawn/board/record system does four
unrelated jobs at once: (a) preventing two sessions from duplicating
work on the same issue, (b) isolating which record files a session may
write, (c) tagging that an independent verification check happened, and
(d) naming a git branch. Retiring role as an identity axis (per
`docs/issue-1758/proposals/role-skill-resolution.md`'s stated phase-5
commitment, executed in part by `docs/issue-1955/proposals/retire-role-source-allowlist.md`)
requires deciding, for each job, whether it needs a sub-key of its own
and — if so — what that sub-key is, since a `skill` name is not unique
per session the way `role` was (two sessions can legitimately mount the
same skill on one issue).

## Decision drivers

- Collision safety (job a) must not regress when role stops being a
  unique-per-session key.
- Append-only audit integrity: a record's authorship must stay
  attributable even under concurrent writers (job b).
- Record-kind (job c) must keep preventing self-verification — the
  same actor providing both the artifact and its independent check.
- Staged landability against real in-flight branches — `gh pr list
  --state open` returned 4 open PRs at survey time (all
  `issue-<n>/implementation`), not the 15 the issue text estimated;
  whatever the count is at each stage's own build time, that stage
  must state what happens to branches already using the old naming.
- No reintroduction of a role-shaped static enum under a new name
  (frozen decision `single-skill-axis`).
- Enforcement stays core-only; no skill-side hooks (frozen decision
  `single-enforcement-surface`).

## Considered options

### Option A — Decompose into four independently-owned concepts (chosen)

An issue-scoped **lease** owns job (a) alone; an append-only **author
identity** field inside each record owns job (b) alone; a **record-kind**
tag owns job (c) alone; **skill** (already the sole capability axis per
`single-skill-axis`) continues to own guidance selection and, combined
with the lease, supplies job (d)'s branch disambiguator. Each concept
changes independently and is proven (stage 1) before anything is made
to depend on it (stages 3-6).

### Option B — Rename `role` to `skill` in-place, keep one axis

Swap the `<role>` path segment for `<skill>` everywhere it appears
today (branch names, record paths, the observer-role tuple) without
introducing lease/author-identity/record-kind as separate concepts.
**Rejected**: a skill is not unique per session, so it cannot safely
serve as the concurrency key or the write-isolation key the way role
did — issue #2241's own text calls this out directly: "swapping
`<role>` for `<skill>` in paths does not carry over the collision
safety... a skill is not unique per session." This option is a rename
of the coupling, not a removal of it.

### Option C — Stop at #1955's scope (guidance-source only)

Leave role identity fully in place everywhere except the
already-completed guidance-source resolution path. **Rejected**: per
this survey, `#1955`'s own out-of-scope note already anticipates this
exact remaining surface ("any change to which skills map to which
role... not the skill-repo guidance mapping already in effect"); stopping
here permanently pins branch-naming, write-isolation, and observer
verification to a 43-name static enum `#1758` already committed to
retiring in its phase 5, and blocks any future skill-composition
flexibility (an issue may eventually want more than one skill mounted
per session, which a role-shaped axis cannot represent).

### Option D — Merge lease and author-identity into one field

A single `actor` object carrying both a renewable lease token and the
identity that authored the record. **Rejected**: a lease is
TTL-scoped, renewable, and expected to expire and be reclaimed
(`roster.py`'s existing `lease_expires_at`/`lease_progress` fields);
author identity must be permanent and append-only once a record entry
exists, or the audit trail loses integrity. Conflating them forces one
invariant to break — either identity becomes mutable (breaks the
append-only guarantee) or the lease becomes immutable (breaks renewal
and expiry-driven requeue). This is a stamp-coupling shape (passing one
merged structure when a lease-renewal caller and an audit-read caller
each need only their own field) that decomposing into two fields avoids.

### Option E — Big-bang cutover in one PR

Land the naming change, the write-scope rewrite, and the observer
record-kind rewrite together, then delete `roles/*.json` in the same
unit. **Rejected**: issue #2241's own text states that `merge_gate`'s
role-matching hardcode is exactly what jammed merges in incident
#2233 and fed the #2238 runaway; touching that logic before the other
new concepts are stable and proven reproduces both failures. A staged,
independently-landable rollout (Strangler Fig mechanics — a
transparent-proxy/dual-scheme period before a hard cutover, per this
role's scout brief) is chosen instead, with the observer-pair rewrite
placed deliberately last (stage 5) and deletion placed after it
(stage 6).

## Decision outcome

Option A. Four concepts, seven independently-landable stages (0-6, per
`docs/issue-2241/proposals/`), each with its own gate and rollback.
Stage 5 (observer pair onto record-kind) is ordered last-but-one and
stage 6 (deletion) last, specifically to avoid reproducing incidents
#2233/#2238.

## Consequences

- A future session building any of stages 0-6 has an independently
  scoped, independently landable unit with its own write set — no
  stage's implementation blocks on another stage's PR merging first,
  except where a stage's own proposal states a hard dependency (stage
  3 depends on stage 1's author-identity field existing; stage 5
  depends on stage 1's record-kind field existing; stage 6 depends on
  stages 0-5 all being landed).
- `roster.py`'s existing TTL lease mechanism (issue #2101) is reused
  and generalized, not reinvented — its fields, renewal, and
  detector-free requeue path carry over; only the second half of its
  key (today `role`) changes meaning.
- `board-gate.sh` (stage 3) and its `EXTRA_SUBTREE` (stage 6) live in a
  separate mounted repository (`tokenmaxxxer/tokenmaxxxer-core`), so
  those two stages each require a PR against that repository in
  addition to any change in this one.

## Frozen-decision disposition

reaffirms single-skill-axis — issue #2241 retires role as a distinct
architectural primitive entirely (Option A's chosen shape has no role
manifest, no role registry, and no role/skill type split survives past
stage 6); it does not reintroduce role under a new name, which is
exactly what Option B (rejected above) would have done.

reaffirms single-enforcement-surface — every stage's constraint list
inherits issue #2241's own "Enforcement stays core-only... skills carry
guidance, never hooks"; stage 3's board-gate rewrite and stage 5's
merge-gate rewrite both land in core (this repo's `gates/` or the
mounted core-hooks repo), never as skill-repository hooks.

## Empty-state note

A target repo that has never used roles (fresh install, post-stage-6):
`spawn.py` carries no `ROLES` constant; `roles/` and `roles/specs/` do
not exist; every session mounts one or more skills directly; branch
names are `issue-<n>/<skill-or-lease-disambiguator>`; every record
frontmatter carries `author:` (append-only) and `kind:` (record-kind)
with no `role:` key; `merge_gate.required_verification_missing()` reads
record-kind presence, naming no role string anywhere. Full detail in
`docs/issue-2241/proposals/2026-08-25-stage-6-role-deletion.md`'s "What
will be done" section.
