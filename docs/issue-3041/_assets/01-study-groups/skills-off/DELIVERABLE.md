# Brief: Should we build course/exam-date study group matching?

## Context check

This repo currently has no product code — only a requirement digest (`docs/specs/requirement-digest.md`). Its one entry, R1, is a `[proposed]` (not yet validated) hypothesis about an *individual* comprehension-gap problem: students can't identify what specifically they don't understand in lecture material or a textbook. The discovery evidence behind R1 is itself incomplete — the "can't articulate which part" clause rests on one unverified source, and there's early evidence that at least one existing AI tutor already serves part of that job.

Study group matching is a different job-to-be-done: *social/logistical coordination* (finding compatible peers, scheduling around a shared deadline) rather than *individual diagnosis* (finding your knowledge gap). Before investing, it's worth being explicit that this is a pivot/addition, not a natural extension of R1 — the two features could succeed or fail independently, and matching doesn't obviously help solve the comprehension-gap problem R1 is chasing. If the team's real goal is still "help students find what they don't understand," group matching is a detour unless there's a specific causal story connecting the two.

## What would need to be true for this to succeed

1. **Enough concurrent demand density.** For a given course + exam date, there need to be enough active users to form groups of 3-6 people who are actually available around the same time. This is the single biggest risk: it fails silently if the user base per course/section is too thin, and thinness is worst exactly when the app is new (cold start, before there's any user base to point to as proof of value).
2. **Students actually want strangers, not their existing circle.** Most students already coordinate study groups through classmates, group chats, or in-person contacts. The matching feature only adds value if it reaches people the existing informal network doesn't — e.g., students new to a school, commuter/online students, or people in large lecture courses without built-in cohorts. If the target users already have a way to solve this, matching is redundant.
3. **Matching by course + exam date is sufficient signal for a *good* group.** Course and date alone say nothing about study level, pace, personality, or reliability. If mismatched groups (a mismatch in preparedness or effort) causes bad experiences, churn will hit before density does.
4. **Someone follows through after the match.** A match is not a study session. There needs to be a low-friction path from "matched" to "actually met/talked," or the feature just produces unused group chats — a common failure mode for matching products generally.
5. **The operational cost is proportionate.** Matching requires trust/safety basics (reporting, no-shows, harassment handling) even at small scale, since it puts strangers in contact. This is real cost that needs to be weighed against a feature that, unlike R1, isn't yet backed by any discovery evidence of unmet need.

## How we'd know quickly if it's not working

Design the earliest test to be cheap and fast, not a full matching engine:

- **Cheapest test first:** before building an algorithm, manually post "who wants to study for [course] before [exam date]" prompts (or a simple sign-up + manual pairing) to a few real course cohorts and see if people sign up and show up. This tests demand and follow-through without writing a matcher.
- **Leading indicator — signup-to-match ratio:** if fewer than a large majority of signups within a course/date cohort actually get matched within a useful window (e.g., a few days before the exam), density is too thin and the algorithm won't fix it — you need concentration in specific courses, not general rollout.
- **Leading indicator — match-to-contact ratio:** if matched groups aren't messaging or scheduling within ~48 hours of being matched, the "follow-through" assumption is false and no UI polish will fix it — that's a signal to interview those users directly.
- **Retention signal:** do students who complete one matched session request another (same exam season or next one)? One-and-done usage suggests curiosity, not a repeatable need.
- **Qualitative signal:** in early interviews/pilot debriefs, ask directly *how* students currently form study groups. If most say "I just ask people in my class/chat," that's a strong sign the informal network already covers this and matching is solving a problem few people have.

## What would make us stop or change direction

- **Stop:** the manual/cheap pilot shows persistent thin density (can't reliably form groups of 3+ in target courses) even when concentrated on the highest-enrollment courses — this means no amount of algorithm sophistication will fix a structural cold-start/liquidity problem.
- **Stop:** signups happen but match-to-contact and contact-to-meetup rates stay low across multiple pilot cohorts — the feature is generating dead matches, not study sessions.
- **Change direction (narrow scope):** demand is real but concentrated in a specific segment (e.g., only large intro courses, or only students without existing local networks — new/transfer/online students). If so, build for that segment specifically rather than a general matching feature.
- **Change direction (change the mechanism):** students want grouping but reject algorithmic matching (prefer browsing/opting in themselves, or want to filter by more than course+date). If so, a lighter "board" or opt-in directory may beat a matching algorithm and is much cheaper to build and reverse.
- **Reconsider fit with R1:** if the team wants to keep the comprehension-gap hypothesis as the core bet, and study groups pilot data shows the effort required (trust & safety, density, follow-through infrastructure) is disproportionate to a still-unvalidated core product, it's worth explicitly deciding whether this is a distraction from validating R1 or a genuinely complementary feature — that decision should be made deliberately, not by default because building started.

## Bottom line

Don't build the matching algorithm first. Run the cheapest possible manual version inside a couple of real, high-enrollment course cohorts, and only invest in real infrastructure if it clears density, follow-through, and "not already solved informally" bars within that pilot. Given R1's own discovery is still incomplete, treat this as a separate hypothesis needing its own (lightweight) evidence, not as a bundled feature that inherits R1's justification.
