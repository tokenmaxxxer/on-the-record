#!/usr/bin/env bash
# issue #517 — on-demand record scaffolder.
#
# CLI-invoked, not a PreToolUse hook: a warrant-hunter finding on the
# phase-1 proposal noted a PreToolUse form would need registration in
# hooks.json's lifecycle-event map with no natural trigger event to hang
# it off (nothing fires "author is about to start a record"). Run it by
# hand (or have an orchestrator run it) before writing a record.
#
# usage: record-scaffold.sh <role> <issue-n> [target-repo-root] [disambiguator]
#
# Writes docs/issue-<n>/reports/<role>-<lease-disambiguator>.md under
# <target-repo-root> (default: cwd) — the same `<skill>-<lease-
# disambiguator>` naming `pipeline.checkout_issue_branch_for_skill` uses for
# branch names (issue #2545: reused here, not reinvented, for the record
# filename too). `disambiguator` is optional; omit it to mint a fresh one
# the same way `roster.new_lease_disambiguator()` does (8 hex chars) — pass
# one explicitly to scaffold into a workspace that already minted and
# persisted its own (spawn.py's `.record-disambiguator.txt` sidecar). Every
# field spawn_roles.json's role entry's record_fields declares is present
# as a `PLACEHOLDER: <field>` token — `record_lint` treats a surviving
# placeholder as a violation (an invalid enum value) until it is replaced
# with a real one. Refuses to overwrite an existing record.
set -euo pipefail

role="${1:?usage: record-scaffold.sh <role> <issue-n> [target-repo-root] [disambiguator]}"
issue="${2:?usage: record-scaffold.sh <role> <issue-n> [target-repo-root] [disambiguator]}"
root="${3:-$(pwd)}"
disambiguator="${4:-}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# spawn_roles.json lives at the repo root, a sibling of on-the-record/ and
# gates/ — two levels up from on-the-record/hooks/ (issue #2539 stage 6C).
plugin_root="$(cd "$script_dir/../.." && pwd)"

python3 - "$role" "$issue" "$root" "$plugin_root" "$disambiguator" <<'PY'
import json
import secrets
import sys
from pathlib import Path

role, issue, root, plugin_root, disambiguator = sys.argv[1:6]
root = Path(root)
plugin_root = Path(plugin_root)
disambiguator = disambiguator or secrets.token_hex(4)

role_data_file = plugin_root / "spawn_roles.json"
try:
    role_cfg = json.loads(role_data_file.read_text(encoding="utf-8"))[role]
except (OSError, json.JSONDecodeError, KeyError) as e:
    sys.stderr.write(f"record-scaffold: 역할 정의를 읽을 수 없다: {role_data_file} 의 {role!r} ({e})\n")
    sys.exit(1)

name = f"{role}-{disambiguator}"
target = root / "docs" / f"issue-{issue}" / "reports" / f"{name}.md"
if target.exists():
    sys.stderr.write(f"record-scaffold: 이미 존재한다, 덮어쓰지 않는다: {target}\n")
    sys.exit(1)

record_fields = role_cfg.get("record_fields", {})
fm_lines = ["code_under_review:", "  - PLACEHOLDER: path/to/file"]
for field in record_fields:
    fm_lines.append(f"{field}: PLACEHOLDER: {field}")
frontmatter = "\n".join(fm_lines)

body = f"""---
{frontmatter}
---

# issue-{issue} phase 2 — {role} delivery record

upstream: PLACEHOLDER: proposal path

PLACEHOLDER: lead paragraph — one short paragraph stating what changed, why,
and what happens next, in plain prose (no heading, this is the record's lead)

## Summary of work

PLACEHOLDER: summary of work

## Why

PLACEHOLDER: rationale

## What did not work

None.

## Open findings

PLACEHOLDER: open findings

## Next steps

PLACEHOLDER: next steps

## Resolution path

PLACEHOLDER: resolution path
"""

target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(body, encoding="utf-8")
print(f"record-scaffold: wrote {target}")
PY
