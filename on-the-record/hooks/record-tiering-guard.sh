#!/usr/bin/env bash
# PreToolUse (Write|Edit|MultiEdit): denies a self-declared-empty
# `## What did not work` body that is padded beyond the bare marker
# (issue #760 — citation-informed section tiering,
# docs/issue-745/proposals/product-discovery.md Item 2 candidate 1).
#
# Scope is narrow by design: only
# docs/issue-<n>/reports/implementation.md (the one section
# docs/issue-745/reports/product-discovery/current-state.md measured at
# zero cross-issue citation) and only the self-declared-empty branch of
# its `## What did not work` section. If the trimmed section body
# starts with "none" (case-insensitive — the author's own signal that
# nothing failed), the body must be the bare marker (`None.` or `None`,
# optional trailing whitespace, nothing else) or this denies. A body
# that does not start with "none" is never inspected further — real
# content of any length passes untouched. This is a content-shape rule
# on the self-declared-empty branch only, never a length threshold
# applied to section content in general — see
# docs/issue-760/proposals/2026-08-11-citation-informed-section-tiering.md
# Rationale for why a blanket length cap was rejected as a candidate.
#
# Reconstructs the full resulting section for Edit/MultiEdit by reading
# the file's current on-disk content and applying the same edit(s) a
# real Edit/MultiEdit call would apply, rather than inspecting only the
# changed fragment — before-landing hunt (stance 0) found that a
# fragment-only check is bypassable by splitting the section heading
# and the padded body across two separate Edit calls (each PreToolUse
# invocation only sees its own call's fragment, and neither fragment
# alone contains both the heading and the padded body). Falls back to
# fragment-only checking only when the file can't be read (new file,
# race, permissions) — same as before this fix.
#
# Fails closed on genuine error (trap remaps non-0/2 exit to 2), same
# house style as record-claim-guard.sh. Kill switch: ORCHESTRATE_OFF=1.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 2

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, posixpath, re, sys

def deny(msg):
    sys.stderr.write("record-tiering-guard: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("RTG_PAYLOAD", ""))
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
if not re.search(r"(^|/)docs/issue-[^/]+/reports/implementation\.md$", n):
    sys.exit(0)

tool_name = e.get("tool_name") or ""


def _apply_edits(text, edit_list):
    for ed in edit_list:
        if not isinstance(ed, dict):
            continue
        old = ed.get("old_string")
        new = ed.get("new_string")
        if not isinstance(old, str) or not isinstance(new, str):
            continue
        text = text.replace(old, new) if ed.get("replace_all") else text.replace(old, new, 1)
    return text


content = None
if tool_name == "Write":
    nc = ti.get("content")
    if isinstance(nc, str):
        content = nc
else:
    try:
        with open(p, "r", encoding="utf-8") as f:
            current = f.read()
    except OSError:
        current = None
    if current is not None:
        if tool_name == "Edit":
            edit_list = [{"old_string": ti.get("old_string"), "new_string": ti.get("new_string")}]
        else:
            edit_list = ti.get("edits") if isinstance(ti.get("edits"), list) else []
        content = _apply_edits(current, edit_list)

if content is None:
    # File unreadable, or content/edits missing/malformed — fall back to
    # the changed fragment(s) only (write-time approximation, same
    # approach as record-claim-guard.sh).
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
    content = "\n".join(content_parts)
if not content.strip():
    sys.exit(0)

SECTION_RE = re.compile(r"(?m)^## What did not work\s*\n(.*?)(?=\n## |\Z)", re.S)
m = SECTION_RE.search(content)
if not m:
    sys.exit(0)

body = m.group(1).strip()
if not body:
    sys.exit(0)

if re.match(r"(?i)^none\b", body) and not re.match(r"(?i)^none\.?\s*$", body):
    deny(
        "`## What did not work` starts with \"None\" (self-declared "
        "empty) but is not the bare marker (issue #760). When nothing "
        "was undone/replaced and no expectation failed during the "
        "build, write the section body as exactly `None.` — no "
        "restated summary of what went to plan. Elaborate only when "
        "there is a real entry (something written then undone, or an "
        "expectation that did not hold)."
    )
sys.exit(0)
PY

RTG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
# Do NOT disarm the fail-closed trap before this exit (record-claim-guard.sh
# precedent, issue #517 before-landing hunt) — a crash inside the python
# guard for a reason unrelated to a genuine violation must still fail
# closed (exit 2), which only holds while the trap stays armed.
exit "$rc"
