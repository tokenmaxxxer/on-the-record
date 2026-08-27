#!/usr/bin/env bash
# PreToolUse (Bash): deny-before-effect gate on `gh pr create --base` / REST
# pulls-create issued from a role workspace, when --base is not the repo's
# default branch (issue #1461).
#
# Root cause (issue #1461 investigation): before this gate, nothing computed
# or validated `--base` at authoring time — a role session picked the value
# itself when composing the `gh pr create` command line (unconstrained model
# choice, not a stale-state read: no script in spawn.py/gates/ ever wrote or
# suggested a `--base` value for a role session to consume). The 2026-08-14
# incident (~/.tokenmaxxxer/work/on-the-record-issue-1202-execution-
# observation.watcher.log, ~14:2x KST) shows issue-1202/execution-observation
# issuing `gh pr create --base issue-247/conformance-review --head
# issue-1202/execution-observation` — a different issue's role branch,
# unrelated to issue-1202's own subject. The likeliest mechanism is context
# bleed: the session's own conversation had issue-247/conformance-review's
# branch name in view (e.g. from a prior board read or log excerpt) and the
# model reused it as `--base` instead of the repo default. Same zero-install
# inline-Python-in-heredoc shape as pr-preflight.sh/contract-guard.sh, so
# this hook needs no gates/ checkout in the consumer repo, only `gh`.
#
# Fail-closed policy (requirement 3, consistent with the PreToolUse
# fail-closed default other gates in this plugin use for authoring-time
# denial): every other lookup failure (no git, no `gh`, non-matching
# command, non-issue branch, no --base found) is a scope miss and passes
# through — this hook only ever *applies* to `gh pr create --base <x>` /
# `gh api .../pulls` calls with a role-shaped current branch. But once it
# applies, an unresolvable default branch (the one fact this gate exists to
# check) denies rather than passing through, since a silent pass-through
# there is exactly the failure mode issue #1461 reports.
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
# issue #2016 phase 2: cheap bash-level short-circuit before the python3 spawn below --
# skip the interpreter launch entirely when the raw payload plainly can't match this
# gate's own command-shape condition (checked again, authoritatively, in python).
grep -qE "gh[[:space:]]+pr[[:space:]]+create" <<<"$payload" || { grep -qF "gh" <<<"$payload" && grep -qF "/pulls" <<<"$payload"; } || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
command -v gh >/dev/null 2>&1 || exit 0

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, subprocess, sys

def deny(msg, hint):
    sys.stderr.write("pr-base-guard: %s\n" % msg)
    sys.stderr.write("pr-base-guard: expected: %s\n" % hint)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("CG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str):
    sys.exit(0)

is_pr_create = bool(re.search(r"\bgh\s+pr\s+create\b", cmd))
is_rest_create = bool(
    re.search(r"\bgh\s+api\b", cmd) and re.search(r"/pulls(?:[\"'\s]|$)", cmd)
)
if not (is_pr_create or is_rest_create):
    sys.exit(0)

# --- extract --base value from the command line ----------------------------
def _extract_flag(cmd, flag):
    m = re.search(
        flag + r"(?:=|\s+)(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|\S+)", cmd
    )
    if not m:
        return None
    raw = m.group(1)
    if len(raw) >= 2 and raw[0] in "\"'" and raw[-1] == raw[0]:
        raw = raw[1:-1]
    return raw

base = _extract_flag(cmd, r"--base")
if base is None and is_rest_create:
    # REST shape: -f base=<value> / -F base=<value> / --raw-field base=<value>
    m = re.search(
        r"(?:-f|-F|--raw-field|--field)\s+base=(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|\S+)",
        cmd,
    )
    if m:
        raw = m.group(1)
        if len(raw) >= 2 and raw[0] in "\"'" and raw[-1] == raw[0]:
            raw = raw[1:-1]
        base = raw

if base is None:
    sys.exit(0)  # no --base on the command — gh defaults to the repo default

# --- subject issue number from the current branch (role workspace scope) ---
try:
    r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                        capture_output=True, text=True, timeout=20)
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
if r.returncode != 0:
    sys.exit(0)
branch = r.stdout.strip()
bm = re.match(r"^issue-(\d+)/", branch)
if not bm:
    sys.exit(0)  # not a per-issue workspace branch — out of this gate's scope
issue = int(bm.group(1))

def gh_json(*args):
    try:
        r = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None

def gh_text(*args):
    # `-q <jq filter>` emits raw (unquoted) text, not JSON — a distinct
    # shape from gh_json's `--json` full-payload calls above.
    try:
        r = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return r.stdout.strip()

# --- resolve the repo default branch — fail CLOSED if this fails -----------
default_branch = gh_text("repo", "view", "--json", "defaultBranchRef",
                          "-q", ".defaultBranchRef.name")
if not default_branch:
    deny(
        f"repo 기본 브랜치를 확인할 수 없다 — '{base}'를(을) --base로 쓰는 "
        f"PR 생성을 안전하게 검증할 수 없어 거부한다(fail-closed).",
        "`gh repo view --json defaultBranchRef`가 성공해야 한다",
    )

if base == default_branch:
    sys.exit(0)

# --- allow only when the issue body explicitly names this alternate base ---
issue_body = gh_text("issue", "view", str(issue), "--json", "body", "-q", ".body")
if isinstance(issue_body, str) and issue_body:
    alt_re = re.compile(
        r"(?i)\bbase\b[^\n]{0,40}?`?" + re.escape(base) + r"`?"
    )
    if alt_re.search(issue_body):
        sys.exit(0)

deny(
    f"'{base}'는(은) repo 기본 브랜치('{default_branch}')가 아니다 — "
    f"role 워크스페이스에서 여는 PR의 --base는 기본 브랜치여야 한다 "
    f"(이슈 본문이 명시적으로 다른 base를 지정하지 않는 한).",
    f"--base {default_branch}",
)
PY

CG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
