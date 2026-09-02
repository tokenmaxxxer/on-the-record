# Can we trust the paywall A/B test result?

**Short answer: not yet.** A "35% lift" from a one-week test is exactly the kind of
result that looks compelling and is frequently wrong. Before shipping variant B
to 100% of users, we should spend a day or two validating the result. Below is
what I'd check, roughly in order of how likely each one is to overturn the
headline number, followed by what I'd actually tell the team.

Note: I didn't find the experiment's data, dashboard, or analysis code in this
repo, so I can't check any of this directly. Treat this as the checklist to run
against whatever system produced the "35%" number (Amplitude/Mixpanel/Statsig/
internal analytics, etc.) before rollout.

## 1. Is the result even statistically sound?

- **What's the sample size and the confidence interval, not just the point
  estimate?** "35% increase" with wide confidence intervals (e.g., 5%–70%) is a
  coin flip dressed up as a finding. Ask for the CI, not just the p-value.
- **Was a minimum sample size / power calculation done before the test started?**
  If the team just ran it for "a week" without pre-computing how many
  conversions were needed to detect a meaningful effect, the test was likely
  underpowered — one week of paywall traffic for a university study app is
  probably a few hundred to low-thousands of conversions at most, which is
  often too small to reliably detect anything short of a huge effect.
- **How many metrics were checked before subscriptions was the one that "won"?**
  If the team looked at trial starts, subscriptions, revenue, retention, etc.
  and picked the one with the best-looking number, that's multiple-comparisons
  p-hacking even if no one intended it that way.
- **Was there any peeking?** If someone checked the dashboard daily and the test
  was called as soon as it looked significant, the real false-positive rate is
  much higher than the nominal 5%. This is one of the most common ways "wins"
  don't replicate.

## 2. Is the effect real or an artifact of how the test was run?

- **Randomization integrity (sample ratio mismatch):** Do the two arms have
  roughly the expected 50/50 (or whatever the intended split was) traffic
  split? A skewed split (e.g., 47/53) is a red flag that assignment,
  logging, or bot traffic is broken, and it can fully explain an apparent lift.
- **Novelty/curiosity effect:** A new paywall design often converts better for
  the first days simply because it's new and users engage with it out of
  curiosity, not because it's genuinely more persuasive. One week is not
  enough to separate a real effect from novelty — this typically needs 2–4
  weeks or a look at whether the lift is decaying day-over-day within the test.
- **Timing/seasonality confound:** What happened during that specific week?
  Start of semester, midterms, a marketing push, a holiday, an app store
  feature, a competitor issue — any of these could inflate or deflate
  conversions independent of the paywall design. Compare against the same week
  last cohort/semester if possible, or check whether the lift is stable across
  the individual days of the test rather than driven by one anomalous day.
- **Instrumentation bug:** Confirm the "subscription" event fires identically
  and correctly for both variants (e.g., B doesn't accidentally double-fire the
  event, or A is undercounting due to a UI change that broke a tracking pixel).
  This is boringly common and easy to check by reconciling event counts against
  actual billing/App Store/Play Store revenue records.

## 3. Does the metric that moved actually matter?

- **Subscriptions vs. revenue vs. retention:** Did variant B increase
  subscriptions by pushing a cheaper plan, a longer free trial, or more
  aggressive/dark-pattern-adjacent framing? If so, check trial-to-paid
  conversion, refund rate, and 30/60-day retention — a paywall that gets more
  people to tap "subscribe" but also gets more people to cancel or refund isn't
  a win. One week of data cannot show this; refunds and churn take longer to
  materialize.
- **Guardrail metrics:** Did variant B hurt anything else — app store rating,
  support tickets, complaint volume, uninstall rate? A paywall that's more
  aggressive can lift short-term conversion while damaging trust and long-term
  retention/LTV.

## 4. Does it generalize?

- **Segment consistency:** Does the lift hold across platforms (iOS/Android/
  web), user types (new vs. returning), and traffic sources, or is it driven
  entirely by one segment? A result concentrated in one small, unrepresentative
  segment shouldn't be generalized to "everyone."
- **External validity for a student audience specifically:** Since this is a
  study app for university students, check whether the test period overlapped
  with a specific academic-calendar moment (e.g., exam week) that wouldn't
  recur once rolled out to all weeks of the year.

## What I'd tell the team

1. **Don't do a full rollout this week based on this alone.** The result is
   plausible but currently unverified — treat it as "promising," not
   "confirmed."
2. **Get the confidence interval and sample size before doing anything else.**
   If the CI is wide or the sample is small, the honest answer is "we don't
   know yet," not "35%."
3. **Check for sample ratio mismatch and reconcile event counts against
   billing data.** This is a 30-minute check that catches a large fraction of
   false "wins."
4. **Extend the test 1–3 more weeks (or until it hits a pre-computed sample
   size), and pre-register a single primary metric** (e.g., paid conversion
   rate) instead of picking the best-looking one after the fact.
5. **Watch decay and downstream metrics.** If the lift is real but driven by
   novelty, it should shrink over the extension. If it's real but driven by a
   more aggressive paywall, refund/cancellation/rating data should show it
   within a few weeks — worth a delayed look even after rollout.
6. **If leadership wants to move faster,** ramp variant B to a larger
   percentage (e.g., 50% → 80%) rather than 100%, so we can keep it as a live
   control comparison and catch a false positive before it's fully baked into
   the product with no easy way to attribute a later revenue dip.

The 35% number might well be real — but right now it's a single week's
observation from what's likely a small, novelty-prone, un-power-checked test.
A few days of validation is cheap insurance against shipping a paywall change
that either doesn't do what we think or quietly hurts retention/trust for
students.
