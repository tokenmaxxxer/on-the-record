---
status: proposed
files:
  - docs/specs/northpole.md
  - docs/issue-748/proposals/2026-08-11-northpole-spec.md
---

## Intent

Canonicalize the 7 north-pole requirements the operator stated on
2026-08-11 (quoted verbatim in issue #748) into a single tracked spec file,
so the project's north star lives in the repo instead of only in chat.

## Constraints

- All 7 requirements recorded verbatim-faithful, none invented or dropped.
- Each requirement traces to at least one existing mechanism (hook,
  directive, gate, spawn behavior, or spec) with a name (and file:line
  where knowable), or is explicitly marked `GAP` if nothing serves it yet.
- No `docs/specs/*` write in this change, so no `reconciled-index.md`
  regeneration is required.

## What was done

Surveyed the repo's hooks (`on-the-record/hooks/hooks.json` and its
scripts), gates (`gates/*.py`), and existing specs
(`docs/specs/requirements.md`) for mechanisms serving each of the 7
requirements, then wrote `docs/specs/northpole.md`: one numbered section
per requirement, verbatim quote, and a traceability note naming the
serving mechanism(s). See `docs/specs/northpole.md`'s own "Gaps" section
for the outcome — every requirement matched at least one mechanism.

## Out of scope

- Closing any gap a mechanism only partially covers (noted inline in the
  traceability text, not remediated here).
- The phase-2 record file
  (`docs/issue-748/reports/requirements-engineering.md`) — blocked by
  `approval-gate.sh` pending phase-2 approval; will land once approved.

## How you'll know it worked

`docs/specs/northpole.md` exists, contains all 7 numbered requirements
verbatim-faithful, and each names an existing mechanism or is marked
`GAP` — matching issue #748's Acceptance criteria.

## What did not work

- Attempted to write `docs/issue-748/reports/requirements-engineering.md`
  in this same pass; `approval-gate.sh` refused it as phase-2-shaped
  (needs an `APPROVE issue-748/requirements-engineering` comment from a
  `docs/specs/approvers.md` account first, and none exists on the issue
  yet). Left for phase 2.
