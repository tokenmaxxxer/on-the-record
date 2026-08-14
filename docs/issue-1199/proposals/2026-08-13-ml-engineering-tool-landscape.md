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

## REWORK (2026-08-14 operator amendment): survey target corrected to the Claude Code plugin/skill ecosystem

The operator's 2026-08-14 comment on issue #1199 corrected this
program's survey target: for every role, survey the most-adopted
CLAUDE CODE PLUGINS/SKILLS relevant to that role's domain — not
general domain tooling. The seven-item fold-in above (surveyed against
MLflow/DVC/Great Expectations/etc, a general ML tooling survey) already
landed on `issue-1199/ml-engineering` in the rulebook repo (commit
3d996d5, PR tokenmaxxxer/ml-engineering-rulebook#23) and stays landed —
it is native, sourceless doctrine text, so it does not conflict with
the corrected target; only the survey basis for further upgrades
changes going forward. This REWORK section is the record of that
correction and the additional fold-in it produces.

### Corrected survey
See `docs/issue-1199/reports/ml-engineering/scout-brief.md` (rewritten
this round): four Claude Code plugins/skills surveyed with adoption
evidence — alirezarezvani/claude-skills (24,380 stars),
jeremylongshore/claude-code-plugins-plus-skills (2,630 stars, its
`ai-ml/model-evaluation-suite` skill), rohitg00/awesome-claude-code-toolkit
(2,499 stars, its `mlops-engineer` agent), probabl-ai/skills (97 stars,
its data-science pipeline/iteration-loop skill groups).

### Additional decision (three upgrades, on top of the seven already landed)
1. **serving design / promotion criteria** — require the promotion
   trigger to name its own numeric minimum-improvement threshold (not
   just the existence of an automated trigger condition).
2. **serving design / rollback** — require rollback to carry a stated
   time-bound recovery target, and require the record to state that
   the rollback procedure and serving-endpoint/monitoring-dashboard
   correctness are items a completion checklist verifies, not items a
   design section merely describes.
3. **ML Test Score / Model Tests** — require the staleness/degradation
   check to be run against an explicitly later-in-time held-out data
   slice, not a generic staleness-tolerance number with no time
   boundary named.

### Rationale
Per the scout brief's Gap line: the rulebook's landed doctrine already
requires a traffic-percentage rollout schedule, an automated trigger,
and a pinned-baseline offline threshold, but does not yet require the
trigger's own numeric bar, a time-bound rollback target verified by a
completion checklist, or a time-boundaried staleness check — the three
gaps the surveyed plugins/skills' design moves (a named numeric
promotion bar and a checklist-verified rollback time target; a
distinct stress-test-on-future-data step) structurally embody.

### What will be done (REWORK)
Edit, in `tokenmaxxxer/ml-engineering-rulebook` on branch
`issue-1199/ml-engineering` (same branch, new commit on top of
3d996d5):
- `ml-engineering/hooks/directive.sh` — fold the three items above into
  the existing serving-design and Model-Tests bullets natively (no
  tool name, no "learned from X" framing — evidence trail stays only
  in this repo's `docs/issue-1199/reports/ml-engineering/scout-brief.md`
  and `.md` record).
- `docs/specs/record-norms.md` — same three items folded into the
  matching Phase 2 subsections.

Then commit (subject: issue-1199), push to origin, and update the
existing rulebook-repo PR #23 and this repo's phase-2 record
(`docs/issue-1199/reports/ml-engineering.md`) to cite the new commit.

### Constraints (unchanged)
- No verbatim copying from any surveyed plugin/skill's own text.
- No tool-attribution framing in the rulebook files themselves — the
  evidence trail (which plugins, adoption counts, per-insight mapping)
  lives only in this repo's issue-side records.
- Every named upgrade target file must actually be edited in the same
  delivery as this proposal (per the 2026-08-13 apply-not-reference
  amendment, still binding).
