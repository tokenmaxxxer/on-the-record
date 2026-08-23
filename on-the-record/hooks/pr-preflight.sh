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
# lookup failure results in exit 0 (pass through). The only paths that exit
# 2 are a positive, evidence-backed determination that the body violates the
# phase-appropriate issue-reference rule (gates/pr_reference.py::check_body),
# and — narrower carve-out, issue #2013 approval amendment — a failed issue-
# body fetch specifically for the design-artifacts existence check below,
# which fails CLOSED rather than open (a gate that opens on broken `gh`
# is bypassable by breaking `gh`).
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
# issue #2016 phase 2: cheap bash-level short-circuit before the python3 spawn below --
# skip the interpreter launch entirely when the raw payload plainly can't match this
# gate's own command-shape condition (checked again, authoritatively, in python).
grep -qE 'gh[[:space:]]+pr[[:space:]]+(create|edit)' <<<"$payload" || exit 0
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
# --body "$(cat <<'EOF' ... EOF)" is the dominant real-world shape (every
# gh pr create/edit invocation found in session logs uses it) — matched
# first via the heredoc's own delimiter line, never via quote-balance,
# because the heredoc body routinely contains literal, unescaped '"'
# characters (a quoted phrase, a code span) that a naive quote-balance
# scan cannot tell apart from the argument's real closing quote. The
# quote-balance regex below stops at the FIRST such literal '"' inside the
# body and silently truncates everything after it — including a
# downstream 'Closes #<n>' (issue #854: confirmed by feeding the hook the
# exact command text a real session ran, with a literal '"무리"' partway
# through the body and 'Closes #839' appended after it; the truncated
# capture never reached the 'Closes' text and the phase-1 refusal below
# never fired). Scoped to this one real-world idiom rather than a general
# shell parser, matching this file's existing inline-port convention.
_HEREDOC_BODY_RE = re.compile(
    r"--body(?:=|\s+)\"\$\(\s*cat\s+<<(-?)\s*(['\"]?)(\w+)\2\s*\n(.*?)\n(?(1)[ \t]*)\3[ \t]*\n?\)\"",
    re.DOTALL,
)

body = None
m = _HEREDOC_BODY_RE.search(cmd)
if m:
    body = m.group(4)
else:
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

# --- subject issue number + role: prefer the .on-the-record/role.json ------
# sidecar (issue #1814) written by spawn.py's issue_workspace() at spawn
# time; any absence/parse/shape failure falls back to the branch-regex
# parse below, byte-identical to pre-#1814 behavior.
issue = None
role = None
try:
    with open(os.path.join(os.getcwd(), ".on-the-record", "role.json"), encoding="utf-8") as f:
        sidecar = json.load(f)
    if (isinstance(sidecar, dict) and isinstance(sidecar.get("role"), str)
            and isinstance(sidecar.get("issue"), int)):
        issue = sidecar["issue"]
        role = sidecar["role"]
except (OSError, ValueError):
    pass

if issue is None:
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

def _first_line_matches(body, token):
    # issue #2021 parity fix (field discovery during #2013): approval-
    # gate.sh already line-anchors this exact match (the token must be
    # the ENTIRE first line, whitespace-stripped, so an approver can
    # attach rationale on subsequent lines without losing the exact-
    # match security posture) — this file's own phase-determination copy
    # had not been ported to the same fix, so a real APPROVE comment with
    # trailing amendment text on later lines was silently read as phase1
    # here while approval-gate.sh already recognized it as phase2.
    first_line = (body or "").split("\n", 1)[0]
    return first_line.strip() == token

phase2 = any(
    _first_line_matches(c.get("body"), needle)
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

# --- amendments-reconciled check (issue #1177) ------------------------------
# A role session that never re-reads the issue thread can open its PR
# against pre-amendment requirements when an operator/orchestrator posts a
# comment while the session is already running (4 round-trips on
# 2026-08-13: PRs #1167/#1168/#1170/#1176). Compare the newest issue
# comment's timestamp against this session's directive-load time (its last
# `session-start` event, written by spawn.py to the workspace's sibling
# `<work>.events.jsonl`); if a comment landed after spawn, refuse PR
# creation until the role's own record cites that newest comment's id in
# an amendments-reconciled line (existence check only — content judgment
# stays with review, per the requirement).
#
# Fail-open on every unknown: no events file, no session-start event, an
# unparseable timestamp — the false-positive bound (issues with no
# post-spawn comments pass untouched) needs the newest-comment check to
# actually run; anything short of solid evidence of a post-spawn amendment
# must not block.
def _last_session_start_ts(cwd):
    events_path = cwd.rstrip("/") + ".events.jsonl"
    if not os.path.isfile(events_path):
        return None
    ts = None
    try:
        with open(events_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(ev, dict) or ev.get("type") != "session-start":
                    continue
                detail = ev.get("detail") or {}
                cand = detail.get("ts") if isinstance(detail, dict) else None
                if not isinstance(cand, (int, float)):
                    cand = ev.get("ts")
                if isinstance(cand, (int, float)):
                    ts = float(cand)
    except OSError:
        return None
    return ts

def _comment_epoch(created_at):
    if not isinstance(created_at, str) or not created_at:
        return None
    try:
        import datetime
        return datetime.datetime.fromisoformat(
            created_at.replace("Z", "+00:00")
        ).timestamp()
    except ValueError:
        return None

def _comment_num_id(c):
    url = c.get("url") or ""
    mm = re.search(r"#issuecomment-(\d+)\s*$", url)
    return mm.group(1) if mm else None

# --- machine-comment cursor auto-advance (issue #1310) ---------------------
# The block above starves gh pr create on busy issues where watchdog/
# delegated-judgment/consult-trace machinery posts a comment every 30-60s:
# every role session's read-thread -> pr-create cycle loses the race
# indefinitely. Comments produced by that machinery never carry operator
# intent, so they must not count as the "newest comment" the block reacts
# to; only the newest *operator* comment newer than spawn still blocks.
_MACHINE_LOGIN_RE = re.compile(
    r"\[bot\]$|^github-actions(\[bot\])?$|^dependabot(\[bot\])?$"
)
_MACHINE_BODY_RE = re.compile(
    r"^\s*(\[(on-the-record|watch|poll-report|watchdog|watchdog-crash|"
    r"reconcile|orphaned|resume|returned-pr|health)\]|"
    r"## Framing snapshot —|- \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*\|\s*role=|"
    r"Judgment opened: |Verdict: PR |"
    r"APPROVE issue-\S+/\S+\s*$)"
)

def _is_machine_comment(c):
    login = (c.get("author", {}) or {}).get("login") or ""
    if _MACHINE_LOGIN_RE.search(login):
        return True
    body = c.get("body") or ""
    return bool(_MACHINE_BODY_RE.match(body))

spawn_ts = _last_session_start_ts(os.getcwd())
if spawn_ts is not None and comments:
    newest = None
    for c in comments:
        if _is_machine_comment(c):
            continue
        epoch = _comment_epoch(c.get("createdAt"))
        if epoch is None:
            continue
        if newest is None or epoch > newest[0]:
            newest = (epoch, c)
    if newest is not None and newest[0] > spawn_ts:
        newest_id = _comment_num_id(newest[1])
        if newest_id:
            record_path = os.path.join(os.getcwd(), "docs", f"issue-{issue}",
                                        "reports", f"{role}.md")
            record_text = ""
            if os.path.isfile(record_path):
                try:
                    with open(record_path, "r", encoding="utf-8") as f:
                        record_text = f.read()
                except OSError:
                    record_text = ""
            reconciled = any(
                "amendments-reconciled" in ln and newest_id in ln
                for ln in record_text.splitlines()
            )
            if not reconciled:
                deny(
                    f"이슈 #{issue}에 세션 시작 이후 새 코멘트(issuecomment-{newest_id})가 "
                    f"달렸다 — PR을 열기 전에 스레드를 다시 읽고 기록에 반영해야 한다.",
                    f"{record_path} 안에 'amendments-reconciled' 줄이 "
                    f"issuecomment-{newest_id}를 인용해야 한다",
                )

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
    # `-q .body` returns raw (unquoted) text for a string result — not
    # valid JSON unless the body itself happens to parse as a JSON
    # literal, so json.loads(...) on that raw text silently returned None
    # for every real-world issue body (issue #2013 field discovery: the
    # design-artifacts fetch below hit this same call shape and always
    # fail-closed against a real repo). Fetch the JSON object instead
    # (no -q) and extract the "body" key from the parsed dict.
    issue_body_obj = gh_json("issue", "view", str(issue), "--json", "body")
    issue_body = issue_body_obj.get("body") if isinstance(issue_body_obj, dict) else None
    if issue_body is None:
        sys.exit(0)  # gh lookup failed — fail-open
    plan = _plan_from_body(issue_body)

# --- design-artifacts existence check (issue #2013, artifact-gate phase 2) -
# Ported inline from gates/design_artifacts_gate.py (same zero-install
# rationale as the other ports in this file). Scoped to `gh pr create`
# time regardless of phase, since the check is about what must exist
# before a PR opens at all, not about phase-specific body content.
#
# Byte-inert when the issue body carries no `design-artifacts:`
# declaration (parse_declaration returns None) — a mechanical issue sees
# no new fetch beyond the one phase2 already made, and no new check at
# all in phase1.
#
# Fail-CLOSED on a body-fetch failure (approval amendment on #2013,
# replacing the proposal's original fail-open-on-infrastructure-trouble
# constraint, per docs/decisions/2026-07-25-gate-unknown-tool-fails-closed.md
# and this file's own pr-base-guard-style posture elsewhere): a gate that
# opens on network trouble is bypassable by breaking `gh`. This is a
# narrower fail-closed carve-out than the rest of this file's documented
# fail-open policy — scoped to exactly this one lookup, not a change to
# the file's overall posture.
_ARTIFACTS_TAG_RE = re.compile(r"^\s*[-*]?\s*design-artifacts\s*:\s*$", re.IGNORECASE)
_ARTIFACTS_BULLET_RE = re.compile(r"^\s*[-*]\s+(\S+)\s*$")
_ARTIFACTS_FENCE_RE = re.compile(r"^\s*```")


def _parse_artifacts_declaration(body):
    lines = (body or "").splitlines()
    tag_idx = None
    for i, line in enumerate(lines):
        if _ARTIFACTS_TAG_RE.match(line):
            tag_idx = i
            break
    if tag_idx is None:
        return None
    rest = lines[tag_idx + 1:]
    i = 0
    while i < len(rest) and rest[i].strip() == "":
        i += 1
    if i < len(rest) and _ARTIFACTS_FENCE_RE.match(rest[i]):
        i += 1
        paths = []
        while i < len(rest) and not _ARTIFACTS_FENCE_RE.match(rest[i]):
            stripped = rest[i].strip()
            if stripped:
                paths.append(stripped)
            i += 1
        return paths
    paths = []
    while i < len(rest):
        m = _ARTIFACTS_BULLET_RE.match(rest[i])
        if not m:
            break
        paths.append(m.group(1))
        i += 1
    return paths


if phase == "phase2":
    artifacts_issue_body = issue_body
else:
    _artifacts_body_obj = gh_json("issue", "view", str(issue), "--json", "body")
    artifacts_issue_body = (_artifacts_body_obj.get("body")
                             if isinstance(_artifacts_body_obj, dict) else None)
if artifacts_issue_body is None:
    deny(
        f"이슈 #{issue} 본문을 읽을 수 없다(`gh issue view` 실패) — "
        f"design-artifacts 게이트는 검사 불가를 통과로 취급하지 않는다(fail-closed).",
        "네트워크/gh 상태를 복구한 뒤 다시 시도한다",
    )
declared_artifacts = _parse_artifacts_declaration(artifacts_issue_body)
if declared_artifacts is not None:
    missing = [p for p in declared_artifacts if not os.path.exists(os.path.join(os.getcwd(), p))]
    if missing:
        listed = "\n".join(f"  - {p}" for p in missing)
        deny(
            f"이슈 #{issue}가 선언한 design-artifacts 중 다음 경로가 작업 트리에 없다:\n{listed}",
            "선언된 모든 design-artifacts 경로를 작업 트리에 만든 뒤 다시 시도한다",
        )
else:
    # issue #2037: a `design-artifacts:` tag with trailing content on the
    # same line (e.g. "design-artifacts: a.md, b.md") is not the contract
    # shape (a bare tag line followed by a bullet list or fence) --
    # _parse_artifacts_declaration's tag regex requires nothing after the
    # colon, so this shape falls through to None exactly like an issue
    # with no declaration at all, and the existence check above goes
    # silently byte-inert on an issue that clearly intended a declaration
    # (observed live, tm-webfolio #5). Refuse loudly instead of parsing
    # as none, quoting the required tag+bullet shape.
    for _line in (artifacts_issue_body or "").splitlines():
        if re.match(r"^\s*[-*]?\s*design-artifacts\s*:\s*\S+", _line, re.IGNORECASE):
            deny(
                f"이슈 #{issue}의 design-artifacts 선언이 잘못된 형태다: {_line.strip()!r} "
                f"— 태그 줄에 내용이 바로 붙어 있다.",
                "design-artifacts:\\n- path/one.md\\n- path/two.md  (또는 태그 다음에 "
                "```fenced``` 블록) — 태그 줄 자체에는 콜론 뒤에 아무 것도 오면 안 된다",
            )

# --- screen-verified citation check (issue #2073) --------------------------
# A design-bearing surface's phase-2 record must carry a `screen-verified:`
# line citing a live-screen screenshot plus a one-line verdict against the
# phase-1 storyboard. Parsing proves the page is not dead (ARTIFACT-SMOKE);
# it does not prove the page is the thing that was designed —
# tm-dicequest#58 shipped flat placeholder tokens against a GDD whose core
# promise was character animation, with every check green.
#
# Presence and existence ONLY, never content: this gate checks that the
# line exists and that the file it cites exists. The verdict itself stays a
# human/session judgment and is never mechanized (no pixel diff, no
# perceptual hash, no LLM verdict inside a gate).
#
# Precision-first trigger: fires only when the issue's OWN
# `design-artifacts:` declaration names a storyboard — an explicit,
# author-written signal, not a keyword score. Phase-1 PRs are exempt: the
# record the line belongs in is phase-2 output.
#
# Fail-open on everything else, including a missing record file (the
# record-shape gates own that), consistent with this file's policy.
if phase == "phase2" and declared_artifacts:
    _storyboards = [p for p in declared_artifacts
                     if re.search(r"storyboard|스토리보드", p, re.IGNORECASE)]
    if _storyboards:
        _reports = os.path.join(os.getcwd(), "docs", "issue-%s" % issue, "reports")
        _record_texts = []
        for _root, _dirs, _files in os.walk(_reports):
            for _f in _files:
                if not _f.endswith(".md"):
                    continue
                try:
                    with open(os.path.join(_root, _f), encoding="utf-8") as _fh:
                        _record_texts.append(_fh.read())
                except OSError:
                    continue
        if _record_texts:
            _cited = None
            for _text in _record_texts:
                _m = re.search(r"^\s*[-*]?\s*screen-verified\s*:\s*(\S+)(.*)$",
                                _text, re.IGNORECASE | re.MULTILINE)
                if _m:
                    _cited = (_m.group(1), (_m.group(2) or "").strip())
                    break
            if _cited is None:
                deny(
                    f"이슈 #{issue}가 스토리보드({', '.join(_storyboards)})를 "
                    f"design-artifacts 로 선언했는데, phase-2 레코드에 "
                    f"`screen-verified:` 줄이 없다 — 실화면 스크린샷 경로와 그 "
                    f"스토리보드에 비춘 한 줄 판정이 있어야 한다(이슈 #2073).",
                    "레코드에 'screen-verified: docs/issue-%s/_assets/<shot>.png "
                    "— <스토리보드 대비 한 줄 판정>' 을 추가한 뒤 다시 시도한다"
                    % issue,
                )
            elif not os.path.exists(os.path.join(os.getcwd(), _cited[0])):
                deny(
                    f"이슈 #{issue}의 `screen-verified:` 줄이 인용한 스크린샷이 "
                    f"작업 트리에 없다: {_cited[0]}",
                    "실화면 스크린샷을 docs/issue-%s/_assets/ 아래에 두고 그 "
                    "경로를 인용한 뒤 다시 시도한다" % issue,
                )
            elif not _cited[1]:
                deny(
                    f"이슈 #{issue}의 `screen-verified:` 줄이 스크린샷만 인용하고 "
                    f"판정을 담고 있지 않다 — 스토리보드"
                    f"({', '.join(_storyboards)}) 대비 한 줄 판정이 같은 줄에 "
                    f"있어야 한다.",
                    "'screen-verified: <경로> — <한 줄 판정>' 형태로 판정을 "
                    "덧붙인 뒤 다시 시도한다",
                )

# --- check_body (ported from gates/pr_reference.py) -------------------------
# issue #1165: first-paragraph and citation-placement rules ported inline
# from gates/human_comprehensibility.py (same zero-install rationale as the
# rest of this file's ports) — kept in sync by hand. gates/test_hooks_parity.py
# does NOT cover this port (it checks hooks.json registration and a
# spec-index-preflight.sh live-fire deny, not pr_reference/check_body
# content); on-the-record/hooks/test_pr_preflight.py is what pins this
# file's ported check_body/_plan_from_body/_phase1_closes_ref logic, by
# duplicating it as plain Python and asserting against it directly (same
# pattern as test_contract_guard.py) — drift from gates/pr_reference.py's
# real check_body is caught only if that duplication is kept honest by
# hand; there is no automated diff between the two.
_HEADING_RE = re.compile(r"^(#{1,6})\s+\S")
_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*]|\d+\.)\s+\S")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
_TRAILER_LINE_RE = re.compile(
    r"^\s*(part of|closes?|fixe?[sd]?|resolves?)\s+#\d+\s*$", re.IGNORECASE
)
_CITATION_RE = re.compile(
    r"(canonical:\s*\S+|derived:\s*\S+|\[[^\]]+\]\([^)]+\)|https?://\S+)"
)
_TRAILING_PUNCT_RE = re.compile(r"^[)\].,;:]*$")


def _strip_frontmatter(text):
    return _FRONTMATTER_RE.sub("", text, count=1)


def _strip_leading_blank_lines(text):
    lines = text.splitlines()
    i = 0
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    return "\n".join(lines[i:])


def _strip_leading_headings(text):
    lines = text.splitlines()
    i = 0
    while i < len(lines) and (_HEADING_RE.match(lines[i]) or lines[i].strip() == ""):
        i += 1
    return "\n".join(lines[i:])


def _first_paragraph(text):
    text = _strip_leading_blank_lines(text)
    lines = text.splitlines()
    para_lines = []
    for line in lines:
        if line.strip() == "":
            break
        para_lines.append(line)
    return "\n".join(para_lines)


def first_paragraph_is_prose(text):
    text = text or ""
    text = _strip_frontmatter(text)
    text = _strip_leading_blank_lines(text)
    text = _strip_leading_headings(text)
    para = _first_paragraph(text)
    if not para.strip():
        return False
    lines = [l for l in para.splitlines() if l.strip()]
    if not lines:
        return False
    if all(_TRAILER_LINE_RE.match(l) for l in lines):
        return False
    if _HEADING_RE.match(lines[0]):
        return False
    if _LIST_ITEM_RE.match(lines[0]):
        return False
    if _FENCE_RE.match(lines[0]):
        return False
    return True


def citation_trailing_placement(text):
    text = text or ""
    text = _strip_frontmatter(text)
    text = _strip_leading_blank_lines(text)
    text = _strip_leading_headings(text)
    para = _first_paragraph(text)
    for line in para.splitlines():
        for m in _CITATION_RE.finditer(line):
            before = line[:m.start()].strip()
            after = line[m.end():].strip()
            if not before:
                continue
            if after and not _TRAILING_PUNCT_RE.match(after):
                return False, "citation splits the point-stating sentence: '%s'" % line.strip()
    return True, ""


_PLAIN_REF = re.compile(r"(?<!\w)#(\d+)")
_CLOSES_REF = re.compile(r"(?i)\b(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)")

def check_body(issue, body, phase, plan=None):
    body = body or ""
    prose_violations = []
    if not first_paragraph_is_prose(body):
        prose_violations.append("PR body's first paragraph is not real prose (trailer-only) — "
                                 "a paragraph stating what/why/what's-next must come first.")
    citation_ok, citation_reason = citation_trailing_placement(body)
    if not citation_ok:
        prose_violations.append("PR body's lead paragraph citation placement splits a sentence "
                                 "(%s) — canonical:/link citations must be a trailing clause or "
                                 "their own line." % citation_reason)
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
                    return prose_violations + ["계획에 미완 스텝이 남아 있다 — 마지막 스텝의 "
                            "phase-2 PR에서만 Closes/Fixes/Resolves를 쓴다."]
                return prose_violations
        mm = _CLOSES_REF.search(body)
        if not mm or int(mm.group(2)) != issue:
            return prose_violations + [f"PR 본문에 'Closes #{issue}'(또는 Fixes/Resolves)가 없다 — "
                    f"phase-2 인도 PR은 이슈를 명시적으로 닫아야 한다."]
        return prose_violations
    refs = {int(n) for n in _PLAIN_REF.findall(body)}
    if issue not in refs:
        return prose_violations + [f"PR 본문에 '#{issue}' 참조가 없다 — phase-1 제안 PR도 자기 "
                f"이슈를 본문에서 가리켜야 한다(Closes/Fixes/Resolves는 금지: "
                f"phase-1 머지가 이슈를 자동으로 닫으면 안 된다)."]
    return prose_violations

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
