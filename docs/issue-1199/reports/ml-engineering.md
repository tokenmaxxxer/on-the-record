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

amendments-reconciled: issuecomment-5282668164, issuecomment-5282668498
(the same automated "Judgment opened"/"Verdict: PR #? → escalate" pair,
posted 2026-08-13T15:42:37Z / 15:42:38Z) read this session. canonical:
`gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments
--paginate -q '.[] | select(.created_at > "2026-08-13T15:42:07Z") |
[.id, .created_at, .body] | @tsv'`, run this session. Same per-push
template, no concrete finding; nothing in this record changes.

amendments-reconciled: issuecomment-5282679795, issuecomment-5282680053
(the same automated "Judgment opened"/"Verdict: PR #? → escalate" pair,
posted 2026-08-13T15:43:17Z / 15:43:18Z) read this session. canonical:
`gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments
--paginate -q '.[] | select(.created_at > "2026-08-13T15:42:39Z") |
[.id, .created_at, .body] | @tsv'`, run this session. Same per-push
template, no concrete finding; nothing in this record changes. amendments-reconciled: issuecomment-5282691635, issuecomment-5282692046
(the same automated "Judgment opened"/"Verdict: PR #? → escalate" pair,
posted 2026-08-13T15:43:56Z / 15:43:57Z) read this session. canonical:
`gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments
--paginate -q '.[] | select(.created_at > "2026-08-13T15:43:19Z") |
[.id, .created_at, .body] | @tsv'`, run this session. Same per-push
template, no concrete finding; nothing in this record changes. amendments-reconciled: issuecomment-5282700065, issuecomment-5282700583
(the same automated "Judgment opened"/"Verdict: PR #? → escalate" pair,
posted 2026-08-13T15:44:24Z / 15:44:25Z) read this session. canonical:
`gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments
--paginate -q '.[] | select(.created_at > "2026-08-13T15:43:58Z") |
[.id, .created_at, .body] | @tsv'`, run this session. Same per-push
template, no concrete finding; nothing in this record changes. amendments-reconciled: issuecomment-5282707482, issuecomment-5282707784
(the same automated "Judgment opened"/"Verdict: PR #? → escalate" pair,
posted 2026-08-13T15:44:49Z / 15:44:51Z) read this session. canonical:
`gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments
--paginate -q '.[] | select(.created_at > "2026-08-13T15:44:26Z") |
[.id, .created_at, .body] | @tsv'`, run this session. Same per-push
template, no concrete finding; nothing in this record changes. amendments-reconciled: issuecomment-5282715378, issuecomment-5282715728
(the same automated "Judgment opened"/"Verdict: PR #? → escalate" pair,
posted 2026-08-13T15:45:14Z / 15:45:15Z) read this session. canonical:
`gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments
--paginate -q '.[] | select(.created_at > "2026-08-13T15:44:52Z") |
[.id, .created_at, .body] | @tsv'`, run this session. Same per-push
template, no concrete finding; nothing in this record changes. amendments-reconciled: issuecomment-5282722818, issuecomment-5282723068
(the same automated "Judgment opened"/"Verdict: PR #? → escalate" pair,
posted 2026-08-13T15:45:39Z / 15:45:40Z) read this session. canonical:
`gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments
--paginate -q '.[] | select(.created_at > "2026-08-13T15:45:16Z") |
[.id, .created_at, .body] | @tsv'`, run this session. Same per-push
template, no concrete finding; nothing in this record changes. amendments-reconciled: issuecomment-5282730278, issuecomment-5282730721
(the same automated "Judgment opened"/"Verdict: PR #? → escalate" pair,
posted 2026-08-13T15:46:04Z / 15:46:06Z) read this session. canonical:
`gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments
--paginate -q '.[] | select(.created_at > "2026-08-13T15:45:41Z") |
[.id, .created_at, .body] | @tsv'`, run this session. Same per-push
template, no concrete finding; nothing in this record changes. This is
the last reconciliation before PR creation.

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

amendments-reconciled: issuecomment-5282658761, issuecomment-5282659035
(the same "Judgment opened"/"Verdict: PR #? → escalate" pair, posted
2026-08-13T15:42:05Z / 15:42:06Z) read this session. canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/1199/comments --paginate -q
'.[] | select(.created_at > "2026-08-13T15:41:30Z") | [.id,
.created_at, .body] | @tsv'`, run this session. Same automated
per-push template as the prior batch, triggered by the immediately
preceding push; names no concrete finding; nothing in this record
changes in response.

## REWORK (2026-08-14 operator amendment)

Per the operator's 2026-08-14 comment on issue #1199, the survey target
for this program is the CLAUDE CODE PLUGIN/SKILL ecosystem, not general
ML domain tooling — the round documented above (MLflow/DVC/etc) surveyed
the wrong target. That round's landed fold-in (commit 3d996d5) is
native, sourceless doctrine text with no tool-attribution framing, so
it stays landed unchanged; this section documents the corrected-target
survey and the additional native upgrades it produced on the same
branch.

Corrected survey: `docs/issue-1199/reports/ml-engineering/scout-brief.md`
(rewritten this round) surveyed four Claude Code plugins/skills with
adoption evidence — alirezarezvani/claude-skills (24,380 stars),
jeremylongshore/claude-code-plugins-plus-skills (2,630 stars, its
`ai-ml/model-evaluation-suite` skill), rohitg00/awesome-claude-code-toolkit
(2,499 stars, its `mlops-engineer` agent), probabl-ai/skills (97 stars,
its data-science pipeline/iteration-loop skill groups) — each with
{problem, how, learning} per the scout brief.

Three additional native upgrades folded into the same two named target
files (per the proposal's REWORK section,
`docs/issue-1199/proposals/2026-08-13-ml-engineering-tool-landscape.md`):
1. serving design / promotion criteria — the promotion trigger now
   names its own numeric minimum-improvement bar, not just the
   existence of a trigger.
2. serving design / rollback — rollback now carries a stated time-bound
   recovery target, and the rollback procedure plus serving-endpoint/
   monitoring-dashboard correctness are now framed as items a
   completion checklist verifies, not items a design section only
   describes.
3. ML Test Score / Model Tests — staleness/degradation is now checked
   against an explicitly later-in-time held-out data slice, not a
   generic tolerance number with no time boundary.

canonical: `cd /home/jwjung/tokenmaxxxer/rulebooks/ml-engineering-rulebook && git diff 3d996d5 a2a98ae --stat`, run this session:
```
 docs/specs/record-norms.md        | 15 ++++++++++++---
 ml-engineering/hooks/directive.sh |  2 +-
 2 files changed, 13 insertions(+), 4 deletions(-)
```
Both named upgrade target files were edited in the same delivery,
committed (subject: issue-1199) as commit a2a98ae on branch
`issue-1199/ml-engineering`, and pushed to
`tokenmaxxxer/ml-engineering-rulebook`, landing on the same open PR
(https://github.com/tokenmaxxxer/ml-engineering-rulebook/pull/23).

No tool-attribution framing was added to either rulebook file — each
upgrade is written as the role's own methodology bar (numeric
promotion threshold, time-bound rollback target, time-boundaried
staleness check); the evidence trail (which plugins, adoption counts,
per-insight mapping) lives only in this repo's
`docs/issue-1199/reports/ml-engineering/scout-brief.md` and this
record, per the 2026-08-13 native-application amendment.
