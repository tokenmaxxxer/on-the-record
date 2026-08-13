#!/usr/bin/env bash
# PreToolUse (Bash): deny fail-closed any call shape that would create a
# pull request against the upstream on-the-record repo (issue #1131 req#4
# — "Consumers file ISSUES ONLY — never PRs. The channel must not offer,
# scaffold, or allow an upstream PR path from consumer sessions." The
# constraint must be structurally enforced, not advisory (issue #1131
# Acceptance).
#
# Coverage surface widened by the post-proposal warrant hunt
# (docs/issue-1131/reports/requirements-engineering/2026-08-13-hunt-upstream-defect-channel-requirements.md):
# a single literal `gh pr create` match would leave these shapes open —
#   - `gh pr create` itself (and any of its aliases: --fill, -R, etc.)
#   - `gh api` POST against a `/pulls`-shaped endpoint
#     (`repos/OWNER/REPO/pulls`)
#   - GraphQL `createPullRequest` mutation via `gh api graphql`
#   - `gh pr create` driven by a `GH_REPO`/`GH_HOST` env-var prefix instead
#     of an explicit `--repo` flag
#   - non-`gh` tooling: `hub pull-request`, or `curl`/`wget` POSTing
#     directly to api.github.com's pulls endpoint or the graphql endpoint
#     with a createPullRequest-shaped body
#
# Scoped (issue #1171): deny only within the upstream-defect channel's own
# flow, never a role session's own delivery PR against origin. Before
# #1171, this fired on every Bash call regardless of target or session —
# which also denied issue-1163's own delivery-PR creation against origin
# (docs/issue-1163/reports/implementation.md, 2026-08-13), because this
# repo's own origin (tokenmaxxxer/on-the-record) is also the channel's
# example upstream target, so a target-repo check alone cannot tell a
# same-repo delivery PR from a same-repo channel PR.
#
# In-scope-for-denial iff EITHER:
#   (a) the acting role is the channel's own role
#       (CLAUDE_ROLE == "upstream-defect-report", read via the
#       session-role-bind snapshot the same way approval-gate.sh already
#       does — issue #698's pattern — falling back to the live env var), or
#   (b) the call shape carries an extractable target repo
#       (--repo/-R flag, GH_REPO env prefix, a repos/OWNER/REPO/pulls
#       path, or a curl URL's repos/OWNER/REPO/pulls segment) that
#       differs from this session's own git origin repo.
# GraphQL and `hub pull-request` carry no extractable target repo, so
# they are in-scope only via (a). Origin-resolution failure (no git
# repo, no origin remote) fails open on signal (b) alone — same posture
# as approval-gate.sh's unparseable-branch fail-open — leaving (a) as the
# only remaining signal.
#
# Shape: stdin JSON payload, trap remapping unexpected exit to 2 (fail
# closed by construction), ORCHESTRATE_OFF kill switch, python3 for the
# actual logic, exit 2 + stderr message to deny, exit 0 to pass.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 2

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, subprocess, sys

CHANNEL_ROLE = "upstream-defect-report"

def deny(msg):
    sys.stderr.write("upstream-defect-scope-guard: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("UDSG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str) or not cmd.strip():
    sys.exit(0)

lowered = cmd.lower()

# --- role identity: prefer the SessionStart-bound snapshot (issue #698) ----
# Same pattern as approval-gate.sh: the snapshot can't be rebound by a later
# Bash-tool re-export of CLAUDE_ROLE within this same session.
role = os.environ.get("CLAUDE_ROLE", "")
session_id = e.get("session_id")
if isinstance(session_id, str) and session_id:
    state_dir = os.environ.get(
        "OTR_ROLE_BIND_STATE_DIR",
        os.path.join(os.environ.get("TMPDIR", "/tmp"), "otr-role-bind"),
    )
    safe_session = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)
    snapshot_path = os.path.join(state_dir, safe_session + ".json")
    try:
        with open(snapshot_path, encoding="utf-8") as f:
            snapshot = json.load(f)
        if isinstance(snapshot, dict) and isinstance(snapshot.get("role"), str):
            role = snapshot["role"]
    except (OSError, ValueError):
        pass  # no snapshot yet — fall back to the live env var
channel_role_active = role == CHANNEL_ROLE

# --- this session's own git origin repo (owner/repo, lowercased) -----------
def origin_repo():
    cwd = e.get("cwd") if isinstance(e.get("cwd"), str) and e.get("cwd") else None
    try:
        r = subprocess.run(
            ["git", "-C", cwd or ".", "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    url = r.stdout.strip()
    m = re.search(r"[:/]([^/:\s]+/[^/:\s]+?)(\.git)?$", url)
    return m.group(1).lower() if m else None

ORIGIN_REPO = origin_repo()

def in_scope(target_repo):
    """PR-creation call is in-scope for denial iff the channel's own role
    is active, or a target repo was extracted and it isn't this session's
    origin repo. `target_repo=None` (no extractable target, or origin
    unresolvable) relies on the role signal alone."""
    if channel_role_active:
        return True
    if target_repo is not None and ORIGIN_REPO is not None:
        return target_repo.lower() != ORIGIN_REPO
    return False

def extract_repo_flag(text):
    m = re.search(r"(?:--repo|-r)[= ]\"?([^\s\"]+/[^\s\"]+)", text)
    return m.group(1) if m else None

def extract_gh_repo_env(text):
    m = re.search(r"\bgh_repo=(\S+)", text)
    return m.group(1) if m else None

def extract_repos_path(text):
    m = re.search(r"repos/([^/\s]+/[^/\s]+?)/pulls\b", text)
    return m.group(1) if m else None

# 1. `gh pr create` literally, or prefixed by a `GH_REPO=`/`GH_HOST=` env
#    var assignment instead of an explicit --repo flag — still the same
#    verb underneath.
if re.search(r"(^|[;&|]\s*|\bgh_repo=\S+\s+|\bgh_host=\S+\s+)gh\s+pr\s+create\b", lowered):
    target = extract_repo_flag(lowered) or extract_gh_repo_env(lowered)
    if in_scope(target):
        deny(
            "`gh pr create` (including a GH_REPO/GH_HOST-env-var-prefixed "
            "invocation) is denied — the upstream defect channel files issues "
            "only, never PRs (issue #1131 req#4)."
        )

# 2. `gh api` POST against a /pulls-shaped endpoint.
if re.search(r"\bgh\s+api\b", lowered) and re.search(r"/pulls\b", lowered):
    if re.search(r"(--method\s+post|-x\s*post)", lowered) or "/pulls" in lowered:
        target = extract_repos_path(lowered) or extract_repo_flag(lowered)
        if in_scope(target):
            deny(
                "`gh api` against a /pulls endpoint is denied — this is a "
                "PR-creation call shape, and the upstream defect channel files "
                "issues only, never PRs (issue #1131 req#4)."
            )

# 3. GraphQL createPullRequest mutation via `gh api graphql`. No target
#    repo is extractable from the call shape itself — in-scope via the
#    role signal only.
if re.search(r"\bgh\s+api\s+graphql\b", lowered) and "createpullrequest" in lowered:
    if in_scope(None):
        deny(
            "a GraphQL createPullRequest mutation is denied — this is a "
            "PR-creation call shape, and the upstream defect channel files "
            "issues only, never PRs (issue #1131 req#4)."
        )

# 4. non-`gh` tooling: `hub pull-request`. No target repo is extractable
#    from the call shape itself — in-scope via the role signal only.
if re.search(r"\bhub\s+pull-request\b", lowered):
    if in_scope(None):
        deny(
            "`hub pull-request` is denied — the upstream defect channel files "
            "issues only, never PRs (issue #1131 req#4)."
        )

# 5. `curl`/`wget` POSTing directly to the GitHub REST pulls endpoint or
#    the GraphQL endpoint with a createPullRequest-shaped body.
if re.search(r"\b(curl|wget)\b", lowered):
    hits_rest_pulls = bool(re.search(r"api\.github\.com/repos/[^/\s]+/[^/\s]+/pulls", lowered))
    hits_graphql_pr = "api.github.com/graphql" in lowered and "createpullrequest" in lowered
    if hits_rest_pulls:
        target = extract_repos_path(lowered)
        if in_scope(target):
            deny(
                "a direct curl/wget call against the GitHub pulls REST endpoint "
                "is denied — the upstream defect channel files issues only, "
                "never PRs (issue #1131 req#4)."
            )
    elif hits_graphql_pr:
        if in_scope(None):
            deny(
                "a createPullRequest GraphQL mutation is denied — this is a "
                "PR-creation call shape, and the upstream defect channel files "
                "issues only, never PRs (issue #1131 req#4)."
            )

sys.exit(0)
PY

UDSG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
