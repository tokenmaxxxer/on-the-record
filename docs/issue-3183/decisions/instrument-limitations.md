---
issue: 3183
type: instrument-limitations
date_stamp: 2026-09-03
status: registered-as-limitations-not-solved
---

# issue-3183 — instrument limitations (R007 consumer-path trust root)

This file states four honesty items the issue requires written into the
record as **limitations of the instrument**, not as problems this issue's
deliverable (`scripts/consumer-path/prepare_arms.py` +
`verify_manipulation.py`) solves. Moving the trust root outside the
spawned process (this issue's actual scope) closes the two forgeability
failures PR #3180 found in the prior design — it does not, and cannot,
close any of the four below.

## 1. Model memorization of skill content

Environment control (a fresh HOME, a skills root that is populated for
"on" and genuinely absent for "off") proves what the spawned process
*could reach on disk*. It cannot prove what the underlying model already
knows. If a skill's guidance overlaps with content the model memorized
during training, the "off" arm's deliverable can still reflect that
guidance's substance even though no skill file was reachable that run —
and the manipulation check in `verify_manipulation.py` would correctly
report `manipulation_held: true` for that pair, because the environment
really was isolated as prepared. A clean manipulation check is evidence
the toggle worked; it is not evidence the toggle is the only channel by
which skill-shaped content could reach the deliverable. This is not
fixable by anything the launcher controls — it would require knowing the
model's training distribution, which this instrument has no access to
and no way to probe.

## 2. Partial self-identification of skill-shaped output

Even with skill slugs scrubbed before blind scoring (the approach
`scripts/issue-3127/run_consumer_pair.py`'s `scrub_skill_slugs()` already
takes for H2, not part of this issue's deliverable but the downstream
consumer of a pair this instrument clears), skill-shaped output can
partially self-identify through structure alone — a numbered procedure
with named gates, a specific evidence-grading footer, a characteristic
section ordering — none of which is a literal slug match a regex can
catch. A blind evaluator reading such a document may correctly infer "a
skill produced this" without ever seeing the skill's name, which leaks
arm identity into what is supposed to be a blind quality read. Blinding
here is partial, not absolute, and the instrument this issue delivers has
no mechanism to detect or bound that leak — it only proves the
environmental manipulation held, not that the downstream blind score is
free of this leak.

## 3. Single-run-per-arm is not evidence

One manifest, one verified pair, proves the manipulation held for that
one run. It says nothing about whether skills help, hurt, or make no
difference — a single paired observation has no statistical standing to
support a directional claim in either direction. Per
`docs/issue-3127/decisions/pre-registration.md`'s own power statement, at
this scale a result is a directional read at best, never a significance
test. **The design target for this instrument is a minimum of five
paired trials** before any H2-style quality or efficiency claim is
interpreted from data this instrument's pairs feed into — this issue
delivers the manifest+verification machinery one pair needs, not the
sample-size discipline that makes a collection of pairs interpretable,
which is the separate, out-of-scope work of actually running and scoring
the pairs (see the accompanying record's scope note).

## 4. Operator independence

Whoever runs `prepare_arms.py` controls both arms' isolation and is
recorded verbatim in the manifest's `operator` field — but that field is
self-reported by the same process that prepares the arms; nothing in
this instrument cryptographically ties it to the actual OS identity that
invoked it, and nothing prevents the same party who benefits from a
particular result from also being the one who ran the launcher. A
manifest whose `operator` field names the person or team whose
hypothesis the result would favor is not disqualified by anything this
instrument checks — that remains a procedural question for whoever
interprets a completed pair's results, not something `verify_manipulation
.py`'s fail-closed checks can settle. State plainly: **who ran the
launcher for any given pair must be recorded and disclosed alongside
that pair's result**, and a launcher run by the party whose hypothesis
the result favors should be treated with the same Twyman's-law
skepticism `experiment-trust` applies to any large, surprising win.
