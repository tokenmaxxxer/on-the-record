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
# Universal (fires on every Bash call), matching credential-network-guard.sh's
# posture — no per-session scoping, since a PR-creation call is denied
# everywhere it appears, not only inside this one channel's own command.
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
import json, os, re, sys

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

# 1. `gh pr create` literally, or prefixed by a `GH_REPO=`/`GH_HOST=` env
#    var assignment instead of an explicit --repo flag — still the same
#    verb underneath.
if re.search(r"(^|[;&|]\s*|\bgh_repo=\S+\s+|\bgh_host=\S+\s+)gh\s+pr\s+create\b", lowered):
    deny(
        "`gh pr create` (including a GH_REPO/GH_HOST-env-var-prefixed "
        "invocation) is denied — the upstream defect channel files issues "
        "only, never PRs (issue #1131 req#4)."
    )

# 2. `gh api` POST against a /pulls-shaped endpoint.
if re.search(r"\bgh\s+api\b", lowered) and re.search(r"/pulls\b", lowered):
    if re.search(r"(--method\s+post|-x\s*post)", lowered) or "/pulls" in lowered:
        deny(
            "`gh api` against a /pulls endpoint is denied — this is a "
            "PR-creation call shape, and the upstream defect channel files "
            "issues only, never PRs (issue #1131 req#4)."
        )

# 3. GraphQL createPullRequest mutation via `gh api graphql`.
if re.search(r"\bgh\s+api\s+graphql\b", lowered) and "createpullrequest" in lowered:
    deny(
        "a GraphQL createPullRequest mutation is denied — this is a "
        "PR-creation call shape, and the upstream defect channel files "
        "issues only, never PRs (issue #1131 req#4)."
    )

# 4. non-`gh` tooling: `hub pull-request`.
if re.search(r"\bhub\s+pull-request\b", lowered):
    deny(
        "`hub pull-request` is denied — the upstream defect channel files "
        "issues only, never PRs (issue #1131 req#4)."
    )

# 5. `curl`/`wget` POSTing directly to the GitHub REST pulls endpoint or
#    the GraphQL endpoint with a createPullRequest-shaped body.
if re.search(r"\b(curl|wget)\b", lowered):
    hits_rest_pulls = bool(re.search(r"api\.github\.com/repos/[^/\s]+/[^/\s]+/pulls", lowered))
    hits_graphql_pr = "api.github.com/graphql" in lowered and "createpullrequest" in lowered
    if hits_rest_pulls or hits_graphql_pr:
        deny(
            "a direct curl/wget call against the GitHub pulls REST endpoint "
            "or a createPullRequest GraphQL mutation is denied — the "
            "upstream defect channel files issues only, never PRs "
            "(issue #1131 req#4)."
        )

sys.exit(0)
PY

UDSG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
