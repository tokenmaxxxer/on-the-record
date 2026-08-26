---
status: proposed
subject: issue-2241
stage: 3
files:
  - tokenmaxxxer-core:core/hooks/board-gate.sh
  - tokenmaxxxer-core:core/hooks/test_board_gate.py
  - docs/issue-2286/reports/implementation/board-gate-r5-migration.md
---

# Stage 3 — rewrite board-gate write-scope onto author identity

## Request

Rewrite `board-gate.sh`'s R5 (foreign-record ownership) check to key
off the append-only `author:` field stage 1 introduces, instead of
matching the writing session's role against the record's filename.

## Constraints

- **Cross-repo**: `board-gate.sh` lives in `tokenmaxxxer/tokenmaxxxer-core`
  (survey finding 2), not this repo — this stage's write set is a PR
  against that separate repository, with its own review/merge cycle,
  landed independently of any same-issue PR in this repo. The `files:`
  list above marks this with a `tokenmaxxxer-core:` prefix to say so
  explicitly.
- Frozen decision `single-enforcement-surface`: the rewritten check
  stays in core (this hook), never moves to a skill-repository hook.
- Record contract must not break mid-flight: a record written before
  this stage lands (carrying only `role:`, no `author:`) must still be
  readable and correctly attributed after this stage lands.
- Requires stage 1 landed first (the `author:` field must exist on
  records for R5 to key off it).

## Rationale

Chosen: R5 keys off `author:` — the field that answers "who wrote the
content already in this file" — rather than off the lease (the field
that answers "who currently holds the right to work on this issue").
Rejected alternative: key R5 off the lease's issue-scope alone,
dropping role and not introducing `author:` as a separate field.
Rejected because a lease's job is concurrency (issue #2241's job (a)),
not write-isolation (job (b)) — collapsing them back into one key
reintroduces the exact overloading this whole issue retires. Two
sessions can legitimately hold sequential leases on one issue (one
expires, another acquires it), and a foreign-write check needs to know
who *authored* the record's existing content, not who currently holds
the lease at write time — those are different questions with different
answers at different moments.

## What will be done

- `board-gate.sh` R5: for a record carrying an `author:` field, the
  writing session may append to a record whose `author:` matches its
  own author identity, or write a brand-new record/subtree it
  authors itself; it may never edit an existing entry authored by a
  different identity (append-only, not read-only-foreign — a session
  may still add new content to a record it doesn't own the header of,
  provided it does not alter another author's existing lines).
- For a record with no `author:` field (pre-stage-1, mid-flight), R5
  falls back to today's role-filename match unchanged — no legacy
  record becomes suddenly unwritable.
- `docs/issue-2286/reports/implementation/board-gate-r5-migration.md`
  states the exact fallback rule above and the date after which every
  new record is expected to carry `author:` (tied to stage 1's landing
  date, not a fixed calendar date). Named under the delivering child
  issue's own tree, not this program issue's tree — `board-gate.sh`
  R4 (branch/tree scope) and R5 (role/report-subtree ownership) both
  forbid a session delivering one child issue from writing into a
  different issue's `docs/issue-2241/` tree or into another role's
  `reports/architecture/` subtree; see issue #2412 for the full
  reasoning. Already landed at this path. (Path correction per
  issue #2412; pure post-landing path fix, no open design decision —
  survey skipped.)
- `EXTRA_SUBTREE`'s stale `"feasibility"`/`"ops"` keys (survey finding
  2) are corrected to match `spawn.py`'s current role names in the same
  PR, since this stage already touches the surrounding logic.

## Out of scope

- Anything about branch naming (stage 4) or the observer-role hardcode
  in `merge_gate.py`/`spawn_on_pr.py` (stage 5) — R5 and R4 are
  distinct rules; this stage touches only R5.
- Deleting the role-filename fallback path — it stays until every
  record predating stage 1 has aged out or been migrated, which this
  stage does not force.

## How you'll know it worked

- `tokenmaxxxer-core:core/hooks/test_board_gate.py` gains cases: an
  `author:`-bearing record accepts an append from its own author,
  refuses an edit from a different author, and a legacy
  `author:`-less record still enforces the old role-filename rule
  unchanged.
- A live write from this session (architecture role, this issue) to
  its own record continues to succeed against the rewritten R5.
- `EXTRA_SUBTREE`'s corrected keys match `spawn.py`'s current `ROLES`
  tuple (`grep`-verified in the test).

## Rollback

Revert the `board-gate.sh` PR in the core repo; the fallback path means
every record written during this stage's brief life stays readable
under the reverted, role-filename-only R5 as long as it also still
carries a role-matching filename (true for every record this stage's
own tests produce).

## Accumulation

This stage touches `board-gate.sh`, a file outside this repo's own
accumulation-check scope; within this repo, only the
`board-gate-r5-migration.md` doc is added (docs-only, not a
subprocess/gh-call-bearing `.py` file). If R5's fallback logic needed N
more record-shape special cases over time, each should extend the one
`author:`-presence branch this stage introduces rather than adding N
parallel filename-matching branches — the whole point of this stage is
collapsing that branching onto one field.
