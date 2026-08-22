---
Subject: issue-2015
code_under_review:
  - scripts/measure_skill_reflection.py
  - gates/test_measure_skill_reflection.py
  - gates/fixtures/skill_reflection_artifacts_session.session.log
  - gates/fixtures/skill_reflection_artifacts_workspace/plan/ia.md
loop_state: landed
type: measurement-only harness extension
breaking: false
verdict: pass
---

# Implementation record — artifact-methodology reflection scorer

## What was done

canonical: gh pr view 2034 --json body,files,mergeCommit,state (executed live)

Extended `scripts/measure_skill_reflection.py` per the approved proposal
(`docs/issue-2015/proposals/artifact-methodology-scorer.md`, merged in
PR #2034, mergeCommit d07580b0):

- `parse_pairing_lines(text)` — regexes the fixed
  `<artifact_path> ↔ <skill_name> — <trigger_line>` line shape spawn.py
  (#2014) appends to task text, returning
  `[{"artifact", "skill"}, ...]`; empty list when absent.
- `read_artifact(workspace_root, artifact_path)` — reads the declared file
  relative to a workspace root; `None` when missing.
- `default_artifact_judge_fn(skill, lens, artifact_text)` — new judge
  prompt path asking whether the artifact follows the paired skill's
  methodology, still one skill + one lens + one artifact's text per call.
- `score_artifact(...)` — mirrors `score_skill`'s shape, emits
  `{"artifact", "skill", "verdict": full|partial|absent, "evidence",
  "votes"}`; missing-file case short-circuits to `absent` with zero judge
  calls (`votes: []`).
- `reflect_artifacts(session_path, workspace_root, judge_fn=..., panel_size=3)`
  — extracts pairing lines, reads each artifact, returns
  `{"path", "status": measured|not-applicable, "rows"}`.
- CLI: `__main__` now takes `--workspace <dir>`; with it, prints both the
  existing per-skill reflection line and a new per-artifact
  `reflect_artifacts` line per session-log path; without it, output is
  unchanged from before.
- `gates/fixtures/skill_reflection_artifacts_session.session.log` +
  `gates/fixtures/skill_reflection_artifacts_workspace/plan/ia.md` — a
  synthetic session log carrying two pairing lines (one resolvable
  artifact, one deliberately missing file) plus the workspace file for the
  resolvable one.
- 8 new tests in `gates/test_measure_skill_reflection.py`: pairing-line
  extraction (present + absent), `read_artifact` present/missing,
  `score_artifact` missing-file -> `absent` with no judge call, majority
  verdict assignment, builder-blind (judge only sees one skill + one
  artifact's text), `reflect_artifacts` measured (mixed present/missing
  rows) and not-applicable paths.

## Why

Per the issue: close the loop "artifact exists" (#2013's existence gate)
-> "artifact follows the methodology" (this scorer), measurement only, no
new gate/refusal path. The proposal's Rationale chose parsing spawn.py's
already-emitted pairing line over re-running #2014's pairing algorithm at
scoring time, because the session log does not preserve the exact
skill-dir set spawn.py had at build time — re-deriving risks scoring
against a skill the builder was never actually shown, breaking
builder-blind's other side.

## Upstream basis

canonical: docs/issue-2015/proposals/artifact-methodology-scorer.md (read, this turn)

- Proposal: `docs/issue-2015/proposals/artifact-methodology-scorer.md`
  (merged PR #2034, commit d07580b0).
- Reused machinery: `parse_consult_output`, `majority`-shaped tie logic
  (issue #1991/#1999); pairing-line shape frozen by
  `test/test_spawn_artifact_skill_pairing.py` (issue #2014).

## Acceptance

canonical: python3 -m pytest -q -o addopts= gates/test_measure_skill_reflection.py (executed live, this turn, transcript below)

acceptance: python3 -m pytest -q -o addopts= gates/test_measure_skill_reflection.py — result: 18 passed, 0 failed, 0 skipped

checked: `python3 -m pytest -q -o addopts= gates/test_measure_skill_reflection.py` — result:
```
18 passed in 0.05s
```

## What did not work

None.

## Open findings

None.

## Test-tier note

`.on-the-record/test-tiers.json`'s `fast` tier
(`python3 -m pytest -q -m "not slow"`, budget 300s) covers this suite; the
`slow` trigger only fires on `spawn.py`/board-flow file changes, none of
which this issue's frozen write set (`scripts/`, `tests/`, `test/`,
`docs/`) touched. No full-suite wall-clock gap to record.
