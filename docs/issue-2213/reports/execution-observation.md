---
issue: 2213
role: execution-observation
loop_state: cleared
upstream:
  - path: consult.py
    sha: ef1ffc997d2eceac2e3c6ebe164fb0ea5992b0d5
subject: PR #2255 (branch issue-2213/performance-engineering, head ef1ffc997d2eceac2e3c6ebe164fb0ea5992b0d5)
test: a real git worktree at PR #2255's head commit; a self-authored script (not PR #2255's own harness) calling the real, unmodified `spawn._consult_cmd_and_env()` directly to inspect the returned argv/env, and a real, unmocked, live `spawn._skill_judge_consult()` call against this repo's actual skill corpus, checking `runs/ledger.jsonl` (gitignored, not checked in) before/after for the new event; `git show main:consult.py` grepped for the same two flag strings; `python3 -m pytest tests/test_spawn_gate_wiring.py::Ledger::test_entry_carries_the_live_log_path`
result: passed
assertedBy: execution-observation (independent live re-execution against the real deployed code in a real worktree at PR #2255's real head commit, not PR #2255's own pasted harness output or its own trace file)
---

# issue-2213 — execution-observation record

## What was done

Per the scope this session was opened for — re-execute PR #2255's two central claims independently rather than trust its own pasted evidence — this session checked out PR #2255's real head commit in an isolated git worktree (`git worktree add`, removed after use) and ran two live checks against the real, unmodified code, not PR #2255's own measurement harness or its own consult trace log.

### 1. Does `_consult_cmd_and_env()` now carry PR #2212's cache flags?

canonical: `spawn._consult_cmd_and_env("performance-engineering", spec, None, "haiku")`, called directly (not through any wrapper PR #2255 wrote), this turn, in the worktree at PR #2255's head — result:

```
CMD_HAS_FLAG: True   # "--exclude-dynamic-system-prompt-sections" in cmd
ENV_HAS_FLAG: 1      # env["ENABLE_PROMPT_CACHING_1H"]
FULL_CMD: ['claude', '-p', '--settings', '/tmp/tmpra_6smgt.json', '--permission-mode',
  'bypassPermissions', '--output-format', 'json',
  '--exclude-dynamic-system-prompt-sections', '--plugin-dir', '.../performance-engineering-operational-playbook',
  '--plugin-dir', '.../core', '--plugin-dir', '.../terse', '--plugin-dir', '.../freelunch',
  '--plugin-dir', '.../scout', '--plugin-dir', '.../warrant', '--model', 'haiku']
```

Both flags PR #2255 claims to have added are present in the actual returned argv/env, read directly off the function's real return value.

canonical: `git show main:consult.py`, grepped this turn for both flag strings — result: zero matches for either `--exclude-dynamic-system-prompt-sections` or `ENABLE_PROMPT_CACHING_1H` anywhere in `main`'s `consult.py`. Independently confirms the gap PR #2255 describes was real on `main` before this fix — not a claim taken on faith from the PR body.

### 2. Does a real consult now emit `skill_judge_perf` to `runs/ledger.jsonl`?

canonical: a real, live, unmocked call to `spawn._skill_judge_consult()` against three real skill candidates from this host's actual skill corpus (`kubernetes-workload-requests-limits-decision`, `decision-records`, `customer-support-research-log` — chosen only for being real and unrelated to the task text, so which one gets picked doesn't matter), issue=2213, model="haiku", this turn, in the same worktree — result:

```
CALL_OK: True picked: []
NEW_PERF_EVENTS: 1
EVENT: {"event": "skill_judge_perf", "ts": 1787618567, "role": "performance-engineering",
  "issue": 2213, "wall_s": 15.506, "duration_ms": 10487,
  "cache_read_input_tokens": 21937, "cache_creation_input_tokens": 7330,
  "concurrency": 0, "outcome_ok": true}
```

`runs/ledger.jsonl` gained exactly one new `event: "skill_judge_perf"` line, with all five fields the issue's Acceptance criterion names (`wall_s`, `duration_ms`, `cache_read_input_tokens`, `cache_creation_input_tokens`, `concurrency`) populated with real, non-null values from a real subprocess call, not fixture data. `cache_read_input_tokens: 21937` matches PR #2255's own reported post-fix value exactly (21937, vs. 18140 pre-fix) — independent corroboration of the specific cache-hit-count claim in the PR body, not just a shape match.

canonical: `git check-ignore -v runs/ledger.jsonl` — result: `.gitignore:1:runs/ runs/ledger.jsonl`. The event above came from a live call made this turn, not from any file checked into the PR.

### 3. The one claimed test regression fix

canonical: `python3 -m pytest tests/test_spawn_gate_wiring.py::Ledger::test_entry_carries_the_live_log_path -q`, this turn, same worktree — result: `1 passed in 10.82s`. Matches PR #2255's own claim for this specific test.

## Why

Per the defect-verification-independence guidance mapped to this role: re-run the actual code path live, against a real worktree at the PR's real head commit, rather than reasoning about the diff in isolation or reusing the PR's own harness/log files as evidence. The two checks above map directly to the scope this session was opened for (skill_judge_perf ledger events on a real consult; cache-flag inheritance in `_consult_cmd_and_env()`), plus one cheap corroborating test run.

This session did not attempt to reproduce PR #2255's full 18-call before/after latency study (median/p90/p50 table, candidate ranking) — that is a much larger, multi-minute-per-call measurement exercise, and the scope this session was opened for names only the two specific mechanisms above, not the full performance verdict. That narrower scope is a deliberate limit of this record, not an oversight — see Open findings.

## Upstream basis

- PR #2255 (branch `issue-2213/performance-engineering`, head `ef1ffc997d2eceac2e3c6ebe164fb0ea5992b0d5`) — the worktree this session checked out and ran both live checks against; its own record content (read via `gh pr diff 2255`, not a path on this branch's tree, since `docs/issue-2213/reports/performance-engineering.md` is untracked here and exists only on that PR's branch) supplied the claimed post-fix `cache_read_input_tokens` value (21937) this session's independent measurement is compared against.
- `main`'s `consult.py` (`git show main:consult.py`), read this turn to independently confirm the pre-fix absence of both cache flags.
- Issue #2213 body (`gh issue view 2213`, read this turn) — the Acceptance criterion's named fields (`cross_family` timing, `cache_read_input_tokens`, concurrency count) are what section 2 above checks are actually present and non-null in a real ledger event.

## Open findings

None blocking the two claims this session was scoped to check.

1. This session did not independently re-run PR #2255's full 18-call before/after latency study or its concurrency probe, so it cannot itself confirm or refute the PR's "candidate 2 (model-side variance) is best-supported" verdict or its p50/p90 table. Resolution path: a future execution-observation pass, if that specific verdict needs independent re-measurement, would need its own multi-call live harness (each call costs tens of seconds) rather than the two point-checks this session ran.
2. This session's single live `_skill_judge_consult()` call landed at `concurrency: 0`, the same scoping gap PR #2255's own record already names (direct function calls don't register into `_live_workspaces()`) — not a new finding, just independently reproduced.

## Next steps

None — loop_state is terminal (cleared). This record's verdict rests on the live checks in sections 1 through 3 above, executed this turn against the real deployed code in a real worktree at PR #2255's actual head commit, not on PR #2255's own pasted evidence.
