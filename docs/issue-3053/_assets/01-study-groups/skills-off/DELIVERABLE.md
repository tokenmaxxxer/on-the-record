# Should we build course/exam-date study-group matching next?

## Bottom line

**Different job, and it competes for the team's attention right now.** It is not a
variant of the job we already committed to in `docs/issue-5/specs/one-pager.md`, and
building it does not reuse the evidence base or the falsifier test we already have in
flight for that job. It also lands on a coping behavior (`Asking a peer`) that
issue-1's own discovery report and the one-pager both already looked at and treated as
out of scope, for a documented reason — not an oversight. I'd hold off until the
monitoring product's falsifier round has run.

## Why this is a different job, not the same one

The job we chose to build for (`docs/issue-5/specs/one-pager.md`, `## Job`) is
explicit on this point: *"the moment this job arises is solo, not social."* The job
statement is "a student who just finished studying alone wants an accurate read on
whether they actually understood it, before deciding to stop or keep going." The
outcome is a **comprehension signal for one student in one sitting** — it doesn't
touch other students at all.

Study-group matching is the opposite on every axis that job statement cares about:

| | Comprehension monitoring (chosen job) | Study-group matching |
|---|---|---|
| Performer | one student, alone | multiple students, coordinated |
| Moment | right after independent study, before deciding to stop | before studying even starts (a discovery/coordination step) |
| Output | a located accuracy signal ("section 3 was weak") | a formed group of people |
| What it measures/improves | predicted-vs-actual comprehension gap (row 1, r ≈ 0.178–0.27) | nothing about comprehension — success is "a group got formed" |

Study-group matching is, in issue-1's own vocabulary, the **`Asking a peer`** coping
behavior — just with better discovery/logistics in front of it. The one-pager already
addressed that coping behavior directly and **declined to attack it on purpose**:

> "A detection-only product has no mechanism for judging whether a subsequent peer
> explanation is correct or diverse enough — that is a resolution-quality problem...
> Out of scope by design, not by oversight." (one-pager, `### Against Asking a peer`)

And issue-1's discovery report names the specific failure mode that peer study already
has, with evidence: the **shared-ignorance ceiling** — a peer at a similar point in the
material can confirm a shared misconception instead of correcting it, with no
independent check in the exchange (issue-1 report, row 4's contrast; `Coping
behaviors → Asking a peer`). The report's own switching-trigger account (row 5) is a
student whose *study group* stopped being useful for exactly this reason — it "could
not stay on the specific topics he was still stuck on" — and he switched to a
one-on-one AI tutor instead. That's a real, sourced account of a student leaving group
study, not one asking to be matched into more of it.

So: building group-matching doesn't advance the monitoring job (it produces no
comprehension signal, located or otherwise), and it doesn't fix peer study's documented
failure mode either — it makes it easier to *find* a group, not more likely that the
group correctly resolves anyone's specific confusion once formed. It's a real,
plausible job in its own right ("help me find people in my course to study with before
this exam"), but it's an undiscovered one — no interview, survey, or secondary-source
work in this repo has evidenced that job the way rows 1–10 evidence the monitoring gap.
It would need its own discovery pass, not an extension of the current one.

## Does it compete, or can it run in parallel?

For a small team, yes, it competes for attention, for three concrete reasons:

1. **No evidence base exists for it yet.** The comprehension-gap work has ten sourced,
   strength-tagged rows behind it and a live falsifier test already scoped (a 15–20
   student interview round, 6-week window, testable by the team's own recommended next
   step). Group-matching has zero equivalent discovery. Starting it now means starting
   a second discovery track from scratch while the first one's decisive test hasn't
   even run.
2. **It's a bigger, riskier build than the chosen job.** The monitoring product is
   deliberately scoped to not touch other students at all (no matching, no messaging,
   no identity beyond one user). Group matching requires course rosters or
   self-reported course/section data, exam-date data, a matching algorithm, and — because
   it puts strangers in contact — some minimum of safety/moderation surface. That's a
   materially larger infrastructure and trust commitment for a job that isn't
   evidenced yet.
3. **It would dilute the falsifier that's already in motion.** The one-pager's
   6-week falsifier is designed to answer whether the *monitoring* framing is even the
   right bet before more is built on it. Splitting the team to prototype matching in
   parallel means the group most likely to answer "is row 9 wrong?" — the same
   students being interviewed — is also the group being pitched a different product,
   which muddies both signals.

The one place they could be genuinely complementary, not competing, is downstream: if
the monitoring product ships and works, its located signal ("you're weak on section 3")
is a plausible, evidenced *matching key* later — pairing students who are weak on the
same section, rather than just the same course and exam date, is a sharper match than
what's being proposed now. That's a reason to sequence group-matching *after*
monitoring ships, using its own output, not a reason to build it in parallel or first.

## What would need to be true for study-group matching to succeed, if pursued later

- Students who want a study partner can't currently find one for a reason that is
  **discovery/logistics**, not **fit/quality** — i.e., the bottleneck is "I don't know
  who else in my course is free before this exam," not "the groups I do form aren't
  useful" (row 4/row 5's shared-ignorance and bandwidth-mismatch failures would still
  apply to a matched group unless the matching key does something today's ad hoc
  groups don't).
- A matching signal exists that beats "same course, same rough exam date" on the thing
  that actually breaks group study today — bandwidth/topic mismatch, per row 5 — such
  as matching on *which sections/concepts* a student is behind on, not just enrollment.
- Enough students can be matched into a *non-empty, differentiated* group at the same
  moment of need (cold-start: a matching product with too few concurrent users produces
  empty results, which is worse than doing nothing).

## How we'd know quickly if it's not working

- **Match-to-first-session conversion is low** — students get matched but never
  actually meet/study together. This would mean the barrier was never discovery; it was
  always trust, scheduling friction, or motivation, and matching software doesn't touch
  those.
- **Groups form but don't reconvene** — one session and no repeat usage would replicate
  row 5's ceiling: the group hits the same shared-ignorance/bandwidth wall today's ad
  hoc groups hit, just found faster.
- **Students report they already have a group** (via existing chats, classmates, clubs)
  and don't need matching — this would mean the "discovery" framing of the problem was
  wrong from the start, i.e., there's no real gap between wanting a group and finding
  one.

## What would make us stop or change direction

- If a lightweight discovery pass (interviews, same rigor as issue-1's) can't find a
  documented case of a student who *wanted* a study group and *couldn't find one* — as
  opposed to a case where a group existed but didn't help — the job doesn't exist in
  the form assumed here, and this should stop before any build.
- If the monitoring product's falsifier round (already scoped, 6-week window) comes
  back negative — i.e., row 9 holds and students *can* name their own gap — the team's
  reframed priority becomes resolution-availability (per the one-pager's own stated
  pivot), and group-matching becomes a much more plausible *next* bet, worth
  re-evaluating then, not now.
- If safety/moderation cost (putting previously-unconnected students in direct contact)
  turns out to require more infrastructure than the team can support at this stage,
  that's a reason to scope down to something lower-risk (e.g., surfacing existing
  university-run or LMS-based groups) rather than building a new matching system from
  scratch.
