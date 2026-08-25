---
status: proposed
files:
  - docs/issue-2211/reports/conformance-review.md
---

## Request

Issue #2211 conformance review (board condition per role spec,
`roles/specs/conformance-review.spec.json`): commit `94fbd4df` landed
the phase-2 delivery on `issue-2211/implementation` (env-var injection
in `spawn_cmd()` plus a new `known-paths.md` directive section), PR
#2228 is open, and no conformance-review record exists yet for that sha
— see `docs/issue-2211/reports/conformance-review/survey.md` for the
full derivation and canonical citations. This role's phase-2 job is a
per-requirement verdict (Present|Surface|Absent|Incorrect|Unverifiable)
against issue #2211's own `## Fix`/`## Acceptance` text — never a
holistic quality judgment, never a fix, and never a rubber stamp of the
implementer's own self-assessment.

## Constraints

- The filled record lands only after human Approve (contract v3 s19);
  this proposal and the survey are the only phase-1 writes this session
  makes.
- This role's `write_scope` is
  `docs/issue-2211/reports/conformance-review.md` only
  (`roles/specs/conformance-review.spec.json`) — it never edits
  `spawn.py`, `pipeline.py`, the implementation role's own record, or
  `docs/reports/deviation-log.md`.
- Verdicts must be re-derived by this role directly against `94fbd4df`
  (and a live re-spawn for R6-R8), not taken from
  `docs/issue-2211/reports/implementation.md`'s own "Acceptance
  verification"/"Acceptance evidence" sections at face value —
  finding-record skill checklist item: the verdict comes from looking at
  the artifact, not from the builder's account of their own intent.
- Issue #2211's `## Acceptance` text names R1-R14 (survey's split/tagged
  list); the two "Notable surface for phase 2" items the survey flags
  (the `tokenmaxxxer-core` companion-issue follow-up, and independently
  re-running the pre-existing-failures comparison) are outside that set
  and get recorded as separate Open Findings, not folded into R1-R14
  verdicts.

## Rationale

Considered trusting `docs/issue-2211/reports/implementation.md`'s own
pasted evidence (a `printenv` transcript for R1-R4, a session-log grep
count for R7-R8, a `127 passed`/`11 failed` pytest summary for R10) as
sufficient on its own, without independent re-runs — rejected: the
survey already found this role's own session cannot see any of
`94fbd4df`'s effects from its ambient environment (spawned off `main`,
which does not carry that commit), so the only way to actually check
R1-R8 is a live re-spawn built from `issue-2211/implementation`'s own
code, run by this role, not read secondhand from the implementer's
transcript. The finding-record skill's own rule against builder
self-report as evidence applies for exactly the same reason it did on
issue #2156.

Considered a stratified/sampled review (e.g. spot-checking `spawn.py`'s
diff hunks but skipping the two test files, or checking only R1-R5 and
treating R6-R14 as "implied") — rejected in the survey's own "Sampling
scope" section: the touched population is four files and 14
requirements, small enough that full enumeration costs no more than
deriving and justifying a sample would, and an env-var injection wired
into every future role spawn is infrastructure-wide blast radius —
exactly the case the sampling-derivation skill's rule 5 says to exempt
from sampling rather than shrink.

## What will be done

Phase 2, once approved, renders one verdict per requirement (R1-R14 as
listed in the survey) against `94fbd4df`, using the verification method
already assigned per requirement in the survey's "Verification method
per requirement" section: Inspection plus reused/re-run Test evidence
for R1-R5 and R10-R14 (per verification-method-selection rule 4, reuse
existing unit tests rather than deriving a parallel manual check, but
re-run them independently rather than trust only a pasted summary),
Demonstration via an independently re-run live `claude -p` spawn for
R6-R8, and Analysis-only for R9 (the undefined "engineering-class" term
— judged for reasonableness of the implementer's stand-in, not verdicted
against an invented threshold). Each verdict carries a file:line +
commit-sha evidence citation per the traceability-and-evidence skill.
The record's frontmatter (`subject`/`test`/`result`/`assertedBy`, per
`roles/specs/conformance-review.spec.json`'s EARL-aligned required
fields) will be filled with `result` recomputed as the worst-case across
the 14 cited verdicts. The survey's two "Notable surface for phase 2"
items (independently re-running the pre-existing-failures comparison;
the `tokenmaxxxer-core` companion-issue follow-up) will be written up as
Open Findings outside the R1-R14 set, each with its own resolution path.

## Out of scope

- Editing `spawn.py`, `pipeline.py`, or either test file, even if a
  verdict below Present is rendered — this role reports, it does not
  fix.
- Filing the companion `tokenmaxxxer-core` issue for the `directive.sh`
  index-line entry — outside this role's `write_scope`; phase 2 will
  name it as an Open Finding for a human/different role to act on.
- Re-litigating issue #2211's own design (whether env-var injection was
  the right fix vs., say, a lazily-computed lookup helper) — phase 2
  checks conformance to what the issue asked for, not whether the issue
  asked for the right thing.
- Reviewing PR #2228's own mergeability, CI status, or review comments —
  this role's subject is the commit's conformance to the issue text, not
  the PR's process state.

## How you'll know it worked

`docs/issue-2211/reports/conformance-review.md` carries 14 requirement
blocks (R1-R14), each with `requirement`/`spec_ref`/`verdict`/`evidence`/`rationale`,
every verdict backed by a citation this role re-derived against
`94fbd4df` (including an independently re-run live spawn for R6-R8, not
merely copied from the implementer's own record); the frontmatter
`result` field matches the worst-case of those 14 verdicts; the two
Open Findings from the survey's "Notable surface" section are recorded
with resolution paths; `loop_state` reaches `reported` (this role's
terminal state per its spec). Caveat, matching the issue-2156 precedent:
`result`-vs-verdicts agreement is not gate-checked today
(`roles/specs/conformance-review.spec.json`'s own `recomputation.checked_by`
is `"TBD"`) — this stays manual discipline in phase 2, not something an
existing gate refuses if violated.
