---
subject: issue-1199
role: ml-engineering
kind: scout-brief
---

# Scout brief: ml-engineering tool landscape (issue-1199)

Mode: parallel WebSearch fan-out (4 angles: model serving, experiment
tracking, data/model validation, feature/data versioning), 1 sweep
stage, 1 verification stage via `gh api repos/<org>/<repo>`
(adoption-evidence method per tech-feasibility). The verification
stage's star-count ranking matched the sweep's category ranking, so a
third round was not run.

canonical: `echo mlflow/mlflow wandb/wandb evidentlyai/evidently treeverse/dvc feast-dev/feast kserve/kserve bentoml/BentoML fivetran/great_expectations | xargs -n1 -I{} gh api repos/{} --jq '{name:.full_name, stars:.stargazers_count, forks:.forks_count}'`, run this session (see counts below).

## Surveyed tools (adoption evidence, live-fetched)

- **MLflow** (mlflow/mlflow): 27,496 stars / 6,147 forks, 30M+ monthly
  package downloads and Apache-project community per an August 2026
  DeployBase comparison (https://deploybase.ai/articles/mlflow-vs-wandb,
  fetched this session). Problem: an ML run's code, params, metrics,
  and artifacts are scattered across notebooks/logs with no single
  traceable identifier. How: each run is registered as one atomic
  record (params + metrics + artifact hash + code version), and the
  model registry stages a specific run's artifact through named
  lifecycle states (e.g. staging/production) rather than a floating
  branch tag. Learning: reproducibility and provenance claims should
  bind to one concrete run identifier that carries code+data+config
  together, not a prose assertion that training is reproducible.
- **Weights & Biases** (wandb/wandb): 11,231 stars / 881 forks, 21.6M+
  monthly PyPI downloads per the same DeployBase comparison (fetched
  this session). Problem: comparing a new model against history is
  usually eyeballed from scattered logs. How: every run comparison is
  plotted against a pinned baseline run, not an undefined "past
  performance." Learning: an offline-evaluation threshold claim should
  name the specific baseline run/model version it is measured against.
- **Evidently** (evidentlyai/evidently): 7,800 stars / 896 forks,
  described by its own repo description as covering "100+ metrics"
  across tabular and GenAI systems (canonical:
  `gh api repos/evidentlyai/evidently --jq .description`, run this
  session). Problem: "the model looks off in production" is usually
  one vague drift alarm with no distinction of what actually shifted.
  How: input/feature drift, prediction drift, and target/concept drift
  are reported as separate named metrics, each with its own statistical
  test and threshold. Learning: a monitoring-tests section should
  distinguish input drift, prediction drift, and label/concept drift as
  separate checkable items, not one generic "drift" line.
- **DVC** (treeverse/dvc — canonical: `gh api repos/treeverse/dvc --jq .full_name`,
  run this session, confirms the current canonical org after transfer):
  15,814 stars / 1,321 forks. Problem: large training datasets and
  model artifacts can't live in git directly, so version history and
  data/model lineage silently drift apart. How: DVC replaces the large
  file with a small content-hash metafile committed to git, so the
  hash — not a mutable filename or tag — is the version identifier.
  Learning: a data/model version identifier should be content-derived
  (hash-based), not a mutable label, or two records claiming the same
  version can silently reference different bytes.
- **Feast** (feast-dev/feast): 7,207 stars / 1,398 forks, the Linux
  Foundation AI & Data project's feature store (canonical:
  `gh api repos/feast-dev/feast --jq .description`, run this session).
  Problem: a feature computed at training time can differ from the
  same feature served at inference time (train/serve skew) when
  freshness isn't controlled. How: point-in-time-correct feature
  retrieval ties every feature value to the timestamp it was valid at,
  so training and serving pull from the same time-consistent view.
  Learning: training/serving skew detection should check feature
  freshness/point-in-time consistency specifically, not just aggregate
  distribution drift.
- **KServe** (kserve/kserve): 5,787 stars / 1,616 forks, a CNCF
  Incubating project (canonical:
  `gh api repos/kserve/kserve --jq .description`, run this session) —
  and **BentoML** (bentoml/BentoML): 8,784 stars / 1,009 forks.
  Problem: promoting a new model version to production is often an
  all-or-nothing cutover with no automatic revert path. How: both
  standardize canary rollout as a named traffic-percentage schedule
  with an automated promotion/rollback trigger tied to a measured
  metric threshold, not a manual "watch and decide" step. Learning: a
  serving design's rollout-stage requirement should force a concrete
  traffic-percentage schedule and an automated trigger condition.
- **Great Expectations** (fivetran/great_expectations — canonical:
  `gh api repos/fivetran/great_expectations --jq .full_name`, run this
  session, confirms current canonical org after transfer): 11,709
  stars / 1,797 forks. Problem: "does this data match what the model
  expects" is usually checked ad hoc. How: each check is a named,
  individually-addressable expectation
  (`expect_column_values_to_be_between`, etc.) scoped to one field, run
  as a gate, instead of one blanket verdict line covering the whole
  dataset. Learning: Data Tests should require expectations named per
  field, not one blanket verdict for the section.

## Gap line (rulebook's current state vs. the surveyed field)

canonical: `grep -n "Data Tests\|Monitoring Tests\|ML Infrastructure Tests\|Model Tests\|version" /tmp/claude-1000/b171/ml-engineering-rulebook/ml-engineering/hooks/directive.sh`, run this session.

The rulebook's directive already requires all four ML Test Score rubric
sections, a model card, paired data/model version identifiers, and
split offline/online evaluation — matching the surveyed field's shared
stance that these are structural requirements, not optional narrative.

It does not yet require: (1) per-field named expectations in Data
Tests; (2) a drift-type taxonomy (input/prediction/label) in Monitoring
Tests; (3) a single traceable run identifier binding code+data+config
in ML Infrastructure Tests; (4) content-derived (hash-based) version
identifiers in model provenance; (5) a concrete traffic-percentage
rollout schedule + automated trigger in serving design; (6) a minimum
comparison-window floor in eval discipline's online decision rule; (7)
a pinned baseline run/model version in Model Tests' offline-threshold
comparison.

## Adopt / skip

Adopt: all seven items above, each folded into the existing PRODUCES
doctrine and doctrine detail file as the role's own methodology
language (no tool name inside the public rulebook). Skip: MLflow's/
W&B's SaaS dashboard and UI-level features (out of `WRITE_SCOPE: []` —
this role is report-only); Great Expectations'/Evidently's own
execution engines (this role does not run pipeline code); Feast's/
DVC's storage-backend mechanics (infrastructure, not doctrine
language); KServe's/BentoML's Kubernetes deployment mechanics
(deployment implementation, not this role's serving-design doctrine
scope).
