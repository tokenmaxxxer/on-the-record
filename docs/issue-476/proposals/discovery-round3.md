---
status: proposed
files:
  - docs/issue-476/reports/product-discovery/survey-round3.md
  - docs/issue-476/reports/product-discovery/scout-brief-round3.md
  - docs/issue-476/proposals/discovery-round3.md
---

# Proposal — issue #476 round 3: the upstream half (spawn/refusal-incentive theater)

Phase 1 only. `docs/issue-476/reports/product-discovery/survey-round3.md`
found that the landed enforcement set (77 rows in
`docs/specs/enforcement-boundary.md`, spanning issues #457/#517/#791/
#793/#870/#914/#923/#476 rounds 1-2) fully covers the downstream half of
issue #476 — is a written claim traceable and re-runnable — and leaves
the upstream half untouched: was the role spawned out of genuine need,
given a real question rather than a decided answer, and does refusing
cost it nothing relative to fabricating. This proposal pre-registers
which upstream candidate to build next, a metric, a threshold, and a
decision rule, before any hook or `spawn.py` change is made.

## Candidates scored (RICE), against the JTBD and OST placement in
survey-round3.md

Reach/Impact scored against "role sessions spawned per week," the same
basis rounds 1-2 used. Effort in relative days. Confidence reflects
whether the candidate survived the scout brief's must-be check (second,
blind actor where possible; population-wide not trigger-only where
feasible; kill switch/fail-open posture matching every landed sibling
mechanism).

| # | Candidate | Reach | Impact | Confidence | Effort | RICE | Verdict |
|---|---|---|---|---|---|---|---|
| E | Refusal-cost-parity: a registered refusal/null-result `loop_state` is explicitly exempted from any implicit "deliverable produced" scoring path in `spawn.py`'s roster/board reporting | 5 | 4 | 0.7 | 1 | 14.0 | **Keep — primary, ships first** |
| F | Spawn-time task-string check: `spawn.py`-side check on a task string for an imperative solution clause with no accompanying open question | 4 | 4 | 0.4 | 2 | 3.2 | Keep, staged after E |
| G | Sampling audit: `spawn.py`'s roster watchdog periodically re-spawns a blind verifier session against a random fraction of landed records | 3 | 5 | 0.5 | 4 | 1.9 | Keep, staged after F — highest structural strength, highest cost |
| H | Diversity/non-transcription check comparing a record's content against its own spawning task string | 2 | 2 | 0.3 | 3 | 0.4 | **Reject for this round** |

### Why each non-primary candidate is scored the way it is

- **E (primary)**: reach and impact are highest because it touches every
  spawned role, not a subset (unlike F, which only matters for spawns
  whose task string is solution-shaped, or G, which only samples a
  fraction). Effort is lowest — it is a scoring/reporting-path change on
  the orchestrator side, not a new interception point, and the repo
  already has the vocabulary (H2's refusal strings, `loop_state`
  registries) to key off of. Confidence is capped below round one/two's
  own top scores because "cost nothing" is being asserted about a
  human-facing reporting surface this proposal has not yet read in
  detail — the architecture phase must confirm exactly where that
  implicit scoring currently lives before design.
- **F**: the direct answer to the issue's own named "orchestrator task
  strings often contain the solution" instance, but confidence is capped
  at 0.4 because distinguishing "an imperative clause because a real
  decision was already made upstream and is legitimately not open" from
  "an imperative clause because the orchestrator pre-decided the answer"
  is a judgment call a regex cannot make reliably — the scout brief's
  gap line already flags this as the field's hardest-to-avoid false-
  positive class (an audit checklist rule that fires on legitimate
  narrow-scope tasks). Staged after E so E's rollout data informs
  whether F's false-positive risk is worth taking.
- **G**: scored highest on Impact (blind second-actor sampling is the
  field's strongest structural pattern per the scout brief) but lowest
  Reach (samples a fraction, not the whole population, by construction —
  full-population re-verification is not affordable) and highest Effort
  (needs a new spawn path, a comparison/scoring step, and a place to
  record divergence — closer to round 1/2's H1 build than E or F).
  Staged last, after E and F's own rollout data narrows what to sample
  against.
- **H — reject for this round**: the scout brief's own segment-fit note
  says this repo's constraint rules out anything requiring persistent
  infrastructure; a diversity/overlap check needs either an n-gram
  comparison step (new infra) or a second LLM judgment call (itself
  gameable by paraphrase, the same shape weakness round two's rejected
  candidate D shared). Revisit only if E/F/G's own data shows role
  sessions transcribing task strings verbatim as a live pattern, not
  ruled out as impossible, ruled out as this round's build target absent
  evidence that gap is real.

## Pre-registered hypothesis package

**H3-refusal-parity (primary, this round).** If a registered refusal or
null-result `loop_state` is explicitly exempted, in `spawn.py`'s own
roster/board reporting path, from whatever implicit signal currently
reads "deliverable produced" as success, then the rate at which role
sessions report a refusal/null-result outcome (rather than manufacturing
a deliverable) on tasks that genuinely warrant one will rise, because
the issue's own named mechanism — refusal reading as failure, so
sessions manufacture deliverables — is a reporting-incentive problem,
not a vocabulary problem (H2 already supplied the vocabulary in round
one; this round changes what happens to a session that uses it).

- **Metric**: `refusal_parity_rate` = (role sessions, across a fixed
  post-rollout window, whose final record uses a registered refusal/
  null-result `loop_state` AND whose spawning task the operator or a
  sampled review agrees genuinely warranted refusal) / (role sessions in
  that same window whose spawning task genuinely warranted refusal,
  regardless of what the session actually reported). This is
  deliberately NOT "rate of refusal records observed" — a rising raw
  refusal rate is ambiguous (could mean either fewer manufactured
  deliverables or a mechanism newly over-triggering refusal); the
  denominator anchors the metric to tasks that actually warranted
  refusal, established by a small sampled human/independent-session
  review, same discriminating-assumption-test shape as rounds 1-2.
- **Threshold**: `refusal_parity_rate` ≥ 80% over the next 30
  qualifying spawns after the change ships (a spawn "qualifies" if the
  sampled review judges refusal was warranted). Chosen below rounds 1-2's
  95%/90% bands deliberately — this metric depends on a judgment call
  (was refusal warranted) that rounds 1-2's mechanical citation checks
  did not need, so a lower bar reflects the metric's own noisier
  ground truth, named here rather than silently inflated to match
  rounds 1-2's stricter bands.
- **Guardrail metric**: `false_refusal_rate` = (role sessions reporting
  refusal/null-result whose spawning task did NOT genuinely warrant
  refusal, i.e. real deliverable work existed) / (all refusal/null-
  result reports in the window) — must stay ≤15%. A parity fix that
  makes refusal "free" must not also make refusal the path of least
  resistance for tasks that actually needed doing; this guardrail is the
  round's own version of rounds 1-2's `false_reject_rate`, same pairing
  discipline the scout brief's must-be #1 names.
- **Decision rule**: `refusal_parity_rate` ≥80% AND `false_reject_rate`
  ≤15% → **go**, proceed to stage F (task-string check) using this
  round's rollout data to calibrate F's false-positive risk.
  `refusal_parity_rate` <80% → **pivot**: the scoring-path change did not
  reach the actual incentive (e.g. a human orchestrator still reads
  refusal as failure regardless of what `spawn.py` reports) — the next
  round must locate where the real incentive lives (operator perception,
  a different reporting surface, PR-merge behavior) rather than assuming
  `spawn.py`'s own reporting path was the lever. `false_reject_rate`
  >15% → **kill-and-redesign**: refusal became the easy default,
  punishing genuine deliverable work — the same guardrail failure mode
  rounds 1-2 already named for their own metrics.
- **Gaming-resistance argument**: the exemption lives in the
  orchestrator's own scoring/reporting path, not in anything the spawned
  role session can write into its own record — a role cannot make itself
  look more "successful" by refusing, because the parity fix removes the
  asymmetry rather than adding a self-reportable field the role controls
  (the same distinction the survey's discriminating-assumption-test
  section draws between candidates a role can satisfy unilaterally and
  ones it cannot).
- **Failure signature**: fails quietly if the "deliverable produced"
  signal this round targets is not actually where the perceived-failure
  pressure comes from — e.g. if it comes from human operator reaction to
  a refusal record rather than any mechanized `spawn.py` scoring path,
  the fix changes nothing a role session experiences. Named here so the
  architecture role is on notice: locating the ACTUAL current scoring
  path (not assuming it is `spawn.py`'s roster watchdog) is this round's
  first architecture task, not a given.

## Accumulation

This proposal is incremental atop rounds 1-2's own H1/H1b/H2 work, not a
restart: it reuses the same `loop_state` refusal vocabulary H2 already
registered, the same discriminating-assumption-test standard rounds 1-2
established, and the same RICE-scoring/pre-registration shape both prior
rounds used. No prior round's mechanism is being replaced or reworked —
H1/H1b's citation-and-re-execution mechanism and this round's refusal-
parity mechanism are additive, covering distinct halves of the same
outcome (downstream traceability vs. upstream incentive), per the
opportunity-solution-tree placement in survey-round3.md.

## What did not work

None.
