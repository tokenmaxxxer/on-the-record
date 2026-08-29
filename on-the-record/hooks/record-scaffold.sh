#!/usr/bin/env bash
# issue #517 — on-demand record scaffolder.
#
# CLI-invoked, not a PreToolUse hook: a warrant-hunter finding on the
# phase-1 proposal noted a PreToolUse form would need registration in
# hooks.json's lifecycle-event map with no natural trigger event to hang
# it off (nothing fires "author is about to start a record"). Run it by
# hand (or have an orchestrator run it) before writing a record.
#
# usage: record-scaffold.sh <role> <issue-n> [target-repo-root]
#
# Writes docs/issue-<n>/reports/<role>.md under <target-repo-root>
# (default: cwd). Refuses to overwrite an existing record.
#
# issue #2610: this used to look `role` up in the role catalog file (a
# 44-entry role catalog, deleted) and scaffold that role's declared
# `record_fields` as placeholder frontmatter keys — a KeyError (any role
# not literally one of the 44 names, i.e. every current skill-slug
# session) refused outright. It now calls the exact same
# `directive_assembly.write_record_skeleton()` every real spawned
# session's bootstrap already uses to pre-write its own skeleton
# (`spawn.py`'s `write_record_skeleton` re-export) — one construction
# path instead of two, and no catalog lookup in either.
set -euo pipefail

skill="${1:?usage: record-scaffold.sh <role> <issue-n> [target-repo-root]}"
issue="${2:?usage: record-scaffold.sh <role> <issue-n> [target-repo-root]}"
root="${3:-$(pwd)}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# directive_assembly.py lives at the repo root, a sibling of on-the-record/
# and gates/ — two levels up from on-the-record/hooks/.
plugin_root="$(cd "$script_dir/../.." && pwd)"

python3 - "$skill" "$issue" "$root" "$plugin_root" <<'PY'
import sys
from pathlib import Path

skill, issue, root, plugin_root = sys.argv[1:5]
sys.path.insert(0, plugin_root)
import directive_assembly

target = Path(root) / "docs" / f"issue-{issue}" / "reports" / f"{skill}.md"
if target.exists():
    sys.stderr.write(f"record-scaffold: 이미 존재한다, 덮어쓰지 않는다: {target}\n")
    sys.exit(1)

p = directive_assembly.write_record_skeleton(root, int(issue), skill)
if p is None:
    sys.stderr.write(f"record-scaffold: 스켈레톤을 쓰지 못했다: {target}\n")
    sys.exit(1)
print(f"record-scaffold: wrote {p}")
PY
