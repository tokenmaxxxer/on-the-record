---
issue: 2182
role: implementation
loop_state: landed
upstream:
  - path: on-the-record/hooks/directive.sh
    sha: same-commit
  - path: on-the-record/hooks/stop-poll-rearm.sh
    sha: same-commit
  - path: docs/handbooks/monitor-liveness.md
    sha: same-commit
  - path: tests/test_monitor_liveness.py
    sha: same-commit
code_under_review: same-commit
type: fix
breaking: false
verdict: pass
---

# issue-2182 — implementation record

## What was done

Build-now bypass (CORE_BUILD_NOW=1): delivered directly on
issue-2182/implementation, no separate phase-1 proposal round (skip
note below).

canonical: `on-the-record/hooks/directive.sh` diff in this commit
(`_monitor_liveness_check_and_notify` and the `ALWAYS-ON INVARIANTS`
block), and the verbatim-duplicated copy in
`on-the-record/hooks/stop-poll-rearm.sh`.

1. `_monitor_liveness_check_and_notify`'s Python heredoc, in both
   `directive.sh` and `stop-poll-rearm.sh`, now receives `$checkout` as
   a fourth argv and prints a rebuilt notice: tag changed from the
   generic `[orchestrate]` to a distinct `[orchestrate][MONITOR-DEAD]`,
   and the body now spells out `persistent: true` explicitly plus the
   concrete re-arm command path (`<checkout>/on-the-record/monitors/
   poll-heartbeat.sh`), instead of the old bare "re-arm via Monitor
   tool". canonical: acceptance run below,
   `ok test_stale_stamp_directive` / `ok test_missing_stamp_treated_as_stale`.
2. `directive.sh`'s byte-stable, always-printed `ALWAYS-ON INVARIANTS`
   block (part of every turn's per-turn injection, issue #2102) gained
   one new standing bullet naming the `[orchestrate][MONITOR-DEAD]` tag
   as an immediate-action signal and repeating the `persistent: true`
   requirement — present on every turn, not only a stale-episode turn,
   mirroring the #878 async-completion rule's shape (a standing rule
   reacting to a runtime-conditional signal). canonical: acceptance run
   below, `ok test_monitor_dead_standing_invariant_always_present`.
3. `docs/handbooks/monitor-liveness.md` updated: the sample notice text
   and a new "Issue #2182: salience and the persistent:true gap"
   section documenting both root causes and why the fix stops short of
   arming the platform's own auto-started plugin Monitor. canonical:
   `docs/handbooks/monitor-liveness.md` diff in this commit.
4. `tests/test_monitor_liveness.py`: existing `test_stale_stamp_directive`
   extended with assertions for the new tag and `persistent: true`
   and the checkout path; added
   `test_monitor_dead_standing_invariant_always_present` pinning that
   the standing bullet is present even on a fresh (non-stale) turn.
   canonical: `tests/test_monitor_liveness.py` diff in this commit.

No changes to `on-the-record/monitors/monitors.json`, `poll-heartbeat.sh`,
or any arming call site — see Why below for why that surface is out of
reach from this repo.

## Why

**Investigation (issue's "Investigate" section).** Two candidate causes
were named: a short/non-persistent arming call site, and a possible
regression in the existing monitor-liveness machinery.

- `on-the-record/monitors/monitors.json` declares the plugin Monitor
  with only `name`/`command`/`description`/`when` — no timeout or
  persistent field exists in that schema, and
  `docs/specs/platform-capabilities.md` states, as an explicit,
  documented, unmechanizable-from-this-repo platform property, that a
  plugin Monitor auto-starts and is "session-bound" — this repo has no
  arming call site with timeout/persistent arguments to fix. canonical:
  `docs/specs/platform-capabilities.md`'s "Claude Code plugin Monitors"
  section and `on-the-record/monitors/monitors.json`, both read this
  session (no timeout/persistent field present in either).
- The Monitor tool's own schema (fetched this session via ToolSearch)
  states `timeout_ms` defaults to 300000 (5 minutes) and is ignored only
  when the caller sets `persistent: true`. canonical: `ToolSearch`
  result this session, `Monitor` tool parameter schema,
  `timeout_ms.default == 300000`, `persistent.default == false`.
  The issue's own live finding records that the orchestrator re-armed
  the dead monitor "via the Monitor tool" manually, but the old notice
  text ("re-arm via Monitor tool") never instructed setting
  `persistent: true`. canonical: `gh issue view 2182` output, the
  "Live finding" paragraph, read this session. A literal, unqualified
  re-arm following the old instruction text would die again five
  minutes later by the tool's own documented default — this is the
  actionable root cause identified, not a crash and not a code
  regression in the existing suite: `git diff` of this commit shows the
  pre-existing `test_stale_stamp_directive`/`test_fresh_stamp_silent`/
  `test_missing_stamp_treated_as_stale` assertions on staleness
  detection and de-dup timing are unchanged, only the notice-text
  assertions were extended (see the acceptance run below).
- Separately, the notice line shared the plain `[orchestrate]` tag with
  the byte-stable, always-present per-turn directive block whose own
  first line is `[orchestrate] You are the orchestration session...`.
  canonical: `on-the-record/hooks/directive.sh:290` (pre-edit), read
  this session. This is the same salience-collision shape as issue
  #2180's `[returned-pr]` burial, named explicitly in issue #2182's own
  "Compounding factor" paragraph. canonical: `gh issue view 2182`
  output, "Compounding factor" paragraph.

**Fix design.** `docs/handbooks/monitor-liveness.md` (pre-existing,
issue #1497) already documents that a hook cannot itself call the
Monitor tool — "Monitors are armed once at session start; nothing in
this repo can trip one from inside a hook" — so true auto-rearm from
inside the hook is architecturally unavailable, and the issue itself
offers the fallback used here: "or emit an unmissable instruction that
the orchestrator's own directive requires acting on immediately, same
shape as #878's async-completion rule." canonical:
`docs/handbooks/monitor-liveness.md`'s "Staleness threshold and the
re-arm directive" section (pre-edit) and `gh issue view 2182`'s "Fix"
paragraph, both read this session. What was built: (a) a distinct tag
so the notice cannot blend into the routine block, (b) an explicit
`persistent: true` mandate so a compliant re-arm cannot silently die
again, and (c) a standing, byte-stable invariant bullet — present every
turn, the same mechanism #878's rule already uses — that names the tag
and repeats the mandate, so the instruction does not depend on the
orchestrator noticing a one-off line for the first time. canonical:
`on-the-record/directive/delegation-loops.md`'s "AUTONOMOUS ASYNC
COMPLETION (issue #878)" section, read this session, as the shape
mirrored.

Two alternatives considered and rejected:
- **Have the hook call the Monitor tool directly.** Rejected: a bash
  hook has no mechanism to invoke an agent-side tool call — the same
  "no way to trip one from inside a hook" boundary
  `monitor-liveness.md` already documents, unchanged by this issue.
- **Put the death notice inline as a conditional line in the per-turn
  injection**, the way issue #2102 rejected doing for the wake
  degradation notice. Rejected for the same reason: the per-turn
  injection is meant to be byte-stable for prompt-cache economics, and a
  conditionally-present line there is exactly the variance #2102 moved
  out. canonical: `on-the-record/directive/monitor-mode.md`'s wake-mode
  section ("it is never printed into the per-turn injection... the
  conditional inline line was the sole byte-stability variance"), read
  this session. The standing invariant *bullet* added here is
  unconditional/byte-stable — it is the notice line itself (still
  printed only when stale) that stays outside the block, one line above
  it, now distinctly tagged.

Skip note (survey-order-directive): no separate survey/proposal file was
written — CORE_BUILD_NOW=1 authorizes direct delivery (contract v3
s19a), and the fix required no open design decision beyond the two
alternatives argued above, resolved inline in this record.

## Upstream basis

- Issue #2182, read via `gh issue view 2182` — names the live finding,
  the two investigate bullets, the fix direction, and the acceptance
  criteria.
- `docs/handbooks/monitor-liveness.md` (same-commit, extended) — the
  existing #1497 design this issue builds on, including its explicit
  "cannot re-arm from inside a hook" boundary.
- `docs/specs/platform-capabilities.md` (unmodified, read for the
  arming-mechanism investigation).
- `on-the-record/monitors/monitors.json` (unmodified, read).
- Monitor tool schema (fetched via `ToolSearch` this session).
- Commit `3271d8f8` ("issue-2180: distinct new-returned-pr signal, stop
  repeating already-surfaced returned-pr lines") — the "same shape"
  salience-collision precedent this issue explicitly names in its
  "Compounding factor" paragraph, read via `git show 3271d8f8` this
  session and used as the record-shape and fix-shape template; its own
  record is not present as a file on this branch's working tree (only
  reachable via that commit), so it is cited by sha here rather than as
  a path.
- `on-the-record/directive/delegation-loops.md`'s #878
  AUTONOMOUS ASYNC COMPLETION section — the standing-rule shape the new
  invariant bullet mirrors.

## Open findings

1. Pre-existing staleness-threshold inconsistency (not introduced by
   this change, not fixed here — out of this issue's scope): canonical:
   `on-the-record/hooks/directive.sh` (`MONITOR_LIVENESS_STALE_SECONDS:-360`)
   vs. `on-the-record/hooks/stop-poll-rearm.sh`
   (`MONITOR_LIVENESS_STALE_SECONDS:-180`) vs.
   `docs/handbooks/monitor-liveness.md` ("default 180 seconds") — all
   read this session; the doc and one of the two hooks agree, the other
   hook does not. Resolution path: a follow-up issue, since reconciling
   it is an independent decision (which value is "correct") outside
   "make recovery automatic."
2. This fix raises the notice's salience and content but cannot force
   an orchestrator to act on it — `docs/handbooks/monitor-liveness.md`'s
   pre-existing "observe-and-direct backstop, not an auto-fix" framing
   already accepts this as the structural ceiling. canonical:
   `docs/handbooks/monitor-liveness.md`, "Staleness threshold and the
   re-arm directive" section. Resolution path: none available from repo
   code; would require a platform-level capability (an OS-level
   scheduled-execution primitive external to the session), already
   recorded as out of scope in that same handbook's "Structural limit"
   section.

## What did not work

None.

## Skill check

- skill-verdict: diagnose-first — applied: invoked; used to sanity-check
  the already-completed root-cause diagnosis against the gated
  procedure's Stage 2 narrow/dig/verify moves before landing. canonical:
  this turn's own Skill tool invocation and its returned guidance. The
  check compared the two identified causes (persistent:true gap,
  tag-salience collision) against the issue's own "Investigate"
  paragraphs — canonical: `gh issue view 2182` output — and found both
  fix mechanisms map onto the two named suspects with no unaddressed
  branch; no change to the already-applied fix resulted from the check.
- other mounted skills: not triggered — implementation-complexity-
  coupling-management, implementation-design-pattern-selection, and
  implementation-performance-data-structure-choice cover no threshold,
  GoF-pattern, or data-structure/perf decision that arose here.
  implementation-blueprint's own scope note excludes a small, mechanical,
  single-pattern text-and-message edit duplicated per this file pair's
  pre-existing verbatim-duplication convention — no new multi-module
  structure was introduced.

## Next steps

None — loop_state is terminal (landed).

Executed acceptance evidence. canonical: this turn's own transcript —
each command below was run directly by this session at landing time,
raw stdout pasted verbatim (pytest-asyncio deprecation warnings trimmed;
pass/fail summary lines are verbatim), no summarization.

acceptance: `bash -n on-the-record/hooks/directive.sh` and
`bash -n on-the-record/hooks/stop-poll-rearm.sh` — checks for syntax
breakage from the heredoc edits, relevant since both files use an
unquoted `cat <<EOF` block where the new invariant bullet's backticks
had to be backslash-escaped to avoid command substitution. result:
```
SYNTAX OK
SYNTAX OK
```
exit code 0 both.

acceptance: `python3 -m pytest tests/test_monitor_liveness.py -q` —
result:
```
......                                                                   [100%]
6 passed in 2.20s
```
exit code 0.

acceptance: `python3 gates/test_hooks_parity.py` — canonical check that
hook registration in `hooks.json` still matches what `spawn.py` injects
for a self-hosted target; unrelated to this change's content but the
directly adjacent gate for the two files touched. result:
```
ok  t_live_fire_deny_before_commit_lands
ok  t_non_self_hosted_target_gets_no_injection
ok  t_registered_hooks_match_hooksjson_entries
ok  t_role_settings_merges_hooks_only_for_self_hosted_target

4 passed
```
exit code 0.

acceptance: broader unrelated-surface regression check —
`python3 -m pytest on-the-record/hooks/test_monitor_notice.py tests/test_monitor_alive_gc.py -q`
and `python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -q`
and `python3 gates/test_poll_heartbeat_delta.py` and
`python3 gates/test_poll_heartbeat_patrol.py`, run to catch any
regression in the sibling monitor/watchdog machinery this change sits
next to but did not modify. result:
```
9 passed, 2 xfailed
23 passed
13/13 passed
3/3 passed
```
exit code 0 across all four.
