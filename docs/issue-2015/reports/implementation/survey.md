---
Subject: issue-2015
---

# Current-state survey — reflection scorer extension for design artifacts

## Write surfaces

- `scripts/measure_skill_reflection.py` (117 lines) — the harness to extend.
- `gates/test_measure_skill_reflection.py` — fixture tests, mirrors this shape.
- `gates/fixtures/skill_reflection_*.session.log` — synthetic session-log fixtures.

## What exists today (`scripts/measure_skill_reflection.py`)

- `extract_session(path)`: reads a session-log JSONL, pulls the mounted-skill
  list from the `init`/`plugins` line, and concatenates all assistant
  text/tool_use text into one `deliverable_text` string.
- `default_judge_fn(skill, lens, deliverable_text)`: shells to
  `spawn.py consult` with a prompt naming one skill and one lens
  (`compliance|violation|applicability`), parses the pretty-printed JSON
  `{"answer","confidence","caveats"}` back into `{"verdict","evidence"}`
  (`parse_consult_output`).
- `score_skill(skill, deliverable_text, judge_fn, panel_size=3)`: runs the
  3-lens panel for one skill, takes `majority(votes)`.
- `reflect_session(path, judge_fn, panel_size)`: mounted-skill list ->
  one `score_skill` row per skill. `status: not-applicable` when nothing
  was mounted.
- Builder-blind property (already established, issue #1991/#1999): each
  judge call only ever receives one `skill` name + one `lens` + the
  deliverable text — never the full mounted-skill list, never which other
  skills scored ok/not. That list only exists in the outer loop
  (`reflect_session`), never crosses into a judge prompt.
- No CLI/API path takes a *workspace* directory today — only a session-log
  path. `deliverable_text` is built purely from the session log's own
  assistant/tool_use content, never a live file read.

## `design-artifacts:` contract (issue #2013, `docs/specs/design-artifacts-contract.md`)

- An issue body may carry a `design-artifacts:` tag followed by a bulleted
  list or fenced block of repo-relative paths.
- `gates/design_artifacts_gate.py::parse_declaration(body) -> list[str] | None`
  parses that tag (existence-only gate, `gh pr create`-time, no content
  judgment — explicitly out of its scope per its own docstring).
- No tag anywhere in the body -> `None`, byte-inert.

## Artifact↔skill pairing (issue #2014, `spawn.py:8173-8212`)

- At spawn time, if `parse_declaration(body)` returns a non-empty list,
  `spawn.py` computes, for each declared artifact path, the mounted skill
  whose SKILL.md trigger line shares the most tokens with the artifact's
  `Path(...).stem` (`_tokenize` reused from #1978B/#2001), and appends one
  line per artifact to the spawned session's task text, in the literal
  format:

  ```
  아티팩트-스킬 짝짓기(이슈 #2014): 선언된 각 아티팩트를 그것을 만드는 절차를 담은 스킬과 짝지었다.
  <artifact_path> ↔ <skill_name> — <trigger_line>
  ```

- This block is only emitted when at least one artifact ties to a skill
  (`pairing_lines` non-empty); absent tag or zero overlap -> byte-identical
  to before (`test/test_spawn_artifact_skill_pairing.py` pins both
  branches).
- Because this text is appended to the *task*, it lands in the session log
  as part of the initial user/task message content — the same JSONL
  `extract_session` already scans for text blocks. No new session-log
  field is needed to recover the pairing after the fact; it is already
  logged verbatim, in a fixed, greppable line shape.

## 3-judge scorer precedent for artifacts (issue #1991/#1999)

- `parse_consult_output` already treats `spawn.py consult`'s pretty JSON as
  the judge-answer channel and extracts `caveats` as quoted evidence —
  reusable as-is for an artifact judge; the prompt content (what's being
  judged) is what needs to change, not the parsing.
- `majority()` is generic over any 3-vote list of `{"verdict","evidence"}`
  dicts — reusable unchanged, but the current vocabulary is
  `yes/no/partial` (booleanish). The issue text asks for
  `full/partial/absent` per artifact, which is a different vocabulary,
  not a reflected/not-reflected boolean — this needs a translation, not a
  reuse of `LENSES`/`yes|no` as-is.

## What's missing for this issue

1. No function reads a workspace's actual artifact *file contents* — only
   session-log text. Judging "does the artifact follow the paired skill's
   methodology" requires the produced file's content (e.g. the HTML
   demo's markup for a contrast/accname check), not just what the builder
   said about it in chat.
2. No function recovers the artifact->skill pairing after the build
   session ended — needs a small parser for the fixed pairing-line shape
   spawn.py already emits (`<path> ↔ <skill_name> — <trigger>`), mirroring
   how `extract_session` already greps a fixed marker line
   (`'"subtype":"init"'`) rather than re-deriving the pairing from
   scratch.
3. No `full/partial/absent` vocabulary or judge prompt asking "does this
   artifact follow this skill's methodology" (current judge prompt asks
   about skill *reflection* in a deliverable, not artifact-vs-procedure
   conformance).
4. No per-artifact table output shape (artifact, paired skill, verdict,
   quoted evidence) — `reflect_session`'s output shape is per-skill rows,
   not per-artifact rows.
5. No fixture test exercising a synthetic *workspace* (files on disk) —
   existing fixtures are session-log-only; a workspace-backed fixture is
   new.

## Builder-blind constraint, reconfirmed for this extension

The existing property judges never see the full mounted-skill list.
Extending to artifacts must preserve this: a per-artifact judge call
receives the one paired skill's procedure + that one artifact's content,
never the full `design-artifacts:` list or which other artifacts/skills
were paired. This is a straightforward carry-over of the existing
per-skill judge-call shape, not a new mechanism.

## No test-tier gap

`.on-the-record/test-tiers.json`'s `fast` tier is
`python3 -m pytest -q -m "not slow"` (budget 300s); `slow` triggers only
on `spawn.py`/board-flow files, none of which this issue's frozen write
set (`scripts/`, `tests/`, `test/`, `docs/`) touches. No full-suite
wall-clock measurement gap to record for this phase (survey/proposal-only,
no code yet).
