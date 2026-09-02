# Onboarding A/B Test: Pre-Registration

## 0. Caveat — read before using this document

This repo currently contains no onboarding implementation, no analytics/event
schema, and no historical traffic or conversion data (`docs/specs/` and
`docs/issue-1/` are the only content — process/discovery docs, not app code).
Everything below that would normally come from real numbers (baseline rate,
daily signups, sample size, duration) is therefore a **placeholder formula
with an illustrative assumption clearly marked**, not a measured fact. Before
this test is turned on, someone must plug in the team's actual baseline
conversion rate and daily new-user volume and re-run the sample-size math in
§3.

Separately: `docs/specs/requirement-digest.md` records the product's core
requirement (R1 — the "comprehension gap" problem this app addresses) as
`[proposed]`, explicitly not yet confirmed as real or unmet. Running a
resourced onboarding experiment is a bet that the funnel we're onboarding
people *into* is worth optimizing. If R1's discovery report isn't done yet,
flag that dependency to whoever owns the roadmap — it doesn't block writing
this pre-registration, but it should block spending real traffic on it.

## 1. What we're measuring

**Primary metric:** Onboarding completion rate — the proportion of new users
in an arm who reach the first activation event (first study session actually
started, e.g. first question submitted or first material uploaded and
processed) within a fixed window (recommend 48 hours of account creation) of
starting onboarding.

Rationale for choosing this over "reached the last onboarding screen": a
redesigned flow can trivially inflate screen-completion by making steps
shorter or more skippable without producing a user who actually gets value.
Anchoring the primary metric to the first real product action ties the test
to the outcome we actually care about (activation), not to onboarding-UI
mechanics.

**Unit of randomization:** user (device/account ID at first launch),
assigned once at the point they enter onboarding. Do not re-randomize on
repeat visits.

**Secondary/diagnostic metrics** (not gating, but explain *why* the primary
moved):
- Step-by-step drop-off rate at each onboarding screen
- Time to complete onboarding (median, p90)
- % who skip onboarding (if skip is offered)

## 2. What counts as success

Define, before launch, on the real baseline:

- `p0` = current (control) onboarding completion rate, from existing
  analytics — **not yet known from this repo; must be pulled from the
  team's product analytics before test start.**
- Minimum detectable effect (MDE): the smallest absolute lift in completion
  rate worth the cost of shipping the redesign. Pick this as a business
  decision, not a statistical one — e.g. "we won't ship a redesign for less
  than a 3-point absolute improvement" is a reasonable illustrative default
  for a mature funnel, but the team should set the real number based on
  what a point of onboarding completion is worth downstream (paid
  conversion, retention, etc.).
- Significance level: α = 0.05, two-sided (we want to know if the new flow
  is *worse* too, not just whether it's better).
- Power: 80% (β = 0.20) minimum; use 90% if the team can afford the larger
  sample/longer runtime.

**Success criterion:** the treatment arm's onboarding completion rate is
statistically significantly higher than control's at the pre-registered α,
AND the observed lift is at or above the pre-registered MDE (a statistically
significant but trivially small lift should not ship on its own — see
guardrails).

**Sample size:** compute with a standard two-proportion power calculation
using the real `p0` and MDE once known, e.g. for illustration only —
`p0 = 0.40`, MDE = 0.05 (absolute), α = 0.05, power = 0.80 → roughly 1,500
users per arm. This number is not to be used for real planning; it exists
only to show the shape of the calculation the team should re-run with real
inputs.

## 3. How long we'll run it

Duration is driven by required sample size ÷ daily new-user volume, not by
a fixed calendar guess. Once `p0`, MDE, and daily signup volume are known:

`days = (2 × sample_size_per_arm) / daily_new_users`

On top of that minimum, apply two floors regardless of what the formula
says:
- **Minimum 1 full week**, so the test spans every day-of-week pattern once
  (weekday vs. weekend signup behavior differs for a student-facing app,
  especially around the academic calendar — avoid a window that's all one
  day-of-week type).
- **No peeking-driven early stop.** Decide the sample size/duration up
  front and don't stop early because the metric looks good (or bad) at day
  3 — that inflates the false-positive rate. If the team wants the option
  to stop early, use a proper sequential-testing method (e.g. group
  sequential design) chosen *before* launch, not an ad hoc peek.

If actual daily new-user volume is low enough that the required sample size
would take more than ~4-6 weeks, that's a signal to either accept a larger
MDE (test for a bigger effect) or hold off until volume grows — don't
quietly lower statistical rigor to hit a calendar deadline.

## 4. Guardrails — what to watch so a "win" isn't quietly a loss

An onboarding redesign can win on completion rate while damaging things
completion rate doesn't capture. Track these for both arms, and treat a
meaningful regression in any of them as a reason to hold the ship decision
even if the primary metric wins:

- **Downstream retention:** D1, D7, and D30 retention of users who
  activated in each arm. A flow that pressures/rushes people through
  onboarding can lift completion while producing users who bounce sooner
  because they didn't understand what they signed up for.
- **Downstream conversion (if applicable):** trial-to-paid or
  free-to-subscribed rate for users who came through each onboarding
  variant, measured over a long enough window to actually observe
  conversion (don't cut this off before the typical conversion latency).
- **Feature/content quality signals post-activation:** e.g. if onboarding
  collects preferences/course info used to personalize the app, check that
  the redesigned flow doesn't degrade the quality or completeness of that
  data (a shorter flow that skips a "what course are you in" step will look
  great on completion rate and quietly break personalization downstream).
- **Support/error signals:** support ticket volume, error/crash rate, and
  rage-click or repeated-back-navigation rate during onboarding — a flow
  can look "completed" while confusing a chunk of users who eventually
  muscle through it.
- **Segment splits, not just the topline average:** break primary and
  guardrail metrics out by device type (iOS/Android/web), by new vs.
  reinstalled users, and by acquisition channel if available. A flow can
  win in aggregate while losing badly for one segment (e.g. a
  video-heavy redesign hurting users on slow connections).
- **Sample ratio mismatch (SRM) check:** verify the actual traffic split
  between arms matches the intended allocation (e.g. 50/50) within
  expected statistical noise. A skewed ratio usually means a bug in the
  assignment/logging pipeline, and any result from that run should be
  distrusted until the SRM is root-caused and fixed.
- **Novelty effects:** if duration allows, check whether the treatment
  effect is stable across the run rather than concentrated in the first
  few days (early lift that fades often reflects users reacting to
  anything-new rather than a genuine improvement).

## 5. Open items for the team before turning this on

1. Confirm current onboarding completion baseline (`p0`) and daily new-user
   volume from existing analytics; re-run the sample-size math in §3 with
   real numbers.
2. Set the real MDE as a business decision (what's a point of onboarding
   completion worth downstream?).
3. Confirm the activation event definition (first study session started)
   is already instrumented, or instrument it before launch — the test
   cannot measure the primary metric otherwise.
4. Decide whether R1's discovery/validation work (`docs/issue-1/`) needs to
   land first, since this test optimizes the entry point to a product
   whose core need is still unconfirmed.
