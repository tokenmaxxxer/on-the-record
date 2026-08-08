#!/usr/bin/env bash
# PreToolUse (Write|Edit|MultiEdit): deny-only, session-side mirror of
# gates/accumulation.py's check_accumulation_claim (issue #424, ported
# per issue #512 — gates/ci.py's runner disappeared with GitHub Actions
# retirement, #460).
#
# Zero-install: no `import gates`, root discovered by walking up from the
# hook payload's `cwd` for a `.git` directory, same pattern as
# record-claim-guard.sh and call-shape-guard.sh.
#
# On a `.py` write, detects the same two evidence-backed accumulation
# shapes accumulation.py checks (shape 1: >= 3 inline subprocess/gh call
# sites in one file; shape 5: roles/*.json-style repeated one-line-edit
# files) against the write's resulting content plus the rest of the
# target repo's tracked tree. If a touched shape is detected, requires a
# `## Accumulation` heading with a non-empty body (field-presence
# strengthening, issue #512 requirement 3 — content is never
# interpreted, contract §14) in the local working-tree proposal file for
# the current issue. If no proposal file exists yet, this hook does not
# block — the proposal may still be mid-authoring.
#
# Fails closed (trap remaps non-0/2 exit to 2). Kill switch: ORCHESTRATE_OFF=1.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 2

IFS='' read -r -d '' GUARD <<'PY' || true
import ast, glob, json, os, posixpath, re, subprocess, sys

def deny(msg):
    sys.stderr.write("accumulation-claim-guard: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("ACG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict):
    sys.exit(0)
if (e.get("tool_name") or "") not in ("Write", "Edit", "MultiEdit"):
    sys.exit(0)
ti = e.get("tool_input") or {}
if not isinstance(ti, dict):
    sys.exit(0)
p = ti.get("file_path")
if not isinstance(p, str) or not p:
    sys.exit(0)

n = posixpath.normpath(p.replace("\\", "/"))
cwd = e.get("cwd") or os.getcwd()
d = n if posixpath.isabs(n) else posixpath.normpath(posixpath.join(cwd, n))

root = None
probe = posixpath.dirname(d)
while probe and probe != "/":
    if os.path.isdir(posixpath.join(probe, ".git")):
        root = probe
        break
    probe = posixpath.dirname(probe)
if root is None:
    sys.exit(0)

rel = os.path.relpath(d, root).replace(os.sep, "/")

_SHAPE_1_THRESHOLD = 3
_ACCUMULATION_HEADING = re.compile(
    r"^##\s*Accumulation\s*$(.*?)(?=^##\s|\Z)", re.M | re.I | re.S)

def _has_filled_accumulation(body):
    m = _ACCUMULATION_HEADING.search(body or "")
    if not m:
        return False
    return any(line.strip() for line in m.group(1).splitlines())

def _is_subprocess_call(node):
    if not isinstance(node, ast.Call):
        return False
    fn = node.func
    return (
        (isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name)
         and fn.value.id == "subprocess"
         and fn.attr in ("run", "check_output", "check_call", "Popen"))
        or (isinstance(fn, ast.Name) and fn.id in ("run", "check_output",
                                                     "check_call", "Popen")))

def _inline_subprocess_call_count(text):
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 0
    return sum(1 for node in ast.walk(tree) if _is_subprocess_call(node))

def _content_over_threshold(text):
    return _inline_subprocess_call_count(text) >= _SHAPE_1_THRESHOLD

def _path_touches_shape_1(check_rel, own_new_content=None):
    """own_new_content, if given, is used for check_rel instead of the
    on-disk file (the write being evaluated hasn't landed on disk yet)."""
    if own_new_content is not None and _content_over_threshold(own_new_content):
        return True
    fpath = os.path.join(root, check_rel)
    if own_new_content is not None and check_rel == rel:
        return False  # already checked above; no on-disk fallback needed
    try:
        text = open(fpath, encoding="utf-8", errors="replace").read()
    except OSError:
        return False
    return _content_over_threshold(text)

def _touches_shape_5(check_rel):
    return bool(re.match(r"^roles/[^/]+\.json$", check_rel))

def _proposal_paths_for_issue(issue_no):
    paths = []
    if issue_no:
        paths.extend(sorted(glob.glob(os.path.join(
            root, "docs", f"issue-{issue_no}", "proposals", "*.md"))))
    paths.extend(sorted(glob.glob(os.path.join(root, "docs", "proposals", "*.md"))))
    return paths

_DENY_MSG = (
    "변경이 축적-비용 모양(공유 헬퍼 없는 인라인 subprocess/gh 호출 "
    "누적, 또는 roles/*.json 류 반복 파일에 대한 동일 한 줄 수정)을 "
    "건드리지만, proposal 본문에 내용이 채워진 '## Accumulation' "
    "필드가 없다 (issue #424/#512) — 이런 변경이 N번 더 오면 이 "
    "파일/목록이 어떻게 되는지 명시해야 한다.")

_PROPOSAL_RE = re.compile(r"^docs/issue-\d+/proposals/[^/]+\.md$")

if _PROPOSAL_RE.match(rel):
    # issue #547: authoring-time branch — the write IS the proposal being
    # authored, so its own resulting body is checked directly (no lookup
    # of a separately-committed proposal file, unlike the .py branch
    # below).
    tool_name = e.get("tool_name")
    if tool_name == "Write":
        nc = ti.get("content")
        new_body = nc if isinstance(nc, str) else ""
    else:
        # Edit/MultiEdit: a fragment-only scan misses a `files:` list
        # edited incrementally (an appended list item that doesn't repeat
        # the `files:` key) — reconstruct the full resulting file by
        # applying the edit(s) to on-disk content, per the design note in
        # docs/issue-547/proposals/2026-08-09-accumulation-claim-authoring-time.md.
        try:
            new_body = open(d, encoding="utf-8", errors="replace").read()
        except OSError:
            new_body = ""
        if tool_name == "Edit":
            os_, ns_ = ti.get("old_string"), ti.get("new_string")
            if isinstance(os_, str) and isinstance(ns_, str):
                new_body = new_body.replace(os_, ns_, 1)
        elif tool_name == "MultiEdit":
            edits = ti.get("edits")
            if isinstance(edits, list):
                for ed in edits:
                    if not isinstance(ed, dict):
                        continue
                    os_, ns_ = ed.get("old_string"), ed.get("new_string")
                    if isinstance(os_, str) and isinstance(ns_, str):
                        new_body = new_body.replace(os_, ns_, 1)

    fm = re.search(r"^files:\s*$(.*?)(?=^\S|\Z)", new_body, re.M | re.S)
    listed = []
    if fm:
        for line in fm.group(1).splitlines():
            lm = re.match(r"^\s*-\s*(\S.*?)\s*$", line)
            if lm:
                listed.append(lm.group(1))

    hit = any(_touches_shape_5(p) or _path_touches_shape_1(p) for p in listed)
    if hit and not _has_filled_accumulation(new_body):
        deny(_DENY_MSG)
    sys.exit(0)

if not rel.endswith(".py"):
    sys.exit(0)

content_parts = []
nc = ti.get("content")
if isinstance(nc, str):
    content_parts.append(nc)
ns = ti.get("new_string")
if isinstance(ns, str):
    content_parts.append(ns)
edits = ti.get("edits")
if isinstance(edits, list):
    for ed in edits:
        if isinstance(ed, dict) and isinstance(ed.get("new_string"), str):
            content_parts.append(ed["new_string"])
new_content = "\n".join(content_parts)
if not new_content.strip():
    sys.exit(0)

def _touches_shape_1_py_write():
    if _content_over_threshold(new_content):
        return True
    pr = subprocess.run(["git", "-C", root, "ls-files", "*.py"],
                         capture_output=True, text=True)
    files = pr.stdout.splitlines() if pr.returncode == 0 else []
    for f_rel in files:
        if f_rel == rel:
            continue
        if _path_touches_shape_1(f_rel):
            return True
    return False

if not (_touches_shape_1_py_write() or _touches_shape_5(rel)):
    sys.exit(0)

branch = None
br = subprocess.run(["git", "-C", root, "branch", "--show-current"],
                    capture_output=True, text=True)
if br.returncode == 0:
    branch = br.stdout.strip()
issue_no = None
m = re.match(r"^issue-(\d+)/", branch or "")
if m:
    issue_no = m.group(1)

proposal_paths = _proposal_paths_for_issue(issue_no)

if not proposal_paths:
    # No proposal on disk yet — still being authored; this hook only
    # catches "wrote the proposal, then the code, but the field is
    # missing," it never forces proposal-before-code ordering.
    sys.exit(0)

filled = False
for pp in proposal_paths:
    try:
        text = open(pp, encoding="utf-8", errors="replace").read()
    except OSError:
        continue
    if _has_filled_accumulation(text):
        filled = True
        break

if not filled:
    deny(_DENY_MSG)
sys.exit(0)
PY

ACG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
trap - EXIT
exit "$rc"
