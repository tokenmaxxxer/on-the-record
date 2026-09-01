---
issue: 2961
role: silent-failure-audit-90a13b9f
author: silent-failure-audit-90a13b9f
skills: silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: directive_assembly.py
    sha: dd5578ad9ad5f75f4d7cc43d942c43e184d32ba4
---

# issue-2961 — silent-failure-audit-90a13b9f record

## What was done

Third pass on issue #2961's turn-cap removal (PR #2964) / backstop
comment-truthfulness follow-up (PR #2983). PR #2983 corrected every
comment/docstring in `pipeline.py`, `spawn.py`, `directive_assembly.py`,
`runaway_backstop.py`, and `runaway_signal.py` that claimed the
wall-clock/token backstops are actively enforced, but its own diff
(despite its PR body's claim to have left `_TURN_BUDGET_PROSE`
untouched) rewrote that session-facing Korean string to say exactly the
thing the rest of the fix was correcting elsewhere: "지갑/시계 백스톱이
걸려 있다... 둘 중 하나만 넘어도 세션이 끝난다" ("a wallet/clock
backstop is in place... exceeding either one ends the session").

canonical: `gh pr view 2983 --json body` — body's own summary line: "`_TURN_BUDGET_PROSE`... was deliberately left untouched: it's runtime content, not a comment/docstring"
derived: `gh pr diff 2983 -- directive_assembly.py` — result (excerpt):
```
+    "세션 예산(이슈 #2961): 이 세션에 턴 상한은 없다 — 더 이상 턴 수로 "
+    "죽지 않는다. 대신 지갑/시계 백스톱이 걸려 있다: 벽시계 "
...
+    "둘 중 하나만 넘어도 세션이 끝난다. 관측 전용 조합 신호("
```
This shows the PR body's own claim about its diff is false — the diff
does touch `_TURN_BUDGET_PROSE`, and the replacement text contains the
identical false enforcement claim the rest of the PR was fixing.

derived: `grep -rn "backstop_verdict\|WALL_CLOCK_BACKSTOP_MS\|TOKEN_COST_BACKSTOP_TOKENS" --include=*.py . | grep -v "/tests/\|test_"` — result:
```
runaway_signal.py:15:caller invokes `backstop_verdict()` either, so nothing in this slice
directive_assembly.py:177:    f"{runaway_backstop.WALL_CLOCK_BACKSTOP_MS // 60_000}분, 누적 토큰 "
directive_assembly.py:178:    f"{runaway_backstop.TOKEN_COST_BACKSTOP_TOKENS // 1_000_000}백만 "
runaway_backstop.py:10:`backstop_verdict()` below — the thresholds exist and are derived, but
runaway_backstop.py:37:WALL_CLOCK_BACKSTOP_MS = 5_400_000        # 90min; max observed 3,064,830ms * 1.5
runaway_backstop.py:38:TOKEN_COST_BACKSTOP_TOKENS = 150_000_000  # max observed 86,752,151 tokens * 1.5, rounded
runaway_backstop.py:42:                         threshold_ms: int = WALL_CLOCK_BACKSTOP_MS) -> bool:
runaway_backstop.py:47:                         threshold_tokens: int = TOKEN_COST_BACKSTOP_TOKENS) -> bool:
runaway_backstop.py:68:def backstop_verdict(elapsed_ms: float, events: list[dict]) -> dict:
pipeline.py:688:    # as shipped no live caller invokes `backstop_verdict()` — wiring an
pipeline.py:1755:    `backstop_verdict()`, so nothing here or elsewhere applies them to a
```
Confirms `backstop_verdict()` has zero production callers — the state
`_TURN_BUDGET_PROSE` needed to reflect, not deny.

Rewrote `_TURN_BUDGET_PROSE` (`directive_assembly.py:174-198`, commit
`dd5578ad`) so it states what is actually true: there is no turn cap and
turn count never terminates a session; the wall-clock/token thresholds
exist in `runaway_backstop.py` as the intended future bound with a
derived value, but no live caller applies them, so nothing currently
ends the session automatically on any of those grounds; the observe-only
composite signal (`runaway_signal.py`) likewise only records a verdict.
The batching guidance and the #2240 measurement (69 grep calls, 68
unique, serial exploration not a loop) were kept verbatim as the
justification for batching — that measurement is about wasted turns
regardless of what bounds the session, so it survives independent of the
false enforcement claim.

acceptance: `grep -rn "max-turns\|DEFAULT_SESSION_MAX_TURNS" spawn.py pipeline.py directive_assembly.py; echo rc=$?` — result:
```
rc=1
```
acceptance: `python3 -m pytest tests/ -k backstop -q` — result:
```
.....                                                                    [100%]
5 passed in 0.89s
```
acceptance: `python3 -m pytest tests/ -k runaway_signal_observe_only -q` — result:
```
....                                                                     [100%]
4 passed in 0.96s
```
acceptance: `python3 -m pytest tests/ -k runaway_signal_discrimination -q` — result:
```
...                                                                      [100%]
3 passed in 0.89s
```
acceptance: `python3 -m pytest tests/ -k subagent_in_flight -q` — result:
```
...                                                                      [100%]
3 passed in 0.85s
```

derived: `python3 -m pytest tests/ -q` (full regression sweep) — result:
```
1 failed, 70 passed in 6.11s
FAILED tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present
```
Confirmed pre-existing and unrelated to this fix (same failure PR #2983's
own record already noted):
derived: `git stash && python3 -m pytest tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present -q; git stash pop` — result:
```
1 failed in 0.83s
AssertionError: 4 not greater than 4
```
(identical failure with this commit's change stashed out.)

## Why

A session reads `_TURN_BUDGET_PROSE` directly and acts on it — unlike a
code comment a future developer might read, this string is delivered
into every spawned session's context as instruction. Telling a session
"exceeding either backstop ends the session" when nothing currently
enforces either backstop is worse than the comment PR #2983 fixed: a
session that believes a hard stop exists may make decisions (e.g. not
bothering to checkpoint-commit against a wall-clock risk it wrongly
thinks is otherwise handled) that a session correctly told nothing
enforces a bound would not make. The fix states the actual three-way
distinction plainly — no cap (true and already correct), no live
backstop enforcement (the part that was false), and an observe-only
signal (also correctly non-terminating) — because collapsing "no longer
capped" into "now backstopped" is exactly the false equivalence the
faulty prose made.

No enforcement caller was added, `runaway_signal.py`'s observe-only
behavior was not touched, and `--max-turns` was not reintroduced.
derived: `git diff 80f11e64..dd5578ad --stat` — result:
```
directive_assembly.py | 37 ++++++++++++++++++++++---------------
1 file changed, 22 insertions(+), 15 deletions(-)
```
(only `directive_assembly.py` changed in this commit; confirmed also by
this record's own `## What was done` acceptance re-runs above, all
passing without touching `runaway_signal.py`, `pipeline.py`, or
`spawn.py`.)

## What did not work

None — the fix was a direct, narrowly-scoped text correction to one
string constant; no approach was attempted and abandoned.

## Upstream basis

This record's branch was reset onto the tip of PR #2983's branch
(`issue-2961/silent-failure-audit-f922a07b`, commit `80f11e64`, which
itself carries PR #2964's full change set from
`issue-2961/observability-methodology-selection+test-derivation-27c16f97`)
before this fix's commit (`dd5578ad`) was made on top, so the PR opened
from this branch carries PR #2964's and PR #2983's full diff until those
merge to `main` — same stacking pattern PR #2983 used on top of PR #2964.
canonical: `git log --oneline -6 origin/issue-2961/silent-failure-audit-f922a07b` confirmed `80f11e64` as that branch's tip before this session began.
PR #2964's own record
(`docs/issue-2961/reports/observability-methodology-selection+test-derivation-27c16f97.md`)
and PR #2983's own record
(`docs/issue-2961/reports/silent-failure-audit-f922a07b.md`) are present
in this tree because they were carried in from that branch tip; both are
unmerged to `main` as of this record.

## Open findings

None new. PR #2964's own "Open findings" (no live enforcement caller;
`consult.py`/`bench/ablation.py` still use `--max-turns`; dead
`_resolve_wrap_up_allowance_turns()`) are unchanged by this fix — this
delivery corrects only the one session-facing prose string that repeated
the false enforcement claim PR #2983 had already fixed elsewhere.

## Next steps

`loop_state: landed` — this record is terminal. Wiring an actual
enforcing caller for `runaway_backstop.backstop_verdict()` (PR #2964's
"Open findings" item 1) remains a separate future issue, unchanged by
this fix.

skill-verdict: silent-failure-audit — not-applicable: this task is a
truthfulness correction to a session-facing prose string on
already-shipped modules, not an audit of error-handling paths (try/
catch, promise rejection, error callback, result type) for
silently-absorbed failures; no error-handling code was touched or
reviewed.
other mounted skills: not triggered (work-in-english governs language
only, applied silently throughout; prose-modes was not invoked since
this record's prose was assembled directly from executed evidence, not
drafted then revised).
