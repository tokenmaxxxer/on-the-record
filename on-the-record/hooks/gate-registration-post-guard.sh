#!/usr/bin/env bash
# PreToolUse+PostToolUse pair: post-commit REPORT (not deny) companion to
# gate-registration-guard.sh -- issue #2705.
#
# gate-registration-guard.sh reads `git diff --cached --name-status` from a
# PreToolUse hook, which fires *before* the intercepted Bash command's text
# runs. For the unbundled shape (stage in one Bash call, commit in a
# following one) that is correct: by the time the `git commit` call fires
# this hook, the earlier `git add` call already completed as its own
# finished tool invocation, so the staged set the hook reads is real. For
# the bundled shape this repo's own landing-batching guidance (#2135)
# recommends -- `git add gates/new_gate.py && git commit -m "..."` in one
# Bash call -- the `git add` has not run yet at PreToolUse-fire time, so
# `--cached` is empty and the check passes silently. That is not a parsing
# gap to patch: #2705's four adversarial rounds on a text-predicting parser
# (cd/subshell resolution, pushd/popd stack, symlinks) each closed one
# shape and the next round found a fresh one inside the SAME family, and
# the seam consult concluded a parser predicting bash's staged-set from
# command text is undecidable in principle (subshells, aliases, functions,
# CDPATH all change what a command stages without changing what it looks
# like). Two honest options followed from that: keep gate-registration-
# guard.sh at PreToolUse and declare the bundled shape outside its
# jurisdiction, or move the check to the point where git itself already
# knows the answer and say plainly that this is a WEAKER promise -- a
# report after the write exists, not a refusal before it. This hook is the
# second option, chosen because the alternative (declaring the bundled
# shape out of jurisdiction) would leave #2705's own acceptance criterion
# unmet: it requires the guard to actually fire on the bundled shape, not
# to disclaim it.
#
# This hook does NOT predict anything from command text. It reads git's
# OWN record of what actually happened:
#
#   post -- PostToolUse/Bash. A `git commit` that just ran prints its own
#           result to stdout in a fixed shape git has used unchanged for
#           decades: `[<branch> <sha>] <subject>` (or
#           `[<branch> (root-commit) <sha>] <subject>`). No exit-code field
#           is available in the PostToolUse payload for Bash (same gap
#           post-landing-obligation-gate.sh's own comment documents), so
#           this mode greps that line out of `tool_response` -- not the
#           command text -- to get the EXACT sha git assigned. It then
#           inspects that commit's own tree via `git show --name-status`,
#           the identical is_gate_module/is_hook_script/is_workflow
#           classification and docs/specs/enforcement-boundary.md /
#           docs/specs/generated-paths.md / hooks.json cross-check
#           gate-registration-guard.sh already implements (intentionally
#           duplicated rather than imported -- see that script's own
#           comment on the "ported inline, no guaranteed checkout"
#           convention every sibling gate in this file follows). A miss
#           writes a pending-violation record to
#           ${OTR_GRG_POST_STATE_DIR:-$TMPDIR/otr-grg-post}/<session_id>.json.
#           Cannot deny (same invariant post-landing-obligation-gate.sh's
#           comment states: PostToolUse fires after the write already
#           landed) -- this mode is pure side-effect, always exit 0.
#   pre  -- PreToolUse, any tool (same broad matcher approach-cap-
#           warning.sh's "pre" mode already uses) -- reads the state file
#           and, for every still-open violation, re-checks the CURRENT
#           working tree (a follow-up commit may have already added the
#           row) before deciding whether to speak. A violation still open
#           emits hookSpecificOutput.additionalContext, in the words a
#           session actually reads, not only in this header comment:
#           the commit named already exists, this hook cannot block or
#           revert it, and the registration row belongs in a follow-up
#           commit now. Repeats on every tool call until the row lands or
#           the state entry is manually cleared, mirroring approach-cap-
#           warning.sh's own "cannot scroll out of context" rationale. A
#           row that lands clears the entry and the nagging stops.
#
# What this pair does NOT restore: the strong guarantee -- refuse the
# write before it happens -- for the bundled shape specifically. That
# guarantee is structurally unavailable there (PreToolUse fires once, over
# the whole compound command, not between its `&&`-joined parts) and no
# amount of additional command-text parsing changes that; #2705's own
# adversarial-review history is the record of that route running out of
# road. gate-registration-guard.sh's PreToolUse/`--cached` check is
# unchanged by this file and keeps blocking the unbundled shape exactly as
# before.
#
# Kill switch: ORCHESTRATE_OFF=1 (same convention as every other gate
# here), checked in both modes.
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac

MODE="${1:-}"
case "$MODE" in pre|post) ;; *) exit 1 ;; esac

STATE_DIR="${OTR_GRG_POST_STATE_DIR:-${TMPDIR:-/tmp}/otr-grg-post}"

# `pre` fires on EVERY tool call (broad matcher) -- the overwhelmingly
# common case is no session anywhere has an open violation, so this checks
# for a fully empty state dir FIRST, before reading stdin or spawning any
# other process (mkdir, command -v, python3): plain glob + `[ -e ]`, no
# fork at all when the dir doesn't exist or is empty. `post` gets its own
# equivalent cheap short-circuit below (payload text can't possibly be a
# `git commit`).
if [ "$MODE" = "pre" ]; then
    _has_state=""
    for _f in "$STATE_DIR"/*.json; do
        [ -e "$_f" ] && { _has_state=1; break; }
    done
    [ -n "$_has_state" ] || exit 0
fi

payload="$(cat 2>/dev/null || true)"
[ -n "$payload" ] || exit 0

if [ "$MODE" = "post" ]; then
    # issue #2016-style cheap short-circuit before the python3 spawn: a
    # payload that cannot possibly contain a `git commit` invocation or a
    # commit-success line skips the interpreter entirely.
    { grep -qF 'git' <<<"$payload" && grep -qF 'commit' <<<"$payload"; } || exit 0
fi

command -v python3 >/dev/null 2>&1 || exit 0
command -v git >/dev/null 2>&1 || exit 0

mkdir -p "$STATE_DIR" 2>/dev/null || true

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, subprocess, sys

mode = os.environ.get("OTR_GRG_POST_MODE", "")
state_dir = os.environ.get("OTR_GRG_POST_STATE_DIR", "")

try:
    e = json.loads(os.environ.get("OTR_GRG_POST_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict):
    sys.exit(0)

session_id = e.get("session_id")
if not isinstance(session_id, str) or not session_id:
    sys.exit(0)
safe_session = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)
state_path = os.path.join(state_dir, safe_session + ".json")


def _load():
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get("violations"), list):
            return data
    except (OSError, ValueError):
        pass
    return {"violations": []}


def _save(data):
    try:
        tmp = state_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp, state_path)
    except OSError:
        pass


def is_gate_module(p):
    if not p.startswith("gates/") or "/" in p[len("gates/"):]:
        return False
    name = os.path.basename(p)
    if not name.endswith(".py") or name.startswith("test_") or name == "__init__.py":
        return False
    return True


def is_hook_script(p):
    if not p.startswith("on-the-record/hooks/") or "/" in p[len("on-the-record/hooks/"):]:
        return False
    return os.path.basename(p).endswith(".sh")


def is_workflow(p):
    if not p.startswith(".github/workflows/") or "/" in p[len(".github/workflows/"):]:
        return False
    return os.path.basename(p).endswith(".yml")


_ROW_RE = re.compile(r"^\|\s*`?([^`|]+?)`?\s*\|\s*(.+?)\s*\|", re.MULTILINE)
_SEP_ROW = re.compile(r"^\|[\s:-]+\|")
_NOT_WIRED_RE = re.compile(
    r"not a hook itself|not wired into `?hooks\.json`?|CLI-invoked",
    re.IGNORECASE,
)


def recorded_names(text):
    out = set()
    for line in text.splitlines():
        if not line.startswith("|") or _SEP_ROW.match(line):
            continue
        m = _ROW_RE.match(line)
        if not m:
            continue
        name, verdict = m.group(1).strip(), m.group(2).strip()
        if name in ("mechanism", "act") or not verdict:
            continue
        out.add(name)
    return out


def boundary_row_text(text, name):
    for line in text.splitlines():
        if line.startswith("|") and not _SEP_ROW.match(line) and f"`{name}`" in line:
            return line
    return ""


# --- shared: given a repo_root and a source ("commit", sha) or
# ("worktree", None), read a spec file from that source and derive the
# missing-registration list for the newly-added mechanism files touched
# there. Mirrors gate-registration-guard.sh's own detection scope: only
# gates/*.py (excluding test_*.py/__init__.py), on-the-record/hooks/*.sh,
# .github/workflows/*.yml, and only the missing-row class (issue
# #839 classification-mismatch class is gate-registration-guard.sh's own
# concern at commit time and is not re-derived here after the fact).
def read_from_worktree(repo_root, rel_path):
    try:
        with open(os.path.join(repo_root, rel_path), "r", encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None


def read_from_commit(repo_root, sha, rel_path):
    r = subprocess.run(["git", "show", f"{sha}:{rel_path}"],
                        capture_output=True, timeout=20, cwd=repo_root)
    if r.returncode != 0:
        return None
    try:
        return r.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return None


def missing_rows(repo_root, targets, read_spec):
    if not targets:
        return []
    boundary_text = read_spec("docs/specs/enforcement-boundary.md")
    boundary_names = recorded_names(boundary_text) if boundary_text is not None else set()
    missing = []
    for p in targets:
        name = os.path.basename(p)
        if name not in boundary_names:
            missing.append(f"{p}: no row in docs/specs/enforcement-boundary.md")
    hook_scripts = [p for p in targets if is_hook_script(p)]
    if hook_scripts:
        paths_text = read_spec("docs/specs/generated-paths.md")
        paths_names = recorded_names(paths_text) if paths_text is not None else set()
        for p in hook_scripts:
            name = os.path.basename(p)
            if name in boundary_names and name not in paths_names:
                missing.append(f"{p}: no row in docs/specs/generated-paths.md")
        hooks_json_text = read_spec("on-the-record/hooks/hooks.json")
        if hooks_json_text is not None:
            try:
                parsed = json.loads(hooks_json_text).get("hooks", {})
                wired = set()
                for group_list in parsed.values():
                    for group in group_list:
                        for h in group.get("hooks", []):
                            for tok in h.get("command", "").split():
                                if tok.endswith(".sh"):
                                    wired.add(os.path.basename(tok))
            except ValueError:
                wired = None
            else:
                for p in hook_scripts:
                    name = os.path.basename(p)
                    if name not in boundary_names:
                        continue
                    row = boundary_row_text(boundary_text, name)
                    if _NOT_WIRED_RE.search(row):
                        continue
                    if name not in wired:
                        missing.append(
                            f"{p}: docs/specs/enforcement-boundary.md claims this is a "
                            "live hook but on-the-record/hooks/hooks.json has no "
                            "command entry for it (issue #909)"
                        )
    return missing


def resolve_repo_root(cwd):
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                            capture_output=True, text=True, timeout=20, cwd=cwd)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    root = r.stdout.strip()
    return root or None


if mode == "post":
    if (e.get("tool_name") or "") != "Bash":
        sys.exit(0)
    resp = e.get("tool_response")
    if isinstance(resp, str):
        text = resp
    elif resp is not None:
        text = json.dumps(resp)
    else:
        sys.exit(0)
    # git's own commit-success line -- unparsed from the command text,
    # read from git's own reported outcome instead (issue #2705's seam
    # consult: "stop predicting the staged set from command text").
    shas = re.findall(
        r"^\[\S+(?:\s+\(root-commit\))?\s+([0-9a-fA-F]{4,40})\]",
        text, re.MULTILINE,
    )
    if not shas:
        sys.exit(0)  # --quiet, nothing to commit, or the commit failed

    cwd = e.get("cwd") or os.getcwd()
    repo_root = resolve_repo_root(cwd)
    if not repo_root:
        sys.exit(0)

    data = _load()
    known = {(v["sha"], v["path"]) for v in data["violations"]}
    for sha in shas:
        r = subprocess.run(["git", "show", "--name-status", "--format=", sha],
                            capture_output=True, text=True, timeout=20, cwd=repo_root)
        if r.returncode != 0:
            continue
        added = []
        for line in r.stdout.splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            status, path = parts[0], parts[-1]
            if status == "A" or status[:1] in ("R", "C"):
                added.append(path)
        targets = sorted(
            p for p in added
            if is_gate_module(p) or is_hook_script(p) or is_workflow(p)
        )
        if not targets:
            continue
        read_spec = lambda rel, _sha=sha: read_from_commit(repo_root, _sha, rel)
        for msg in missing_rows(repo_root, targets, read_spec):
            path = msg.split(":", 1)[0]
            key = (sha, path)
            if key in known:
                continue
            known.add(key)
            data["violations"].append({"sha": sha, "path": path, "message": msg})
    _save(data)
    sys.exit(0)

# mode == "pre"
data = _load()
if not data["violations"]:
    sys.exit(0)

cwd = e.get("cwd") or os.getcwd()
repo_root = resolve_repo_root(cwd)
if not repo_root:
    sys.exit(0)

still_open = []
for v in data["violations"]:
    path = v["path"]
    read_spec = lambda rel, _root=repo_root: read_from_worktree(_root, rel)
    remaining = missing_rows(repo_root, [path], read_spec)
    if remaining:
        still_open.append(v)

if len(still_open) != len(data["violations"]):
    data["violations"] = still_open
    _save(data)

if not still_open:
    sys.exit(0)

lines = [
    "gate-registration-guard (post-commit report, issue #2705): the "
    "following commit(s) already exist in git history and cannot be "
    "blocked or reverted by this hook -- gate-registration-guard.sh only "
    "sees a `git commit`'s staged set BEFORE the command runs, so a "
    "bundled `git add ... && git commit ...` call left nothing to refuse "
    "at the time it fired:",
]
for v in still_open:
    lines.append(f"  - {v['sha'][:12]}: {v['message']}")
lines.append(
    "Add the missing row(s) above in a follow-up commit now. This report "
    "is the weaker half of a deliberate two-guard split (issue #2705): "
    "gate-registration-guard.sh's own PreToolUse/`--cached` check is "
    "unchanged and still REFUSES the commit outright when the file was "
    "staged in an earlier, separate Bash call -- only the single-call "
    "bundled shape lands first and is reported after the fact."
)
out = {"hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "\n".join(lines),
}}
sys.stdout.write(json.dumps(out))
sys.exit(0)
PY

OTR_GRG_POST_PAYLOAD="$payload" OTR_GRG_POST_MODE="$MODE" OTR_GRG_POST_STATE_DIR="$STATE_DIR" \
  python3 -c "$GUARD"
exit 0
