#!/usr/bin/env bash
# PreToolUse (Bash): deny-before-effect gate on git commit axis-completeness
# drift in roles/*.json (issue #650, hunt #628 finding).
#
# gates/role_spec_shape.py's check_axis_ownership/check_role_judgment_axes
# (issue-573) are real, unit-tested functions with zero operational
# caller — the exact dead-code class already fixed once in #594/#586, now
# recurring. This hook wires a real caller: on a `git commit` attempt it
# reads the staged `roles/*.json` set (git show :<path> for staged paths,
# falling back to the working tree for any roles/*.json not itself staged,
# since axis ownership is evaluated across the WHOLE set) and denies the
# commit when an axis is owned by zero or by more than one role, or a
# role's own judgment_axes shape is invalid.
#
# Import, not re-port: same precedent role-spec-reference-guard.sh already
# set for this exact module. The packaged on-the-record/gates copy can lag
# the top-level gates/ (observed: check_axis_ownership/
# check_role_judgment_axes exist at gates/role_spec_shape.py but not yet in
# the packaged on-the-record/gates copy) — so this hook tries each
# candidate gates dir in turn and uses the first one that actually exposes
# both functions, rather than hard-coding a single stale path.
#
# The `git commit` detection itself is a `shlex.split` token check, not
# a substring regex (issue #876, porting the fix #866 landed in
# spec-index-preflight.sh) — a plain `\bgit\s+commit\b` substring match
# misses `git -c <key>=<val> commit ...`, letting a global option
# between `git` and `commit` bypass the trigger entirely.
#
# Fail-open on environment gaps (missing python3/git, no candidate module
# exposes the needed functions, not a git-commit command, no staged
# roles/*.json): those are not a positively-determined violation. Fail-
# closed (exit 2) only when the assembled roles/*.json set positively
# fails axis completeness.
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 0
command -v git >/dev/null 2>&1 || exit 0

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cand1=""
cand2=""
[ -d "$script_dir/../gates" ] && cand1="$(cd "$script_dir/../gates" && pwd)"
[ -d "$script_dir/../../gates" ] && cand2="$(cd "$script_dir/../../gates" && pwd)"

IFS='' read -r -d '' GUARD <<'PY' || true
import glob, importlib.util, json, os, shlex, subprocess, sys

def deny(msg):
    sys.stderr.write("role-axis-completeness-guard: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("RACG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str):
    sys.exit(0)

import re

# issue #866/#876: a plain `\bgit\s+commit\b` substring match misses an
# ordinary `git -c <key>=<val> commit ...` (or any other global option
# between `git` and its `commit` subcommand) -- tokenizing first and
# checking for the two tokens survives any number of intervening
# options, and (unlike a looser substring check) does not fire on
# `commit` appearing inside an unrelated token (`--grep=commit`,
# `commit-tree`) or inside a quoted string.
try:
    tokens = shlex.split(cmd)
except ValueError:
    sys.exit(0)
if "git" not in tokens or "commit" not in tokens:
    sys.exit(0)

cwd = e.get("cwd") or os.getcwd()

def load_role_spec_shape():
    candidates = [c for c in (os.environ.get("RACG_GATES_CAND1") or "",
                               os.environ.get("RACG_GATES_CAND2") or "") if c]
    for i, gates_dir in enumerate(candidates):
        mod_path = os.path.join(gates_dir, "role_spec_shape.py")
        if not os.path.isfile(mod_path):
            continue
        try:
            spec = importlib.util.spec_from_file_location(
                "racg_role_spec_shape_%d" % i, mod_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        except Exception:
            continue
        if hasattr(mod, "check_axis_ownership") and hasattr(mod, "check_role_judgment_axes"):
            return mod
    return None

role_spec_shape = load_role_spec_shape()
if role_spec_shape is None:
    sys.exit(0)

try:
    r = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, timeout=20, cwd=cwd,
    )
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
if r.returncode != 0:
    sys.exit(0)
repo_root = r.stdout.strip()
if not repo_root:
    sys.exit(0)

try:
    r = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True, timeout=20, cwd=repo_root,
    )
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
if r.returncode != 0:
    sys.exit(0)
staged = set(line.strip() for line in r.stdout.splitlines() if line.strip())
staged_role_files = sorted(p for p in staged if re.match(r"^roles/[^/]+\.json$", p))
if not staged_role_files:
    sys.exit(0)

def git_show_text(rel_path):
    rr = subprocess.run(
        ["git", "show", ":" + rel_path],
        capture_output=True, timeout=20, cwd=repo_root,
    )
    if rr.returncode != 0:
        return None
    try:
        return rr.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return None

all_role_paths = set(
    os.path.relpath(p, repo_root).replace(os.sep, "/")
    for p in glob.glob(os.path.join(repo_root, "roles", "*.json"))
) | set(staged_role_files)

roles = {}
for rel_path in sorted(all_role_paths):
    if not re.match(r"^roles/[^/]+\.json$", rel_path):
        continue
    name = rel_path[len("roles/"):-len(".json")]
    text = None
    if rel_path in staged:
        text = git_show_text(rel_path)
    if text is None:
        abs_path = os.path.join(repo_root, rel_path)
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                text = f.read()
        except OSError:
            continue
    try:
        roles[name] = json.loads(text)
    except ValueError:
        deny(f"{rel_path}: unreadable/invalid JSON, cannot evaluate axis completeness")

reasons = []
for name, cfg in roles.items():
    for reason in role_spec_shape.check_role_judgment_axes(cfg):
        reasons.append(f"roles/{name}.json: {reason}")
for reason in role_spec_shape.check_axis_ownership(roles):
    reasons.append(reason)

if reasons:
    deny("axis-completeness violation(s):\n" + "\n".join(reasons))
PY

RACG_PAYLOAD="$payload" RACG_GATES_CAND1="$cand1" RACG_GATES_CAND2="$cand2" python3 -c "$GUARD"
rc=$?
exit "$rc"
