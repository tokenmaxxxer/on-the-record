---
proposal: docs/issue-847/proposals/phase-2-github-host-guard.md
---

# Hunt record — phase-2-github-host-guard

## before-landing — stance: assume this guard goes silent when its own input is malformed — make it go silent

Verdict: FINDING — whitespace-only NORTHPOLE_HARNESS_GH_TOKEN bypasses the "no token" guard (truthy string, not stripped), so resolve_harness_github_host() returns available:True with a garbage token instead of UNMEASURED-with-reason, and downstream reset_and_push_fixture_to_github would then crash opaquely via subprocess CalledProcessError rather than degrade gracefully as the docstring promises.
Kind: silent-failure
Seed: harness/driver.py new functions resolve_harness_github_token, resolve_harness_github_host, reset_and_push_fixture_to_github, seed_steady_state_github_host (uncommitted working-tree diff on issue-847/implementation)
cap_seconds: 180
tier: default
diff_stat_lines: harness/driver.py (+~110), harness/test_driver.py (+5 tests), docs/handbooks/northpole-harness.md
started_at: 2026-08-11T20:58:00+09:00
ended_at: 2026-08-11T20:59:30+09:00

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-847-implementation
python3 -c "
import os, sys
os.environ['NORTHPOLE_HARNESS_GH_TOKEN'] = '   '
sys.path.insert(0, 'harness')
import driver
print(driver.resolve_harness_github_host())
"
```

### Observed
`{'available': True, 'repo': 'JiwonJung94/northpole-harness-fixture', 'token': '   '}`

### Expected
`{'available': False, 'reason': '...no NORTHPOLE_HARNESS_GH_TOKEN set...'}`, matching the behavior when the env var is unset or empty. resolve_harness_github_token() reads `token = os.environ.get(...)`  then only checks `if token:` (truthy check, no `.strip()`) before returning it directly — unlike the `gh auth token` fallback branch a few lines below, which correctly does `result.stdout.strip() or None`. The env-var path lacks the same whitespace guard as its sibling branch in the same function.
