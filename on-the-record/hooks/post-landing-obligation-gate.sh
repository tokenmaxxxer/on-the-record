#!/usr/bin/env bash
# PostToolUse (Bash): opens a post-landing verification obligation after a
# successful `gh pr merge` — issue #1098 (northpole req#3, req#5), per
# docs/issue-1098/proposals/2026-08-12-post-landing-verify-refile-loop.md.
#
# `PostToolUse` cannot deny — this hook is pure side-effect: on a
# successfully-merged, resolvable-PR-number `gh pr merge` call, it writes a
# `.landing-obligations/<issue>-<role>-<pr>.json` record via
# `gates/landing_obligation.py` so the loop's step 1 ("every landed fix is
# verified by actually running the changed behavior") has a default,
# no-operator-prompt-required tracked state. Resolution composes with the
# existing `reexecution_gate.py`/`.reexecution/<issue>-<role>.json` verdict
# (gates/landing_obligation.py:resolve_with_reexecution_verdict) rather than
# re-implementing execution here.
#
# Command-shape detection reuses merge-allow-gate.sh's strict shlex-based
# `gh pr merge`/`cd DIR && gh pr merge` tokenization (issue #824) rather than
# a new regex — the same two recognized shapes, no other chaining/
# substitution operator tolerated.
#
# issue/role resolution: the current branch is expected to be
# `issue-<n>/<role>` (contract v3's one-branch-per-issue-x-role convention);
# a branch that does not match that shape cannot be tied to an issue, so the
# hook is a no-op (fail open — no false obligation on an unresolvable
# branch).
#
# Success detection is a heuristic over `tool_response` text (no exit-code
# field is available in the PostToolUse payload for Bash) — the same
# substring-based posture `landing_readiness.py`'s own `_pr_checks_summary`
# already uses for `gh pr checks` output. This is a known detection-latency
# gap (a merge via the GitHub web UI or a raw REST call never fires this
# hook at all) — the after-proposal hunt
# (docs/issue-1098/reports/architecture/2026-08-12-hunt-post-landing-verify-refile-loop.md)
# named the fix as a phase-2-scoped, out-of-this-write-set reconciliation
# pass over `gh pr list --json state`.
#
# Kill switch: ORCHESTRATE_OFF=1 (same convention as every other gate here).
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 0

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
  return 1
}
CHECKOUT="$(_checkout_resolve || true)"
[ -n "$CHECKOUT" ] || exit 0
[ -f "$CHECKOUT/gates/landing_obligation.py" ] || exit 0

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, shlex, subprocess, sys

try:
    e = json.loads(os.environ.get("PLOG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str):
    sys.exit(0)
if not re.search(r"\bgh\s+pr\s+merge\b", cmd):
    sys.exit(0)

# --- strict command-shape validation, ported from merge-allow-gate.sh -----
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
    _tail = tokens[3:]
    target_cwd = None
elif (len(tokens) >= 6 and tokens[0] == "cd" and tokens[2] == "&&"
      and tokens[3] == "gh" and tokens[4] == "pr" and tokens[5] == "merge"):
    _tail = [tokens[1]] + tokens[6:]
    target_cwd = tokens[1]
else:
    sys.exit(0)

if any(_is_operator_token(t) for t in _tail):
    sys.exit(0)

rest = re.split(r"\bgh\s+pr\s+merge\b", cmd, maxsplit=1)[1]
num_m = re.search(r"(?<!\S)(\d+)(?!\S)", rest)
if not num_m:
    sys.exit(0)  # implicit "current PR" — cannot resolve to a fixed number
pr = int(num_m.group(1))

# --- success detection: heuristic over tool_response text -----------------
resp = e.get("tool_response")
if isinstance(resp, str):
    text = resp
elif resp is not None:
    text = json.dumps(resp)
else:
    sys.exit(0)  # no response captured — unreached, fail open
low = text.lower()
FAILURE_MARKERS = ("failed to merge", "graphql error", "could not merge",
                    "is not mergeable", "pull request is not mergeable")
if any(m in low for m in FAILURE_MARKERS):
    sys.exit(0)  # merge did not actually succeed — no obligation to open

# --- issue/role resolution from the PR's own head branch -------------------
# `gh pr merge` is an orchestrator-only action (merge-allow-gate.sh's own
# invariant: role sessions never call it, CLAUDE_ROLE set => sys.exit(0)
# there). The orchestrator merges from the base/main checkout, never from
# an `issue-<n>/<role>` branch — so reading the CALLER's current branch
# (as an earlier version of this hook did) never matches on the one call
# shape that actually happens, and the hook silently no-ops on every real
# merge (warrant-hunter before-landing finding, issue #1098). The PR being
# merged is the one that carries the `issue-<n>/<role>` branch, via its own
# `headRefName` — read that instead of the caller's branch.
run_cwd = target_cwd or e.get("cwd") or os.getcwd()
head_r = subprocess.run(
    ["gh", "pr", "view", str(pr), "--json", "headRefName,mergeCommit"],
    cwd=run_cwd, capture_output=True, text=True, timeout=30)
if head_r.returncode != 0:
    sys.exit(0)
try:
    head_data = json.loads(head_r.stdout)
except ValueError:
    sys.exit(0)
branch = head_data.get("headRefName") if isinstance(head_data, dict) else None
if not isinstance(branch, str):
    sys.exit(0)
bm = re.match(r"^issue-(\d+)/([A-Za-z0-9_-]+)$", branch)
if not bm:
    sys.exit(0)  # not a per-issue role branch — cannot resolve, no-op
issue, role = bm.group(1), bm.group(2)

merge_commit = head_data.get("mergeCommit") if isinstance(head_data, dict) else None
sha = None
if isinstance(merge_commit, dict):
    sha = merge_commit.get("oid")
if not isinstance(sha, str) or not sha:
    sha_r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=run_cwd,
                            capture_output=True, text=True)
    sha = sha_r.stdout.strip() if sha_r.returncode == 0 else "unknown"

checkout = os.environ.get("PLOG_CHECKOUT")
script = os.path.join(checkout, "gates", "landing_obligation.py")
subprocess.run(
    [sys.executable, script, "open", "--issue", issue, "--role", role,
     "--pr", str(pr), "--sha", sha, "--repo", run_cwd],
    capture_output=True, text=True, timeout=30,
)
sys.exit(0)
PY

PLOG_PAYLOAD="$payload" PLOG_CHECKOUT="$CHECKOUT" python3 -c "$GUARD"
exit 0
