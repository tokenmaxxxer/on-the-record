---
status: proposed
files:
  - scripts/measure_skill_reflection.py
  - gates/test_measure_skill_reflection.py
  - gates/fixtures/skill_reflection_artifacts_workspace/
---

## Request

Issue #2015 (artifact-gate phase 4): extend
`scripts/measure_skill_reflection.py` so that, for a completed
design-bearing session, each artifact declared under that session's
`design-artifacts:` tag is scored — full/partial/absent, with quoted
evidence — against the methodology of the skill #2014's pairing logic
tied it to at spawn time. Measurement only, no gate. Builder-blind stays:
judges never see the full mounted-skill list. A fixture test runs the
scorer over a synthetic workspace and checks verdict extraction and
evidence quoting.

## Constraints

- No gate, no refusal path — this is a measurement/reporting addition
  only (issue text: "This is measurement only (no gate)").
- Builder-blind preserved: a per-artifact judge call must never see the
  full mounted-skill list or which other artifacts were paired to which
  other skills.
- Reuse #1991/#1999's 3-judge/`majority`/`parse_consult_output` machinery
  rather than inventing a second judging pipeline.
- Reuse #2013/#2014's existing parsing surfaces
  (`design_artifacts_gate.parse_declaration`, the fixed
  `<path> ↔ <skill_name> — <trigger>` pairing-line shape spawn.py already
  emits into the task text) rather than re-deriving the pairing from
  scratch — the survey confirms this pairing line already lands in the
  session log's text content, no new logging needed.
- Frozen write set: `scripts/`, `tests/`, `test/`, `docs/` (per issue
  scope line).

## Rationale

Two designs were considered for recovering "which skill was this artifact
paired to":

1. **Re-run #2014's pairing algorithm at scoring time** (re-tokenize the
   artifact stem, re-score against the workspace's currently-mounted
   skill dirs) — rejected. It requires reconstructing the exact
   `skill_dirs`/`role_source`/`cross_family_dirs` set spawn.py had at
   *build* time, which the session log does not preserve verbatim (only
   the flattened mounted-skill list survives, not which skill-repository
   directories fed the pairing scorer, nor the original tie-break order).
   Re-deriving it risks a different pairing than what the builder actually
   saw, which would silently break builder-blind's other side: the score
   would then be judging the artifact against a skill the builder was
   never actually pointed at.
2. **Parse the pairing line spawn.py already wrote into the task text**
   (chosen) — the line format is fixed
   (`<artifact_path> ↔ <skill_name> — <trigger_line>`,
   `test/test_spawn_artifact_skill_pairing.py` pins it), it is already
   captured verbatim in the session log's assistant/user text that
   `extract_session` scans, and it records the *actual* pairing the
   builder session was told about — not a recomputation. This mirrors how
   `extract_session` already recovers the mounted-skill list from a fixed
   marker line (`'"subtype":"init"'`) instead of re-deriving it.

For the verdict vocabulary, `full/partial/absent` (issue's own wording)
is used instead of reusing `yes/no/partial` verbatim, because "does this
artifact follow the paired skill's methodology" is a conformance
judgment, not a reflected/not-reflected boolean — `absent` covers both
"artifact file missing from the workspace" and "artifact exists but shows
no trace of the skill's procedure," which `no` does not distinguish for a
human reading the table. `majority()` stays untouched and generic — it
already operates on any 3-vote `{"verdict","evidence"}` list, verdict
strings included.

## What will be done

- Add `parse_pairing_lines(text) -> list[dict]` to
  `scripts/measure_skill_reflection.py`: regex over the
  `<path> ↔ <skill_name> — <trigger_line>` shape, returning
  `[{"artifact": path, "skill": skill_name}, ...]`. Byte-inert (empty
  list) when the marker block or no matching lines are present.
- Add `read_artifact(workspace_root, artifact_path) -> str | None`: reads
  the declared artifact file relative to a workspace root; `None` when
  missing (feeds the `absent` verdict directly, no judge call needed for
  a missing file).
- Add an artifact-conformance judge prompt path: a new
  `default_artifact_judge_fn(skill, lens, artifact_text)` (or a `kind`
  parameter threaded through the existing `default_judge_fn`) that asks
  the judge whether the artifact content follows the named skill's
  methodology, still one skill + one lens + one artifact's text per call
  — never the sibling artifact/skill list.
- Add `score_artifact(artifact_path, skill, artifact_text, judge_fn,
  panel_size=3) -> dict` mirroring `score_skill`'s shape but emitting
  `{"artifact", "skill", "verdict": "full"|"partial"|"absent",
  "evidence", "votes"}`.
- Add `reflect_artifacts(session_path, workspace_root, judge_fn=...,
  panel_size=3) -> dict`: extracts pairing lines from the session log,
  reads each artifact from `workspace_root`, and returns
  `{"path", "status": "measured"|"not-applicable", "rows": [...]}` —
  `not-applicable` when no pairing lines were found (mirrors
  `reflect_session`'s own `no-mounted-skills` empty state).
- Wire a small CLI addition (`__main__` block) so running the script
  against a session log + `--workspace <dir>` prints both the existing
  per-skill reflection rows and the new per-artifact table, without
  changing the existing no-`--workspace` output shape.
- Add `gates/fixtures/skill_reflection_artifacts_workspace/` — a
  synthetic workspace directory plus a session-log fixture carrying a
  pairing-line block — and matching tests in
  `gates/test_measure_skill_reflection.py` asserting: pairing-line
  extraction, full/partial/absent verdict assignment from mocked judges,
  quoted-evidence propagation, and the missing-artifact-file ->
  `absent`-with-no-judge-call path.

## Out of scope

- No enforcement/gate behavior — nothing here blocks `gh pr create` or
  any other action; #2013's existence-only gate is untouched.
- No change to #2014's pairing algorithm itself (`spawn.py:8173-8212`) —
  this issue only *consumes* the pairing line it already emits.
- No change to the `reflect_session`/per-skill reflection output shape or
  its existing fixtures — the artifact table is additive, a new function
  and a new CLI flag, not a rewrite of the existing path.
- Live wiring into any CI/reporting pipeline that automatically invokes
  the extended scorer post-session — this issue delivers the harness
  capability and its fixture test, not a new automated invocation site.

## How you'll know it worked

- `python3 scripts/measure_skill_reflection.py <session-log> --workspace
  <dir>` on a completed design-bearing session's real workspace prints a
  per-artifact table: artifact path, paired skill, verdict
  (full/partial/absent), quoted evidence — matching the issue's
  Acceptance line verbatim.
- A judge-call inspection (mock in tests) confirms each artifact-judge
  call receives exactly one skill name + one artifact's text — never the
  full declared-artifact list or sibling pairings — preserving
  builder-blind.
- `gates/test_measure_skill_reflection.py`'s new tests pass: pairing-line
  parsing, verdict extraction (full/partial/absent) from a mocked 3-judge
  panel, evidence quoting, and the missing-file -> `absent` path with no
  judge call made.
