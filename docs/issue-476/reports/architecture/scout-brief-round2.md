# Scout brief -- issue #476 round 2 architecture

## Scope and mode

Not a product/exemplar space: this is a decision about this repo's own
deployed hook surface, same framing product-discovery's own round-2 scout
brief already used for the identical question (which chokepoint pattern
to reuse). Per scout-directive's product-shaped vs own-deliverable-kind
split, and per the survey-first order: the survey above already found the
decision-relevant facts by reading this repo's own hooks (pr-preflight.sh,
record-claim-guard.sh, hooks.json, claim_scan.py). One stage, internal
read, no external search -- stated per the directive's
fallback-and-say-so requirement, same mode discovery's own round-2 scout
brief used and for the same reason.

## Must-bes carried forward from product-discovery's round-2 scout brief

1. No second copy of check logic.
2. Fail posture matches blast radius (write-time: fail closed; act-time:
   fail open on ambiguity, closed only on a positive, evidence-backed
   hit).
3. A kill switch (ORCHESTRATE_OFF) present on every ported guard.

## What this round's own read adds beyond product-discovery's brief

Product-discovery's scout brief established WHICH shape to adopt
(pr-preflight.sh's deny-before-effect pattern) and flagged the call-shape
coverage gap as a named risk for architecture to resolve, not to silently
inherit. This survey's own read went one step further and confirmed the
gap is concrete, not hypothetical: pr-preflight.sh's existing matcher
already misses `gh api` PR-body writes and wrapper-script indirection
today, for the exact same reason discovery predicted (the matcher tests
the literal Bash command string, not the effect). That means candidate
A's new hook inherits an existing, already-live blind spot merely by
copying pr-preflight.sh's matcher verbatim -- the proposal below must
decide whether to widen the matcher now or register the inheritance
explicitly and defer, per H1-wiring's own decision rule ("widen the
matcher or add a second chokepoint ... before declaring wiring
insufficient").

## Adopt / skip (architecture-specific)

- Adopt: joining the existing `PreToolUse`/`Bash` matcher array in
  hooks.json as a new sibling entry, ordered after pr-preflight.sh (both
  read the same --body/--body-file; ordering after it means a request
  pr-preflight.sh already denies never reaches this hook, one fewer
  regex-extraction to run on a command that is about to be blocked
  anyway).
- Adopt: an inline, minimal port of claim_scan's two regexes (CLAIM_RE
  and EVIDENCE_MARKER_RE) rather than importing gates/claim_scan.py,
  matching pr-preflight.sh's own precedent and reasoning (gates/ has no
  guaranteed location relative to a marketplace-installed plugin).
- Skip (this round): widening the matcher to cover `gh api` PR-body
  writes or wrapper-script indirection -- out of scope per
  discovery-round2's own registered decision rule, which treats
  matcher-widening as the pivot action AFTER wiring_coverage_rate is
  measured and found low, not a precondition to shipping candidate A.
  Registering the gap explicitly (this brief, the survey, and the
  proposal's own failure-signature section) is what keeps this a stated
  deferral rather than a silent inheritance.

Sources consulted (read this session, no external fetch):
on-the-record/hooks/pr-preflight.sh, on-the-record/hooks/
record-claim-guard.sh, on-the-record/hooks/hooks.json,
gates/claim_scan.py, docs/issue-476/reports/product-discovery/
scout-brief-round2.md, docs/issue-476/reports/product-discovery/
survey-round2.md.

Stages used: one (internal prior-art read only, no external sweep --
reason stated above). Wall-clock well under the three-minute budget.
