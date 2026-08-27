---
issue: 2607
role: technical-writing-structure-comprehension+silent-failure-audit-67ab369b
author: technical-writing-structure-comprehension+silent-failure-audit-67ab369b
skills: technical-writing-structure-comprehension (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
loop_state: landed
upstream:
  - path: gates/spawn_on_pr.py
    sha: same-commit
---

# issue-2607 — technical-writing-structure-comprehension+silent-failure-audit-67ab369b record

## What was done

Build-now bypass (`CORE_BUILD_NOW=1`, contract v3 s19a) — delivered directly, no proposal round.

- Added `clear_ceiling(root, subject=None, role=None)` to `gates/spawn_on_pr.py` (next to the existing `unpark()`). It clears only `ceiling_hit` and `attempts` on matching park-state entries — `blocked`/`parked`/`pr_number` are left untouched, so the next tick's spawn attempt still routes through the real `is_approval_blocked()` check, never through this command alone. With no `--subject`/`--role`, it targets every entry currently reported as `ceiling_hit: True`; with both given, it targets only that named pair (and only if it is currently `ceiling_hit`).
- Wired a `clear-ceiling` CLI subcommand (`--subject`/`--role` optional, must be given together) alongside the existing `unpark` subcommand.
- Restructured the CEILING HIT print into three lines — what happened, the fix command, the affected pairs — instead of one long concatenated line (technical-writing-structure-comprehension: chunk the message at its natural breakpoints instead of one dense sentence carrying the command inline).
- silent-failure-audit finding, fixed inline (see canonical diff excerpt below): the CLI's "nothing to clear" message was one string for two different situations — a genuinely empty ceiling state, and an operator-named `--subject`/`--role` pair that doesn't exist or isn't currently `ceiling_hit` (e.g. a typo). Split into two distinct messages so a typo doesn't read as "already handled."
  canonical:
  ```python
  elif args.subject and args.role:
      print(f"[clear-ceiling] {args.subject}/{args.role}: "
            f"ceiling_hit 상태 아님 (지울 것 없음)")
  else:
      print("[clear-ceiling] 지울 ceiling 상태 없음")
  ```
- Tests added to `gates/test_spawn_on_pr.py`: empty-state no-op, default clears-all-reported-pairs (leaving a non-ceiling park entry untouched), named-pair-only clears (leaving another `ceiling_hit` pair untouched), and the two end-to-end cases through the real `spawn_missing_for_pr()` entrypoint — clear-then-respawn when a real approval signal is present, and clear-does-NOT-bypass-approval when it isn't.
- derived: `python3 -m pytest gates/test_spawn_on_pr.py -q` — result: `15 passed in 0.86s`

Executed-live verification (both acceptance checks), reproduced against a real park-state file under this workspace's own `runs/` (gitignored, created and removed for the demo, not committed):

- derived: seeded `runs/spawn_on_pr_parked.json` with a `ceiling_hit: true, attempts: 4` entry, then `python3 gates/spawn_on_pr.py clear-ceiling` — result: `[clear-ceiling] 1건 해제됨: ['issue-99001/execution-observation']`; the saved JSON afterward showed `"ceiling_hit": false, "attempts": 0, "blocked": true, "parked": true` (ceiling state cleared, park bookkeeping untouched).
- derived: re-seeded the same ceiling-hit entry, ran the real `spawn_missing_for_pr()` entrypoint (gh/git/session boundaries stubbed exactly as `gates/test_spawn_on_pr.py`'s own `_wire()` helper does — no real network calls) with `is_approval_blocked` stubbed to `False` (standing in for "an approval comment is already on the issue," the scenario the issue itself describes) after running `clear_ceiling()` — result: `spawned pairs: [('issue-99001', 'execution-observation')]`, `spawn_one call count: 1`, printed `CONFIRMED: entry no longer blocks a spawn after clear-ceiling.` — acceptance requirement met.
- derived: `python3 gates/spawn_on_pr.py clear-ceiling` run a second time against the now-empty ceiling state — result: `[clear-ceiling] 지울 ceiling 상태 없음`, exit code `0` (empty case exits cleanly, no error) — acceptance requirement met.
- derived: seeded an entry with `attempts: 4` and no `ceiling_hit` flag yet (about to trip the ceiling this tick), ran the real entrypoint with `is_approval_blocked` stubbed `False` — result (three lines, stdout):
  ```
  [spawn-on-pr] CEILING HIT: 1건이 최대 재시도 횟수(4)에 도달해 자동 스폰을 멈춘다 — 사람 개입 필요 (park_state 에 ceiling_hit=True 로 기록됨).
  [spawn-on-pr]   해제: `python3 gates/spawn_on_pr.py clear-ceiling` (특정 쌍만 지우려면 `--subject <subject> --role <role>` 추가)
  [spawn-on-pr]   대상: [('issue-99001', 'execution-observation', 4)]
  ```
  subject/role/attempts (`대상:` line) and the ceiling value (`4`) are still present, alongside the new command — acceptance requirement met.

skill-verdict: silent-failure-audit — applied: invoked; audited `clear_ceiling()`/CLI wiring, found and fixed the ambiguous "nothing to clear" message (canonical excerpt above)
skill-verdict: technical-writing-structure-comprehension — applied: invoked; restructured the CEILING HIT print from one dense line into three (what happened / fix command / affected pairs, live output above)
other mounted skills: not triggered

## Why

Issue #2607's Decision (operator, 2026-08-27, `gh issue view 2607` — canonical): the CEILING HIT message names where the blocking state lives (`park_state`, `ceiling_hit=True`) but not how to clear it, and no reset path existed in code — the only real remedy was hand-editing a JSON file whose path the message never printed. The operator explicitly decided the counter must never reset on any automatic signal (approval, elapsed time, a PR-number change) — coupling it back to a signal would restore the exact single point of failure `#2604`'s independent ceiling was built to survive. So the fix is a message that names a working command, plus the command itself, not a change to when the ceiling clears automatically (it never does).

The `must not:` list drove the design directly:
- "do not make the ceiling reset on any automatic signal" → `clear_ceiling()` is only ever invoked from the CLI's `clear-ceiling` subcommand — no call site inside `spawn_missing_for_pr()`'s automatic tick logic.
- "do not add a flag that disables the ceiling" → no such flag exists; `max_respawn_attempts` remains the only ceiling-value override, unchanged from #2238's original design, and it is not surfaced as a "disable" switch.
- "do not make the clearing command clear anything other than the ceiling state for pairs the operator names or that are currently reported" → the function only ever writes `ceiling_hit`/`attempts` on matching keys, scoped to either the named pair or the current `ceiling_hit: True` set; every other park-state field and every non-ceiling-hit entry is left byte-for-byte alone.
  derived: `python3 -m pytest gates/test_spawn_on_pr.py -q -k clear_ceiling` — result: 5 passed, including `test_clear_ceiling_no_args_clears_all_currently_reported_pairs` and `test_clear_ceiling_named_pair_leaves_other_ceiling_hits_alone`, which assert the untouched entries byte-for-byte.

## Upstream basis

No proposal document exists for this issue (untracked — the build-now bypass, `CORE_BUILD_NOW=1`, skips the proposal round entirely). The operator's Decision section in the issue itself (verbatim, quoted above) already resolved the one open design question — must the ceiling ever auto-reset — no. `gates/spawn_on_pr.py` (this same commit) is the concrete upstream basis: the pre-existing `unpark()` function and its CLI subcommand pattern are the direct model `clear_ceiling()` and `clear-ceiling` follow.
canonical: `gates/spawn_on_pr.py` (this commit) — `unpark()`/`unpark` subcommand precede `clear_ceiling()`/`clear-ceiling` in the same file, same structure reused.

## Open findings

- silent-failure-audit (skill-repository(297e350), invoked this session) also surfaced that `load_park_state()`'s existing fail-safe (a corrupt/unreadable park-state JSON file silently reads as `{}`, pre-existing behavior shared by `unpark()`) would make `clear-ceiling` report "지울 ceiling 상태 없음" even when a real, unreadable ceiling-hit state exists on disk.
  canonical:
  ```python
  def load_park_state(root: Path) -> dict[str, dict]:
      ...
      try:
          return json.loads(p.read_text())
      except (OSError, ValueError):
          return {}
  ```
  This is inherited behavior, not introduced by this change, and reworking it is a general park-state administration concern the issue's own Non-goals section excludes (a general park-state administration surface is explicitly out of scope — this is one recovery path for one loudly-reported state). No resolution path opened; left as-is.
- No other open findings.

## Next steps

None — `loop_state: landed`. This record and the code land together in one commit/PR (build-now, single-phase).
