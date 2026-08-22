# issue-1999 current-state survey

## Skip condition

This is a pure bugfix (design-research-skip: mechanical, per the issue's
own frontmatter) — the fix is a parser-format mismatch with one correct
resolution, not a design choice among alternatives. Scouting/design-scope
skipped per the scout-directive's stated skip condition; this survey
documents the actual defect instead.

## What was surveyed

- `scripts/measure_skill_reflection.py` (91 lines) — `default_judge_fn`
  parses `spawn.py consult`'s stdout via `out.splitlines()[0]` (verdict)
  and `out.splitlines()[1]` (evidence), assuming a plain-text
  "verdict-line, evidence-line" format.
- `spawn.py`'s `consult_cmd` (spawn.py:5658) and its CLI print
  (spawn.py:7058: `print(json.dumps(verdict, indent=2, ensure_ascii=False))`)
  — the actual output is a pretty-printed JSON object
  `{"answer", "confidence", "caveats"}`, never the plain two-line text
  `default_judge_fn`'s own prompt requests. `consult_cmd`'s base prompt
  (spawn.py:5701-5709) unconditionally appends its own JSON-format
  instruction, overriding any format request in the caller's prompt —
  so the caller's "answer with yes/no/partial then one line of evidence"
  instruction was always going to be ignored.
- `gates/test_measure_skill_reflection.py` (85 lines, pre-fix) — every
  existing test mocks `judge_fn` directly (`make_judge`), so
  `default_judge_fn`'s parsing logic was never exercised by any test;
  the defect shipped without any test catching it.
- `docs/specs/guidance-reflection-rubric.md` — already documented the
  mixed-vote → `partial` tie table (lines 47-54, pre-fix), but had no
  section on evidence extraction itself and no single explicit
  "mixed-vote tie rule" label to cite against the acceptance check's
  wording.
- `gates/fixtures/skill_reflection_with_skills.session.log` and
  `skill_reflection_no_skills.session.log` — existing fixtures, reused
  as-is; the defect is in judge-output parsing, not session extraction,
  so no new fixture was needed.

## Root cause

Pretty-printed JSON's line 1 is `{` (unrecognized as yes/no/partial →
silently defaults to `partial`) and line 2 is `  "answer": "no",` — the
literal fragment shape reported in the issue's production-run example.
