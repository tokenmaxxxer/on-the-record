---
status: proposed
subject: issue-2241
stage: 4
files:
  - pipeline.py
  - spawn.py
  - board.py
  - roster.py
  - docs/handbooks/branch-naming.md
  - docs/issue-2241/reports/architecture/in-flight-branch-migration.md
  - test/test_branch_naming_dual_scheme.py
---

# Stage 4 — move branch and record naming to skill axis + lease disambiguator

## Request

Move branch derivation (`pipeline.py:893-923` `checkout_issue_branch`)
and record-path derivation (`board.py`'s discovery walk) from
`issue-<n>/<role>` to `issue-<n>/<skill>-<lease-disambiguator>` (or
equivalent), while stating explicitly what happens to branches already
using the old naming.

## Constraints

- **In-flight branches**: `gh pr list --state open` showed 4 open PRs
  at survey time (`docs/issue-2241/reports/architecture/survey.md`,
  section 7), all `issue-<n>/implementation`; the count will differ by
  this stage's actual build time. Per this issue's own constraint, this
  proposal states the handling below rather than deferring it.
- Requires stages 0 (skill-based spawn exists), 1 (lease exists), and 3
  (write-scope no longer keys off branch/role match) landed first.
- Frozen decisions `single-skill-axis` / `single-enforcement-surface`
  apply to the new naming scheme itself (no role-shaped primitive
  reappears in the new branch name) and to where the dual-scheme
  read logic lives (core, not skill-side).

## Rationale

Chosen: a dual-scheme coexistence period — `board.py` and
`pipeline.py` read *both* `issue-<n>/<role>` and
`issue-<n>/<skill>-<disambiguator>` branches for a stated window, new
sessions are spawned only under the new scheme, and old-scheme
branches are left alone (never force-renamed) until each is merged or
closed through its own normal PR lifecycle. Rejected alternative:
force-migrate every in-flight branch to the new naming at cutover time
(rename or re-point existing PRs). Rejected because the constraint this
issue itself states — any stage changing branch/record naming must say
what happens to in-flight branches — is best satisfied by never
touching branches a human is actively pushing to; this scouted pattern
(`docs/issue-2241/reports/architecture/scout-brief.md`, angle 4,
Strangler Fig's transparent-proxy/dual-write seam) is exactly a
dual-read period before a hard cutover, not a flag day that would
orphan or break open PRs mid-review.

## What will be done

- `pipeline.py checkout_issue_branch`: gains a new naming function
  producing `issue-<n>/<skill>-<lease-disambiguator>`; the old
  role-based function stays callable and produces identical output to
  today for any caller still passing a role.
- `board.py`: board discovery walks both naming schemes for the
  duration of the coexistence window and merges results — a record
  under either scheme's path is visible on the board.
- `docs/handbooks/branch-naming.md`: documents both schemes, the
  coexistence window's start (this stage's landing commit) and
  intended end (stage 6, once no old-scheme branch remains open).
- `docs/issue-2241/reports/architecture/in-flight-branch-migration.md`:
  states plainly — every branch open at this stage's landing time keeps
  its `issue-<n>/<role>` name and finishes its lifecycle unchanged
  (reviewed, merged or closed, exactly as today); only newly spawned
  sessions after this stage lands use the new naming; no existing PR is
  renamed, re-pointed, or force-pushed by this stage.
- `roster.py`'s lease key (generalized in stage 1) supplies the
  `<lease-disambiguator>` segment for the new naming scheme.

## Out of scope

- Force-renaming, closing, or re-pointing any currently open PR or
  branch.
- Removing the old-scheme reader path from `board.py`/`pipeline.py` —
  that removal is stage 6's job, once no old-scheme branch remains.
- The observer-role rewrite in `merge_gate.py`/`spawn_on_pr.py`
  (stage 5) — naming and verification-kind matching are independent.

## How you'll know it worked

- `test/test_branch_naming_dual_scheme.py`: a session spawned under the
  new scheme produces a board-visible record; a pre-existing
  role-named branch's record remains board-visible unchanged; both
  appear together in one `board.py` listing.
- A live re-check of `gh pr list --state open` at this stage's landing
  time confirms every open PR still resolves correctly under the
  dual-scheme reader (none becomes invisible to the board).
- No existing open PR's branch name or content changes as a result of
  this stage landing.

## Rollback

Revert the naming/discovery changes; every branch spawned under the new
scheme during this stage's brief life becomes unreadable by the
reverted single-scheme `board.py` until re-applied, but no existing
role-named branch or PR is affected either way — rollback risk is
scoped entirely to sessions spawned after this stage and before a
rollback, not to any pre-existing work.

## Accumulation

`pipeline.py` (12 existing call sites) and `board.py` (18) each gain
one new naming/discovery function, not N per-scheme special cases
scattered through existing call sites — old and new schemes are each
one function, selected once at the top of the relevant call path. If a
third naming scheme were ever needed, the dual-scheme reader
established here is the shared pattern to extend (a list of naming
functions the discovery walk tries in order), not a third parallel
inline branch.
