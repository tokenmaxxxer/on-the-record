---
role: ml-engineering
mode: parallel (5 WebSearch angles, round 1) + 1 deepening round (5 more WebSearch angles) = 2 stages total
---

# Scout brief — ml-engineering operational playbook

## Decision axes (6, matching this role's PHASE-2 required components)

canonical: this session's own SessionStart role directive (ml-engineering PHASE 2 required components list, read this turn).

1. serving-pattern-selection (batch vs online-sync vs online-async/streaming)
2. slo-definition-tradeoffs (latency/availability/throughput/cost SLIs, error budget policy)
3. rollout-promotion-rollback (shadow -> canary -> full, promotion/rollback gates)
4. ml-test-score-scoring (Breck et al. 2017's four sections: data, model, infra, monitoring tests)
5. model-provenance-versioning (Mitchell et al. 2019 model card fields + data/model version identifiers)
6. evaluation-discipline (offline metric/holdout vs online A/B/shadow/canary, decision rule)

## Must-bes per axis (category must-bes a strong practitioner source assumes)

- serving pattern: a default choice keyed to latency tolerance and traffic shape. source: https://xebia.com/blog/ml-serving-architectures/ , cross-checked against https://arxiv.org/pdf/1612.03079 (Clipper) — batch for bounded-latency-tolerant bulk work, online-sync for per-request low latency, online-async/streaming for continuous unbounded input.
- SLO: chosen from user tolerance rather than an arbitrary round number, with an explicit error-budget policy gating deploy velocity. source: https://sre.google/sre-book/service-level-objectives/ and https://sre.google/workbook/error-budget-policy/
- rollout: multi-gate pattern (offline eval -> shadow -> canary -> full) with automated threshold-based promote/rollback. source: https://docs.cloud.google.com/architecture/guidelines-for-developing-high-quality-ml-solutions
- ML Test Score axis: source: https://research.google/pubs/the-ml-test-score-a-rubric-for-ml-production-readiness-and-technical-debt-reduction/ — Breck et al. 2017's rubric assigns a per-item score across its four sections rather than prose description.
- model card: Mitchell et al.'s named field set (model details, intended use, factors, metrics, evaluation data, training data, ethical considerations, caveats/recommendations). source: https://arxiv.org/pdf/2403.15394 (secondary summary of Mitchell et al. 2019 field categories)
- evaluation: offline (holdout/backtest vs. threshold) reported separately from online (A/B/shadow/canary decision rule). source: https://exp-platform.com/Documents/2017-05-17EmetricsControlledExperimentsPitfallsKohaviNR.pdf — Kohavi et al. require SRM/randomization validation for an online result to be trusted.

## Performance axes strong sources compete on

- automation of the promote/rollback gate (threshold-based vs. human judgment). source: https://docs.cloud.google.com/architecture/guidelines-for-developing-high-quality-ml-solutions favors automated threshold checks.
- skew-detection method sophistication (L-infinity norm vs. Jensen-Shannon divergence). source: https://www.tensorflow.org/tfx/guide/tfdv supports both; JS divergence is preferred for mixed categorical+numeric features.
- SRM as a precondition for trusting any online result. source: https://arxiv.org/pdf/2208.07766 reports SRM as a frequent, silent invalidator of A/B test results when unchecked.

## Adopt / skip

- Adopt: condition->choice->source rule format, mirroring the api-design-rulebook exemplar surveyed in docs/issue-1174/proposals/operational-playbook-program.md section (d).
- Adopt: explicit REMOVAL-category rules per axis (amendment 4) — e.g. dropping shadow-mode as a gate when traffic is too low for a meaningful comparison sample; dropping a stale/redundant SLI from a dashboard.
- Skip: full MLOps maturity-model framing — canonical: this session's own SessionStart role directive, Prohibited list, "adopting the MLOps full-lifecycle-maturity frame (out of WRITE_SCOPE per issue-1 §b's explicit skip)."

## Segment fit

ml-engineering's issue-1174 role directive names the axis boundaries directly (serving design / ML Test Score / model provenance / eval discipline); the axis list above maps that directive's four PHASE-2 components plus the serving-pattern sub-decision it implies.

## Gap line

canonical: `ls docs/issue-1174/reports/ml-engineering/` command run this turn against the working tree before this write, output: directory not present. This role's playbook content for issue-1174 starts from this session; the six axes above had no prior content in this issue's tree to build on.

## Sources

- https://research.google/pubs/the-ml-test-score-a-rubric-for-ml-production-readiness-and-technical-debt-reduction/ (Breck et al. 2017, ML Test Score, primary)
- https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/aad9f93b86b7addfea4c419b9100c6cdd26cacea.pdf (Breck et al. 2017 full PDF)
- https://arxiv.org/pdf/2403.15394 (secondary discussion of Mitchell et al. 2019 model card categories)
- https://docs.cloud.google.com/architecture/guidelines-for-developing-high-quality-ml-solutions (Google Cloud, canary/shadow rollout guidance)
- https://www.qwak.com/post/shadow-deployment-vs-canary-release-of-machine-learning-models (shadow vs canary practitioner comparison)
- https://sre.google/sre-book/service-level-objectives/ (Google SRE book, SLO definition)
- https://sre.google/workbook/error-budget-policy/ (Google SRE workbook, error budget policy)
- https://www.tensorflow.org/tfx/guide/tfdv (TFX Data Validation, training-serving skew detection)
- https://exp-platform.com/Documents/2017-05-17EmetricsControlledExperimentsPitfallsKohaviNR.pdf (Kohavi, trustworthy online controlled experiments pitfalls)
- https://arxiv.org/pdf/2208.07766 (Sample Ratio Mismatch automated detection)
- https://lakefs.io/blog/mlflow-data-versioning/ (MLflow/DVC data+model versioning practice)
- https://xebia.com/blog/ml-serving-architectures/ (batch/online-sync/online-async serving pattern taxonomy)
- https://arxiv.org/pdf/1612.03079 (Clipper: Low-Latency Online Prediction Serving System)
