#!/usr/bin/env bash
# PreToolUse (Bash): delegated-judgment-gate.sh — issue #573.
#
# Auto-approves or auto-rejects a candidate decision only when BOTH the
# depth axis (the decision follows from an operator judgment already
# recorded under docs/product/*.md) and the impact axis (mechanical
# reversibility grade, same tiers `gates/risk_report.py::classify_axes`
# already uses) clear, AND the multi-role panel (every role with standing
# over the changed paths that also owns an implicated judgment axis)
# reaches quorum and synthesizes to `approve`/`reject` under the fixed,
# named `panel-unanimous-support-v1` rule — never a single role's solo
# `supports`, never an orchestrator judgment call made at decision time.
# Any missing precondition escalates (no partial credit, no OR fallback);
# an empty/absent docs/product corpus means the depth axis never matches,
# so everything escalates via the same AND composition — no special-case
# branch (issue #573 architecture proposal, sections 1-9).
#
# Zero-install consumer surface (implementation proposal constraint): no
# gates-package import and no on-the-record checkout resolution — the
# four-axis reversibility grade this hook needs is ported inline below
# rather than imported from `gates/risk_report.py`, so this script runs in
# a target repo that never clones the on-the-record checkout at all.
#
# Trigger: `gh pr create` on an `issue-<n>/<role>` branch — the moment a
# candidate decision enters gate evaluation (architecture proposal section
# 12's "PR opened under judgment" event). This hook never denies the
# underlying command; it only judges alongside it and writes/posts its own
# audit trail, so it always exits 0 once the payload is well-formed Bash.
#
# Kill switch: ORCHESTRATE_OFF=1 (same convention as impact-guard.sh).
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 0

TARGET_REPO="$(pwd -P)"

IFS='' read -r -d '' GATE <<'PY' || true
import fnmatch, json, os, re, subprocess, sys, time
from pathlib import Path

TARGET = Path(os.environ["DJG_TARGET"])


def _run(args):
    try:
        r = subprocess.run(args, cwd=TARGET, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    return r if r.returncode == 0 else None


def _gh(args, body=None):
    """Best-effort `gh` call — posting failures never change the gate's
    own exit code or block the underlying command; they only mean the
    in-place comment layer (architecture proposal section 11/12) is
    unavailable this run, same fail-open posture as pr-preflight.sh's
    own gh-lookup failures."""
    try:
        subprocess.run(["gh", *args], cwd=TARGET, input=body, text=True,
                        capture_output=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        pass


try:
    e = json.loads(os.environ.get("DJG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str):
    sys.exit(0)
if not re.search(r"\bgh\s+pr\s+create\b", cmd):
    sys.exit(0)

r = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
if r is None:
    sys.exit(0)
branch = r.stdout.strip()
bm = re.match(r"^issue-(\d+)/([\w-]+)$", branch)
if not bm:
    sys.exit(0)
issue = int(bm.group(1))

prm = re.search(r"--number\s+(\d+)", cmd)
pr_ref = prm.group(1) if prm else "?"

r = _run(["git", "diff", "--name-only", "origin/main...HEAD"])
paths = [p for p in (r.stdout.splitlines() if r else []) if p.strip()]
if not paths:
    sys.exit(0)

_gh(["issue", "comment", str(issue), "--body",
     f"Judgment opened: PR #{pr_ref} — candidate decision on branch `{branch}` "
     f"({len(paths)} path(s) changed) entered delegated-judgment evaluation."])

# --- depth axis: docs/product/*.md corpus match -----------------------------
def depth_match(paths):
    corpus_dir = TARGET / "docs" / "product"
    if not corpus_dir.is_dir():
        return False
    entries = list(corpus_dir.glob("*.md"))
    if not entries:
        return False
    basenames = {Path(p).name for p in paths if Path(p).name}
    for f in entries:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if any(b in text for b in basenames):
            return True
    return False


DEPTH = depth_match(paths)

# --- impact axis: inline port of risk_report.py's reversibility tiers ------
# (issue #511's dominant-axis rule, reversibility axis only — this gate's
# own scope per the implementation proposal's Rationale section.)
AXIS_MAX = 4
CONTRACT_ROOT_FILES = {"protocol.md", "protocol.ko.md", "spawn.py"}
CONTRACT_PATHS = {"docs/specs/approvers.md"}
HOOK_DIRS = {"hooks"}
GATES_DIRS = {"gates", "roles", "agents", "on-the-record", ".claude-plugin"}


def reversibility_of(path):
    parts = Path(path).parts
    if not parts:
        return AXIS_MAX
    lower = path.lower()
    if lower in CONTRACT_ROOT_FILES or lower in CONTRACT_PATHS:
        return AXIS_MAX
    if any(seg in HOOK_DIRS for seg in parts[:-1]):
        return AXIS_MAX
    if parts[0] in GATES_DIRS:
        return AXIS_MAX - 1
    if parts[0] == "docs":
        return 1
    return 2


def reversibility_grade(paths):
    if not paths:
        return AXIS_MAX
    return max(reversibility_of(p) for p in paths)


IMPACT_GRADE = reversibility_grade(paths)
LOW_IMPACT = IMPACT_GRADE < AXIS_MAX


def escalate(reason):
    _gh(["issue", "comment", str(issue), "--body",
         f"Verdict: PR #{pr_ref} → escalate ({reason})"])
    sys.exit(0)


if not (DEPTH and LOW_IMPACT):
    escalate("depth or impact axis did not clear")

# --- roles / write_scope / judgment_axes ------------------------------------
def load_roles():
    roles = {}
    roles_dir = TARGET / "roles"
    if not roles_dir.is_dir():
        return roles
    for f in sorted(roles_dir.glob("*.json")):
        try:
            roles[f.stem] = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
    return roles


ROLES = load_roles()


def glob_matches(path, pattern):
    if fnmatch.fnmatch(path, pattern):
        return True
    prefix = pattern.split("**")[0].rstrip("/")
    return bool(prefix) and (path == prefix or path.startswith(prefix + "/"))


def role_scope(role):
    """`write_scope` globs with the `<n>` issue-number placeholder resolved
    to this decision's own issue — the raw placeholder never matches a real
    path via fnmatch."""
    return [g.replace("<n>", str(issue)) for g in (ROLES.get(role, {}).get("write_scope") or [])]


standing_roles = set()
for p in paths:
    for role in ROLES:
        if any(glob_matches(p, g) for g in role_scope(role)):
            standing_roles.add(role)

implicated_axes = set()
for role in standing_roles:
    implicated_axes.update(ROLES.get(role, {}).get("judgment_axes") or [])

eligible_roles = sorted(
    role for role, cfg in ROLES.items()
    if set(cfg.get("judgment_axes") or []) & implicated_axes)

if not eligible_roles:
    escalate("no eligible role owns an implicated judgment axis")

# --- read each eligible role's latest axis_evaluation record ---------------
BLOCK_RE = re.compile(r"<!--\s*axis_evaluation\s*\n(.*?)-->", re.S)


def parse_axis_evaluations(text):
    out = []
    for block in BLOCK_RE.findall(text):
        entry, finding = {}, {}
        for line in block.splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            k, v = (x.strip() for x in line.split(":", 1))
            if k.startswith("finding."):
                finding[k.split(".", 1)[1]] = v
            else:
                entry[k] = v
        if finding:
            entry["finding"] = finding
        out.append(entry)
    return out


def role_record_path(role):
    for g in ROLES.get(role, {}).get("write_scope") or []:
        if g.endswith(".md") and "<n>" in g:
            return TARGET / g.replace("<n>", str(issue))
    return None


def latest_axis_evaluation(role, axis):
    path = role_record_path(role)
    if path is None or not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    entries = [en for en in parse_axis_evaluations(text) if en.get("axis") == axis]
    return entries[-1] if entries else None


evaluating_roles = []
quorum = True
for role in eligible_roles:
    role_axes = sorted(set(ROLES[role].get("judgment_axes") or []) & implicated_axes)
    found = None
    for axis in role_axes:
        ev = latest_axis_evaluation(role, axis)
        if ev is not None:
            found = (role, axis, ev)
            break
    if found is None:
        quorum = False
        continue
    evaluating_roles.append(found)

if not quorum:
    escalate("full-panel quorum not reached")

verdicts = [ev.get("verdict") for (_, _, ev) in evaluating_roles]
if any(v == "contradicts" for v in verdicts):
    decision = "reject"
elif verdicts and all(v == "supports" for v in verdicts):
    decision = "approve"
else:
    decision = "escalate"

if decision == "escalate":
    escalate("panel-unanimous-support-v1 resolved neither approve nor reject")

# --- write the audit record --------------------------------------------------
def rfc3339():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


decisions_dir = TARGET / "docs" / f"issue-{issue}" / "decisions"
decisions_dir.mkdir(parents=True, exist_ok=True)
seq = len(list(decisions_dir.glob("auto-*.md"))) + 1
audit_path = decisions_dir / f"auto-{seq}.md"

lines = [
    "---",
    "derivation_source: docs/product corpus match",
    f"impact_grade: {IMPACT_GRADE}",
    f"eligible_roles: {eligible_roles}",
    "synthesis_rule_id: panel-unanimous-support-v1",
    "evaluating_roles:",
]
for role, axis, ev in evaluating_roles:
    lines.append(f"  - role: {role}")
    lines.append(f"    axis: {axis}")
    lines.append(f"    verdict: {ev.get('verdict')}")
lines += [f"decision: {decision}", f"timestamp: {rfc3339()}", "---", ""]
audit_path.write_text("\n".join(lines), encoding="utf-8")

table_rows = "\n".join(
    f"| {role} | {axis} | {ev.get('verdict')} | "
    f"{(ev.get('finding') or {}).get('required_fix', '—') if ev.get('verdict') == 'contradicts' else '—'} |"
    for role, axis, ev in evaluating_roles)
synthesis_comment = (
    f"### Delegated judgment: `auto-{seq}` — **{decision}**\n\n"
    "| Role | Axis | Verdict | Finding |\n|---|---|---|---|\n"
    f"{table_rows}\n\n"
    f"Synthesis rule: `panel-unanimous-support-v1` · quorum: "
    f"{len(evaluating_roles)}/{len(eligible_roles)}\n"
    f"Audit record: `docs/issue-{issue}/decisions/auto-{seq}.md`")
_gh(["pr", "comment", pr_ref, "--body", synthesis_comment])
_gh(["issue", "comment", str(issue), "--body",
     f"Verdict: PR #{pr_ref} → {decision}\n"
     f"Audit record: `docs/issue-{issue}/decisions/auto-{seq}.md`"])

if decision == "approve":
    sys.exit(0)

# --- decision == reject: route the finding, write the remediation record ---
finding_role_axis_ev = next(
    ((role, axis, ev) for role, axis, ev in evaluating_roles
     if ev.get("verdict") == "contradicts" and ev.get("finding")), None)
if finding_role_axis_ev is None:
    sys.exit(0)  # contradiction with no routable finding — nothing more to route

contradicting_role, _, contradicting_ev = finding_role_axis_ev
finding = contradicting_ev["finding"]
target_path = finding.get("target_path", "")
required_fix = finding.get("required_fix", "")

routed_to = None
for role in ROLES:
    if any(glob_matches(target_path, g) for g in role_scope(role)):
        routed_to = role
        break

MAX_REMEDIATION_ROUNDS = 3
finding_source = f"docs/issue-{issue}/decisions/auto-{seq}.md"
prior = sorted(decisions_dir.glob("remediation-*.md"))
# A "chain" is every prior remediation record still routing the same
# target_path — this candidate decision re-entering the gate after a
# failed remediation attempt is what increments `round` (architecture
# proposal section 8), not the fresh auto-<seq> id each re-entry writes.
chain = [p for p in prior
         if f"target_path: {target_path}" in p.read_text(encoding="utf-8", errors="ignore")]
round_n = len(chain) + 1

# section 8's second escalation condition: the SAME contradicting role
# rejects the SAME target_path with the SAME required_fix a second time —
# no new remediation content since the last round means nothing was
# actually tried, a repeat rather than a fixable gap, and it escalates
# before the round bound would otherwise be hit. A round whose
# required_fix differs from the prior one is a genuine new attempt and
# only counts against the round bound above, not this check.
repeat_contradiction = any(
    f"contradicting_role: {contradicting_role}" in (txt := p.read_text(encoding="utf-8", errors="ignore"))
    and f"target_path: {target_path}" in txt
    and f"required_fix: {required_fix}" in txt
    for p in chain)

status = ("escalated" if round_n > MAX_REMEDIATION_ROUNDS or routed_to is None
          or repeat_contradiction else "open")

rem_seq = len(prior) + 1
rem_path = decisions_dir / f"remediation-{rem_seq}.md"
rem_lines = [
    "---",
    f"finding_source: {finding_source}",
    f"routed_to: {routed_to or 'UNRESOLVED'}",
    f"target_path: {target_path}",
    f"required_fix: {required_fix}",
    f"contradicting_role: {contradicting_role}",
    f"round: {round_n}",
    f"status: {status}",
    f"timestamp: {rfc3339()}",
    "---", "",
]
rem_path.write_text("\n".join(rem_lines), encoding="utf-8")

_gh(["pr", "comment", pr_ref, "--body",
     f"### Remediation routed: round {round_n}\n\n"
     f"Finding from `{finding_source}` routed to **{routed_to or 'UNRESOLVED'}** "
     f"(owns `{target_path}` via `write_scope`).\n"
     f"Required fix: {required_fix}\n"
     f"Remediation record: `docs/issue-{issue}/decisions/remediation-{rem_seq}.md`"])
_gh(["issue", "comment", str(issue), "--body",
     f"Remediation round {round_n}: PR #{pr_ref}'s finding → {routed_to or 'UNRESOLVED'}\n"
     f"Remediation record: `docs/issue-{issue}/decisions/remediation-{rem_seq}.md`"])

if status == "escalated":
    if repeat_contradiction:
        condition = "repeat contradiction from the same role on the same path"
    elif round_n > MAX_REMEDIATION_ROUNDS:
        condition = "round exhausted"
    else:
        condition = "no role owns the finding's target_path"
    _gh(["pr", "comment", pr_ref, "--body",
         f"### Escalated to operator\n\n"
         f"`{finding_source}` chain, round {round_n} — {condition}."])
    _gh(["issue", "comment", str(issue), "--body",
         f"Escalated: PR #{pr_ref}, round {round_n} — {condition}."])

sys.exit(0)
PY

DJG_PAYLOAD="$payload" DJG_TARGET="$TARGET_REPO" python3 -c "$GATE"
exit 0
