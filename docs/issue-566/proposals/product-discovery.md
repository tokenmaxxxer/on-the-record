---
status: proposed
files:
  - docs/issue-566/reports/product-discovery/current-state.md
  - docs/issue-566/reports/product-discovery/survey.md
  - docs/issue-566/reports/product-discovery/scout-brief.md
  - docs/issue-566/proposals/product-discovery.md
---

# Proposal — issue #566: durable requirements/priorities/philosophy/goals record

Phase 1 only. Pre-registers hypotheses, metric, threshold, decision rule per this role's own
contract obligation. No hook code, no gate code — that is architecture/implementation's job. This
proposal resolves the issue's four open questions and does not leave any of them open for a later
role to re-litigate as if undecided.

## Open questions resolved

**1. Docs layout under the target repo's `docs/`.** Four separate files, not one ledger:
`docs/product/requirements.md`, `docs/product/priorities.md`, `docs/product/philosophy.md`,
`docs/product/goals.md`, each an append-only dated log (one entry per captured statement, newest
last), mirroring this repo's own `docs/decisions/` precedent (current-state.md) rather than a
single continuously-rewritten document. Reasoning: the four nouns in the issue title are
semantically distinct (a requirement is falsifiable/actionable, a philosophy is not), and a single
ledger would force either a type tag on every entry (equivalent complexity to four files, worse
diffability) or lossy merging. Four files is the minimum split that keeps each file
single-purpose and independently append-only-diffable.

**2. Update granularity.** Per-turn detection, per-`Stop`-hook write. The hook that detects a
requirement-shaped statement must inspect the turn as it happens (so nothing is lost to context
compaction before end-of-session), but the *write* to `docs/product/*.md` happens at `Stop`
(batched per session, not per turn) — writing on every single `UserPromptSubmit` would fragment
one user thought expressed across several turns into several disconnected entries. This mirrors
the `retry-loop-bound.sh pre`/`post` pairing already in this repo's own `hooks.json` (detect
early, act at a later defined checkpoint), applied to session `Stop` as the checkpoint instead.

**3. How a hook detects "a requirement was stated but not recorded."** Two-part mechanism, both
already-precedented in this repo rather than invented from scratch:
   - **Detection**: a `Stop`-time hook pattern-matches the session transcript for
     requirement/priority/philosophy/goal-shaped language (imperative statements about what the
     project should do, ranking language, "because"/"the point is" rationale statements, "the
     goal is" statements) — the same pattern-match-on-language-not-self-reported-field approach
     H1 in #476's proposal already established for claim detection ("the trigger must fire on
     pattern-match against claim language... not on a field the session opts into" —
     `docs/issue-476/proposals/discovery.md`). A self-reported "I recorded everything" field would
     have the exact same gaming weakness #476 already flagged and rejected.
   - **Cross-check**: the hook diffs the detected statement set against what the same session
     actually wrote to `docs/product/*.md` (via git diff of the session's own commits/working
     tree, the same mechanism `contract-guard.sh`/`pr-preflight.sh` already use to inspect the
     session's own changes) — a requirement-shaped statement with no corresponding new entry is
     the refusal condition.
   - This makes the check mechanized and cheap (regex/keyword pattern class match, cross-
     referenced against a git diff already available to the hook), not an LLM self-judgment call —
     consistent with #566's own scope note that "automatically" means the hook surface must make
     skipping visible/refused, not a model promise.

**4. Interaction with issue-creation flow and #476's anti-theater line.** Strictly upstream and
non-overlapping, not competing: `directive.sh`'s existing "requirements become issues" flow is
the *discharge* path (already scoped as issue #310's territory per current-state.md); this
issue's record is the *capture* path that exists whether or not a requirement is ever discharged
into an issue — a philosophy or a priority statement in particular may never become an issue at
all (issues are actionable asks; philosophy is not) yet still needs a durable record. #476's
anti-theater line applies here exactly as it does to any record: a
`docs/product/requirements.md` entry that is boilerplate-worded rather than the actual structured
capture of what was said would be the same failure mode #476 names for §20 boilerplate. This
proposal inherits #476's already-registered countermeasure design (pattern-match detection, not
self-report) rather than re-deriving a separate anti-theater mechanism — one existing
gaming-resistance argument, reused, not duplicated.

## Candidates scored (RICE)

Reach/Impact scored against "orchestrating-session conversations with a target-repo user, per
week" (no direct log exists for this cadence yet — scored qualitatively against the same order of
magnitude as #476's role-session cadence, since both fire once per role/session).

| # | Candidate | Reach | Impact | Confidence | Effort | RICE | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | `Stop`-time transcript pattern-match + git-diff cross-check (detailed above) | 5 | 5 | 0.6 | 3 | 5.0 | **Keep — primary hypothesis (H1)** |
| 2 | `UserPromptSubmit`-time per-turn immediate write (no batching) | 4 | 3 | 0.5 | 2 | 3.0 | Reject — fragments one thought across turns (open-question 2 above) |
| 3 | Single ledger file, type-tagged entries | 3 | 3 | 0.6 | 1 | 5.4 | Reject — worse diffability than 4-file split at near-equal effort (open-question 1 above) |
| 4 | Self-reported "I captured this" field, checked for presence only | 3 | 2 | 0.2 | 1 | 1.2 | **Reject** — reproduces the exact field-presence-not-truth gap #476 already found and the issue's own "not that a model promise suffices" line explicitly rules out |
| 5 | LLM-judged (a model call classifies whether the turn contained a requirement) | 4 | 4 | 0.3 | 4 | 1.2 | Reject for now — non-deterministic detector on a hook surface that must "make skipping visible," inconsistent with this repo's existing hooks all being deterministic script checks; revisit only if H1's pattern-match false-negative rate proves too high |

## Pre-registered hypothesis package

Guardrail metrics: false_flag_rate (H1) and refusal_noise_rate (H1). Both named and non-empty at
this same registration moment, distinct from the primary metric (unrecorded_requirement_rate)
below — a win on the primary while a guardrail breaches is a reduced-trust result, not a win.

**H1 (primary).** If a `Stop`-time hook pattern-matches the session transcript for
requirement/priority/philosophy/goal-shaped statements and cross-checks the match set against
`docs/product/*.md` entries actually written by that session, the rate of requirement-bearing
statements that leave no durable record will fall, because today no mechanism performs this
check at all (current-state.md: zero transcript-scoped hooks exist).

- **Metric**: `unrecorded_requirement_rate` = (requirement/priority/philosophy/goal-shaped
  statements flagged by the pattern-match layer with no corresponding new `docs/product/*.md`
  entry in that session's diff) / (total requirement-shaped statements flagged), measured over a
  rolling window of the next 20 orchestrating-session conversations after the hook ships in a
  target repo.
- **Threshold**: baseline is unmeasured-but-effectively-100% (no detection or capture mechanism
  exists today, per current-state.md — every requirement-shaped statement in the current state is
  unrecorded by construction, since nothing writes anything). Decision threshold:
  **`unrecorded_requirement_rate` ≤ 10%** after the hook ships, measured next to
  `unrecorded_requirement_rate`'s value at the same window close.
- **Guardrail status at measurement**: `false_flag_rate` (statements the pattern-match layer
  flags as requirement-shaped that a human reviewer, on spot-check, judges were not actually a
  requirement/priority/philosophy/goal statement — e.g. a hypothetical, a question, a quoted
  example) must stay at or below 20 percent over the same window, stated explicitly next to the
  primary metric's value, never implied — a detector so broad it flags ordinary conversation
  would make the hook noise the operator learns to route around, the same failure shape as an
  over-eager refusal gate.
- **Decision rule**: unrecorded_requirement_rate at or below 10 percent AND false_flag_rate at or
  below 20 percent → **go**. If unrecorded_requirement_rate exceeds 10 percent → **pivot**: widen
  the pattern-match vocabulary (more linguistic markers) before concluding the mechanism doesn't
  work — same "widen the trigger before declaring insufficient" rule #476's H1 already established
  for this repo. If false_flag_rate exceeds 20 percent regardless of the primary metric →
  **kill-and-redesign**: the detector is over-broad, which the guardrail catches before the hook
  trains operators to ignore it.
- **Gaming-resistance argument**: the trigger is pattern-match on transcript language, not a
  self-reported field a session can omit — identical structure to, and directly reused from, the
  gaming-resistance argument already pre-registered in `docs/issue-476/proposals/discovery.md`'s
  H1. The cross-check (git diff of what the session actually wrote) is produced by the hook
  layer, not asserted by the session under audit.
- **Failure signature**: fails quietly if the pattern-match vocabulary is narrow enough that
  paraphrased or indirectly-stated requirements slip through undetected (a false negative in
  detection itself, which this metric cannot distinguish from "correctly nothing to record"
  without a separate periodic manual audit) — named here so the architecture/implementation role
  is on notice that `unrecorded_requirement_rate` alone cannot validate detector recall, only
  detector-to-write consistency; a manual audit sample is a follow-up, not built here.

## ITWWS (if this works we should ...)

If H1 proves out, extend the same detect-and-cross-check pattern to the discharge boundary itself
(#310's territory) — checking that every `docs/product/requirements.md` entry that reads as
actionable eventually gets an issue reference, closing the loop from capture through discharge.
Deferred to whichever role owns #310's surface next, not actioned here — this proposal's scope is
capture only, per the issue's own "Scope notes" distinguishing it from #310.

## Deployment-surface constraint carried forward

Scoped entirely to the deployed `on-the-record/hooks/` surface (a new `Stop`-time hook script,
wired into `on-the-record/hooks/hooks.json` alongside the existing `stop-gate.sh` /
`report-framing-check.sh` entries) plus a bootstrap behavior for target repos with no `docs/`
tree (create the four `docs/product/*.md` files with a header on first detected requirement,
rather than refusing outright — matches this repo's own existing behavior of offering to fill
missing preconditions "always confirmed, never silent," per `directive.sh`). No GitHub Actions
proposed anywhere, per the issue's own 2026-08-08 constraint. Hook name, exact regex vocabulary,
and `hooks.json` wiring are architecture/implementation decisions, not specified here.
