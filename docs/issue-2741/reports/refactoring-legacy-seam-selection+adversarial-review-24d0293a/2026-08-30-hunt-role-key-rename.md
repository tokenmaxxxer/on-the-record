---
proposal: docs/issue-2741/proposals/role-key-rename.md
---

# Hunt record — role-key-rename

## before-landing — stance 0: assume the gate/hook just touched is bypassable — find the bypass

Verdict: FINDING — approval-gate.sh silently drops phase-2 approval enforcement (zero stderr diagnostic) for any workspace still carrying a pre-rename .on-the-record/role.json sidecar ({"role": ...}) whose branch name does not match issue-<n>/<skill>, whereas the pre-rename hook enforced (or at least logged a fail-open reason) in the identical scenario.
Kind: silent-failure
Seed: commit 4cda5c3a, on-the-record/hooks/approval-gate.sh (and structurally identical sidecar-read blocks in contract-guard.sh, call-shape-guard.sh, deviation-log-guard.sh, pr-preflight.sh, skill-verdict-guard.sh)
cap_seconds: 180
tier: default (hook/gate files, full tier per dispatch instructions)
diff_stat_lines: 34 files changed, 282 insertions(+), 138 deletions(-) (repo-wide commit); approval-gate.sh itself: 8 lines
started_at: 2026-08-30T00:00:00+09:00
ended_at: 2026-08-30T00:20:00+09:00

### Reproduce
```
# Build a workspace whose branch does NOT match issue-<n>/<skill> (the exact
# case the role.json sidecar (#1814) exists to cover -- e.g. a worktree left
# on a differently-named branch, or a detached HEAD), carrying a role.json
# sidecar written by the PRE-rename spawn.py (key "role", not "skill" --
# this rename is forward-only, no dual read, no migration):

WORK=$(mktemp -d); cd "$WORK"
git init -q; git checkout -q -b main
mkdir -p .on-the-record docs/specs docs/issue-99/reports
printf -- '- approver1\n' > docs/specs/approvers.md
git add -A; git commit -qm init
python3 -c "import json; json.dump({'role':'blah','issue':99}, open('.on-the-record/role.json','w'))"

PAYLOAD=$(python3 -c "import json,sys; print(json.dumps({'tool_name':'Write','tool_input':{'file_path':'docs/issue-99/reports/blah.md'},'cwd':sys.argv[1],'session_id':'sess1'}))" "$WORK")
export CLAUDE_SKILL=blah ORCHESTRATE_OFF=0 AG_PAYLOAD="$PAYLOAD"
unset CORE_BUILD_NOW

# pre-rename approval-gate.sh, extracted via: git show 4cda5c3a^:on-the-record/hooks/approval-gate.sh > /tmp/approval-gate-old.sh
printf '%s' "$PAYLOAD" | bash /tmp/approval-gate-old.sh; echo "exit=$?"

# post-rename approval-gate.sh (this commit, HEAD of on-the-record repo)
printf '%s' "$PAYLOAD" | bash on-the-record/hooks/approval-gate.sh; echo "exit=$?"
```

### Observed
Pre-rename script: sidecar resolves (issue=99, role=blah) via the old "role" key, so the gate proceeds all the way to the approvers/gh check, and explains its fail-open on stderr:
```
approval-gate: gh issue view lookup failed — cannot verify approval state, failing open (infrastructure failure, not an approval-state failure).
exit=0
```
Post-rename script: sidecar.get("skill") is None for the legacy {"role": ...} file, so the shape check fails; issue/branch_role stay None; the branch-regex fallback also fails ("main" doesn't match `issue-<n>/<skill>`), landing on `sys.exit(0)` at the "unparseable branch — accepted fail-open" line, which writes no stderr at all:
```
exit=0
(no stderr output)
```
Both exit 0, but the post-rename path reaches allow through a completely silent branch that never even attempts to read docs/specs/approvers.md or contact `gh` — there is no trace in stderr that any check was skipped, unlike every other fail-open branch in the same file (gh-missing, gh-lookup-failure, snapshot-parse-failure) which all log a reason.

### Expected
A gate whose enforcement source (branch-regex vs. sidecar) is a forward-incompatible rename should, at minimum, not silently regress a previously-enforced (or previously-diagnosed) code path to a diagnostic-free fail-open for workspaces spawned before the rename lands. Every other fail-open branch in approval-gate.sh writes an explanatory stderr line; this one — now newly reachable for any pre-rename sidecar on a non-issue-N/skill branch — does not, so an operator watching stderr for fail-open notices would see nothing at all.
