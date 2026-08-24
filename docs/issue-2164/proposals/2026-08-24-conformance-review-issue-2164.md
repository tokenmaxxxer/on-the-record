---
status: proposed
issue: 2164
files:
  - docs/issue-2164/reports/conformance-review.md
---

# Proposal — conformance review of issue #2164's terminology-rename commit

Upstream: docs/issue-2164/reports/conformance-review/survey.md.

## Request

Audit commit `3ea0ec88` (merged to `main` via PR #2168, issue #2164's
own delivery) against issue #2164's own "Change"/"Acceptance" text: did
the `룰북`→skill-repo-guidance rename in `consult.py`/`pipeline.py`, and
the `pipeline.py:215` dangling-reference fix, land as specified, stay
inside the stated exclusion, and leave the test suite clean. Render a
per-requirement verdict with re-derivable evidence, and record open
findings. This role reviews; it does not fix anything the review finds,
and does not edit any file outside its own report area.

## Constraints

- **The target is fully built and merged.** Unlike a typical
  conformance-review target, `3ea0ec88` already sits at `main`'s tip
  (survey §"log --oneline"), so this review evaluates a finished
  artifact, not a moving one — nothing about it changes between now and
  when the record is written.
- **This role's write set is its own report area only.** No change to
  `consult.py`, `pipeline.py`, or the implementation role's own record
  under `docs/issue-2164/reports/implementation.md`/`implementation/`
  may issue from this session.
- **Small, fully-enumerable scope.** One commit, two source files,
  eight issue-named line items — the sampling-derivation skill does not
  apply (survey §7); nothing here justifies stratified sampling.
- **`record-claim-guard.sh` governs everything written under
  `docs/issue-2164/reports/**`** — count claims need a `derived:`
  citation or fenced reproduction, state/defect claims need a
  `canonical:` tag within 3 lines, outcome claims need an executed-live
  citation. The record's evidence blocks are built to that shape
  already in the survey and carry the same shape into phase 2.
- **The after-proposal warrant-hunter dispatch could not complete.**
  Three attempts (docs/issue-2164/reports/conformance-review/2026-08-24-hunt-2026-08-24-conformance-review-issue-2164.md)
  hit a naming mismatch then a stuck `hunt-guard.sh` lock past its own
  60s cap; per contract v3 s22 this session stopped retrying rather than
  loop on an unconverging dispatch. No hunter finding exists for this
  transition.
- **This session's own environment denies two classes of command**
  (survey §6, third finding): re-running the implementation record's
  original 10-file combined pytest command, and any invocation of
  `test/test_spawn_skill_judge_haiku_timeout_overlap.py` — both via an
  approval-gate hook whose `gh` query requests a JSON field
  (`state_reason`) the installed `gh` CLI does not recognize. The
  record must state this plainly as the reason those two specific
  reproductions are partial, not silently work around it or claim full
  reproduction it did not achieve.

## Rationale

**Independent re-execution of the implementation record's cited tests,
rejecting acceptance of the record's own pasted output on trust.** The
implementation record already pastes a full green pytest run (183
passed, 4 xfailed, 0 failed) covering the ten test files issue #2164's
acceptance bullet asks about. Taking that on trust was the cheaper
option and is rejected: conformance-review's entire reason to exist is
independent audit, and trusting a builder's own pasted evidence at face
value collapses the role into a rubber stamp. The survey's independent
re-run (in batches, since the exact 10-file command denies in this
session) is what surfaced the actual finding: `tests/test_spawn_pipeline.py`
shows 2 failures standalone that the implementation record's own
transcript does not show. Re-executing rather than trusting is what
made that discrepancy visible at all.

**Regression judged by a before/after commit comparison, rejecting
"any failure found means REQ-7 fails."** A naive rule — any test
failure observed during review means the "tests still pass" acceptance
bullet is unmet — was considered and rejected: it would blame issue
#2164's diff for two failures that reproduce identically on the parent
commit `d9a1e826` (survey §5), unrelated to `consult.py`/`pipeline.py`'s
content. The chosen method — checkout the parent commit, re-run the
same two failing tests, compare — is what distinguishes "this diff
broke something" from "something was already broken," which a single
after-the-fact test run cannot do on its own.

**Verdict vocabulary Present / Surface / Absent / Incorrect /
Unverifiable, matching this repo's own `conformance-review-verdict-assignment`
skill and prior conformance-review proposals (e.g. issue-2093's).** No
alternative vocabulary was considered for this proposal — the skill
mandates this exact five-value set, and inventing a repo-local variant
(as issue-749's MET/PARTIAL/GAP once did) would cost cross-record
comparability for no benefit here, since none of this review's findings
need a vocabulary richer than the mandated five.

## What will be done

1. **The record** (`docs/issue-2164/reports/conformance-review.md`):
   contract §20 fields plus the role spec's `subject`/`test`/`result`/
   `assertedBy` frontmatter, one `---`-delimited finding block per
   REQ-1..REQ-8 (survey §2) carrying `requirement`/`spec_ref`/`verdict`/
   `evidence`/`rationale` per `conformance-review-finding-record`'s field
   list, each evidence pointer citing file:line plus the `3ea0ec88` sha
   per `conformance-review-traceability-and-evidence`.
2. **Verdicts** for REQ-1 through REQ-6 and REQ-7: `Present`, evidence
   already gathered in the survey (static inspection for REQ-1..REQ-5,
   Analysis for REQ-6, independent test re-execution plus the
   parent-commit comparison for REQ-7).
3. **Verdict for REQ-8** (executed acceptance evidence in the
   implementation record): `Surface` — the record's evidence blocks
   have the right shape, but the `tests/test_spawn_pipeline.py`
   transcript specifically does not, on independent replay, establish
   the zero-failure claim it makes (survey §5-6).
4. **Open findings section**: the three findings the survey already
   surfaced (§6) — the residual `pipeline.py:451` dangling reference
   outside REQ-3's scope, the non-reproducing `test_spawn_pipeline.py`
   evidence, and this session's own approval-gate/`gh` environment
   defect — each with the resolution path already stated in the survey,
   carried into the record largely verbatim.
5. **Overall `result`**: recomputed per the role spec's own rule
   (worst-case across cited test entries, `failed > cantTell >
   inapplicable > untested > passed`) rather than asserted
   independently — driven down from `passed` by REQ-8's `Surface`
   finding, landing on `cantTell`.
6. **Skill verdicts**: the five skills already invoked this session for
   the survey (requirement-extraction, verification-method-selection,
   verdict-assignment, traceability-and-evidence, finding-record) get
   `applied: invoked` lines carried into the record; sampling-derivation
   and severity-classification stay `not-applicable` (survey §7; no
   severity-weighting was requested).

## Out of scope

- Fixing anything the review finds — including the `pipeline.py:451`
  dangling reference, or re-running `test_spawn_pipeline.py` in a
  different environment to resolve the discrepancy. Findings are
  recorded and reported; a fix belongs to a future implementation
  session.
- Any edit to `consult.py`, `pipeline.py`, `on-the-record/hooks/`, or
  `gates/` — including a fix for the `gh`/`state_reason` approval-gate
  defect this session hit repeatedly. That defect is reported as an
  open finding, not patched from inside this role's write set.
- Judging whether the implementation's scope-widening deviation (the
  deviation log at `docs/issue-2164/reports/implementation/deviation-log.md`)
  was the right call as a design decision — REQ-4/REQ-5's verdicts
  already cover whether the delivered scope satisfies the issue's own
  acceptance text, which is what this review checks.
- Severity-weighting any finding. That is a separate, explicitly-scoped
  extension of a review (`conformance-review-severity-classification`),
  not part of ordinary fidelity-checking, and was not requested here.
- Re-litigating PR #2168's process state (approvals, merge readiness) —
  it is already merged to `main`; this review checks the merged
  artifact.

## How you'll know it worked

- Every REQ line item in the survey's requirement list (§2) appears as
  exactly one `---`-delimited finding block in the record, with a
  verdict, a method, and a file:line+sha evidence citation.
- The record's overall `result` is the recomputed worst-case across all
  eight finding blocks, not a value asserted independently of them.
- The three open findings from the survey (§6) appear in the record's
  "Open findings" section with their resolution paths intact.
- `record_lint.lint_record()` (or the equivalent `record-claim-guard.sh`
  checks) reports zero violations against the written record, the same
  bar the survey was held to before this proposal was written.
- `loop_state` reaches this role's terminal value, `reported`.
- No file outside this proposal's `files:` set is modified by this
  session (`git diff --stat` on the branch confirms it).

## Skill verdicts (phase-1 home)

These lines belong to this session's record, but the record
(`docs/issue-2164/reports/conformance-review.md`) is phase-2 output and
`approval-gate.sh` refuses a phase-1 write to it. They are recorded
here, in the phase-1 home, and carry forward into the record verbatim
in phase 2.

skill-verdict: conformance-review-requirement-extraction — applied:
invoked; produced the REQ-1..REQ-8 split in survey §2 — one obligation
per line, dimension-tagged, backward-traced to the issue's own sweep-
finding/Change/Acceptance text, REQ-7 kept as its own conditional item
per rule 5 rather than merged into REQ-6.

skill-verdict: conformance-review-verification-method-selection —
applied: invoked; set survey §3-5's method choice per requirement —
Inspection for the static docstring/prompt-text renames and the
untouched-exclusion check, Test (reusing the repo's own pytest files)
for the grep-based and test-suite acceptance bullets, Analysis for the
"meaning unchanged" claim.

skill-verdict: conformance-review-verdict-assignment — applied:
invoked; used to work out the REQ-1..REQ-8 verdicts this proposal's
"What will be done" states (six/seven `Present`, one `Surface`), and to
require the parent-commit re-check (rule 6) before treating
`test_spawn_pipeline.py`'s failures as this issue's own regression
rather than pre-existing.

skill-verdict: conformance-review-traceability-and-evidence — applied:
invoked; set the evidence-citation shape throughout the survey — file:
line plus the `3ea0ec88` sha rather than a bare path, one link per
contributing file (`consult.py` and `pipeline.py` cited separately in
survey §3).

skill-verdict: conformance-review-finding-record — applied: invoked;
its field list (`requirement`/`spec_ref`/`verdict`/`evidence`/
`rationale`) is what step 1 above commits to write per REQ item in
phase 2; no verdict is written to the record itself in phase 1.

skill-verdict: conformance-review-sampling-derivation — not-applicable:
full enumeration of the issue's own eight named line items is feasible
at this size (survey §7) — no stratified sample is needed.

skill-verdict: conformance-review-severity-classification —
not-applicable: this review's scope was not explicitly extended into
risk-weighting a recorded finding; no severity band was requested.
