#!/usr/bin/env bash
# PostToolUse (Write|Edit|MultiEdit): lint + impacted-test-on-edit
# (issue #2326 Ask #2).
#
# Measurement basis (issue #2326, round 3 -- docs/issue-2326/reports/
# diagnose-first-71f82584.md): rework fraction re-derived on the live
# $MUSTER_WORKSPACE_ROOT session-log corpus (see that record for the
# exact command and number -- the earlier 4.5% figure's source corpus
# was an ephemeral /tmp directory that no longer exists). This hook
# shortens the fail -> re-edit rework loop by injecting the failure
# signal (a syntax error, or a failing impacted test) into the very
# next turn's additionalContext, instead of the agent discovering the
# same failure several turns later by running tests itself.
#
# Docs-only edits are the acceptance's stated empty state: zero added
# latency, so the skip check below is pure bash string/pattern
# matching against the raw payload text -- no subprocess of any kind
# (not even `cat`/`grep`/`sed`), before python3 or any lint/test tool
# is ever invoked. Everything past that point (the real, authoritative
# parse) happens inside the python3 body.
#
# LINT: `.py` -> `python3 -m py_compile <file>` (fast syntax check; no
# ruff/flake8/etc. is configured anywhere in this repo, so this does
# not invent a dependency). `.sh` -> `bash -n <file>`. Any other
# extension: no lint step.
#
# IMPACTED TESTS -- import-graph selection, not 1:1 stem-equality: a
# 1:1 `test_<stem>.py` heuristic misses this repo's own descriptive
# multi-word test naming convention entirely for the traced rework
# episode (docs/issue-2326/reports/diagnose-first-56b99f15.md finding
# 1; docs/issue-2326/reports/adversarial-review-941d677c.md finding 1).
# Instead, every file under test/ and tests/ is grepped for a leading
# `import <stem>` / `from <stem> import` line naming the edited
# module's stem; every match is treated as impacted. This is accurate
# on the traced episode (selects all three real failing tests for a
# `spawn.py` edit) but, for a high-fan-in module like `spawn.py`
# (~70% of this repo's test files), the matched set can be dozens of
# files.
#
# PER-FILE TIMEOUT bounds the cost of that fan-in without excluding
# any file by name: OTR_LINT_TEST_PER_FILE_TIMEOUT_S (default 3)
# caps how long any single selected test item may run
# (otr_lint_test_timeout_plugin.py, SIGALRM-based) before it is
# abandoned (reported as a failure) and the run moves on to the next
# item. Measured directly against the traced episode's actual 36-file
# import-graph union (docs/issue-2326/reports/diagnose-first-
# 71f82584.md): the one file in that union carrying deliberate
# `time.sleep(30)` calls unrelated to the traced episode
# (test/test_bootstrap_signal_guard.py) is bounded to ~3s instead of
# running ~30s, and the full union completes in ~9-12s -- inside the
# combined budget below -- while still selecting, running, and
# reporting all three real failing tests from the episode. Excluding
# that file by name was rejected in the prior round specifically
# because a filename rule rots the moment the file is renamed; a time
# bound generalizes to any future outlier.
#
# The per-file timeout requires pytest-xdist's default parallel
# workers (`-n auto`, this repo's own pytest.ini) disabled for this
# invocation (`-o addopts=""`): SIGALRM only interrupts the process
# that receives it, and measurement showed the same bound far less
# effective under `-n auto` (one abandoned item still cost ~24s
# wall-clock, vs ~3-3.5s single-process) -- see diagnose-first-
# 71f82584.md for both timings side by side.
#
# BUDGET: OTR_LINT_TEST_BUDGET_S (default 15) is a combined wall-clock
# cap over the lint + test subprocess work, tracked in python via each
# subprocess.run(..., timeout=<remaining budget>) call (same primitive
# every other hook in this directory already uses for its own
# subprocess calls -- grep this file's siblings for `timeout=20` --
# rather than shelling out to a separate `timeout(1)` process, which
# would just be one more external-tool dependency for the same effect
# on an already-Linux-only harness). If the budget is exhausted before
# a step runs (including a budget of 0), that step is skipped and
# reported as "budget exceeded, skipped", never left to hang. The
# per-file timeout is a second, independent bound nested inside this
# one: it stops one item from consuming the whole combined budget by
# itself, but the combined budget still governs the invocation as a
# whole (e.g. an unusually large fan-in match set on a slower
# machine).
#
# FAILS OPEN on any missing tool (`python3`, `bash`), malformed JSON
# payload, permission error, or path-resolution failure -- same
# `trap 'exit 0' EXIT` posture as retry-loop-bound.sh. PostToolUse
# cannot deny a tool call in this harness; this hook only ever adds
# `hookSpecificOutput.additionalContext` on FAILURE (lint or impacted
# test failed, or budget exceeded) and is silent on success -- it must
# never be the reason a turn fails or hangs.
#
# No role-axis: this hook keys nothing on a role/skill identity (only
# ever on the file path it was handed), no state is persisted at all,
# and it never touches board-gate.sh, merge_gate.py, or anything under
# gates/ -- purely additive advisory behavior on top of the existing
# gates, per the retired-role-axis decision
# (docs/decisions/2026-08-25-retire-role-axis-staging.md).
trap 'exit 0' EXIT
set -uo pipefail

MODE="${1:-post}"
case "$MODE" in pre|post) ;; *) trap - EXIT; exit 0 ;; esac

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac

# --- read stdin via bash builtins only: no `cat`, no subprocess -------
PAYLOAD=""
IFS= read -r -d '' PAYLOAD
[ -n "$PAYLOAD" ] || { trap - EXIT; exit 0; }

# --- docs-only fast path: pure bash pattern matching, zero subprocess -
# Crude on purpose: this only needs to answer "is this obviously a
# docs path" before deciding whether to pay for python3 at all. The
# real (authoritative) file_path extraction happens in the python body
# below, which is reached for every non-docs-shaped path.
_fp_guess=""
if [[ "$PAYLOAD" =~ \"file_path\"[[:space:]]*:[[:space:]]*\"([^\"]*)\" ]]; then
    _fp_guess="${BASH_REMATCH[1]}"
elif [[ "$PAYLOAD" =~ \"path\"[[:space:]]*:[[:space:]]*\"([^\"]*)\" ]]; then
    _fp_guess="${BASH_REMATCH[1]}"
fi

case "$_fp_guess" in
    *..*)
        # a raw ".." segment can make an actual code path (e.g.
        # "docs/../spawn.py") match the docs/* / */docs/* globs below on
        # the UN-normalized string, even though it normalizes to a real
        # code file -- never fast-path skip on unnormalized input that
        # contains ".."; fall through to python's authoritative
        # posixpath.normpath-based check instead (issue #2326 round 3
        # hunt finding).
        ;;
    docs/*|*/docs/*|*.md|*.txt|*.rst)
        trap - EXIT; exit 0
        ;;
esac

command -v python3 >/dev/null 2>&1 || { trap - EXIT; exit 0; }

_hook_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

OTR_LTE_PAYLOAD="$PAYLOAD" \
    OTR_LTE_BUDGET_S="${OTR_LINT_TEST_BUDGET_S:-15}" \
    OTR_LTE_PER_FILE_TIMEOUT_S="${OTR_LINT_TEST_PER_FILE_TIMEOUT_S:-3}" \
    OTR_LTE_HOOK_DIR="$_hook_dir" \
    python3 - <<'PY'
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import time

payload_raw = os.environ.get("OTR_LTE_PAYLOAD", "")
try:
    budget_s = float(os.environ.get("OTR_LTE_BUDGET_S", "15"))
except ValueError:
    budget_s = 15.0
per_file_timeout_s = os.environ.get("OTR_LTE_PER_FILE_TIMEOUT_S", "3")
hook_dir = os.environ.get("OTR_LTE_HOOK_DIR", "")

_start = time.monotonic()


def _remaining():
    return budget_s - (time.monotonic() - _start)


def _emit(text):
    text = text.strip()
    if not text:
        sys.exit(0)
    # truncate to a few KB -- never dump megabytes of test output into
    # the next turn's context
    _CAP = 4000
    if len(text) > _CAP:
        text = text[:_CAP] + "\n... [truncated]"
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "lint-test-on-edit: " + text,
        }
    }
    sys.stdout.write(json.dumps(out))
    sys.exit(0)


try:
    payload = json.loads(payload_raw)
except ValueError:
    sys.exit(0)
if not isinstance(payload, dict):
    sys.exit(0)

tool_input = payload.get("tool_input")
if not isinstance(tool_input, dict):
    sys.exit(0)

fp = tool_input.get("file_path")
if not isinstance(fp, str) or not fp:
    fp = tool_input.get("path")
if not isinstance(fp, str) or not fp:
    sys.exit(0)

norm = posixpath.normpath(fp.replace("\\", "/"))
ext = posixpath.splitext(norm)[1].lower()

# defense-in-depth: the bash fast path above already skips this for
# the common shapes, but re-check here against the authoritative parse
# (e.g. a payload shape the bash regex missed) before spawning
# anything.
if ext in (".md", ".txt", ".rst"):
    sys.exit(0)
parts = [p for p in norm.split("/") if p]
if "docs" in parts[:-1] or (parts and parts[0] == "docs"):
    sys.exit(0)

cwd = payload.get("cwd") or os.getcwd()
abs_path = norm if posixpath.isabs(norm) else posixpath.normpath(
    posixpath.join(cwd, norm))

root = None
probe = posixpath.dirname(abs_path)
while probe and probe != "/":
    if os.path.isdir(posixpath.join(probe, ".git")):
        root = probe
        break
    probe = posixpath.dirname(probe)
if root is None:
    root = cwd

failures = []
budget_hit = False


def _run(args, cwd_arg=None, env_extra=None):
    """Bounded by the remaining combined budget. Returns (ok, output) --
    ok is False on nonzero exit OR on a timeout (the timeout case is
    also reported as a lint/test failure, distinct from the overall
    budget-exceeded report).

    Output is captured via temp files, not pipes, and the subprocess
    runs in its own process group (start_new_session=True), which is
    killed in full once we are done with it. A per-file-timed-out test
    item (otr_lint_test_timeout_plugin) can leave its own forked
    grandchild alive after the pytest process itself has moved on --
    that grandchild still holds the *inherited* stdout/stderr fds open,
    so a pipe-based `capture_output=True` blocks reading until the
    grandchild exits on its own (measured: up to the grandchild's full
    original sleep, regardless of our per-item bound). A real file has
    no such "wait for every writer to close" semantics, so this reads
    back immediately once our own subprocess.run call returns, and the
    process-group kill reclaims the orphan rather than leaving it to
    finish its sleep in the background.
    """
    global budget_hit
    remaining = _remaining()
    if remaining <= 0:
        budget_hit = True
        return None, None
    env = None
    if env_extra:
        env = dict(os.environ)
        env.update(env_extra)
    import tempfile
    with tempfile.TemporaryFile() as out_f:
        proc = None
        pgid = None
        try:
            proc = subprocess.Popen(
                args, cwd=cwd_arg, stdout=out_f, stderr=subprocess.STDOUT,
                env=env, start_new_session=True,
            )
            # start_new_session=True calls setsid() in the child, which
            # by definition makes its own pid the new process group id
            # -- read directly off proc.pid rather than os.getpgid(),
            # which would race the child's own setsid() call.
            pgid = proc.pid
            proc.wait(timeout=max(remaining, 0.01))
        except subprocess.TimeoutExpired:
            budget_hit = True
            _killpg(pgid)
            return None, None
        except OSError:
            # missing tool / permission error -- fail open for this step
            return True, ""
        finally:
            _killpg(pgid)
        out_f.seek(0)
        out = out_f.read().decode("utf-8", "replace")
    ok = proc.returncode == 0
    return ok, out


def _killpg(pgid):
    """Best-effort: reclaim the whole process group, including any
    grandchild the subprocess forked and left behind (e.g. a per-file-
    timed-out test's own forked child, which the pytest process itself
    does not wait for or kill). Fail-open on any error -- this is
    cleanup, never the reason the hook fails."""
    if pgid is None:
        return
    try:
        os.killpg(pgid, 9)
    except (OSError, ProcessLookupError):
        pass


# --- lint step ----------------------------------------------------------
if ext == ".py":
    if shutil.which("python3"):
        ok, out = _run(["python3", "-m", "py_compile", abs_path], root)
        if ok is False:
            failures.append("lint failed for %s:\n%s" % (norm, out))
elif ext == ".sh":
    if shutil.which("bash"):
        ok, out = _run(["bash", "-n", abs_path], root)
        if ok is False:
            failures.append("lint failed for %s:\n%s" % (norm, out))
# other extensions: no lint step -- not every language has tooling
# this repo can assume


# --- import-graph impacted-test selection --------------------------
_IMPORT_RE_TMPL = r"^\s*(?:import\s+{stem}\b|from\s+{stem}\s+import)"


def _find_impacted(stem, root_dir):
    pat = re.compile(_IMPORT_RE_TMPL.format(stem=re.escape(stem)))
    out = []
    for d in ("test", "tests"):
        dpath = posixpath.join(root_dir, d)
        if not os.path.isdir(dpath):
            continue
        for fn in sorted(os.listdir(dpath)):
            if not fn.endswith(".py"):
                continue
            fpath = posixpath.join(dpath, fn)
            try:
                with open(fpath, "r", errors="ignore") as f:
                    for line in f:
                        if pat.match(line):
                            out.append(fpath)
                            break
            except OSError:
                continue
    return out


# only run the test step if lint didn't already fail -- a file with a
# syntax error will fail its test for the same reason, and there is no
# budget-neutral reason to pay for both.
if not failures and not budget_hit:
    stem = posixpath.splitext(posixpath.basename(norm))[0]
    rel = os.path.relpath(abs_path, root).replace(os.sep, "/")
    rel_parts = rel.split("/")

    candidates = []
    is_own_test = (
        len(rel_parts) >= 2
        and rel_parts[0] in ("test", "tests")
        and rel_parts[-1].startswith("test_")
        and rel_parts[-1].endswith(".py")
    )
    if is_own_test:
        candidates.append(abs_path)
    elif ext == ".py":
        candidates.extend(_find_impacted(stem, root))

    if candidates and shutil.which("python3"):
        pytest_args = [
            "python3", "-m", "pytest",
            "-p", "otr_lint_test_timeout_plugin",
            "-o", "addopts=",
        ] + candidates + ["-q"]
        env_extra = {
            "OTR_LINT_TEST_PER_FILE_TIMEOUT_S": per_file_timeout_s,
            "PYTHONPATH": hook_dir + os.pathsep + os.environ.get(
                "PYTHONPATH", ""),
        }
        ok, out = _run(pytest_args, root, env_extra=env_extra)
        if ok is False:
            failures.append(
                "impacted test failed (%s):\n%s"
                % (", ".join(os.path.relpath(c, root) for c in candidates),
                   out))
    # no matching test file -- skipped silently, this is import-graph
    # selection on the edited module's stem, not full test-impact
    # analysis (e.g. it will not catch a test that reaches the edited
    # module only transitively through another module it imports)

if failures:
    _emit("\n\n".join(failures))
elif budget_hit:
    _emit("budget exceeded (%ss), skipped remaining lint/test checks for %s"
          % (os.environ.get("OTR_LTE_BUDGET_S", "15"), norm))

sys.exit(0)
PY
rc=$?
trap - EXIT
exit "$rc"
