---
status: approved
issue: 2204
files:
  - docs/issue-2204/reports/conformance-review.md
---

# Proposal — conformance review of issue #2204's protocol-injection/cache fix

Upstream: docs/issue-2204/reports/conformance-review/survey.md.

## Request

Audit the three commits on `issue-2204/implementation` (`924efed8`,
`262e410d`, `38f2427f`) against issue #2204's own `## Acceptance` (5
bullets) and `## Fix` (6 bullets) text: does moving protocol/contract
docs from the session read path into `--append-system-prompt`, plus
`--exclude-dynamic-system-prompt-sections` and 1h caching, actually
eliminate the measured Read round trips and the cross-cwd cache miss,
without dropping any content the session used to receive. Render a
per-requirement verdict with re-derivable evidence, and record open
findings. This role reviews; it does not fix anything the review finds,
and does not edit any file outside its own report area.

## Constraints

- **This role's write set is its own report area only** — no change to
  `pipeline.py`, `spawn.py`, or the implementation role's own record
  under `docs/issue-2204/reports/implementation.md`/`implementation/`
  may issue from this session.
- **Phase-2 write is gated.** This session's own `approval-gate.sh` hook
  denies a phase-2 write to `docs/issue-2204/reports/conformance-review.md`
  before a human Approve exists on this role's PR or issue #2204 — no
  such approval exists yet (checked live this session via the same
  denial the hook itself raised on an early Bash call). This proposal
  and its survey are this session's entire phase-1 output; the terminal
  `loop_state: reported` record itself is phase-2, deferred to the next
  session after Approve.
- **Small, fully-enumerable scope.** Three commits, two source files
  plus three test files, twelve requirement line items the issue's own
  text names (survey §2/§14) — the sampling-derivation skill does not
  apply; nothing here justifies stratified sampling.
- **`record-claim-guard.sh` governs everything written under
  `docs/issue-2204/reports/**`** — every count claim needs a `derived:`
  citation or fenced reproduction, every status/defect claim needs a
  `canonical:` citation within 3 raw lines, and every outcome
  (pass/done/complete) claim needs a `canonical:` tag that itself opens
  with an executed command (`gh `/`git `/`pytest`/`python3 `/...) or
  names this session's own live-spawn measurement — narrative
  back-references ("same command as above") do not satisfy it. The
  survey was iterated against `gates.record_lint`'s functions directly
  until it returned zero violations before being written; the record
  will need the same discipline in phase 2.
- **This review independently reproduced, not merely trusted, the
  implementation record's own pasted evidence** — a fresh live
  `claude -p` spawn with the fix's exact flags/content (survey §3), an
  independent combined pytest re-run of all three updated test files
  (survey §7), and an independent re-derivation of the two claimed
  pre-existing test failures (survey §9). One of the record's own
  literal acceptance-bar claims (REQ-1, end-to-end) is contradicted by
  this session's own live self-observation, not merely by re-reading the
  record (survey §4) — this session's own first tool call was a Read of
  a protocol doc before any task action, sourced from a separate repo
  the fix cannot touch.

## Rationale

**Independent re-execution and live reproduction, rejecting acceptance
of the implementation record's own pasted evidence on trust.** The
record already pastes three live-spawn runs and a full test suite. The
alternative of citing that pasted evidence directly, without
re-deriving any of it, was considered and rejected: conformance-review's
purpose is independent audit, and trusting pasted evidence at face value
collapses the role into a rubber stamp — the issue-2164 precedent found
a real discrepancy this way, and this review's own re-derivation
(survey §3-4) surfaced one too: this very session's live SessionStart
hook message is direct, first-hand proof that REQ-1's literal
"a spawned session's log shows no Read calls... before its first task
action" does not hold end-to-end, a fact the implementation record
already discloses as an open finding but which this review confirms
live rather than by re-reading that disclosure alone.

**Two Acceptance-section bullets carried a Surface candidate verdict
rather than either Present or Absent.** A stricter binary rule — REQ-1
and REQ-3 either fully pass or fully fail — was considered and rejected:
REQ-1's in-repo mechanism is genuinely implemented and independently
confirmed working (survey §3), and REQ-3's Read-round-trip elimination
is the dominant plausible contributor to the original baseline figure
even without its own timed re-measurement (survey §6); collapsing either
to a bare Absent would misstate real, verified work, and collapsing
either to Present would hide a real gap (an out-of-repo Read source
still fires; no direct timed re-measurement exists) from the next
reader. Surface is the skill's own value for exactly this shape:
matching evidence exists but does not establish the requirement's full
literal condition.

**Two of the six `## Fix` bullets (REQ-8, REQ-10) carried a candidate
Absent verdict rather than being folded into REQ-7/REQ-9/REQ-11's
Present verdicts as "mostly done."** Treating all six `## Fix` bullets
as one bundled item and calling it Present because most of it shipped
was considered and rejected — the requirement-extraction skill's rule 1
requires splitting bundled obligations precisely because a bundled line
lets a partial build score as one Present instead of surfacing the
missing half; REQ-8 (CLAUDE.md/`.claude/rules/`) and REQ-10 (path-scoped
decomposition) have zero trace of having been considered anywhere in the
implementation record, deviation log, or consult log (survey §11),
unlike REQ-9's SessionStart-hook alternative, which is at least cited
against a frozen decision.

## What will be done

1. **The record** (`docs/issue-2204/reports/conformance-review.md`,
   phase-2, after Approve): contract §20 fields plus the role spec's
   `subject`/`test`/`result`/`assertedBy` frontmatter, one
   `---`-delimited finding block per REQ-1..REQ-12 (survey §2) carrying
   `requirement`/`spec_ref`/`verdict`/`evidence`/`rationale` per
   `conformance-review-finding-record`'s field list, each evidence
   pointer citing file:line plus commit sha per
   `conformance-review-traceability-and-evidence`.
2. **Verdicts carried forward from this survey's candidates** (subject
   to one more evidence recheck per verdict-assignment rule 6 before
   finalizing, specifically REQ-8/REQ-10's Absent candidates):
   REQ-2, REQ-4, REQ-5, REQ-6, REQ-7, REQ-9, REQ-11, REQ-12 — `Present`;
   REQ-1, REQ-3 — `Surface`; REQ-8, REQ-10 — `Absent`.
3. **Open findings section**: the three findings the survey already
   surfaced (§13) — REQ-1's end-to-end cross-repo gap, REQ-3's missing
   timed re-measurement, REQ-8/REQ-10's unaddressed `## Fix` bullets —
   each with the resolution path already stated in the survey, carried
   into the record largely verbatim.
4. **Overall `result`**: recomputed per the role spec's own worst-case
   rule across cited finding entries (matching the issue-2164
   precedent's approach: `failed > cantTell > inapplicable > untested >
   passed`) rather than asserted independently — two Surface and two
   Absent candidates on a twelve-item list place this below `passed`.
5. **Skill verdicts**: the five skills already invoked this session
   (requirement-extraction, verification-method-selection,
   verdict-assignment, traceability-and-evidence, finding-record) get
   `applied: invoked` lines carried into the record; sampling-derivation
   and severity-classification stay `not-applicable` (survey §14; no
   severity-weighting requested).

## Out of scope

- Fixing anything the review finds — including REQ-8/REQ-10's missing
  `CLAUDE.md`/`.claude/rules/` decomposition, or filing the companion
  `tokenmaxxxer-core` issue REQ-1's open finding names. Findings are
  recorded and reported; a fix or a companion issue belongs to a future
  session.
- Any edit to `pipeline.py`, `spawn.py`, `on-the-record/hooks/`, or
  `gates/`.
- Producing REQ-3's missing timed re-measurement (a real docs-only issue
  spawn through `spawn.py`'s actual pipeline, pre-fix vs. post-fix) —
  survey §13 names this as a resolution path for a future session, not
  something this review manufactures to close its own open finding.
- Judging whether the implementation's build-now-bypass process choice
  (no phase-1 proposal round on that branch, `CORE_BUILD_NOW=1`) was the
  right call — that bypass is itself contract-authorized (v3 s19a); this
  review checks the delivered artifact against the issue's acceptance
  text, not the process that produced it.
- Severity-weighting any finding (`conformance-review-severity-classification`)
  — not requested, and this review's scope was not explicitly extended
  into risk-weighting.
- Re-litigating PR review/merge state for either branch — this review
  checks the merged-to-`issue-2204/implementation` artifact as it stands.

## How you'll know it worked

- Every REQ line item in the survey's requirement list (§2) appears as
  exactly one `---`-delimited finding block in the record, with a
  verdict, a method, and a file:line+sha evidence citation.
- The record's overall `result` is the recomputed worst-case across all
  twelve finding blocks, not a value asserted independently of them.
- The three open findings from the survey (§13) appear in the record's
  "Open findings" section with their resolution paths intact.
- `python3 -m gates.record_lint docs/issue-2204/reports/conformance-review.md`
  reports zero violations against the written record, the same bar the
  survey was held to (validated locally against `gates.record_lint`'s
  functions before this proposal was written).
- `loop_state` reaches this role's terminal value, `reported`.
- No file outside this proposal's `files:` set is modified by this
  session (`git diff --stat` on the branch confirms it).

## Skill verdicts (phase-1 home)

These lines belong to this session's record, but the record
(`docs/issue-2204/reports/conformance-review.md`) is phase-2 output and
`approval-gate.sh` refuses a phase-1 write to it. They are recorded
here, in the phase-1 home, and carry forward into the record verbatim
in phase 2.

skill-verdict: conformance-review-requirement-extraction — applied:
invoked; produced the REQ-1..REQ-12 split in survey §2 — one obligation
per line, dimension-tagged, backward-traced to the issue's own
`## Acceptance`/`## Fix` text, REQ-2's empty-state exception and
REQ-12's `--bare` note kept as their own conditional items per rule 5
rather than merged into a neighboring item.

skill-verdict: conformance-review-verification-method-selection —
applied: invoked; set the method per requirement throughout the survey —
Inspection for the static CLI-help/file-existence/code-signature checks
(§9-11), Test (independent re-execution, not a fresh manual check) for
the pytest-covered items (§7, §9), Analysis/live-reproduction for the
Read-round-trip and cache-token claims that only a real spawn can settle
(§3-6).

skill-verdict: conformance-review-verdict-assignment — applied:
invoked; used to work out the candidate verdicts this proposal's "What
will be done" §2 states — Surface (not Present) for REQ-1/REQ-3 per
rule 1 (matching evidence exists but does not establish the requirement's
literal full condition), Absent (not folded into a bundled Present) for
REQ-8/REQ-10 per rule 5 (each verdict names its own failing clause
rather than a bare label), and Present for REQ-9 via rule 4's
carry-forward logic applied to a cited substitute mechanism rather than
the literal one named.

skill-verdict: conformance-review-traceability-and-evidence — applied:
invoked; set the evidence-citation shape throughout the survey — every
cross-branch citation reads via an explicit `git show
issue-2204/implementation:<path>` command rather than a bare path (since
none of those paths exist on this review branch's own tree), one link
per contributing file (`pipeline.py` and `spawn.py` cited separately in
survey §10-11).

skill-verdict: conformance-review-finding-record — applied: invoked;
its field list (`requirement`/`spec_ref`/`verdict`/`evidence`/
`rationale`) is what "What will be done" §1 above commits to write per
REQ item in phase 2; no verdict is written to the record itself in
phase 1 (`approval-gate.sh` refuses that write pre-Approve).

skill-verdict: conformance-review-sampling-derivation — not-applicable:
full enumeration of the issue's own twelve requirement line items is
feasible at this size (survey §14) — no stratified sample is needed.

skill-verdict: conformance-review-severity-classification —
not-applicable: this review's scope was not explicitly extended into
risk-weighting a recorded finding; no severity band was requested.
