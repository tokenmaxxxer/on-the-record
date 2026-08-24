---
status: proposed
issue: 2166
files:
  - docs/issue-2166/reports/conformance-review.md
---

# Proposal — conformance review of issue #2166's skill-recommender fix

Upstream: docs/issue-2166/reports/conformance-review/survey.md.

## Request

Audit branch `issue-2166/implementation`'s two commits (`cd4c59a3`,
`64c5c571`, PR #2171, open at survey time) against issue #2166's own
Investigate/Fix/Acceptance text: did the BM25 fast-path scan-window
narrowing land as specified, with real (not asserted) evidence for its two
investigated skills, and does the delivered artifact's own internal
evidence trail hold up under independent replay. Render a per-requirement
verdict with re-derivable evidence, and record open findings. This role
reviews; it does not fix anything the review finds, and does not edit any
file outside its own report area.

## Constraints

- **The target is not yet merged.** PR #2171 is open, not merged — unlike
  a typical post-merge conformance-review target, this review evaluates a
  live, still-open PR's branch tip. Re-derivation used the branch's remote
  ref (`origin/issue-2166/implementation`) directly via a disposable `git
  worktree`, not a checkout of this role's own branch.
- **This role's write set is its own report area only.** No change to
  `consult.py`, `tests/test_retrieval_eval.py`, or the implementation
  role's own record under `docs/issue-2166/reports/implementation.md`/
  `implementation/` may issue from this session.
- **Small, fully-enumerable scope.** Two commits, three touched files,
  REQ-1 through REQ-7 (REQ-6 split into REQ-6a/REQ-6b, one verdict per
  finding) plus one reviewer-surfaced finding (REQ-8) — the
  sampling-derivation skill does not apply (survey §7).
- **`record-claim-guard.sh` governs everything written under
  `docs/issue-2166/reports/**`** — count claims need a `derived:` citation
  or fenced reproduction, state/defect claims need a `canonical:` tag
  within 3 lines, outcome claims need an executed-live citation. The
  survey's evidence blocks are already built to this shape and carry the
  same shape into phase 2.
- **This session's own environment denies one class of command,
  reproducing a defect issue-2164's conformance-review session already
  hit.** Any Bash invocation naming a `test/*.py` path (the singular
  directory) is refused by `approval-gate.sh`'s `gh issue view <n> --json
  state,comments,state_reason` call, which the installed `gh` CLI rejects
  outright (`Unknown JSON field: "state_reason"`) — fail-closed regardless
  of actual approval state (survey §5). The record must state this
  plainly as the reason the combined 4-file pytest reproduction is
  partial (3 of 4 files unreachable), not silently work around it or
  claim full reproduction it did not achieve.
- **The after-proposal warrant-hunter dispatch is attempted once, in
  background, after this proposal lands** — per the warrant protocol; its
  result (or non-completion, per issue-2164's precedent) will be noted in
  the record rather than blocking this proposal.

## Rationale

**Independent re-derivation of the implementation record's own cited BM25
ranks, rejecting acceptance of the record's pasted numbers on trust.** The
cheaper option — read the implementation record's `derived:` block and
take its rank-13/rank-10 figures as established — was rejected:
conformance-review's entire reason to exist is independent audit, and
trusting a builder's own pasted evidence at face value collapses the role
into a rubber stamp. Independently re-running the exact same
`spawn._bm25_cross_family_scores` call against issue #525's real body
(survey §3) is what surfaced the actual finding: the record's own number
(rank 13) reproduces exactly, but the shipped code comment and test
docstring in the same commit assert a different, non-reproducing number
(47) for the same named input. Trusting the record's prose without
replaying the underlying call would have missed this entirely.

**Verdict vocabulary Present / Surface / Absent / Incorrect / Unverifiable,
matching this repo's own `conformance-review-verdict-assignment` skill and
issue-2164's prior conformance-review proposal.** No alternative
vocabulary was considered — the skill mandates this exact five-value set,
and a repo-local variant would cost cross-record comparability for no
benefit here.

**The rank-47/rank-13 discrepancy is recorded as its own finding (REQ-8),
not folded into REQ-3's verdict or silently omitted as "close enough."**
Two alternatives were considered and rejected: (a) treat it as immaterial
prose noise and leave it out of the record, since the fix's actual logic
(the topN slice) is correct and independently tested regardless of which
number a comment cites — rejected because a future maintainer reading
`consult.py`'s own comment has no way to know it cites a non-reproducing
number, and the whole point of `conformance-review-traceability-and-evidence`
is that a reader can re-derive what a record/comment claims; silently
dropping a confirmed, reproducible mismatch defeats that. (b) downgrade
REQ-3 itself to Incorrect or Surface because of this — rejected because
the mechanism-level fix (the scan-window narrowing) is independently
verified correct and covered by a passing regression test (survey §3);
conflating a documentation/citation defect with a functional-correctness
verdict would misrepresent which part of the delivery is actually wrong.

## What will be done

1. **The record** (`docs/issue-2166/reports/conformance-review.md`):
   contract §20 fields plus the role spec's `subject`/`test`/`result`/
   `assertedBy` frontmatter, one `---`-delimited finding block per
   REQ-1..REQ-5, REQ-6a, REQ-6b, REQ-7, and REQ-8 (survey §2, §6) carrying
   `requirement`/
   `spec_ref`/`verdict`/`evidence`/`rationale` per
   `conformance-review-finding-record`'s field list, each evidence pointer
   citing file:line plus the relevant commit sha per
   `conformance-review-traceability-and-evidence`.
2. **Verdicts**: REQ-1, REQ-3, REQ-4, REQ-5, and REQ-6a —
   `Present` (survey §3-4, independently re-derived, not taken on trust).
   REQ-2 and REQ-6b — `Unverifiable` (survey §4, issue #527
   unresolvable in either repository checked). REQ-7 — `Surface` (survey
   §5, partial independent reproduction — 2 of the 4 cited evidence
   commands re-executed cleanly, the other 2 blocked by the environment
   defect). REQ-8 (new, reviewer-surfaced) — `Incorrect`, with
   `spec_vs_built` naming the record's own reproducible rank versus the
   shipped comment/docstring's non-reproducing "47" (survey §6 finding
   1).
3. **Open findings section**: the four findings the survey already
   surfaces (§6) — the REQ-8 evidence-citation mismatch, REQ-7's
   partial-verification gap, the live `approval-gate.sh`/`gh
   state_reason` defect, and the minor REQ-1 description-reading-depth
   note — each with the resolution path already stated in the survey,
   carried into the record largely verbatim.
4. **Overall `result`**: recomputed per the role spec's own worst-case
   rule (`failed > cantTell > inapplicable > untested > passed`), applied
   to a per-finding value each finding's own `verdict` maps to — not a
   direct substitution of any one finding's `verdict` for the
   frontmatter's `result`. `conformance-review-finding-record` rule 3.3
   is explicit that the two five-value sets "do not map 1:1, this is
   vocabulary alignment, not a swap" (a design error a background
   warrant-hunter caught in this proposal's own first draft — see
   docs/issue-2166/reports/conformance-review/deviation-log.md). The
   mapping this record uses, argued once here rather than left implicit:
   `Present` conforms outright, so it maps to the value meaning the check
   ran and held. `Unverifiable` names its own missing-evidence location
   rather than asserting either a hold or a violation, so it maps to the
   value meaning insufficient information to tell. `Surface`, `Absent`,
   and `Incorrect` each describe the requirement not actually holding —
   present-but-wrong, nothing-found, and actively-contradicts
   respectively — so each maps to the value meaning the check ran and did
   not hold. Applying this per finding: REQ-1/REQ-3/REQ-4/REQ-5/REQ-6a
   map to the held-value; REQ-2/REQ-6b map to the insufficient-
   information-value; REQ-7 (`Surface`) and REQ-8 (`Incorrect`) both map
   to the did-not-hold-value. The worst-case across those mapped values is
   the did-not-hold-value — the record's `result` frontmatter field takes
   that value, stated next to a plain note that the functional fix itself
   (REQ-1/REQ-3/REQ-4/REQ-5/REQ-6a) independently verifies as holding, so
   the overall value reflects REQ-7's partial-verification gap and REQ-8's
   citation defect specifically, not a claim that the delivered behavior
   is broken.
5. **Skill verdicts**: the five skills already invoked this session for
   the survey (requirement-extraction, verification-method-selection,
   verdict-assignment, traceability-and-evidence, finding-record) get
   `applied: invoked` lines carried into the record; sampling-derivation,
   severity-classification, and implementation-audit stay
   `not-applicable` (survey §7; no severity-weighting or separate
   two-session audit protocol was requested — this role's own contract
   already specifies the audit process).

## Out of scope

- Fixing anything the review finds — including the `consult.py`/
  `tests/test_retrieval_eval.py` rank-citation mismatch, or the
  `approval-gate.sh`/`gh state_reason` defect. Findings are recorded and
  reported; a fix belongs to a future implementation session.
- Any edit to `consult.py`, `tests/test_retrieval_eval.py`,
  `on-the-record/hooks/`, or `gates/`.
- Re-litigating PR #2171's process state (approvals, merge readiness) —
  it is still open; this review checks the branch tip as it stands.
- Severity-weighting any finding — a separate, explicitly-scoped
  extension of a review (`conformance-review-severity-classification`),
  not part of ordinary fidelity-checking, and was not requested here.
- Judging whether the implementation's scope choice (fixing
  `work-in-english`'s exposure via the retrieval mechanism rather than
  either skill's own description) was the right design call — REQ-5/REQ-6
  already cover whether the delivered scope satisfies the issue's own
  acceptance text, which is what this review checks.

## How you'll know it worked

- Every REQ line item in the survey's requirement list (§2, REQ-6 split
  into REQ-6a/REQ-6b), plus REQ-8, appears as exactly one `---`-delimited
  finding block in the record, with a verdict, a method, and a
  file:line+sha evidence citation.
- The record's overall `result` is the recomputed worst-case across the
  per-finding values step 4's mapping assigns every finding block, not a
  direct substitution of any single finding's own `verdict`.
- The four open findings from the survey (§6) appear in the record's
  "Open findings" section with their resolution paths intact.
- `loop_state` reaches this role's terminal value, `reported`.
- No file outside this proposal's `files:` set is modified by this
  session (`git diff --stat` on the branch confirms it).

## Skill verdicts (phase-1 home)

These lines belong to this session's record, but the record
(`docs/issue-2166/reports/conformance-review.md`) is phase-2 output and
`approval-gate.sh` refuses a phase-1 write to it. They are recorded here,
in the phase-1 home, and carry forward into the record verbatim in phase
2.

skill-verdict: conformance-review-requirement-extraction — applied:
invoked; produced the REQ-1..REQ-7 split in survey §2 — one obligation per
line, dimension-tagged, backward-traced to the issue's own Investigate/
Fix/Acceptance text, REQ-2 kept as its own unverifiable-as-written item
per rule 2, REQ-5 kept conditional per rule 5 rather than merged into
REQ-1/REQ-3.

skill-verdict: conformance-review-verification-method-selection —
applied: invoked; set survey §3-5's method choice per requirement — Test
(reusing/replaying the implementation record's own reproduction and
regression test) for REQ-1/REQ-3/REQ-7, Inspection for REQ-4 (a
structural git-log fact).

skill-verdict: conformance-review-verdict-assignment — applied: invoked;
used to work out the REQ-1..REQ-8 verdicts this proposal's "What will be
done" states (five `Present`, two `Unverifiable`, one `Surface`, one new
`Incorrect`), including the rule-6 re-check before finalizing REQ-8's
Incorrect verdict (survey §3's replay run a second time to confirm the
13-vs-47 discrepancy was not a first-pass fluke) and rule-2's Incorrect-
not-Absent choice (the shipped artifact actively contradicts its own
cited reproduction, rather than merely omitting one).

skill-verdict: conformance-review-traceability-and-evidence — applied:
invoked; set the evidence-citation shape throughout the survey — file:line
plus commit sha rather than a bare path, one link per contributing file
(`consult.py` and `tests/test_retrieval_eval.py` cited separately in
survey §6 finding 1).

skill-verdict: conformance-review-finding-record — applied: invoked; its
field list (`requirement`/`spec_ref`/`verdict`/`evidence`/`rationale`,
plus `spec_vs_built` for REQ-8's Incorrect verdict) is what step 1 above
commits to write per REQ item in phase 2; no verdict is written to the
record itself in phase 1.

skill-verdict: conformance-review-sampling-derivation — not-applicable:
full enumeration of the issue's own named line items (REQ-1 through
REQ-7, REQ-6 split into REQ-6a/REQ-6b) plus one reviewer-surfaced finding
(REQ-8) is feasible at this size (survey §7) — no stratified sample is
needed.

skill-verdict: conformance-review-severity-classification —
not-applicable: this review's scope was not explicitly extended into
risk-weighting a recorded finding; no severity band was requested.

skill-verdict: implementation-audit — not-applicable: this role's own
contract (role-handoff contract v3 s19) already specifies a full
audit/evidence process for this session; the skill's own two-session
builder-extracts-claims-then-structurally-independent-evaluator protocol
is a distinct workflow this task does not separately invoke.
