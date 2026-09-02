---
issue: 3053
type: pre-registration
date_stamp: 2026-09-02
status: registered-before-data-collection
---

# issue-3053 — pre-registration (hypothesis-testing Step 4 / product-discovery-hypothesis-preregistration)

Written before `scripts/issue-3041/run_pair.sh` is invoked for real against
the corrected harness. No pair has been run under this registration at the
time this file is written; `git log` on this branch and the absence of
`docs/issue-3053/_assets/` at this commit are the check.

## Theory (hypothesis-testing Step 2)

We believe mounting the marketplace skill corpus (`--plugin-dir`, alongside
the existing `--setting-sources project,local`) will produce higher-quality
blind-scored deliverables from the skills-on arm than the skills-off arm,
for a consumer session doing product/growth, experimentation, architecture,
and data/trust-adjacent tasks on a target repo with real content, because
the corpus gives the model access to methodology procedures (falsifiability
gates, pre-registration forms, guardrail checks, statistical-power framing)
it would otherwise have to reconstruct ad hoc or omit under time/tool
pressure.

## Hypotheses (Step 3)

- **H1 (manipulation check, precondition, not itself the R007 hypothesis)**:
  the skills-on arm's init event shows more than the 17 built-in skills in
  at least 3 of 4 runs. Falsifiable: could return 0 of 4 (as issue #3053's
  retracted baseline did).
- **H2 (the R007 hypothesis)**: across the 4 grounded pairs, the skills-on
  arm's blind deliverable score is higher than the skills-off arm's in a
  majority of pairs, with a combined margin large enough to read as a
  directional signal rather than noise. Falsifiable: could come back tied,
  reversed, or with the corpus mounted but no score movement (the "consumer
  session never opens it" finding restated with a working corpus this time).

## Pre-registration form (Step 4)

| Field | Content |
|---|---|
| (a) Hypothesis | H2 above; H1 is the gating precondition for interpreting H2 at all |
| (b) Test design | `scripts/issue-3041/run_pair.sh`, 4 pairs, 4 disciplines (product/growth, experimentation, architecture, data/trust), target repo `JiwonJung94/study-companion` pinned at `d6f14aebd1a79002fda3a7f22320ee63c6e7a736`; blind evaluator (`evaluate_pair.py`) scores each document 1-10 against a discipline rubric with no arm labels visible to it; `instrument.py` plus a raw `jq`/`python3` re-derivation from each `skills-on.session.jsonl` init event, independent of the evaluator |
| (c) Metric and measurement window | Per-pair `document_1_score`/`document_2_score` (mapped back to skills-on/skills-off via the sibling `document_N_actual_arm` field, never shown to the evaluator); one run per arm per pair, no repeated sampling; skill_opens count and init-event skill-count per skills-on run, recorded alongside but never passed to the evaluator |
| (d) Threshold values with decision rule | **Manipulation-check gate (H1, must pass before H2 is interpreted at all)**: mount counts as verified only if >=3 of 4 skills-on init events show `len(skills) > 20`. If this gate fails, H2 is reported as unmeasured/mount-failure, not as a null (must-not clause). **H2 decision rule, registered given n=4 (too small for a significance test — this is a directional read, not a statistical one, and is stated as such in the verdict)**: skills-on is called *better* if it scores higher in >=3 of 4 pairs AND the combined score margin (sum(skills-on) − sum(skills-off) across all 4 pairs) is >=3 points; *worse* under the symmetric condition; *indistinguishable* otherwise (a 2-2 split, or any win count with margin in [-2, 2]). Skill-open count is diagnostic only (per the issue's must-not clause) — it is never itself the pass condition for H2, only for H1 |
| (e) Sample size / duration | n=4 pairs, fixed in advance by the harness's existing task set and this session's budget — not extended or shrunk after seeing any result; one run per arm, no interim peeking at partial pairs before all 4 have completed |
| (f) Date stamp | 2026-09-02, before `run_pair.sh` is invoked under this registration |

## Deviations log

- 2026-09-02: the first invocation of all 4 pairs (relative `<output-root>`
  `docs/issue-3053/_assets`) failed both arms of all 4 pairs at the
  `claude -p` step itself (exit 1, no session log, no deliverable) — a
  pre-existing bug in `run_pair.sh`, not something this registration
  anticipated: `run_arm()` redirects to `"$pair_dir/$arm.session.jsonl"`
  *after* `cd`-ing into the per-arm workspace, so a relative `$pair_dir`
  resolves against the wrong cwd. Fixed by resolving `pair_dir` to an
  absolute path immediately after `mkdir -p` (see `run_pair.sh`). No
  deliverable or session log exists from this failed first attempt, so no
  measurement is affected — it produced zero data, not wrong data. All 4
  pairs re-run from scratch (`rm -rf` on the failed pair dirs first) under
  the same registration above; nothing about the registered metric,
  threshold, or decision rule changed.

## Scope note (experiment-trust)

This is an offline, small-n (4) paired comparison with pre-assigned
conditions (one skills-on run and one skills-off run per task, not random
assignment of live traffic to variants) — `experiment-trust`'s scope gate
(Step 1) routes this away from SRM/A-A-validation machinery, which applies
to online controlled experiments with random unit assignment at volume.
Applying chi-square/A-A checks here would be theater; the applicable
machinery is `hypothesis-testing`'s pre-registration discipline above, not
`experiment-trust`'s Steps 2-6.
