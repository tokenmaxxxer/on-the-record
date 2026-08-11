---
subject: issue-791
role: product-discovery
kind: proposal
status: proposed
files:
  - docs/issue-791/proposals/2026-08-11-read-before-claim-grounding-gate.md
---

# Proposal: default-on grounding check for defect/root-cause claims

## Request, paraphrased

Prevent a role session from committing a record that claims a
defect/root-cause on the strength of a bare grep/keyword hit — require
that the citation show actual multi-line, in-context read content, and
catch this by default (hook/directive only, no CI, no explicit
invocation), composed with the existing `record_lint.py` citation
checks (#333/#310/#331/#330). Live trigger: a filtered `spawn.py ps`
line was misread as "all sessions gone" when the raw output showed all
alive.

## JTBD (carried from the survey, unchanged)

See `docs/issue-791/reports/product-discovery/survey.md` — job
performer: any defect-claiming role session; job: ground the claim in
context, not an isolated match; circumstance: nothing today
distinguishes the two in the written record; desired outcome: a
mechanical check catches the difference, additive/doc records untouched.

## What counts as "read" vs. "skim"

- **Skim (not sufficient evidence):** a citation is a single line or
  token match with no surrounding lines — e.g. a copy-pasted grep hit,
  or a `file:line` reference with no quoted content at all. Legal for
  *locating* a candidate cause; not legal as the *evidence* for a claim.
- **Read (sufficient evidence):** a citation quotes ≥3 contiguous lines
  of the actual source/design/output content around the cited line,
  attributed to a real `file:line` (or, for command output that isn't a
  file — e.g. raw `ps` — a fenced block whose content is reproduced
  in the record verbatim, satisfying the existing `derived:` +
  code-fence convention `record_lint.py` already requires for count
  claims). The bar is contiguity and volume, not a tool-call log: a
  hook cannot see which tool produced the text (Read vs. `grep -A/-B`
  vs. `sed -n`), so it checks the *artifact* — is there real, in-context
  content behind the claim — not the *method*.

## Directive (default-on, no explicit invocation)

A new hook, same shape as `on-the-record/hooks/record-claim-shape-directive.sh`
(fires on `UserPromptSubmit`/session start, req #7's no-explicit-
invocation mechanism): instructs any role session that "grep/keyword
search locates a candidate defect; it is never itself the evidence for
a defect/root-cause claim in a record — quote the actual surrounding
content you read (≥3 lines, real `file:line` or a reproduced command
output) before writing the claim." This is the instruction layer;
the gate below is the enforcement layer. Directive-only, unenforced,
was the "reduced trust" incident this issue reports — read below for
why it isn't the recommendation alone.

## Gate: composed into `record_lint.py`, not a new file

A new check function, `defect_claim_grounding_check(root, text)`,
added to `on-the-record/gates/record_lint.py` alongside the four
existing full-text checks, re-exported the same way
`record-claim-guard.sh` already re-uses `record_enums` /
`record_wellformed_in` / etc. — single source of truth, same pattern,
no parallel copy.

1. **Trigger vocabulary (conservative, bilingual):** a line matches a
   defect-claim trigger if it contains a root-cause/defect assertion
   pattern — `\b(bug|defect|root cause|the (bug|issue|cause) is|broken|
   버그|결함|원인은|문제는)\b` combined with a causal/assertive verb
   nearby (not a bare noun mention — "no bugs found" or "bug tracker"
   must not trigger). Kept narrow on purpose: false negatives (a missed
   claim) leave today's status quo; false positives (blocking an
   additive record) are the guardrail this proposal must not breach.
2. **Grounding requirement, once triggered:** the same paragraph/bullet
   must carry either (a) a fenced quote of ≥3 contiguous lines whose
   content is checked to exist **verbatim** (whitespace-normalized) at
   the cited `file:line` range in the working tree — the structural
   step that closes the loophole a shape-only check leaves open, where
   a plausible-looking but fabricated or single-line-repeated excerpt
   would pass — or (b) a `derived: <command>` code-fence reproduction
   already satisfying #333's existing bare-count convention, extended
   here to also satisfy grounding for causal claims quoting command
   output (the `ps` case: not a file, so file:line verbatim-match
   doesn't apply — the fence + `derived:` tag is the equivalent bar).
3. **Refusal message:** on failure, name the specific triggering line
   and state the requirement in one sentence — same failure-message
   convention as the four existing checks, so the author fixes it in
   one pass instead of a refusal loop (the issue #517 problem
   `record_lint.py` itself was built to avoid).

## Empty state (guardrail)

A record with no line matching the trigger vocabulary is unaffected —
`defect_claim_grounding_check` returns no violations, same no-op shape
`bare_count_claim_check` already has for a record with no count claim.
Pure additive features, doc-only edits, and legitimate quick lookups
(a `file:line` reference used only to *locate*, with no causal
assertion attached) are never blocked — the check fires on the
assertion pattern, not on the presence of a `file:line` reference or a
grep-shaped citation by itself.

## Feasibility with hooks alone

A PreToolUse/write-time hook sees only the record's resulting text at
the moment of the write — never the session's prior tool-call history,
so it cannot literally verify "a Read tool call happened before this
sentence was typed." This is a hard ceiling, stated rather than
papered over: the gate can verify the *artifact* (real, in-context,
verbatim-matching content is present) but not the *act* (that the
session's own eyes were on it, versus generating a plausible excerpt
after the fact). The verbatim content-match step is the strongest
available proxy under that ceiling — a fabricated or single-line-
repeated-to-look-multiline excerpt fails the verbatim check, which a
shape-only check (candidate (b) below) would not catch. Hooks alone are
therefore feasible for "no defect claim ships on a citation that isn't
real, in-context content" but not for "the session definitely read it
before claiming it" — the second is not achievable from write-time
text alone under req #7's constraint (no CI, no explicit invocation,
so no session-transcript inspection channel is available either).

## Candidate solutions, scored (RICE)

| Candidate | Reach | Impact | Confidence | Effort | RICE |
|---|---|---|---|---|---|
| (a) directive-only, no gate | all defect-claiming records | 1 (low — the 2026-08-11 incident happened *with* general discipline norms already in place) | 1 (low — relies on the exact failure mode this issue reports) | 1 | Reach×1×1/1 = lowest |
| (b) gate checks citation *shape* only (multi-line + file:line present, no content-match) | all defect-claiming records | 2 (medium — catches "no context at all" but not a fabricated-looking excerpt) | 2 (medium) | 2 | mid |
| (c) gate verifies verbatim content-match + directive layer (recommended) | all defect-claiming records | 3 (high — directly closes the observed failure: an out-of-context or fabricated citation cannot pass) | 2 (medium — capped by the tool-call-visibility ceiling above, not by design weakness) | 3 | highest |

(c) wins on RICE despite the highest effort — it is the only candidate
whose Impact rating isn't capped by the exact gap the incident exposed.
Recommendation: **(c)**, composed as directive (instruction) + gate
(enforcement), not either alone.

## Pre-registration (hypothesis-testing)

- **Hypothesis:** a `defect_claim_grounding_check` gate, verifying
  verbatim content-match at the cited `file:line` (or a `derived:`
  fenced reproduction for non-file output), refuses a synthetic
  bare-grep-shaped defect claim and passes a synthetic properly-grounded
  one and a synthetic no-claim (additive/doc) record, in a unit-test
  harness built at implementation (issue #791 step 2).
- **Metric:** pass/fail of that unit-test harness across three fixture
  classes — (1) defect claim + bare grep citation (must refuse), (2)
  defect claim + verbatim in-context citation (must pass), (3) no
  defect claim at all (must pass, unaffected).
- **Threshold:** 100% of class-1 fixtures refused, 100% of class-2 and
  class-3 fixtures pass — this is a mechanical pass/fail test suite, not
  a sampled rate; the threshold is exact, not approximate.
- **Decision rule:** all three classes hit 100% → **validated**, ship
  the gate. Class-1 refusal works but class-3 (empty-state) shows any
  false-positive on real historical records (spot-checked against
  `docs/issue-782/reports/product-discovery/survey.md` and
  `docs/issue-776`'s record — both already in the tree) → **pivot** to
  a directive-only warn (candidate (a)/(b)) until the trigger vocabulary
  is narrowed enough to clear class-3. If content-match structurally
  cannot distinguish real reads from fabricated ones for any writeable
  fixture (i.e. candidate (c)'s core mechanism doesn't hold up) →
  **kill**, and record why in the implementation record's `## What did
  not work`.

## Guardrail metric

False-positive rate on class-3 (no-claim, additive/doc-only, and
legitimate-locate-only) fixtures must stay at 0 in the same measurement
pass as the primary metric above — a 100% class-1 pass alongside any
class-3 false-positive is a reduced-trust result, not a win, and blocks
shipping regardless of the primary threshold.

## ITWWS (if this works)

Extend the same verbatim content-match step to `bare_count_claim_check`
(#333) itself — today a `derived:` tag is trusted at face value; the
same fabrication risk this issue found for defect claims applies to a
count claim's cited command output. Deferred to a follow-up issue, not
in scope here.

## Out of scope

- Any session-transcript / tool-call-history inspection channel (would
  need a mechanism beyond hooks, explicitly excluded by req #7 and by
  the feasibility ceiling above).
- Re-scoring or re-designing the four existing `record_lint.py` checks
  (#333/#310/#331/#330) — this proposal adds one new check alongside
  them, unchanged otherwise.
- Implementation itself (issue #791 step 2, gated behind this
  proposal's approval per contract v3 s19).

## Accumulation

This is accumulation-cost-shaped: it adds a fifth full-text check
function to `record_lint.py`'s existing four (`unverifiable_reason_check`,
`checked_claim_reason_check`, `bare_count_claim_check`,
`orphaned_path_reference_check`), called from the same `lint_record()`
aggregator and re-exported through `record-claim-guard.sh` the same
way the existing four are — no new file, no new hook-registration
surface, no new record-path pattern. The cost added per future record
write is one more mechanical check running in the same pass authors
already go through; it does not add a new refusal-loop shape distinct
from the four that already exist (same one-file-per-violation message
convention). The trigger vocabulary is the one piece that can grow
unbounded if tuned reactively per false-negative report — implementation
should keep it as a single reviewed list, not accreted ad hoc per
incident, to avoid the vocabulary itself becoming an accumulation risk.

## How this will be known to have worked

The unit-test harness in Pre-registration above, run at implementation
time (issue #791 step 2), plus a re-run of the #776 harness (per the
issue's acceptance) showing no regression, plus (ideally, per the
issue) the harness gaining a distinguishing signal for "cited real read
content vs. skim" — satisfied directly by the verbatim content-match
step's pass/fail signal.
