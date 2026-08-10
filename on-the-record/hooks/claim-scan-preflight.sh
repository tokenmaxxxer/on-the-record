#!/usr/bin/env bash
# PreToolUse (Bash): claim-scan preflight on gh pr create/edit — issue #476 H1.
#
# Zero-install baseline, same rationale as pr-preflight.sh and
# contract-guard.sh: this script ships with the plugin and needs no gates/
# checkout in the consumer repo, only `python3` on PATH. It ports
# gates/claim_scan.py's CLAIM_RE/EVIDENCE_MARKER_RE/FENCE_RE and the
# fence-adjacency helpers (_fence_spans/_in_fence/_nearby_evidence,
# ADJACENCY_LINES = 5) inline, character-for-character, rather than
# importing them — a zero-install hook cannot assume gates/ sits beside
# on-the-record/ in the consumer repo (architecture-round2 Decision point 3).
# Repo-target traceability (TARGET_RE/_cite_matches) is not ported: this
# hook judges claim + evidence-marker presence only, the text-only mode
# scan_text() runs in when called with no repo_targets.
#
# Scope: intercepts `gh pr create` / `gh pr edit`, same matcher and
# --body/--body-file extraction as pr-preflight.sh, copied verbatim.
#
# Branches:
#   (a) any parse ambiguity (non-matching command, missing python3, absent
#       --body/--body-file, unreadable body-file) -> exit 0, no output.
#   (b) a positive claim-with-no-evidence finding -> exit 0 (warn, does not
#       block), emitting hookSpecificOutput.additionalContext plus a
#       mirrored stderr message naming the claim line, the missing
#       evidence-marker requirement, and the flip-to-deny condition below.
#   (c) future branch, not live code yet: per the H1b flip-to-deny rule,
#       quoted verbatim here --
#       "the decision rule in the pre-registration MUST be iterative --
#       after rollout, measure the registered metric against the
#       threshold": two weeks from this hook's first shipped commit date,
#       if the warn-period correction rate is >= 60%, branch (b) flips
#       from exit 0 (warn) to exit 2 (deny) -- that edit touches only
#       branch (b)'s exit code and nothing else in this file. If the
#       correction rate is < 60% at the two-week mark, this pivots to a
#       documentation fix instead of a flip.
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 0

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, sys

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

# --- extract PR body from the command line itself (verbatim from
# pr-preflight.sh) -----------------------------------------------------------
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
            sys.exit(0)  # unreadable body-file -- nothing to check yet, fail-open

if body is None:
    sys.exit(0)  # no --body/--body-file on the command -- nothing to check yet

# --- ported verbatim from gates/claim_scan.py -------------------------------
ADJACENCY_LINES = 5

CLAIM_RE = re.compile(
    r"\b(reproduced|verified|confirmed|passed|tests?\s+pass(?:es|ed)?|"
    r"repro(?:duces|duced)?)\b",
    re.IGNORECASE,
)
EVIDENCE_MARKER_RE = re.compile(r"^\s*(repro|verify)\s*:", re.IGNORECASE)
FENCE_RE = re.compile(r"^\s*```")


def _fence_spans(lines):
    spans = []
    start = None
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            if start is None:
                start = i
            else:
                spans.append((start, i))
                start = None
    return spans


def _in_fence(spans, i):
    return any(s <= i <= e for s, e in spans)


def _nearby_evidence(lines, idx, spans):
    lo = max(0, idx - ADJACENCY_LINES)
    hi = min(len(lines) - 1, idx + ADJACENCY_LINES)
    chunks = []
    for i in range(lo, hi + 1):
        if _in_fence(spans, i) or EVIDENCE_MARKER_RE.match(lines[i]):
            chunks.append(lines[i])
    return "\n".join(chunks) if chunks else None


def scan_text(text):
    lines = text.splitlines()
    spans = _fence_spans(lines)
    findings = []
    for i, line in enumerate(lines):
        m = CLAIM_RE.search(line)
        if not m:
            continue
        evidence = _nearby_evidence(lines, i, spans)
        if evidence is None:
            findings.append((m.group(0), i + 1, line))
    return findings

findings = scan_text(body)
if not findings:
    sys.exit(0)  # branch (a): no claim-without-evidence -- pass through silently

claim, line_no, line_text = findings[0]
ctx = (
    "claim-scan-preflight: claim '%s' on line %d has no adjacent runnable "
    "evidence (a code fence or a Repro:/Verify: line within %d lines): %s. "
    "This is a warn-only branch under the H1b flip-to-deny pre-registration "
    "-- it does not block yet." % (claim, line_no, ADJACENCY_LINES, line_text.strip())
)
sys.stderr.write(ctx + "\n")
out = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "permissionDecisionReason": ctx,
        "additionalContext": ctx,
    }
}
sys.stdout.write(json.dumps(out))
sys.exit(0)  # branch (b): warn, never block
PY

CG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
