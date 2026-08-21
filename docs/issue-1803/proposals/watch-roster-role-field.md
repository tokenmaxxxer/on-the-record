---
status: proposed
files:
  - spawn.py
  - test/test_convention_equivalence.py
  - test/test_roster_role_field.py
---

## Request

#1803 (skill-axis phase 5, frozen migration order entry 2): stop deriving
`role` in watch/roster by splitting the roster/workspace-index string key
(`issue-N/role`, `repo/issue-N/role`); carry an explicit `role` field in
the entry instead, dual-written alongside the unchanged key. The three
key-split read sites the #1792 survey named switch to reading the field
when present, falling back to the key split for legacy entries — behavior
identical for both entry shapes. `test/test_convention_equivalence.py`
stays green with additions only (no edits/deletions to existing golden
cases); a new `test/test_roster_role_field.py` covers dual-write,
field-read, legacy-fallback, and key byte-identity.

## Constraints

- The string key format is unchanged byte-for-byte — same construction,
  same value, for both ROSTER and workspace-index entries.
- `test/test_convention_equivalence.py`'s existing golden cases may not
  be edited or deleted (requirement 3) — new cases only.
- Only the three read sites named in the survey
  (`_live_roster_matches`, `_roster_fallback_entry`,
  `_lookup_workspace_entry`) change read behavior; no other consumer
  (branch names, APPROVE grammar, approval-gate, rsb) is touched
  (non-goal 5).
- Zero convention bugs (operator hard constraint): the field-read and
  key-split paths must produce identical `role` values for every case the
  new test file covers, including the legacy (no-field) empty state.

## Rationale

Two ways to land the explicit field were considered:

1. **Chosen: dual-write field on write, field-with-fallback on read.**
   Every write site continues writing the same key and additionally sets
   `entry["role"] = role`; every read site tries `entry.get("role")`
   first and falls back to the existing key-split logic only when the
   field is absent (legacy entries written before this change, or any
   entry surviving a process restart mid-rollout). This is exactly what
   requirement 1-2 specifies and what the frozen #1792 migration-order
   entry commits to.

2. **Rejected: one-shot migration that rewrites all existing roster/
   workspace-index entries to add the field on next load** (analogous to
   `_workspace_index_load`'s existing legacy-key migration at
   `spawn.py:4516-4533`, which already rewrites `issue-N/role` keys to
   `repo/issue-N/role` in place on load). Rejected because ROSTER and the
   workspace index are ephemeral, short-lived process-tracking stores
   (entries represent live or recently-live sessions, not durable
   history) — a load-time rewrite adds a second in-place mutation path to
   maintain, risks colliding with the existing key-migration rewrite in
   the same function, and buys nothing requirement 2 doesn't already get
   more simply from a get-with-fallback: once every *new* write carries
   the field, old entries age out on their own (sessions end, roster
   entries get removed via `roster_remove`) without any rewrite ever
   running. The dual-write + fallback approach is also what requirement
   2's exact wording asks for ("read the `role` field when present,
   falling back to the key split for legacy entries"), so it needs no
   deviation to justify.

## What will be done

1. **`spawn.py:4553-4589` (`_workspace_index_put`)** — add `role` to the
   entry dict written to the workspace index: `entry = {"work": work,
   "log": log, "role": role}` (role is already a required parameter of
   this function, only used today to build the key). Key construction is
   unchanged.
2. **`spawn.py:8289-8390` (`roster_register` call sites)** — already
   write `role` into ROSTER entries (survey finding: ROSTER is already
   migrated); no change needed here.
3. **`spawn.py:4695-4706` (`_live_roster_matches`)** — read
   `role = v.get("role")` from the workspace-index match `v` first;
   fall back to `k.rsplit("/", 1)[1]` only if the field is absent (or
   falsy).
4. **`spawn.py:4726-4756` (`_roster_fallback_entry`)** — in the
   candidate-scan branch (no `role` given), read `found_role =
   e.get("role")` from each ROSTER entry `e` first; fall back to the
   `re.match(rf"^issue-{issue}/([^/]+)$", k)` extraction only when the
   field is absent.
5. **`spawn.py:4780-4811` (`_lookup_workspace_entry`)** — the matching
   branches that build `matches`/`key` by membership (`endswith`,
   `f"/issue-{issue}/" in k`) are unchanged (they don't extract `role`,
   they test key membership against an already-known `role` or scan for
   `issue` only). `_ambiguous_watch_exit`'s candidate-list construction
   (`spawn.py:4705-4713`, called from within this region) switches its
   `roles = [...]` comprehension to prefer each match's `v.get("role")`
   before falling back to `k.rsplit("/", 1)[1]` — cosmetic (error text)
   but kept consistent with the other three sites for the same
   zero-convention-bug reason.
6. **`test/test_convention_equivalence.py`** — add new cases to
   `WatchRosterEquivalenceTest` (additions only, existing three cases
   untouched) covering: field-present entries produce the same `role` as
   the legacy split would have for the same key, for all three
   read sites.
7. **`test/test_roster_role_field.py`** (new file) — dedicated coverage
   per requirement 4: dual-write shape (workspace-index entries written
   via `_workspace_index_put` carry `role`), field-read path (all three
   read sites prefer the field when present), legacy-fallback path (all
   three read sites reproduce today's split-derived `role` when the
   field is absent — explicit empty-state case per acceptance §2), and
   byte-identity of the string key before/after (same key value for the
   same spawn, asserted by direct string comparison, not just structural
   equality).

## Out of scope

- Branch names, APPROVE grammar, approval-gate, rsb status board
  (migration-order entries 3-6) — untouched, per non-goal 5.
- Rewriting or migrating existing on-disk ROSTER/workspace-index entries
  in place — dual-write is forward-only; legacy entries age out via
  fallback (see Rationale).
- Any change to the workspace-index legacy key-shape migration already
  present in `_workspace_index_load` (`spawn.py:4516-4533`) — orthogonal
  (that migration rewrites the key's shape, not the entry's fields).

## Accumulation

This change adds one field (`role`) to one write site
(`_workspace_index_put`) and a get-with-fallback read at three call
sites — it is not an inline-subprocess or repeated-file-edit pattern.
If a future phase-5 sub-issue needed to add another explicit field the
same way (e.g. for a different derived value some other consumer splits
out of the key), the shape to reuse is this same one: one field on the
existing entry dict, one `.get(field) or <legacy derivation>` per read
site — no new shared helper is warranted at N=1 field; if a third
dual-written field appears on these same entries, the get-with-fallback
snippet (`v.get(field, <split-fallback>)`) should be factored into a
small shared helper (e.g. `_entry_field(entry, key, field, fallback_fn)`)
at that point rather than copy-pasted a third time.

## How you'll know it worked

- `python3 -m pytest test/test_convention_equivalence.py -q` passes, and
  `git diff` over that file shows only additions (no removed/modified
  lines among the pre-existing golden cases) — acceptance §1.
- `python3 -m pytest test/test_roster_role_field.py -q` passes, with an
  explicit legacy-only-entry case asserting identical behavior to today
  via the fallback path, and a case asserting the string key is
  byte-identical before/after the same spawn — acceptance §2.
