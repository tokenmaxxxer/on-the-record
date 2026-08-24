---
issue: 2165
role: conformance-review
loop_state: scope-proposed
---

# issue-2165 — proposal: conformance review of PR #2170

files:
- docs/issue-2165/reports/conformance-review.md

## Request

Render a conformance-review verdict on `issue-2165/implementation`'s
delivered fix (PR #2170) against issue #2165's `## Fix`/`## Acceptance`
clauses (R1-R9, extracted in
`docs/issue-2165/reports/conformance-review/survey.md`), and land it as
this role's own record.

## Constraints

- Write only `docs/issue-2165/reports/conformance-review.md` — never
  `docs/issue-2165/reports/implementation.md` or any other role's area
  (contract v3 s19: "write only your own record area").
- No code change to `gates/spawn_on_pr.py` or its tests — this role
  reviews PR #2170's delivery, it does not extend or fix it; a finding
  against R5 (see survey's gap candidate) is recorded as a verdict with
  its resolution path, not patched directly.
- Re-run `tests/test_spawn_on_pr.py` and `tests/test_spawn_on_pr_park.py`
  live against the actual `issue-2165/implementation` branch content
  before citing a pass count, rather than repeating PR #2170's own pasted
  numbers as this record's own evidence (verify-at-landing, contract v3).

## Rationale

**Chosen approach: full inspection of both changed files against all 9
extracted requirements, verified by an independent live test run.** The
survey's sampling-derivation check already found full enumeration
feasible (one source file, one test file, both small) — this proposal
doesn't reopen that call, but it does choose HOW to confirm PR #2170's
own pasted verification numbers.

**Rejected alternative 1: trust PR #2170's pasted `28 passed` / `20
passed` pytest output as this review's own acceptance evidence, without
re-running.** Rejected because this review's worktree currently predates
PR #2170's diff (survey: `git log` on `gates/spawn_on_pr.py` shows no
issue-2165 commit yet) — citing another role's pasted output as this
role's own executed evidence would violate verify-at-landing's own
"actual command and output in your record" bar; a conformance review's
credibility rests on independently reproducing the claim, not relaying
it.

**Rejected alternative 2: treat the R5 gap candidate (no #513-shape test
in `tests/test_spawn_on_pr_park.py`) as an automatic Absent/Incorrect
without further inspection.** Rejected as premature — the survey only
established that the literal file named in Acceptance bullet 1's
parenthetical wasn't touched; it did not yet establish whether the two
new tests actually landing in `tests/test_spawn_on_pr.py` functionally
cover the same #513 shape (which the survey's diff excerpt suggests they
do) closes the substance of R5 even though the letter names a different
file. Phase 2 renders that verdict call explicitly instead of either
assuming Pass or Fail from the file-list mismatch alone.

**Failure signal:** if phase 2's independent test re-run against
`issue-2165/implementation` does not reproduce PR #2170's own pasted
pass counts, or if `tests/test_spawn_on_pr_park.py` genuinely has no
equivalent coverage for the #513 shape once inspected in full, the
record must state Incorrect/Absent against the specific requirement
rather than carrying forward a Present verdict.

## What will be done

1. Fetch/checkout `issue-2165/implementation`'s content (the PR #2170
   branch) into this workspace so the changed files are actually present
   for citation and test execution.
2. Render a verdict (Present/Surface/Absent/Incorrect/Unverifiable, per
   conformance-review-verdict-assignment) for each of R1-R9 from the
   survey, with file:line + commit-sha evidence per
   conformance-review-traceability-and-evidence.
3. Independently re-run `python3 -m pytest tests/test_spawn_on_pr.py
   tests/test_spawn_on_pr_park.py -q` against that checked-out content
   and paste the actual output as this record's own acceptance evidence
   (R6, R8).
4. Resolve the R5 gap candidate explicitly: state whether the new tests'
   actual scenario coverage satisfies Acceptance bullet 1's
   `test_spawn_on_pr_park.py` clause in substance, or record
   Absent/Incorrect against the literal wording.
5. State R9 as Unverifiable-as-written, per the survey, without guessing
   a bound or a token/session-cost figure.
6. Write the verdicts into
   `docs/issue-2165/reports/conformance-review.md` (the pre-existing
   skeleton) per conformance-review-finding-record, set
   `loop_state: reported` (this record kind's terminal state), and leave
   severity-classification untouched — this issue's scope is ordinary
   fidelity-checking, not an explicit risk-weighting request.
7. Commit, push, and open the phase-2 PR on `issue-2165/conformance-review`.

## Out of scope

- Fixing or extending PR #2170's code — any finding against R1-R9 is
  recorded as a verdict with a resolution path, not patched by this role.
- Determining the actual `gh`-flakiness recurrence rate in the external
  target repo #513 ran in (R9) — no access from this workspace, stated
  as Unverifiable rather than guessed.
- Severity-classification of any finding — this issue's scope is ordinary
  conformance-checking, not an explicit risk-weighting extension.
- Re-opening the sampling-derivation call — the survey already found full
  enumeration feasible and this proposal does not revisit it.

## Skill checks

skill-verdict: conformance-review-requirement-extraction — applied:
invoked; used to split issue #2165's `## Fix`/`## Acceptance` clauses
into R1-R9 in `docs/issue-2165/reports/conformance-review/survey.md`
(one obligation per line, dimension-tagged, R9 flagged
unverifiable-as-written per its rule 2).

skill-verdict: conformance-review-verification-method-selection —
applied: invoked; used to assign Inspection/Analysis/Test per
requirement in the survey's verification-method-plan table, reusing PR
#2170's own new regression tests as Test-method evidence for R1/R3/R4
per its rule 4.

skill-verdict: conformance-review-traceability-and-evidence — applied:
invoked; used to pin the survey's evidence citations to file:line plus
commit sha (`e2fdec458f6d43671458844e1259ec0de91b95ff`) and to record one
link per contributing file (`gates/spawn_on_pr.py`,
`tests/test_spawn_on_pr.py`, `tests/test_spawn_on_pr_park.py`
separately) rather than a single bundled citation.

other mounted skills: not triggered — conformance-review-sampling-derivation
was checked and found not-applicable (survey: full enumeration of R1-R9
is feasible, no stratification needed); conformance-review-verdict-assignment,
conformance-review-finding-record, and conformance-review-severity-classification
apply to phase-2 (rendering and recording verdicts), which this phase-1
proposal does not yet do — no verdict has been rendered.

## How you'll know it worked

- `docs/issue-2165/reports/conformance-review.md` carries a verdict line
  for every one of R1-R9, each with a file:line/commit-sha or
  Unverifiable-reason citation.
- The record's own `## Verification`-equivalent section pastes a live
  `pytest` run against the checked-out `issue-2165/implementation`
  content, not a repeated citation of PR #2170's own pasted numbers.
- The record's frontmatter `loop_state` is set to `reported` (review-record's
  terminal state per contract v3 s2), or states explicitly why it isn't
  yet terminal.
