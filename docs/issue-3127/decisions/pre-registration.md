---
issue: 3127
type: pre-registration
date_stamp: 2026-09-02
status: registered-before-data-collection
---

# issue-3127 — pre-registration (product-discovery-hypothesis-preregistration Step 4)

Written before `scripts/issue-3127/run_consumer_pair.py` is invoked in any
non-`--dry-run` mode. No pair has been run under this registration at the
time this file is written; `git log` on this branch and the absence of a
populated `docs/issue-3127/_assets/consumer-path-results.json` (still the
skeleton from the same commit as this file, `run_status: "not_executed"`) at
this commit are the check that `scripts/issue-3127/verify_preregistration.py`
runs mechanically.

## Theory (Step 1)

Issue #3053 measured a floor condition (bare `claude -p`, no orchestrator, no
`--skills`) and found the skills-on/skills-off blind-score margin
indistinguishable (+1, short of its own registered threshold). It also found
that under the real consumer path — `/on-the-record:run`'s orchestrator
naming skills via `spawn.py --skills` — the same corpus opened 4/4 at BM25
positions 0.12-0.16, against 0.36-0.83 in the floor condition: selection
quality itself differs by path, not just skill availability. We believe that
running both arms through the real `spawn.py --skills` path — same
orchestrator dispatch, same issue, same task, differing only in whether the
skill corpus resolves to anything when spawn.py mounts it — will surface an
effect the floor condition was structurally unable to see, because the floor
condition never exercised the selection/mounting machinery the product
actually uses.

## Hypotheses (Step 2)

- **H1 (manipulation check, gating precondition, not itself the R007
  hypothesis)**: in every completed skills-on arm run, the spawned session's
  init event and directive-composition byte count differ measurably from
  the paired skills-off arm's (i.e. the corpus actually mounted something
  beyond the identically-named `--skills` argument). Falsifiable: could
  return identical directive bytes across arms, meaning the toggle did not
  actually change what the spawned session received (a repeat of #3053's
  first, retracted zero-mount run).
- **H2 (the R007 quality hypothesis)**: across the registered pairs, the
  skills-on arm's blind deliverable score (scrubbed of skill-slug mentions
  before scoring, per #3053's leak finding) is higher than the skills-off
  arm's in a majority of pairs, with a combined margin large enough to read
  as directional rather than noise. Falsifiable: could come back tied,
  reversed, or mounted-with-no-score-movement.
- **H3 (the R007 efficiency hypothesis — the half of the operator's goal
  sentence no prior run measured)**: the skills-on arm needs fewer
  verification rounds per landed PR than the skills-off arm, and/or reaches
  a landed deliverable in less wall-clock, without a token-cost increase
  large enough to erase the efficiency gain. Falsifiable: skills-on could
  need the same or more rounds/wall-clock/tokens than skills-off, which the
  issue explicitly requires reporting as data, not as an excluded bad run.

## Pre-registration form (Step 3, rules 1-5)

| Field | Content |
|---|---|
| (a) Primary metric | H2's blind deliverable score margin (sum(skills-on) − sum(skills-off) across all registered pairs), scored by a rubric-based evaluator blind to arm identity, against each issue's own acceptance criteria |
| (b) Numeric threshold + decision rule (ship criterion, rule 2) | skills-on is called **better** if it scores higher in >=3 of the registered pairs AND the combined margin is >=3 points (same magnitude #3053 registered, for continuity across the floor-vs-consumer-path comparison); **worse** under the symmetric condition; **indistinguishable** otherwise (a tie in win-count, or any win count with margin in [-2, 2]) |
| (c) Guardrail metric + bounded degradation limit (rules 4-5) | wall-clock-to-landed-PR for the skills-on arm must not exceed the skills-off arm's by more than 50% combined across registered pairs, AND verification-round count for skills-on must not exceed skills-off's by more than 1 round combined. A primary-metric win recorded alongside a breached guardrail is reported as **a breach, not an unqualified win** (rule 6) — this is the mechanical form of the issue's own instruction that a same-or-more verification burden on the skills-on arm means "the layer is costing time without buying correctness" even if H2 reads as a win |
| (d) Secondary/diagnostic metrics (not gating, reported regardless) | token cost (total per session + directive-composition bytes alone), verification-round defect counts (not just round counts), BM25 selection position per skill mount (H1's manipulation-check evidence) |
| (e) Sample size / duration (rule 3, rules 9-10) | Registered at n = 2 pairs minimum for a first real run (matched to the two toy tasks already scaffolded in `docs/issue-3053/_assets/01-study-groups` and `docs/issue-3053/_assets/02-onboarding-experiment`'s task text, reused so pair identity is held constant across the floor-condition and consumer-path measurements), extensible to the full n=4 set `run_consumer_pair.py --plan` enumerates. One run per arm per pair, no repeated sampling, no interim peeking before all registered pairs complete. **At n=2-4 this is not a powered significance test** — the decision rule above is a directional read, stated as such in every verdict this harness emits, per experiment-trust's Twyman's-law framing (a large, surprising swing at this n is exactly the shape to distrust before trusting) |
| (f) Date stamp | 2026-09-02, before `run_consumer_pair.py` is invoked under this registration in any executing mode |

## Power statement (must-not clause: no null without stating what it could detect)

At n=2 pairs (1 skills-on + 1 skills-off run each), a binary win/loss/tie
read per pair has no meaningful statistical power — a two-outcome comparison
cannot distinguish a true small effect from noise at this sample size under
any reasonable significance convention. The registered decision rule above is
explicitly a **directional threshold**, not a significance test: it can only
ever report "met" or "not met" against the fixed ±3-point/50%-time/1-round
bars, never "no effect exists." A future run that returns "indistinguishable"
under this registration means the sample could not resolve an effect smaller
than the registered margin (3 points on this rubric's scale, roughly a
one-grade-band shift per pair) — it does not mean no such effect exists. If
this registration is extended to the full n=4 set, that remains true; a
change of decision rule after seeing partial results is itself a mid-flight
threshold change and is refused per rule 8 regardless of n.

## Deviations log

- 2026-09-02: this registration's harness (`run_consumer_pair.py`) was not
  invoked in any executing mode this session — see the accompanying record's
  "Rationale for deviations" section for why, and `docs/issue-3127/_assets/
  consumer-path-results.json`'s `run_status` field for the mechanical
  statement. This is a deviation from the issue's ask to run the
  measurement, not a change to the registered metric, threshold, decision
  rule, or sample size above — those remain fixed for whichever session
  executes this harness next.

## Scope note (experiment-trust Step 1 — scope gate)

This is an offline, small-n (2-4) paired comparison with pre-assigned
conditions (one skills-on run and one skills-off run per task through the
same `spawn.py` invocation shape, not random assignment of live production
traffic to variants). `experiment-trust`'s SRM/A-A-validation machinery
(Steps 2-6) targets online controlled experiments with random unit
assignment at volume; applying chi-square/A-A checks to a 2-4-pair offline
comparison would be theater. The applicable machinery is this skill's
pre-registration discipline above, plus `experiment-trust`'s Twyman's-law
skepticism (Step 1) applied to any large, surprising swing this harness's
future run reports — that skepticism is why the decision rule above is
framed as directional, not as a significance claim, at this n.
