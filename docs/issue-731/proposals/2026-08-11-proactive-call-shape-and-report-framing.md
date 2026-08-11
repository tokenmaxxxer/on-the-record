---
status: proposed
files:
  - on-the-record/commands/run.md
---

## Request

From audit #726, two on-the-record-own conventions are enforced only by
a gate/hook, with no proactive statement in on-the-record's own
commands/docs: (row 7) `call-shape-guard.sh`'s flag-consistency rule for
call sites sharing the same `(argv[0], argv[1])`, and (row 23, advisory)
`report-framing-check.sh`'s four-element report framing (resolved
problem / prior cost / newly possible / still broken, issue #320). State
both proactively in on-the-record's own docs.

## Constraints

- Doc-only change: no gate/hook logic changes, no behavior change to
  either check.
- Must land in on-the-record's own commands/docs (not a role rulebook) —
  per the issue, these are call-site/report conventions, not
  role-specific.
- Acceptance check (per issue #731): a unit test must be able to assert
  that `on-the-record/commands/*.md` (or a referenced style doc) names
  the flag-consistency rule and the four-element report framing.

## Rationale

Considered adding a new standalone style doc (e.g.
`on-the-record/docs/style.md`) referenced from `run.md`, instead of
editing `run.md` directly. Rejected: `run.md` already carries every
other reactively-enforced-but-proactively-documented convention in this
repo (`#419`'s sibling-marker half, `#415`, `#416`, `#424`) as inline
`##` sections — introducing a second doc for just these two rows would
split one convention family across two files for no benefit, and the
issue's acceptance check text explicitly anticipates `commands/*.md`
(or, only as a fallback, "a referenced style doc") as the primary
location.

## What will be done

- In `on-the-record/commands/run.md`, extend the existing `## 같은
  모양의 재발은 마킹하거나 기계가 잡는다 (#419)` section with an explicit
  proactive statement of the flag-consistency rule itself (call sites
  sharing the same `(argv[0], argv[1])` should use the same semantic
  flag shape — `-X`/`--method`/`-f`/`--field` — from the start), stated
  as something to do, not only as a description of what the gate
  catches.
- Add a new short `##` section documenting the four-element report
  framing (resolved problem / prior cost / newly possible / still
  broken, issue #320) as something a PR/board report should hit
  proactively, cross-referencing that `report-framing-check.sh` enforces
  it as an advisory Stop-hook check.

## Out of scope

- Any change to `call-shape-guard.sh` or `report-framing-check.sh`
  themselves.
- Writing the acceptance unit test named in issue #731's Acceptance
  section (`gates/test_*` for this convention) — the issue's Acceptance
  names a check as the definition of done; this proposal's write set is
  docs-only per the survey, so the test is out of scope for this pass
  unless the approver wants it folded in.

## How you'll know it worked

`grep -n "argv\[0\]\|flag consistency\|resolved problem.*prior cost.*
newly possible.*still broken\|report-framing" on-the-record/commands/run.md`
returns non-empty hits for both conventions, stated as directives rather
than only as gate-behavior descriptions.
