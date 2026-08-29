#!/usr/bin/env bash
# PreToolUse (Write|Edit|MultiEdit|NotebookEdit): deny-only. In an
# orchestrator session (this plugin enabled, not spawned), deliverables
# are SESSION WORK — the coding-rulebook lesson, enforced mechanically after
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
# orchestrator scribing, same category as approvers.md), and the sharded
# per-entry priorities/ directory that replaces priorities.md going
# forward (issue #2637 — same category, priorities.py's shard shape, one
# new file per entry rather than an append to the flat file). No
# scratch/tmp/plugin-cache exemption (issue #2661 — removed): no
# orchestrator write path in this codebase or on-disk plugin install
# actually needs one (verified live, issue #2661 record), and the
# unconditional per-segment form let any deliverable write pass by
# putting a "tmp" folder anywhere in its own path.
# Kill switch: ORCHESTRATE_OFF=1. Fail closed on non-0/2 (now including
# parse failure, not just crashes — the previous header claim here was
# false for the parse-failure path; issue #287 S4).
#
# Spawned-session identity (issue #706, keyed off TOKENMAXXXER_SPAWNED per
# issue #2538): the presence check is resolved inside the Python body from
# the #698 session-role-bind snapshot, falling back to the live env var
# only when no snapshot exists — a spawned session unsetting the env var
# before this hook fires can no longer flip itself into the orchestrator
# branch and dodge its own deliverable-write denial. This hook only ever
# tests presence (never the skill name), so it needs no identity beyond
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
import json, os, posixpath, re, subprocess, sys

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
        "OTR_SKILL_BIND_STATE_DIR",
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
# construction (see `posixpath.normpath` above) only when `file_path`
# arrived relative — the real target directory must start at position 0,
# not appear as an arbitrary suffix.
PRODUCT_CAPTURE_PRIORITIES_DIR_RE = re.compile(
    r"^docs/reports/product/priorities/[^/]+\.md$"
    r"|^docs/issue-\d+/reports/product/priorities/[^/]+\.md$"
)
# issue #2637 (adversarial-review, aba56a87): the `^`-anchor above closes
# the src/-rooted bypass but then never matches when `file_path` arrives
# absolute — `n` is the raw absolute path in that case, not "docs/...".
# A first fix attempt (rejected, PR #2653) re-derived a *cwd*-relative
# form and matched that instead. `cwd` is reported by the calling session
# itself, so a session that `cd src` before its write handed the guard a
# relative form ("docs/reports/product/priorities/hack.md") that lands
# right back inside the exemption — the identical src/-rooted bypass,
# only the calling shape changed. The base a path is made relative to
# must not be something the caller controls. Resolve `n` to an absolute
# path and find the actual repo root by walking up for a `.git` directory
# (the same walk this hook already does lower down to decide whether it's
# even in a board repo) — that root is filesystem truth, not a
# session-reported value. Match the anchored regex against the path
# relative to THAT root. This also closes the relative-path mirror of the
# same bug: a relative `file_path` was previously assumed repo-root-
# relative "by construction", which is only true when cwd happens to be
# the repo root — a session that `cd src` and then writes the identical
# relative shard-looking path was never exercised by the regression test
# and would have been wrongly exempted too. No exemption is granted when
# no git root can be found (falls back to matching raw `n`, unchanged) —
# a narrower miss, never a new bypass.
def _nearest_existing_dir(path):
    # `path` (and any number of its parents) may not exist yet for a
    # brand-new file a write is about to create, and `git -C` requires a
    # directory that already exists to start looking from.
    probe = path
    while probe and probe != "/" and not os.path.isdir(probe):
        probe = posixpath.dirname(probe)
    return probe if probe and os.path.isdir(probe) else "/"


def _run_git(args, cwd):
    env = dict(os.environ)
    env["LC_ALL"] = "C"  # deterministic English output/stderr, so string
                          # matches on git's messages aren't locale-dependent
    try:
        return subprocess.run(
            ["git", "-C", cwd] + list(args),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=10, env=env,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _git_root_from(path_hint):
    # issue #2659: this used to trust `os.path.isdir(<probe>/".git")` as
    # proof that `<probe>` is a real repo root — true for an ordinary
    # clone, but a linked worktree or a submodule marks its root with a
    # `.git` FILE (a "gitdir: <path>" pointer), which `os.path.isdir`
    # never matches, so the walk fell through those layouts entirely.
    # `git rev-parse --show-toplevel` parses both shapes the way git
    # itself does, and — unlike the old walk — does not accept a bare
    # `.git` directory/symlink with no real git content as a repo
    # boundary either: it keeps walking up past one and finds the actual
    # root above it (verified live, issue #2659 record). A session that
    # runs a genuine `git init` in a subdirectory before the guarded
    # write still relocates the perceived root, because that directory
    # is then a real, independent git repository from git's own
    # perspective — that narrower class is unchanged and stays out of
    # scope here (issue #2637, not this issue).
    probe = _nearest_existing_dir(posixpath.dirname(path_hint))
    r = _run_git(["rev-parse", "--show-toplevel"], probe)
    if r is not None and r.returncode == 0:
        top = r.stdout.strip()
        if top:
            return top
    return None

# root_relative_n backs both EXEMPT_SUFFIXES and
# PRODUCT_CAPTURE_PRIORITIES_DIR_RE below — filesystem truth (the actual
# git root), never a caller-supplied cwd or a raw-`n` guess, per the
# src/-rooted-bypass history above. EXEMPT_SUFFIXES used to be matched
# with `n.endswith(...)` against the raw (possibly caller-rooted) `n`
# directly (issue #2661 finding): unanchored suffix matching means any
# path ending in "docs/specs/approvers.md" passes, including
# `tmp/docs/specs/approvers.md` — a real deliverable path one directory
# short of the sanctioned file, verified live to rc=0 EXEMPT against the
# unfixed hook. Matching root_relative_n by exact equality closes that
# the same way the priorities-dir regex's `^`-anchor closed its own
# src/-rooted bypass. PRODUCT_CAPTURE_ISSUE_RE below is intentionally
# left unanchored/unresolved — an adjacent gap of the identical shape,
# not exercised by any acceptance path here; out of scope for issue
# #2661, left as an open finding in that issue's record.
root_relative_n = n
_cwd_for_exemption = e.get("cwd")
_cwd_ok = (isinstance(_cwd_for_exemption, str) and _cwd_for_exemption
           and posixpath.isabs(_cwd_for_exemption))
if posixpath.isabs(n):
    _abs_for_exemption = n
elif _cwd_ok:
    _abs_for_exemption = posixpath.normpath(
        posixpath.join(_cwd_for_exemption, n))
else:
    _abs_for_exemption = None
if _abs_for_exemption is not None:
    _root_for_exemption = _git_root_from(_abs_for_exemption)
    if _root_for_exemption is not None:
        _rel = posixpath.relpath(_abs_for_exemption, _root_for_exemption)
        if _rel != "." and not _rel.startswith(".."):
            root_relative_n = _rel
if (root_relative_n in EXEMPT_SUFFIXES or PRODUCT_CAPTURE_ISSUE_RE.search(n)
        or PRODUCT_CAPTURE_PRIORITIES_DIR_RE.search(root_relative_n)):
    sys.exit(0)
# issue #787 H1 used to widen this from "src/tests?/docs segment only" to
# "everything is a deliverable path" and then carve back out any path
# with a "scratch", "tmp", ".git", or "plugin-cache" segment ANYWHERE in
# it. issue #2661: that carve-out is removed. It was unconditional on
# segment position, so `src/tmp/module.py`, `docs/tmp/note.md`, and any
# other real deliverable path with a "tmp"-named directory anywhere
# passed it (verified live). No real write in this codebase or on-disk
# plugin install needs it, per the same issue's record: no repo code
# (spawn.py, roster.py, pipeline.py, the hooks) creates or writes a
# project-relative `scratch/` or `tmp/` directory, and no installed
# plugin-checkout path on this system has a literal "plugin-cache"
# segment (the real layout is `plugins/cache/...`, two segments, never
# hyphenated as one). `.git` is real — every git repo has one — but no
# legitimate Write/Edit/NotebookEdit call ever targets a path segment
# named `.git` (git itself manages its own internals over a subprocess,
# not through Claude's Write tool); keeping it exempted only offered a
# disguise for a write that would already be suspicious on its own
# terms, not a real use case, so it is removed for that separate reason,
# not carried along with the other three by inheritance.
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
d = n if posixpath.isabs(n) else posixpath.normpath(posixpath.join(cwd, n))

# issue #2659: this activation check used to walk up for a directory
# literally named ".git", which is how an ordinary clone marks its root
# but not how a linked worktree or a submodule checkout does — there
# `.git` is a FILE holding a "gitdir: <path>" pointer, the directory
# walk matched nothing, and the fallback below was to ALLOW the write
# outright (fail-open, in a guard, exactly where the layout is
# unusual). `_run_git` asks git itself instead of hand-rolling a second
# walk with the same weakness — a `.git` file's gitdir pointer is not
# taken on faith, git already validates what it points at before it
# will say "true". When git cannot answer at all (binary missing,
# timeout, unrecognized output), that is reported as a refusal, not an
# allow — "I could not find the root" and "this write is fine" are
# opposite conclusions.
probe = _nearest_existing_dir(posixpath.dirname(d))
r = _run_git(["rev-parse", "--is-inside-work-tree"], probe)
if r is None:
    deny("could not determine whether %s is inside a git repository "
         "(git rev-parse did not run) — cannot verify this write is "
         "outside a board repo, denying rather than silently allowing "
         "it through." % n)
out = r.stdout.strip()
if r.returncode == 0 and out == "true":
    inside = True
elif r.returncode == 0 and out == "false":
    inside = False
elif "not a git repository" in r.stderr.lower():
    inside = False
else:
    deny("could not determine whether %s is inside a git repository "
         "(git rev-parse --is-inside-work-tree exited %d: %s) — cannot "
         "verify this write is outside a board repo, denying rather "
         "than silently allowing it through."
         % (n, r.returncode, r.stderr.strip()))
if not inside:
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
