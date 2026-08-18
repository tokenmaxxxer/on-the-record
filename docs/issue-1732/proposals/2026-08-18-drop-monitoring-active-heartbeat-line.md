---
status: proposed
files:
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/monitors/test_poll_heartbeat.py
---

Skip condition: pure bugfix (scout-directive skip condition) — issue #1732 states `validity-consult-skip: trivial` and `design-research-skip: mechanical`, and the fix is fully specified by the issue's own Acceptance section plus the existing delta-diff/returned-pr logic (see docs/issue-1732/reports/implementation/survey.md). No design decision is open; scouting/full survey round skipped accordingly (survey.md still written, per survey-order-directive, to record the concrete write set).

## Request
`on-the-record/monitors/poll-heartbeat.sh`'s delta-diff heredoc (#1220/#1719) emits `[heartbeat] monitoring active, N session(s) tracked, no changes` every time a due tick crosses the 1800s `last_emit_epoch` bound with nothing else to report, waking the orchestration session for a full model turn with no actionable content — monitor liveness is already covered by the separate alive marker (`poll-heartbeat.sh:105-114`). Drop that line. Keep the `returned-pr:` re-surfacing #1719 req#1 attached to the same bound (those name an undisposed PR the operator must act on). When there are no `returned-pr:` lines to re-surface, the bound must emit nothing at all and leave `last_emit_epoch` untouched, so a fully idle repo produces zero session wakes.

## Constraints
- The line-keyed diff logic above the bound (`TAG_RE`/`ENTRY_RE`/`BULLET_RE`/`ALWAYS_RE`/`AGE_STRIP_RE`, the `to_emit` computation) stays byte-for-byte unchanged — only the `to_emit`-empty/bound branch changes.
- The `returned-pr:` age-normalized comparison and re-surfacing behavior #1719 built (`AGE_STRIP_RE`, the `returned-pr:` branch in the `changed` computation) is untouched; this proposal only changes what happens with the resulting `returned-pr:` lines once the bound fires.
- `last_emit_epoch` semantics stay keyed off `emitted_now` exactly as today (`new_state = {..., "last_emit_epoch": now if emitted_now else prev.get("last_emit_epoch", 0)}`, poll-heartbeat.sh:343) — no new state field, no change to how `last_emit_epoch` advances on a non-empty `to_emit` tick.

## Rationale
Two ways to stop the bound from always emitting the heartbeat line were considered:
1. **Chosen**: delete the `heartbeat_lines`/`healthy` construction entirely and, inside the same `if now - last_emit_epoch >= 1800:` guard, collect just the `returned-pr:`-keyed lines from `curr`; write them (and set `emitted_now = True`) only when that list is non-empty. When it's empty, the branch does nothing, so `emitted_now` stays `False` and the existing `new_state` line (poll-heartbeat.sh:343) leaves `last_emit_epoch` untouched with no separate code change needed there.
2. **Rejected**: keep emitting a heartbeat-shaped line but only when `healthy == 0` (i.e., collapse it to a "nothing tracked" signal instead of removing it outright). Rejected because the issue's Acceptance section is explicit that a no-returned-pr bound tick must write nothing to stdout at all, not a different, rarer line — any residual periodic line reintroduces the same "session wakes with nothing to report" problem the issue exists to remove, just at a lower duty cycle. The alive marker (`poll-heartbeat.sh:105-114`, read by `directive.sh`) already covers liveness detection without needing a Monitor-visible echo.

## What will be done
- `on-the-record/monitors/poll-heartbeat.sh:326-341`: replace the `to_emit`-empty branch's unconditional `heartbeat_lines` construction with a guard that collects `returned-pr:`-keyed lines from `curr` and writes them only if the list is non-empty, setting `emitted_now = True` only in that case. The `healthy` computation is deleted along with the heartbeat f-string; the surrounding `if now - last_emit_epoch >= 1800:` bound check and the `new_state` write (line 343) are unchanged.
- `on-the-record/monitors/test_poll_heartbeat.py`: add two tests exercising the bound directly, reusing the existing `_run_tick(checkout, home, report)` two-tick harness (#1719) plus a new small helper that rewrites `runs/poll_heartbeat_last_state.json`'s `last_emit_epoch` between the two ticks (the bound cannot be crossed by real wall-clock waiting in a test) — one asserting an unchanged report with no `returned-pr:` lines produces empty stdout on the bound tick and leaves `last_emit_epoch` at the forced value, the other asserting an unchanged report carrying a `returned-pr:` line emits exactly that line (and no `monitoring active` text) on the bound tick.
- Paste the required Acceptance-check outputs (the `grep -n "monitoring active"` empty result, and the `python3 -m pytest monitors/test_poll_heartbeat.py gates/test_poll_heartbeat_delta.py gates/test_poll_heartbeat_patrol.py` run) into `docs/issue-1732/reports/implementation.md` once phase 2 executes.

## Accumulation
This is a single conditional-branch rewrite inside one existing heredoc block plus two new tests reusing an existing test harness — not a repeated per-entry or per-file pattern. The heartbeat-line construction has exactly one call site (the bound branch cited above); no other code path builds or reads a `"[heartbeat] monitoring active"`-shaped string.

## Out of scope
- Any change to the `to_emit` line-keyed diff logic, the always-emit category (`ALWAYS_RE`), or the `returned-pr:` age-normalized comparison itself.
- Any change to the alive-marker mechanism (`poll-heartbeat.sh:105-114`) or `directive.sh`'s staleness read of it.
- `docs/handbooks/monitor-liveness.md` — its existing "Quiet ticks" prose already describes the post-fix contract accurately (survey.md) and names no env var/config key/dependency/migration/setup step that would need updating per the doc-placement ladder.
- Historical records under `docs/issue-1220/**` and `docs/issue-1719/**` that name the current heartbeat line in past-tense prose describing prior state — those are frozen records, not live documentation.

## How you'll know it worked
The issue's four Acceptance checks, run against the PR branch:
- a `_run_tick`-driven bound tick with an unchanged report and no `returned-pr:` entries writes nothing to stdout
- a `_run_tick`-driven bound tick with an unchanged report and one or more `returned-pr:` entries emits exactly those lines and no `monitoring active` text
- `grep -n "monitoring active" on-the-record/monitors/poll-heartbeat.sh` prints nothing
- `python3 -m pytest monitors/test_poll_heartbeat.py gates/test_poll_heartbeat_delta.py gates/test_poll_heartbeat_patrol.py` (run from `on-the-record/`, or the equivalent repo-root-relative paths) passes, with the pre-existing macOS `flock: command not found` failure in `t_patrol_wiring_does_not_alter_heartbeat_tick_or_rearm_behavior` shown to fail identically on `main`
