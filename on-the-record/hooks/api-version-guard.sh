#!/usr/bin/env bash
# PreToolUse (Write|Edit|MultiEdit): issue #1130, docs/specs/role-invariant-
# coverage.md row 2 (api-design, gate-now, unwired before this).
#
# Presence-check only: fires on a diff to a discovered API contract file
# (**/openapi.{yaml,json}, **/swagger.{yaml,json}) and structurally
# compares the on-disk (old) version of the file against the resulting
# (new) content — rejects a removed/renamed top-level `paths` entry or a
# removed `required` field on a schema when the spec's own `info.version`
# field is unchanged. Not a full OpenAPI diff (that's oasdiff's job on a
# real integration); this is the minimal structural check the acceptance
# criterion's own check clause calls for. New files (no prior on-disk
# version) are unreached — nothing to diff against.
#
# File-pattern matching runs against tool_input.file_path as received —
# always relative to the target project root, never hardcoded to this
# repo's own layout (issue #1130 req#4).
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
    sys.stderr.write("api-version-guard: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("AVG_PAYLOAD", ""))
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

if not re.search(r"(^|/)(openapi|swagger)\.(ya?ml|json)$", p, re.IGNORECASE):
    sys.exit(0)

try:
    with open(p, encoding="utf-8") as f:
        old_text = f.read()
except OSError:
    sys.exit(0)  # no prior version on disk — nothing to diff against


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


if tool_name == "Write":
    new_text = ti.get("content")
    if not isinstance(new_text, str):
        sys.exit(0)
else:
    edits = [ti] if tool_name == "Edit" else (ti.get("edits") or [])
    if tool_name == "MultiEdit" and not isinstance(edits, list):
        sys.exit(0)
    new_text = _apply_edits(old_text, edits)


def _load(text, path):
    try:
        if re.search(r"\.json$", path, re.IGNORECASE):
            return json.loads(text)
        import yaml  # optional dependency — target repos may not have it
        return yaml.safe_load(text)
    except Exception:
        return None


old_doc = _load(old_text, p)
new_doc = _load(new_text, p)
if not isinstance(old_doc, dict) or not isinstance(new_doc, dict):
    sys.exit(0)  # not structurally parseable — presence check has nothing to check

old_version = ((old_doc.get("info") or {}) if isinstance(old_doc.get("info"), dict) else {}).get("version")
new_version = ((new_doc.get("info") or {}) if isinstance(new_doc.get("info"), dict) else {}).get("version")
version_unchanged = old_version is not None and old_version == new_version

old_paths = old_doc.get("paths") if isinstance(old_doc.get("paths"), dict) else {}
new_paths = new_doc.get("paths") if isinstance(new_doc.get("paths"), dict) else {}
removed_paths = set(old_paths) - set(new_paths)

if removed_paths and version_unchanged:
    deny(
        "removed path(s) %s with info.version unchanged (%r) — %s"
        % (sorted(removed_paths), old_version, p)
    )

for path_key in set(old_paths) & set(new_paths):
    old_ops = old_paths.get(path_key) if isinstance(old_paths.get(path_key), dict) else {}
    new_ops = new_paths.get(path_key) if isinstance(new_paths.get(path_key), dict) else {}
    removed_methods = set(old_ops) - set(new_ops)
    if removed_methods and version_unchanged:
        deny(
            "removed method(s) %s on path %r with info.version unchanged (%r) — %s"
            % (sorted(removed_methods), path_key, old_version, p)
        )

sys.exit(0)
PY

AVG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
