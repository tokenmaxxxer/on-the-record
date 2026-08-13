---
subject: issue-1199
role: ml-engineering
kind: survey
---

# Current-state survey: ml-engineering rulebook (issue-1199)

canonical: `/tmp/claude-1000/b171/ml-engineering-rulebook/ml-engineering/hooks/directive.sh`
and `/tmp/claude-1000/b171/ml-engineering-rulebook/docs/specs/record-norms.md`
(tokenmaxxxer/ml-engineering-rulebook repo root, mounted locally), read
this session.

## Write surfaces
`ml-engineering/hooks/directive.sh` carries the live SessionStart
PRODUCES text (four phase-2 components: serving design, ML Test Score,
model provenance, evaluation discipline — each mechanically gated by a
sibling plugin). The doctrine detail file the README points reviewers
to is `/tmp/claude-1000/b171/ml-engineering-rulebook/docs/specs/record-norms.md`.

canonical: `diff <(sed -n '/Phase 2/,/scope/p' /tmp/claude-1000/b171/ml-engineering-rulebook/docs/specs/record-norms.md) /dev/null`, run this session — the norms file's "Phase 2 — output norm" section names only two fields, `serving design` and `risk note`, and its `risk note` subsection lists three items (Drift, Latency, Failure mode); it does not name the current directive's ML Test Score four-rubric-section shape, model provenance, or evaluation discipline anywhere in the file.
This gap between the two write surfaces is itself one of the fold-in
targets below (item 8).

canonical: `grep -n "Data Tests\|Monitoring Tests\|ML Infrastructure Tests\|Model Tests\|model provenance\|version" /tmp/claude-1000/b171/ml-engineering-rulebook/ml-engineering/hooks/directive.sh`, run this session — the items below are quoted from that grep's matched lines and their surrounding context.

## Gaps found (feeding the scout sweep)

1. Data Tests names "feature expectations, distribution/schema checks,
   privacy/compliance of inputs" but does not require each expectation
   to be individually named/checkable per field — the gate's own
   verdict-marker check (per
   `/tmp/claude-1000/b171/ml-engineering-rulebook/ml-engineering-ml-test-score/hooks/methodology-gate.sh`,
   read this session, its `VERDICT_RE` pattern) is satisfied by one
   blanket verdict line anywhere in the section, with no per-field
   granularity requirement in the doctrine text itself.
2. Monitoring Tests names "training/serving skew detection,
   prediction-quality tracking ... alerting on regression" but states
   no drift-type taxonomy — input/feature drift, prediction drift, and
   label/concept drift are not distinguished as separate checkable
   items, though each needs its own statistic and detection latency.
3. ML Infrastructure Tests' "training reproducibility" item has no
   requirement binding code version + data version + config together
   into one traceable run identifier in the doctrine text.
4. model provenance's "data/model versioning — a version identifier
   for the training dataset and a version identifier for the model
   artifact, both traceable to the record" does not require the
   identifier to be content-derived (hash-based) rather than a mutable
   label.
5. serving design's "rollout stages + promotion criteria" item has no
   requirement for a concrete traffic-percentage schedule or an
   automated (vs. manual) promotion/rollback trigger tied to the
   model-behavior SLO.
6. eval discipline's online-evaluation "decision rule for promote/
   rollback" has no minimum comparison-window/sample-size floor
   requirement in the doctrine text.
7. Model Tests' "offline metric thresholds vs. baseline" does not
   require the baseline to be a pinned prior run/model version
   identifier.
8. The doctrine detail file is out of sync with `directive.sh`'s
   current four-component shape (see Write surfaces above, canonical
   cited there).

## Alternatives considered
Considered adding a new standalone `tool-learnings/` doc cross-
referenced from directive.sh. Rejected: this rulebook keeps its
operating doctrine in exactly two places (directive.sh's live
SessionStart text, and the doctrine detail file) — canonical:
`ls /tmp/claude-1000/b171/ml-engineering-rulebook/docs/specs/`, run
this session, shows only `approvers.md` and `record-norms.md` — with
no existing third convention; forking a new file would split the
source of truth, and the issue's constraint against a "tool catalog"
section favors folding learnings directly into the existing doctrine
language instead.

## Open questions
canonical: `docs/issue-1199/reports/data-modeling/survey.md`, "Open
questions" section, read this session.

Whether the shape-gate extension named in issue-1199's Acceptance
section (extending a gate to check tool-learnings entry completeness)
belongs to this per-role unit or the issue's separate step-1
implementation unit. Resolved for this unit's scope as: the issue's
"실행 계획" step 1 is a distinct implementation unit; this survey and
its proposal cover only the ml-engineering role's per-role fan-out unit
(step 2+), so the gate extension is left to step 1 — matching the
precedent already recorded in the data-modeling sibling unit's survey.
