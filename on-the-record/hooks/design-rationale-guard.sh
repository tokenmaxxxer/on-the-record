#!/usr/bin/env bash
# PreToolUse (Write|Edit|MultiEdit): first domain-cluster gate landed off the
# issue-960 43-role coverage matrix (docs/specs/role-invariant-coverage.md,
# row 18 interaction-design / row 43 ux-engineering) — the highest-RICE
# gate-now candidate in that matrix's prioritization section.
#
# Enforces: a change to this plugin's own user-facing command surface
# (on-the-record/commands/*.md — the slash commands an operator actually
# invokes, this repo's own product-facing UX, same scope
# docs/specs/role-invariant-coverage.md names for row 18/43) must carry a
# `design-rationale:` frontmatter field with a non-empty value, mirroring
# the `description:`/`argument-hint:` fields those files already use.
#
# Reconstructs the resulting file content for Edit/MultiEdit the same way
# record-tiering-guard.sh does (read current on-disk content, apply the
# edit(s)), rather than inspecting only the changed fragment, so a rename of
# the frontmatter block across two Edit calls can't slip past a
# fragment-only check. Falls back to fragment-only when the file can't be
# read (new file, race, permissions).
#
# Fails closed on genuine error (trap remaps non-0/2 exit to 2), same house
# style as record-claim-guard.sh / record-tiering-guard.sh. Kill switch:
# ORCHESTRATE_OFF=1.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 2

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, posixpath, re, sys

def deny(msg):
    sys.stderr.write("design-rationale-guard: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("DRG_PAYLOAD", ""))
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
if not re.search(r"(^|/)on-the-record/commands/[^/]+\.md$", n):
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

fm_m = re.match(r"(?s)^---\s*\n(.*?)\n---\s*\n", content)
frontmatter = fm_m.group(1) if fm_m else ""

field_m = re.search(r"(?m)^design-rationale:\s*(.*)$", frontmatter)
if not field_m or not field_m.group(1).strip():
    deny(
        "on-the-record/commands/*.md is this plugin's own user-facing "
        "command surface (issue #960 row 18/43) — its frontmatter must "
        "carry a non-empty `design-rationale:` field stating why the "
        "command is shaped this way, alongside `description:`/"
        "`argument-hint:`."
    )
sys.exit(0)
PY

DRG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
