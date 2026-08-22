---
status: proposed
files:
  - scripts/measure_skill_reflection.py
  - gates/test_measure_skill_reflection.py
  - docs/specs/guidance-reflection-rubric.md
  - docs/issue-1991/reports/implementation/survey.md
  - docs/issue-1991/proposals/guidance-reflection-rubric-and-multi-judge-scoring.md
---

## Request

Build a companion measurement to `scripts/measure_skill_invocation.py`
(issue #1960 lineage) that scores, per completed role session, whether
the session's deliverable/record actually reflects the rules of each
skill mounted for it — not merely whether the skill was invoked. Score
via multiple independent judge calls with distinct lenses (builder-blind,
addressing self-grading-bias per the 2026-08-22
requirements-engineering consult), taking a majority verdict per skill,
each row in the shape `{skill, reflected: yes/no/partial, evidence}`.
The rubric that defines "reflected" must exist as a documented artifact,
written before any judge call runs against it. A session with zero
mounted skills produces an explicit not-applicable row rather than
silently emitting nothing.

## Constraints

- Acceptance names the exact invocation:
  `python3 scripts/measure_skill_reflection.py <session-log-or-record-paths>`
  — must accept one or more explicit paths as argv, mirroring
  `measure_skill_invocation.py`'s calling convention (survey, lineage
  section).
- Must produce "the per-session reflection table for a fixture session"
  — a fixture session-log/record is required in the test tree so the
  script's live output is checkable without a real role session.
- The multi-judge majority mechanism must be asserted by test, with
  judges mockable — the judge-call boundary cannot be a hard-wired live
  subprocess (survey: `spawn.py consult` is expensive,
  non-deterministic per call).
- Rubric-first: the rubric must be a separate, stable, documented
  artifact — not inlined ad hoc inside the script or invented per
  judge prompt.
- Empty-state rule: zero mounted skills → one explicit not-applicable
  row, never an empty/silent skip (mirrors
  `measure_skill_invocation.py`'s "every input produces exactly one
  output row" discipline, survey confirms this is already the sibling
  script's own norm).
- Acceptance's `provenance: executed-live` — the check must be run live
  against the fixture in this session's own phase-2 record, not just
  claimed.
- Operational-surface commit gate: this change touches only scripts/
  gates/docs — no package manifest, CI config, or deploy script — so
  the operational-surface-plus-handbook commit restriction does not
  apply.

## Rationale

**Where the rubric document lives.** Considered inlining the rubric as
a docstring/constant inside `measure_skill_reflection.py` itself,
versus a separate file under
`docs/specs/`. Rejected inlining: the issue's "rubric-first" framing
(2026-08-22 consult) treats the rubric as the thing judges are graded
*against*, which the test suite must be able to cite and freeze
independently of script internals; a docstring can't be diffed or
referenced by `docs/specs/reconciled-index.md` machinery the way a
`docs/specs/*` file can, and any future change to the rubric's wording
becomes a code diff instead of a spec diff. Chose a standalone
`docs/specs/guidance-reflection-rubric.md`, which also means any commit
touching it must regenerate `docs/specs/reconciled-index.md` per the
existing spec-index-preflight gate — an explicit, already-enforced
discipline for keeping the rubric from drifting out of the index.

**Judge substrate: reuse `spawn.py consult` vs. build a standalone
judge.** Considered writing a self-contained judge (e.g. a second
direct model call inside the script, independent of `spawn.py`).
Rejected: `spawn.py consult` (survey: `consult_cmd`, line 5658) is
already the repo's one judgment-only, non-mutating call shape, already
traced to `docs/reports/consult-log.md`, and already used by
requirements-engineering/architecture roles for exactly this kind of
distinct-lens judgment call — duplicating that subprocess/logging
plumbing inside a new script would be pure repetition with no
behavioral gain, and would create two divergent consult-tracing
mechanisms in the same repo. Chose: default the judge-call seam to
shell to `spawn.py consult` (one call per lens), but keep that seam a
single swappable function/parameter so tests inject a mock judge
instead of shelling out — satisfying "judges mockable" without forking
the consult mechanism.

**Majority arithmetic: 2 vs. 3 judges, and tie handling.** Considered a
fixed 3-judge panel always. Rejected as the sole mode: 3 distinct lenses
per skill per session multiplies judge calls by mounted-skill count,
which is costly for a plain measurement script; also a 3-vote panel has
no tie to handle (odd N), which under-tests the majority function
itself. Chose: default panel size 3 (odd, matching the issue body's "2-3
consult calls... majority"), and the majority function accepts smaller
panel sizes too, treating an even split (only reachable at N=2) as
`partial` rather than crashing — so a 2-judge cost-saving mode stays
usable. The fixture test exercises both a clean 3-judge majority and
the 2-judge split case.

## What will be done

1. Draft `docs/specs/guidance-reflection-rubric.md`: defines the
   `reflected: yes/no/partial` categories with an evidence-citation
   requirement per verdict (what counts as "yes" — a specific
   deliverable/record passage that satisfies a specific skill rule;
   "no" — an identifiable rule violation or absence; "partial" — rule
   partially satisfied or judges split), and the not-applicable row
   shape for zero-mounted-skill sessions. Regenerate
   `docs/specs/reconciled-index.md` in the same commit
   (spec-index-preflight requirement).
2. Write `scripts/measure_skill_reflection.py`:
   - argv: one or more session-log-or-record paths (same convention as
     `measure_skill_invocation.py`).
   - Per path: reuse `measure_skill_invocation.py`'s mounted-skill
     extraction logic (either import it or duplicate its minimal JSONL
     scan — decided during implementation by which keeps the two
     scripts least coupled while avoiding drift) to get the mounted
     skill list and the session's deliverable/record content.
   - Zero mounted skills → emit one row: `{status: "not-applicable",
     reason: "no-mounted-skills"}` for that session — never nothing.
   - Non-zero mounted skills → for each skill, run the judge panel
     (default 3 calls, distinct lens prompts: e.g. "did the deliverable
     comply," "did the deliverable violate," "is the rule even
     triggered by this task") against the rubric + deliverable text,
     take the majority verdict, and emit
     `{skill, reflected, evidence, votes}`.
   - Judge-call function is a single named seam (e.g. `judge_fn`
     parameter, default wired to `spawn.py consult`) so tests pass a
     mock returning canned verdicts.
   - Output: one JSON line per session (per-session reflection table),
     matching the sibling script's one-row-per-input discipline.
3. Add a fixture session (a minimal JSONL log or record path under the
   test tree, matching the shape `measure_skill_invocation.py`'s own
   tests would expect) representing a session with mounted skills and
   one representing zero mounted skills.
4. Write `gates/test_measure_skill_reflection.py`: mocks the judge
   function, asserts (a) majority arithmetic over 3 mocked votes with a
   clear 2-1 split, (b) the 2-judge even-split → `partial` case, (c)
   the zero-mounted-skill fixture produces the explicit not-applicable
   row, (d) the per-session table shape matches `{skill, reflected,
   evidence}` per row.
5. Run `python3 scripts/measure_skill_reflection.py <fixture path>`
   live against the fixture and record its actual output in this
   issue's phase-2 implementation record (satisfies
   `provenance: executed-live`).

## Out of scope

- Wiring this script into any automated CI/gate pipeline, spawn.py, or
  the watchdog — the issue's Acceptance is the script producing correct
  output when run directly; automated scheduling is a separate,
  unrequested surface.
- Re-scoring or backfilling reflection data for any past/historical
  session logs — only the fixture and whatever session paths an
  operator later passes explicitly.
- Changing `measure_skill_invocation.py` itself, beyond reading from or
  optionally reusing its extraction helper.
- Any change to the actual mounted-skills content, skill-registry, or
  role rulebooks — this issue measures reflection, it does not alter
  what is being reflected against.
- The 2026-08-22 consult log entry itself — this proposal works from the
  issue body's paraphrase since the consult row is not present in this
  checkout (survey, consult basis section); it does not attempt to
  reconstruct or re-run that consult.

## How you'll know it worked

- `python3 scripts/measure_skill_reflection.py <fixture-path>` run live
  prints a per-session reflection table (one JSON line per session) for
  the fixture, each row shaped `{skill, reflected, evidence}` for a
  session with mounted skills, or the explicit not-applicable row for
  the zero-mounted-skill fixture.
- `docs/specs/guidance-reflection-rubric.md` exists, is referenced by
  `docs/specs/reconciled-index.md`, and documents the yes/no/partial
  boundary before any judge call logic depends on it.
- `python3 gates/test_measure_skill_reflection.py` (or pytest over that
  path) passes, with judges mocked, asserting the majority mechanism
  including the split/tie case.
- The zero-mounted-skill case is asserted in test to produce the
  explicit not-applicable row, not an empty or missing row.
