kind: current-state-survey
subject: issue-1160

## What was read this session

- `docs/issue-1160/reports/execution-observation.md` (full file) — the
  step-3 FAIL and its blameless finding, naming three missing pieces: a
  `need_detector` evaluator, a wake path, and a `mission_deliverables`/
  `verified_by` bar-verdict check.
- `roles/specs/brand-design.spec.json`, `content-design.spec.json`,
  `market-analysis.spec.json` (full files) — each carries
  `use_when.need_detector.condition` (prose predicate) +
  `advisory_only: true` + `false_positive_bound`, plus
  `outcome_mission` / `mission_deliverables` (`{artifact,
  fit_criterion}`) / `verified_by` (naming a different role).
- `gates/roles_due.py` (full file) — the closest existing analog: reads
  `use_when.trigger` (a *structured* predicate: `path_patterns`,
  `content_patterns`, `obligation_status`) per spec, evaluates it
  against `git diff`-changed files, and prints a reason string. It is a
  pure classifier — it never spawns anything itself.
- `gates/quality_bar.py` (full file) — `classify(bar_scoped, verdict,
  record_author_account, producer_account, consecutive_bar_not_met_count)`
  → `(BAR_MET|BAR_NOT_MET|ESCALATE|NO_BAR_SCOPED, reason)`. Anti-circularity
  is enforced by comparing *accounts*, not `CLAUDE_ROLE` strings.
  `bar_scoped_roles(pr_files, role_path_patterns)` maps changed files to
  roles via `write_scope`-style glob patterns. Neither function reads
  `mission_deliverables` or `verified_by` today.
  canonical: gates/quality_bar.py (full file, read this session) —
  neither string appears anywhere in it; cross-checked against
  docs/issue-1160/reports/execution-observation.md's own cited
  `grep -n "mission_deliverables\|verified_by" gates/quality_bar.py`
  (zero hits, cited there).
- `gates/role_spec_shape.py` (full file) — shape-checks
  `use_when.board_condition` only; does not touch `need_detector`,
  `outcome_mission`, or `mission_deliverables`.
- `gates/test_quality_bar.py` (first ~40 lines) — existing test style for
  `quality_bar.classify`: five acceptance scenarios plus reject-cap
  escalation, all pure-function, no fixture repos, no network.
- `docs/specs/role-spec-template.schema.json` (first 60 lines) — the
  documented shape `role_spec_shape.py` hand-checks; `use_when` is
  typed loosely (no `need_detector` sub-shape documented yet).

## Write surfaces and their unknowns (aimed at by the proposal)

1. **Need-detector evaluator.** `need_detector.condition` is free prose
   today (e.g. "has UI source files ... AND no design-tokens/*.json
   file exists"), unlike `use_when.trigger`'s already-structured
   `path_patterns`/`content_patterns`. Unknown: whether to (a) parse the
   prose with a hand-rolled heuristic (fragile, couples the evaluator to
   exact wording) or (b) add a small structured sub-schema
   (`path_patterns_present` / `absence_patterns`) alongside the existing
   prose `condition` field, evaluated mechanically like `roles_due.py`
   already does for `trigger`. This is the load-bearing design decision
   the proposal must freeze.
2. **Wake/advisory surface.** Issue #1160 requirement 2 says
   "advisory-first, never a hard gate on day one." Unknown: where the
   advisory line surfaces — a new `spawn.py` subcommand (mirroring
   `roles-due`), or folded into the existing `roles-due` output. The
   requirement explicitly rules out auto-spawn, so the surface is
   read-only text, not a spawn call.
3. **Bar-verdict linkage.** `mission_deliverables`/`verified_by` need a
   check function reusing `quality_bar.classify`'s anti-circularity
   (account-resolved, not `CLAUDE_ROLE`-resolved) rather than
   reinventing it. Unknown: whether this is a thin wrapper around
   `classify` (mapping `verified_by`'s named role to the account that
   authored the bar-verdict record) or a new function in
   `gates/quality_bar.py` itself. Existing `bar_scoped_roles` already
   establishes the pattern of deriving role-scope from spec-declared
   glob patterns — `mission_deliverables[].artifact` values are
   glob-shaped path strings, so the same helper shape applies.
4. **Hermetic tests.** `gates/test_quality_bar.py`'s existing style
   (pure functions, in-memory dicts, no fixture repos, no network) is
   the established convention for `gates/*_test.py`/`test_*.py` in this
   repo — the new evaluator's tests should follow the same shape rather
   than shelling out to `/tmp` fixtures the way execution-observation's
   manual check did (that was explicitly a non-repository throwaway).

## Skip-condition check

Neither scout-directive skip condition applies: this is not a pure
bugfix (three new pieces of machinery, none of which exist), and the
spec (issue #1160 + the execution-observation finding) leaves open
design decisions — item 1 and item 3 above name real forks with more
than one plausible answer. Scouting runs.
