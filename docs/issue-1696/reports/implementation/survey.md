# Current-state survey — issue #1696

Scope: command-identity rule for executed-live provenance.

## Write set found by reading the codebase

- `gates/requirement_met.py` — the `requirement_met` grader (issue
  #1651/#1660/#1661). Its `grade()` already runs a deterministic
  artifact-presence sub-check (`_artifact_in_diff_hunk`) that blocks a
  YES-graded check whose cited artifact is absent from the PR diff. This
  is the natural home for a second deterministic sub-check:
  command-identity. `grade()`'s docstring already documents the
  separation between the deterministic layer (blocks) and the semantic
  LLM verdict layer (advisory-only, never blocks) — the new check must
  stay on the deterministic side per that existing contract.
- `gates/test_requirement_met.py` — existing fixture-style unit tests
  (`t_*`, `rm.grade()` called directly with a body/diff/verdicts triple,
  no network). The mismatched-command fixture belongs here, matching the
  file's own convention.
- `on-the-record/hooks/directive.sh` — carries the "ACCEPTANCE FORMAT"
  block (around line 300) that is the injected orchestrate/role
  directive text governing how `## Acceptance` criteria get drafted.
  This is the "orchestrate/role directive text" the issue's acceptance
  criterion names.
- `gates/acceptance_gate.py` — its module docstring is the acceptance
  criteria format's own documentation (referenced from directive.sh:
  "`gates/acceptance_gate.py` enforces this post-hoc as a backstop").
  This is the "acceptance-format documentation" the issue names.

## What already exists (reused, not rebuilt)

- `gates/record_lint.py`'s `_EXECUTED_LIVE_CANONICAL` already defines
  the citation shape `acceptance: <command> — result: <outcome word>`
  (three accepted outcome words) as the canonical executed-live proof
  format (issue #870/#892/#914). The new command-identity check reuses
  this exact shape to find "what was actually recorded as run" in a PR
  diff — no new citation format is introduced.
- `gates/check_runner.py`'s `parse_checks()` already classifies a
  `check:`/`gate:` bullet's backtick content as a `command` when it
  looks like an invocation (starts with `python3`/`bash`/etc. or is a
  path with a dot) — same heuristic informs how this check's "artifact"
  is read as a command surface rather than a mere file path.
- `docs/specs/acceptance-commands.md` +
  `on-the-record/hooks/acceptance-command-real-run-guard.sh` (issue
  #914) already re-run a *registered* acceptance command at commit time
  and compare its actual exit status against the claimed outcome — a
  different axis (did the claimed result actually happen just now) from
  this issue's axis (does the recorded command match the command
  surface the check itself names). The two are complementary, not
  overlapping: the guard proves the recorded command really ran and
  matched its claimed outcome; this issue's grader proves the recorded
  command IS the one the check named.

## Design decision (no alternative worth naming — mechanical extension)

The task is a direct extension of an existing, already-shaped
deterministic sub-check in the same function (`grade()`), reusing an
already-defined citation regex from a sibling module. There is no
design/methodology choice open — the shape (fields, blocking semantics,
docstring separation of concerns) is fixed by the surrounding code this
change must not diverge from. Per the scout directive's skip condition
("the spec leaves no design decision open"), scouting is skipped here;
this survey substitutes for it.
