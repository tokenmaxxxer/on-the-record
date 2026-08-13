#!/usr/bin/env bash
# PreToolUse (Bash): per-role quality-bar merge-blocking gate — issue #1156,
# docs/issue-1156/proposals/per-role-quality-bars.md §3.
#
# Same shape as merge-allow-gate.sh (path:on-the-record/hooks/
# merge-allow-gate.sh): hooks-only, default-on, target-root-anchored
# (northpole req#7 — no CI/Actions), PreToolUse on `gh pr merge`, pure-
# function classifier in `gates/` (gates/quality_bar.py: classify). Unlike
# merge-allow-gate.sh (which only ever ADDS an "allow"), this hook emits a
# `"deny"` `hookSpecificOutput.permissionDecision` with exit code 2 when
# `gates/quality_bar.py`'s `classify` returns BAR_NOT_MET or ESCALATE for
# any bar-scoped role on the target PR — reusing the existing
# deny-wins-over-allow composition merge-allow-gate.sh's own docstring
# already documents.
#
# Bar-scoped roles: the 7 specs carrying a `quality_bar` array
# (roles/specs/{ux-engineering,interaction-design,accessibility,api-design,
# performance-engineering,secure-coding,test-authoring}.spec.json) — a role
# is bar-scoped for a PR when the PR's changed files match that spec's own
# `use_when.trigger.path_patterns`.
#
# Verdict record convention: a role's own docs/issue-<n>/reports/<role>.md
# carries a line `quality_bar_verdict: bar-met` or
# `quality_bar_verdict: bar-not-met` — the most recent such line in the
# file is the verdict this gate reads. No line at all is "no record"
# (gates/quality_bar.py treats this the same as an explicit bar-not-met).
#
# Anti-circularity (proposal §4): identity is account-resolved, never a
# bare CLAUDE_ROLE compare (a same-operator bypass the requirements-
# engineering hunt found and closed in design, not deferred — docs/
# issue-1156/reports/requirements-engineering/2026-08-13-hunt-
# per-role-quality-bars.md). `producer_account` is the PR author (`gh pr
# view --json author`); `record_author_account` is the git author of the
# most recent commit that touched the role's own record file — both are
# real accounts, never a CLAUDE_ROLE string.
#
# Bounded rejection (proposal §5): `consecutive_bar_not_met_count` is read
# from the same record file, counting immediately-preceding
# `quality_bar_verdict: bar-not-met` lines from the end of the file
# (reset by any `bar-met` line). At the reject cap (3, gates/
# quality_bar.py:REJECT_CAP) the classifier returns ESCALATE instead of
# BAR_NOT_MET — this hook still denies (escalation never auto-passes) and
# additionally names the open_decision_item path the escalation belongs
# in, per the issue body's requirement 4 and the existing
# open_decision_item/delegated-judgment-gate.sh escalation pattern
# (docs/specs/northpole.md section 5).
#
# Kill switch: ORCHESTRATE_OFF=1. Fail-open on any environment gap
# (missing python3/git/gh, unresolvable checkout, lookup failure, PR not
# an exact `gh pr merge <n>` shape) — same posture as merge-allow-gate.sh;
# this hook only ever narrows an already-attempted merge, never widens one.
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 0
command -v gh >/dev/null 2>&1 || exit 0

_checkout_resolve() {
  if [ -n "${TOKENMAXXXER_CHECKOUT:-}" ] && [ -f "${TOKENMAXXXER_CHECKOUT}/spawn.py" ]; then
    printf '%s' "${TOKENMAXXXER_CHECKOUT}"; return 0
  fi
  d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
  probe="$d"
  for _ in 1 2 3 4; do
    probe="$(dirname "$probe")"
    if [ -f "$probe/spawn.py" ]; then printf '%s' "$probe"; return 0; fi
  done
  mk="$HOME/.claude/plugins/marketplaces/tokenmaxxxer"
  if [ -f "$mk/spawn.py" ]; then printf '%s' "$mk"; return 0; fi
  own="$HOME/.claude/tokenmaxxxer/on-the-record"
  if [ -f "$own/spawn.py" ]; then printf '%s' "$own"; return 0; fi
  old="$HOME/.claude/tokenmaxxxer/muster"
  if [ -f "$old/spawn.py" ]; then printf '%s' "$old"; return 0; fi
  return 1
}
CHECKOUT="$(_checkout_resolve || true)"
[ -n "$CHECKOUT" ] || exit 0
[ -f "$CHECKOUT/gates/quality_bar.py" ] || exit 0

IFS='' read -r -d '' GUARD <<'PY' || true
import fnmatch
import json
import os
import re
import shlex
import subprocess
import sys

CHECKOUT = os.environ.get("QBG_CHECKOUT")
sys.path.insert(0, os.path.join(CHECKOUT, "gates"))
import quality_bar  # noqa: E402

BAR_ROLES = [
    "ux-engineering", "interaction-design", "accessibility", "api-design",
    "performance-engineering", "secure-coding", "test-authoring",
]

try:
    e = json.loads(os.environ.get("QBG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str) or not re.search(r"\bgh\s+pr\s+merge\b", cmd):
    sys.exit(0)
if "`" in cmd or "$(" in cmd or "\n" in cmd:
    sys.exit(0)

try:
    _lexer = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    _lexer.whitespace_split = True
    tokens = list(_lexer)
except ValueError:
    sys.exit(0)

OPERATOR_CHARS = set(_lexer.punctuation_chars) | {";"}


def _is_operator_token(tok):
    return bool(tok) and all(c in OPERATOR_CHARS for c in tok)


if len(tokens) >= 3 and tokens[0] == "gh" and tokens[1] == "pr" and tokens[2] == "merge":
    target_cwd = None
    _tail = tokens[3:]
elif (len(tokens) >= 6 and tokens[0] == "cd" and tokens[2] == "&&"
      and tokens[3] == "gh" and tokens[4] == "pr" and tokens[5] == "merge"):
    target_cwd = tokens[1]
    _tail = [tokens[1]] + tokens[6:]
else:
    sys.exit(0)

if any(_is_operator_token(t) for t in _tail):
    sys.exit(0)

rest = re.split(r"\bgh\s+pr\s+merge\b", cmd, maxsplit=1)[1]
url_m = re.search(r"github\.com/([^/\s]+/[^/\s]+)/pull/(\d+)", rest)
repo_flag_m = re.search(r"(?:-R|--repo)[= ]([^\s/]+/[^\s/]+)", rest)
if url_m:
    pr = url_m.group(2)
    target_repo_flag = url_m.group(1)
    target_cwd = None
elif repo_flag_m:
    num_m = re.search(r"(?<!\S)(\d+)(?!\S)", rest)
    if not num_m:
        sys.exit(0)
    pr = num_m.group(1)
    target_repo_flag = repo_flag_m.group(1)
    target_cwd = None
else:
    num_m = re.search(r"(?<!\S)(\d+)(?!\S)", rest)
    if not num_m:
        sys.exit(0)
    pr = num_m.group(1)
    target_repo_flag = None

if target_repo_flag and target_cwd is None:
    sys.exit(0)  # no local checkout to read records/diff from — unreached

run_cwd = target_cwd or e.get("cwd") or os.getcwd()


def _run(args, cwd=None, timeout=20):
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None


# --- PR changed files + branch (to resolve issue number) -------------------
gh_files = _run(["gh", "pr", "view", pr, "--json", "files,headRefName,author"], cwd=run_cwd, timeout=30)
if gh_files is None or gh_files.returncode != 0:
    sys.exit(0)
try:
    pr_json = json.loads(gh_files.stdout)
except ValueError:
    sys.exit(0)
pr_files = [f.get("path") for f in (pr_json.get("files") or []) if isinstance(f, dict) and f.get("path")]
head_ref = pr_json.get("headRefName") or ""
producer_account = ((pr_json.get("author") or {}).get("login")) if isinstance(pr_json.get("author"), dict) else None
if not pr_files:
    sys.exit(0)

issue_m = re.match(r"^issue-(\d+)/", head_ref)
issue = issue_m.group(1) if issue_m else None

# --- bar-scoped roles for this PR -------------------------------------------
role_patterns = {}
for role in BAR_ROLES:
    spec_path = os.path.join(CHECKOUT, "roles", "specs", role + ".spec.json")
    try:
        spec = json.load(open(spec_path, encoding="utf-8"))
    except (OSError, ValueError):
        continue
    trigger = (spec.get("use_when") or {}).get("trigger") if isinstance(spec.get("use_when"), dict) else None
    role_patterns[role] = (trigger or {}).get("path_patterns") or []

scoped_roles = quality_bar.bar_scoped_roles(pr_files, role_patterns)
if not scoped_roles or issue is None:
    sys.exit(0)  # NO_BAR_SCOPED — nothing to deny

VERDICT_RE = re.compile(r"^\s*quality_bar_verdict:\s*(bar-met|bar-not-met)\s*$", re.MULTILINE)

denials = []
for role in sorted(scoped_roles):
    record_path = os.path.join(run_cwd, "docs", "issue-%s" % issue, "reports", role + ".md")
    verdict = None
    consecutive = 0
    record_author = None
    if os.path.isfile(record_path):
        try:
            text = open(record_path, encoding="utf-8", errors="ignore").read()
        except OSError:
            text = ""
        matches = VERDICT_RE.findall(text)
        if matches:
            verdict = matches[-1]
            for v in reversed(matches):
                if v == "bar-not-met":
                    consecutive += 1
                else:
                    break
        log = _run(["git", "log", "-1", "--format=%an", "--", record_path], cwd=run_cwd)
        if log is not None and log.returncode == 0:
            record_author = log.stdout.strip() or None

    status, reason = quality_bar.classify(
        True, verdict, record_author, producer_account, consecutive,
    )
    if status in (quality_bar.BAR_NOT_MET, quality_bar.ESCALATE):
        denials.append((role, status, reason))

if not denials:
    sys.exit(0)  # every bar-scoped role is BAR_MET

lines = []
for role, status, reason in denials:
    lines.append("%s: %s (%s)" % (role, status, reason))
    if status == quality_bar.ESCALATE:
        lines.append(
            "  -> open docs/issue-%s/decisions/open_decision_item-%s-<ts>.md for operator attention"
            % (issue, role)
        )

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": (
            "quality-bar-gate: PR #%s has a bar-scoped role that has not "
            "met its quality_bar (issue #1156) — %s" % (pr, "; ".join(lines))
        ),
    }
}))
sys.exit(2)
PY

QBG_PAYLOAD="$payload" QBG_CHECKOUT="$CHECKOUT" python3 -c "$GUARD"
rc=$?
exit "$rc"
