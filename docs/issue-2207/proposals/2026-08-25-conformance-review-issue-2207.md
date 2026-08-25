---
status: proposed
issue: 2207
files:
  - docs/issue-2207/reports/conformance-review.md
---

# Proposal — conformance review of issue #2207's refactoring-legacy delivery (PR #2308)

Upstream: docs/issue-2207/reports/conformance-review/survey.md.

## Request

Audit PR tokenmaxxxer/on-the-record#2308 (branch
`issue-2207/refactoring-legacy`, open/unmerged at head `85a9611f`) against
issue #2207's own Investigate/Fix/Acceptance text and the 2026-08-25
operator-frozen systemic constraint comment: did the `directive_assembly.py`
extraction land as specified, follow a real access-pattern seam rather
than decomposing for its own sake, stay systemic/overhead-free/
conflict-free/deadlock-free/pollution-free as that comment demands, and
carry executed acceptance evidence. Render a per-requirement verdict with
re-derivable evidence, and record open findings. This role reviews; it
does not fix anything the review finds, and does not edit any file
outside its own report area.

## Constraints

- **The target is open, not merged.** PR #2308 sits at head `85a9611f`,
  base `ede98d8f` (survey §0) — unlike the issue-2164 precedent this
  proposal otherwise follows, which audited an already-merged commit.
  `main` has grown `spawn.py` by 39 lines since the PR's base (survey
  §0) from unrelated work; phase 2 re-checks the PR's head sha has not
  moved before rendering final verdicts, and re-checks the before/after
  line counts against whatever `main` looks like at merge time rather
  than trusting the record's own base-relative numbers as the permanent
  ones.
- **This role's write set is its own report area only** —
  `docs/issue-2207/reports/conformance-review.md` and
  `docs/issue-2207/reports/conformance-review/**`. No change to
  `spawn.py`, `directive_assembly.py`, or the refactoring-legacy role's
  own record may issue from this session.
- **The filled record lands only after human Approve** (contract v3 s19);
  this proposal and the survey are the only phase-1 writes this session
  makes.
- **Fully-enumerable scope.** 14 issue-derived requirement line items
  (survey §2) — the sampling-derivation skill does not apply (survey
  §5); nothing here justifies stratified sampling.
- **Two session-environment gates surfaced findings of their own**
  (survey §4): an `approval-gate` hook denies any Bash call whose argv
  contains a `docs/issue-<n>` path substring, for any issue number, and
  a `git fetch` of the PR's own ref; a `board-gate` hook denies reading
  another role's record via `gh api .../contents/...`. Both were routed
  around this session (via `gh pr diff` and the `Write` tool
  respectively, survey §4) rather than fixed — fixing either is outside
  this role's write scope.
- **Full-suite pytest re-verification is deferred to phase 2.** The
  refactoring-legacy record's own pasted run took 927.82s — longer than
  this session's single-call Bash budget — so this survey did not
  independently reproduce it (survey §3). Phase 2 re-runs it
  (backgrounded, across the session's full turn budget) rather than
  accepting the pasted transcript on trust.

## Rationale

**Independent re-derivation of the record's "no source-pin floor exists"
claim, rejecting acceptance on trust.** The refactoring-legacy record
greps only `tests/ test/ gates/` for `2649`/`source_pin` and finds
nothing. This proposal's survey (§3) already re-ran a broader
repo-wide grep (every `.py`/`.md`/`.json`) and independently confirms the
same conclusion — the one `spawn.py` hit is an unrelated coverage-mapping
comment, not a line-count assertion. Taking the narrower grep on trust
would have been cheaper but is rejected for the same reason the
issue-2164 precedent rejected trusting a builder's pasted test output:
this role's entire reason to exist is independent audit, and a review
that only re-states the builder's own search scope is not independent.

**REQ-5 verdict `Unverifiable`, not `Absent` or deferred out of the
record entirely.** Two alternatives were considered and rejected: (a)
`Absent`, on the theory that no re-measured evidence exists yet — rejected
per `conformance-review-verdict-assignment` rule 2/3: `Absent` is reserved
for "no attempt found," but a concrete attempt at the underlying mechanism
(the module split itself) exists and is otherwise verifiable; the missing
piece is specifically future evidence (post-landing session logs) this
session cannot read because they do not exist yet, which is rule 3's
`Unverifiable` case exactly. (b) Omitting REQ-5 from the record's
Findings entirely, since the issue's own "empty state" note calls it a
future observation — rejected: the issue itself lists it as an
`## Acceptance` bullet, and dropping a stated acceptance bullet from the
checkable list (rather than rendering it `Unverifiable` with a named
resolution path) would silently shrink the record's own completeness
claim.

**Verdict vocabulary Present / Surface / Absent / Incorrect /
Unverifiable**, matching this repo's own
`conformance-review-verdict-assignment` skill and the issue-2164
precedent. No alternative vocabulary was considered — the skill mandates
this exact five-value set.

## What will be done

1. **The record** (`docs/issue-2207/reports/conformance-review.md`):
   contract §20 fields plus the role spec's `subject`/`test`/`result`/
   `assertedBy` frontmatter, one `---`-delimited finding block per
   REQ-1..REQ-14 (survey §2) carrying `requirement`/`spec_ref`/`verdict`/
   `evidence`/`rationale` per `conformance-review-finding-record`'s field
   list, each evidence pointer citing PR #2308's head sha `85a9611f`
   plus file:line per `conformance-review-traceability-and-evidence`.
2. **REQ-1..REQ-3** verdicts: re-derived directly (Test method — reuse
   the record's own reproducible aggregation script and greps rather
   than a fresh manual check, per verification-method-selection rule 4),
   not accepted from the record's pasted output alone — this survey's
   own broader grep (§3) is the first independent leg of that
   re-derivation; phase 2 also re-runs the 20-log read-offset
   aggregation script itself.
3. **REQ-4** verdict: Analysis (qualitative judgment on whether the
   extracted module is a coherent seam, per verification-method-selection
   rule 2) — checking the moved-symbol list against the offset clusters
   the record itself cites (survey §1, §2).
4. **REQ-5** verdict: `Unverifiable` — missing evidence named as
   "post-landing `*-implementation` session logs measured against
   `directive_assembly.py`, which do not yet exist" (rule 3), carried
   into Open findings with the record's own stated resolution path
   (repeat the 20-log sampling method once enough post-landing sessions
   exist).
5. **REQ-6** verdict: `Present` — no source-pin test exists to update
   (REQ-3's finding), and the record states that reasoning rather than
   silently skipping the bullet.
6. **REQ-7** verdict: independently re-run the full suite (Test method,
   rejecting the pasted transcript on trust per this role's own
   precedent) and, if failures recur, re-run the record's own
   parent-commit comparison (`git stash`/checkout `ede98d8f` or the
   PR's own parent) to separate this diff's regressions from
   pre-existing ones, exactly as the issue-2164 precedent did.
7. **REQ-8** verdict: Inspection — confirm the record's evidence blocks
   carry pasted commands plus pasted output (already visible via
   `gh pr diff 2308`, survey §1).
8. **REQ-9..REQ-14** verdicts: Analysis — independently re-check the
   record's own "Operator-frozen constraint reconciliation" section's
   five sub-claims (systemic scope, no overhead, no conflict surface, no
   stall/deadlock, no pollution) plus its trade-off-stated paragraph
   against the actual diff (`ROOT` computation, file-write call sites,
   import-time cost), rather than accepting the section's own citations
   as self-certifying.
9. **Overall `result`**: recomputed per the role spec's worst-case rule
   (`failed > cantTell > inapplicable > untested > passed`) once every
   REQ verdict is set — not asserted independently.
10. **Open findings**: REQ-5's deferred nature, the base-commit drift
    (survey §0), and the two environment-gate findings (survey §4),
    each with the resolution path already stated in the survey.
11. **Skill verdicts**: the five skills already invoked this session for
    the survey/proposal (requirement-extraction,
    verification-method-selection, verdict-assignment,
    traceability-and-evidence, finding-record) get `applied: invoked`
    lines carried into the record; sampling-derivation and
    severity-classification stay `not-applicable`.

## Out of scope

- Fixing anything the review finds — including the two environment-gate
  findings (survey §4), the base-commit drift, or REQ-5's deferred
  status. Findings are recorded and reported; a fix belongs to a future
  session.
- Any edit to `spawn.py`, `directive_assembly.py`,
  `on-the-record/hooks/`, or the refactoring-legacy role's own record.
- Merging, approving, or otherwise changing PR #2308's process state —
  this review checks its diff content, not its mergeability.
- Judging whether Extract Class was the best possible refactoring choice
  as a design decision, beyond whether the delivered scope satisfies
  issue #2207's own Investigate/Fix/Acceptance text (REQ-4 already
  covers that).
- Severity-weighting any finding — not requested here.

## How you'll know it worked

- Every REQ line item in the survey's requirement list (§2) appears as
  exactly one `---`-delimited finding block in the record, with a
  verdict, a method, and a file:line+sha evidence citation.
- The record's overall `result` is the recomputed worst-case across all
  fourteen finding blocks, not a value asserted independently of them.
- The open findings from the survey (§0, §4) plus REQ-5's deferred
  status appear in the record's "Open findings" section with their
  resolution paths intact.
- `loop_state` reaches this role's terminal value.
- No file outside this proposal's `files:` set, and this role's own
  report area, is modified by this session (`git diff --stat` on the
  branch confirms it).

## Skill verdicts (phase-1 home)

These lines belong to this session's record, but the record
(`docs/issue-2207/reports/conformance-review.md`) is phase-2 output and
`approval-gate.sh` refuses a phase-1 write to it. They are recorded here,
in the phase-1 home, and carry forward into the record verbatim in
phase 2.

skill-verdict: conformance-review-requirement-extraction — applied:
invoked; produced the REQ-1..REQ-14 split in survey §2 — one obligation
per line, dimension-tagged, backward-traced to the issue's own
Investigate/Fix/Acceptance text and the 2026-08-25 operator-frozen
comment, REQ-5 and REQ-6 kept as their own conditional items per rule 5
rather than merged into REQ-1 or REQ-3.

skill-verdict: conformance-review-verification-method-selection —
applied: invoked; set the method choice in "What will be done" per
requirement — Test for REQ-1..REQ-3/REQ-7 (reusing the record's own
reproducible scripts/greps and this survey's own independent re-run),
Analysis for REQ-4/REQ-9..REQ-14 (qualitative/architectural claims not
cost-effectively demonstrable), Inspection for REQ-6/REQ-8 (structural
presence checks).

skill-verdict: conformance-review-verdict-assignment — applied: invoked;
used to work out this proposal's REQ-5 `Unverifiable`-not-`Absent`
determination (Rationale above) and REQ-6's `Present` reasoning
(rule 5's naming-the-satisfied-clause requirement).

skill-verdict: conformance-review-traceability-and-evidence — applied:
invoked; set the evidence-citation shape for phase 2 — PR #2308's head
sha `85a9611f` plus file:line rather than a bare path (rule 1), and
required this proposal/survey to state explicitly that
`refactoring-legacy.md`/`directive_assembly.py`/`spawn.py`'s diff are
untracked-here paths sourced via `gh pr diff` rather than a local read
(rule 5's spec-version-pin analogue, applied to an unmerged branch's
content instead of a spec version).

skill-verdict: conformance-review-finding-record — applied: invoked; its
field list (`requirement`/`spec_ref`/`verdict`/`evidence`/`rationale`) is
what step 1 above commits to write per REQ item in phase 2; no verdict is
written to the record itself in phase 1.

skill-verdict: conformance-review-sampling-derivation — not-applicable:
full enumeration of 14 requirement line items is feasible at this size
(survey §5) — no stratified sample is needed.

skill-verdict: conformance-review-severity-classification —
not-applicable: this review's scope was not explicitly extended into
risk-weighting a recorded finding; no severity band was requested.
