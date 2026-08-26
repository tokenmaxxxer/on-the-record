---
status: proposed
files:
  - docs/issue-2409/reports/conformance-review.md
---

## Request

Issue #2409 conformance review (board condition per role spec,
`roles/specs/conformance-review.spec.json`): commit `02aba0a9` landed
the phase-2 delivery on `issue-2409/implementation` (the
`session_waste_metrics.py`/`related_files.py` instruments plus
`task-lookup.md`/`hook-contract.md` directive sections and a
`turn-budget.md` addition), PR #2416 is open, and no conformance-review
record exists yet for that sha — see
`docs/issue-2409/reports/conformance-review/survey.md` for the full
derivation and canonical citations. This role's phase-2 job is a
per-requirement verdict (Present|Surface|Absent|Incorrect|Unverifiable)
against issue #2409's own `## Acceptance` text — never a holistic
quality judgment, never a fix, and never a rubber stamp of the
implementer's own self-assessment.

## Constraints

- The filled record lands only after human Approve (contract v3 s19);
  this proposal and the survey are the only phase-1 writes this session
  makes.
- This role's `write_scope` is
  `docs/issue-2409/reports/conformance-review.md` only
  (`roles/specs/conformance-review.spec.json`) — it never edits
  `spawn.py`, `directive_assembly.py`, the implementation role's own
  record, or either new script.
- Verdicts must be re-derived by this role directly against `02aba0a9`
  (and independent re-runs for R1, R4-R13), not taken from
  `docs/issue-2409/reports/implementation.md`'s own self-reported
  numbers at face value — finding-record skill checklist item: the
  verdict comes from looking at the artifact, not from the builder's
  account of their own intent. This matters concretely here: PR #2416's
  own body already hedges its result as "a partial, honestly-bounded
  win" with "live-fire after-evidence for two of the three mechanisms"
  — phase 2 needs the record's own text, not this hedge, to know exactly
  which of R5-R7/R9's before/after pairs actually got a real "after"
  measurement versus only a qualitative spot-check.
- Issue #2409's `## Acceptance` text names 6 `check:` bullets, split in
  the survey into R1-R18 (R18 a non-independent flag, not a separate
  verdict target). The survey's "Notable surface for phase 2" item (a
  gate-precision gap in the approval-gate's own Bash-command path
  matching, found this session, unrelated to issue #2409's own subject
  matter) is outside that set and gets recorded as a separate Open
  Finding, not folded into R1-R18 verdicts.

## Rationale

Considered trusting `docs/issue-2409/reports/implementation.md`'s own
pasted evidence (a pytest summary, the PR body's before-numbers table,
its stated live-fire spot checks) as sufficient on its own, without
independent re-runs — rejected: this role's own live PreToolUse denial
this session (quoted in the survey's "Board / approval state" section)
already shows this session cannot read that record at all before
Approve, so the only way to check R1, R4, R8, R10-R13 today is direct
inspection of the actual code plus independent test/demonstration runs
against a worktree built from `issue-2409/implementation`'s own commits
— which this survey already did for R1's test suite (`79 passed, 1
skipped`, matching the PR body's own claim) and R4's live
`related_files.py` run, rather than accepting either secondhand. The
finding-record skill's own rule against builder self-report as evidence
applies for exactly the same reason it did on issue #2211, and the
`hook-contract.md`/`related_files.py` deliverable under review is itself
the same class of mechanism issue #2211 shipped — its own conformance
review is the direct precedent for this role's method here, not a
different case needing a different approach.

Considered a stratified/sampled review (e.g. spot-checking only
`session_waste_metrics.py`'s Bash-classification logic and treating the
rest of the diff as "implied correct by the passing test suite") —
rejected in the survey's own "Sampling scope" section: the touched
population is eight code/test files and 18 requirements, small enough
that full enumeration costs no more than deriving and justifying a
sample would, and `hook-contract.md`/`task-lookup.md` are now baseline
sections materialized into every future role spawn's directive set —
exactly the infrastructure-wide-blast-radius case the sampling-derivation
skill's rule 5 says to exempt from sampling rather than shrink.

## What will be done

Phase 2, once approved, renders one verdict per requirement (R1-R17 as
listed in the survey, R18 recorded as a non-independent flag rather than
its own verdict) against `02aba0a9`, using the verification method
already assigned per requirement in the survey's "Verification method
per requirement" section: Test plus Demonstration for R1 (independently
re-run `session_waste_metrics.py` against a real session log, not only
the unit suite), Inspection for R2-R3 (does a committed artifact exist;
does the record document the regenerate command), Inspection/Test/
Demonstration for R4 (already substantially satisfied per the survey's
own live-fire evidence, re-confirmed against `02aba0a9` directly),
Demonstration for R5-R7/R9-R13 (independently locate the same 5
real-issue session logs the record cites and re-run the batch tool
before/after, per R17's re-derivation requirement — this is the item
most likely to surface a gap given PR #2416's own hedged language),
Inspection/Test for R8, and Inspection of the record's own prose for
R14-R17 (blocked from this session, first available in phase 2). Each
verdict carries a file:line + commit-sha evidence citation per the
traceability-and-evidence skill. The record's frontmatter
(`subject`/`test`/`result`/`assertedBy`, per
`roles/specs/conformance-review.spec.json`'s EARL-aligned required
fields) will be filled with `result` recomputed as the worst-case across
the cited verdicts. The survey's "Notable surface for phase 2" item (the
approval-gate's own path-matching over-block, found this session) will
be written up as an Open Finding outside the R1-R18 set, with its own
resolution path naming a different issue as the fix owner.

## Out of scope

- Editing `directive_assembly.py`, `spawn.py`, either new script, or
  either test file, even if a verdict below Present is rendered — this
  role reports, it does not fix.
- Filing a follow-up issue for the approval-gate's Bash-command
  path-matching over-block this session found — outside this role's
  `write_scope`; phase 2 will name it as an Open Finding for a human/
  different role to act on.
- Re-litigating issue #2409's own design (whether a lookup script plus
  directive prose was the right mechanism vs., say, a different
  instrumentation approach) — phase 2 checks conformance to what the
  issue asked for, not whether the issue asked for the right thing.
- Independently re-deriving the original 177-session corpus numbers the
  issue body itself states — those are the issue's own baseline, not
  part of `02aba0a9`'s deliverable; phase 2 checks whether the record's
  before/after numbers are genuine re-derivations (R17), not whether the
  issue's own pre-existing baseline is correct.
- Reviewing PR #2416's own mergeability, CI status, or review comments —
  this role's subject is the commit's conformance to the issue text, not
  the PR's process state.

## How you'll know it worked

`docs/issue-2409/reports/conformance-review.md` carries requirement
blocks for R1-R17 (R18 noted as a non-independent flag), each with
`requirement`/`spec_ref`/`verdict`/`evidence`/`rationale`, every verdict
backed by a citation this role re-derived against `02aba0a9` (including
an independently re-run before/after batch measurement for R5-R7/R9-R13,
not merely copied from the PR body's own hedged summary); the
frontmatter `result` field matches the worst-case of those verdicts; the
survey's one "Notable surface" item is recorded as an Open Finding with
a resolution path; `loop_state` reaches `reported` (this role's terminal
state per its spec). Caveat, matching the issue-2211 precedent:
`result`-vs-verdicts agreement is not gate-checked today
(`roles/specs/conformance-review.spec.json`'s own
`recomputation.checked_by` is `"TBD"`) — this stays manual discipline in
phase 2, not something an existing gate refuses if violated.
