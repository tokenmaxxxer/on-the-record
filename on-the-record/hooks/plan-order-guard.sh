#!/usr/bin/env bash
# PreToolUse (Bash): deny a `spawn`/`gh pr merge` invocation that would run
# a step ahead of its issue's declared Execution Plan order — issue #659
# Axis 2. The issue body's `## 실행 계획` block (parsed by
# `gates/flows.py:_plan_from_body`) already expresses parallel-vs-sequential
# via `‖`; this hook is what mechanically consumes it instead of leaving the
# order in the orchestrator's head.
#
# Scope: matches `spawn.py <role> ... --issue <n>` (spawn.py's real CLI has
# no `--step` flag — the plan's step numbers map to roles via the issue's
# `## 실행 계획`, not to a spawn.py argument, so this hook resolves role ->
# step itself). When matched, this hook resolves the issue's plan via `gh
# issue view --json body`, maps the spawned role to its declared step
# number, computes `gates/flows.py:plan_order_blocked()`, and denies if
# that step is blocked by an undone earlier step. A command that isn't a
# role-naming spawn call, or whose role the plan doesn't mention, is not
# this hook's concern — it exits open, matching impact-guard.sh's
# fail-open-on-ambiguity posture. `gh pr merge` is intentionally not
# matched: a merge carries no role/step signal in the command text to
# correlate against the plan (unlike `spawn.py`'s positional role arg), so
# there is nothing safe to gate there — Axis 2 enforcement is at the
# spawn boundary, before a premature step's session ever starts.
#
# Deployment target: same checkout-resolution as impact-guard.sh
# (zero-install, git-clone fallback), paths anchored to the TARGET repo.
#
# Kill switch: ORCHESTRATE_OFF=1 (same convention as the other guards).
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
  mkdir -p "$(dirname "$own")" 2>/dev/null
  git clone -q https://github.com/tokenmaxxxer/on-the-record.git "$own" 2>/dev/null
  if [ -f "$own/spawn.py" ]; then printf '%s' "$own"; return 0; fi
  return 1
}
CHECKOUT="$(_checkout_resolve || true)"
[ -n "$CHECKOUT" ] || exit 0

TARGET_REPO="$(pwd -P)"

IFS='' read -r -d '' GUARD <<'PY' || true
import datetime, json, os, re, subprocess, sys
from pathlib import Path

def deny(msg):
    sys.stderr.write("plan-order-guard: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("POG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str):
    sys.exit(0)

# `spawn.py <role> "<task>" --issue <n>` is the real CLI shape (no `--step`
# flag exists — the plan's step numbers map to roles, not to a spawn.py
# argument). Pull the role from the token right after `spawn.py` and the
# issue number from `--issue`.
m_spawn = re.search(r"\bspawn\.py\s+(\S+)", cmd)
m_issue = re.search(r"--issue[= ]\s*(\d+)", cmd) or re.search(r"\bissue[-\s]?(\d+)\b", cmd, re.I)
if not m_spawn or not m_issue:
    sys.exit(0)  # not a role-naming spawn call, or no issue — not this hook's concern
role = m_spawn.group(1).strip("'\"")
if role in ("watch", "kill", "consult", "reconcile", "approve-scope", "update",
            "init", "drive"):
    sys.exit(0)  # spawn.py subcommand, not a role name
issue_n = m_issue.group(1)

checkout = os.environ.get("POG_CHECKOUT")
target = os.environ.get("POG_TARGET")
sys.path.insert(0, os.path.join(checkout, "gates"))
try:
    import flows
except ImportError:
    sys.exit(0)

p = subprocess.run(["gh", "issue", "view", issue_n, "--json", "body"],
                    cwd=target, capture_output=True, text=True)
if p.returncode != 0:
    sys.exit(0)  # gh lookup failed — fail-open, same posture as impact-guard's
try:
    body = json.loads(p.stdout).get("body") or ""
except ValueError:
    sys.exit(0)

plan = flows._plan_from_body(body)
if not plan:
    sys.exit(0)

step_n = next((p["step"] for p in plan if role in p["roles"]), None)
if step_n is None:
    sys.exit(0)  # role not named in this issue's plan — not this hook's concern

blocked = {b["step"]: b for b in flows.plan_order_blocked(plan)}
hit = blocked.get(step_n)
if hit is None:
    sys.exit(0)

root = Path(target)
out_dir = root / "docs" / f"issue-{issue_n}" / "decisions"
out_dir.mkdir(parents=True, exist_ok=True)
ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
lines = [
    f"# spawn/merge refusal — issue #{issue_n} step {step_n} — {ts}",
    "",
    f"Refused: step {step_n} was requested before step "
    f"{hit['prerequisite_step']} (declared prerequisite, per the issue's "
    "`## 실행 계획`) was marked done.",
    "",
    "Basis: `gates/flows.py:plan_order_blocked()` over "
    "`gates/flows.py:_plan_from_body()`'s parse of the issue body "
    "(issue #659 Axis 2).",
]
(out_dir / f"spawn-refusal-{ts}.md").write_text("\n".join(lines) + "\n")

deny(f"issue #{issue_n} step {step_n} refused: prerequisite step "
     f"{hit['prerequisite_step']} is not done yet per the issue's "
     f"`## 실행 계획`. Refusal basis: "
     f"docs/issue-{issue_n}/decisions/spawn-refusal-{ts}.md")
PY

POG_PAYLOAD="$payload" POG_CHECKOUT="$CHECKOUT" POG_TARGET="$TARGET_REPO" python3 -c "$GUARD"
rc=$?
exit "$rc"
