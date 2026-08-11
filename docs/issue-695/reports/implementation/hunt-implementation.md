---
proposal: docs/issue-695/proposals/implementation.md
---

# Hunt record — implementation

(Note: dispatcher-requested path docs/issue-695/reports/hunt-implementation.md was denied by board-gate.sh R5 — role "implementation" may only write docs/issue-695/reports/implementation.md or docs/issue-695/reports/implementation/**. Filed under the latter.)

## before-landing — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — go_proxy_layer()/playwright_cache_layer() now always return None because the allowRead-population block they depend on was removed, silently disabling the GOPROXY/PLAYWRIGHT_BROWSERS_PATH cache-redirect optimization for every spawn without any error or log line
Kind: silent-failure
Seed: git diff HEAD -- spawn.py — role_settings()'s sandbox-disable centralization removes the host-package-cache mount block that used to populate sandbox.filesystem.allowRead, but go_proxy_layer() and playwright_cache_layer() (still present, still called from spawn()'s issue-spawn path) keep gating their return value on that same allowRead list.
cap_seconds: 180
tier: default
diff_stat_lines: see `git diff HEAD -- spawn.py`
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:20:00Z

### Reproduce
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-695-implementation
python3 << 'PYEOF'
import spawn
s = spawn.role_settings('implementation')
print('sandbox.enabled=', s.get('sandbox', {}).get('enabled'))
print('allowRead=', s.get('sandbox', {}).get('filesystem', {}).get('allowRead'))
print('go_proxy_layer=', spawn.go_proxy_layer(s))
print('playwright_cache_layer=', spawn.playwright_cache_layer(s))
PYEOF

### Observed
```
sandbox.enabled= False
allowRead= None
go_proxy_layer= None
playwright_cache_layer= None
```

Even with a real host Go module cache present (e.g. ~/go/pkg/mod), go_proxy_layer() returns None because `s["sandbox"]["filesystem"]["allowRead"]` is never populated anymore — the mount block that used to fill it was removed as "now-unreachable," but the two functions that read it, and their unconditional call site inside spawn()'s issue-spawn branch, were left in place. The call site's `if proxy:` / `if playwright_cache:` guards swallow the None, so no error, warning, or log ever surfaces; the extra_env GOPROXY/PLAYWRIGHT_BROWSERS_PATH overrides are just silently never set.

### Expected
Either go_proxy_layer()/playwright_cache_layer() and their call site should have been removed alongside the allowRead-population block they depend on (the proposal explicitly lists removing "now-unreachable plumbing" but missed this pair), or the invariant they rely on (host cache dirs mounted into allowRead) should still be maintained somewhere. As shipped, the functions and their docstrings assert behavior ("호스트 캐시가 있으면 그 경로를 그대로 넘긴다") that can never occur, and nothing signals the discrepancy.
