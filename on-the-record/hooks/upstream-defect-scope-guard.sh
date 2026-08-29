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
# flow, never a spawned session's own delivery PR against origin. Before
# #1171, this fired on every Bash call regardless of target or session —
# which also denied issue-1163's own delivery-PR creation against origin
# (docs/issue-1163/reports/implementation.md, 2026-08-13), because this
# repo's own origin (tokenmaxxxer/on-the-record) is also the channel's
# example upstream target, so a target-repo check alone cannot tell a
# same-repo delivery PR from a same-repo channel PR.
#
# In-scope-for-denial iff EITHER:
#   (a) the acting role is the channel's own role
#       (CLAUDE_SKILL == "upstream-defect-report", read via the
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
# Cwd resolution (issue #2669): "this session's own git origin repo" in
# (b) used to be resolved with `git -C <payload cwd> remote get-url
# origin` unconditionally, where `<payload cwd>` is the PreToolUse
# event's own `cwd` field — the harness's fixed per-session workspace
# directory, which does NOT track a `cd` the command itself performs
# (Bash's cwd persists across separate tool calls, but the hook payload's
# `cwd` field does not follow it). A session legitimately delivering to a
# second repo it has a real local checkout of — `cd <repo-B-checkout> &&
# gh pr create --repo owner/repo-B` — always resolved ORIGIN_REPO from
# the first (harness) repo, never repo B, so `target != origin` and the
# call was denied regardless of the `cd`. Fixed by preferring a leading
# `cd <dir> &&`/`cd <dir>;` in the command text (resolved against the
# payload cwd if relative) as the directory `git remote get-url origin`
# is actually run in, falling back to the payload cwd when no leading
# `cd` is present — this is "the checkout the command is actually about
# to run in," not a new claim the session makes about itself: the
# directory must be a real local git checkout whose CONFIGURED remote is
# inspected on disk, not a string taken from the command line.
#
# Known residual gap, deliberately not chased further (issue #2637's
# precedent: docs/issue-2637/reports/silent-failure-audit+architecture-
# interface-contract-shape-149dabd2.md found that no path/git-derived
# resolution a hook computes from session-reported strings before the
# write can be made fully unsteerable, and pinned the gap as
# `expectedFailure` tests rather than iterating a fourth resolution
# scheme). The same class applies here: a session can `git init` a
# throwaway directory, `git remote add origin <target-url>`, and `cd`
# into it before the `gh pr create` call, which makes ORIGIN_REPO report
# the target repo with zero real relationship to it. This fix does not
# and cannot close that — it is pinned as a live `expectedFailure` test
# in test/test_upstream_defect_scope_guard_cross_repo_cwd.py rather than
# silently left uncovered. What it does close is the reported case: a
# session with a genuine local checkout of a second repo it legitimately
# works in.
#
# Fail-open guard (PR #2703 review): the pre-#2669 code already failed
# open (allowed) when origin was unresolvable at all (no git repo, no
# origin remote) — see "Origin-resolution failure" above. Before this
# fix, that fallback only fired where the HARNESS put the session, which
# the session could not choose. Once the operative directory could come
# from a `cd` in the command text, an unresolvable directory became
# something the session picks on purpose: `cd /tmp && gh pr create
# --repo <anything>` made ORIGIN_REPO resolve to None for every target,
# which fell open for every target. `operative_cwd`/`origin_repo` now
# report whether the directory that failed to resolve was session-chosen
# (via `cd`) or the harness's own payload cwd; `in_scope` fails open only
# in the latter case and treats the former as in-scope, so a `cd` to a
# non-checkout no longer buys a session an unconditional PR-creation
# allow.
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

CHANNEL_SKILL = "upstream-defect-report"

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

# --- channel identity: mounted skills, not CLAUDE_SKILL (issue #2576) -------
# CLAUDE_SKILL now carries whatever (possibly composed, "+"-joined) slug a
# --skills spawn produced, so an exact-string compare against the single
# literal "upstream-defect-report" only ever matched a spawn mounting that
# skill alone — any multi-skill composition silently fell out of scope.
# The session-role-bind.sh snapshot this used to prefer never actually
# carries a role value either (issue #2538 stage 6B narrowed it to a bare
# {"spawned": true} flag) — that fallback path was already dead. Read
# $MUSTER_SKILLS (pipeline.py:723) directly instead: true membership,
# unaffected by what else is mounted alongside it.
mounted = [s for s in os.environ.get("MUSTER_SKILLS", "").split(",") if s]
channel_role_active = CHANNEL_SKILL in mounted

# --- the directory the command actually runs in (issue #2669) --------------
# A leading `cd <dir> &&`/`cd <dir>;` in the command text names the real
# checkout the guarded call executes in more accurately than the payload's
# `cwd` field does (that field is the harness's fixed per-session
# workspace dir and does not follow a `cd` the command itself performs).
# Falls back to the payload cwd when no leading `cd` is present. Also
# reports whether the returned directory was named by the command text
# itself (session-chosen) rather than the harness's own payload cwd — the
# unresolvable-origin fallback below must not fail open on a session-chosen
# directory the way it does on a harness-chosen one (issue #2669 PR #2703
# review: `cd /tmp && gh pr create --repo <anything>` made the session able
# to pick whether origin resolves at all, since `/tmp` is never a git repo).
def operative_cwd(payload_cwd):
    m = re.match(r'^\s*cd\s+("[^"]+"|\'[^\']+\'|\S+)\s*(?:&&|;)', cmd)
    if not m:
        return payload_cwd, False
    target = m.group(1).strip("'\"")
    if not target:
        return payload_cwd, False
    if not target.startswith("/") and payload_cwd:
        target = os.path.join(payload_cwd, target)
    return target, True

# --- this session's own git origin repo (owner/repo, lowercased) -----------
def origin_repo():
    payload_cwd = e.get("cwd") if isinstance(e.get("cwd"), str) and e.get("cwd") else None
    cwd, cwd_session_chosen = operative_cwd(payload_cwd)
    cwd = cwd or payload_cwd
    try:
        r = subprocess.run(
            ["git", "-C", cwd or ".", "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None, cwd_session_chosen
    if r.returncode != 0:
        return None, cwd_session_chosen
    url = r.stdout.strip()
    m = re.search(r"[:/]([^/:\s]+/[^/:\s]+?)(\.git)?$", url)
    return (m.group(1).lower() if m else None), cwd_session_chosen

ORIGIN_REPO, ORIGIN_CWD_SESSION_CHOSEN = origin_repo()

def in_scope(target_repo):
    """PR-creation call is in-scope for denial iff the channel's own role
    is active, or a target repo was extracted and it isn't this session's
    origin repo. `target_repo=None` (no extractable target) relies on the
    role signal alone.

    Origin-unresolvable fails open ONLY when the directory that failed to
    resolve is the harness's own payload cwd — the pre-#2669 posture,
    unchanged here. That is a narrower exposure than a `cd`-target
    failure: it requires the session to have already mutated its own
    harness workspace's git state (e.g. `git remote remove origin`) in a
    prior call, which is the same session-mutable-local-git-state class
    as the already-pinned spoofed-origin gap below, not something this
    fix introduces or is scoped to close. When the directory came instead
    from a `cd` in the command text, the session picks a fresh,
    arbitrary directory on the spot with no such precondition (e.g. `cd
    /tmp`, never a git repo), so failing open there would let the
    session pick its way out of the guard entirely on any single call;
    treat
    an unresolvable session-chosen directory as in-scope instead."""
    if channel_role_active:
        return True
    if target_repo is not None:
        if ORIGIN_REPO is not None:
            return target_repo.lower() != ORIGIN_REPO
        if ORIGIN_CWD_SESSION_CHOSEN:
            return True
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
