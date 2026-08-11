#!/usr/bin/env bash
# PreToolUse (Bash): deny-before-effect gate on a newly-staged gate/hook
# module with no matching row in docs/specs/enforcement-boundary.md (and,
# for a new on-the-record/hooks/*.sh file, docs/specs/generated-paths.md)
# — issue #759.
#
# #689 fixed this exact registration gap once (2026-08-11 00:08); the
# omission recurred within a day because only gates/test_boundary.py /
# gates/test_generated_paths.py catch it, and this repo runs no CI
# (#460) to run that pytest suite automatically. This hook ports the
# same derive-and-compare presence check those two test modules already
# implement inline (zero-install, no repo checkout guaranteed at
# hook-invocation time beyond the commit's own cwd), so the next
# newly-added gate/hook module has to land its spec row in the same
# commit instead of relying on someone remembering to run the suite.
#
# Trigger is narrow by design (matching spec-index-preflight.sh/
# role-axis-completeness-guard.sh precedent): only a NEWLY-STAGED (git
# diff --cached --name-status "A", or the destination side of an "R"/"C"
# rename/copy — before-landing hunt, stance 0: a rename lands a
# never-registered file at a target path without ever showing "A")
# gates/*.py (excluding test_*.py/__init__.py) / on-the-record/hooks/*.sh
# / .github/workflows/*.yml file fires this check — editing an
# already-registered module's internals (plain "M"), or any unrelated
# commit, is untouched (the ambient-noise failure mode #744
# investigates). The `git commit` detection itself is a `shlex.split`
# token check, not a substring regex (issue #876, porting the fix
# #866 landed in spec-index-preflight.sh) — a plain `\bgit\s+commit\b`
# substring match misses `git -c <key>=<val> commit ...`, letting a
# global option between `git` and `commit` bypass the trigger entirely.
#
# Fail-open on any environment gap (missing python3/git, not a `git
# commit` command, no newly-staged mechanism file, unreadable spec
# file). Fail-closed (exit 2) only when a newly-staged mechanism file's
# basename has no row in the relevant spec(s).
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 0
command -v git >/dev/null 2>&1 || exit 0

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, shlex, subprocess, sys

def deny(msg):
    sys.stderr.write("gate-registration-guard: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("GRG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str):
    sys.exit(0)

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
        ["git", "diff", "--cached", "--name-status"],
        capture_output=True, text=True, timeout=20, cwd=repo_root,
    )
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
if r.returncode != 0:
    sys.exit(0)

staged_all = set()
added = []
for line in r.stdout.splitlines():
    if not line.strip():
        continue
    parts = line.split("\t")
    if len(parts) < 2:
        continue
    status, path = parts[0], parts[-1]
    staged_all.add(path)
    # "A" is a plain new file. A rename/copy ("R100"/"C100"/"R<NN>") also
    # introduces its destination path fresh -- an existing tracked file
    # renamed into a target location is indistinguishable from a brand
    # new, never-registered module at that path, and a follow-up edit
    # would show as plain "M" (which this guard intentionally leaves
    # untouched for already-registered modules), so the rename step
    # itself is the only point this can still be caught (before-landing
    # hunt, stance 0).
    if status == "A" or status[:1] in ("R", "C"):
        added.append(path)


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


gate_modules = sorted(p for p in added if is_gate_module(p))
hook_scripts = sorted(p for p in added if is_hook_script(p))
workflows = sorted(p for p in added if is_workflow(p))

targets = gate_modules + hook_scripts + workflows
if not targets:
    sys.exit(0)

_ROW_RE = re.compile(r"^\|\s*`?([^`|]+?)`?\s*\|\s*(.+?)\s*\|", re.MULTILINE)
_SEP_ROW = re.compile(r"^\|[\s:-]+\|")

# Ported from gates/test_generated_paths.py's _WRITE_CALL_RE/_ISSUE_PLACEHOLDER_RE
# (issue #839) -- same inline-porting convention _ROW_RE above already uses
# for that module's _ROW_RE, for the same no-guaranteed-checkout reason.
_WRITE_CALL_RE = re.compile(
    r"write_text\(|open\([^)]*['\"]w|\.mkdir\(|shutil\.(copy|move)|"
    r"\bmkdir\s+-p\b|\bgit\s+clone\b"
)
_ISSUE_PLACEHOLDER_RE = re.compile(
    r"issue-\$\{?issue|issue-\{issue|f[\"'].*issue[_-]?\{|issue-\(\?P<n>|"
    r"docs/issue-|issue-\d\+.*rev-parse|re\.match.*issue-"
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


def recorded_classifications(text):
    """{mechanism: classification} from a generated-paths.md-shaped table.

    _ROW_RE's second (non-greedy) capture group lands on the classification
    column for a 3-column table (mechanism | classification | verdict) --
    same regex recorded_names() already uses for the 2-column presence
    check, reused here for its second group instead of discarding it.
    """
    out = {}
    for line in text.splitlines():
        if not line.startswith("|") or _SEP_ROW.match(line):
            continue
        m = _ROW_RE.match(line)
        if not m:
            continue
        name, classification = m.group(1).strip(), m.group(2).strip()
        if name in ("mechanism", "act") or not classification:
            continue
        out[name] = classification
    return out


def read_spec(rel_path):
    if rel_path in staged_all:
        rr = subprocess.run(["git", "show", ":" + rel_path],
                             capture_output=True, timeout=20, cwd=repo_root)
        if rr.returncode == 0:
            try:
                return rr.stdout.decode("utf-8")
            except UnicodeDecodeError:
                pass
    abs_path = os.path.join(repo_root, rel_path)
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None


boundary_text = read_spec("docs/specs/enforcement-boundary.md")
boundary_names = recorded_names(boundary_text) if boundary_text is not None else set()

missing = []
mismatches = []
for p in targets:
    name = os.path.basename(p)
    if name not in boundary_names:
        missing.append(f"{p}: no row in docs/specs/enforcement-boundary.md")

if hook_scripts:
    paths_text = read_spec("docs/specs/generated-paths.md")
    paths_names = recorded_names(paths_text) if paths_text is not None else set()
    paths_classifications = (
        recorded_classifications(paths_text) if paths_text is not None else {}
    )
    for p in hook_scripts:
        name = os.path.basename(p)
        if name not in paths_names:
            missing.append(f"{p}: no row in docs/specs/generated-paths.md")
            continue
        # issue #839: existence alone (above) does not catch a row that
        # exists but is classified wrong (the incident this guard missed) --
        # derive write-call/issue-placeholder presence from this hook's own
        # staged text and compare against its recorded classification, same
        # bounded scope as the presence check (only this commit's own
        # newly-staged hook_scripts, never the whole directory).
        source_text = read_spec(p)
        if source_text is None:
            continue
        classification = paths_classifications.get(name, "")
        has_write = bool(_WRITE_CALL_RE.search(source_text))
        if not has_write:
            if classification != "n/a":
                mismatches.append(
                    f"{p}: recorded '{classification}' in "
                    "docs/specs/generated-paths.md but has no write call in "
                    "its own staged text (expected n/a)"
                )
        elif classification == "collision-risk" or classification not in (
            "out-of-tree", "issue-scoped",
        ):
            mismatches.append(
                f"{p}: recorded '{classification}' in "
                "docs/specs/generated-paths.md, which is not out-of-tree/"
                "issue-scoped"
            )
        elif classification == "issue-scoped" and not _ISSUE_PLACEHOLDER_RE.search(
            source_text
        ):
            mismatches.append(
                f"{p}: recorded issue-scoped in docs/specs/generated-paths.md "
                "but no issue-number placeholder found in its own staged text"
            )

if missing or mismatches:
    parts = []
    if missing:
        parts.append(
            "newly-added gate/hook module(s) missing a spec registration row "
            "(issue #441/#684):\n" + "\n".join(missing)
        )
    if mismatches:
        parts.append(
            "newly-added hook script(s) with a classification mismatch in "
            "docs/specs/generated-paths.md (issue #839):\n" + "\n".join(mismatches)
        )
    parts.append(
        "Fix the row in the same commit (docs/specs/enforcement-boundary.md, "
        "and for a hook script also docs/specs/generated-paths.md), then "
        "retry the commit."
    )
    deny("\n".join(parts))
PY

GRG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
