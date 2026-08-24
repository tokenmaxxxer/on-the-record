---
status: approved
files:
  - docs/issue-2208/reports/conformance-review.md
---

## Request

Issue #2208 conformance review (board condition per
roles/specs/conformance-review.spec.json): the implementation branch
carries a landed record at commit range 8e934e0d..326506f2 (PR #2218,
still open against main), and no conformance-review record exists yet
for that range — see docs/issue-2208/reports/conformance-review/survey.md
for the full derivation and canonical citations. This role's phase-2
job is a per-requirement verdict (Present|Surface|Absent|Incorrect|Unverifiable)
against the twelve requirements (R1-R12) the survey extracted from issue
#2208's own Acceptance text — never a holistic quality judgment, never a
fix, and never a rewrite of the implementer's own prose.

## Constraints

- The filled record lands only after human Approve (contract v3 s19);
  this proposal and the survey are the only phase-1 writes this session
  makes.
- This role's write_scope is docs/issue-2208/reports/conformance-review.md
  only (roles/specs/conformance-review.spec.json) — it never edits
  pipeline.py, skills.py, spawn.py, or any other role's record, even if a
  verdict below Present is rendered.
- Verdicts must be re-derived by this role directly against the
  implementation branch's committed diff, not taken from the
  implementation record's own acceptance blocks at face value —
  finding-record's own checklist refuses a verdict written from the
  builder's account of their own intent rather than from looking at the
  artifact.
- The record's required fields (subject/test/result/assertedBy, per
  roles/specs/conformance-review.spec.json's EARL-aligned schema) must
  resolve to real refs, and result must recompute as the worst-case
  across the cited per-requirement verdicts, per the spec's own EARL
  severity ordering (failed ranks worse than cantTell, which ranks worse
  than inapplicable, which ranks worse than untested, which ranks worse
  than the fully-conforming value) and recomputation rule.

## Rationale

Considered trusting the implementation record's own "acceptance:"
blocks (it already pastes before/after pytest runs and a fail-open
retrieval re-run) as sufficient evidence on its own, without this role
independently re-running anything — rejected: the same finding-record
discipline the survey already applied to item 1's abstention-rate query
(re-run this session, matching the implementer's figures exactly) needs
to extend to items 2 and 3 in phase 2 too, since the implementer's
account and the underlying artifact can diverge in ways a self-report
alone would miss (the survey's own before-landing-hunt paragraph is an
example: the implementer's own account describes discovering and
fixing a gap in their own first attempt mid-build, so a single
self-reported acceptance line is not, by itself,
strong enough evidence of the requirement's final state).

Considered treating R7 ("work-in-english is bound statically for the
roles that need it") as a simple structural check — does
_STATIC_POLICY_SKILLS exist and get referenced — without engaging the
open scope question the survey flagged (pinning based on two logged
mounts, both role=implementation, against the issue's open-ended "roles
that need it" phrasing) — rejected: R7's own verdict is exactly where
that scope question has to be weighed; deferring it to a separate,
un-verdicted Open Finding (as issue-2156's conformance-review record did
for an unrelated PR-trailer gap) would misplace it, since here the
question is intrinsic to whether R7 itself is satisfied, not an
observation the issue's Acceptance text is silent on.

## What will be done

Phase 2, once approved, renders one verdict per requirement (R1-R12 as
listed in the survey) against the implementation branch's committed
diff (pipeline.py, skills.py, spawn.py, plus the implementation record's
own acceptance evidence where R1-R3/R6/R9/R11 require checking what the
record itself states, not just what the code does), using Inspection for
structural claims (R3, R5, R7, R8, R11's presence check), Test for
claims with an existing or re-runnable command (R1's abstention query,
R4/R6/R10/R12 via tests/test_retrieval_eval.py, R9 via the retrieval
pipeline re-run against the frozen negative case), and Analysis where a
condition cannot be directly re-executed from this working tree (none
currently anticipated, but reserved per verification-method-selection
rule 2 if one surfaces). Each verdict carries a file:line/commit-sha
evidence citation per the traceability-and-evidence skill. The record's
frontmatter result is recomputed as the worst-case across the twelve
cited verdicts, not asserted independently.

## Out of scope

- Editing pipeline.py, skills.py, or spawn.py, even if a verdict below
  Present is rendered — this role reports, it does not fix.
- Re-litigating issue #2208's own scoping choices (whether cheapest-first
  ordering across its three diagnoses was the right call, whether a
  fourth unrequested item belonged in the same commit) — phase two
  checks conformance to what the issue asked for, not whether the issue
  asked for the right thing.
- Re-scoring the two frozen negative gold cases' own construction
  (whether work-in-english-declared-phrase-self-inflation-fp or
  issue-525-cross-family-off-domain-fp are well-designed test cases) —
  they are treated as fixed fixtures inherited from #2205/#2206, not
  something this review audits.

## How you'll know it worked

docs/issue-2208/reports/conformance-review.md carries twelve requirement
blocks (R1-R12), each with requirement/spec_ref/verdict/evidence/rationale,
every verdict backed by a citation this role re-derived against the
implementation branch's actual commits (not merely copied from the
implementer's record); the frontmatter result field matches the
worst-case of those twelve verdicts; R7's verdict explicitly engages the
survey's "roles that need it" scope question rather than treating it as
a separate unverdicted finding; loop_state reaches reported (this role's
terminal state per its own spec).
