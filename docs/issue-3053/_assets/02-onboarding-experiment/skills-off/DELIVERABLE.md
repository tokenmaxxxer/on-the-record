# Pre-registration: redesigned first-run onboarding (comprehension-gap intro) vs. current onboarding

## Scope — what this experiment is and isn't

This tests **onboarding**, not the comprehension-gap feature itself. Per `docs/issue-5/specs/one-pager.md`, the feature's job is *monitoring*: catch a student at the moment they finish solo study and are about to trust a felt sense of "done," insert a short scored check, and surface a located mismatch ("section 3 was weak") before they close the book. Onboarding's only causal lever over that job is the step *before* it — whether the student knows the check exists and is willing to try it the first time a real moment-of-use arrives. So the thing this experiment can move is **discovery and first use**, not comprehension outcomes. Whether the check itself narrows the felt/actual gap once used is a separate question — that's the 6-week interview falsifier already pre-registered in the one-pager (`## Falsifier`), not this test.

Concretely: **control** = current onboarding, which never mentions the comprehension-gap check (a student only finds it, if at all, by encountering it organically in-app after a study session). **Treatment** = redesigned onboarding that explains the check's job in the student's terms during first-run.

## Primary metric

**D7 check-completion rate**: the % of new accounts created during the experiment window that complete at least one comprehension check within 7 days of signup.

Why this metric and not an earlier or later one:
- Not "onboarding screens viewed" — that measures exposure to the pitch, not behavior change, and is trivially near-100% in treatment by construction (everyone sees the new screens), which would tell us nothing.
- Not same-session completion only — the one-pager's moment of use is "just finished a solo reading/problem-set session," which for most students won't be the signup session itself. A same-session-only metric would undercount and mostly measure whether onboarding can strong-arm one check, not whether it primed the student to use the feature at its real moment of use.
- 7 days, not 1 or 30 — one week is short enough to still be attributable to onboarding's framing (not diluted by unrelated in-app prompts a student might hit later) and long enough to contain at least one realistic independent-study session for most course loads.

## Success threshold

**Ship the redesigned onboarding if:**
1. Treatment's D7 check-completion rate exceeds control's by **≥10 percentage points absolute**, with a 95% CI on that difference excluding zero (two-sided test, α = 0.05), **and**
2. The lift is not purely onboarding-forced novelty: among users who did *not* complete a check in week 1, the week-2 (days 8-14) completion-rate difference between arms retains **at least half** of the week-1 lift.

**Why 10pp, not just "statistically significant":** a lift that's significant but tiny (e.g., +1pp) isn't worth the cost of a heavier, more front-loaded onboarding flow that spends more of a new user's attention before they've done anything else in the app. 10pp is a judgment call, not derived from existing data — this repo has no analytics baseline for current check-adoption rate. **This number must be replaced before launch** once the team has the actual current organic (non-onboarding-driven) check-completion rate; if that baseline is, say, already 20%, a 10pp ask is a 50% relative lift and may be too aggressive, and if baseline is near 0%, 10pp may be too conservative. Re-run the sample-size math below with the real baseline before enrolling users.

**Why the durability check matters:** onboarding can trivially inflate week-1 completion by, e.g., forcing a check as a final onboarding step. That would hit the headline number without telling us whether the redesign actually changed the student's standing behavior at their real moment of use. Requiring the lift to partially persist into users who *didn't* convert in week 1 is a cheap guard against declaring victory on a forced first touch that doesn't generalize.

## Sample size and duration

Using a two-proportion test at 80% power, α = 0.05 two-sided, and a placeholder baseline (control) rate of **p₁ = 15%** (unverified — flag as an assumption to replace with real data) against a target treatment rate of **p₂ = 25%** (the +10pp bar above):

- n ≈ 247 per arm for the core comparison alone.
- Target **~1,000 users per arm** (2,000 total) in practice, not 250 — the durability check and the segment guardrail below both split the sample further and need more power than the headline test alone.

**Duration — plan for 5 weeks (35 days), structured as:**
- **Enrollment window: 3 weeks (21 days).** Floor of 2 full weeks regardless of how fast the N target is hit, so the sample isn't skewed to a single weekday/weekend pattern or a single point in the academic calendar (evidence in `docs/issue-1` ties usage intensity to exam-period crunch, so a window entirely inside or entirely outside exam season would bias results). Cap of 6 weeks — if the N target isn't reached by then, close enrollment and analyze with whatever power was achieved rather than let the test run into a new confound (e.g., crossing into finals changes baseline behavior for reasons unrelated to onboarding).
- **Follow-on window: 14 days after the last enrolled user**, so every cohort has a full 7-day primary-metric window and a full 14-day durability window before the final read. No interim peeking / early stopping on the primary metric — check only at the pre-registered readout date, to avoid inflating false-positive risk from repeated looks.
- If actual weekly signup volume is known and much higher than what gets ~1,000/arm in 3 weeks, shorten the enrollment window accordingly and keep the same 14-day follow-on.

## Guardrails — what to watch so a win here isn't a quiet loss elsewhere

All guardrails are pre-registered non-inferiority checks, evaluated at the same readout as the primary metric (not used to stop the test early except for a severe breach, defined below):

| Guardrail | Concern | Threshold |
|---|---|---|
| Onboarding completion rate (finishes account setup) | New flow is longer/adds a pitch step; could raise drop-off before the account even exists | No more than 3pp absolute drop vs. control (95% CI) |
| D1 retention (any app open next day) | Front-loading a "you might not understand as well as you think" message could be off-putting on first contact | No more than 2pp drop |
| D7 overall retention (not feature-specific) | Redesign could win the feature metric while net-losing general engagement | No more than 3pp drop |
| Time to first core action (first note/flashcard/deck created) | Onboarding attention spent explaining the check is attention not spent getting users to the app's existing core loop | Median should not increase by more than 20% |
| Check abandonment rate (started, not finished) | If onboarding oversells the check without the student being ready to use it, expect starts that don't convert | Flag for review if abandonment exceeds 40% in treatment |
| Uninstall/opt-out within 7 days | Direct signal of the new framing landing badly | No more than 1pp increase |
| Support tickets / reviews mentioning "confusing," "pressured," "anxious" tied to onboarding | Qualitative early-warning that a quantitative guardrail hasn't caught yet | Any material increase (judgment call, not a fixed number) triggers manual review before shipping |

**Segment guardrail, tied directly to the feature's own stated job:** the one-pager and the underlying discovery report (`docs/issue-1`) both note the students who most need this feature — the least-prepared, per Kruger-Dunning — are also the worst at judging their own comprehension and, plausibly, the group most likely to find a "you might be overestimating yourself" pitch uncomfortable. Cut the primary metric by an available proficiency proxy (e.g., self-reported confidence at signup, or prior-course performance if available) and confirm the lift among the **lowest** band is not reliably smaller than the overall lift. If the redesigned onboarding's adoption lift is concentrated in already-strong, already-confident students while the target population is flat or negative, that is a quiet failure the headline number would hide — the feature would be reaching the users who need it least.

**Severe-breach stopping rule (the one case that does justify stopping early):** if D1 retention or uninstall rate crosses more than 2x its threshold above at any weekly interim check, stop enrollment and investigate before the scheduled readout — this is a safety valve for a badly broken flow, not a mechanism for early-stopping on the primary metric.

## Decision rule

- Primary metric hits its bar **and** no guardrail breaches → ship the redesigned onboarding as default.
- Primary metric hits its bar **but** a guardrail breaches → do not auto-ship; escalate the specific tradeoff (adoption lift vs. the harmed metric) for a human decision.
- Primary metric misses its bar → do not ship the redesigned onboarding globally. The comprehension-gap check itself is unaffected by this outcome — it can still exist in-app and be discovered organically; this only means front-loading it into first-run onboarding didn't pay for itself.

## Open items / assumptions to replace before launch

1. **Baseline check-completion rate (p₁ = 15%) is an assumption, not measured data** — this repo has no product analytics. Pull the real current organic completion rate and re-run the sample-size and threshold math above before enrolling users.
2. **Actual weekly new-signup volume** is unknown here and needed to convert the 3-week enrollment floor/cap into a concrete calendar date range.
3. **Proficiency proxy for the segment guardrail** (self-reported confidence, prior grades, etc.) needs to be confirmed as something actually collected at signup; if nothing exists, that's a gap to close before this guardrail can be evaluated, not a reason to drop it.
