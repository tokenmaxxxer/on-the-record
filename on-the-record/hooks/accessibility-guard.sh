#!/usr/bin/env bash
# PreToolUse (Write|Edit|MultiEdit): issue #1130, docs/specs/role-invariant-
# coverage.md row 1 (accessibility, gate-now, unwired before this).
#
# Presence-check only, mirroring design-rationale-guard.sh's pattern (not a
# semantic accessibility audit): fires on a diff to a user-visible-surface
# file (**/*.html, .jsx, .tsx, .vue, .svelte) in the target project and
# denies an added <img> element with no alt attribute, or an added
# interactive element (<button>, <a href=...>, or role="button") with no
# discoverable accessible name (no text content and no aria-label/
# aria-labelledby). File-pattern matching runs against tool_input.file_path
# as received — always relative to the target project root the hook fires
# in, never hardcoded to this repo's own layout (issue #1130 req#4).
#
# Reconstructs the resulting file content for Edit/MultiEdit by reading the
# current on-disk content and applying the edit(s), same as
# design-rationale-guard.sh, so a violation split across two Edit calls
# can't slip past a fragment-only check. Falls back to fragment-only when
# the file can't be read (new file, race, permissions).
#
# Fails closed on genuine error (trap remaps non-0/2 exit to 2). Kill
# switch: ORCHESTRATE_OFF=1.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 2

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, sys

def deny(msg):
    sys.stderr.write("accessibility-guard: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("AG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict):
    sys.exit(0)
tool_name = e.get("tool_name") or ""
if tool_name not in ("Write", "Edit", "MultiEdit"):
    sys.exit(0)
ti = e.get("tool_input") or {}
if not isinstance(ti, dict):
    sys.exit(0)
p = ti.get("file_path")
if not isinstance(p, str) or not p:
    sys.exit(0)

if not re.search(r"\.(html?|jsx|tsx|vue|svelte)$", p, re.IGNORECASE):
    sys.exit(0)


def _apply_edits(text, edit_list):
    for ed in edit_list:
        old = ed.get("old_string")
        new = ed.get("new_string", "")
        if not isinstance(old, str) or old == "":
            continue
        if ed.get("replace_all"):
            text = text.replace(old, new)
        else:
            text = text.replace(old, new, 1)
    return text


new_fragment = None
if tool_name == "Write":
    new_fragment = ti.get("content")
    if not isinstance(new_fragment, str):
        sys.exit(0)
    resulting = new_fragment
else:
    edits = [ti] if tool_name == "Edit" else (ti.get("edits") or [])
    if tool_name == "MultiEdit" and not isinstance(edits, list):
        sys.exit(0)
    new_fragment = "\n".join(
        (ed.get("new_string") or "") for ed in edits if isinstance(ed, dict)
    )
    resulting = None
    try:
        with open(p, encoding="utf-8") as f:
            current = f.read()
        resulting = _apply_edits(current, edits)
    except OSError:
        resulting = None

check_text = resulting if resulting is not None else new_fragment

img_no_alt = re.search(r"<img\b(?![^>]*\balt\s*=)[^>]*>", check_text, re.IGNORECASE)
if img_no_alt:
    deny("added <img> with no alt attribute (WCAG 2.2 1.1.1, w3.org/TR/WCAG22) — %s" % p)

for m in re.finditer(r"<(button|a)\b([^>]*)>(.*?)</\1>", check_text, re.IGNORECASE | re.DOTALL):
    tag, attrs, inner = m.group(1), m.group(2), m.group(3)
    if tag.lower() == "a" and not re.search(r"\bhref\s*=", attrs, re.IGNORECASE):
        continue
    has_text = bool(re.sub(r"<[^>]+>", "", inner).strip())
    has_label = bool(re.search(r"\baria-label(ledby)?\s*=", attrs, re.IGNORECASE))
    if not has_text and not has_label:
        deny(
            "added interactive <%s> with no discoverable accessible name "
            "(WAI-ARIA, w3.org/TR/wai-aria-1.2) — %s" % (tag, p)
        )

for m in re.finditer(r'role\s*=\s*"button"([^>]*)>(.*?)<', check_text, re.IGNORECASE | re.DOTALL):
    attrs, inner = m.group(1), m.group(2)
    has_text = bool(re.sub(r"<[^>]+>", "", inner).strip())
    has_label = bool(re.search(r"\baria-label(ledby)?\s*=", attrs, re.IGNORECASE))
    if not has_text and not has_label:
        deny(
            "added role=\"button\" element with no discoverable accessible name "
            "(WAI-ARIA, w3.org/TR/wai-aria-1.2) — %s" % p
        )

sys.exit(0)
PY

AG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
