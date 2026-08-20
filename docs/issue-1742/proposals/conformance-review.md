---
status: proposed
files:
  - docs/issue-1742/reports/conformance-review.md
---

## Request

Issue #1742 conformance review (board condition per role spec, issue
#521): commit df7046f7 landed the phase-2 delivery for spawn.py
`--skills` additive mount, and no conformance-review record exists yet
for that sha. This role's job is a per-requirement verdict
(Present|Surface|Absent|Incorrect|Unverifiable) against the issue's own
Acceptance section — never a holistic quality judgment, never a fix.

## Requirement list (phase-1 output; see
docs/issue-1742/reports/conformance-review/survey.md for the full
derivation and canonical citations)

1. `--skills a,b` mounts named skills additively; no-flag path stays
   argv/env-byte-identical, verified by a case in
   `test/test_spawn_skills_mount.py` that the issue text specifies
   should diff against "the pre-change fixture."
2. Unknown skill name → non-zero exit before any workspace/branch
   creation, verified by an unknown-name case in the same test file.
3. Roster entry + co-injected directive carry skill list + skill-repo
   SHA when `--skills` is used, verified by a record-fields case in the
   same test file.

## Plan for phase 2

Once approved, phase 2 renders one verdict per requirement above,
working from `spawn.py`/`test/test_spawn_skills_mount.py` at df7046f7
and the issue's Acceptance text — deliberately without the
implementation session's stated intent (its `docs/issue-1742/reports/implementation.md`
and `docs/issue-1742/reports/implementation/survey.md`). The survey
already surfaced two candidate divergences (fixture-diff substitution
for requirement 1; inline-reimplementation instead of calling
production code for requirement 3) to weigh into those verdicts, not
pre-decide them.

## Constraints

- Record file lands only after human Approve (contract v3 s19); this
  proposal and the survey are the only phase-1 writes.
- Findings, if any, are addressed to the implementation role (issue
  #1742's owning role) — this role never edits spawn.py or the test
  file.
