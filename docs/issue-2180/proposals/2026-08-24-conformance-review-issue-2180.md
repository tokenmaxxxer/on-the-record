---
status: proposed
issue: 2180
files:
  - docs/issue-2180/reports/conformance-review.md
---

# Proposal — conformance review of issue #2180's returned-pr signal-shape fix

Upstream: docs/issue-2180/reports/conformance-review/survey.md.

## Request

Audit `issue-2180/implementation`'s delivery (PR #2181, four commits
tipped at `3e67434d`) against issue #2180's own "Fix"/"Acceptance"/
empty-state text: did the distinct `[new-returned-pr]` marker and the
collapsed `[returned-pr-pending]` summary line land as specified, does
the "already-surfaced" dedup survive a phase1→phase2 transition, does
the empty-state (first-ever tick) clause hold, does existing watchdog/
Monitor behavior stay unchanged, and does the record carry real executed
acceptance evidence. Render a per-requirement verdict with re-derivable
evidence, and record the one open finding this review's own independent
replay surfaced. This role reviews; it does not fix anything the review
finds, and does not edit any file outside its own report area.

## Constraints

- **The target is a landed delivery, not yet on `main`.** `PR #2181`
  carries `issue-2180/implementation`'s four commits, tip `3e67434d`
  (survey §"git log"); nothing about the diff changes between now and
  when the record is written, but this review's own working tree does
  not carry the fix on disk (branched before it landed), so every
  independent test re-run in the survey first had to temporarily bring
  the two changed files in via `git checkout issue-2180/implementation
  --`, then restore `HEAD` afterward (survey §3, §5).
- **This role's write set is its own report area only.** No change to
  `on-the-record/monitors/poll-heartbeat.sh`,
  `on-the-record/monitors/test_poll_heartbeat.py`, or the implementation
  role's own record under `docs/issue-2180/reports/implementation.md`/
  `implementation/` may issue from this session — confirmed by
  restoring the working tree to `HEAD` after each temporary checkout
  (survey §3, §5).
- **Small, fully-enumerable scope.** One PR, two source files, seven
  issue-derived requirement line items — the sampling-derivation skill
  does not apply (survey §9); nothing here justifies stratified
  sampling.
- **`record-claim-guard.sh` governs everything written under
  `docs/issue-2180/reports/**`** — count claims need a `derived:`
  citation or fenced reproduction, state/defect claims need a
  `canonical:` tag within 3 lines, outcome claims need an executed-live
  citation. `record-claim-guard.sh`'s own scope check
  (`docs/issue-[^/]+/reports/` prefix, no path-depth limit) covers the
  nested survey path, and did in fact deny an earlier draft of the
  survey on this exact basis (five citation-shape violations, fixed
  before the file was written). Before writing the final survey, this
  session also called `gates/record_lint.py`'s individual check
  functions (`bare_count_claim_check`, `canonical_source_claim_check`,
  `outcome_claim_citation_check`, `orphaned_path_reference_check`,
  `git_tracked_path_reference_check`) directly against the draft text —
  the same functions `record-claim-guard.sh` itself calls — and got a
  clean result before writing. This is distinct from
  `record_lint.py`'s own CLI/`lint_record()` path, which is gated by a
  stricter `RECORD_PATH` regex (`docs/issue-<n>/reports/<role>.md`,
  one path segment only) that does not recognize a nested
  `reports/<role>/survey.md` path at all — running
  `python3 gates/record_lint.py docs/issue-2180/reports/conformance-review/survey.md`
  reports "not a record path shape" rather than a pass, a gap in that
  CLI wrapper's own path recognition, not evidence that the survey's
  citations are ungrounded (a before-landing warrant-hunt dispatch on
  this transition confirmed the CLI-wrapper gap live; see
  `docs/issue-2180/reports/conformance-review/2026-08-24-hunt-2026-08-24-conformance-review-issue-2180.md`).
  The record carries the same citation shape into phase 2.
- **This session's own `approval-gate.sh` refuses two classes of write**
  before a human Approve: any change to `docs/issue-2180/reports/
  implementation.md` or `implementation/**` (a different role's phase-2
  homes), and the write this proposal's `files:` names — both are read
  freely (a `git show`/`git diff` with no output redirection is a
  read-only op the gate allows) but not written from this session.

## Rationale

**Independent re-execution of the implementation record's cited tests,
rejecting acceptance of the record's own pasted output on trust.** The
implementation record already pastes four clean `acceptance:` blocks
covering every acceptance bullet the issue names. Taking that on trust
was the cheaper option and is rejected: conformance-review's entire
reason to exist is independent audit, and trusting a builder's own
pasted evidence at face value collapses the role into a rubber stamp.
The survey's independent re-run (temporarily checking out the fix into
this session's own working tree, per the Constraints above) is what
surfaced the actual finding: the broader five-file suite's
`xfailed`/`xpassed` split does not line up between this session's run
and the record's own pasted transcript, even though every other block
reproduces exactly (survey §5-6).

**Attaching the discrepancy to REQ-6 (the evidentiary requirement)
rather than to REQ-4 (the scope-boundary "unchanged behavior"
requirement), rejecting the alternative of folding it into REQ-4's own
verdict.** REQ-4's two directly-relevant suites — the
`on-the-record/monitors/test_poll_heartbeat.py` and `gates/
test_poll_heartbeat_delta.py` runs — reproduce with no difference at
all (survey §3, §5); the discrepancy sits specifically in the record's
own transcript for a broader, unrelated-scope check, not in evidence
that this diff changed anything about watchdog/Monitor behavior. Folding
it into REQ-4 would understate that requirement's own strong, exactly-
reproducing evidence and would misdescribe what actually diverges — the
record's claim, not the code's behavior.

**Verdict vocabulary Present / Surface / Absent / Incorrect /
Unverifiable, matching this repo's own `conformance-review-verdict-assignment`
skill and prior conformance-review proposals (e.g. issue-2164's).** No
alternative vocabulary was considered for this proposal — the skill
mandates this exact five-value set, and inventing a repo-local variant
would cost cross-record comparability for no benefit here.

## What will be done

1. **The record** (`docs/issue-2180/reports/conformance-review.md`):
   contract §20 fields plus the role spec's `subject`/`test`/`result`/
   `assertedBy` frontmatter, one `---`-delimited finding block per
   REQ-1..REQ-7 (survey §2) carrying `requirement`/`spec_ref`/`verdict`/
   `evidence`/`rationale` per `conformance-review-finding-record`'s
   field list, each evidence pointer citing file:line plus the
   `3271d8f8`/`f33a7a62` commit shas per
   `conformance-review-traceability-and-evidence`.
2. **Verdicts for REQ-1, REQ-2, REQ-3, REQ-5**: `Present` — each has a
   direct, independently-reproduced test (survey §3-4) plus a
   source-level assertion match to the issue's own wording.
3. **Verdict for REQ-4** (existing watchdog/Monitor behavior otherwise
   unchanged): `Present` — `relay.py`/`watchdog.py` carry no diff
   (survey §5), both directly-relevant regression suites reproduce with
   no difference, and `bash -n` reports no syntax break.
4. **Verdict for REQ-6** (executed acceptance evidence in the record):
   `Surface` — the record's four evidence blocks have the right shape,
   but one of the four does not, on independent replay, establish the
   exact `xfailed`/`xpassed` split it states (survey §6), even though
   the pass count and total xfail-adjacent count both line up.
5. **Verdict for REQ-7** (the optional aging-line-escalation
   suggestion): `Unverifiable` — the issue itself states no acceptance
   threshold for this suggestion (requirement-extraction rule 2), and
   the implementation record's own "Why" section states plainly it was
   left out because it is a suggestion, not a requirement (survey §7).
   Recorded as `inapplicable` in the overall-result computation (step 6
   below), not `cantTell`, since nothing here is missing evidence — the
   requirement itself sets no checkable bar.
6. **Overall `result`**: recomputed per the role spec's own rule
   (worst-case across cited test entries, `failed > cantTell >
   inapplicable > untested > passed`) rather than asserted
   independently — driven down from `passed` by REQ-6's `Surface`
   finding, landing on `cantTell` (REQ-7's `inapplicable` does not
   change this outcome, since `cantTell` already outranks
   `inapplicable`).
7. **Open findings section**: the one finding the survey already
   surfaced (survey §8) — the broader-suite `xfailed`/`xpassed` split,
   with its resolution path (a candidate separate flaky-test issue, out
   of this review's own scope to pin down further) carried into the
   record largely verbatim.
8. **Skill verdicts**: the five skills already invoked this session for
   the survey and this proposal (requirement-extraction,
   verification-method-selection, verdict-assignment,
   traceability-and-evidence, finding-record) get `applied: invoked`
   lines carried into the record; sampling-derivation and
   severity-classification stay `not-applicable` (survey §9; no
   severity-weighting was requested).

## Out of scope

- Fixing anything the review finds — including identifying which of
  the seven `xfail`-marked tests in `on-the-record/hooks/
  test_monitor_notice.py`/`tests/test_spawn_observation_recovery.py` is
  the timing-dependent one, or re-running the broader suite again to
  see if the split changes a third time. Findings are recorded and
  reported; a fix or further diagnosis belongs to a future session.
- Any edit to `on-the-record/monitors/poll-heartbeat.sh`,
  `on-the-record/monitors/test_poll_heartbeat.py`, or any file under
  `docs/issue-2180/reports/implementation.md`/`implementation/**`.
- Implementing REQ-7's optional aging-line-escalation suggestion, or
  judging whether the implementation's choice not to build it was the
  right call — the issue itself states no threshold, so there is
  nothing to check it against beyond confirming it was not silently
  dropped (REQ-7's own verdict covers that).
- Severity-weighting any finding — a separate, explicitly-scoped
  extension of a review (`conformance-review-severity-classification`),
  not part of ordinary fidelity-checking, and was not requested here.
- Re-litigating PR #2181's process state (approvals, merge readiness) —
  this review checks the delivered diff on its own branch, independent
  of where the PR sits in GitHub's own review flow.

## How you'll know it worked

- Every REQ line item in the survey's requirement list (survey §2)
  appears as exactly one `---`-delimited finding block in the record,
  with a verdict, a method, and a file:line+sha evidence citation.
- The record's overall `result` is the recomputed worst-case across all
  seven finding blocks, not a value asserted independently of them.
- The one open finding from the survey (survey §8) appears in the
  record's "Open findings" section with its resolution path intact.
- `gates/record_lint.py`'s check functions (or the equivalent
  `record-claim-guard.sh` checks) report zero violations against the
  written record, the same bar the survey was held to before this
  proposal was written.
- `loop_state` reaches this role's terminal value, `reported`.
- No file outside this proposal's `files:` set is modified by this
  session (`git diff --stat` on the branch confirms it).

## Skill verdicts (phase-1 home)

These lines belong to this session's record, but the record
(`docs/issue-2180/reports/conformance-review.md`) is phase-2 output and
`approval-gate.sh` refuses a phase-1 write to it. They are recorded
here, in the phase-1 home, and carry forward into the record verbatim
in phase 2.

skill-verdict: conformance-review-requirement-extraction — applied:
invoked; produced the REQ-1..REQ-7 split in survey §2 — one obligation
per line, dimension-tagged, backward-traced to the issue's own "Fix"/
"Acceptance"/empty-state text, REQ-3 kept as its own conditional item
per rule 5, REQ-7 flagged unverifiable-as-written per rule 2 rather
than silently dropped or scored against an invented threshold.

skill-verdict: conformance-review-verification-method-selection —
applied: invoked; set survey §3-6's method choice per requirement —
Test (reusing and independently re-running the repo's own pytest/plain
test files) for REQ-1/REQ-2/REQ-3/REQ-4/REQ-5, Inspection for REQ-4's
`relay.py`/`watchdog.py`-untouched check and REQ-6's evidence-shape
check, Analysis-adjacent grep-based characterization for the REQ-6
discrepancy's root cause (survey §6).

skill-verdict: conformance-review-verdict-assignment — applied:
invoked; used to work out the REQ-1..REQ-7 verdicts this proposal's
"What will be done" states (five `Present`, one `Surface`, one
`Unverifiable`), and to decide the discrepancy belongs to REQ-6 (rule 1:
Surface for evidence that exists in the right shape but doesn't
establish the exact claimed condition) rather than downgrading REQ-4.

skill-verdict: conformance-review-traceability-and-evidence — applied:
invoked; set the evidence-citation shape throughout the survey — file:
line plus the `3271d8f8`/`f33a7a62` commit shas rather than a bare
path, one link per contributing file (`on-the-record/monitors/
poll-heartbeat.sh` and `on-the-record/monitors/test_poll_heartbeat.py`
cited separately in survey §3-5).

skill-verdict: conformance-review-finding-record — applied: invoked;
its field list (`requirement`/`spec_ref`/`verdict`/`evidence`/
`rationale`) is what step 1 above commits to write per REQ item in
phase 2; no verdict is written to the record itself in phase 1.

skill-verdict: conformance-review-sampling-derivation — not-applicable:
full enumeration of the issue's own seven derived line items is
feasible at this size (survey §9) — no stratified sample is needed.

skill-verdict: conformance-review-severity-classification —
not-applicable: this review's scope was not explicitly extended into
risk-weighting a recorded finding; no severity band was requested.
