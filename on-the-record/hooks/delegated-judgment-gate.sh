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
# Sixth firing condition (issue #597): `gh pr merge` / `gh issue reopen <n>`
# / `gh issue close <n>` post a four-element framing snapshot (resolved
# problem / prior cost / newly possible / still broken) as an issue
# comment, synthesized only from citable record fields with a mechanized
# resolvability check (fails closed — no comment — if a citation doesn't
# resolve), per docs/issue-597/proposals/{architecture,implementation}.md.
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

# --- framing-snapshot citation resolvability (issue #597, architecture.md
# section 4) — inline port, same convention as reversibility_of below; no
# `gates`/record_lint import, matching this file's zero-install header. ---
def resolve_citation(target, value):
    if re.fullmatch(r"[0-9a-fA-F]{7,40}", value):
        return True
    if re.fullmatch(r"\d+ \(no prior record; issue body is the baseline\)", value):
        return True
    return (target / value).exists()


def gather_citable_records(target, issue):
    records = []
    reports_dir = target / "docs" / f"issue-{issue}" / "reports"
    if reports_dir.is_dir():
        records += sorted(reports_dir.glob("*.md"))
    decisions_dir = target / "docs" / f"issue-{issue}" / "decisions"
    if decisions_dir.is_dir():
        records += sorted(decisions_dir.glob("*.md"))
    return records


def _field_and_citation(text, key):
    """`key: value` frontmatter-style field, plus an optional immediately-
    following `Citation: ...` override line (the record's own path is the
    default citation otherwise)."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(rf"^{re.escape(key)}:\s*(.*)$", line.strip())
        if not m:
            continue
        value = m.group(1).strip()
        citation = None
        if i + 1 < len(lines) and lines[i + 1].strip().lower().startswith("citation:"):
            citation = lines[i + 1].strip().split(":", 1)[1].strip()
        return value, citation
    return None, None


def _first_heading_prose(text, headings):
    """First non-blank paragraph line under any of `headings` (matched by
    stripped, lower-cased heading text), plus an optional following
    `Citation: ...` override line."""
    wanted = {h.lower() for h in headings}
    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip().lstrip("#").strip().lower().rstrip(":")
        if stripped not in wanted:
            continue
        sentence = sentence_idx = None
        for j in range(i + 1, len(lines)):
            cand = lines[j].strip()
            if cand.startswith("#"):
                break
            if not cand:
                if sentence is not None:
                    break
                continue
            sentence, sentence_idx = cand, j
            break
        if sentence is None:
            continue
        citation = None
        if sentence_idx + 1 < len(lines) and lines[sentence_idx + 1].strip().lower().startswith("citation:"):
            citation = lines[sentence_idx + 1].strip().split(":", 1)[1].strip()
        return sentence, citation
    return None, None


def build_framing_snapshot(target, issue, transition, pr_ref):
    records = gather_citable_records(target, issue)
    if not records:
        baseline_cite = f"{issue} (no prior record; issue body is the baseline)"
        elements = {
            "Resolved problem": (
                "No prior records exist for this issue — this is the first "
                "tracked transition. Baseline: no established resolution to "
                "compare against yet.", baseline_cite),
            "Prior cost": (
                "No prior records exist for this issue — this is the first "
                "tracked transition. Baseline: no established cost to compare "
                "against yet.", baseline_cite),
            "Newly possible": (
                "No prior records exist for this issue — this is the first "
                "tracked transition. Baseline: nothing yet built to compare "
                "against.", baseline_cite),
            "Still broken": (
                "No prior records exist for this issue — this is the first "
                "tracked transition. Baseline: nothing yet attempted or "
                "resolved.", baseline_cite),
        }
    else:
        reports = [p for p in records if p.parent.name == "reports"]
        decisions = [p for p in records if p.parent.name == "decisions"]
        auto_decisions = sorted(p for p in decisions if p.name.startswith("auto-"))
        remediations = sorted(p for p in decisions if p.name.startswith("remediation-"))

        resolved_sentence = resolved_cite = None
        if auto_decisions:
            latest = auto_decisions[-1]
            value, cite = _field_and_citation(
                latest.read_text(encoding="utf-8", errors="ignore"), "decision")
            if value:
                resolved_sentence = f"Decision recorded: {value}"
                resolved_cite = cite or str(latest.relative_to(target))

        broken_sentence = broken_cite = None
        if remediations:
            latest = remediations[-1]
            text = latest.read_text(encoding="utf-8", errors="ignore")
            value, cite = _field_and_citation(text, "status")
            fix, _ = _field_and_citation(text, "required_fix")
            if value:
                broken_sentence = ("Open remediation status: " + value
                                    + (f" — required fix: {fix}" if fix else ""))
                broken_cite = cite or str(latest.relative_to(target))
        elif auto_decisions:
            latest = auto_decisions[-1]
            value, cite = _field_and_citation(
                latest.read_text(encoding="utf-8", errors="ignore"), "decision")
            if value == "reject":
                broken_sentence = "Latest candidate decision was rejected; no approved remediation yet."
                broken_cite = cite or str(latest.relative_to(target))

        cost_sentence = cost_cite = None
        possible_sentence = possible_cite = None
        for rep in reports:
            text = rep.read_text(encoding="utf-8", errors="ignore")
            if cost_sentence is None:
                sentence, cite = _first_heading_prose(
                    text, ["what did not work", "rationale for deviations"])
                if sentence:
                    cost_sentence, cost_cite = sentence, cite or str(rep.relative_to(target))
            if possible_sentence is None:
                sentence, cite = _first_heading_prose(
                    text, ["what was done", "what did we do", "summary of work",
                           "what will be done"])
                if sentence:
                    possible_sentence, possible_cite = sentence, cite or str(rep.relative_to(target))
            if cost_sentence and possible_sentence:
                break

        fallback_cite = str(records[0].relative_to(target))
        elements = {
            "Resolved problem": (
                resolved_sentence or "No resolved-problem field found in this "
                "issue's audit records yet.", resolved_cite or fallback_cite),
            "Prior cost": (
                cost_sentence or "No prior-cost prose found in this issue's "
                "role records yet.", cost_cite or fallback_cite),
            "Newly possible": (
                possible_sentence or "No newly-possible prose found in this "
                "issue's role records yet.", possible_cite or fallback_cite),
            "Still broken": (
                broken_sentence or "No open remediation record found for "
                "this issue.", broken_cite or fallback_cite),
        }

    for _, citation in elements.values():
        if not resolve_citation(target, citation):
            return None

    pr_part = f" / PR #{pr_ref}" if pr_ref else ""
    out = [f"## Framing snapshot — {transition} ({issue}{pr_part})", ""]
    for label in ("Resolved problem", "Prior cost", "Newly possible", "Still broken"):
        sentence, citation = elements[label]
        out.append(f"**{label}:** {sentence}")
        out.append(f"Citation: {citation}")
        out.append("")
    return "\n".join(out).rstrip("\n") + "\n"


FRAMING_TRANSITIONS = [
    (re.compile(r"\bgh\s+pr\s+merge\s+(\S+)"), "delivery-merged", "arg"),
    (re.compile(r"\bgh\s+issue\s+reopen\s+(\d+)"), "issue-reopened", "arg"),
    (re.compile(r"\bgh\s+issue\s+close\s+(\d+)"), "issue-closed", "arg"),
]

for _pattern, _transition, _ in FRAMING_TRANSITIONS:
    _m = _pattern.search(cmd)
    if not _m:
        continue
    if _transition == "delivery-merged":
        _r = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        if _r is None:
            sys.exit(0)
        _bm = re.match(r"^issue-(\d+)/([\w-]+)$", _r.stdout.strip())
        if not _bm:
            sys.exit(0)
        _f_issue = int(_bm.group(1))
        _f_pr_ref = _m.group(1)
    else:
        _f_issue = int(_m.group(1))
        _f_pr_ref = None
    _body = build_framing_snapshot(TARGET, _f_issue, _transition, _f_pr_ref)
    if _body is not None:
        _gh(["issue", "comment", str(_f_issue), "--body-file", "-"], body=_body)
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


def rfc3339():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# --- roles / write_scope / judgment_axes ------------------------------------
# Moved above the candidate-decision AND-gate exit below (issue #609): the
# open-decision triage block that follows needs ROLES/parse_axis_evaluations/
# latest_axis_evaluation regardless of whether that gate escalates, since
# triage evaluates a different, item-scoped question than the candidate
# decision does. Function bodies are unchanged from #573 — only their
# definition point moved earlier in the same heredoc.
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


# --- read a role's latest axis_evaluation record ----------------------------
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


# --- open-decision triage (issue #609) --------------------------------------
# A role that declined to settle a spec-stage ambiguity records a thin
# `open_decision_item` block in its own docs/issue-<n>/reports/<role>.md.
# Triage routes each item, mechanically, to the role(s) owning its
# candidate_axes (reusing the same judgment_axes table candidate-decision
# panel synthesis uses below), reuses that role's latest axis_evaluation
# verbatim (no new evaluation logic), and escalates on threshold-exceeded
# (the same DEPTH/LOW_IMPACT AND-gate below, unmodified) OR panel-conflict
# (mixed supports/contradicts across the owning roles for the same item) —
# an OR gate, deliberately looser than the candidate-decision AND gate,
# since an unrouted or contested open decision is exactly the case an
# operator needs to see. Runs before the candidate-decision gate's own
# early exit so an empty judgment-capture corpus (DEPTH always False)
# still produces a triage record for every item found, instead of the
# whole hook returning before triage ever executes.
_JUDGMENT_AXES = {
    "alignment", "maintenance_complexity", "external_burden",
    "attack_potential", "performance",
}
ITEM_BLOCK_RE = re.compile(r"<!--\s*open_decision_item\s*\n(.*?)-->", re.S)


def parse_open_decision_items(text):
    out = []
    for block in ITEM_BLOCK_RE.findall(text):
        entry = {}
        for line in block.splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            k, v = (x.strip() for x in line.split(":", 1))
            if k == "candidate_axes":
                entry[k] = [a.strip() for a in v.split(",") if a.strip()]
            else:
                entry[k] = v
        out.append(entry)
    return out


def changed_role_record_paths(paths, issue):
    pattern = re.compile(rf"^docs/issue-{issue}/reports/[^/]+\.md$")
    return [p for p in paths if pattern.match(p)]


TRIAGE_DECISIONS_DIR = TARGET / "docs" / f"issue-{issue}" / "decisions"

for _rec_rel in changed_role_record_paths(paths, issue):
    _rec_path = TARGET / _rec_rel
    if not _rec_path.is_file():
        continue
    try:
        _rec_text = _rec_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        continue
    for _item in parse_open_decision_items(_rec_text):
        _source_role = _item.get("source_role", "")
        _candidate_axes = [a for a in _item.get("candidate_axes", []) if a in _JUDGMENT_AXES]
        _owning_roles = sorted({
            role for role, cfg in ROLES.items()
            if set(cfg.get("judgment_axes") or []) & set(_candidate_axes)})

        _item_evaluations = []
        for _o_role in _owning_roles:
            for _o_axis in sorted(set(ROLES[_o_role].get("judgment_axes") or []) & set(_candidate_axes)):
                _o_ev = latest_axis_evaluation(_o_role, _o_axis)
                if _o_ev is not None:
                    _item_evaluations.append((_o_role, _o_axis, _o_ev))

        _verdicts = {ev.get("verdict") for (_, _, ev) in _item_evaluations}
        _threshold_exceeded = not (DEPTH and LOW_IMPACT)
        _panel_conflict = "supports" in _verdicts and "contradicts" in _verdicts
        _triage_decision = ("escalated"
                             if (_threshold_exceeded or _panel_conflict or not _owning_roles)
                             else "resolved")

        TRIAGE_DECISIONS_DIR.mkdir(parents=True, exist_ok=True)
        _tseq = len(list(TRIAGE_DECISIONS_DIR.glob("triage-*.md"))) + 1
        _tpath = TRIAGE_DECISIONS_DIR / f"triage-{_tseq}.md"
        _tpath.write_text("\n".join([
            "---",
            f"derivation_source: {_rec_rel}",
            f"impact_grade: {IMPACT_GRADE}",
            f"evaluating_roles: {[r for r, _, _ in _item_evaluations]}",
            f"decision: {_triage_decision}",
            f"timestamp: {rfc3339()}",
            "---", "",
        ]), encoding="utf-8")

        if _triage_decision == "escalated":
            _gh(["issue", "comment", str(issue), "--body",
                 f"Open-decision triage: `{_item.get('item', '?')}` (from "
                 f"{_source_role or '?'}) → escalated.\n"
                 f"Audit record: `docs/issue-{issue}/decisions/triage-{_tseq}.md`"])
        else:
            _gh(["pr", "comment", pr_ref, "--body",
                 f"Open-decision triage: `{_item.get('item', '?')}` → resolved "
                 f"by {', '.join(r for r, _, _ in _item_evaluations)}.\n"
                 f"Audit record: `docs/issue-{issue}/decisions/triage-{_tseq}.md`"])

if not (DEPTH and LOW_IMPACT):
    escalate("depth or impact axis did not clear")

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
    f"candidate_pr: {pr_ref}",
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
