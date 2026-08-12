#!/usr/bin/env bash
# PreToolUse (Write|Edit|MultiEdit): deny a write under docs/** whose new
# content contains a full-length credential (issue #858, near-miss from
# PR #855 — a truncated gh-token prefix landed in a committed record).
#
# Fail-closed on a full-length token (GitHub gho_/ghp_/ghs_/ghr_ + 36
# base62 chars, github_pat_ + 22 base62 chars, OpenAI-style sk- + 20
# chars, AWS AKIA + 16 chars). A [REDACTED] marker or a short truncated
# prefix (<12 chars of the secret body) passes by construction: the
# long-run pattern below requires the long run to match, so a short
# fragment or a [REDACTED] replacement never trips it.
#
# Modeled on record-claim-guard.sh's shape (JSON payload via stdin,
# path-scoped, EXIT trap remapping any unexpected exit code to 2,
# ORCHESTRATE_OFF kill switch).
#
# MultiEdit fragment-splitting bypass (after-proposal hunt finding,
# docs/issue-858/reports/implementation/2026-08-11-hunt-credential-record-guard.md):
# checking each edits[].new_string independently misses a credential
# split across two adjacent edits. This hook additionally checks the
# no-separator concatenation of all edits[].new_string values (in edit
# order) against the same patterns.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 2
CRG_HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, posixpath, re, sys

def deny(msg):
    sys.stderr.write("credential-record-guard: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("CRG_PAYLOAD", ""))
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
if not re.search(r"(^|/)docs/", n):
    sys.exit(0)

# Import only after the scope checks above: a missing/unresolvable
# allowlist module must not crash-deny every Write/Edit/MultiEdit call,
# only ones that would otherwise reach the credential scan (after-
# proposal hunt finding, docs/issue-1033/reports/implementation/hunt-credential-example-allowlist.md).
sys.path.insert(0, os.environ.get("CRG_HOOKS_DIR", ""))
from credential_example_allowlist import EXAMPLE_ALLOWLIST

PATTERNS = [
    (r"gh[oprs]_[A-Za-z0-9]{36,}", "GitHub token"),
    (r"github_pat_[A-Za-z0-9_]{22,}", "GitHub fine-grained PAT"),
    (r"sk-[A-Za-z0-9]{20,}", "OpenAI-style secret key"),
    (r"AKIA[0-9A-Z]{16}", "AWS access key"),
]

def find_credentials(text):
    hits = []
    for pat, label in PATTERNS:
        for m in re.finditer(pat, text):
            if m.group(0) in EXAMPLE_ALLOWLIST:
                continue
            # A [REDACTED] marker immediately after the matched span
            # means the secret body was already replaced; not a leak.
            tail = text[m.end():m.end() + 11]
            if tail.startswith("[REDACTED]"):
                continue
            hits.append(label)
    return hits

# Fragments: Write carries full content; Edit/MultiEdit carry only the
# changed fragment(s) (write-time approximation, not full-file re-read).
fragments = []
nc = ti.get("content")
if isinstance(nc, str):
    fragments.append(nc)
ns = ti.get("new_string")
if isinstance(ns, str):
    fragments.append(ns)
edits = ti.get("edits")
edit_strings = []
if isinstance(edits, list):
    for ed in edits:
        if isinstance(ed, dict) and isinstance(ed.get("new_string"), str):
            edit_strings.append(ed["new_string"])
            fragments.append(ed["new_string"])

hits = []
for frag in fragments:
    hits += find_credentials(frag)

# MultiEdit fragment-splitting: check the no-separator concatenation of
# all edit fragments in order, catching a credential split across two
# adjacent edits that are each individually short/no-match.
if len(edit_strings) >= 2:
    hits += find_credentials("".join(edit_strings))

if hits:
    deny(
        "full-length credential pattern (%s) in a docs/** write is denied. "
        "Use [REDACTED] or a short truncated prefix instead."
        % ", ".join(sorted(set(hits)))
    )
sys.exit(0)
PY

CRG_PAYLOAD="$payload" CRG_HOOKS_DIR="$CRG_HOOKS_DIR" python3 -c "$GUARD"
rc=$?
exit "$rc"
