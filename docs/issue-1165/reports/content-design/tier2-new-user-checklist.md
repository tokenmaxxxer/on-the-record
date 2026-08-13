# Tier 2 — new-user checklist for screens (issue-1165)

content_id: docs/issue-1165/reports/content-design/tier2-new-user-checklist.md
user_need: a reviewer needs a named, non-subjective test for whether a
screen is intuitive to someone who has never used the product before,
so a verdict can cite which item failed instead of "feels confusing".

Decision: score each item accept/reject with a named failing condition
and a named accepting shape, never a numeric severity, because a quick
unaided-reviewer check cannot support the precision a numeric score
implies -> per the scout-brief "skip" line.

Per issue requirement 4 (anti-nitpick bound), every item below states:
which NN/g heuristic it is grounded in, the failing condition, and what
an accepting shape looks like. A verdict cites the item, not a general
impression.

## Item 1 — Intuitive-first-screen test

Grounded in: NN/g heuristic #6 (recognition over recall) + #2 (match
between system and real world).

- Procedure: show a reviewer with no session context only the first
  screen. Ask two questions: "what is this for?" and "what would you
  do next?"
- Reject condition: the reviewer cannot answer either question without
  guessing, or answers using system/internal vocabulary the screen
  never actually shows them.
- Accept shape: the reviewer states, in their own words close to the
  screen's own labels, what the screen is for and names the visible
  control they'd use next.

## Item 2 — Primary-task-completion test

Grounded in: NN/g heuristic #8 (aesthetic and minimalist design) + #1
(visibility of system status).

- Procedure: give the reviewer the screen's stated primary task (one
  sentence) and let them attempt it unaided, no hints.
- Reject condition: the reviewer stalls because no single control reads
  as "the" next step (multiple equal-weight competing actions), or a
  state transition (loading/success/error) gives no visible signal so
  the reviewer cannot tell whether their action did anything.
- Accept shape: the reviewer finishes the task and can narrate, at each
  step, what just happened and why they picked the control they did.

## Item 3 — Error-recovery test

Grounded in: NN/g heuristic #9 (help users recognize, diagnose, and
recover from errors).

- Procedure: force one realistic error state; ask the reviewer what
  went wrong and what they'd try next.
- Reject condition: the reviewer sees a blank/frozen/generic state, or
  the error text names an internal code/exception with no
  plain-language explanation or next step.
- Accept shape: the reviewer restates the problem in plain language and
  names a concrete recovery action the screen actually offers.

## Item 4 — Convention-conformance test (amendment 2, added 2026-08-13)

Grounded in: Jakob's Law, principle of least astonishment, Norman's
mental models, processing fluency (canonical:
`docs/issue-1165/proposals/content-design-screens-comprehensibility.md`
§Amendment 2, sources cited there).

- Procedure: name the screen's stated convention family (Material/HIG/
  common navigation-form pattern, from the screen's `convention_family`
  metadata note). Ask the reviewer to perform the primary flow and note
  any point where the screen's actual behavior surprised them relative
  to that named family.
- Reject condition: the reviewer's expectation (built from ordinary
  Material/HIG/common-pattern exposure) is violated with no stated
  reason on record — e.g. a back-gesture that does not go back, a
  primary-looking button that opens a destructive action, a form-submit
  control in an unexpected position — and the screen's own metadata
  carries no `convention_family: none-applicable` deviation note
  explaining why.
- Accept shape: the reviewer's expectations hold throughout the primary
  flow, or, where the screen deviates from the named family, the
  deviation is stated in the screen's own metadata with a reason a new
  user could plausibly accept (e.g. a domain-specific safety
  interstitial that intentionally breaks the expected one-tap-submit
  pattern).

canonical: acceptance: manual plain-language self-review this turn against digital.gov/guides/plain-language/principles — result: UNMEASURED-with-reason: no acceptance command on record for this target
plain_language_check: pass
