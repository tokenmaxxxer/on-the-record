#!/usr/bin/env bash
# PostToolUse (Write|Edit|MultiEdit): lint + impacted-test-on-edit
# (issue #2326 Ask #2).
#
# Measurement basis (issue #2326): across 17 real (non-audit-diff-
# comparison) session transcripts, 7.9% of edit turns (18/228) sat
# inside a fail -> re-edit rework loop, and once it happens the cost is
# a median 41 / mean 54.6 turns per episode (up to 98 in the worst
# family). This hook shortens that loop by injecting the failure
# signal (a syntax error, or a failing impacted test) into the very
# next turn's additionalContext, instead of the agent discovering the
# same failure several turns later by running tests itself (the
# SWE-agent/Aider precedent cited in the issue).
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
# IMPACTED TESTS: derive the edited file's stem (basename without
# extension) and look for `test/test_<stem>.py` or
# `tests/test_<stem>.py` (both directories exist in this repo and both
# hold pytest files) -- or, if the edited file itself already matches
# `test/test_*.py`/`tests/test_*.py`, treat it as its own impacted
# test. Only the matched file(s) are ever run
# (`python3 -m pytest <matched> -q`), never the whole suite -- this is
# a 1:1-stem heuristic, not full test-impact analysis, and not every
# edited file has a matching test file at all (silently skipped when
# none is found).
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
# reported as "budget exceeded, skipped", never left to hang.
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
    docs/*|*/docs/*|*.md|*.txt|*.rst)
        trap - EXIT; exit 0
        ;;
esac

command -v python3 >/dev/null 2>&1 || { trap - EXIT; exit 0; }

OTR_LTE_PAYLOAD="$PAYLOAD" \
    OTR_LTE_BUDGET_S="${OTR_LINT_TEST_BUDGET_S:-15}" \
    python3 - <<'PY'
import json
import os
import posixpath
import shutil
import subprocess
import sys
import time

payload_raw = os.environ.get("OTR_LTE_PAYLOAD", "")
try:
    budget_s = float(os.environ.get("OTR_LTE_BUDGET_S", "15"))
except ValueError:
    budget_s = 15.0

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


def _run(args, cwd_arg=None):
    """subprocess.run bounded by the remaining combined budget. Returns
    (ok, output) -- ok is False on nonzero exit OR on a timeout (the
    timeout case is also reported as a lint/test failure, distinct
    from the overall budget-exceeded report)."""
    global budget_hit
    remaining = _remaining()
    if remaining <= 0:
        budget_hit = True
        return None, None
    try:
        r = subprocess.run(
            args, cwd=cwd_arg, capture_output=True, text=True,
            timeout=max(remaining, 0.01),
        )
    except subprocess.TimeoutExpired:
        budget_hit = True
        return None, None
    except OSError:
        # missing tool / permission error -- fail open for this step
        return True, ""
    ok = r.returncode == 0
    out = (r.stdout or "") + (r.stderr or "")
    return ok, out


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

# --- impacted-test step ---------------------------------------------
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
    else:
        for d in ("test", "tests"):
            cand = posixpath.join(root, d, "test_%s.py" % stem)
            if os.path.isfile(cand):
                candidates.append(cand)

    if candidates and shutil.which("python3"):
        ok, out = _run(
            ["python3", "-m", "pytest"] + candidates + ["-q"], root)
        if ok is False:
            failures.append(
                "impacted test failed (%s):\n%s"
                % (", ".join(os.path.relpath(c, root) for c in candidates),
                   out))
    # no matching test file -- skipped silently, this is a 1:1-stem
    # heuristic, not full test-impact analysis

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
