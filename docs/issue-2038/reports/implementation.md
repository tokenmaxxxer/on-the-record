---
code_under_review:
  - scripts/measure_skill_reflection.py
  - gates/test_measure_skill_reflection.py
  - gates/fixtures/skill_reflection_empty_deliverable_session.session.log
loop_state: landed
type: fix
breaking: false
verdict: pending
---

# Issue #2038 — reflection scorer refuses on empty deliverable, falls back to workspace diff

## What was done

canonical: scripts/measure_skill_reflection.py:196-219 @ 3a00e37b

`reflect_session` no longer scores an empty deliverable.

canonical: scripts/measure_skill_reflection.py:203-210 @ 3a00e37b

When `extract_session` finds mounted skills but the deliverable text is
empty/whitespace, it calls the new `get_final_commit_diff(workspace_root)`
helper: `git -C <workspace> show HEAD`, returning `None` on no workspace,
no git repo, or an empty diff.

canonical: scripts/measure_skill_reflection.py:211-213 @ 3a00e37b

If a diff is found, judging proceeds against it, prefixed with a
`[workspace final commit diff — code-shaped deliverable, ...]` label.

canonical: scripts/measure_skill_reflection.py:214-216 @ 3a00e37b

If no diff is found either, `reflect_session` returns
`{"status": "no-deliverable-extracted", "rows": []}` — no judge calls.

canonical: scripts/measure_skill_reflection.py:204-206 @ 3a00e37b

The CLI `__main__` block now forwards `--workspace` to `reflect_session`
too (previously only `reflect_artifacts` received it).

## Why

Previously, an empty deliverable (observed live on the arcade-dodger #29
session, per the issue text) silently produced judge calls whose verdicts
were artifacts of missing input — 4 "partial" verdicts whose evidence
uniformly said the deliverable text was absent. Refusing loudly on empty
input, and extending extraction to code-shaped deliverables via the
workspace's final commit diff, matches issue #2038's frozen `## Acceptance`.

## Upstream basis

Issue #2038 (frozen `## Acceptance`), building on `reflect_session` /
`extract_session` as landed in issue #2015 phase 2, commit 8841c7e6.

## What did not work

None.

## Tests

canonical: python3 -m pytest -o addopts= gates/test_measure_skill_reflection.py -v (executed this turn)
acceptance: python3 -m pytest -o addopts= gates/test_measure_skill_reflection.py -v — result: PASS (22 passed, 0 skipped, 0 failed in 0.13s)

New/changed tests in gates/test_measure_skill_reflection.py:
- `test_reflect_session_empty_deliverable_no_workspace_refuses` — asserts
  `status == "no-deliverable-extracted"`, `rows == []`, and the judge is
  never called, when there is no workspace to fall back to.
- `test_reflect_session_empty_deliverable_falls_back_to_workspace_diff` —
  builds a throwaway git repo at test time (`make_code_workspace`, not a
  checked-in fixture — a nested `.git` under `gates/fixtures` would stage
  as a submodule gitlink rather than real file content) with one commit,
  and asserts the judge is called with the labeled diff and a "yes"
  verdict flows through.
- `test_get_final_commit_diff_returns_none_for_non_git_dir` /
  `_for_missing_workspace` — direct unit coverage of the new helper's
  refusal paths.

canonical: gates/fixtures/skill_reflection_empty_deliverable_session.session.log @ 3a00e37b

New fixture: mounted skill, but only a `tool_use` block, no assistant
text, so `extract_session` yields an empty deliverable string.

## What will be done

Build-now bypass, contract v3 s19a: `CORE_BUILD_NOW=1` was set by the
spawner; delivered directly per the frozen Acceptance, no phase-1 proposal
round.

## Out of scope

`reflect_artifacts` (the separate artifact-conformance path) was not
touched — issue #2038's Acceptance text is scoped to the deliverable-scoring
path (`reflect_session`).

## Open findings

None.
