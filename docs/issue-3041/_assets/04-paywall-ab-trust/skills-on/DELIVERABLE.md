# Should we roll out paywall variant B? Not yet.

A 35% lift is a big, attention-grabbing number, and that alone is a reason to slow
down rather than speed up — large effects from a single test are more often noise,
novelty, or a measurement bug than real, durable improvements. Before shipping to
everyone, I'd want the team to walk through the checks below. None of them require
new tooling beyond the experiment platform and the raw event logs.

## 1. Is the result even statistically trustworthy?

- **What's the confidence interval, not just the point estimate?** "35% increase"
  is a single number; the real question is the range. If the CI is something like
  [3%, 70%], that's a coin flip dressed up as a finding. Ask for the interval and
  the p-value (or Bayesian equivalent) before repeating the headline number.
- **How many subscribers actually converted in each arm?** Subscription events are
  rare relative to app opens. If variant A had, say, 40 conversions and variant B
  had 54, a 35% relative lift is well within the range you'd expect from noise
  alone. Small numerators make relative-lift percentages misleading — ask for raw
  counts, not just the percentage.
- **Was the sample size pre-registered, or did the test stop as soon as it looked
  good ("peeking")?** Stopping a test early because it crossed significance
  inflates the false-positive rate substantially. Ask whether the sample size/
  test duration was fixed in advance or whether someone was watching the dashboard
  and called it when B pulled ahead.
- **Did the test run for at least one full week, ideally two?** University
  students' study/spending behavior is highly cyclical — different on weekdays vs.
  weekends, and near exam periods vs. mid-semester. A test that ran Tuesday–Friday
  only captures one slice of the cycle and won't generalize.
- **Was there a sample ratio mismatch (SRM)?** Check that the number of users
  actually assigned to A vs. B matches the intended split (e.g., 50/50). If it's
  meaningfully off (say 52/48 when it should be 50/50 and that's outside sampling
  noise), the randomization or logging pipeline is broken and every downstream
  number is suspect.

## 2. Is "subscriptions" the right — and only — metric to trust?

- **Revenue, not just conversion count.** A paywall variant can raise conversion
  rate while pushing users toward a cheaper plan or a longer trial, netting flat or
  negative revenue. Check ARPU/total revenue in each arm, not just "did they
  subscribe."
- **Downstream retention and refunds.** A more aggressive or confusing paywall can
  buy short-term conversions from students who cancel or request refunds within
  days. If the experiment window closed right after signup, we're blind to this.
  Ideally, check 7- and 30-day retention/refund rates for the cohorts already
  acquired, even if that means waiting before the full rollout.
- **Guardrail metrics.** Did app opens, session length, free-feature usage, or
  support tickets/complaints move in the wrong direction for variant B? A paywall
  that's more aggressive about interrupting the study flow could convert some
  students while quietly annoying or losing others (e.g., increased uninstalls or
  negative App Store reviews). These wouldn't show up in a "subscriptions" metric
  alone.

## 3. Could something other than the design be driving the difference?

- **Novelty effect.** Anything new — including a new paywall — can produce a
  temporary bump simply because it's different, which fades within a couple of
  weeks. This is a strong candidate given only "last week" of data.
- **External events.** Did the test window overlap with midterms, a new semester
  start, a marketing push, a school partnership announcement, or a price change?
  Any of these would move subscription rates independent of the paywall design and
  wouldn't be attributable to variant B.
- **Randomization integrity.** Confirm users were bucketed once and consistently
  (not re-randomized on each app open), and that the split was truly random (not,
  e.g., new installs going to B and existing users to A, or iOS/Android split
  unevenly between arms — platform alone can swing subscription rate a lot).
- **Instrumentation bugs.** Double check that "subscription" events are logged
  identically in both arms (e.g., B's flow doesn't accidentally fire the event
  twice, or count starting a free trial as a subscription while A only counts paid
  conversions).

## 4. Does the effect hold up when you slice it?

- **By platform (iOS/Android/web), by new vs. existing user, and by student
  segment** (e.g., paying out of pocket vs. institution-sponsored, if that
  distinction exists). If the lift is concentrated in one thin slice and flat or
  negative elsewhere, "roll out to everyone" is the wrong conclusion even if the
  headline number is real.
- **Consistency over time within the test.** Plot daily conversion rate for A and
  B across the test window. A real effect should look reasonably stable, not like
  one anomalous day driving the whole result.

## What I'd tell the team

Don't roll out variant B this week based on this result alone. A single week and
a single headline percentage isn't enough evidence for a subscription-revenue
decision, especially given how rare and cyclical conversion events are for a
student audience. Concretely:

1. **Ask for the raw numbers**: sample sizes per arm, raw conversion counts, the
   confidence interval, and confirmation the sample size was pre-registered
   (not stopped early).
2. **Check for SRM and instrumentation bugs** before trusting any downstream
   number.
3. **Extend or re-run the test** for at least 2 full weeks to smooth out
   weekday/weekend and novelty effects, ideally avoiding exam-period bias.
4. **Look at revenue, retention/refunds, and guardrail metrics** (churn, support
   complaints, app ratings) — not just conversion count — before calling it a win.
5. **Slice the results** by platform and user segment to make sure the effect is
   broad-based, not concentrated in one group.

If, after that, variant B still shows a robust, statistically solid lift with no
red flags in retention or guardrails, it's a good candidate for a staged rollout
(e.g., 50% → 100% over a week or two) with monitoring, rather than a full
switch-over in one step. That gives a safety net if something was missed.
