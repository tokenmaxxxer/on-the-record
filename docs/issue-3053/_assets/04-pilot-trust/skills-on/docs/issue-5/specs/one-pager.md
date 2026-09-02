# Product one-pager: a monitoring signal for the comprehension gap

Targets R1. Design-bearing, not implementation: no stack, no screens, no data model, no API — this document defines what job the product serves, for whom, against which alternatives, and what would prove the bet wrong.

## Background

Issue #1's landed discovery report (`docs/issue-1/reports/research-evidence-discipline+user-discovery-evidence-strength-tagging-1ae594fd/user-discovery.md`) evidences two distinct claims at very different strength:

- **Monitoring failure (Fact-tier, behavioral, rows 1-2):** university students are poor judges of their own comprehension — a weighted mean predicted-vs-actual correlation of 0.178 across 115 studies / 502 effects / 15,889 participants (Yang, Zhao, Yuan, Luo & Shanks, 2023), and the least-prepared students overestimate themselves most (Kruger & Dunning, 1999: bottom-quartile students at the 12th percentile actually, rated themselves at the 62nd). This is well-evidenced and structural, not occasional.
- **Articulation failure (unestablished):** the narrower claim that students, once they notice a gap, cannot *name* which specific part confuses them. The only support for this in the landed report is row 9 — a search-synthesized description of a paywalled metacomprehension paper the report itself could not fetch (HTTP 403) or independently verify, tagged `label: Assumption` with an explicit flag that it "should be the first thing a real interview round tests."

This one-pager builds for the first claim, not the second, and says so explicitly below, per the issue's own instruction not to launder the unestablished clause into a premise.

## Job

**Job performer:** a student studying independently, outside class and without a peer or instructor present — the moment this job arises is solo, not social.

**Job statement (circumstance + motivation + outcome form):** when a student has just finished reading or working through assigned material on their own, before any test, discussion, or office-hours visit, they want an accurate read on whether they actually understood it well enough to stop here, so they can decide whether to keep studying this material now, while it is still cheap to fix, or move on.

**Desired outcomes (independently measurable):**
1. Minimize the gap between the student's *felt* comprehension and their *actual* comprehension immediately after independent study — this is the same gap row 1's r = 0.178 correlation measures at population scale; the job is to shrink it for one student in one sitting.
2. Minimize the probability that a student stops studying, or moves to the next chapter, while a real, unaddressed comprehension gap remains.
3. Achieve (1) and (2) **without requiring the student to already be able to say what specifically is wrong** — detection must not presuppose the capability the articulation clause claims and the report could not verify.

**Which framing this is, explicitly:** this is the **monitoring** job — "do I actually understand this, yes or no, and roughly where" — not the **articulation** job — "can I state precisely what confuses me about it." The report evidences the first at Fact tier and flags the second as its single weakest, unverified link. Building for articulation would mean building on an assumption the report explicitly could not check; building for monitoring builds on rows 1-2, which are Fact-tier and independent of the disputed row 9.

**What breaks if this framing is wrong:** if a real interview round finds row 9's disconfirming signal holds — students, when actually confused, generally *can* name the specific concept or step they're stuck on — then the bottleneck was never self-diagnosis. In that world, a monitoring signal that tells a student "you have a gap around section 3" is redundant: the student already knew that. The unmet job would instead be resolution-availability (getting a correct, timely explanation once the gap is already known), which is the job rows 4 and 6 below show is already being served, at least partially, by existing tools. A monitoring-only product built on the wrong framing would be solving a step students don't actually need help with, while the step they do need help with (resolution) is handled elsewhere. This is a falsifiable bet, not a hedge — see Falsifier below.

## Moment of use

A student finishes a solo reading or problem-set session — a textbook chapter, a set of lecture notes, a problem set worked without a study group. Under today's default (the true competing alternative, per JTBD-fit: not a rival product, but doing nothing — trusting the felt sense of "I think I've got this" and closing the book), the student's only signal that they understood is how *fluent* the material now feels, which row 1 shows is a weak proxy for actual comprehension, and which re-reading (below) actively inflates without checking anything.

In this moment, the product inserts a short, automatically-scored check — retrieval or generation prompts drawn from the material just covered, scored against the actual content, not against the student's confidence — before the student is allowed to treat the session as closed. The output is a comprehension-accuracy signal at the section or concept level ("your checked understanding of section 3 was low; sections 1-2 were solid") — a *location*, not a *diagnosis*. It never asks the student to explain their own confusion, and it never explains the material itself; it reports a measured mismatch between felt-done and checked-done, and where in the material that mismatch sits.

What the student does with that signal — re-study alone, ask a peer, ask an LLM, go to office hours — is outside this product's job; the product's job ends at making the gap visible and located, at the moment it would otherwise go unnoticed.

### Against Re-reading

Failure mode: **illusion of fluency** (row 1, Yang et al. 2023) — re-reading raises how familiar a passage feels without proportionally raising actual comprehension, because familiarity and comprehension are read off the same felt sense the student cannot independently check.

**Attacks this directly.** The core mechanism of the product is to replace the student's own felt-fluency judgment with an externally checked, scored signal at the exact moment re-reading would otherwise let a false sense of "done" stand unchallenged. This is the product's primary differentiator: none of the other three coping behaviors below produce a checked signal at all.

### Against Office hours

Failure mode: **the resource demands the thing the student lacks** (row 7) — office hours require converting a diffuse "I don't get this chapter" into a specific, askable question before the visit is worth making, and most students never make that conversion.

**Attacks this, narrowly.** A per-section accuracy signal hands the student a specific location ("section 3 was where the check missed") without requiring the student to already be able to say *why* it's wrong — location, not diagnosis, which is the one thing this product's job statement commits to not presupposing. It converts "I don't get this chapter" into "I don't get section 3," which is enough to make an office-hours visit, a peer question, or an LLM prompt specific — but the product does not itself resolve anything past that point.

### Against Asking a peer

Failure mode: **shared-ignorance ceiling** — a peer at a similar point in the material can confirm a shared misconception rather than correct it, with no independent check built into the exchange; the Crimson account (row 4) names the flip side directly, that peer discussion's real value is "five or ten different ways of thinking," a diversity a single possibly-wrong peer explanation collapses.

**Declines to attack this.** A detection-only product has no mechanism for judging whether a subsequent peer explanation is correct or diverse enough — that is a resolution-quality problem, and this product's job ends before resolution starts. Out of scope by design, not by oversight.

### Against Generic LLM Q&A

Two failure modes, both Fact-tier: the **crutch effect** (row 3 — unrestricted AI access raised practice-time success while lowering unassisted-test success, closing the felt gap without closing the real one) and **confident fabrication compounded by the target population's own gap** (LLMs answer wrong questions with unhedged confidence, and a population with an undetected comprehension gap is the population least equipped to catch a plausible-sounding wrong answer).

**Declines to attack this.** This product does not generate explanations or answers at all, so it cannot itself produce a crutch effect or a fabricated explanation — but that is a structural side effect of staying out of the resolution step, not a claim that this product fixes generic-LLM Q&A's failure modes when a student uses one elsewhere after the gap is flagged. Explaining well, or fabricating badly, is explicitly not this product's job.

## Counter-evidence: is this distribution of an already-solved capability?

Two pieces of counter-evidence from the landed report, addressed by name, not omitted:

- **Kestin et al. (2025), *Scientific Reports*:** a crossover RCT of **194 Harvard undergraduates** in one introductory physics course found a purpose-built AI tutor produced significantly larger learning gains, in less time, than an in-class active-learning condition — a real, peer-reviewed result, at single-course scale.
- **Kumar, *The Harvard Crimson* (2024):** a named Harvard undergraduate reports that, after campus-wide ChatGPT Edu access, he feels "no need to go to office hours, open a textbook, or work through problems with peers" — a first-person account of an existing AI tutor already replacing all three of the report's most-cited coping behaviors, for at least one real student.

**Frame:** the question this counter-evidence forces is whether building anything new here is redundant with a capability that already exists and mostly needs distribution, not invention.

**Position:** split by job step, not a single yes/no. For the **resolution** step — explaining material well once a gap is known — both pieces of evidence say that capability increasingly looks solved and already being distributed: Kestin's RCT is peer-reviewed evidence that a purpose-built tutor already out-explains a taught-content alternative, and Kumar's account is direct evidence that an existing tool is already doing that job end-to-end for at least one student. This product deliberately declines to compete there (see the two "Declines to attack" sections above) — building a second resolution engine against evidence this strong would be exactly the redundant move the counter-evidence warns against.

For the **monitoring** step this product actually targets, neither piece of evidence is direct evidence either way. Kestin's RCT compares two ways of *delivering* content within a course; it does not measure whether the 194 students knew, unprompted, which parts they had failed to learn. Kumar's account describes replacing resources he already knew to consult — office hours, textbook, peers — not discovering a gap he did not know he had. Both accounts are downstream of the monitoring step working (or not being tested at all); neither is evidence that detection itself is already solved or already being distributed.

**Confidence and falsifier for this position:** roughly 65/100 — split-verdict positions like this one are exactly where a single strong counter-example does the most damage. It would flip if a lightweight scan of an already-deployed tool of Kumar's kind (campus AI-tutor rollouts, PS2-Pal-style systems) turned up a monitoring signal as a byproduct of normal use — e.g., the tool already surfaces "you're weak on X" before the student asks anything — in which case detection would already be getting distributed alongside resolution, and this product's remaining opportunity would shrink to whatever gap exists between an incidental byproduct signal and a purpose-built one.

## Falsifier

The smallest thing that would tell us this framing is wrong: run a targeted interview/pilot round (the landed report's own recommended next step) with 15-20 students, pairing each student's self-predicted score on material they just studied against their actual score on a comprehension check of that same material, and asking students who score low to state, unprompted and before seeing the check's results, what they expected to be weak on.

**Time bound: within 6 weeks of starting that round.** If, within that window, a majority of the low-scoring students can independently and correctly name the section or concept the check flags as weak *before* being shown the check's result, that replicates row 9's disconfirming signal under direct questioning rather than leaving it an unverified secondary source — the monitoring gap this product targets is not the bottleneck for this population, the articulation/resolution framing (row 6/row 4 territory, already being closed by existing tools) is the better bet instead, and this specific detection-only angle should stop rather than proceed to a build.
