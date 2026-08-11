---
proposal: docs/issue-695/proposals/implementation.md
---

# Hunt record — implementation

## after-proposal — stance 4: assume the write set cannot carry the work; find a path the build will need that the proposal does not list

Verdict: NO FINDING
Seed: docs/issue-695/proposals/implementation.md (write set: spawn.py, test_spawn.py, docs/decisions/2026-08-11-remove-role-session-sandbox.md)
cap_seconds: 120
tier: default
diff_stat_lines: ~213 (2 new docs files)
started_at: 2026-08-11T09:50:58+09:00
ended_at: 2026-08-11T09:58:10+09:00

Checked: grepped the whole repo (not just the diff) for every symbol the
proposal names as removable (sandbox, allowUnsandboxedCommands,
tlsTerminate, SANDBOX_OPEN_*, PACKAGE_CACHE_DIRS, PACKAGE_REGISTRY_HOSTS,
WEB_ACCESS_DOMAINS) outside spawn.py/test_spawn.py — none found; only
spawn.py defines/uses them. Checked roles/*.json for a "sandbox" key
(present in ~40 role files) but the proposal explicitly keeps those files
untouched and out of scope, and role_settings() forcing sandbox.enabled
false is documented to make that key inert — consistent, not a gap.
Checked every non-test caller of role_settings() via
`grep -rln role_settings --include=*.py .`: only gates/test_hooks_parity.py
besides spawn.py itself. Read gates/test_hooks_parity.py's use of
role_settings() (t_role_settings_merges_hooks_only_for_self_hosted_target,
line 82) — it asserts only on the `hooks` key of role_settings() output,
never touches `sandbox`, `allowUnsandboxedCommands`, or
`allowedDomains`/`allowRead`, so this proposal's change cannot break it;
no write-set gap there. Grepped for `.get("sandbox"` / `["sandbox"]`
accesses anywhere outside spawn.py/test_spawn.py — none. Grepped shell
scripts for "sandbox" — one comment-only hit in
on-the-record/hooks/contract-guard.sh, no functional dependency. Found no
file the build will need to touch that isn't already in the frozen write
set.
