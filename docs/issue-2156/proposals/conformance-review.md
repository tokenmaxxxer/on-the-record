---
status: proposed
files:
  - docs/issue-2156/reports/conformance-review.md
---

## Request

Issue #2156 conformance review (board condition per role spec,
`roles/specs/conformance-review.spec.json`): commit `b47a2abf` landed
the phase-2 delivery (the "NO REDUNDANT WATCHER, BY ANY MECHANISM" block
in `on-the-record/directive/spawn-and-board.md`), and no
conformance-review record exists yet for that sha — see
`docs/issue-2156/reports/conformance-review/survey.md` for the full
derivation and canonical citations. This role's phase-2 job is a
per-requirement verdict (Present|Surface|Absent|Incorrect|Unverifiable)
against issue #2156's own `## Change`/`## Acceptance` text — never a
holistic quality judgment, never a fix.

## Constraints

- The filled record lands only after human Approve (contract v3 s19);
  this proposal and the survey are the only phase-1 writes this session
  makes.
- This role's `write_scope` is `docs/issue-2156/reports/conformance-review.md`
  only (`roles/specs/conformance-review.spec.json`) — it never edits
  `on-the-record/directive/spawn-and-board.md`, `docs/reports/deviation-log.md`,
  or any other role's record.
- Verdicts must be re-derived by this role directly against `b47a2abf`,
  not taken from `docs/issue-2156/reports/implementation.md`'s own
  self-assessment at face value (finding-record skill checklist item:
  "the verdict came from looking at the artifact, not from the builder's
  account of their own intent").

## Rationale

Considered trusting `docs/issue-2156/reports/implementation.md`'s own
"Acceptance evidence" section (it already pastes a grep run showing the
guidance text present) as sufficient evidence on its own, without an
independent re-run — rejected: this role's own finding-record skill
refuses a Present/Absent/Incorrect verdict written from the builder's
account rather than from looking at the artifact directly, and the
survey already found one place (the PR #2157 trailer / issue-#2156-still-open
gap) where the implementer's record is silent on something the raw
`gh pr view`/`gh issue view` state itself surfaces — an unexamined
self-report would have missed it.

Considered folding that PR trailer / still-open observation into one of
the 8 extracted requirements as an Incorrect or Absent verdict — rejected:
issue #2156's own `## Acceptance` text names none of it (it covers only
the guidance content, the docs-only label, and the grep evidence), so
scoring it against a requirement the issue never stated would
misattribute a process-compliance gap as a spec nonconformance. Phase 2
will instead record it as a separate Open Finding, outside the R1-R8
verdict set — see the survey's "Notable surface for phase 2" section.

## What will be done

Phase 2, once approved, renders one verdict per requirement (R1-R8 as
listed in the survey) against `on-the-record/directive/spawn-and-board.md`
at `b47a2abf`, using Inspection for R1-R7 (structural text-presence) and
Test for R8 (re-running the grep independently rather than reusing only
the implementer's pasted output), each with a file:line + commit-sha
evidence citation per the traceability-and-evidence skill. The record's
frontmatter (`subject`/`test`/`result`/`assertedBy`, per
`roles/specs/conformance-review.spec.json`'s EARL-aligned required
fields) will be filled with `result` recomputed as the worst-case across
the 8 cited verdicts. The PR-trailer/still-open observation from the
survey will be written up as one Open Finding with its own resolution
path (naming who owns fixing it, since it falls outside this role's
`write_scope`).

## Out of scope

- Editing `on-the-record/directive/spawn-and-board.md` itself, even if a
  verdict below Present is rendered — this role reports, it does not fix.
- Adding the missing entry to `docs/reports/deviation-log.md` — outside
  this role's `write_scope`; phase 2 will name it as an Open Finding for
  a different role/a human to act on instead.
- Re-litigating issue #2156's own design (whether "by any mechanism" was
  the right scope to ship) — phase 2 checks conformance to what the
  issue asked for, not whether the issue asked for the right thing.

## How you'll know it worked

`docs/issue-2156/reports/conformance-review.md` carries 8 requirement
blocks (R1-R8), each with `requirement`/`spec_ref`/`verdict`/`evidence`/`rationale`,
every verdict backed by a citation this role re-derived against
`b47a2abf` (not merely copied from the implementer's record); the
frontmatter `result` field matches the worst-case of those 8 verdicts;
one Open Finding documents the PR-trailer/still-open gap with a
resolution path; `loop_state` reaches `reported` (this role's terminal
state per its spec). Caveat, per this proposal's after-proposal
warrant-hunter dispatch (stance 0,
`docs/issue-2156/reports/conformance-review/2026-08-24-hunt-conformance-review.md`):
`result`-vs-verdicts agreement is not gate-checked
(`roles/conformance-review.json`'s `record_fields` declares only
`loop_state`; `roles/specs/conformance-review.spec.json`'s own
`recomputation.checked_by` is `"TBD"`) — this is manual discipline in
phase 2, not something any existing gate will refuse if violated.
