#!/usr/bin/env bash
# PreToolUse (Bash): issue #1130, docs/specs/role-invariant-coverage.md
# row 28 (performance-engineering, gate-now, unwired before this).
#
# Presence-check only: fires on a `git commit` invocation whose staged
# diff (git diff --cached --name-only, run against the target project's
# own working tree via tool_input.cwd/e.cwd — never this repo's own path,
# issue #1130 req#4) touches a hot-path file. Hot-path files are
# pattern-matched (**/*perf*, **/hot/**, **/hotpath/**) plus any
# additional glob the target project declares via PERF_HOT_PATH_GLOB
# (comma-separated, fnmatch syntax) — a project can widen what counts as
# hot without editing this hook. Denies the commit when the message (-m
# value(s), or a -F file's content) carries no `perf:` trailer citing a
# benchmark number or before/after latency.
#
# Mirrors merge-allow-gate.sh's Bash-command-shape handling (only a
# recognized `git commit` invocation is inspected; anything else falls
# through unreached) rather than a substring match on the whole command.
#
# Fails closed on genuine error (trap remaps non-0/2 exit to 2). Kill
# switch: ORCHESTRATE_OFF=1.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 2

IFS='' read -r -d '' GUARD <<'PY' || true
import fnmatch, json, os, re, shlex, subprocess, sys

def deny(msg):
    sys.stderr.write("perf-measurement-guard: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("PMG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str):
    sys.exit(0)
if not re.search(r"\bgit\s+commit\b", cmd):
    sys.exit(0)

if "`" in cmd or "$(" in cmd:
    sys.exit(0)  # substitution present — unreached, same fail-open posture as merge-allow-gate.sh

try:
    tokens = shlex.split(cmd, posix=True)
except ValueError:
    sys.exit(0)

if "commit" not in tokens or "git" not in tokens[: tokens.index("commit")]:
    sys.exit(0)

# --- extract the intended commit message -----------------------------------
message = None
i = 0
while i < len(tokens):
    tok = tokens[i]
    if tok in ("-m", "--message") and i + 1 < len(tokens):
        message = (message or "") + tokens[i + 1] + "\n"
        i += 2
        continue
    if tok in ("-F", "--file") and i + 1 < len(tokens):
        try:
            with open(tokens[i + 1], encoding="utf-8") as f:
                message = (message or "") + f.read()
        except OSError:
            pass
        i += 2
        continue
    i += 1

if message is None:
    sys.exit(0)  # no inline/-F message to inspect (e.g. editor-driven commit) — unreached

if re.search(r"^perf:\s*\S", message, re.MULTILINE):
    sys.exit(0)  # trailer present — nothing more to check

run_cwd = ti.get("cwd") if isinstance(ti.get("cwd"), str) else (e.get("cwd") or os.getcwd())

try:
    r = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=run_cwd, capture_output=True, text=True, timeout=20,
    )
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
if r.returncode != 0:
    sys.exit(0)

staged = [line for line in r.stdout.splitlines() if line.strip()]
if not staged:
    sys.exit(0)

extra_globs = [g for g in os.environ.get("PERF_HOT_PATH_GLOB", "").split(",") if g.strip()]
hot_globs = ["*perf*", "*/hot/*", "*/hotpath/*"] + extra_globs

hot_files = [
    f for f in staged
    if any(fnmatch.fnmatch(f, g) or fnmatch.fnmatch("/" + f, "*/" + g.lstrip("*/")) for g in hot_globs)
]
if not hot_files:
    sys.exit(0)

deny(
    "staged hot-path file(s) %s carry no `perf:` trailer citing a benchmark "
    "number or before/after latency (USE/RED method, brendangregg.com/usemethod.html)"
    % sorted(hot_files)
)
PY

PMG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
