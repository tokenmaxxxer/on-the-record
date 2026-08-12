---
status: proposed
files:
  - gates/roles_due.py
  - gates/test_roles_due.py
  - roles/specs/defect-verification.spec.json
  - docs/issue-1102/decisions/2026-08-12-obligation-trigger-predicate.md
  - .gitignore
---

## Request

Add a `roles/specs/*.spec.json` trigger shape so `roles_due.py` surfaces
the mapped specialist role when a landing obligation is failing —
scoped out of a prior PR's proposal as a named follow-up (#1101 step 4
/ Out of scope). Requirement: northpole req#5.

## Constraints

- The obligation-writer module this trigger would eventually key on
  does not exist yet (survey: no `landing_obligation.py`, no
  `.landing-obligations/` anywhere in the tree) — this proposal cannot
  import functions from a module that isn't built.
- Acceptance requires: a failing obligation surfaces the mapped role as
  due; a resolved obligation does not; no obligations present means no
  output at all (empty state).
- validity-consult-skip: trivial (issue label) — no external consult
  needed for this shape.

## Rationale

**Chosen approach:** read obligation record files directly from a
`.landing-obligations/` directory as a new, independent trigger
predicate (`obligation_status`, a list of statuses that count as a
match) inside `_trigger_matches`, alongside the existing
`path_patterns`/`content_patterns` predicates. `defect-verification`
gets the trigger, since its board_condition is the closest existing
match for "a landing that was supposed to pass verification came back
disputed."

**Alternative considered and rejected:** wait for
`gates/landing_obligation.py` to be built first and call its exported
helpers (e.g. a hypothetical `list_open_obligations`) from
`roles_due.py`, coupling this trigger's predicate directly to that
module's API. Rejected because that module is unbuilt phase-2 work
behind its own unapproved proposal — blocking this issue on it would
leave #1102 undeliverable for an indefinite time, and would make
`roles_due.py` depend on an internal function signature that is not
yet frozen. Reading the obligation JSON file shape directly (the shape
already documented in #1101's proposal: `{status, pr, sha, issue, role,
opened_at}`) keeps `roles_due.py`'s dependency on a stable *file
format*, the same way it already depends on `roles/specs/*.spec.json`'s
file format rather than importing another module's Python. When
`landing_obligation.py` is eventually built, it only has to keep
writing that same file shape — no coupling in either direction.

## What will be done

1. `gates/roles_due.py`:
   - `_trigger_matches` gains a first check: when `trigger.get("obligation_status")`
     is a non-empty list, scan `.landing-obligations/*.json` for a
     record whose `status` is in that list and whose `issue` field
     matches the current subject (`issue-<n>` derived from the branch,
     already computed by `roles_due()`); on a match, return the same
     `(reason, matched_path)` shape the path/content predicates already
     return, so the existing `record_absent_for` / commit-ancestry
     "does the record cover this" suppression logic in `roles_due()`
     applies unchanged.
   - A spec with only `obligation_status` (no path/content patterns)
     still counts as `trigger`-carrying for `load_triggered_specs`
     (unchanged — that function already accepts any non-empty trigger
     dict).
   - No `.landing-obligations/` directory, or no matching-status
     record, returns no match — the acceptance's empty-state
     requirement, satisfied by the same "no match -> not due" path
     every other predicate already uses.

2. `gates/test_roles_due.py` gains three cases:
   - a `.landing-obligations/*.json` record with `status: "failing"`
     for the branch's subject surfaces the mapped role as due.
   - the same record with `status: "resolved"` does not surface it.
   - no `.landing-obligations/` directory at all (with the trigger
     spec present) surfaces nothing — empty state.

3. `roles/specs/defect-verification.spec.json`'s `use_when.trigger`
   gains `"obligation_status": ["failing"]` plus
   `"record_absent_for": "defect-verification"` (reusing the existing
   `record_absent_for` field, no new field needed there).

4. One ADR at `docs/issue-1102/decisions/2026-08-12-obligation-trigger-predicate.md`
   recording the file-format-coupling decision from Rationale above
   (context/decision/consequences/alternatives).

5. `.gitignore` gains a `.landing-obligations/` entry (alongside the
   existing `.reexecution/` line), so obligation record files stay
   untracked worktree state — the same convention `.reexecution/`
   already established — which is what the `_last_commit_hash`/
   `_commit_at_or_after` suppression logic in `roles_due()` depends on
   to treat an obligation file as "uncommitted, fresh" rather than
   silently changing behavior if one were ever committed.

## Out of scope

- Building `gates/landing_obligation.py` itself or the
  `.landing-obligations/` writer (#1101's own follow-up, separate
  proposal).
- The `post-landing-obligation-gate.sh` hook and any other piece of
  #1098's proposal.
- Wiring any other role spec's trigger beyond `defect-verification`.

## How you'll know it worked

- `python3 gates/test_roles_due.py` — all cases pass, including the
  three new ones, with pasted output in the phase-2 record.

## Open findings (after-proposal hunt)

canonical: docs/issue-1102/reports/implementation/hunt-roles-due-obligation-trigger.md
The hunt (stance 4, after-proposal) found that the original write set
omitted `.gitignore`: the obligation-status predicate's suppression
logic depends on `.landing-obligations/*.json` staying uncommitted
worktree state, and nothing enforced that. Resolved in this revision
by adding `.gitignore` to the write set and item 5 above, mirroring the
existing `.reexecution/` entry.

## Accumulation

This adds `obligation_status` as one more entry in `_trigger_matches`'s
small predicate vocabulary (now: `path_patterns`, `content_patterns`,
`obligation_status`) and one more `roles/specs/*.spec.json` file
(`defect-verification.spec.json`) gaining a `use_when.trigger` block —
the same one-block-per-file shape `security-threat-model.spec.json`
already established under issue #896. If N more role specs later need
an obligation-status trigger, each is the same one `trigger` block
addition to its own spec file — no new code path, since
`_trigger_matches`/`roles_due()` already read the predicate generically
per spec. If a third distinct predicate kind (beyond
path/content/obligation) is proposed later, that is the point to
consider a small predicate-dispatch table in `_trigger_matches` instead
of a third `if trigger.get(...)` branch — not before, since two
existing predicate kinds is not yet the field's own N>1-with-evidence
bar this repo's `accumulation.py` gate applies.
