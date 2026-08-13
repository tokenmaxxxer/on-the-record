#!/usr/bin/env bash
# PreToolUse (Bash): issue #1130 routing-fix, cause-b role test-authoring.
# roles/specs/test-authoring.spec.json's use_when.trigger names
# record_absent_for: "test-authoring" — this hook is the missing consumer
# (docs/issue-1130/reports/requirements-engineering/scout-brief.md: the
# hook already works but never causes the role's own session to spawn).
#
# Fires on a `gh pr merge` invocation. When the target checkout's diff
# between its default branch and HEAD touches a path matching the spec's
# own trigger.path_patterns, denies the merge unless
# docs/issue-<n>/reports/test-authoring.md exists for the issue resolved
# from the current branch name (issue-<n>/<role>).
#
# Presence-check only — this does not judge test quality, only whether the
# routing record exists. Target-root-anchored: all paths resolve against
# tool_input.cwd/e.cwd, never this repo's own layout (issue #1130 req#4).
#
# Kill switch: ORCHESTRATE_OFF=1.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 2

IFS='' read -r -d '' GUARD <<'PY' || true
import fnmatch, json, os, re, subprocess, sys

ROLE = "test-authoring"

def deny(msg):
    sys.stderr.write("test-authoring-spawn-check: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("SPAWN_CHECK_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str) or not re.search(r"\bgh\s+pr\s+merge\b", cmd):
    sys.exit(0)
if "`" in cmd or "$(" in cmd:
    sys.exit(0)

run_cwd = ti.get("cwd") if isinstance(ti.get("cwd"), str) else (e.get("cwd") or os.getcwd())

try:
    spec = json.load(open(os.path.join(run_cwd, "roles", "specs", ROLE + ".spec.json")))
except (OSError, ValueError):
    sys.exit(0)
trigger = (spec.get("use_when") or {}).get("trigger") if isinstance(spec.get("use_when"), dict) else None
if not isinstance(trigger, dict):
    sys.exit(0)
path_patterns = trigger.get("path_patterns") or []

try:
    branch = subprocess.run(
        ["git", "-C", run_cwd, "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, timeout=10,
    ).stdout.strip()
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
m = re.match(r"^issue-(\d+)/", branch)
if not m:
    sys.exit(0)  # not an issue-scoped role branch — unreached
issue = m.group(1)

try:
    diff = subprocess.run(
        ["git", "-C", run_cwd, "diff", "--name-only", "origin/main...HEAD"],
        capture_output=True, text=True, timeout=15,
    )
    changed = [l for l in diff.stdout.splitlines() if l.strip()]
except (OSError, subprocess.SubprocessError):
    changed = []

if not changed or not path_patterns:
    sys.exit(0)

matched = [f for f in changed if any(fnmatch.fnmatch(f, pat) for pat in path_patterns)]
if not matched:
    sys.exit(0)

record_path = os.path.join(run_cwd, "docs", "issue-%s" % issue, "reports", ROLE + ".md")
if os.path.isfile(record_path):
    sys.exit(0)

deny(
    "trigger path(s) %s changed on issue-%s but no %s exists yet "
    "(roles/specs/%s.spec.json use_when.trigger.record_absent_for)"
    % (matched, issue, os.path.relpath(record_path, run_cwd), ROLE)
)
PY

SPAWN_CHECK_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
