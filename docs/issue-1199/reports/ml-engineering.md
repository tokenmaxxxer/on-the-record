---
subject: issue-1199
role: ml-engineering
kind: record
---

# Record: ml-engineering tool-landscape fold-in (issue-1199)

code_under_review:
- ml-engineering/hooks/directive.sh
- docs/specs/record-norms.md

kind: record
loop_state: landed

## What was done
Approval for this role was posted on issue #1199 as the exact-match
comment `APPROVE issue-1199/ml-engineering` (canonical: `gh issue view
1199 --json comments -q '.comments[] | select(.body |
test("ml-engineering")) | .body'`, run this session — two matches, both
the exact string), so phase-2 proceeded on branch
`issue-1199/ml-engineering` in `tokenmaxxxer/ml-engineering-rulebook`.

Folded the seven design-move upgrades named in this branch's proposal
(docs/issue-1199/proposals/2026-08-13-ml-engineering-tool-landscape.md)
directly into the two named target files, and brought the rulebook
repo's docs/specs/record-norms.md Phase 2 section back in sync with
directive.sh's current four-component shape (it had been stuck on a
stale two-field/three-item "risk note" shape):

1. Data Tests — expectations now named individually per field.
2. Monitoring Tests — drift split into input/feature, prediction, and
   label/concept, each with its own statistic and threshold.
3. ML Infrastructure Tests — training reproducibility now requires one
   traceable run identifier binding code version + data version +
   config/hyperparameters together.
4. model provenance — data/model version identifiers now required to
   be content-derived (hash-based), not a mutable label.
5. serving design — rollout stages now require a concrete
   traffic-percentage schedule and an automated (not manually-watched)
   promotion/rollback trigger tied to the model-behavior SLO.
6. evaluation discipline — the online decision rule now requires a
   stated minimum comparison-window/sample-size floor before it fires.
7. Model Tests — offline metric thresholds now measured against a
   pinned prior run/model-version identifier, never an undefined
   "baseline."

canonical: `cd /tmp/claude-1000/b171/ml-engineering-rulebook && git diff main issue-1199/ml-engineering --stat`, run this session:
```
 docs/specs/record-norms.md          | 46 ++++++++++++++++++++++++++++--------
 ml-engineering/hooks/directive.sh   | 14 ++++++-----
 2 files changed, 47 insertions(+), 13 deletions(-)
```
Both named upgrade files were actually edited, committed (subject:
issue-1199), pushed, and opened as a PR in that repo:
commit 3d996d5, https://github.com/tokenmaxxxer/ml-engineering-rulebook/pull/23.

Note on scope: this issue's deliverable is a doctrine fold-in — WRITE_SCOPE
is [] and no model, service, or dataset is under review in this record.
The mechanical phase-2 record gates apply unconditionally to this file
path regardless of subject matter, so the sections below are filled with
an explicit not-applicable note for each element rather than left out.

## Serving design

### Serving Pattern
Not applicable — this record reviews no batch, online-serving, or
streaming system; the fold-in target is the serving-design doctrine
text itself, not a deployed service.

### Service SLO
Not applicable — no latency/availability/throughput target is being
set for any service in this record.

### Model-Behavior SLO
Not applicable — no drift threshold or prediction quality target is
being tracked in this record.

### Rollout
Not applicable — no staged/canary/promotion rollout is occurring; the
doctrine change itself was delivered as a single reviewed PR, not a
staged rollout.

### Rollback
Not applicable — no deployment occurred, so no rollback conditions
apply.

## ML Test Score

### Data Tests
score: N/A — no dataset is under review in this doctrine fold-in.

### Model Tests
score: N/A — no model artifact is under review in this doctrine
fold-in.

### ML Infrastructure Tests
score: N/A — no training/serving infrastructure is under review; this
record's own infrastructure is a doctrine-text diff, verified by
`git diff --stat` above.

### Monitoring Tests
score: N/A — no production monitoring is under review in this
doctrine fold-in.

## model provenance

### model_id
Not applicable — no model artifact/registry reference exists for this
doctrine-only record.

### intended use
Not applicable — this record's content is a doctrine edit, not a
deployed model with an intended use.

### limitations
Not applicable — no model limitations apply; the record's own
limitation is scope: doctrine text only, per WRITE_SCOPE: [].

### training data
Not applicable — no training data is used or reviewed in this record.

### evaluation data
Not applicable — no eval_data is used or reviewed in this record.

### Verdict
canonical: `git -C /tmp/claude-1000/b171/ml-engineering-rulebook log --oneline -1 issue-1199/ml-engineering` — result: `3d996d5 issue-1199: fold ML tool-landscape learnings into ml-engineering doctrine`, run this session, confirming the commit is present on the pushed branch backing PR #23.
pass — the fold-in matches the approved proposal's seven items 1:1 and
both named target files were edited in the same delivery.

data version: not applicable (dataset version N/A — no dataset here).
model version: not applicable (model version N/A — no model here).

## evaluation discipline

### offline evaluation
Not applicable — no metric, holdout, or backtest dataset exists for
this doctrine-only record; there is no offline evaluation to report.

### online evaluation
Not applicable — no A/B, shadow, or canary comparison exists for this
doctrine-only record; there is no online evaluation to report.

## Why
Per the scout brief (docs/issue-1199/reports/ml-engineering/scout-brief.md),
each of the seven items above is a design move the field's
highest-adoption tool in its category structurally enforces (MLflow's
atomic run identifier binding code+data+config; DVC's content-hash
versioning; Great Expectations' per-field named expectations;
Evidently's drift-type taxonomy; Feast's point-in-time feature
consistency feeding train/serve-skew detection; KServe/BentoML's
canary traffic-percentage schedules with automated triggers; Weights
& Biases' baseline-pinned run comparison) that the doctrine text did
not yet ask for. Folding these in as the role's own native rules (no
tool-attribution catalog) raises what this role's own PRODUCES bar
already demands, per issue #1199's requirement 4: each fold-in
upgrades a specific existing doctrine item rather than adding new
gated sections, so the mechanical shape checks in the five owning
plugins are unaffected — only the doctrine's specificity changed.

## Upstream basis
- docs/issue-1199/proposals/2026-08-13-ml-engineering-tool-landscape.md
- docs/issue-1199/reports/ml-engineering/current-state-survey.md
- docs/issue-1199/reports/ml-engineering/scout-brief.md
- northpole req#1 (docs/specs/northpole.md)

## Open findings
None — the seven-item fold-in matches the proposal 1:1 and both named
files were edited in the same delivery.

amendments-reconciled: issuecomment-5282629810 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)", posted 2026-08-13T15:40:25Z)
read this session. canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5282629810 -q .body`,
run this session. The comment names no PR number ("PR #?") and no
role, so it does not identify this ml-engineering delivery as its
target; nothing in this record changes in response.

amendments-reconciled: issuecomment-5282638668 (same template, "Verdict:
PR #? → escalate (depth or impact axis did not clear)", posted
2026-08-13T15:40:57Z) read this session. canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5282638668 -q .body`,
run this session. Same generic no-PR-number, no-role shape as the prior
entry; does not identify this delivery as its target; nothing in this
record changes.

amendments-reconciled: issuecomment-5282629474, issuecomment-5282638385,
issuecomment-5282648208 (three "Judgment opened: PR #? — candidate
decision on branch `issue-1199/ml-engineering` (4 path(s) changed)
entered delegated-judgment evaluation." comments, posted
2026-08-13T15:40:23Z / 15:40:56Z / 15:41:28Z) and issuecomment-5282648559
(fourth "Verdict: PR #? → escalate (depth or impact axis did not
clear)", posted 2026-08-13T15:41:29Z) read this session. canonical:
`gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments --paginate
-q '.[] | select(.created_at > "2026-08-13T15:30:00Z") | [.id,
.created_at, .body] | @tsv'`, run this session. All are an automated
watcher's per-push judgment/verdict pair reacting to this branch's own
commit pushes so far — each names no concrete PR number and no
role-specific finding beyond the generic escalate template; none
identifies a defect in this delivery's content, so nothing in this
record changes in response. This branch's commits stop after this one;
no further push-triggered pairs are expected from this delivery.
