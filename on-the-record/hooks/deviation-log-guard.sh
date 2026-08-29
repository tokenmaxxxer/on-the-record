#!/usr/bin/env bash
# Stop: no-traceless-deviation invariant for issue #803's deviation loop
# (docs/issue-803/proposals/2026-08-11-self-driven-deviation-loop.md,
# docs/issue-803/proposals/2026-08-12-implementation-deviation-loop.md).
#
# Binds in BOTH orchestrator and spawned-session contexts (issue #983 —
# previously a CLAUDE_SKILL-unset orchestrator-only gate, matching
# stop-gate.sh's skeleton, left role sessions structurally unenforced;
# audit E Finding 1, docs/issue-754/reports/defect-verification.md). The
# branch-to-path regex below already resolves a spawned session's own
# issue-<n>/<role> branch correctly, so no other change was needed to
# extend coverage. Same fail-closed trap / ORCHESTRATE_OFF kill switch as
# stop-gate.sh's skeleton — but stop-gate.sh's
# own check mechanism (last_assistant_message text only, no file/git
# access) cannot maintain a "no matching deviation-log append this turn"
# fact (warrant hunt finding,
# docs/issue-803/reports/implementation/2026-08-12-hunt-implementation-deviation-loop.md,
# stance 3). This guard instead follows product-capture-stopgate.sh's
# mechanism: reads transcript_path off the raw Stop event JSON, scans the
# transcript for a recognized-deviation marker, and separately checks via
# git diff / git log -p against the deviation-log path(s) whether a
# matching append actually landed.
#
# issue #2348: deviation-log.md sharded per session, same conflict-
# elimination shape issue #2333 shipped for consult-log.md -- see
# deviation_log.py's module docstring for the shard-id/aggregation
# reasoning. This guard does not need to compute a session's own shard id
# to verify one landed: it checks whether the shard DIRECTORY gained any
# added line this turn (git diff/log -p accept a directory pathspec the
# same way they accept a file one), which is exactly as precise as the
# old single-file check was in a single-workspace-per-session model --
# `git diff` only ever shows this session's own working-tree changes, so a
# directory-level hit cannot be another session's shard.
#
# Path also now folds in the pre-existing, previously unenforced role-
# scoped convention many spawned sessions already use
# (docs/issue-<n>/reports/<role>/deviation-log/ instead of the flat
# docs/issue-<n>/reports/deviation-log/) -- role comes ONLY from
# $CLAUDE_SKILL (same signal board-gate's R4 already treats as
# authoritative for a spawned session's own subtree), never re-derived from
# the branch name: a spawned session is defined by CLAUDE_SKILL being set, not
# by what its branch happens to look like, and the branch is already
# required to equal issue-<n>/<CLAUDE_SKILL> for a spawned session (board-gate
# R4) rather than being an independent source for it. No CLAUDE_SKILL (the
# orchestrator) means no role component, same as before this issue.
#
# Refuses via hookSpecificOutput.additionalContext, never decision:"block"
# — matching stop-gate.sh's own house-style rationale that a heuristic
# misfire on unusual phrasing should not discard the whole turn.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"

command -v python3 >/dev/null 2>&1 || exit 2

REPO="$(pwd -P)"

IFS='' read -r -d '' CHECK <<'PY' || true
import json, os, re, subprocess, sys

try:
    e = json.loads(os.environ.get("STOP_PAYLOAD", ""))
except ValueError:
    sys.exit(2)
if not isinstance(e, dict):
    sys.exit(2)

# Issue #1725: honor the Stop-hook contract's stop_hook_active field --
# the harness treats ANY Stop additionalContext as inject-and-resume, so
# a forced-retry turn must emit nothing at all. Mirrors #1718's
# decision-queue-stopgate.sh placement: before any other field of e is
# read.
if e.get("stop_hook_active"):
    sys.exit(0)

transcript_path = e.get("transcript_path")
if not isinstance(transcript_path, str) or not transcript_path:
    sys.exit(0)
if not os.path.isfile(transcript_path):
    sys.exit(0)

repo = os.environ.get("DEVLOG_GUARD_REPO", "")

# Recognized-deviation marker: the assistant's own turn text stating one
# of the deviation-loop's classification outcomes (inline/filed) for a
# concrete deviation — mirrors the RECOGNIZE/CLASSIFY vocabulary in
# directive.sh's injected paragraph and docs/handbooks/deviation-loop.md.
MARKER_RE = re.compile(
    r"(deviation[^.\n]{0,80}(inline-fix|file-as-issue|inline fix|filed as"
    r"\s+(an\s+)?issue)|"
    r"(inline-fix|file-as-issue)[^.\n]{0,80}deviation)",
    re.IGNORECASE,
)


def flat_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                t = block.get("text")
                if isinstance(t, str):
                    parts.append(t)
        return "\n".join(parts) if parts else None
    return None


marker_found = False
try:
    with open(transcript_path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if not isinstance(entry, dict) or entry.get("type") != "assistant":
                continue
            message = entry.get("message")
            if not isinstance(message, dict):
                continue
            text = flat_text(message.get("content"))
            if not text:
                continue
            if MARKER_RE.search(text):
                marker_found = True
                break
except OSError:
    sys.exit(0)

if not marker_found:
    sys.exit(0)

# --- prefer the .on-the-record/role.json lease sidecar (issue #1814) -------
# written by spawn.py's issue_workspace() at spawn time; carries the exact
# (possibly composed, e.g. "skill-a+skill-b-<disambiguator>") identity
# string the session was spawned under. Any absence/parse failure falls
# back to the branch-regex parse below.
issue_n, skill = None, None
try:
    with open(os.path.join(repo, ".on-the-record", "role.json"), encoding="utf-8") as f:
        sidecar = json.load(f)
    if (isinstance(sidecar, dict) and isinstance(sidecar.get("skill"), str)
            and isinstance(sidecar.get("issue"), int)):
        issue_n, skill = sidecar["issue"], sidecar["skill"]
except (OSError, ValueError):
    pass

if skill is None:
    branch_r = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo, capture_output=True, text=True, timeout=10,
    )
    branch = branch_r.stdout.strip() if branch_r.returncode == 0 else ""
    branch_m = re.match(r"^issue-(\d+)/([^/]+)$", branch)
    if branch_m:
        issue_n, skill = branch_m.group(1), branch_m.group(2)
    # CLAUDE_SKILL presence-only override: a session with no branch/sidecar
    # identity at all but a live CLAUDE_SKILL still scopes to its own dir.
    skill = skill or (os.environ.get("CLAUDE_SKILL") or None)

if issue_n is not None:
    base = os.path.join("docs", f"issue-{issue_n}", "reports")
    rel = os.path.join(base, skill, "deviation-log") if skill else os.path.join(base, "deviation-log")
else:
    rel = os.path.join("docs", "reports", "deviation-log")

added_lines = 0
for args in (
    ["git", "diff", "--unified=0", "--", rel],
    ["git", "log", "-1", "--format=", "-p", "--", rel],
):
    try:
        r = subprocess.run(
            args, cwd=repo, capture_output=True, text=True, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        continue
    for out_line in r.stdout.splitlines():
        if out_line.startswith("+") and not out_line.startswith("+++"):
            added_lines += 1

# issue #2348: sharding means a session's FIRST deviation-log entry for a
# given issue+role is now the common case, not a one-time-ever event --
# every session mints its own new shard file, and a brand-new file is
# untracked until something stages it. `git diff`/`git log -p` never
# report untracked paths at all, so relying on them alone would make the
# guard blind to exactly the case sharding makes common. `git status
# --porcelain` reports untracked ("??"), staged, and unstaged-modified
# paths alike, so it closes that gap regardless of which of the three
# states this turn's new/changed shard is currently in.
if added_lines == 0:
    try:
        st = subprocess.run(
            ["git", "status", "--porcelain", "--", rel],
            cwd=repo, capture_output=True, text=True, timeout=10,
        )
        if st.returncode == 0 and st.stdout.strip():
            added_lines = 1
    except (OSError, subprocess.SubprocessError):
        pass

if added_lines > 0:
    sys.exit(0)

out = {
    "hookSpecificOutput": {
        "hookEventName": "Stop",
        "additionalContext": (
            "deviation-log-guard: this turn's transcript names a recognized "
            "deviation (inline-fix or file-as-issue) but " + rel + " gained "
            "no new shard. Append the deviation-log entry (timestamp, "
            "inline/filed/resolved, description, and for filed/resolved the "
            "issue number/role/PR) to the path `spawn.py deviation-log-path "
            "--issue <n>` prints, before ending the turn — see "
            "docs/handbooks/deviation-loop.md."
        ),
    }
}
sys.stdout.write(json.dumps(out))
sys.exit(0)
PY

STOP_PAYLOAD="$payload" DEVLOG_GUARD_REPO="$REPO" python3 -c "$CHECK"
rc=$?
trap - EXIT
exit "$rc"
