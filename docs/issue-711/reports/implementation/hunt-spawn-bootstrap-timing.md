---
proposal: docs/issue-711/proposals/spawn-bootstrap-timing.md
---

# Hunt record — spawn-bootstrap-timing

## after-proposal — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — the proposed `gh_token` phase timer cannot measure the `gh auth token` shell-out cost when `--issue` is given, because `_resolve_gh_token()`'s process-wide `_GH_TOKEN_CACHE` is warmed earlier, inside the `workspace`/`branch` phases (via `_fetch_or_halt` → `_git_env` → `_resolve_gh_token`), so by the time `spawn_cmd` calls `_resolve_gh_token()` again for the phase the proposal names `gh_token`, the cache always hits and the real subprocess cost — which did happen — gets silently attributed to `workspace` or `branch` instead.
Kind: design-error
Seed: docs/issue-711/proposals/spawn-bootstrap-timing.md; spawn.py _spawn_one (~4308-4386), issue_workspace/checkout_issue_branch (~3975-4134, via _fetch_or_halt ~3942 and _git_env ~3914), _resolve_gh_token/_GH_TOKEN_CACHE (~3885-3911), spawn_cmd's gh_token call (~3472)
cap_seconds: 120
tier: default
diff_stat_lines: 0 (proposal-only, no code diff yet)
started_at: 2026-08-11T02:21:37Z
ended_at: 2026-08-11T02:26:30Z

### Reproduce
```
python3 - <<'PYEOF'
import sys, time, subprocess
sys.path.insert(0, ".")
import spawn

calls = []
real_run = subprocess.run
def fake_run(cmd, *a, **kw):
    calls.append(cmd)
    class R:
        returncode = 0
        stdout = "FAKETOKEN\n"
        stderr = ""
    if cmd[:2] == ["gh", "auth"]:
        time.sleep(0.3)  # simulate the actual shell-out cost
        return R()
    return real_run(cmd, *a, **kw)
subprocess.run = fake_run

# workspace/branch phase, as issue_workspace/checkout_issue_branch do via _fetch_or_halt -> _git_env
t0 = time.monotonic()
spawn._git_env()
workspace_phase_gh_cost = time.monotonic() - t0

# the proposal's "gh_token" phase, i.e. spawn_cmd's later call
t0 = time.monotonic()
spawn._resolve_gh_token()
gh_token_phase_cost = time.monotonic() - t0

print("gh auth token subprocess calls made:", calls.count(["gh", "auth", "token"]))
print(f"workspace/branch phase absorbed gh cost = {workspace_phase_gh_cost:.3f}s")
print(f"gh_token phase cost                      = {gh_token_phase_cost:.3f}s")
PYEOF
```

### Observed
```
gh auth token subprocess calls made: 1
workspace/branch phase absorbed gh cost = 0.301s
gh_token phase (spawn_cmd's call) cost   = 0.000s  <- this is what bootstrap_timing would report as gh_token=
```
The single `gh auth token` shell-out (the entire cost the proposal wants the `gh_token=` field to represent) is paid during `workspace`/`branch`, and the field the proposal labels `gh_token=` reads ~0 every time a spawn is `--issue`-scoped (i.e. every real spawn — `_spawn_one` only skips `issue_workspace`/`checkout_issue_branch` for adhoc, non-issue spawns).

### Expected
The proposal's step 3 output format (`gh_token=0.09` etc.) implies `gh_token=` measures the `gh auth token` cost per spawn. For any `--issue`-scoped spawn (the normal case) the field will instead read near-zero while `workspace` or `branch` silently absorbs a real ~0.1-0.3s+ network round trip that the proposal's phase attribution claims is not part of those phases. No state in the current code (no per-phase cache-miss flag, no re-entrant timer) tracks *where* the cache was actually warmed, so the timer cannot attribute the cost correctly without new bookkeeping the proposal never introduces.
