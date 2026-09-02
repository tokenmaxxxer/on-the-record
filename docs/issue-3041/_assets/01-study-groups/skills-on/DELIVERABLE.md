# Brief: Study-Group Matching (by Course + Exam Date)

## Bottom line

Not worth building yet. It's a plausible feature but currently an unvalidated bet on
a *different* user problem than the one this product is actually built around, and
none of the demand/quality assumptions it depends on have been tested. Recommend a
cheap, non-engineering validation pass before writing any matching code.

## Context that should shape this decision

The repo's current live requirement (R1) is about individual comprehension gaps —
a student can't identify what they specifically don't understand in lecture
material — and that requirement itself is still `[proposed]`, not yet confirmed by
interviews. Study-group matching is a social/coordination feature, not an
extension of that hypothesis: it assumes the bottleneck is *finding the right
people*, not *understanding the material*. Treat it as a separate hypothesis with
its own evidence bar, not a natural next step for R1. If both are pursued, they
will compete for the same discovery and engineering capacity, so sequencing
matters.

## What would need to be true for this to succeed

1. **The bottleneck is real and specific.** Students who want a study group for a
   given course/exam currently fail to form one — not because groups are hard to
   *find*, but because they're hard to *match well* (compatible pace, commitment
   level, schedule). If students already solve this via KakaoTalk/class chats/
   in-person asking, matching software adds little.
2. **There's a liquidity floor.** For any given course + exam date, enough
   students need to be active on the platform at the same time to form a
   non-trivial group (3-5 people). Below that density, "matching" degrades to an
   empty waiting room — the classic marketplace cold-start problem, and worse here
   because demand is calendar-spiky (everyone wants a group in the same 2-week
   window before exams, then the need vanishes).
3. **Matching quality beats naive grouping.** Course + exam date alone is a weak
   signal — it doesn't capture study pace, current understanding level, or
   commitment. If match quality isn't meaningfully better than "post in the class
   group chat," students won't route through us.
4. **Groups actually meet and it changes behavior.** The feature only matters if
   matched groups convert to real study sessions and those sessions show up in
   retention or outcomes (return usage, self-reported help, eventually grades/
   comprehension proxies) — not just "group created."

## How we'd know quickly if it's not working

Run this as a manual/low-tech pilot before building matching infrastructure:

- Post a lightweight signup ("want a study group for [course] before [exam]?") for
  2-3 popular courses near a real exam date, form groups by hand.
- **Kill/continue signals within 1-2 weeks:**
  - **Signup-to-group conversion:** if fewer than ~30-40% of signups end up in a
    group people will actually message could plausibly indicate the demand isn't
    real or density is too thin — you're not routing anything, you're a lonely
    signup form. Note that a threshold this specific hasn't been tested here; treat
    it as a starting assumption to refine once you see real distributions, not a
    fixed law.
  - **Group activation:** if formed groups don't produce a first real interaction
    (message, meeting, call) within 48 hours of formation, the group is dead on
    arrival — matching alone didn't solve the coordination problem.
  - **Repeat intent:** if students who go through it once don't want to do it
    again next exam cycle, this is a one-off utility, not a retention driver worth
    permanent product surface area.

These signals are cheap to get with a form + spreadsheet + manual matching —
no app feature required to learn the first-order answer.

## What would make us stop or change direction

- **Density never clears the floor** outside a couple of huge intro courses —
  i.e., the long tail of courses can't be matched, so the feature only works for a
  small slice of catalog. Stop building general matching; consider it a niche
  feature for high-enrollment courses only, or drop it.
- **Students report existing informal channels (class chats, KakaoTalk) are
  "good enough."** If the honest failure mode is "I could find people but didn't
  bother," this is a motivation problem, not a matching problem, and software
  won't fix it.
- **Groups form but don't meet or don't return.** If activation and repeat-use
  signals stay low even after adjusting group size/composition, the core
  hypothesis (that better matching drives real study behavior) is falsified —
  don't keep iterating on matching algorithms, the problem is downstream of
  matching.
- **It cannibalizes focus from R1 without evidence R1 is wrong.** Since R1 is the
  product's stated core bet and is itself unvalidated, spending the next
  discovery cycle on study groups instead of finishing R1's validation should be
  an explicit, conscious tradeoff — not something that happens by default because
  this feature is easier to picture.

## Recommended next step

Before any engineering: run the manual pilot above for one exam cycle on 2-3
courses, using existing chat tools for coordination. Decide continue/stop based
on signup-to-group conversion, 48-hour activation, and repeat intent. Only build
automated matching if the manual version clearly works and density looks
sufficient across more than a couple of courses.
