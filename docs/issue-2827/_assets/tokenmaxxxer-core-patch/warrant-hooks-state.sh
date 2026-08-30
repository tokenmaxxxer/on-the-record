#!/usr/bin/env bash
# SessionStart hook: rebuilds work-unit state from the repository.
#
# The point of putting state on disk is that a new session can pick up an
# interrupted unit without being told. This reads the proposal files and git,
# and says where things stand. It writes nothing.
# Kill switch: export WARRANT_OFF=1

. "${CLAUDE_PLUGIN_ROOT_CORE:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)}/hooks/lib/gate-lib.sh" || { echo "state.sh: cannot source gate-lib.sh" >&2; exit 2; }
gate_trap_fail_closed
set -uo pipefail
gate_kill_switch_active "${WARRANT_OFF:-}" || { trap - EXIT; exit 0; }

command -v python3 >/dev/null 2>&1 || { trap - EXIT; exit 0; }

root="${CLAUDE_PROJECT_DIR:-$PWD}"
root="$(git -C "$root" rev-parse --show-toplevel 2>/dev/null)" || { trap - EXIT; exit 0; }
[ -n "$root" ] || { trap - EXIT; exit 0; }

branch="$(git -C "$root" rev-parse --abbrev-ref HEAD 2>/dev/null)"

# issue-scoped session (CLAUDE_SKILL set AND branch resolves to exactly
# issue-<n>/<CLAUDE_SKILL>, the same detection warrant-protocol's own
# hunt-record routing uses): a role session only ever writes its own
# proposals under docs/issue-<n>/proposals/ (the per-issue layout every
# --skills spawn uses per on-the-record#2572) and only ever acts inside
# its own issue's tree — the top-level docs/proposals/ directory holds
# OTHER units it has no mandate to touch. Scope the scan there instead;
# fall back to the top-level directory unchanged for a non-issue-scoped
# (interactive/operator) session.
proposals_rel="docs/proposals"
if [ -n "${CLAUDE_SKILL:-}" ]; then
  case "$branch" in
    issue-*/"${CLAUDE_SKILL}")
      issue_n="${branch#issue-}"
      issue_n="${issue_n%%/*}"
      proposals_rel="docs/issue-${issue_n}/proposals"
      ;;
  esac
fi
[ -d "$root/$proposals_rel" ] || { trap - EXIT; exit 0; }

WARRANT_ROOT="$root" WARRANT_BRANCH="$branch" WARRANT_PROPOSALS_REL="$proposals_rel" python3 <<'PY'
import os
import re
import subprocess
import sys
import time

root = os.environ["WARRANT_ROOT"]
branch = os.environ.get("WARRANT_BRANCH", "")
proposals_rel = os.environ["WARRANT_PROPOSALS_REL"]
proposals = os.path.join(root, *proposals_rel.split("/"))

STATUS = re.compile(r"^status:\s*([A-Za-z]+)\s*(?:#.*)?$", re.M)

# issue-189 decision 3: reporting-only auto-expiry. Mirrors hunt-guard.sh's
# STALE_SECONDS pattern (hunt-guard.sh:85) for a different kind of
# staleness in the same repo. No new `gh` call: this reads the same
# per-file `git log` this pass already runs (line below), never an issue
# timestamp. A stale open unit is labeled "deferred (auto, stale since
# <timestamp>)" in the report — never a write to the unit's own
# status:/loop_state field; only an actual human/role act changes those.
STALE_SECONDS = 60 * 60 * 24 * 14  # 14 days


# F5 (issue-305): a proposal with an opening `---` fence but no matching
# closing fence was silently skipped, byte-identical to "not a proposal
# file at all" — exactly the mid-edit/broken-frontmatter case a human is
# most likely to need surfaced. _UNCLOSED distinguishes that from the
# genuine not-a-proposal case (no opening fence) so it can be reported
# instead of dropped.
_UNCLOSED = object()


def frontmatter(path):
    try:
        with open(path, encoding="utf-8-sig") as handle:
            text = handle.read(65536)
    except (OSError, UnicodeDecodeError):
        return None
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return _UNCLOSED
    return text[3:end]


open_units = []
closed_units = []
malformed_units = []
for name in sorted(os.listdir(proposals)):
    if not name.endswith(".md") or name == "README.md":
        continue
    block = frontmatter(os.path.join(proposals, name))
    if block is None:
        continue
    if block is _UNCLOSED:
        malformed_units.append(proposals_rel + "/" + name)
        continue
    found = STATUS.search(block)
    status = found.group(1).lower() if found else "proposed"
    if status in ("proposed", "approved"):
        open_units.append((status, proposals_rel + "/" + name))
    elif status in ("withdrawn", "rejected"):
        closed_units.append((status, proposals_rel + "/" + name))

if not open_units and not closed_units and not malformed_units:
    sys.exit(0)

def stale_suffix(path):
    try:
        out = subprocess.run(
            ["git", "-C", root, "log", "-1", "--format=%ct", "--", path],
            capture_output=True, text=True, timeout=10,
        )
        ts = int(out.stdout.strip()) if out.returncode == 0 and out.stdout.strip() else None
    except (OSError, subprocess.SubprocessError, ValueError):
        ts = None
    if ts is None:
        return ""
    if time.time() - ts < STALE_SECONDS:
        return ""
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))
    return " — deferred (auto, stale since %s)" % stamp


lines = []
if open_units:
    lines.append("warrant: open work units in this repository —")
for status, path in open_units:
    if status == "approved":
        try:
            shipped = subprocess.run(
                # -F: a proposal filename may contain regex metacharacters.
                ["git", "-C", root, "log", "--oneline", "-F", "--grep", "Proposal: " + path],
                capture_output=True, text=True, timeout=10,
            ).stdout.strip().splitlines()
        except (OSError, subprocess.SubprocessError):
            shipped = []
        lines.append(
            "  APPROVED, in progress: %s — %d commit(s) so far, branch %s. "
            "Read it before writing anything; the write set in its frontmatter is still frozen.%s"
            % (path, len(shipped), branch or "?", stale_suffix(path))
        )
    else:
        lines.append(
            "  AWAITING APPROVAL: %s — do not start this work until the user approves it.%s"
            % (path, stale_suffix(path))
        )

if closed_units:
    if lines:
        lines.append("")
    lines.append("warrant: closed (withdrawn/rejected) — history —")
    for status, path in closed_units:
        lines.append("  %s: %s" % (status.upper(), path))

if malformed_units:
    if lines:
        lines.append("")
    lines.append("warrant: malformed — never picked up, needs a human look —")
    for path in malformed_units:
        lines.append("  %s: opening --- frontmatter fence with no matching closing --- fence" % path)

print("\n".join(lines))
PY

exit 0
