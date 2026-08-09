---
proposal: docs/issue-551/proposals/proposal.md
---

# Hunt record — issue-551-implementation

## before-landing — stance 0: assume the gate/convention just touched (or introduced) is bypassable — find the bypass.

Verdict: FINDING — `resolve_core()` treats mere file *existence* of `hooks/lib/gate-lib.sh` as proof core is reachable, so any empty/stale/garbage file at that relative path (in `$CLAUDE_PLUGIN_ROOT_CORE` or a candidate) makes it declare a real, non-SKIP resolution — silently converting a genuinely-unreachable/broken core into a false "resolved" success instead of the SKIP outcome the convention promises.
Kind: silent-failure
Seed: gates/test_env_resolve.py (new), docs/specs/test-env-resolution.md (new) — `_has_gate_lib()` is `os.path.isfile(...)` only, no content/validity check
cap_seconds: 120
tier: default
diff_stat_lines: ~380 (new files gates/test_env_resolve.py, gates/test_test_env_resolve.py, docs/specs/test-env-resolution.md, docs/issue-551/reports/implementation.md, + Accumulation section in proposal.md)
started_at: 2026-08-09T00:00:00Z
ended_at: 2026-08-09T00:05:00Z

### Reproduce
```
mkdir -p /tmp/claude-1000/fakecore/hooks/lib
touch /tmp/claude-1000/fakecore/hooks/lib/gate-lib.sh   # empty stub, not real gate-lib.sh
CLAUDE_PLUGIN_ROOT_CORE=/tmp/claude-1000/fakecore python3 -m gates.test_env_resolve
echo "exit=$?"
```

### Observed
```
/tmp/claude-1000/fakecore
exit=0
```
The resolver prints the fake path on stdout and exits `0` (success, per the doc's own "Adoption per consumer shape" branching rule: `0` means "prints the resolved path on stdout"), i.e. it claims core was successfully resolved and downstream gate tests should proceed sourcing `hooks/lib/gate-lib.sh` from this path — even though the file is empty and sourcing it supplies none of core's actual gate-lib functions. A gate test that sources this "resolved" path and then finds the functions it needs are simply undefined will either crash with an unrelated `command not found` (looking like a real gate regression) or, if it wraps calls in `|| true`/optional checks, silently no-op — exactly the "delivery regression vs. environment" ambiguity this convention exists to eliminate, just reintroduced one level down.

### Expected
Per `docs/specs/test-env-resolution.md`'s stated purpose ("so a test cannot mistake 'core is unreachable outside spawn env' for 'the gate under test actually regressed'"), a `CLAUDE_PLUGIN_ROOT_CORE`/candidate whose `hooks/lib/gate-lib.sh` is not a real, sourceable core library should not be treated as a resolved success — it should fall through to SKIP (or a distinct hard-failure) rather than being handed to the caller as `path`, exit 0. At minimum the doc's "no hardcoded paths" contract implicitly assumes existence implies validity, which is not checked anywhere in the reference implementation it embeds verbatim.
