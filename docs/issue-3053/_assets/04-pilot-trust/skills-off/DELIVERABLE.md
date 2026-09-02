# Review: does the pilot in docs/issue-5/specs/one-pager.md actually let a bad result stop the project?

## Bottom line

No. As written, the pilot has exactly one exit ramp — a "stop" condition — and no corresponding "proceed" condition. Every outcome that isn't that one specific, high-bar disconfirming result (a majority of low-scoring students correctly self-diagnosing, unprompted, before seeing the check) defaults to "proceed," including outcomes that should worry the team: too few qualifying students, ambiguous scoring, a null result, or the pilot simply running out of time. A design with one asymmetric exit ramp isn't a stop/go test; it's a test that can only ever confirm.

## What the pilot as written actually tests

Read closely, the Falsifier section (one-pager.md:76-80) only pre-registers a rule for one direction:

> "If ... a majority of the low-scoring students can independently and correctly name the section or concept the check flags as weak before being shown the check's result ... this specific detection-only angle should stop rather than proceed to a build."

There is no sentence anywhere in the document that says what result would make the team proceed with confidence, versus proceed by default because the stop trigger wasn't hit. That asymmetry is the core problem, and everything below is a consequence of it.

## Specific checks I'd want the team to run before treating this as pre-registered

**1. Write the proceed rule down, not just the stop rule.**
Right now "proceed" is whatever isn't the one named stop condition. That means an inconclusive, underpowered, or ambiguous pilot silently counts as a green light. Ask the team to state, in the same document, what result they'd accept as evidence *for* building — not just the absence of the disconfirming one.

**2. Define "low-scoring" and the target n of that subgroup, not just total enrollment.**
The stop rule only engages for "the low-scoring students," a subset of the 15-20. If, say, only 3-4 students land in that bucket, "a majority" could be 2 people. Ask: what score threshold defines "low-scoring," and how many low-scoring students does the pilot need to reach before the stop rule is even eligible to fire? Without a floor, a pilot that happens to produce few low scorers can't trigger a stop no matter what the true rate is — which is itself a silent bias toward proceeding.

**3. Establish a chance baseline for "correctly name the section or concept."**
If the comprehension check only covers, say, 3-4 sections, a student could name the right one at 25-33% by pure guessing, with zero real diagnostic insight — inflating apparent articulation ability and making a stop less likely to trigger even if the product's premise is right. Conversely, if the material is finely divided into many sub-concepts, correct guesses become very hard to produce even when real insight exists, making stop nearly impossible to trigger regardless of the true rate. Either way, "majority correctly names it" is uninterpretable without knowing the check's granularity and the corresponding chance rate. Ask for that number before running the pilot, not after.

**4. Specify who judges "correctly name" and how, in advance.**
Matching a student's stated guess ("I was weak on section 3") to what the check reports is a judgment call with room for generous or strict interpretation. If the same team that wants the product to proceed is also the one scoring the match, that's a conflict of interest baked into the single number the stop rule hinges on. Ask for a scoring rubric and, ideally, a rater blind to which answer would trigger a stop.

**5. Ask what happens to the predicted-vs-actual data that's actually collected.**
The pilot's primary measurement, per the design, is pairing each student's self-predicted score against their actual score (one-pager.md:78) — that's the same gap the product exists to shrink (Desired Outcome 1, one-pager.md:20-21). But the stop/proceed rule is built entirely on the secondary articulation question, not on this primary pairing. If this cohort's predicted-vs-actual gap turns out to be small or absent — i.e., these 15-20 students turn out to be good self-assessors — that would be a real disconfirming signal for the premise the whole product rests on, and there's currently no rule that reacts to it at all. Ask the team to pre-register a rule for this measurement too, not just for the articulation add-on.

**6. Check the sample size against what it can actually detect.**
15-20 total students, an unknown and possibly small low-scoring subgroup, and a "majority" threshold on that subgroup is a very high-variance test. Ask for a quick power sketch: if the true population rate of correct unprompted self-diagnosis is, say, 30% or 50%, what's the probability this pilot's subgroup produces a "majority" by chance alone? If nobody can answer that before running it, the team doesn't yet know whether a null result means "the effect isn't there" or "the pilot was too small to see it" — and by default, that ambiguity resolves to proceed.

**7. Ask what happens on attrition or a missed 6-week window.**
The time bound is "within 6 weeks of starting that round" (one-pager.md:80), but there's no stated fallback if enrollment, scoring, or follow-up slips past that window, or if dropout shrinks the low-scoring subgroup below whatever floor is set in check #2. Silently extending the deadline, or quietly treating a shrunken sample as sufficient, are both ways an ambiguous result becomes a de facto proceed.

## What I'd tell the team

Run the pilot, but don't treat it as pre-registered yet. As written, it's a test that can produce a "stop," but can't produce a confident "proceed" — every ambiguous or underpowered outcome collapses to "proceed" by default, which means the pilot is structurally biased toward confirming the decision the team has probably already leaned toward. Before starting the clock on the 6 weeks, get the team to write down, in the same document: (a) an explicit proceed condition, not just a stop condition; (b) a minimum n of qualifying (low-scoring) students required before the rule is eligible to fire; (c) the chance-guessing baseline for the comprehension check's granularity; (d) a pre-committed, ideally blinded scoring rubric for "correctly name"; (e) a rule for the predicted-vs-actual gap itself, since that's the pilot's primary measurement and currently has no decision rule attached to it at all; and (f) what happens on attrition or a missed deadline. If the team can't answer these before the pilot starts, the 6-week clock should not start yet — filling these in after seeing partial data is exactly how a pilot gets tuned to whatever answer was already expected.
