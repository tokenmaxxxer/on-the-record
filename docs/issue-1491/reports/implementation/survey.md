# Survey: standing-red zero policy (#1491)

## Current state

- Watchdog logic lives entirely in `spawn.py`. The observe-only contract
  is established there: `watchdog_check_one()` (spawn.py:2404) inspects
  one live session and returns anomalies without mutating anything;
  `roster_watchdog()` (spawn.py:3078) is the outer loop that prints
  signal lines and is explicitly documented as never fixing or closing
  anything. `WATCHDOG_STATE` (spawn.py:2384, `runs/watchdog_state.json`)
  is the existing precedent for a watchdog persisting cross-tick state
  (denial counters, silence timers) — the standing-red check's
  `(test_id, tree_hash, consecutive_count)` state (req 3) fits the same
  shape and should live beside it, not invent a new state-file
  convention.
- No existing "run the test suite and diff results" watchdog check
  exists yet — a search across `*.py` outside `spawn.py` and its tests
  for watchdog-check function definitions turns up nothing else. This
  is new surface, not an extension of an existing check function.
- Tiering (#1490) landed as `gates/test_tier_contract.py`: `load_contract()`
  reads a target repo's `.on-the-record/test-tiers.json` (fast command +
  `budget_seconds`, default 300; optional slow command +
  `trigger_change_classes`); `select_tier()` picks the tier. This repo's
  own contract is what a standing-red check on *this* repo's main would
  read.
- The test-tier contract convention (#1518) landed
  `gates/test_tier_contract.py`'s consuming surface plus
  `on-the-record/hooks/test-tier-directive.sh`, an observe-only
  `UserPromptSubmit` directive (the same one visible in this session's
  own hook output) that tells a role session to check for
  `.on-the-record/test-tiers.json` before running a target repo's suite.
  #1491 reuses the same artifact, but from watchdog cadence code, not
  from a role session's directive-following.
- `WATCHDOG_SILENCE_MIN` / `WATCHDOG_NO_COMMIT_MIN` / `WATCHDOG_DENIAL_THRESHOLD`
  (spawn.py:2385-2387) are the existing "bounded cadence + threshold"
  precedent this issue's flake-suppression req (3 — two consecutive
  failures on the same tree) should mirror in shape: a named constant,
  a short comment citing its issue, state carried in the JSON state file.
- The "observation-loss regression guard" pattern is a project-wide
  invariant, not specific to #1491: `tests/test_gh_read_cost.py`'s
  `TestNoObservationLoss.test_no_observation_loss` and the invariant
  named at spawn.py:2125 both establish that a watchdog-adjacent change
  must not silently drop coverage of something it used to observe. For
  #1491 this means: adding the standing-red check must not reduce
  roster_watchdog's existing per-session anomaly coverage, and the new
  check's own coverage (which tests it is/isn't watching) must itself
  be assertable, not just implied.
- Issue-filing precedent: `roster_watchdog()`'s docstring (spawn.py:3081)
  states the check prints signal lines for a human/orchestrator to act
  on — the filing of a defect issue per req 2 is explicitly the
  orchestrator's job reading that signal line, not the watchdog process
  itself calling `gh issue create`. No existing watchdog code path calls
  `gh issue create` directly; keeping that pattern (report-only, orchestrator
  files) is consistent with every other watchdog check in the codebase.

## Write set for this issue, phase-1

Per the task's own framing ("design only, no enforcement changes yet"),
phase-1 delivers a design/proposal record only: the proposal document
under the issue's proposals directory, and this survey. No `spawn.py`,
`gates/`, or `tests/` changes land in this PR.

## Alternatives considered (feeds proposal Rationale)

- Standalone new script (e.g. a new `checks/` module) vs. a new
  function inside `spawn.py` alongside `watchdog_check_one`/`roster_watchdog`.
  Both are plausible: `spawn.py` already owns every other watchdog
  check and its state file, but it is already a very large module
  (6000+ lines) and standing-red watch is a self-contained
  read-suite/diff/report loop with almost no coupling to session
  roster state (`entry`, `key`, git worktree paths) that
  `watchdog_check_one` depends on.
