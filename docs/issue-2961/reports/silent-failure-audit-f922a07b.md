---
issue: 2961
role: silent-failure-audit-f922a07b
author: silent-failure-audit-f922a07b
skills: silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: pipeline.py, spawn.py, directive_assembly.py, runaway_backstop.py, runaway_signal.py
    sha: 58b22de88de3e0dd0b6f5680f5e02b78bfe11c1c
---

# issue-2961 — silent-failure-audit-f922a07b record

## What was done

Narrow follow-up on PR #2964 (issue #2961, turn-cap removal + wall-clock/
token backstops): both independent verifiers of that PR (#2971, #2975)
found that `pipeline.py:687` claimed the backstops are "enforced by the
watchdog poll loop," which is false as shipped —
`runaway_backstop.backstop_verdict()` has zero production callers and
`watchdog.py` never references it. PR #2964's own record already
disclosed this gap honestly in its "Open findings" section; the code
comment asserted the opposite.

canonical: task text of this session, quoting PR #2971/#2975's finding
verbatim (pipeline.py:687's claim vs the confirmed absence of a caller)

Searched every comment/docstring in the tree that describes the
backstops and corrected each one making the same or a related claim
(that a caller exists, that the backstops actively bound/end a session,
or that the watchdog poll loop enforces them), without adding an
enforcing caller or touching the observe-only signal's behavior:
derived: `grep -rn "backstop" --include=*.py . | grep -v "/tests/\|test_"` (before the fix, to enumerate every site) — result:
```
runaway_signal.py:13:wall-clock/token-cost backstops in `runaway_backstop.py` are the only
directive_assembly.py:29:import runaway_backstop
directive_assembly.py:121:# the actual worst-case bound is runaway_backstop.py's wall-clock/token
directive_assembly.py:122:# backstops.
directive_assembly.py:171:# bound the worst case (runaway_backstop.py), and serial exploration
directive_assembly.py:176:    f"{runaway_backstop.WALL_CLOCK_BACKSTOP_MS // 60_000}분, 누적 토큰 "
directive_assembly.py:177:    f"{runaway_backstop.TOKEN_COST_BACKSTOP_TOKENS // 1_000_000}백만 "
directive_assembly.py:178:    "토큰(runaway_backstop.py) — "
runaway_backstop.py:1:"""Wall-clock and token/cost backstops (issue #2961).
runaway_backstop.py:6:two backstops do, each independently (either alone is sufficient — this
runaway_backstop.py:16:max 13.73 / p99 12.99. Each backstop below is 1.5x the observed max,
runaway_backstop.py:64:def backstop_verdict(elapsed_ms: float, events: list[dict]) -> dict:
runaway_backstop.py:65:    """Both backstops evaluated independently; `terminate` is true when
pipeline.py:687:    # now `runaway_backstop.py`'s wall-clock/token backstops, enforced by
pipeline.py:1751:    worst-case bound anymore, since `runaway_backstop.py`'s wall-clock/
pipeline.py:1752:    token backstops apply unconditionally to every spawn regardless of
gates/spawn_on_pr.py:146:# issue #2238 item 2: a second, independent backstop. Even with a correct
spawn.py:2332:    # ever passed a turn ceiling anymore — the wall-clock/token backstops
spawn.py:2333:    # in runaway_backstop.py bound the worst case instead), so the
```
`gates/spawn_on_pr.py:146` is an unrelated backstop (a different,
pre-existing mechanism, #2238) and was not touched.

Five files edited (all at commit `58b22de8`, see frontmatter):
1. `pipeline.py` — both occurrences, including the exact flagged line
   (`pipeline.py:687`, `spawn_cmd()`'s comment) and
   `_admission_check_budget_caps()`'s docstring (`pipeline.py:1748-1755`,
   which claimed the backstops "apply unconditionally to every spawn").
2. `spawn.py` — the `--allow-unlimited-turns` argparse help comment
   (`spawn.py:2331-2334`), which claimed the backstops "bound the worst
   case instead" as settled fact.
3. `directive_assembly.py` — two comments (`DEFAULT_SESSION_TURN_GUIDANCE`'s
   definition and the `_TURN_BUDGET_PROSE` derivation comment above it).
   The `_TURN_BUDGET_PROSE` string itself (the Korean text materialized
   into spawned sessions' `turn-budget.md`) was deliberately left
   untouched: it is runtime session-facing content, not a comment or
   docstring, and rewording what spawned sessions are told about their
   own backstops is a separate, larger disclosure decision than this
   narrowly-scoped comment/docstring fix — out of scope per the task.
4. `runaway_backstop.py` — the module docstring and `backstop_verdict()`'s
   own docstring, which had the most direct false claim: "the caller (the
   watchdog poll loop) is what actually kills the process."
5. `runaway_signal.py` — the module docstring's claim that the backstops
   "are the only things in this slice that actually end a session."

acceptance: `grep -rn "max-turns\|DEFAULT_SESSION_MAX_TURNS" spawn.py pipeline.py directive_assembly.py; echo rc=$?` — result:
```
rc=1
```
acceptance: `python3 -m pytest tests/ -k backstop -q` — result:
```
.....                                                                    [100%]
5 passed in 0.83s
```
acceptance: `python3 -m pytest tests/ -k runaway_signal_observe_only -q` — result:
```
....                                                                     [100%]
4 passed in 0.84s
```
acceptance: `python3 -m pytest tests/ -k runaway_signal_discrimination -q` — result:
```
...                                                                      [100%]
3 passed in 0.82s
```
acceptance: `python3 -m pytest tests/ -k subagent_in_flight -q` — result:
```
...                                                                      [100%]
3 passed in 0.82s
```
All five of issue #2961's own Acceptance checks, verbatim, re-run live
against this fix (`runaway_signal_observe_only` shows 4 passed rather
than PR #2964's originally-recorded 3 — pre-existing from that PR's own
`test-derivation` mixed-batch-test addition, not caused by this fix;
this session did not touch `runaway_signal.py`'s tests or behavior).

derived: `python3 -m pytest tests/ -q` (full regression sweep) — result:
```
1 failed, 70 passed in 6.04s
FAILED tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present
```
Confirmed pre-existing and unrelated to this fix:
derived: `git stash && python3 -m pytest tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present -q; git stash pop` — result:
```
1 failed in 0.79s
FAILED tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present
AssertionError: 4 not greater than 4
```
(identical failure with this fix's changes stashed out — predates this delivery.)

## Why

The gap between the PR record's honest disclosure ("Open findings" item
1: no live enforcement caller exists) and the code comment's false claim
("enforced by the watchdog poll loop") is a genuine defect: a future
reader of `pipeline.py` alone, without reading the record, would believe
a runaway session is bounded today when it is not. Both independent
verifiers flagged it as blocking-quality despite confirming the rest of
the delivery. The fix scope is deliberately narrow — correct every
false/misleading claim about enforcement status, add nothing that
enforces, and leave the observe-only signal's behavior and the CLI's
turn-flag removal untouched — because wiring an actual enforcing caller
into the watchdog poll loop is its own design decision (PR #2964's
record already scoped that out as "Open findings" item 1, and PR #2964's
own "What did not work" section shows a prior attempt at wiring it into
`roster_watchdog()` was reverted specifically because that function is
documented observe-only).

## What did not work

None — the fix was a direct, narrowly-scoped text correction; no
approach was attempted and abandoned.

## Upstream basis

PR #2964 (branch `issue-2961/observability-methodology-selection+test-derivation-27c16f97`)
is the code this fix corrects; its own record is
`docs/issue-2961/reports/observability-methodology-selection+test-derivation-27c16f97.md`
(present on that PR's branch, not merged to main yet, so not present in
this tree). The two independent-verification PRs that surfaced the
finding are PR #2971 (branch `issue-2961/adversarial-review-fb462020`)
and PR #2975 (branch `issue-2961/adversarial-review-225e111b`); their
records likewise live only on their own open-PR branches, not in this
tree:
canonical: `gh pr view 2971 --json body` / `gh pr view 2975 --json body` — both bodies quote the same `pipeline.py:687` finding this fix addresses.
The fix commit itself, `58b22de8`, was built directly on top of PR
#2964's branch tip (`03e0b2ff`) so the corrected files exist in the same
tree; this session's own branch
(`issue-2961/silent-failure-audit-f922a07b`) was then reset to that same
commit so the PR opened from it carries the identical fix diff.

## Open findings

None new. PR #2964's own "Open findings" items (no live enforcement
caller; `consult.py`/`bench/ablation.py` still use `--max-turns`; dead
`_resolve_wrap_up_allowance_turns()`) are unchanged by this fix — this
delivery corrects only comment/docstring truthfulness, per the task's
explicit "Fix ONLY that discrepancy" scope.

## Next steps

`loop_state: landed` — this record is terminal. The follow-up path for
actually enforcing the backstops (item 1 in PR #2964's "Open findings")
remains a separate future issue, as it was before this fix.

skill-verdict: silent-failure-audit — not-applicable: this task is a
comment/docstring truthfulness correction on an already-shipped module,
not an audit of error-handling paths (try/catch, promise rejection,
error callback, result type) for silently-absorbed failures; no new or
existing error-handling code was touched or reviewed.
other mounted skills: not triggered (work-in-english governs language
only, applied silently throughout; prose-modes was not invoked since
this record's own prose was assembled directly, not drafted-then-revised).
