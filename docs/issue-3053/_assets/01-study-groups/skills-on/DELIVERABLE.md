# Brief: should study-group matching (by course + exam date) be built next?

**Scope gate:** this is a genuine, still-open build-or-don't decision — nothing has shipped toward it yet — so it's worth running through before committing engineering time. (per `hypothesis-testing`)

## Verdict: different job, and it competes for the team's attention right now

**Different job, not the same one.** The job we've committed to building for (`docs/issue-5/specs/one-pager.md`) is explicitly a **solo, monitoring** job: "when a student has just finished reading or working through material *on their own* ... they want an accurate read on whether they actually understood it." The job performer is defined as solo by design — "the moment this job arises is solo, not social." Study-group matching is the opposite shape: it's a **social coordination** job — "find me people to study with" — that fires before or independent of any individual study session, not at the moment a comprehension gap appears. There's no version of "match students by course and exam date" that answers "do I actually understand this, yes or no, and roughly where." It's a different job with a different performer-state (about to study, or coordinating logistics) and a different outcome (a group exists) than the one the one-pager defines.

**It doesn't just fail to serve the chosen job — it re-enters territory the one-pager deliberately excluded.** The one-pager's "Against Asking a peer" section explicitly declines to compete on peer study, and names why: peer discussion has a **shared-ignorance ceiling** — a peer at a similar point in the material can confirm a shared misconception with no independent check, and the product's monitoring job "has no mechanism for judging whether a subsequent peer explanation is correct or diverse enough... out of scope by design, not by oversight." Study-group matching doesn't fix that failure mode; it makes the failure-prone coping behavior easier to access at scale. It's building distribution for the exact alternative the chosen job was scoped to not compete with.

**It competes for attention, concretely.** Two reasons this isn't just "a different feature we could also build":
1. The chosen job's own falsifier — a 15–20 student interview/pilot round, pre-registered with a 6-week time bound, testing whether students can name their own weak spots before seeing a comprehension check — does not appear to have been run yet based on what's in `docs/issue-1` and `docs/issue-5` (secondary-source discovery and a one-pager exist; no pilot-results report does). Spending build time on group matching now means committing engineering effort *before* knowing whether the monitoring bet the team already chose is even right.
2. Group matching is not a small add-on. It's a two-sided marketplace problem (matching needs density per course × exam-date cohort to work at all) with its own discovery, cold-start, and moderation questions that have had zero discovery work done against them in this repo. It would need its own JTBD framing and evidence base from scratch, run in parallel with — and drawing on the same limited team attention as — the still-unvalidated monitoring bet.

## If it were pursued anyway: what would need to be true

- **A liquidity/density claim**: enough students per course + exam-date cohort, in the same term, to form viable groups — this is the classic marketplace cold-start problem and the one place this idea could fail silently (matching exists but never fires because there's no counterparty).
- **A displacement claim**: that students who want a group don't already have one via existing channels (class GroupMe/KakaoTalk chats, dorms, clubs, section discussion boards). If those already solve group-formation, matching has no job to do.
- **A quality claim that answers the shared-ignorance ceiling**: matching by course and exam date alone doesn't select for complementary knowledge — it could just as easily assemble a room of people all missing the same section. Some mechanism (mixed skill level, staggered progress, etc.) would need to exist for matched groups to outperform status-quo self-organized ones.

## How we'd know quickly if it's not working

- **Match-activation rate**: of groups formed, % that exchange a first message or hold a first session within ~1 week of matching. A pilot with a handful of courses, measured over 2–3 weeks, is enough to see whether matches turn into real groups at all.
- **Opt-in rate** among eligible active students — low opt-in signals students already have a group-formation solution (see displacement claim above).
- **Abandonment before exam date**: groups that form but go silent before the exam they were matched around.
- A lightweight survey question to non-adopters — "did you already have a study group for this course?" — would directly test the displacement claim within the same pilot window, without a separate research cycle.

## What would make us stop or change direction

- **Stop**: a 2–3 week pilot shows most matched groups never activate (e.g., under ~20-25% hold even one session), or most eligible students report already having a group — either result means there's no real coordination gap to fill, and the idea should be killed rather than iterated on.
- **Change direction**: activation is fine but groups consistently converge on the shared-ignorance failure mode (a matched group collectively stuck on the same section, per the coping-behavior analysis in `docs/issue-1`) — that's a signal to pivot the matching criteria (e.g., stagger by self-reported progress or the monitoring product's own per-section signal, once it exists) rather than kill the idea outright.
- **Escalate/reprioritize regardless of pilot result**: if the still-unrun falsifier for the monitoring job (the 15–20 student interview round, `docs/issue-5/specs/one-pager.md` §Falsifier) hasn't been run, that should happen first. Running it doesn't cost the group-matching idea anything — it's cheap and fast — and it prevents building two unvalidated bets in parallel with the same limited attention.

## Recommendation

Don't build study-group matching next. Run the monitoring job's pre-registered falsifier interview round first — it's already scoped, cheap, and six-week-bounded. Treat study-group matching as a separate, later JTBD investigation (its own discovery pass, its own one-pager) if and when the team has spare attention, not as a natural extension of the monitoring product — the two jobs solve different problems for differently-postured students, and the one-pager already made a deliberate, evidenced call to stay out of the peer-coordination space this feature would re-enter.
