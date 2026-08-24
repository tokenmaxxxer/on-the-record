---
code_under_review:
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/monitors/test_poll_heartbeat.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# issue-2163 — implementation record

## What was done

Root-caused and fixed the patrol-poll crash burst reported live in the
issue: `claude plugin marketplace update tokenmaxxxer` (stale-directory
cleanup + re-clone) produced `[patrol-poll] <role>: crashed (rc=2)` for
every one of the 43 configured roles in a single tick.

- `on-the-record/monitors/poll-heartbeat.sh`: added an existence guard
  at the top of the tick loop, right after `_alive_stamp_write` and
  before the `poll-due` call. It re-checks the same signal
  `poll_rearm_resolve_checkout` already trusts (`spawn.py` present at
  `CHECKOUT`); when missing, it prints exactly one advisory line
  (`[poll-heartbeat] checkout unavailable at <path> (mid-update?),
  skipping tick`) and skips the whole tick — both the due-check branch
  and the unconditional patrol block — instead of letting `poll-due` and
  every per-role `patrol_promote.py` subprocess fail independently.
  Also added an in-code note next to the patrol block documenting that
  its per-tick "check every configured role" behavior is intentionally
  uncapped and a different code path from `gates/patrol_wiring.py`'s
  merge-seam `MAX_ROLES_PER_MERGE=3` (acceptance check 2 below).
- `on-the-record/monitors/test_poll_heartbeat.py`: added
  `t_patrol_tick_skips_when_checkout_vanishes_mid_sleep`, which runs the
  script as a background subprocess, deletes the checkout directory
  while it sleeps between ticks (simulating the reclone's stale-dir
  cleanup), and asserts exactly one skip line, no `crashed` text, no
  `[patrol-poll]` output at all, and that no per-role
  `patrol_promote.py` subprocess ran (marker file stays absent).

canonical: `on-the-record/monitors/poll-heartbeat.sh:188-209` (new guard
clause), `on-the-record/monitors/poll-heartbeat.sh:410-419` (new
uncapped-by-design comment before `patrol_tick=$((patrol_tick + 1))` at
line 421), `on-the-record/monitors/test_poll_heartbeat.py:716-766`
(new test `t_patrol_tick_skips_when_checkout_vanishes_mid_sleep`).

## Why

Root cause, 5-Whys chain (per `incident-response-rca-method-selection`
skill guidance — a single linear causal path fits a 5-Whys chain; no
second chain for a detection/response delay, because the user caught
this live via the Monitor channel, not late):

1. Why did every role's patrol check crash (rc=2) in one tick? — Each
   crashed subprocess was `python3 "${CHECKOUT}/gates/patrol_promote.py"
   run ...`, one per configured role, and `python3` itself failed to
   open that path.
2. Why did `python3` fail to open a path that normally exists? —
   `${CHECKOUT}` momentarily pointed at a directory that did not exist
   on disk.
3. Why did `CHECKOUT` point at a missing directory? — `CHECKOUT` is
   resolved exactly once, at Monitor-session startup
   (`poll_rearm_resolve_checkout`, on-the-record/hooks/poll-rearm.sh),
   and never re-resolved per tick; `claude plugin marketplace update
   tokenmaxxxer` running mid-session does a stale-directory cleanup
   *and* re-clone of that same directory, so there is a window where the
   path is physically absent.
4. Why did a momentarily-missing path fail 43 times instead of once? —
   The (pre-fix) patrol block looped over every role in
   `POLL_HEARTBEAT_PATROL_ROLES` (`spawn.ROLES`, 43 entries) and
   launched one subprocess per role, unconditionally, outside the
   `due_rc` gate — with no check that `CHECKOUT` still exists before
   spawning any of them.
5. Why was there no such check? — The loop was built (issue #1598/#1722)
   assuming `CHECKOUT`, once resolved at startup, stays valid for the
   Monitor's lifetime.

canonical: `on-the-record/monitors/poll-heartbeat.sh:54` (`CHECKOUT="$(poll_rearm_resolve_checkout ...)"`,
once, before the `while true` loop at line 185); `on-the-record/hooks/poll-rearm.sh:19-29`
(`poll_rearm_resolve_checkout`'s own docstring: resolve-once-per-caller
contract shared verbatim between `directive.sh` and `stop-poll-rearm.sh`,
and by extension this script); `on-the-record/monitors/poll-heartbeat.sh:169-183`
(`POLL_HEARTBEAT_PATROL_ROLES` populated once from `spawn.ROLES`, before
the loop); canonical: acceptance: `python3 -c "import sys;
sys.path.insert(0,'.'); import spawn; print(len(spawn.ROLES))"` — result:
`43`.

Primary cause: the missing existence guard in the patrol tick (point 4
above), fixed directly. Contributing, systemic factors (not separately
fixed, listed for context): (a) `CHECKOUT` is resolve-once/cache-for-session
by design, so any future addition to this loop inherits the same
staleness risk unless it re-checks; (b) the patrol block was written to
run unconditionally outside the `due_rc` gate (issue #1598) specifically
so a `poll-due` crash could never silently swallow patrol trace lines —
a reasonable tradeoff on its own, but it also meant the patrol block
never benefited from any degrade-on-crash handling the due branch might
grow.

Two things the issue asked to confirm, canonical: `gates/patrol_wiring.py:29-31`
(`MAX_ROLES_PER_MERGE = 3`), `gates/patrol_wiring.py:82-96` (`run()`'s
capped role loop calling `spawn.judge_cmd`), `on-the-record/monitors/poll-heartbeat.sh:402-409`
(issue #1598 comment: patrol block runs unconditionally, outside the
`due_rc` gate), `gates/patrol_promote.py:262-288` (`run_patrol_promote`:
reads the board issue and returns early unless a checkbox was freshly
ticked — no `gh` write on a quiet tick):

- **Which poll path produced the burst**: `on-the-record/monitors/poll-heartbeat.sh`'s
  own Monitor-driven `patrol_tick` cadence (`POLL_HEARTBEAT_PATROL_EVERY_N`),
  not `gates/patrol_wiring.py`'s merge-seam entry point. They are separate
  code paths with separate role lists (`spawn.ROLES`, all 43, vs.
  `patrol_wiring._known_roles()` capped at `MAX_ROLES_PER_MERGE=3` hits).
- **43-per-tick is intended, not a cap regression**: `patrol_wiring.py`'s
  cap protects `spawn.judge_cmd`, an expensive Haiku-prefiltered judge
  run, invoked once per merge. The Monitor's patrol tick instead calls
  `gates/patrol_promote.py`, a cheap board-state read/tick-detect that
  only reaches a `gh` write when a checkbox was actually ticked — sweeping
  all 43 roles on a slow, fixed cadence (`patrol_every_n`, default every
  5th ~2min tick) costs one cheap read per role, not one judge run per
  role. Documented in-code (both directives now live next to their
  respective loops) so the two caps are never conflated or unified later.

## Upstream basis

Issue #2163 itself (the live finding pasted into the issue body) is the
only upstream input — build-now bypass (contract v3 s19a, `CORE_BUILD_NOW=1`
set by the spawner) skipped the phase-1 proposal round, so there is no
`docs/issue-2163/proposals/*` file to cite. Root cause was derived
directly from reading `on-the-record/monitors/poll-heartbeat.sh`,
`on-the-record/hooks/poll-rearm.sh` (`poll_rearm_resolve_checkout`),
`gates/patrol_promote.py`, and `gates/patrol_wiring.py` in this session
(citations above), cross-checked against existing tests in
`on-the-record/monitors/test_poll_heartbeat.py` (the `_run_patrol_tick`
fixture, issue #1722) and `gates/test_patrol_wiring.py` (the
`MAX_ROLES_PER_MERGE` cap test). Both changed files land in this same
commit, so `sha: same-commit` for both.

Scout/survey: skipped under the mandatory pure-bugfix skip condition
(scout-directive and survey-order-directive both name this as one of the
two exceptions). canonical: `on-the-record/monitors/poll-heartbeat.sh:188-209`
(guard clause), `on-the-record/monitors/poll-heartbeat.sh:410-419` (doc
comment) — the change is a single existence guard plus a documentation
comment inside one existing function, not a new component with an open
design/product decision.

## Doc placement ladder

- [x] `docs/specs/` — not applicable; no system design changed.
- [x] `docs/decisions/` — not applicable; no hard-to-reverse choice was made
  (the guard reuses an existing, already-trusted existence check).
- [x] `docs/reports/` — not applicable; no cross-cutting measurement produced.
- [x] This implementation record — filled (this file).

## What did not work

- Expected: the first in-code comment I added next to the patrol block
  (documenting the intentional uncapped-by-design behavior, acceptance
  check 2) would insert cleanly as its own paragraph. What actually
  happened: my first edit inserted it in the middle of an existing
  multi-line comment sentence (issue #1598's "folding patrol emission
  into the due-gated report would / silently drop promotion trace lines
  on exactly those ticks)" continuation), splitting it across two
  unrelated comments. Caught before running any test — re-edited to move
  the new comment after the original sentence's closing parenthesis.

## Open findings

- The guard checks `[ ! -f "${CHECKOUT}/spawn.py" ]` — file existence,
  not file integrity. A theoretically tighter race (spawn.py present but
  mid-write / zero-byte during git's checkout phase) is not covered.
  Resolution path: not fixed here because the reported burst matches a
  full "path absent" window (rm-then-clone), not a partial-write race;
  if a future report shows the tighter race actually firing, extend the
  guard (e.g. a byte-size or `git status` check) then.
- Acceptance's literal reproduction step ("trigger `claude plugin
  marketplace update tokenmaxxxer` while a patrol poll tick is due") was
  not run live in this session — that command mutates this session's own
  plugin marketplace checkout, a shared/hard-to-reverse action outside
  this issue's write set. Instead,
  `t_patrol_tick_skips_when_checkout_vanishes_mid_sleep` reproduces the
  same underlying condition (CHECKOUT physically absent mid-tick) under
  full test isolation. Resolution path: if a live-environment
  reproduction is still wanted, it needs a separate, explicitly
  authorized session (it is a destructive/shared action, not a code
  change).

## Next steps

None — `loop_state: landed` (terminal for a `coding-record`): the fix,
regression test, and this record are committed, pushed, and carried in
the phase-2 delivery PR for issue #2163.

## Acceptance evidence

Executed in this session, from the repo root.

canonical: acceptance: `bash -n on-the-record/monitors/poll-heartbeat.sh && echo "SYNTAX OK"` — result:
```
SYNTAX OK
```

canonical: acceptance: `python3 on-the-record/monitors/test_poll_heartbeat.py` — result:
```
ok  t_board_sweep_lock_skip_treated_as_no_change
ok  t_heartbeat_arms_watchdog_when_due
ok  t_heartbeat_attaches_on_board_repo
ok  t_heartbeat_bound_with_no_returned_pr_emits_nothing
ok  t_heartbeat_bound_with_returned_pr_emits_only_those_lines
ok  t_heartbeat_orchestrate_off_alone_still_stops_monitor
ok  t_heartbeat_refuses_to_arm_on_non_git_root
ok  t_heartbeat_respects_kill_switch
ok  t_heartbeat_respects_monitor_only_kill_switch
ok  t_heartbeat_skips_attachment_on_non_board_repo
ok  t_heartbeat_skips_watchdog_when_not_due
ok  t_heartbeat_surfaces_empty_roster_report
ok  t_heartbeat_surfaces_induced_dead_poller
ok  t_patrol_crashed_role_tick_still_prints_summary_line
ok  t_patrol_kill_switch_still_prints_disabled_line_only
ok  t_patrol_promotion_tick_still_prints_summary_line
ok  t_patrol_quiet_tick_with_roles_emits_no_summary_line
ok  t_patrol_tick_skips_when_checkout_vanishes_mid_sleep
ok  t_patrol_wiring_does_not_alter_heartbeat_tick_or_rearm_behavior
ok  t_returned_pr_new_item_emits_on_due_tick
ok  t_returned_pr_unchanged_set_produces_no_output_on_due_tick
ok  t_unkeyed_line_content_change_still_emits
ok  t_unkeyed_line_insertion_suppresses_unchanged_lines_below

23/23 passed
```

canonical: acceptance: `python3 -m pytest gates/test_patrol_wiring.py gates/test_patrol_promote.py -q` — result:
```
......................                                                   [100%]
22 passed in 1.05s
```

## Skill check

skill-verdict: incident-response-rca-method-selection — applied: invoked; used to choose the RCA method for this record's `## Why` section (single linear 5-Whys chain, no second detection-delay chain since the burst was caught live).
skill-verdict: implementation-complexity-coupling-management — not-applicable: no class/module coupling or cohesion threshold, cross-module import direction, or check-pipeline ordering was in play; the fix is one existence guard inside an existing loop.
skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-pattern decision was on the table; the fix is a plain guard clause.
skill-verdict: implementation-performance-data-structure-choice — not-applicable: no data structure, algorithm, or communication-scheme choice was made; the fix skips subprocess spawns entirely rather than choosing among structures.
skill-verdict: implementation-blueprint — not-applicable: the change is a small, single-file guard clause plus one test, not a new multi-module structure needing a frozen contract.
