---
status: proposed
files:
  - gates/ci.py
  - spawn.py
  - test/test_convention_equivalence.py
  - test/test_approval_role_field.py
---

## Request

Issue #1818: today the APPROVE check builds the exact-match needle
`"APPROVE issue-<n>/<role>"` from the issue/role pair and re-scans
issue comments for it on every call (`_approved_roles_on_issue`,
`gates/ci.py:189`). Introduce a structured approval record carrying
`{issue, role, actor, timestamp}`, dual-written alongside the existing
token comment (the comment itself is unchanged and keeps being
accepted), and have the python needle consumer read the record when
present, falling back to the exact-needle comment scan otherwise —
identical outcomes on both paths. `approval-gate.sh` (entry 5) and the
APPROVE grammar itself are out of scope.

## Constraints

- `test/test_convention_equivalence.py` (29 tests after #1814) stays
  green with additions only — no edits to existing golden cases.
- Dual-read: structured record preferred per role, exact-needle scan
  fallback identical to today when the record is absent or does not
  yet cover a given role (fresh-workspace case, and the case where a
  new approval landed since the record was last written).
- The token comment (`APPROVE issue-<n>/<role>`, and the `VIA
  DELEGATION` variant) keeps working unchanged; nothing stops emitting
  or accepting it.
- New `test/test_approval_role_field.py` covers dual-write shape,
  field-read, fallback, and the legacy token-only case (byte-identical
  to today).
- Non-goals (explicit in the issue): `approval-gate.sh`, rsb, removing
  or changing the token grammar, branch names.

## Rationale

Three carriers were on the table (survey.md): a workspace-local file
under the established `.git/gh-read-cache/` convention, a
repo-committed file, and a second machine-readable issue comment
auto-posted alongside the human's token comment.

The **repo-committed file** was rejected: every consumer of
`_approved_roles_on_issue` here is a *read* path (`spawn.py`'s phase
checks, `landing_readiness.py`, `spawn_on_pr.py`) — none of them is
already producing a commit at the point it would need to write the
record. Making a read path also produce a commit pulls in
role-handoff contract v3 s13's one-subject-one-commit trailer
requirement for no reachability gain: the survey found every consumer
here already resolves the same workspace root a workspace-local file
would use, so committing buys nothing a cache write doesn't already
give.

A **second, bot-posted issue comment** was rejected: nothing in this
repo posts a comment as a side effect of reading approval state today
(survey.md: `grep` for `gh issue comment`/`gh pr review`/`--approve`
across `spawn.py`/`gates/ci.py` finds no matches) — only humans post
the token comment. Adding this would require giving a read-only funnel
a new write-scope network dependency (`gh issue comment`) it does not
have today, for a record that a plain cache file already gives us
without any network write.

The chosen carrier is a **workspace-local JSON file under
`.git/gh-read-cache/`**, sibling to the existing
`_etag_cache_path`/`issue-{number}-comments.json` convention
(`spawn.py:1327`) that this exact call site already uses for exactly
this kind of GH-API-derived data. `_approved_roles_on_issue` already
receives the workspace root (`repo: Path`) that convention keys off of,
so no new dependency class is introduced — this is the #1814
reachability method applied here: unlike #1814's four sites sharing no
single medium, this issue has exactly one python funnel-site
(`_approved_roles_on_issue`, `gates/ci.py:189`) already sitting on top
of the reachable medium.

The dual-write is a **write-through cache of the needle scan's own
result**, not an independently-computed value: on every call,
`_approved_roles_on_issue` scans comments as it does today, and any
role it finds approved (with the approving login and the comment's
`createdAt`) is persisted into the record file. The next call reads
the record first; for any role the record already covers, the record
answer and a fresh needle scan are the same answer by construction
(it was populated FROM that scan), so requirement 2's "identical
outcomes on both paths" holds trivially rather than needing to be
proven by parallel maintenance of two independent implementations. For
a role the record does not yet cover (new approval, fresh workspace,
record file absent/corrupt), the function falls back to (in fact,
still runs) the live comment scan — the legacy path is simply today's
unmodified code, so the "token-only issue resolves byte-identically"
acceptance case is true by construction, not by a second parallel
implementation that could drift.

Rejected alternative: treating the record as *authoritative* and
skipping the comment scan whenever a record file exists (an
independently-trusted read, not a cache) — rejected because that
would make the record able to go stale relative to new approvals
(survey.md open finding) and would turn "identical outcomes on both
paths" into a claim that needs proving per-role over time instead of
holding by construction; the write-through-cache design avoids that
failure mode entirely by never treating record-presence as a reason to
stop reading comments for roles the record hasn't seen.

## Accumulation

This adds one cache file per issue (`.git/gh-read-cache/issue-<n>-approvals.json`,
sibling to the existing comments cache), read/written from the single
funnel function. Because every python consumer already goes through
that one function, no per-consumer duplication is introduced — unlike
#1814's four independent regex sites, there is nothing here to
accumulate across call sites.

## What will be done

1. `gates/ci.py`: `_approved_roles_on_issue` gains a read of
   `.git/gh-read-cache/issue-<n>-approvals.json` before the comment
   scan; roles found there are unioned into the result. After the
   (always-run) comment scan, any newly-found `{role: {actor,
   timestamp}}` not already in the record is written back
   (write-through). Comment-scan behavior and its return value are
   unchanged; the record read/write is additive.
2. `spawn.py`: no read-path change (all `_ci._approved_roles_on_issue`
   callers keep calling the same function signature). If a helper for
   the record file path/shape is needed it lives next to
   `_etag_cache_path` for symmetry, imported by `gates/ci.py`.
3. `test/test_convention_equivalence.py`: additions only — new cases
   under the `approve_grammar` consumer asserting record-present and
   record-absent paths produce identical role output to today's
   comment-scan-only behavior.
4. New `test/test_approval_role_field.py`: dual-write shape (record
   file written after a scan finds an approval, with `actor` and
   `timestamp` populated from the comment), field-read (record
   preferred when present), fallback (record absent/partial ->
   comment scan covers the gap), and the legacy case (issue with only
   token comments, no record file, resolves identically to today).

## Out of scope

`approval-gate.sh` (entry 5's needle match), rsb, changing the APPROVE
token grammar, branch naming — all named non-goals in the issue body,
deferred to later sub-issues.

## How you'll know it worked

- `python3 -m pytest test/test_convention_equivalence.py -q` passes,
  and `git diff` over that file shows additions only (no lines removed
  or altered in existing cases).
- `python3 -m pytest test/test_approval_role_field.py -q` passes,
  including the dedicated case asserting an issue with only legacy
  token comments (no structured record) resolves approvals
  byte-identically to today.
