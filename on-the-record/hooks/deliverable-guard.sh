#!/usr/bin/env bash
# PreToolUse (Write|Edit|MultiEdit|NotebookEdit): deny-only. In an
# orchestrator session (this plugin enabled, not spawned), deliverables
# are ROLE WORK — the coding-rulebook lesson, enforced mechanically after
# a live session authored a requirements doc itself despite the directive.
#
# Denied: writes to any deliverable-shaped path in a target repo — not
# just the src/, test(s)/, docs/-segment layout, but also a flat
# top-level package layout with no such segment (issue #787 H1: the
# #776 baseline fixture's `fixture_target/__init__.py` and
# `test_fixture_target.py` sat beside each other with no src/test/docs
# segment at all, and the old segment-only regex let both through
# unexamined). Also denied: an unparseable stdin payload (empty, non-JSON,
# non-dict JSON, missing file_path) — issue #287 S4: a delivery failure
# on stdin must not silently become an ALLOW.
# Allowed: docs/specs/approvers.md (the file the orchestrator is
# sanctioned to write, with the user's confirmation), the
# product-capture-stopgate.sh category files under docs/reports/product/
# and docs/issue-<n>/reports/product/ (issue #1111 — product capture is
# orchestrator scribing, same category as approvers.md), the sharded
# per-entry priorities/ directory that replaces priorities.md going
# forward (issue #2637 — same category, priorities.py's shard shape, one
# new file per entry rather than an append to the flat file), and
# anything under a scratch/tmp path or a .git/plugin-cache directory (the
# muster checkout itself, scratch notes).
# Kill switch: ORCHESTRATE_OFF=1. Fail closed on non-0/2 (now including
# parse failure, not just crashes — the previous header claim here was
# false for the parse-failure path; issue #287 S4).
#
# Spawned-session identity (issue #706, keyed off TOKENMAXXXER_SPAWNED per
# issue #2538): the presence check is resolved inside the Python body from
# the #698 session-role-bind snapshot, falling back to the live env var
# only when no snapshot exists — a role session unsetting the env var
# before this hook fires can no longer flip itself into the orchestrator
# branch and dodge its own deliverable-write denial. This hook only ever
# tests presence (never the role name), so it needs no identity beyond
# "was this session spawned" — see approval-gate.sh for the ported
# resolve pattern.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"

# No fast-path skip on "doesn't look like src/test/docs" here anymore:
# that shortcut used to also skip empty/malformed payloads straight to
# ALLOW (issue #287 S4), since those don't contain the substring either.
# python3 below re-derives the real allow/deny decision from tool_name,
# file_path, and the same exemption checks — it is the single source of
# truth.
command -v python3 >/dev/null 2>&1 || exit 2

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, posixpath, re, sys

def deny(msg):
    sys.stderr.write("orchestrate: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("ORCH_PAYLOAD", ""))
except ValueError:
    deny("stdin payload is not valid JSON — cannot verify this write is "
         "safe, denying rather than silently allowing it through.")
if not isinstance(e, dict):
    deny("stdin payload is not a JSON object — cannot verify this write is "
         "safe, denying rather than silently allowing it through.")

# --- spawned identity: prefer the SessionStart-bound snapshot (issue #698,
# #2538) ----------------------------------------------------------------
# same resolve-with-fallback pattern as approval-gate.sh: a role session
# that unsets TOKENMAXXXER_SPAWNED before this Write/Edit no longer flips
# this hook into treating the write as orchestrator-authored.
spawned = bool(os.environ.get("TOKENMAXXXER_SPAWNED", ""))
session_id = e.get("session_id")
if isinstance(session_id, str) and session_id:
    state_dir = os.environ.get(
        "OTR_ROLE_BIND_STATE_DIR",
        os.path.join(os.environ.get("TMPDIR", "/tmp"), "otr-role-bind"),
    )
    safe_session = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)
    snapshot_path = os.path.join(state_dir, safe_session + ".json")
    try:
        with open(snapshot_path, encoding="utf-8") as f:
            snapshot = json.load(f)
        if isinstance(snapshot, dict) and "spawned" in snapshot:
            spawned = bool(snapshot["spawned"])
    except (OSError, ValueError):
        pass  # no snapshot yet — fall back to the live env var
if spawned:
    sys.exit(0)  # role session — deliverable writes are its own job, not this hook's

if (e.get("tool_name") or "") not in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
    sys.exit(0)
ti = e.get("tool_input") or {}
p = ti.get("file_path") or ti.get("notebook_path") if isinstance(ti, dict) else None
if not isinstance(p, str) or not p:
    deny("tool_input is missing file_path/notebook_path — cannot verify "
         "this write's target, denying rather than silently allowing it "
         "through.")

n = posixpath.normpath(p.replace("\\", "/"))
# Orchestrator scribing exemptions: docs/specs/approvers.md, plus the
# product-capture-stopgate.sh categories (issue #1111) — both are the
# orchestrator's own recognized job, not role work.
EXEMPT_SUFFIXES = (
    "docs/specs/approvers.md",
    "docs/reports/product/requirements.md",
    "docs/reports/product/priorities.md",  # legacy, frozen (issue #2637)
    "docs/reports/product/philosophy.md",
    "docs/reports/product/goals.md",
)
PRODUCT_CAPTURE_ISSUE_RE = re.compile(
    r"docs/issue-\d+/reports/product/"
    r"(requirements|priorities|philosophy|goals)\.md$"
)
# issue #2637: priorities.md's replacement is a directory of per-entry
# shard files (priorities.py), not a single path — same category as the
# flat-file suffixes above, just directory-shaped. `[^/]+\.md$` (not
# `.*`) so this only ever matches a shard file directly inside the
# priorities/ directory, never an unrelated nested path that happens to
# contain the segment. Anchored with `^` (warrant-hunt, issue #2637,
# before-landing dispatch): `.search()` with no anchor let a path like
# `src/docs/reports/product/priorities/hack.md` pass this exemption
# merely by ENDING with the recognized suffix, exempting a real
# deliverable write under `src/`. `n` is repo-root-relative by
# construction (see `posixpath.normpath` above), so the real target
# directory must start at position 0, not appear as an arbitrary suffix.
PRODUCT_CAPTURE_PRIORITIES_DIR_RE = re.compile(
    r"^docs/reports/product/priorities/[^/]+\.md$"
    r"|^docs/issue-\d+/reports/product/priorities/[^/]+\.md$"
)
if (n.endswith(EXEMPT_SUFFIXES) or PRODUCT_CAPTURE_ISSUE_RE.search(n)
        or PRODUCT_CAPTURE_PRIORITIES_DIR_RE.search(n)):
    sys.exit(0)
# issue #787 H1: the old src/tests?/docs-segment-only regex missed a flat
# top-level package layout (no such segment at all). Widen to "everything
# is a deliverable path" and instead exempt the narrow set of paths that
# are never a deliverable: scratch/tmp work areas and the plugin's own
# .git/plugin-cache internals.
segs = [s for s in n.split("/") if s]
if any(s in ("scratch", "tmp", ".git", "plugin-cache") for s in segs):
    sys.exit(0)
# Only guard writes inside a git repo reachable from cwd (issue #787 H1:
# the target repo no longer needs to already carry docs/specs/approvers.md
# itself — that used to be the sole activation signal, which silently
# no-ops on an ordinary, freshly-instantiated target repo that has no
# board files yet). A random project the user is hand-editing outside any
# git repo is still not this gate's business.
cwd = e.get("cwd")
if not isinstance(cwd, str) or not cwd or not posixpath.isabs(cwd):
    deny("PreToolUse payload is missing an absolute cwd — cannot verify "
         "this write's target relative to the session's actual working "
         "directory, denying rather than silently resolving a relative "
         "cwd against the hook process's own unrelated cwd.")
root = None
d = n if posixpath.isabs(n) else posixpath.normpath(posixpath.join(cwd, n))
probe = posixpath.dirname(d)
while probe and probe != "/":
    if os.path.isdir(posixpath.join(probe, ".git")):
        root = probe
        break
    probe = posixpath.dirname(probe)
if root is None:
    sys.exit(0)

deny("this is an orchestrator session and %s is a deliverable path in a "
     "board repo. Deliverables are role work: draft the issue, get the "
     "user's confirmation, and spawn a session (spawn.py --skills <skill> "
     "\"<task>\" --issue <n> — issue #2572: --skills is the sole spawn "
     "form). You author only confirmed issues, PR comments, and "
     "docs/specs/approvers.md." % n)
PY

ORCH_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
trap - EXIT
exit "$rc"
