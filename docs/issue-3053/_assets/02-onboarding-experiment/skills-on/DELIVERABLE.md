# Onboarding experiment: introduce the comprehension-gap monitor vs. current onboarding

Pre-registered per `product-discovery-hypothesis-preregistration`: every number below is fixed
before the test launches. Sources: `docs/issue-5/specs/one-pager.md` (what the feature is for)
and `docs/issue-1/reports/.../user-discovery.md` (the job it's built for).

## What this test can and can't tell us

The one-pager is explicit that the product's job is **monitoring** — surfacing a checked,
located comprehension signal at the moment a student would otherwise close the book on an
unaddressed gap — not articulation and not resolution (one-pager, "Which framing this is,
explicitly"). This onboarding test sits one step upstream of that job entirely: it asks whether
telling a new student the feature exists gets them to *try* it. It does not, and cannot in the
timeframe below, tell us whether the check actually shrinks the felt-vs-actual comprehension gap
(desired outcome 1) or reduces premature stopping (desired outcome 2) — that's the feature's own
efficacy question, already gated behind the one-pager's separately-registered falsifier (15-20
students, 6-week window, self-prediction vs. checked score). Conflating "more people tried the
check" with "the check works" would overstate what this experiment proves.

## Hypothesis

Onboarding that explains the comprehension-gap check and prompts a first use of it, versus
today's onboarding (which never mentions the feature), increases the share of new students who
actually run the check at least once — i.e., it fixes a pure discoverability gap, not a
motivation or trust gap, since the feature is otherwise unchanged in both arms.

## Primary metric, threshold, decision rule

**Primary metric:** *first-check activation rate* — the share of new signups who complete at
least one comprehension check (a check is "completed" when scored, not merely opened) within 7
days of account creation.

Why this metric and not a downstream one (retention, comprehension-gap size): onboarding's only
job is exposure and first trial. Desired outcomes 1-2 from the one-pager depend on repeated use
across many study sessions, which this single onboarding touchpoint can't move directly — if
students never try the check once, nothing else in the one-pager can happen; if they do try it,
whether it keeps delivering value is a separate, later question. First-check activation is the
one metric that isolates onboarding's actual job.

**Open input to fill before lock:** pull the trailing-4-week baseline of this exact metric (share
of new signups who complete ≥1 check within 7 days) under the *current* onboarding, call it
`p0`. Current onboarding never mentions the feature, so `p0` reflects organic discovery only
(browsing the app, stumbling on the check) — expect it to be low, but it must be measured, not
assumed, before the threshold below is locked.

**Ship criterion (all three required):**
1. Statistical: two-sided p < 0.05 on a two-proportion z-test, treatment vs. control.
2. Practical significance: absolute lift ≥ +8 percentage points over `p0` (roughly a doubling if
   `p0` is in the 5-15% range typical of an unannounced feature; if the measured `p0` falls
   outside that range, recompute the absolute-lift bar so it still represents at least a 2x
   relative improvement — write the recomputed number into this document before launch, not
   after).
3. No guardrail breach (below) — a primary-metric win with a breached guardrail is recorded as a
   breach, not a win.

**Decision rule:** ship the redesigned onboarding to 100% of new users only if all three hold at
the end of the pre-committed window below. If (1) and (2) hold but (3) doesn't, treat as "breach —
do not ship as-is," diagnose the breach, and re-test a revised version rather than shipping the
original. If (1) or (2) fail, treat as a flat/negative result — the norm for most product ideas,
not a failure of execution — and do not ship.

## Sample size and duration

Two-proportion z-test, α = 0.05 two-sided, power = 80%, 1:1 allocation.

| Baseline `p0` | Target `p1` (p0 + 8pp) | Required n per arm |
|---|---|---|
| 5% | 13% | ~410 |
| 8% | 16% | ~610 |
| 10% | 18% | ~660 |
| 15% | 23% | ~740 |

Use the row matching the measured `p0`; if `p0` lands between rows, interpolate conservatively
(round up). Multiply required n per arm by 2 for total signups needed.

**Duration:** run for a minimum of 4 full weeks and a maximum of 6, whichever is later reached
after hitting the required sample size — 4 weeks minimum so the 7-day activation window plus a
weekday/weekend cycle isn't dominated by any single cohort-week's idiosyncrasies (e.g., a
syllabus-week signup spike behaving differently from a mid-semester trickle). Do not start the
test in the first week of a term or during finals week — those signup cohorts have different
baseline motivation and would bias `p0` and the effect estimate; if the measured `p0` was itself
pulled from one of those windows, re-pull it from a mid-semester window instead. No interim
peeking that could influence a decision: the primary-metric decision is made once, at the
pre-committed horizon (sample size reached AND minimum 4 weeks elapsed), not before.

## Guardrail metrics (must not move adversarially, checked regardless of primary-metric result)

| Guardrail | Breach threshold | Action on breach |
|---|---|---|
| Day-1 onboarding completion rate (signup → first study session started) | Drops ≥ 2 percentage points vs. control | Stop outright — the added explanation is adding enough friction to cost first-session starts, which is a worse outcome than the status quo regardless of activation gains |
| Check abandonment rate (check opened but not completed, among those who open one) | ≥ 15 percentage points higher than control's abandonment rate among openers | Stop outright — an activation win driven by students opening-then-quitting the check is not a real activation win, it inflates the primary metric without the check ever being scored |
| Day-7 return rate (any app open 2-7 days post-signup) | Drops ≥ 3 percentage points vs. control | Reduced trust, re-examine before shipping — could indicate the framing ("checked before you're allowed to close the session," per the one-pager's moment-of-use description) reads as punitive or test-like rather than helpful, discouraging return visits even if first-check activation went up |
| Negative-sentiment support contacts mentioning the check (words like "graded," "forced," "stressful," "test") as a share of new-user contacts | ≥ 5 such contacts per 1,000 new users in the treatment arm, or a rate ≥ 2x the control arm's rate, whichever is reached first | Reduced trust, re-examine — qualitative signal that the onboarding copy is setting the wrong expectation about what the check is (a location signal, not a grade — one-pager, "moment of use") |

Guardrails are read at the same pre-committed horizon as the primary metric, not earlier and not
selectively after a favorable primary-metric read.

## Readout protocol

Before interpreting any number: confirm random assignment was correct (a chi-square test of
observed vs. expected 50/50 split, reported alongside its p-value — stop and investigate the
assignment pipeline if this fails, before looking at the primary metric at all) and confirm
whether the experimentation platform in use has an existing A/A validation record; if none exists,
flag results as carrying an unknown false-positive rate rather than treating a clean-looking
result as automatically trustworthy. Report the primary metric's effect with its confidence
interval, all four guardrail readings, and the pre-committed-vs-actual design (sample size,
duration, any deviations) side by side — a flat or negative result is reported as such, not
reframed as a near-miss.

## What we'd still owe an answer on if this ships

A win here only proves the redesigned onboarding gets more new students to try the check once.
It does not test whether repeat use holds up, whether the check keeps activation gains after the
novelty of a new onboarding flow fades, or the feature's actual comprehension-gap efficacy (the
one-pager's own falsifier, already scoped separately). Those are follow-on hypotheses, not covered
by this registration.
