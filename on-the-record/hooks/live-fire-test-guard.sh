#!/usr/bin/env bash
# PreToolUse (Bash): mandatory live-fire test for a newly-staged plugin
# gate/hook -- issue #914 step 2, mechanism (b) (highest-RICE candidate,
# closes the #909 orphan class at the point it would land).
#
# Sibling to gate-registration-guard.sh (#759/#909), one layer stricter:
# that guard checks a REGISTRATION row exists (docs/specs/
# enforcement-boundary.md, and for a hook script also hooks.json wiring
# and docs/specs/generated-paths.md). This guard checks the newly-staged
# gate/hook's own TEST actually fires it as a real lifecycle event with a
# crafted payload and asserts its allow/deny outcome -- a test existing is
# not the same as the capability having been proven to actually fire.
# absorbed-branch-recut-guard.sh (#909) had its own test file present and
# a doc row claiming it ships live, but no hooks.json entry -- nothing to
# pipe a crafted payload into. gate-registration-guard.sh now catches the
# missing hooks.json row; this guard additionally requires that the test
# file staged alongside a new hook script actually pipes a crafted
# lifecycle-event JSON payload into the script via stdin (the same
# subprocess+stdin convention test_gate_registration_guard.py already
# uses to drive gate-registration-guard.sh itself) and asserts at least
# two distinct exit-code outcomes (an allow path and a deny path) -- not
# merely that the script imports or runs without raising.
#
# Scope, per docs/issue-914/proposals/2026-08-12-standing-real-build-and-
# use-verification.md ("Artifact type 2"):
#   - on-the-record/hooks/*.sh (excluding hooks.json): live-fire test is
#     on-the-record/hooks/test_<slug>.py (slug = basename with `-` -> `_`,
#     minus `.sh`), staged in the same commit, containing a
#     subprocess.run/check_output/Popen call that pipes payload via
#     `input=`, references the script's own basename, and asserts >= 2
#     distinct `returncode == N` outcomes (allow vs deny).
#   - gates/*.py (excluding test_*.py/__init__.py) registered as a gate
#     (i.e. present in docs/specs/enforcement-boundary.md, staged or on
#     disk): live-fire test is gates/test_<stem>.py, staged in the same
#     commit, referencing the module and calling into it from >= 2
#     distinct test functions (gates/*.py modules are invoked in-process
#     by other gates/hooks, not via a subprocess stdin lifecycle payload,
#     so the bar here is "actually calls the module's checking function
#     and asserts an outcome from more than one crafted scenario" rather
#     than the stricter subprocess+stdin shape .sh scripts get).
#
# Escape hatches:
#   - A commit-message line `^Live-fire-N/A:\s*\S.*$` (non-empty reason)
#     exempts the whole commit -- for a gate/hook module with no
#     lifecycle-event surface to live-fire at all (e.g. a pure library
#     module sourced by other scripts, never itself a hooks.json row).
#   - A newly-staged file whose enforcement-boundary.md row is not yet
#     present at all is left to gate-registration-guard.sh to deny --
#     this guard only evaluates live-fire coverage for files that ARE (or
#     are being) registered as a gate/hook in the same staged tree, so
#     the two guards never race on the same missing-row condition.
#
# Fail-open: no python3/git, not a git repo, not a `git commit`
# invocation, unparseable payload, or no newly-staged mechanism file.
# Fail-closed (exit 2) only on a positive, evidence-backed determination
# that a newly-staged gate/hook has no live-fire test covering it.
#
# Kill switch: ORCHESTRATE_OFF=1 (same convention as the other hooks here).
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 0
command -v git >/dev/null 2>&1 || exit 0

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, shlex, subprocess, sys

def deny(msg):
    sys.stderr.write("live-fire-test-guard: %s\n" % msg)
    sys.stderr.write(
        "live-fire-test-guard: add a live-fire test that actually invokes "
        "the gate/hook as a real lifecycle event with a crafted payload and "
        "asserts its allow/deny outcome, or add a commit-message line "
        "'Live-fire-N/A: <reason>' if this module has no lifecycle-event "
        "surface to live-fire.\n"
    )
    sys.exit(2)

try:
    e = json.loads(os.environ.get("LFTG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str):
    sys.exit(0)

try:
    _lexer = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    _lexer.whitespace_split = True
    tokens = list(_lexer)
except ValueError:
    sys.exit(0)
if "git" not in tokens or "commit" not in tokens:
    sys.exit(0)
if "--no-verify" in tokens:
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

# --- commit message: same -m/-F/heredoc extraction gate-registration-guard
#     and test-authoring-invariant-guard.sh both already use -----------------
def _extract_message(cmd):
    m = re.search(
        r"-m(?:=|\s+)(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|\S+)", cmd
    )
    if m:
        raw = m.group(1)
        if len(raw) >= 2 and raw[0] in "\"'" and raw[-1] == raw[0]:
            raw = raw[1:-1]
        return raw
    heredoc = re.compile(
        r"-m\s+\"\$\(\s*cat\s+<<(-?)\s*(['\"]?)(\w+)\2\s*\n(.*?)\n(?(1)[ \t]*)\3[ \t]*\n?\)\"",
        re.DOTALL,
    )
    m = heredoc.search(cmd)
    if m:
        return m.group(4)
    m = re.search(r"-F(?:=|\s+)(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|\S+)", cmd)
    if m:
        raw = m.group(1)
        if len(raw) >= 2 and raw[0] in "\"'" and raw[-1] == raw[0]:
            raw = raw[1:-1]
        try:
            with open(raw, encoding="utf-8") as f:
                return f.read()
        except OSError:
            return None
    return None

message = _extract_message(cmd) or ""
if re.search(r"^Live-fire-N/A:\s*\S.*$", message, re.MULTILINE):
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
    if status == "A" or status[:1] in ("R", "C"):
        added.append(path)


def is_hook_script(p):
    if not p.startswith("on-the-record/hooks/") or "/" in p[len("on-the-record/hooks/"):]:
        return False
    name = os.path.basename(p)
    return name.endswith(".sh") and name != "hooks.json"


def is_gate_module(p):
    if not p.startswith("gates/") or "/" in p[len("gates/"):]:
        return False
    name = os.path.basename(p)
    if not name.endswith(".py") or name.startswith("test_") or name == "__init__.py":
        return False
    return True


hook_scripts = sorted(p for p in added if is_hook_script(p))
gate_modules = sorted(p for p in added if is_gate_module(p))
if not hook_scripts and not gate_modules:
    sys.exit(0)


def read_text(rel_path):
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


_ROW_RE = re.compile(r"^\|\s*`?([^`|]+?)`?\s*\|\s*(.+?)\s*\|", re.MULTILINE)
_SEP_ROW = re.compile(r"^\|[\s:-]+\|")


def recorded_names(text):
    out = set()
    for line in text.splitlines():
        if not line.startswith("|") or _SEP_ROW.match(line):
            continue
        m = _ROW_RE.match(line)
        if not m:
            continue
        name = m.group(1).strip()
        if name in ("mechanism", "act"):
            continue
        out.add(name)
    return out


boundary_text = read_text("docs/specs/enforcement-boundary.md")
boundary_names = recorded_names(boundary_text) if boundary_text is not None else None

missing = []

if hook_scripts:
    for p in hook_scripts:
        name = os.path.basename(p)
        if boundary_names is not None and name not in boundary_names:
            # gate-registration-guard.sh's business, not this guard's --
            # avoid double-denying the same missing-row condition.
            continue
        slug = re.sub(r"[^0-9a-zA-Z]+", "_", name[:-3]).strip("_")
        test_path = f"on-the-record/hooks/test_{slug}.py"
        test_text = read_text(test_path) if test_path in staged_all else None
        if test_text is None:
            missing.append(
                f"{p}: no live-fire test staged at {test_path} "
                "(issue #914 mechanism b)"
            )
            continue
        has_subprocess = bool(re.search(r"subprocess\.(run|check_output|Popen)", test_text))
        has_stdin = "input=" in test_text
        has_name_ref = name in test_text
        returncodes = set(re.findall(r"returncode\s*==\s*(\d+)", test_text))
        if not (has_subprocess and has_stdin and has_name_ref and len(returncodes) >= 2):
            missing.append(
                f"{p}: {test_path} exists but does not live-fire it (needs a "
                "subprocess call piping a crafted payload via `input=` into "
                f"'{name}' and asserting >= 2 distinct exit-code outcomes, "
                f"found {len(returncodes)})"
            )

if gate_modules:
    for p in gate_modules:
        name = os.path.basename(p)
        if boundary_names is not None and name not in boundary_names:
            continue
        stem = name[:-3]
        test_path = f"gates/test_{stem}.py"
        test_text = read_text(test_path) if test_path in staged_all else None
        if test_text is None:
            missing.append(
                f"{p}: no live-fire test staged at {test_path} "
                "(issue #914 mechanism b)"
            )
            continue
        has_ref = re.search(r"\b" + re.escape(stem) + r"\b", test_text) is not None
        has_call = re.search(r"\.[A-Za-z_][A-Za-z0-9_]*\(", test_text) is not None
        outcome_fns = len(re.findall(r"^def (?:t|test)_\w+", test_text, re.MULTILINE))
        if not (has_ref and has_call and outcome_fns >= 2):
            missing.append(
                f"{p}: {test_path} exists but does not live-fire it (needs "
                f"to import/call '{stem}' from >= 2 distinct test functions "
                f"asserting an outcome, found {outcome_fns} test function(s))"
            )

if missing:
    deny(
        "newly-staged gate/hook module(s) with no live-fire test proving "
        "the allow/deny/log outcome actually fires (issue #914, closes the "
        "#909 orphan class):\n" + "\n".join(missing)
    )
PY

LFTG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
