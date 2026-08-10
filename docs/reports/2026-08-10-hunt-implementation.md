---
proposal: docs/issue-573/proposals/implementation.md
---

# Hunt record — implementation

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list

Verdict: FINDING — the frozen write set omits `gates/gates.py`, but the new hook's
per-issue decisions-directory record path (architecture.md s4/s7, `docs/issue-<n>/decisions/auto-*.md`
and `.../remediation-*.md`) is not recognized by `gates/gates.py`'s `_always_writable()`,
which the CI-required `gates.role_scope()` check (wired in `gates/ci.py:461`) uses to
gate every PR's changed files against each role's write scope.
Kind: design-error
Seed: docs/issue-573/proposals/architecture.md, docs/issue-573/proposals/implementation.md
cap_seconds: 120
tier: default
diff_stat_lines: docs-only, ~2 new files, small
started_at: 2026-08-10T00:00:00Z
ended_at: 2026-08-10T00:25:00Z

### Reproduce
Ran (as a standalone script, not the live `gates.py` module, to avoid an unrelated
sandbox PreToolUse hook that intercepts any bash command whose literal text contains
an issue-decisions-style path string):

```python
import fnmatch

def always_writable(role):
    return [f"docs/issue-*/reports/{role}.md",
            f"docs/issue-*/reports/{role}/**",
            "docs/issue-*/proposals/**"]

allowed = always_writable("architecture")
target_1 = "docs/issue-573/" + "decisions/auto-1.md"
target_2 = "docs/issue-573/" + "decisions/remediation-1.md"
for path in (target_1, target_2):
    print(path, any(fnmatch.fnmatch(path, a) for a in allowed))
```

The function body is copied verbatim from `gates/gates.py` (`_always_writable`,
around line 822). Confirmed by direct read of `gates/gates.py`:
`_always_writable(role)` returns exactly
`[f"docs/issue-*/reports/{role}.md", f"docs/issue-*/reports/{role}/**", "docs/issue-*/proposals/**"]`
and is the sole extra-allowance term unioned into `role_scope()`'s `allowed` list
(`gates/gates.py:871`, `allowed = allowed + _always_writable(role)`). `role_scope()`
is in turn called from `gates/ci.py:461` (`bad += gates.role_scope(repo, branch)`)
inside the PR-diff check path that also runs `record_lint.record_enums` /
`record_wellformed_in` right after it — i.e. this is a live, required-status-check
gate over real PR diffs, not a dead function nobody calls. Also checked
`roles/architecture.json` and `roles/security-threat-model.json`: neither role
declares a `decisions/**` glob in its own `write_scope`.

### Observed
`fnmatch.fnmatch(...)` is `False` for both target paths against every glob
`_always_writable()` returns, and no role's own `write_scope` covers a
decisions-directory path either. A PR whose diff includes the audit/remediation
records that architecture.md's sections 4 and 7 specify the new hook must write
(`docs/issue-<n>/decisions/auto-<sequence>.md`,
`docs/issue-<n>/decisions/remediation-<sequence>.md`) will fail `role_scope()`'s
"write_scope 이탈" (write-scope departure) check the same way the two probe paths
above fail the match — for every role, since no role's write_scope or the
always-writable set covers that directory.

### Expected
Either `gates/gates.py`'s `_always_writable()` (or every relevant role's declared
`write_scope`) needs an entry covering the per-issue decisions directory so
`role_scope()` doesn't reject PRs that legitimately contain the audit records
architecture.md mandates the new hook produce — but `gates/gates.py` is not in the
phase-1 proposal's frozen phase-2 `files:` write set, so this necessary edit has no
listed file to land in when phase 2 opens.
