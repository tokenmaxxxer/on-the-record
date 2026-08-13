---
status: proposed
files:
  - docs/issue-1199/reports/ml-engineering/current-state-survey.md
  - docs/issue-1199/reports/ml-engineering/scout-brief.md
  - docs/issue-1199/reports/ml-engineering.md
---

# Proposal: ml-engineering tool-landscape fold-in (issue-1199)

## Intent
For the `ml-engineering` role, survey the tool ecosystem ML engineers
actually use, analyze what each tool solves and how, and fold the
distilled design moves into the role's own rulebook doctrine — not as
a tool catalog, but as native upgrades to the existing PRODUCES
doctrine (`ml-engineering/hooks/directive.sh`) and its doctrine detail
file (`docs/specs/record-norms.md`). See
`docs/issue-1199/reports/ml-engineering/current-state-survey.md` and
`docs/issue-1199/reports/ml-engineering/scout-brief.md` for the survey
and sweep this proposal is built on.

## Context
Per the survey: the rulebook's directive already requires all four ML
Test Score rubric sections (Breck et al. 2017), a model card, paired
data/model version identifiers, and split offline/online evaluation.
The doctrine detail file (`docs/specs/record-norms.md`) is out of sync
with that shape — it still names an older two-field PRODUCES. Per the
scout brief: seven concrete gaps exist between the doctrine's current
language and the design moves the surveyed field's highest-adoption
tools (MLflow 27,496 stars, DVC 15,814 stars, BentoML 8,784 stars,
Great Expectations 11,709 stars, Weights & Biases 11,231 stars, Feast
7,207 stars, Evidently 7,800 stars, KServe 5,787 stars — all counts
per `gh api repos/<org>/<repo>`, fetched this session) structurally
embody.

## Decision
Fold seven native rule upgrades into the two doctrine files, and bring
`docs/specs/record-norms.md` back in sync with `directive.sh`'s current
four-component shape while doing so:

1. **Data Tests** — require expectations named per field (not one
   blanket verdict for the section).
2. **Monitoring Tests** — require the drift taxonomy split into input/
   feature drift, prediction drift, and label/concept drift, each with
   its own statistic and threshold.
3. **ML Infrastructure Tests** — require training reproducibility to
   name one traceable run identifier binding code version + data
   version + config together.
4. **model provenance** — require the data/model version identifiers to
   be content-derived (hash-based), not a mutable label.
5. **serving design** — require rollout stages to name a concrete
   traffic-percentage schedule and an automated (not manual)
   promotion/rollback trigger tied to the model-behavior SLO.
6. **eval discipline** — require the online decision rule to state a
   minimum comparison-window/sample-size floor before promote/rollback.
7. **Model Tests** — require the offline-threshold baseline to be a
   pinned prior run/model version identifier, not an undefined
   "baseline."

## Rationale
Per the scout brief's Gap line: each item above is a design move the
highest-adoption tool in its category structurally enforces (atomic
run identifiers binding code+data+config: MLflow; content-hash
versioning: DVC; named per-field expectations: Great Expectations;
drift-type taxonomy: Evidently; point-in-time feature consistency
feeding train/serve-skew detection: Feast; canary traffic-percentage
schedules with automated triggers: KServe/BentoML; baseline-pinned run
comparison: Weights & Biases) that the rulebook's current doctrine text
does not yet ask for. Rejected alternative: a standalone
`tool-learnings/` doc (see survey's Alternatives-considered section) —
rejected because it would fork the doctrine source of truth the
existing two files already own, and the issue explicitly prohibits a
tool-catalog section in the public rulebook.

## Consequences
Both `ml-engineering/hooks/directive.sh`'s PRODUCES text and
`docs/specs/record-norms.md`'s Phase 2 section gain sharper, more
specific bars — none of the five methodology-gate plugins' shape
checks (section presence + word-boundary verdict marker) change, since
the seven upgrades are doctrine-level specificity, not new gated
sections. No tool name or "learned from X" attribution appears in
either file; each upgrade is stated as the role's own methodology norm.

## Constraints
- Adoption evidence only (stars/downloads/multi-source), no pretrained-
  recall tool lists — see the scout brief.
- Bounded fold-in: distilled design moves, not a tool catalog; no
  verbatim copying from any surveyed tool's docs.
- Every named upgrade target file must actually be edited.
- Work happens in the separate `tokenmaxxxer/ml-engineering-rulebook`
  repo (mounted at /tmp/claude-1000/b171/ml-engineering-rulebook); this
  repo (on-the-record) carries only the phase-1/phase-2 records.

## What will be done
Edit, in `tokenmaxxxer/ml-engineering-rulebook` on branch
`issue-1199/ml-engineering`:
- `ml-engineering/hooks/directive.sh` — PRODUCES text, all seven items
  above folded into their existing bullets.
- `docs/specs/record-norms.md` — rewritten Phase 2 section matching the
  current four-component shape, carrying the same seven items as
  concrete "how" bars.

Then commit (subject: issue-1199), push to origin, open a PR in that
repo, and write this repo's phase-2 record at
`docs/issue-1199/reports/ml-engineering.md` citing that PR/commit.

## Alternatives considered
See the survey's Alternatives-considered section: a separate
`tool-learnings/` doc was considered and rejected in favor of folding
directly into the two existing doctrine files.

## Open questions
See the survey's Open-questions section: the issue's shape-gate
extension is left to the issue's step-1 implementation unit, not this
per-role unit.

## Out of scope
MLflow's/W&B's SaaS dashboard and UI features; Great Expectations'/
Evidently's own execution engines; Feast's/DVC's storage-backend
mechanics; KServe's/BentoML's Kubernetes deployment mechanics — all out
of `WRITE_SCOPE: []` (report-only role, no pipeline/deployment code).

## How you will know it worked
The rulebook PR's diff shows the seven doctrine edits landed across the
two named files; this repo's phase-2 record cites the rulebook-repo
commit sha and PR URL as canonical sources.
