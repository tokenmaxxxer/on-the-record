# Review: does the pilot in docs/issue-5/specs/one-pager.md let a bad result stop us?

## Bottom line

No — as written, the pilot can only produce a "stop" verdict on a narrow, hard-to-hit
condition, and produces "proceed" by default on every other outcome, including several
outcomes that should count as bad news. Before treating its result as the answer, the
decision rule needs to be made symmetric and several undefined terms need numbers attached.
This isn't a matter of rerunning statistics — the pilot hasn't started, so this is exactly
the moment to fix it (pre-registration must happen before data collection, not after).

## What the pilot actually says (quoting the one-pager's Falsifier section)

> run a targeted interview/pilot round... with 15-20 students, pairing each student's
> self-predicted score on material they just studied against their actual score on a
> comprehension check of that same material, and asking students who score low to state,
> unprompted and before seeing the check's results, what they expected to be weak on.
>
> Time bound: within 6 weeks... If... a majority of the low-scoring students can
> independently and correctly name the section or concept the check flags as weak before
> being shown the check's result... this specific detection-only angle should stop rather
> than proceed to a build.

That is one rule, pointing one direction: a specific result → **stop**. Nothing in the
document says what result → **proceed**, or what counts as an inconclusive result and what
happens to it. That asymmetry is the core problem, and everything below is a specific way it
shows up.

## What I checked this against

This is a go/kill decision on an idea, not yet committed to a build, so it's squarely
pre-registration territory (hypothesis-testing, product-discovery-hypothesis-preregistration
rules). It is *not* a randomized online controlled experiment — no random assignment, no
control arm, 15-20 self-selected students — so A/A validation and SRM checks
(experiment-trust) don't apply; the relevant discipline here is registering an unambiguous
metric, threshold, and decision rule for every branch of the outcome, before data collection.

## Specific gaps

**1. No persist/confirm branch — only a kill branch is defined.**
The rule states one condition that triggers "stop." It never states what result would count
as confirming the monitoring bet and justify proceeding with confidence, versus what counts
as an ambiguous result that should trigger *more* pilot, not a green light. As written, any
outcome that isn't "a majority of low-scorers correctly named the weak section" silently
defaults to "proceed" — including a 45% success rate, which is not "a majority" but is close
enough to a coin flip that it should probably not be read as confirming the bet either. A
complete decision rule needs three bins (stop / proceed / inconclusive-retest), not one.

**2. "Students who score low" has no numeric cutoff.**
Nothing defines what comprehension-check score counts as "low." Whoever runs the pilot will
be choosing that cutoff after seeing the score distribution — which is exactly the "threshold
added after results are visible" failure pre-registration exists to prevent. It also
determines the size of the group the whole verdict rests on: define "low" narrowly and the
subsample might be 3-4 students out of 15-20, at which point "majority" is decided by one or
two people's individual judgment calls, not a stable signal.

**3. "Correctly name the section or concept" has no rubric, no grader, no blinding.**
Exact match only, or partial credit for naming an adjacent topic? Who judges correctness —
the same person who ran the pilot and has a stake in the outcome? Is that person blind to
which section the check actually flagged as weak, or do they see both side by side while
scoring? Without a pre-written rubric and an independent or blinded grader, this judgment call
happens at the exact moment motivated reasoning is most likely to bend it — after the numbers
are in, when whoever wants to proceed can grade generously and whoever wants to stop can grade
strictly.

**4. The metric named in the pilot's description (predicted-vs-actual score gap) has no
threshold attached, but is still being collected.**
The pilot pairs "self-predicted score" against "actual score" for every student — that's the
headline measurement. But the decision rule never references the size of that gap; it's used
only to define who counts as "low-scoring" for the naming sub-task. That leaves a second,
unregistered number sitting in the data: a team that wants to proceed regardless of the
naming-task result has a ready-made alternative to point to ("look how big the predicted/actual
gap was") that was never bound to a threshold or a decision. A metric collected without a
number and a rule attached is not pre-registered — it's raw material for post-hoc
rationalization in whichever direction is convenient.

**5. No sample size or power justification for a "majority of low-scorers" threshold.**
15-20 students total, an undefined and likely small "low-scoring" subgroup, and a bright-line
majority rule on top of that subgroup is a fragile basis for a stop/proceed call either way. A
small-n test is not just imprecise — it's structurally biased toward failing to trigger the
stop condition by chance alone, which reinforces the default-to-proceed lean described in
point 1. There's no stated sample-size target for the "low-scoring" subgroup itself (only for
the pilot as a whole), so there's no way to know in advance whether the pilot can actually
detect the effect it's designed to look for.

**6. No interim-peeking or early-stop policy inside the 6-week window.**
The 6-week bound is a deadline, not a data-collection plan. Nothing says whether the team is
allowed to look at results as they trickle in and act early if the picture looks clear before
week 6, or whether they commit to waiting for the full window regardless. Without that stated
up front, an early look that "just happens" to land near a threshold is indistinguishable from
cherry-picking after the fact.

## What I'd tell the team

Run this pilot, but not as currently written. Before it starts:

1. Add an explicit proceed condition (e.g., "if fewer than X% of low-scorers can name the
   weak section unprompted, and predicted-vs-actual gap exceeds Y points on average, treat
   the monitoring bet as supported and proceed"), and an explicit inconclusive condition, so
   all three outcomes — stop, proceed, retest — have a rule instead of just one of them.
2. Define "low score" numerically (e.g., bottom tercile of the check, or below a fixed
   percentage-correct cutoff) before anyone sees the distribution.
3. Write the "correctly named" rubric in advance, and have it scored by someone blind to
   which section the check actually flagged, or use two independent graders and report
   agreement.
4. Attach a threshold to the predicted-vs-actual gap metric, or drop it from the decision
   rule entirely and label it descriptive-only so it can't be swapped in post hoc as the
   real justification.
5. State in advance roughly how many students are expected to land in the "low-scoring"
   group given 15-20 total, and treat a subgroup that ends up in single digits as too small
   to support a confident stop *or* proceed call — that's itself a possible outcome the rule
   should name ("if the low-scoring subgroup is smaller than N, treat the pilot as
   underpowered and extend or redesign rather than deciding").
6. Decide and write down now whether interim looks are allowed during the 6 weeks, and if so,
   under what rule — otherwise commit explicitly to a single look at the 6-week mark.

None of this requires a bigger or more expensive pilot — 15-20 students, 6 weeks, and the
predicted-vs-actual/naming design can stay as is. What's missing is the other half of the
decision rule and a few numeric definitions, all of which cost nothing to write down now and
everything to skip: without them, "run the pilot and treat its outcome as the answer" really
means "run the pilot and treat whichever outcome we get as license to proceed," because that's
the only branch the current design doesn't leave ambiguous.
