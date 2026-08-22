---
status: proposed
files:
  - scripts/measure_skill_reflection.py
  - gates/test_measure_skill_reflection.py
  - docs/specs/guidance-reflection-rubric.md
---

## Request

Fix `measure_skill_reflection.py` so every measured row's evidence field
carries a non-JSON prose snippet (the judge's quoted rationale or a
deliverable quote), not a raw fragment of the judge consult's pretty-
printed JSON (e.g. `'"answer": "no",'`), and document the mixed-vote tie
rule explicitly in the rubric doc. A judge returning no rationale must
yield the literal `evidence: 'judge-gave-no-rationale'`, never a JSON
fragment.

## Constraints

- Fix confined to `scripts/`, `docs/`, `gates/` per the issue's stated
  scope.
- Must not change `majority()`'s existing tie behavior (already correct
  and covered by tests) — only the judge-output parsing that feeds
  `evidence` into `score_skill`/`majority`.
- Existing mocked-judge tests must keep passing unchanged.

## Rationale

Per `docs/issue-1999/reports/implementation/survey.md`, the actual bug is
that `spawn.py consult` prints pretty-printed JSON
(`json.dumps(verdict, indent=2)`), not the plain two-line text
`default_judge_fn`'s own prompt requests — `consult_cmd`'s own
JSON-format instruction always overrides any format the caller asks for.
Two alternatives were considered:

1. **Change `consult_cmd`'s output format** to the plain "verdict line +
   evidence line" text `default_judge_fn` originally expected. Rejected:
   `consult_cmd` is a shared seam used by every other `spawn.py consult`
   caller across the codebase (issue #699 lineage); changing its output
   contract to suit one caller risks breaking every other consumer of
   `{"answer","confidence","caveats"}`, and is out of this issue's
   `scripts/, docs/, gates/` scope (spawn.py is not in scope).
2. **Parse the JSON `consult_cmd` actually emits**, mapping `answer` to
   the verdict and `caveats` to the evidence string (falling back to
   `judge-gave-no-rationale` when caveats are empty or the output isn't
   parseable). Chosen: confines the fix entirely to
   `measure_skill_reflection.py`'s own judge-output parsing, matches
   `consult_cmd`'s actual, stable output contract, and directly produces
   prose evidence (the caveats are free-text rationale) instead of a
   JSON fragment.

## What will be done

- Add `parse_consult_output(out)` in `measure_skill_reflection.py`:
  `json.loads` the consult output, take `answer` as the verdict
  (fallback `partial` if missing/unrecognized), join non-empty `caveats`
  as the evidence string, fallback to `judge-gave-no-rationale` when
  there are none or the output fails to parse as a JSON object.
- Route `default_judge_fn` through it instead of `out.splitlines()`.
- Add unit tests for `parse_consult_output` covering: pretty-printed
  JSON with caveats, no caveats, and unparseable output.
- Add an explicit "Mixed-vote tie rule" paragraph and an "Evidence
  extraction" section to `docs/specs/guidance-reflection-rubric.md`
  stating the `judge-gave-no-rationale` empty-state and that a raw judge
  JSON fragment is not valid evidence.

## Out of scope

- Changing `consult_cmd`'s or `spawn.py consult`'s CLI output format.
- Adding a live network/subprocess-invoking test for `default_judge_fn`
  itself (it already documents that it is not exercised by tests, by
  design — this issue does not change that seam, only what it does with
  the output it receives).
- Any change to `majority()`'s tie-resolution logic — it already
  produces `partial` on an even split / three-way tie; this issue is
  about a different bug (evidence extraction) that happened to surface
  in the same file.

## How you'll know it worked

`python3 -m pytest -o addopts= gates/test_measure_skill_reflection.py -v`
run live, all tests passing, including new `parse_consult_output` tests
asserting evidence for a pretty-printed-JSON judge reply contains no `{`
or `"answer"` fragment, and that a no-caveats/unparseable reply yields
exactly `judge-gave-no-rationale`.
