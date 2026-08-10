# issue-685 — scout brief

Mode: 1 sweep stage, single WebSearch query (batched-sequential fallback —
only one angle was decision-relevant: how existing CI systems already
solve "gate on whether a diff touches UI paths"; this repo's own
provenance/glob conventions, covered in survey.md, are the second input
and needed no web search). Stages used: 1 sweep + 1 judge point, well
under the 5-stage/3min budget — saturated immediately: the field's answer
converges on one mechanism.

## Category must-be

- Path-glob diff filtering is the standard mechanism for "does this
  change touch surface X" gates (dorny/paths-filter, tj-actions/changed-
  files, GitHub's own `paths:`/`paths-ignore:` workflow triggers) — every
  serious implementation matches changed file paths against declared glob
  patterns, not file extensions alone or heuristic content sniffing.

## Performance axes the field competes on

1. Declaration ergonomics — glob syntax richness (globstar, brace
   expansion, negation).
2. Default behavior when no filter matches — the field's tools default
   *permissive* (no match = the gated job simply doesn't run; there is no
   "unknown, block" state in paths-filter/changed-files).
3. Output granularity (boolean flag vs. list of matched files) for
   downstream messaging.

## Adopt / skip

- Adopt: glob-pattern path matching as the detection primitive (matches
  this repo's own `write_scope` convention in `roles/*.json` already —
  no new mechanism class introduced).
- Skip (deliberate divergence): the field's permissive default. This
  repo's existing gates (`acceptance_gate.py`'s "검사 불가는 통과가
  아니다" / fail-closed-on-unreadable stance, `record_enums`'s "역할
  정의를 못 읽으면... 차단한다") already establish fail-closed as house
  style for missing declarations — issue #685's body explicitly asks for
  this ("fail-closed to 'UI-facing' when undeclared but screen-like paths
  change"), which is the opposite of paths-filter's silent-skip default.
  Adopting the field's default here would contradict both the issue text
  and this repo's own established gate philosophy.

## Gap line

This repo already has the glob-declaration mechanism (`write_scope` in
`roles/*.json`) and the fail-closed philosophy (multiple existing gates).
What is missing, and what this proposal must add, is (1) a target-repo-
facing declaration point for *UI* globs specifically (not write-scope,
which is agent-permission-shaped, not surface-classification-shaped), and
(2) the actual diff-classification + provenance-requirement check itself
— no existing gate does either.

Sources:
- https://github.com/dorny/paths-filter
- https://github.com/tj-actions/changed-files
