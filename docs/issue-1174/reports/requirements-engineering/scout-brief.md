# Scout brief — issue #1174 step 1

mode: batched-sequential (single session, sequential `gh api`/`gh issue`
calls — no parallel dispatch available for this repo-survey shape)
stage count: 2 rounds total — round 1 sweep covered rulebook layout and
spec-pointer convention; round 2 was a focused read of the gate scope
inside ux-engineering-rulebook.
canonical: gh api calls and file reads listed below, all issued this
turn.

## Current state (survey, run before sweep)

- roles/*.json = 43 role manifests.
  derived: `ls roles/*.json | xargs -n1 basename | wc -l`
  canonical: shell output of the above command, this turn.
- roles/specs/<role>.spec.json already carries per-field methodology
  pointers (source_standard, finding_method, anti_pattern) but no field
  pointing at operational decision-rule content.
  canonical: full read of roles/specs/requirements-engineering.spec.json,
  this turn — no playbook or rulebook_section key present in that file.
- No role's rulebook repo yet carries an operational-content directory
  matching the "playbook" shape this issue asks for; the operator's own
  example domain (tokenmaxxxer/ux-engineering-rulebook) has none either.
  canonical: `gh api repos/tokenmaxxxer/ux-engineering-rulebook/contents/docs`
  and `gh api repos/tokenmaxxxer/ux-engineering-rulebook/contents/ux-engineering`,
  both this turn — neither listing contains a playbook entry.
- consult-log 2026-08-13T04:36:27 (role=requirements-engineering,
  issue=none) already ruled on two of the five design questions this
  step owns: landing location is the rulebook (not spec — spec stays
  verification layer), and depth-gate anti-shallowness = "소스 강제 인용 +
  반례 테스트 통과를 완성 단위로 삼는 것".
  canonical: docs/reports/consult-log.md line 17, read this turn.
  This proposal treats that consult as binding and builds the concrete
  script/threshold spec on top of it.

## Sweep: tokenmaxxxer/ux-engineering-rulebook layout (operator-named exemplar)

Sources:
- https://github.com/tokenmaxxxer/ux-engineering-rulebook (repo root, via `gh api .../contents`)
- https://github.com/tokenmaxxxer/ux-engineering-rulebook/blob/main/README.md

Findings (canonical: gh api contents listing + README.md read, both this turn):
- Top level = one dir per methodology gate plugin
  (ux-phase1-structure-gate/, ux-migration-handoff/, ux-token-schema/,
  ux-wcag-onpair/), each holding .claude-plugin/hooks/tests — these are
  enforcement plugins, not content.
- docs/ holds the repo's own on-the-record-style tree: docs/handbooks/,
  docs/specs/ (approvers.md, proposal-and-deliverable-norms.md,
  record-fields-terminal-states.json), and per-issue docs/issue-<n>/
  dirs (1, 2, 7, 10, 13, 16, 20) — this repo already runs the same
  role-handoff contract v3 the parent repo does, phase-1/phase-2 and
  all.
- README's "Layout" section is the authoritative index of what each
  top-level dir is for — any new content dir this proposal adds needs a
  matching README entry (adopt pattern: self-documenting layout list).
- No dir currently holds practitioner decision content — every existing
  plugin gates *shape* (Double Diamond structure, WCAG contrast math,
  DTCG token shape), never the domain knowledge itself. This is the gap
  the issue names: gates exist, content doesn't.

## Gap line

Field already met: phase-1/phase-2 proposal discipline, per-issue docs
tree, gate-lib.sh convention, README-as-layout-index — all reusable
as-is for a new content directory.
Missing: any operational-content directory, any shape-gate that counts
decision rules (existing gates check structure/format, not rule density
or condition-choice-source shape), any spec-to-content pointer field.

## Judge point

Would another sweep round change a build decision here? No — the
question was what a real rulebook repo looks like today, and one
authoritative example (the operator-named one) plus the parent repo's
own docs/specs/ convention (mirrored 1:1 inside the rulebook already)
settles the landing structure and pointer shape. Stopped after the two
rounds above.
