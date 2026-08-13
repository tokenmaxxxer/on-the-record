---
status: approved
files:
  - spawn.py
  - tests/test_spawn.py
---

## Request

Consumer sessions (target repos, plugin installed) get `spawn.py watchdog`
output scoped to tokenmaxxxer/on-the-record itself (its own drift lines,
issue/PR references, checkout paths) instead of their own target repo's
board — cross-repo leakage every ~60s. Anchor the watchdog to the session's
target project root in consumer sessions; keep it anchored to the checkout
in dev sessions (cwd == the checkout).

## Constraints

- No behavior change for the dev-session case (cwd is the on-the-record
  checkout itself) — same board, same output shape.
- No new `gh`/network calls introduced (matches `requirement_drift`'s own
  stated no-new-gh-call-type constraint).
- `gates/` code (closure_sweep, spawn_coverage, requirement_linkage) only
  ever exists in the checkout — the import path must not follow the scan
  target.
- Skip condition applies (see survey): mechanical anchoring defect, no design
  decision open — validity consult and scout sweep both skipped per the
  issue's own `validity-consult-skip: trivial` tag and this build's
  skip-condition line.

## Rationale

Considered leaving `roster_watchdog()`'s signature untouched and instead
having `poll-rearm.sh` pass an explicit `-C "$(pwd -P)"` on the `nohup ...
watchdog` call, relying on `-C`'s existing default-to-cwd behavior. Rejected:
the CLI's `watchdog` dispatch line never read `a.cwd` at all
(`roster_watchdog(auto_respawn=..., all_scope=...)`, no `root`/`cwd`
argument) — fixing only the shell caller would still leave `-C` silently
discarded for every other watchdog entry point (tests, ad-hoc `spawn.py
watchdog -C <repo>` calls), not just this one. Threading `root` through
`roster_watchdog()` itself fixes the CLI, the shell caller (which already
passes no `-C`, correctly relying on cwd-as-default now that the value is
actually used), and any future caller in one place.

## What will be done

- Add `root: Path = ROOT` to `roster_watchdog()`; replace its internal
  `ROOT` references used for board scanning (`_board_wide_sweep`,
  `_build_observed`, `_post_session_end_comment`,
  `_pr_open_or_merged_for_branch`, both `diagnose_health` calls) with `root`.
- In `_board_wide_sweep` and `requirement_drift`, keep the `gates/` import
  `sys.path.insert` pinned to the module-level `ROOT` (checkout) regardless
  of the `root` argument, since that argument now means "board to scan," not
  "where the code lives."
- In the CLI dispatch for `a.role == "watchdog"`, pass
  `root=Path(a.cwd).resolve()` so `-C` (default `"."`) actually reaches the
  watchdog.
- Update the one existing test asserting the old (rootless) call shape;
  add a CLI `-C`-threading test, a hermetic consumer-fixture test (foreign
  repo, no board, no gh reachability required) asserting no checkout-path /
  `marketplaces` / `tokenmaxxxer/on-the-record` references appear in output,
  and a dev-session-unchanged test.

## Out of scope

- `directive.sh`'s prose (it already reads the board via `spawn.py -C
  <repo>`, and role-spawn defaults already thread `-C` correctly per the
  survey — only the `watchdog` CLI branch silently dropped it).
- Any other `spawn.py` subcommand's `-C` handling — none of the others were
  found to ignore `a.cwd`.
- The northpole harness fixture's own signal #7 precondition file (not
  located in this tree per the survey — out of this write set).

## Accumulation

This does not add a new inline `gh`/subprocess call site or a new repeated
per-role file — it corrects one existing call site (`roster_watchdog()`'s
board-facing calls) to take an already-parsed argument it was silently
dropping. There is exactly one `watchdog` CLI dispatch line and one
`roster_watchdog()` definition, so this fix does not multiply: per the
survey, no other `spawn.py` subcommand was found ignoring `a.cwd` the same
way — each already threads its own `-C`/`root` independently, so there is
nothing here to repeat N times.

## How you'll know it worked

- `python3 -m pytest tests/test_spawn.py -k "watchdog or board_wide_sweep or ConsumerFixture"`
  passes, including the new hermetic consumer-fixture test.
- A live scratch foreign repo (git-init'd, no GitHub remote, no board) run
  through `spawn.roster_watchdog(root=<scratch repo>)` produces no
  tokenmaxxxer/on-the-record or checkout-path references — silent/generic
  "no board data" output only.
