---
issue: 2511
role: silent-failure-audit+observability-explorability-fac0f402
author: silent-failure-audit+observability-explorability-fac0f402
loop_state: landed
upstream:
  - path: docs/issue-2511/reports/silent-failure-audit+observability-explorability-6f5691f7.md
    sha: 30ca2a6970e2a4a08c0ea9baf3298760031201bf
  - path: docs/issue-2511/reports/silent-failure-audit+observability-explorability-fac0f402/2026-08-27-hunt-spawn-attempt-supersession.md
    sha: same-commit
---

# issue-2511 — silent-failure-audit+observability-explorability-fac0f402 record

skill-verdict: silent-failure-audit — applied: invoked; audited the new `spawn._attempt_superseded()` for a silently-absorbed re-check. Its first draft trusted a recorded `outcome == "session-log"` claim in `spawn-attempts.jsonl` at face value — the one path in this mechanism that replayed a past claim instead of re-deriving live state, unlike every other class in `_halt_condition_cleared()`. A before-landing warrant-hunt (stance: "assume the gate just touched is bypassable") reproduced this exactly (see "Open findings" 1) and it was fixed in this same session before landing: the referenced session-log path is now re-verified to exist on disk (`Path(log_path).is_file()`) before counting as supersession evidence.
canonical: `python3 -m pytest test/test_spawn_attempt_staleness.py -k AttemptSupersededTest -q` — result: `8 passed`, including `test_false_when_the_log_path_no_longer_exists` (the fix's own regression test)

skill-verdict: observability-explorability — applied: invoked; asked whether "why did this halt clear" stays answerable ad-hoc after the fix, not just "did it clear". Added `resolved_via` (`"class-recheck"` or `"superseded"`) to the `spawn_attempt_resolved` event, the `spawn_attempt_resolved_reported` ledger write, and the printed "halt RESOLVED" line — so `runs/ledger.jsonl` alone answers "which resolution path cleared this halt" without re-deriving it from the class + attempt fields after the fact.
canonical: `grep -n "resolved_via" roster.py` output (this commit) — three sites: the `spawn_attempt_resolved` event dict, the print f-string, and the `ledger_write` call

## What was done

Build-now bypass (`CORE_BUILD_NOW=1`, spawner-set) — delivered directly on this branch, no phase-1 proposal round. This closes the residual the issue's own most recent comment (posted after PR #2594 merged) reopened it for.

PR #2594 (prior session, `docs/issue-2511/reports/silent-failure-audit+observability-explorability-6f5691f7.md`) fixed the watchdog's `[spawn-attempt]` replay bug for four of five halt classes via `spawn._halt_condition_cleared(cls, attempt, reason)` — a per-class **re-check** of the live blocking condition. The reopen comment found that this re-check alone can never clear `cwd-invalid` (and, by the same shape, `workspace-origin-mismatch`): the halted attempt's own recorded `cwd` argument is a property of *that specific spawn invocation*, and that argument never changes once written. For the fixture that motivated the reopen, the `-C` value actually passed to spawn was the string `tokenmaxxxer/on-the-record` (a repo slug, not a path — visible in the halt's `reason` text), which could never become a directory even if it had been recorded. A follow-up comment (`amendments-reconciled` below) narrowed this further mid-session: the `spawn_attempt` event's own `cwd` *field* is not merely bad on this fixture, it is absent entirely — every attempt record currently in `spawn-attempts.jsonl` predates PR #2594's addition of `cwd` recording, so the class re-check returns `False` for all three live entries (`issue-2576`, `issue-2587`, `issue-1`) on missing-data grounds, not argument-badness grounds. Both failure modes (bad-but-present, or absent) land on the same conclusion the class re-check alone can never escape from for this attempt. The original comment reported watching the `issue-2576` halt replay six times over roughly an hour after the underlying spawn had actually been re-run successfully and its PR merged.

Added `spawn._attempt_superseded(attempt_id, attempt, attempts, outcomes)` (spawn.py) and wired it into `roster.spawn_attempt_sweep()` (roster.py) alongside — not replacing — the existing class re-check:

```python
condition_cleared = _sp._halt_condition_cleared(cls, a, reason)
superseded = _sp._attempt_superseded(attempt_id, a, attempts, outcomes)
if condition_cleared or superseded:
    ...
    resolved_via = "class-recheck" if condition_cleared else "superseded"
```
canonical: `git show 5df50f91:roster.py | grep -n "condition_cleared\|superseded ="` output — same lines present in `spawn_attempt_sweep()`

`_attempt_superseded()` asks a different question than the class re-check: not "is this attempt's own recorded argument still bad" but "has this same (issue, role) subject since been attempted successfully" — scanning `attempts`/`outcomes` (already returned by `_load_spawn_attempts()`, per the reopen comment's own pointer) for another attempt with the same `issue`+`role`, a strictly later `ts`, and `outcome == "session-log"` whose recorded log path still exists on disk. A halt superseded by a later successful attempt resolves regardless of whether its own recorded arguments still look bad — exactly the question the class-based design didn't ask.

Test additions in `test/test_spawn_attempt_staleness.py`:
- `AttemptSupersededTest` — unit-level coverage of `_attempt_superseded()`: superseded-true, no-later-attempt, later-attempt-also-halted, earlier-not-later, different-subject, missing-ts, missing-log-file, missing-detail.
  derived: `sed -n '/class AttemptSupersededTest/,/^class /p' test/test_spawn_attempt_staleness.py | grep -c "    def test_"` — result: `8`
- `SpawnAttemptSweepSupersededFixTest` — end-to-end, using the exact two live fixtures the task named from the canonical checkout's `runs/spawn-attempts.jsonl`, both reproduced with no `cwd` field on the halted attempt (matching the real live entries exactly — see `amendments-reconciled` below):
  - `issue-2576/silent-failure-audit-ec09cf78` (cwd-invalid, real recorded reason string) — superseded by a synthetic later successful attempt for the same (issue, role) → resolves, `resolved_via=superseded`.
  - `issue-1/implementation-af260856` (requirement-tag, real recorded reason string) — nothing superseded it → keeps reporting at full volume, as required.
  canonical: `python3 -c "import json; [print(json.loads(l).get('issue'), json.loads(l).get('cwd')) for l in open('$ON_THE_RECORD/runs/spawn-attempts.jsonl') if json.loads(l).get('event')=='spawn_attempt']"` — result: `2576 None`, `2587 None`, `1 None` (no live attempt record carries a `cwd`)

canonical: `python3 -m pytest test/test_spawn_attempt_staleness.py -q` output — result: `35 passed in 0.93s`

## Why

**Why a second, independent check instead of extending the class re-check**: `requirement-tag`/`acceptance-format` are properties of the *issue* (fixing the issue clears the halt on its own, no matter which attempt raised it), so re-deriving live issue state is the correct and complete re-check for them. `cwd-invalid`/`workspace-origin-mismatch` are properties of *that one spawn invocation's arguments*, which are durably recorded and never mutate — no live re-check of "is this string now a valid directory" can ever become true for a string that was never a path to begin with. Re-checking harder along the same axis cannot fix this; the fix has to ask a different question ("was this subject retried and did it succeed"), so it's additive (`or`), not a reshape of `_halt_condition_cleared()` — per the task's explicit constraint not to reshape or revert #2594.

**Why `outcome == "session-log"` is the definition used for "attempted successfully"**: it is recorded at the point bootstrap reaches session-log/roster existence — including the cwd/workspace resolution that `cwd-invalid`/`workspace-origin-mismatch` halts block — for that attempt. It does not claim the eventual task/PR outcome (that is a separate, later fact); it only claims the specific class of failure this mechanism cares about (bad `-C` argument, wrong workspace origin) did not recur on that attempt. That is what "has this (issue, role) since been attempted successfully" is defined to mean here.
canonical: `python3 -c "import pathlib; s = pathlib.Path('spawn.py').read_text(); i = s.index('_record_spawn_outcome(attempt_id, \"session-log\"'); print(s[i-260:i+120])"` — result: the call site inside the comment block reading "이 지점 이후로는 세션 로그/로스터가 곧 존재한다 — 부트스트랩 halt 구간을 이 시도의 성공으로 확정한다", immediately followed by `_record_spawn_outcome(attempt_id, "session-log", str(log_path))`

**Staleness determination for this new check (acceptance bullet 3, extended to the residual)**: **re-check**, not expiry — same principle as every existing class. `_attempt_superseded()` re-derives its answer from two independent, currently-true facts each time it's called: (1) does a later attempt record exist for the same (issue, role) with `outcome == "session-log"`, and (2) does that attempt's claimed session-log file *still actually exist on disk right now* (`Path(log_path).is_file()`). Neither is "N minutes/hours have passed" — fact (1) can never become true on its own (nothing writes a session-log entry without spawn.py's own bootstrap code reaching that point), and fact (2) is a live filesystem re-check, not a replay of the recorded claim, matching the rest of the design's "always re-derive, never just trust a recorded claim" principle (see Open finding 1 for why this second half was added). A still-broken spawn cannot be marked resolved by this path: nothing marks `outcome: "session-log"` except `spawn.py`'s own bootstrap code, at the exact point a later attempt's bootstrap genuinely reached that point — there is no elapsed-time branch anywhere in this function, and every ambiguous/missing-data case (`ts` missing, no later attempt, later attempt not session-log, log file gone) returns `False` (still live), matching the conservative direction `_halt_condition_cleared()` already uses throughout.
canonical: `python3 -m pytest test/test_spawn_attempt_staleness.py -k "AttemptSupersededTest or SpawnAttemptSweepSupersededFixTest" -q` — result: `10 passed`, covering both facts' positive and negative branches

**Two live fixtures, mirrored exactly (task's own instruction)**: the current canonical `spawn-attempts.jsonl` (`$ON_THE_RECORD/runs/spawn-attempts.jsonl`) holds only the original *halted* entry for `issue-2576/silent-failure-audit-ec09cf78` — the successful retry's own trace already aged out (see Open finding 2 for why, and why the demo therefore uses a synthetic later entry rather than mutating shared production state). The `issue-1/implementation-af260856` fixture (`requirement-tag`, no `cwd` recorded) needed no synthesis at all: nothing superseded it, and the class re-check independently also stays `False` (no `cwd`), so it keeps reporting exactly as before, live-demoed directly against the isolated copy of the real file.
canonical: `python3 -c "print(sum(1 for l in open('$ON_THE_RECORD/runs/spawn-attempts.jsonl') if '\"issue\": 2576' in l))"` — result: `1` (only the halted entry, no successful-retry trace remains)

## Upstream basis

- `docs/issue-2511/reports/silent-failure-audit+observability-explorability-6f5691f7.md` (sha `30ca2a6970e2a4a08c0ea9baf3298760031201bf`) — PR #2594's record; this session's fix is additive to, and explicitly does not reshape, the mechanism that record documents.
- `docs/issue-2511/reports/silent-failure-audit+observability-explorability-fac0f402/2026-08-27-hunt-spawn-attempt-supersession.md` (same-commit) — the before-landing warrant-hunt whose finding (Open finding 1) was fixed in this session before landing.
- The issue's most recent comment (posted after #2594 merged, reopening #2511) — the task brief for this session, quoted verbatim in the task prompt; not re-fetched separately since the task prompt already carried its full text and the canonical `spawn-attempts.jsonl` fixtures it named were read directly.
canonical: `python3 -c "print(open('$ON_THE_RECORD/runs/spawn-attempts.jsonl').read())"` output — the two entries for issue 2576 (`silent-failure-audit-ec09cf78`) and issue 1 (`implementation-af260856`) the task named, byte-matched into the new end-to-end tests

## Open findings

1. **Warrant-hunt finding (before-landing, stance 0, fixed in this same session before landing).** The hunter (`docs/issue-2511/reports/silent-failure-audit+observability-explorability-fac0f402/2026-08-27-hunt-spawn-attempt-supersession.md`) found the first draft of `_attempt_superseded()` trusted a recorded `outcome == "session-log"` entry with no live re-verification — a forged or stale claim in `spawn-attempts.jsonl` could permanently silence a halt whose class re-check independently says is still live, contradicting `_halt_condition_cleared()`'s own "always re-derive, never replay a recorded claim" principle. Fixed by requiring the claimed session-log path to still exist on disk (`Path(log_path).is_file()`) before trusting it.
   canonical: `git show 5df50f91:docs/issue-2511/reports/silent-failure-audit+observability-explorability-fac0f402/2026-08-27-hunt-spawn-attempt-supersession.md` — the hunt record's "### Reproduce"/"### Observed" sections
   derived: `python3 -m pytest test/test_spawn_attempt_staleness.py -k test_false_when_the_log_path_no_longer_exists -q` — result: `1 passed` (post-fix regression test derived directly from the hunter's repro shape)
2. **Mid-session amendments-reconciled correction.** A second reopen-thread comment landed while this session was working (issue #2511, `issuecomment-5434456805`, posted after this session's first read of the thread): the commenter's own live re-verification found that every `spawn_attempt` record currently in the canonical `spawn-attempts.jsonl` predates PR #2594's addition of `cwd` recording, so `cwd` is `None`/absent on all three of them (`issue-2576`, `issue-2587`, `issue-1`) — not merely present-but-bad as this session's own first draft of "What was done"/tests had assumed (mirroring, independently, the same kind of correction the commenter's first reopen comment needed after its own hand-built fixture didn't represent production data). Consequence for this fix: none to the code — `_attempt_superseded()` never reads `attempt.get("cwd")`, so it is unaffected either way. Consequence for this record and its tests: fixed before landing — the end-to-end test for `issue-2576` in `test/test_spawn_attempt_staleness.py` (class `SpawnAttemptSweepSupersededFixTest`, method `test_cwd_invalid_superseded_by_later_successful_attempt_stops_replaying`) no longer fabricates a `cwd` value on the halted attempt, and this record's "What was done"/"Why" prose was corrected to state the missing-field fact accurately rather than the bad-value framing.
   canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/2511/comments --jq '.[] | select(.id==5434456805) | .body'` output — the comment's own re-verification table (`0/3 attempts carry cwd`) and its explicit self-correction ("my earlier comment reported the requirement-tag class as clearing correctly... my fixture did not represent production data")
   derived: `python3 -c "import json; [print(json.loads(l).get('issue'), json.loads(l).get('cwd')) for l in open('$ON_THE_RECORD/runs/spawn-attempts.jsonl') if json.loads(l).get('event')=='spawn_attempt']"` — result: `2576 None`, `2587 None`, `1 None` (re-verified independently by this session, matches the comment's finding exactly)
   amendments-reconciled: issuecomment-5434456805 — reconciled above; no code change required (`_attempt_superseded()` never reads `cwd`), record/test prose corrected before landing.
3. **The `issue-2576` live-fixture demonstration uses a synthetic later attempt, not the real successful retry's own trace.** `_prune_spawn_attempts()` removes a `"session-log"`-outcome attempt's raw jsonl entry on the very next prune pass (called unconditionally at the end of every `spawn_attempt_sweep()` tick) — by design, since a successful bootstrap is never a retention target. By the time this session read the canonical file, the real successful retry's trace for `issue-2576/silent-failure-audit-ec09cf78` had already aged out this way; only the original halted entry remained. The demonstration therefore appends a synthetic later `spawn_attempt`/`spawn_attempt_outcome(session-log)` pair (with a real, existing log file, per Open finding 1's fix) to an **isolated copy** of the canonical file under a temp `MUSTER_STATE_ROOT`, never mutating `$ON_THE_RECORD/runs/spawn-attempts.jsonl` itself — avoiding side effects on shared watchdog state while still processing the real recorded halt entry as input. `issue-1/implementation-af260856` needed no synthesis (nothing was ever pruned for it — it's still `"halted"`, unresolved).
   derived: `MUSTER_STATE_ROOT=<isolated copy> python3 -c "import spawn, roster; ..."` (this session, inline, both runs against the same real `spawn-attempts.jsonl` copy) — before appending the synthetic entry: `reported count: 3` (issue-1, issue-2576 cwd-invalid, issue-2587, all live); after: `reported count: 2`, issue-2576 line reads `halt RESOLVED ... resolved_via=superseded`, issue-1 and issue-2587 unchanged
4. **Unrelated pre-existing test failures**, same 15 before and after this change (identical failing test names in both runs).
   derived: `git stash && python3 -m pytest test/ tests/test_tmp_resource_gc.py -q 2>&1 | tail -3` → `15 failed, 304 passed`; `git stash pop`; `python3 -m pytest test/ tests/test_tmp_resource_gc.py -q 2>&1 | tail -3` → `15 failed, 314 passed` (314 = 304 baseline-passing + 10 new tests; 15 failing names identical in both runs, all in `test_spawn_cross_family_skill_selection.py`/`test_spawn_skill_judge_haiku_timeout_overlap.py`/`test_spawn_artifact_skill_pairing.py`, a network/origin-fetch environment issue unrelated to this diff)
   Resolution path: none — pre-existing, out of this issue's scope.

## What did not work

None — the warrant-hunt finding (Open finding 1) was a design gap the hunt surfaced before landing, not a false start; it was fixed once, in place, without reverting or discarding any prior approach.

## Next steps

None — loop_state is terminal (`landed`).

Acceptance requirement met — checked: `python3 -m pytest test/test_spawn_attempt_staleness.py -q` — result: `35 passed`, covering the residual against both named live fixtures:
- `issue-2576/silent-failure-audit-ec09cf78` (cwd-invalid, superseded) — `SpawnAttemptSweepSupersededFixTest::test_cwd_invalid_superseded_by_later_successful_attempt_stops_replaying`: reports live before the synthetic successful retry exists, stops replaying (`resolved_via=superseded`) after, fully swept away the tick after that.
- `issue-1/implementation-af260856` (requirement-tag, unsuperseded) — `SpawnAttemptSweepSupersededFixTest::test_requirement_tag_without_a_successful_retry_keeps_reporting`: keeps reporting at full volume, never marked resolved.
- The "since attempted successfully" question's staleness method (per-attempt re-check: later session-log record + live on-disk file existence, never elapsed time) — `AttemptSupersededTest` and the "Why" section above.
- The must-not carried forward from #2511/#2594 (never resolve on elapsed time alone; a genuinely-still-broken halt keeps reporting) — verified by `test_requirement_tag_without_a_successful_retry_keeps_reporting` and by `HaltConditionClearedCwdInvalidTest`/`HaltConditionClearedUnknownClassTest` (unchanged, still passing).

canonical: `python3 -m pytest test/ tests/test_tmp_resource_gc.py -q` — result: `15 failed, 314 passed`
acceptance: `python3 -m pytest test/test_spawn_attempt_staleness.py -q` — result: `35 passed in 0.93s` (0 regressions, 10 new tests, both named live fixtures reproduced and demonstrated)
