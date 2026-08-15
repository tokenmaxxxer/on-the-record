---
code_under_review:
  - spawn.py
  - tests/test_spawn_judge.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# issue-1605 — judge per-merge cap counting defect

## What was done

`_judge_roles_run_today()` in `spawn.py` counted every trace line for a
merge sha, including `outcome='ok: prefilter 미스 — judge 미호출'`
(prefilter-miss) and `outcome='error: 캡 초과 ...'` (cap-exceeded
rejection) lines. Fixed it to count only lines where a judge session
actually ran — excludes the two outcome patterns above, keeps everything
else (ok-with-findings, ok-zero-findings, real-run errors like timeouts
or session-exit failures). `_append_judge_trace()` / trace-always
behavior is unchanged: a cap-exceeded rejection still writes a trace
line, it is just never counted toward the cap.

This is a direct-to-code session (no separate phase-1 proposal round for
this issue): skip condition per scout-directive — pure bugfix, fix fully
specified by the issue body, no design decision open.

## Why

PR #1601's binding correction (counting only prefilter-HIT judge runs)
was applied to the E1 wiring loop in `gates/patrol_wiring.py` but never
ported into `spawn.py`'s own internal cap check inside `judge_cmd()`.
Live wiring run on merge 72a4daff (per the issue) showed the first three
alphabetical roles were prefilter misses, which exhausted
`JUDGE_MAX_ROLES_PER_MERGE=3`, and every subsequent role was then
rejected `cap_exceeded` — each rejection appending another counted line,
snowballing the count. Net effect: no merge could ever be judged by a
role later than 3rd in iteration order.

## Upstream basis

Issue #1605 body (fix + acceptance criteria), and PR #1601 / #1590
binding review notes referenced there and in `spawn.py`'s existing
docstrings.

## Regression tests

Added to `tests/test_spawn_judge.py`, class `JudgeCapTest`:
- `test_three_prefilter_misses_then_fourth_role_still_runs` — 3
  prefilter-miss trace lines for one merge sha -> counted as 0, still
  under the cap.
- `test_cap_exceeded_lines_do_not_increment_count` — 1 genuine run + 2
  cap-exceeded rejection lines -> counted as 1, not 3.
- `test_three_genuine_runs_then_fourth_role_rejected` -> 3 genuine
  outcome lines (ok-zero-findings, ok-with-findings, real timeout error)
  count as 3, at/over the cap.

derived: `python3 -m pytest tests/test_spawn_judge.py -q`
```
...................                                                      [100%]
19 passed in 0.84s
```

## Live re-run (acceptance criterion 2)

Ran `gates/patrol_wiring.py`'s own per-role loop logic (calling
`spawn.judge_cmd` directly, role by role, over `_known_roles()`) against
merge sha `72a4daff` on a fresh clone (`git clone` of this branch's HEAD
into `/tmp/otr-fresh-1605b`, no prior trace-log entries for that merge
sha). Note: the current repo has 44 role specs under `roles/*.json`, not
43 as stated in the issue body (`derived: ls roles/*.json | wc -l` ->
`44`) — the count grew since the issue was filed; the acceptance intent
(every role gets real prefilter evaluation, no cap-exceeded cascade) is
what was verified, over the current role set.

canonical: /tmp/otr-fresh-1605b/docs/reports/patrol-judge-log.md (this
session's own live run's trace log, read after the run)

acceptance: python3 -c "... loop over spawn.judge_cmd(role, '72a4daff', cwd='.') for each of _known_roles() ..." — result: hits=3 misses=10 errors=0 cap_exceeded=31 total=44

The 10 prefilter-miss roles at the front of the alphabetical order did
**not** exhaust the cap; the cap was reached only after 3 genuine judge
runs (`architecture`, `conformance-review`, `execution-observation`),
and every one of the remaining 31 roles still received a real per-role
prefilter-cap check (not a group-rejected cascade) before being
correctly turned away as `cap_exceeded`.

Trace excerpt (`docs/reports/patrol-judge-log.md` in the fresh clone,
first 14 lines for `merge=72a4daff`, showing the pre-fix defect no
longer reproduces):
```
- ...T14:11:51... | role=accessibility | verb=judge | merge=72a4daff | outcome='ok: prefilter 미스 — judge 미호출'
- ...T14:12:06... | role=api-design | verb=judge | merge=72a4daff | outcome='ok: prefilter 미스 — judge 미호출'
- ...T14:12:23... | role=architecture | verb=judge | merge=72a4daff | outcome='ok: findings 없음'
- ...T14:13:04... | role=brand-design | verb=judge | merge=72a4daff | outcome='ok: prefilter 미스 — judge 미호출'
- ...T14:13:18... | role=capacity-planning | verb=judge | merge=72a4daff | outcome='ok: prefilter 미스 — judge 미호출'
- ...T14:13:37... | role=conformance-review | verb=judge | merge=72a4daff | outcome='ok: findings 없음'
- ...T14:14:26... | role=content-design | verb=judge | merge=72a4daff | outcome='ok: prefilter 미스 — judge 미호출'
- ...T14:14:44... | role=customer-support | verb=judge | merge=72a4daff | outcome='ok: prefilter 미스 — judge 미호출'
- ...T14:14:58... | role=data-engineering | verb=judge | merge=72a4daff | outcome='ok: prefilter 미스 — judge 미호출'
- ...T14:15:14... | role=data-modeling | verb=judge | merge=72a4daff | outcome='ok: prefilter 미스 — judge 미호출'
- ...T14:15:29... | role=defect-verification | verb=judge | merge=72a4daff | outcome='ok: prefilter 미스 — judge 미호출'
- ...T14:15:51... | role=devrel | verb=judge | merge=72a4daff | outcome='ok: prefilter 미스 — judge 미호출'
- ...T14:16:12... | role=execution-observation | verb=judge | merge=72a4daff | outcome='ok: findings 없음'
- ...T14:17:04... | role=finance-unit-economics | verb=judge | merge=72a4daff | outcome='error: 캡 초과 (merge=72a4daff 에 이미 3개 역할 실행, 상한 3)'
```

## Rationale for deviations

The issue's acceptance criterion literally names
`python3 gates/patrol_wiring.py run . <recent-merge-sha>` as the command
to re-run. That CLI entry point was not run end-to-end, because its own
per-role loop (`gates/patrol_wiring.py:88`) has no exception handling
around `judge_cmd()`, and it aborted mid-loop on an unrelated live
judge-session failure (`role=defect-verification`, exit code 1, empty
stderr — an environment/session issue, not a cap-counting one). Fixing
that missing exception handling is outside this issue's frozen write set
(`spawn.py`, `tests/test_spawn_judge.py` only). Instead, the live
re-run drove the identical call `patrol_wiring.run()` itself makes —
`spawn.judge_cmd(role, merge_sha, cwd=...)` per role from
`_known_roles()`, with the exact same cap logic under test — just with a
per-role try/except added around that one call so one role's unrelated
live-session error would not stop the sweep over the remaining roles.
The cap-counting behavior demonstrated is therefore the same behavior
`gates/patrol_wiring.py run` would exhibit, module-for-module, once it
reaches each role.

## What did not work

- First attempt ran `python3 gates/patrol_wiring.py run . 72a4daff`
  directly; it aborted on an uncaught `RuntimeError` from one role's
  live judge-session exit code 1 (unrelated to the cap fix). Switched to
  calling `spawn.judge_cmd()` per role directly (same function
  `patrol_wiring.run()` calls), catching exceptions per-role, so the
  loop kept going past that one role's error instead of stopping there.
- First live-rerun attempt reused a clone that had already accumulated
  trace lines for `merge=72a4daff` from the aborted run above, which
  made a second `cap_exceeded` appear earlier than expected (log
  accumulation across two runs against the same merge sha, not a
  defect). Re-cloned fresh (`/tmp/otr-fresh-1605b`) with a trace log that
  had zero prior lines for `merge=72a4daff` and re-ran once to get a
  clean result.

## Open findings

None.
