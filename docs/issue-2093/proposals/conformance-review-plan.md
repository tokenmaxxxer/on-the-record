---
status: proposed
issue: 2093
files:
  - docs/issue-2093/reports/conformance-review.md
  - docs/issue-2093/reports/conformance-review/requirements.md
  - docs/issue-2093/reports/conformance-review/evidence.md
  - docs/issue-2093/reports/deviation-log.md
---

# Proposal — conformance review of issue #2093's hook-crash class fix

Upstream: docs/issue-2093/reports/conformance-review/survey.md and
docs/issue-2093/reports/conformance-review/scout-brief.md.

## Request

Review, against issue #2093's own text, what the implementation role delivers
on branch `issue-2093/implementation`: a shared total hook-input parser, a
crash-conformance test driven from `hooks.json`, and a fail-open ledger. Render
a per-requirement verdict with evidence a later reader can re-derive, and
record open findings. This role reviews; it does not fix, and does not edit any
file the implementation role owns.

## Constraints

- **The target is mostly not built yet.** At the surveyed commit the
  implementation branch carries four documents and no hook code (survey §1).
  The plan must therefore produce an honest verdict set at execution time
  whatever has landed by then, rather than assuming code exists.
- **This role's write set is its own report area only.** Contract v3: a role
  writes its own record area and never another role's. No change to
  `on-the-record/hooks/**` may issue from this session, including a change
  that would "fix" a finding.
- **Two dimensions, 58 x 9 cells.** 58 `hooks.json` registrations against a
  nine-case edge corpus (survey §3) cannot each be re-executed and eyeballed
  inside a review, so the scope needs a stated sampling derivation, not a
  silent spot-check.
- **One guard is deliberately fail-closed.** `deliverable-guard.sh` denies with
  exit 2 on unverifiable stdin by design (survey §4). Exit 2 there is
  conformant behaviour and the review must not file it as a defect.
- **Provenance is fixed by the issue**: `executed-unit via pytest`. An
  inspection-only verdict does not discharge an acceptance check whose stated
  provenance is an executed unit test.
- **`record-claim-guard.sh` governs everything written under
  `docs/issue-2093/reports/**`** — count claims need a `derived:` reproduction,
  state and defect claims need a `canonical:` tag, outcome claims need an
  executed-live citation. The review's evidence format has to be built to that
  shape from the start.

## Rationale

**Requirement list keyed to the Acceptance section, rejecting a list
re-derived from the Scope section.** The issue's Scope section has three
design-bearing items and reads like the natural requirement list, and an
earlier draft of this plan keyed to it. Rejected: the Acceptance section
already states the checkable obligations *and* their provenance, and the
requirement-extraction discipline says an issue's own stated derivation is used
verbatim rather than re-derived — re-deriving silently changes what "complete"
means mid-review. Scope items are kept as backward-trace sources for the
Acceptance checks (which Scope item each check descends from), not as
independent verdict rows.

**Stratified sampling with the high-impact stratum fully enumerated, rejecting
both full enumeration and a flat 10% spot-check.** Full enumeration of 522
cells was a live option because the conformance test itself will execute all of
them — the review could simply re-run it. Rejected as the *review's* method
because re-running the suite verifies that the suite is green, not that the
suite checks what the issue asked; those are different claims and only the
second is this role's job. A flat spot-check was rejected for the opposite
reason: it would dilute the small critical stratum (the five `cd`-extraction
hooks that carry the #2092 defect, plus the fail-closed guard) into a mass of
low-risk registrations. The chosen shape — enumerate the high-impact stratum
whole, sample the remainder pairwise across the hook x corpus dimensions — is
what the sampling discipline prescribes when impact tiers differ.

**Verdict vocabulary Present / Surface / Absent / Incorrect / Unverifiable,
rejecting issue-749's MET/PARTIAL/GAP.** The repo precedent is real and
rejecting it costs cross-record comparability (survey §5). Chosen anyway
because PARTIAL cannot distinguish the two states that dominate this specific
review: a check whose artifact exists but only tests the shape of the thing
(Surface), versus a check whose artifact is absent entirely (Absent). Both
would collapse into PARTIAL, and that distinction is the review's main product
here.

**Negative control re-executed by the review, rejecting acceptance of the
implementation's own claim of one.** The implementation proposal already
promises a negative control. Taking that on trust was the cheaper option and is
rejected: the scout brief's central must-be is that an all-green result must be
shown non-vacuous by an independent party, and the party who wrote the test is
not independent of it.

**Verdicts on absent artifacts recorded as Absent, rejecting Unverifiable.**
Unverifiable is for a requirement the reviewer *cannot* check; a requirement
whose artifact does not exist has been checked, and the answer is no. Marking
it Unverifiable would launder a missing deliverable into a reviewer limitation.

## What will be done

1. **Requirement extraction** — `docs/issue-2093/reports/conformance-review/requirements.md`:
   one line per obligation, bundled `and` clauses split (acceptance check 2
   bundles tilde expansion, heredoc, and malformed JSON into one line — three
   obligations), each row tagged with its dimension (functional-behavior,
   error-handling, edge-case, scope-boundary), each backward-traced to the
   issue line it came from, and any obligation with no observable success
   condition flagged unverifiable-as-written rather than given an invented
   threshold.
2. **Verification-method assignment** — one method per requirement row before
   any verdict: Test for the three acceptance checks (their stated provenance
   is executed-unit, and an existing repo test is reused as its own evidence
   rather than re-derived); Inspection for structural obligations (the ledger
   line format, the parser's import direction, `hooks.json` rewiring);
   Analysis for the obligations about consumer-repo deployment, which this
   session cannot reproduce.
3. **Sampling derivation, stated before the draw** — population 58
   registrations x 9 corpus cases; strata: (a) high-impact — the five
   `cd`-extraction hooks named in the implementation proposal step 6 plus the
   fail-closed `deliverable-guard.sh` — enumerated whole, no sampling; (b) the
   remaining registrations — pairwise coverage so every corpus case appears
   against at least one registration of each event type. Population size,
   stratum definitions, per-stratum size, and selection method all recorded;
   the sample is fixed before execution and is not enlarged afterwards if it
   comes back empty.
4. **Evidence execution and capture** — `docs/issue-2093/reports/conformance-review/evidence.md`:
   the actual commands run (`python3 -m pytest ...` per acceptance check) with
   their pasted output including any SKIPPED lines, the negative-control run
   and its result, and per sampled cell the signal it was judged on (exit code,
   presence of `Traceback` on stderr). Every citation carries file:line plus
   the commit sha read; a requirement whose evidence spans several files gets
   one link per contributing file.
5. **The record** — `docs/issue-2093/reports/conformance-review.md`: contract
   §20 fields, a per-requirement verdict table (Present / Surface / Absent /
   Incorrect / Unverifiable) with the Evidence column pointing into
   evidence.md, a provenance note if the implementation record has still not
   landed, and Open findings — including the candidate already carried from
   survey §6 (the implementation proposal asserts #2092 has not landed, while
   main's tip commit is titled as the #2092 fix).
6. **Deviation log** — `docs/issue-2093/reports/deviation-log.md` gets a line
   per deviation, or stays unwritten if none occurs.

## Out of scope

- Fixing anything the review finds. Findings are recorded and reported; a fix
  belongs to the implementation role on its own branch.
- Any edit under `on-the-record/hooks/`, `gates/`, or `test/`.
- Generating new crash inputs by fuzzing or mutation beyond the single
  negative control (scout brief, Skip).
- Judging the implementation's design choices on their merits — parser
  placement, ledger location, wrapper-vs-preamble. Those were settled in the
  approved implementation proposal; this review checks fidelity to the issue,
  not the wisdom of an approved design.
- Reviewing PR #2095's process state (approvals, merge readiness).
- Severity-weighting the findings. That is a separate, explicitly-scoped
  extension of a review, not part of ordinary fidelity-checking.

## How you'll know it worked

- Every `check:` line in issue #2093's Acceptance section appears as at least
  one row in requirements.md, with each bundled clause split out — and each row
  carries a verdict, a method, and an evidence citation in the record.
- The record's sampling derivation states population, strata, per-stratum
  sample size, and selection method, so a later reader can redraw the same
  sample.
- Every executed-unit acceptance check is discharged by pasted command output
  in evidence.md, not by a file read; where the artifact is absent, the record
  says Absent and names the diff that shows the absence.
- The negative control is re-executed by this session and its red result is
  pasted; if it cannot be made red, that fact is the review's headline finding.
- No file outside this proposal's `files:` set is modified by this session
  (`git diff --stat` on the branch confirms it).

## Skill verdicts (phase-1 home)

These lines belong to this session's record, but the record
(docs/issue-2093/reports/conformance-review.md) is phase-2 output and
`approval-gate.sh` refuses a phase-1 write to it. They are recorded here, in
the phase-1 home, and carry forward into the record verbatim in phase 2.

skill-verdict: conformance-review-requirement-extraction — applied: invoked;
its rules set step 1 above — one obligation per line, acceptance check 2's
bundled tilde/heredoc/malformed-JSON clause split into three, dimension tags,
and the issue's own Acceptance section used verbatim as the scope instead of a
re-derived N.

skill-verdict: conformance-review-verification-method-selection — applied:
invoked; its four-method taxonomy is step 2 above — Test for the executed-unit
acceptance checks (existing repo tests reused as their own evidence),
Inspection for structural obligations, Analysis for the consumer-repo
deployment obligations this session cannot reproduce.

skill-verdict: conformance-review-sampling-derivation — applied: invoked; its
rules produced step 3 above — stratify before drawing, enumerate the
high-impact stratum whole rather than sampling it, pairwise coverage over the
two independent dimensions, state the derivation, and never enlarge the sample
after an empty draw.

skill-verdict: conformance-review-traceability-and-evidence — applied:
invoked; its rules set the evidence format in step 4 above — file:line plus
commit sha rather than a bare path, one link per contributing file,
backward-trace to the issue line before checking the artifact, and one named
spec version (survey §2).

skill-verdict: conformance-review-verdict-assignment — not-applicable: no
verdict is assigned in phase 1; the vocabulary choice was settled in the
Rationale above, and the assignment itself belongs to phase 2.

skill-verdict: conformance-review-finding-record — not-applicable: its trigger
is the auditing/draft-reported state with a requirement already checked; no
requirement has been checked yet, so no finding exists to record.

skill-verdict: conformance-review-severity-classification — not-applicable:
its trigger requires the review's scope to have been explicitly extended into
risk-weighting an already-recorded finding; no such extension was requested and
no finding is recorded.
