#!/usr/bin/env bash
# PreToolUse (Bash): issue #1130 routing-fix, cause-b role
# issue-retrospective. roles/specs/issue-retrospective.spec.json's
# use_when.trigger names record_absent_for: "issue-retrospective" — this
# hook is the missing consumer (docs/issue-1130/reports/
# requirements-engineering/scout-brief.md: the role's board_condition
# names the right event, closing an issue, but nothing consults it).
#
# Fires on a `gh issue close <n>` invocation. Denies the close unless
# docs/issue-<n>/reports/issue-retrospective.md already exists in the
# target checkout. Presence-check only, and deliberately blunt: the
# board_condition's "non-incident" qualifier is not mechanically
# classifiable here (same posture as design-rationale-guard.sh's
# presence-only precedent) — every issue close is treated as requiring
# the record.
#
# Target-root-anchored: all paths resolve against tool_input.cwd/e.cwd,
# never this repo's own layout (issue #1130 req#4).
#
# Kill switch: ORCHESTRATE_OFF=1.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 2

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, sys

ROLE = "issue-retrospective"

def deny(msg):
    sys.stderr.write("issue-retrospective-spawn-check: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("SPAWN_CHECK_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str) or not re.search(r"\bgh\s+issue\s+close\b", cmd):
    sys.exit(0)
if "`" in cmd or "$(" in cmd:
    sys.exit(0)

m = re.search(r"\bgh\s+issue\s+close\s+(?:--\S+\s+\S+\s+)*(\d+)", cmd)
if not m:
    sys.exit(0)  # implicit/unresolvable issue number — unreached
issue = m.group(1)

run_cwd = ti.get("cwd") if isinstance(ti.get("cwd"), str) else (e.get("cwd") or os.getcwd())

try:
    spec = json.load(open(os.path.join(run_cwd, "roles", "specs", ROLE + ".spec.json")))
except (OSError, ValueError):
    sys.exit(0)
trigger = (spec.get("use_when") or {}).get("trigger") if isinstance(spec.get("use_when"), dict) else None
if not isinstance(trigger, dict) or trigger.get("record_absent_for") != ROLE:
    sys.exit(0)

record_path = os.path.join(run_cwd, "docs", "issue-%s" % issue, "reports", ROLE + ".md")
if os.path.isfile(record_path):
    sys.exit(0)

deny(
    "issue-%s closing but no %s exists yet "
    "(roles/specs/%s.spec.json use_when.trigger.record_absent_for)"
    % (issue, os.path.relpath(record_path, run_cwd), ROLE)
)
PY

SPAWN_CHECK_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
