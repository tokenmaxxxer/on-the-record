---
proposal: docs/issue-1112/proposals/2026-08-13-consult-self-hosted-hook-skip.md
---

# Hunt record — consult-self-hosted-hook-skip

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list.

Verdict: FINDING — proposal's write set (spawn.py, gates/test_consult_json_parse.py) omits `_run_panel_session()` (spawn.py:4493), a third `role_settings()` call site that mirrors `consult_cmd()` by design and stays exposed to the same self-hosted-hook injection this proposal is meant to fix.
Kind: design-error
Seed: docs/issue-1112/proposals/2026-08-13-consult-self-hosted-hook-skip.md (0-line diff, docs-only)
cap_seconds: 60
tier: size:docs-only
diff_stat_lines: 0
started_at: 2026-08-13T00:00:00Z
ended_at: 2026-08-13T00:05:00Z

### Reproduce
```
grep -n "role_settings(" spawn.py
```
Shows three call sites that build `claude -p` session settings via `role_settings()`:
- spawn.py:4377 inside `consult_cmd()` (the one the proposal patches with `inject_self_hosted_hooks=False`)
- spawn.py:4513 inside `_run_panel_session()` (unpatched)
- spawn.py:5631 inside `spawn_cmd()`'s issue-scoped path (intentionally left injecting per the proposal's Constraints)

`_run_panel_session()`'s own docstring (spawn.py:4495-4499) states it is built "consult_cmd() 와 똑같이 role_settings()/plugin_dirs() 로 조립한다 — 두 코드경로가 갈라지면 한쪽만 고쳐지는 드리프트가 난다 (#695/#700, consult_cmd() 독스트링과 같은 이유)" — i.e. the repo's own prior history (#695/#700) is about exactly this class of drift: fixing one role_settings() call site and not its sibling.

### Observed
The proposal's `files:` frontmatter and body only name `spawn.py` (for the `role_settings()`/`consult_cmd()` change) and `gates/test_consult_json_parse.py` (new regression test). It gives no instruction to also pass `inject_self_hosted_hooks=False` at spawn.py:4513, and the new test targets `consult_cmd()`'s JSON-parse path only, not `_run_panel_session()`. If phase-2 implements literally what's written, panel-mode consult sessions (used for cross-session judging peers, per the #973 phase-1 reference in the docstring) keep getting the same self-hosted hook merge that #1112's own root-cause note blames for the turn-budget/JSON-not-found failure — the bug reproduces via the panel path even after the "fix" lands through `consult_cmd()` alone.

### Expected
The write set should also list the `_run_panel_session()` call site (spawn.py:4513) and either pass `inject_self_hosted_hooks=False` there too, or the proposal should explicitly argue why panel sessions are exempt (they are not — the docstring says the opposite, that both paths must stay in lockstep).
