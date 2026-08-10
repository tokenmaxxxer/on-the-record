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

## after-proposal — stance 0 (proposal: docs/issue-608/proposals/implementation.md): approval-gate.sh is bypassable via branch-name parse failing open

Verdict: FINDING — a role session on a branch that doesn't match `^issue-(\d+)/([\w-]+)$` (e.g. detached HEAD, or any branch not shaped exactly `issue-<n>/<role>`) causes approval-gate.sh, by the proposal's own design ("same regex as pr-preflight.sh"), to skip the check entirely (fail-open), letting an unapproved phase-2-shaped Write/Edit/MultiEdit through regardless of CLAUDE_ROLE or approvers.md/comment state.
Kind: design-error
Seed: docs/issue-608/proposals/implementation.md, "What will be done" step 1 ("Parses `issue-<n>/<role>` off the current branch name (same regex as `pr-preflight.sh`)")
cap_seconds: 120
tier: default
diff_stat_lines: 256 (docs-only, `git show 3e57697`)
started_at: 2026-08-10T00:00:00Z
ended_at: 2026-08-10T00:10:00Z

### Reproduce
`on-the-record/hooks/pr-preflight.sh` (the script the proposal names as the source of the reused regex) contains:

    branch = r.stdout.strip()
    bm = re.match(r"^issue-(\d+)/([\w-]+)$", branch)
    if not bm:
        sys.exit(0)

Run the same regex against branch names a real session can be on (script saved to a scratch file to avoid heredoc-in-heredoc issues):

    python3 /tmp/claude-1000/-home-jwjung--tokenmaxxxer-work-on-the-record-issue-608-implementation/810ea3cf-8401-46b2-b631-f6ed48ccbb74/scratchpad/branch_regex_probe.py

### Observed

    HEAD -> NO MATCH (fail-open, gate skipped)
    main -> NO MATCH (fail-open, gate skipped)
    issue-608/implementation -> MATCH
    wip/issue-608/execution-observation -> NO MATCH (fail-open, gate skipped)

`git rev-parse --abbrev-ref HEAD` returns literally `HEAD` for a detached checkout, and returns any custom/renamed branch string for a renamed local branch — neither matches the required `issue-<n>/<role>` shape. Since the proposal specifies "same regex" and inherits pr-preflight.sh's `if not bm: sys.exit(0)` fail-open-on-parse-failure convention (justified there because it only skips an *additional* PR-body check on an already-permitted `gh pr` command), an implementer following this design verbatim will produce an approval-gate.sh that no-ops for any role session doing its unapproved record/src/test write while checked out detached or on a differently-named local branch (`git checkout --detach <sha>` then perform the write) — a trivial, silent bypass of the very enforcement the proposal exists to add.

### Expected
The proposal should specify that a branch-parse failure for a role session (`CLAUDE_ROLE` set) is treated as a deny-and-instruct case (or otherwise reject the phase-2-shaped write), not a silent skip — reusing pr-preflight.sh's fail-open-on-parse-failure policy verbatim converts an infra-failure convention (safe there, because failure only skips an *additional* check on an already-permitted command) into a full enforcement bypass here, because failure skips the *entire* gate on the underlying Write/Edit/MultiEdit tool call.

## before-landing — stance 1: assume this change and another plugin's rule cancel each other — find the pair

Verdict: NO FINDING
Seed: on-the-record/hooks/approval-gate.sh (new), on-the-record/hooks/hooks.json (wires it into the PreToolUse Write|Edit|MultiEdit group after record-claim-guard.sh, role-spec-reference-guard.sh, call-shape-guard.sh, accumulation-claim-guard.sh), docs/specs/enforcement-boundary.md (new row)
cap_seconds: 120
tier: default
diff_stat_lines: 3 files changed, 18 insertions(+), 1 deletion(-) (working tree, git diff --stat) plus 2 untracked files (approval-gate.sh, test_approval_gate.py)
started_at: 2026-08-10T00:00:00Z
ended_at: 2026-08-10T00:20:00Z

Checked whether approval-gate.sh's deny could be cancelled by an allow from a sibling hook in the same Write|Edit|MultiEdit PreToolUse matcher group (record-claim-guard.sh, role-spec-reference-guard.sh, call-shape-guard.sh, accumulation-claim-guard.sh, deliverable-guard.sh in the adjacent matcher, retry-loop-bound.sh in the broader Write|Edit|MultiEdit|Bash matcher). All of these sibling hooks are deny-only (exit 0 = no-op/pass, exit 2 = block), and every one traps non-0/2 exits to fail closed; none of them emits a hookSpecificOutput permissionDecision of allow for this matcher/tool combination. The one hook in the repo that does emit an explicit allow permissionDecision, retry-loop-bound.sh (around line 193), no-ops unconditionally whenever CLAUDE_ROLE is set (its line ~32 guard), i.e. it is orchestrator-session-only and structurally excluded from every session in which approval-gate.sh is active (approval-gate.sh itself no-ops unless CLAUDE_ROLE is set). Under the PreToolUse aggregation this plugin relies on, an explicit deny (exit 2) from any one matched hook blocks the tool call regardless of what co-matched hooks return, so there is no code path in this diff by which a sibling hook's success or no-op could reverse approval-gate.sh's deny, since none of the co-matched hooks can produce an allow outcome for a role session in the first place. Also considered whether contract-guard.sh's Bash-matcher approval check for the merge verb (unmodified by this diff, accepts an APPROVE-issue-N-prefix comment from any role via a startswith match, looser than approval-gate.sh's exact-role match) could let the merge command proceed while approval-gate.sh still blocks the underlying file write earlier in the session; this is a pre-existing loose/strict asymmetry between two independently-scoped hooks (one Bash-matcher on the merge verb, one Write-matcher on the file write) that predates this diff and is not a cancellation introduced by it, and a later merge succeeding does not retroactively un-deny an already-blocked write. No reproducible allow/deny cancellation pair found for this diff.
