# Onboarding Redesign A/B Test — Pre-Registration

Status: draft, not yet launched. Fill in the bracketed `[TODO]` values from
current analytics before flipping the experiment on — see "What's missing"
at the end. Everything else here is a firm commitment: don't change the
primary metric, threshold, or duration after data starts coming in.

## 0. Scope note

This repo has no onboarding implementation, analytics events, or baseline
numbers yet (`docs/specs/requirement-digest.md` shows the underlying
product problem itself is still `[proposed]`, not validated). So this plan
is written as a template with the statistical logic fully worked out and
the inputs clearly marked as placeholders. It should not be launched as-is
— the `[TODO]` baseline and the "does the redesign exist and is it
instrumented" question both need to be resolved first.

## 1. Hypothesis

Redesigned onboarding **increases the share of new users who reach their
first genuine study action** (see metric definition below) **without
reducing** activity in the next 7 days, judged against a set of guardrails.

## 2. Primary metric

**Activation rate**: of users who start onboarding (see new session,
account created), the % who complete a first real study action within 48
hours of signup.

"Real study action," not "finished onboarding screens" — a redesign can
trivially raise onboarding-completion by making it shorter or more
naggy while producing users who never actually study. Define it as one
specific, already-loggable event, e.g. "submitted first flashcard review"
or "uploaded first document and got a diagnosed comprehension gap back" —
whichever is the first moment the product delivers real value. Pick one
event and freeze it before launch.

- Numerator: unique users in the assigned arm who fire that event within
  48h of account creation.
- Denominator: unique users who were exposed to the onboarding flow (saw
  screen 1), assigned to that arm, in the enrollment window.
- Unit of randomization: user (device/account, not session) — assign at
  first app open, before they see either flow, so partial exposure can't
  bias the split.
- Excluded: internal/QA accounts, users who signed up but never opened
  the app past the splash screen (never actually exposed to either
  flow), duplicate accounts.

## 3. Success threshold

- **Minimum detectable effect (MDE):** absolute lift ≥ 5 percentage points
  on activation rate (e.g., 30% → 35%). `[TODO: replace with the smallest
  lift that would be worth shipping given engineering cost — 5pp is a
  placeholder, not a derived number]`.
- **Statistical test:** two-proportion z-test (or chi-squared), two-sided.
- **Significance:** p < 0.05, with power ≥ 80%.
- **Decision rule:** ship the redesign only if (a) activation lift is
  statistically significant in the predicted direction, AND (b) no
  guardrail (§4) regresses beyond its threshold. A significant activation
  win alongside a guardrail breach is not a ship — it's a "redesign
  partially and re-test" result.
- One-sided vs two-sided: use two-sided even though the hypothesis is
  directional — a redesign that makes activation significantly *worse*
  is a real and useful finding, not noise to discard.

## 4. Guardrails (what could quietly get worse)

Checked every analysis, not just at the end, but **not** used to stop the
test early on their own (see §6 for the one exception — safety/legal).

| Guardrail | Why it matters | Alarm threshold |
|---|---|---|
| **Day-7 retention** (any-app-open on day 7 post-signup) | A flow that front-loads a flashy first action but doesn't set correct expectations can spike activation and tank retention a week later. | Non-inferiority: new flow must be within 2pp of control, not just "not significantly worse" — underpowered guardrails default to false safety. |
| **Onboarding drop-off / abandonment rate** | Redesign could raise activation among finishers while making more people quit onboarding entirely (selection effect masking a worse flow). | No statistically significant increase. |
| **Time-to-first-value** | A flow that's "faster" by skipping context could produce users who activate but are confused about what the product does. | Directional check only — report, don't gate on it alone, since faster isn't automatically bad. |
| **Support/help-center contact rate in first 48h** | Redesigned copy or flow steps are a common source of new confusion tickets. | No statistically significant increase. |
| **Uninstall/account-deletion rate in first 7 days** | Catches "activated but immediately regretted it" — activation alone can't distinguish delight from a forced funnel. | No statistically significant increase. |
| **Crash rate / error rate during onboarding** | Basic regression check — new screens, same reliability bar. | No increase beyond noise floor. |
| **Downstream feature adoption (week 2)** | Checks the redesign isn't just moving the activation moment earlier without changing real habit formation. | Report only; directional, not gating. |

If any gating guardrail breaches its threshold, that overrides a
significant primary-metric win: do not ship, diagnose which part of the
redesign caused it, and re-test.

## 5. Duration / sample size

- Compute required sample size per arm from `[TODO: current baseline
  activation rate]` and the 5pp MDE using a standard two-proportion power
  calculation at α=0.05, power=0.80. Example: baseline 30%, MDE 5pp →
  ≈ 1,090 users per arm (≈2,180 total). Baseline 15% → ≈ 770 per arm.
  Recompute with the real baseline before committing to a date.
- Translate that sample size into calendar time using `[TODO: current
  daily new-signup volume]`. Round up to the nearest **full week
  multiple** regardless of when the sample-size target is hit, to average
  out day-of-week effects (weekday vs. weekend signups behave
  differently for a study app tied to term schedules).
- **Minimum run time: 2 full weeks**, even if the sample-size target is
  reached sooner — this is specifically to catch the day-7 retention
  guardrail, which by definition needs 7 days of data per cohort plus
  enough cohorts to be stable.
- **Maximum run time: 6 weeks.** If the target sample size isn't reached
  by then, the effect is smaller than the MDE can detect at current
  traffic — stop and treat as inconclusive rather than let the test run
  indefinitely.
- Academic-calendar caveat: if enrollment spans a semester
  start/end/exam period, note it explicitly in the write-up — onboarding
  behavior for a study app is plausibly not stationary across the term,
  and a test that straddles, say, syllabus week and finals week is
  comparing two different populations, not just two flows.

## 6. Analysis discipline (so the test isn't secretly p-hacked)

- No peeking-and-stopping on the primary metric. Look at guardrails
  throughout for safety, but the ship/no-ship call is made once, at the
  pre-committed sample size or time cap — whichever comes first.
- One exception to "don't stop early": a severe guardrail breach (crash
  rate, uninstall spike, support-ticket spike) is a kill-switch condition
  — stop immediately regardless of primary-metric sample size, because
  user harm accumulates the same as it's measured.
- Pre-register the primary metric and MDE (this document) before
  first exposure, so post-hoc metric-swapping to find a significant
  result isn't possible.
- Segment-cut results (e.g., by device, by first-time vs. returning) are
  exploratory only unless pre-specified — report them as hypotheses for a
  follow-up test, not as justification to ship or kill this one.

## 7. What's missing before this can actually launch

- No onboarding flow (old or new) exists in this repo yet, so there's
  nothing to instrument or randomize.
- No analytics/event pipeline is defined, so "first real study action"
  isn't a loggable event yet — needs a concrete event name and schema.
- No baseline activation rate, signup volume, or existing retention
  numbers exist to plug into §5's sample-size formula — the numbers
  above are illustrative, not real.
- The underlying product hypothesis this onboarding sits on top of is
  still `[proposed]`, not validated (`docs/specs/requirement-digest.md`,
  R1) — worth flagging to whoever approves the test, since an onboarding
  A/B test assumes people already want the core product enough to reach
  activation at all.
