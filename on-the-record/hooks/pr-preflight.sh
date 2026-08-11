#!/usr/bin/env bash
# PreToolUse (Bash): deny-before-effect gate on gh pr create/edit — issue #459.
#
# Zero-install baseline (contract, not CI-supplement), same rationale as
# contract-guard.sh (gh pr merge): this script ships with the plugin and
# needs no gates/ checkout in the consumer repo, only `gh` on PATH. It ports
# gates/pr_reference.py::check_body and gates/flows.py::_plan_from_body
# inline rather than importing them, because a zero-install hook cannot
# assume gates/ is on sys.path in the consumer repo.
#
# Scope: intercepts `gh pr create` / `gh pr edit` — the acts that set a PR's
# body BEFORE the PR exists (create) or change it (edit). Unlike
# contract-guard.sh (which reads an existing PR via `gh pr view`), this hook
# extracts the body straight from the command line (--body / --body-file),
# because for `create` there is no PR yet to look up.
#
# Fail-open policy: any parse failure, missing tool, non-matching command,
# absent --body/--body-file, unreadable body-file, non-issue branch, or `gh`
# lookup failure results in exit 0 (pass through). The only path that exits
# 2 is a positive, evidence-backed determination that the body violates the
# phase-appropriate issue-reference rule (gates/pr_reference.py::check_body).
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 0
command -v gh >/dev/null 2>&1 || exit 0

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, subprocess, sys

def deny(msg, hint):
    sys.stderr.write("pr-preflight: %s\n" % msg)
    sys.stderr.write("pr-preflight: expected: %s\n" % hint)
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

if not re.search(r"\bgh\s+pr\s+(create|edit)\b", cmd):
    sys.exit(0)

# --- extract PR body from the command line itself --------------------------
body = None
m = re.search(r"--body(?:=|\s+)(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|\S+)", cmd)
if m:
    raw = m.group(1)
    if len(raw) >= 2 and raw[0] in "\"'" and raw[-1] == raw[0]:
        raw = raw[1:-1]
    body = raw
else:
    m = re.search(r"--body-file(?:=|\s+)(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|\S+)", cmd)
    if m:
        raw = m.group(1)
        if len(raw) >= 2 and raw[0] in "\"'" and raw[-1] == raw[0]:
            raw = raw[1:-1]
        try:
            with open(raw, "r", encoding="utf-8") as f:
                body = f.read()
        except OSError:
            sys.exit(0)  # unreadable body-file — nothing to check yet, fail-open

if body is None:
    sys.exit(0)  # no --body/--body-file on the command — nothing to check yet

# --- subject issue number + role from the current branch -------------------
try:
    r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                        capture_output=True, text=True, timeout=20)
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
if r.returncode != 0:
    sys.exit(0)
branch = r.stdout.strip()
bm = re.match(r"^issue-(\d+)/([\w-]+)$", branch)
if not bm:
    sys.exit(0)
issue = int(bm.group(1))
role = bm.group(2)

# --- phase determination via issue comments + approvers.md -----------------
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

comments = gh_json("issue", "view", str(issue), "--json", "comments", "-q", ".comments")
if comments is None:
    sys.exit(0)  # gh lookup failed — fail-open, not a verdict

approvers_path = os.path.join(os.getcwd(), "docs", "specs", "approvers.md")
approvers = set()
if os.path.isfile(approvers_path):
    for line in open(approvers_path, encoding="utf-8"):
        mm = re.match(r"^\s*-\s*(\S+)", line)
        if mm:
            approvers.add(mm.group(1))

needle = "APPROVE issue-%d/%s" % (issue, role)
phase2 = any(
    (c.get("body") or "").strip() == needle
    and (c.get("author", {}) or {}).get("login") in approvers
    for c in (comments or [])
)

# --- delegation-citation provenance (issue #707) ----------------------
# Same distinct-shape acceptance as approval-gate.sh: a
# "APPROVE issue-<n>/<role> VIA DELEGATION <scope>" citation from an
# approvers.md login also flips phase to phase2, but only when backed by a
# live (unexpired, unrevoked, in-scope) "DELEGATE <scope> UNTIL <date>"
# grant. Empty state (no citation, no DELEGATE comment) leaves phase2
# byte-identical to the exact-match check above.
if not phase2:
    _DELEGATE_RE = re.compile(r"^DELEGATE (\S+) UNTIL (\d{4}-\d{2}-\d{2})$")
    _REVOKE_RE = re.compile(r"^REVOKE (\S+)$")
    _CITE_RE = re.compile(r"^APPROVE issue-(\d+)/([\w-]+) VIA DELEGATION (\S+)$")

    def _delegation_valid(scope, all_comments, approver_set):
        import datetime
        grants, revokes = [], []
        for c in all_comments:
            b = (c.get("body") or "").strip()
            login = (c.get("author", {}) or {}).get("login")
            if login not in approver_set:
                continue
            created = c.get("createdAt") or ""
            gm = _DELEGATE_RE.match(b)
            if gm and gm.group(1) == scope:
                grants.append((created, gm.group(2)))
            rm = _REVOKE_RE.match(b)
            if rm and rm.group(1) == scope:
                revokes.append(created)
        if not grants:
            return False
        grants.sort()
        latest_created, expiry = grants[-1]
        if any(rc > latest_created for rc in revokes):
            return False
        try:
            exp = datetime.date.fromisoformat(expiry)
        except ValueError:
            return False
        return datetime.date.today() <= exp

    own_scope = "issue-%d/%s" % (issue, role)
    for c in (comments or []):
        b = (c.get("body") or "").strip()
        login = (c.get("author", {}) or {}).get("login")
        cm = _CITE_RE.match(b)
        if not cm or login not in approvers:
            continue
        if int(cm.group(1)) != issue or cm.group(2) != role:
            continue
        cited_scope = cm.group(3)
        if cited_scope == own_scope and _delegation_valid(cited_scope, comments, approvers):
            phase2 = True
            break

phase = "phase2" if phase2 else "phase1"

# --- plan parsing (ported from gates/flows.py::_plan_from_body) ------------
_PLAN_STEP_RE = re.compile(r"^-\s\[([ xX])\]\s+step\s+(\d+)\s+(.+)$")

def _plan_from_body(issue_body):
    lines = (issue_body or "").splitlines()
    start = None
    in_fence = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        stripped = line.strip()
        if stripped == "## 실행 계획" or stripped.startswith("## 실행 계획 "):
            start = i + 1
            break
    if start is None:
        return None
    steps = []
    in_fence = False
    for line in lines[start:]:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        stripped = line.strip()
        if stripped.startswith("##"):
            break
        mm = _PLAN_STEP_RE.match(stripped)
        if not mm:
            continue
        done = mm.group(1) in ("x", "X")
        step_n = int(mm.group(2))
        roles = [r.strip() for r in mm.group(3).split("‖")]
        steps.append({"step": step_n, "roles": roles, "done": done})
    return steps

plan = None
if phase == "phase2":
    issue_body = gh_json("issue", "view", str(issue), "--json", "body", "-q", ".body")
    if issue_body is None:
        sys.exit(0)  # gh lookup failed — fail-open
    plan = _plan_from_body(issue_body)

# --- check_body (ported from gates/pr_reference.py) -------------------------
_PLAIN_REF = re.compile(r"(?<!\w)#(\d+)")
_CLOSES_REF = re.compile(r"(?i)\b(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)")

def check_body(issue, body, phase, plan=None):
    body = body or ""
    if phase == "phase2":
        if plan:
            incomplete = [s for s in plan if not s["done"]]
            max_step = max(s["step"] for s in plan) if plan else 0
            only_last_incomplete = (
                len(incomplete) == 1 and incomplete[0]["step"] == max_step
            )
            if incomplete and not only_last_incomplete:
                mm = _CLOSES_REF.search(body)
                if mm and int(mm.group(2)) == issue:
                    return ["계획에 미완 스텝이 남아 있다 — 마지막 스텝의 "
                            "phase-2 PR에서만 Closes/Fixes/Resolves를 쓴다."]
                return []
        mm = _CLOSES_REF.search(body)
        if not mm or int(mm.group(2)) != issue:
            return [f"PR 본문에 'Closes #{issue}'(또는 Fixes/Resolves)가 없다 — "
                    f"phase-2 인도 PR은 이슈를 명시적으로 닫아야 한다."]
        return []
    refs = {int(n) for n in _PLAIN_REF.findall(body)}
    if issue not in refs:
        return [f"PR 본문에 '#{issue}' 참조가 없다 — phase-1 제안 PR도 자기 "
                f"이슈를 본문에서 가리켜야 한다(Closes/Fixes/Resolves는 금지: "
                f"phase-1 머지가 이슈를 자동으로 닫으면 안 된다)."]
    return []

bad = check_body(issue, body, phase, plan)
if bad:
    if phase == "phase2":
        hint = f"'Closes #{issue}' (or Fixes/Resolves #{issue}) in the PR body"
    else:
        hint = f"a plain '#{issue}' reference in the PR body (no Closes/Fixes/Resolves)"
    deny(bad[0], hint)

# --- phase-1 author-written closing-keyword refusal (issue #741 round 2) ---
# check_body's phase1 branch intentionally does not gate closing keywords
# itself — that responsibility belongs to gates/ci.py::_phase1_mismatch
# (tests/test_gates.py::t_pr_reference_phase1_does_not_gate_closing_
# keywords_itself pins check_body(126, "Closes #126", "phase1") == []). But
# _phase1_mismatch's only caller was gates/ci.py's main(), the GitHub
# Actions runner retired with issue #460 — so nothing live ever refused an
# author writing 'Closes #<issue>' straight into a phase-1 PR body
# themselves (PR #763 real-world recurrence). This ports that check inline,
# using .finditer() rather than a single .search() call — a lone .search()
# stops at the first closing-keyword match even when it names a different
# issue, missing a real match further in the body (the exact bypass
# gates/ci.py::_closes_ref_for_issue's own docstring documents having
# hunted and fixed once already; this hook's before-landing warrant hunt
# confirmed the same bypass would apply here if implemented as a single
# .search() call).
if phase == "phase1":
    closes_match = None
    for m in _CLOSES_REF.finditer(body):
        if int(m.group(2)) == issue:
            closes_match = m
            break
    if closes_match:
        deny(
            f"phase-1 제안 PR 본문에 closing 키워드({closes_match.group(1)})가 "
            f"있다 — phase-1 머지가 이슈 #{issue}를 자동으로 닫으면 안 된다.",
            f"a plain '#{issue}' reference only — no Closes/Fixes/Resolves for #{issue}",
        )
PY

CG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
