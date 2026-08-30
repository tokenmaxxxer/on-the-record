#!/usr/bin/env bash
# PostToolUse (Write|Edit|MultiEdit): lint + impacted-test-on-edit
# (issue #2326 Ask #2).
#
# Measurement basis (issue #2326, round 3 -- docs/issue-2326/reports/
# diagnose-first-71f82584.md): rework fraction re-derived on the live
# $MUSTER_WORKSPACE_ROOT session-log corpus (see that record for the
# exact command and number -- the earlier 4.5% figure's source corpus
# was an ephemeral /tmp directory that no longer exists). Round 4
# (docs/issue-2326/reports/silent-failure-audit+diagnose-first-0f11c1bf.md)
# re-derived it again and found it swings 1.1%-6.0% on +/-2 of 17 corpus
# files -- treat that as an interval, not a point estimate. This hook
# shortens the fail -> re-edit rework loop by injecting the failure
# signal (a syntax error, or a failing impacted test) into the very
# next turn's additionalContext, instead of the agent discovering the
# same failure several turns later by running tests itself.
#
# Docs-only edits are the acceptance's stated empty state: zero added
# latency, so the skip check below is pure bash string/pattern
# matching against the raw payload text -- no subprocess of any kind
# (not even `cat`/`grep`/`sed`), before python3 or any lint/test tool
# is ever invoked. It is a NON-authoritative pre-filter restricted to
# well-known non-code extensions only (`.md`/`.txt`/`.rst`) -- it does
# not attempt to classify a bare `docs/*` prefix, because that
# requires resolving symlinks to be safe (round 4 finding: a
# `docs/live_spawn.py -> ../spawn.py` symlink matches a `docs/*` glob
# on the raw string while actually pointing at real code) and bash
# cannot resolve symlinks without spawning a subprocess, which would
# defeat the point of this fast path. Every path this fast path does
# not skip -- including every bare `docs/*` path -- falls through to
# python's authoritative, realpath-resolved check below.
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
# item.
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
# subprocess.run(..., timeout=<remaining budget>) call. Round 3 shipped
# this as a single-invocation timing claim; round 4's independent
# verification found it breaks under this hook's own actual deployment
# shape (fires on every edit, fleet-wide -- concurrent invocations
# against the same repo contend for the same CPU): 3 of 8 concurrent
# runs against the same edit hit the outer budget, and the pre-round-4
# behavior discarded whatever partial pytest output already existed at
# that point, replacing it with a bare "budget exceeded, skipped"
# message -- losing the fact that real, already-confirmed test
# failures were sitting in that discarded output. Round 4 fixes this
# two ways, neither of which is a bigger timeout (a bigger timeout only
# raises the concurrency level at which the same silent loss recurs):
#
#   1. Concurrency-aware serialization: a best-effort, non-blocking
#      advisory lock (flock) scoped to the repo root serializes the
#      CPU-heavy test step across concurrent invocations against the
#      SAME repo, so N concurrent edits queue instead of all thrashing
#      the same CPU at once and degrading each other's wall-clock. This
#      reduces how often the budget is hit at all; it does not claim to
#      eliminate it at arbitrarily high concurrency, which is why (2)
#      exists as the actual correctness guarantee.
#   2. Never discard evidence, never claim a verdict that was not
#      computed: pytest is invoked with `-v` (not `-q`) and
#      PYTHONUNBUFFERED=1, so each test item's PASSED/FAILED/ERROR line
#      is flushed to the output capture file as soon as that item
#      finishes -- not deferred to an end-of-run summary that a
#      mid-run kill would erase. On a timeout, that partial output is
#      read (never discarded) and scanned for already-confirmed
#      failures; if any are found, they are reported explicitly as
#      "budget exceeded mid-run -- N test(s) ALREADY CONFIRMED FAILING
#      before the timeout". If none are found (or none can be
#      recovered), the report says so explicitly -- "budget exceeded
#      ... verdict INCOMPLETE (not verified clean)" -- which can never
#      be mistaken for silence or for a clean pass: this hook's only
#      other terminal state is emitting nothing at all on a run that
#      actually completed clean, and every budget-exceeded path always
#      emits non-empty text.
#
# If the budget is exhausted before the test step starts at all
# (including a budget of 0, or lint alone consuming it), the test step
# is skipped and this is reported the same explicit, non-silent way.
# The per-file timeout is a second, independent bound nested inside
# the combined one: it stops one item from consuming the whole budget
# by itself, but the combined budget still governs the invocation as a
# whole.
#
# FAILS OPEN on any missing tool (`python3`, `bash`), malformed JSON
# payload, permission error, or path-resolution failure -- same
# `trap 'exit 0' EXIT` posture as retry-loop-bound.sh. PostToolUse
# cannot deny a tool call in this harness; this hook only ever adds
# `hookSpecificOutput.additionalContext` on FAILURE (lint or impacted
# test failed, or budget exceeded) and is silent on success -- it must
# never be the reason a turn fails or hangs. The repo-root walk checks
# for `.git` existing at all (file or directory), not just a
# directory, so it also recognizes a `git worktree` checkout's `.git`
# file, not only a primary clone's `.git` directory (round 4 finding:
# the directory-only check silently zeroed out impacted-test selection
# when a worktree sat nested under an unrelated ancestor repo). If the
# harness's own timeout plugin cannot be imported (e.g. moved or
# deleted), that is reported as a distinct "harness internal error",
# not folded into the generic "impacted test failed" text a real
# broken test would produce.
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
# Narrow and extension-only on purpose (see header comment): this only
# ever skips on a well-known non-code suffix, never on a bare `docs/*`
# prefix, so it cannot be fooled by a symlink whose literal path looks
# docs-shaped but resolves elsewhere. The real (authoritative)
# file_path extraction and symlink resolution happens in the python
# body below, which is reached for every path this does not skip.
_fp_guess=""
if [[ "$PAYLOAD" =~ \"file_path\"[[:space:]]*:[[:space:]]*\"([^\"]*)\" ]]; then
    _fp_guess="${BASH_REMATCH[1]}"
elif [[ "$PAYLOAD" =~ \"path\"[[:space:]]*:[[:space:]]*\"([^\"]*)\" ]]; then
    _fp_guess="${BASH_REMATCH[1]}"
fi

case "$_fp_guess" in
    *.md|*.txt|*.rst)
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
import fcntl
import hashlib
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
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
cwd = payload.get("cwd") or os.getcwd()
abs_path = norm if posixpath.isabs(norm) else posixpath.normpath(
    posixpath.join(cwd, norm))

# authoritative docs-only classification: resolve symlinks BEFORE
# checking extension or directory shape, not after -- a symlink whose
# literal path looks docs-shaped (or vice versa) is classified by
# where it actually points, never by the string used to reach it
# (issue #2326 round 4: a `docs/live_spawn.py -> ../spawn.py` symlink
# defeated both this check and the bash fast path above when both
# matched on the unresolved string). This resolves the path rather
# than adding another string spelling to check.
try:
    real_path = os.path.realpath(abs_path)
except (OSError, ValueError):
    # cannot resolve (e.g. an embedded NUL) -- fail toward running the
    # check, never toward silently exempting an unresolvable path
    real_path = abs_path

ext = posixpath.splitext(real_path)[1].lower()
if ext in (".md", ".txt", ".rst"):
    sys.exit(0)
real_parts = [p for p in real_path.split("/") if p]
if "docs" in real_parts[:-1]:
    sys.exit(0)

root = None
probe = posixpath.dirname(real_path)
while probe and probe != "/":
    # `os.path.exists`, not `os.path.isdir`: a `git worktree` checkout's
    # `.git` is a file (containing `gitdir: <path>`), not a directory
    # (issue #2326 round 4 finding -- the directory-only check silently
    # zeroed out impacted-test selection under a worktree nested inside
    # an unrelated ancestor repo).
    if os.path.exists(posixpath.join(probe, ".git")):
        root = probe
        break
    probe = posixpath.dirname(probe)
if root is None:
    root = cwd

rel = os.path.relpath(real_path, root).replace(os.sep, "/")

failures = []
budget_hit = False


def _run(args, cwd_arg=None, env_extra=None):
    """Bounded by the remaining combined budget. Returns (ok, out) --
    ok is True/False for a run that actually completed, None if the
    combined budget ran out first. `out` is the captured output either
    way: on a timeout the subprocess is killed, but whatever it already
    wrote to the capture file before the kill is still read back and
    returned, never discarded (issue #2326 round 4 -- the previous
    version returned (None, None) on timeout, throwing away partial
    pytest output that could already contain real, confirmed
    failures).

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
        return None, ""
    env = None
    if env_extra:
        env = dict(os.environ)
        env.update(env_extra)
    with tempfile.TemporaryFile() as out_f:
        proc = None
        pgid = None
        timed_out = False
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
            timed_out = True
        except OSError:
            # missing tool / permission error -- fail open for this step
            return True, ""
        finally:
            _killpg(pgid)
        out_f.seek(0)
        out = out_f.read().decode("utf-8", "replace")
    if timed_out:
        return None, out
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


def _acquire_repo_lock(root_dir, deadline):
    """Best-effort mutual exclusion on the CPU-heavy test step, scoped
    to one repo root. Reduces (does not claim to eliminate) the CPU-
    contention-induced budget exhaustion issue #2326 round 4 traced:
    without it, N concurrent hook invocations against the same repo
    all fight for the same CPU at once and each one's wall-clock
    degrades together; with it, they queue instead, each still bounded
    by its own remaining budget. Returns (fd, timed_out):

    - locking infrastructure unavailable (e.g. no writable temp dir):
      (None, False) -- fail open, caller proceeds without
      serialization, exactly like today.
    - lock acquired: (fd, False) -- caller must release it.
    - deadline reached while waiting for another invocation to finish:
      (None, True) -- caller treats this exactly like any other
      budget-exceeded case (never silently proceeds, never silently
      gives up).
    """
    try:
        lock_dir = os.path.join(
            tempfile.gettempdir(), "otr-lint-test-on-edit-locks")
        os.makedirs(lock_dir, exist_ok=True)
        digest = hashlib.sha1(
            root_dir.encode("utf-8", "replace")).hexdigest()[:16]
        lock_path = os.path.join(lock_dir, digest + ".lock")
        fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    except OSError:
        return None, False
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd, False
        except OSError:
            pass
        if time.monotonic() >= deadline:
            try:
                os.close(fd)
            except OSError:
                pass
            return None, True
        time.sleep(min(0.05, max(0.0, deadline - time.monotonic())))


def _release_repo_lock(fd):
    if fd is None:
        return
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    except OSError:
        pass
    try:
        os.close(fd)
    except OSError:
        pass


_FAILED_LINE_RE = re.compile(r"^(\S+::\S+)\s+(FAILED|ERROR)\b")


def _extract_confirmed_failures(out):
    """pytest's own end-of-run summary only prints after the full item
    set completes -- useless once a run is killed mid-way -- but this
    hook always invokes pytest with `-v` (never `-q`) and
    PYTHONUNBUFFERED=1, so each item's own PASSED/FAILED/ERROR line is
    written to the capture file as soon as that item finishes, not
    deferred. Used only on the timeout path: a completed run already
    reports its failures via the normal ok=False path above."""
    found = []
    for line in out.splitlines():
        m = _FAILED_LINE_RE.match(line.strip())
        if m:
            found.append(m.group(1))
    return found


# --- lint step ----------------------------------------------------------
if ext == ".py":
    if shutil.which("python3"):
        ok, out = _run(["python3", "-m", "py_compile", real_path], root)
        if ok is False:
            failures.append("lint failed for %s:\n%s" % (rel, out))
elif ext == ".sh":
    if shutil.which("bash"):
        ok, out = _run(["bash", "-n", real_path], root)
        if ok is False:
            failures.append("lint failed for %s:\n%s" % (rel, out))
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
    stem = posixpath.splitext(posixpath.basename(real_path))[0]
    rel_parts = rel.split("/")

    candidates = []
    is_own_test = (
        len(rel_parts) >= 2
        and rel_parts[0] in ("test", "tests")
        and rel_parts[-1].startswith("test_")
        and rel_parts[-1].endswith(".py")
    )
    if is_own_test:
        candidates.append(real_path)
    elif ext == ".py":
        candidates.extend(_find_impacted(stem, root))

    if candidates and shutil.which("python3"):
        pytest_args = [
            "python3", "-u", "-m", "pytest",
            "-p", "otr_lint_test_timeout_plugin",
            "-o", "addopts=",
            "-v",
        ] + candidates
        env_extra = {
            "OTR_LINT_TEST_PER_FILE_TIMEOUT_S": per_file_timeout_s,
            "PYTHONPATH": hook_dir + os.pathsep + os.environ.get(
                "PYTHONPATH", ""),
            "PYTHONUNBUFFERED": "1",
        }
        lock_fd, lock_timed_out = _acquire_repo_lock(root, _start + budget_s)
        if lock_timed_out:
            budget_hit = True
            ok, out = None, ""
        else:
            try:
                ok, out = _run(pytest_args, root, env_extra=env_extra)
            finally:
                _release_repo_lock(lock_fd)

        candidate_list = ", ".join(
            os.path.relpath(c, root) for c in candidates)
        if ok is False:
            if ("otr_lint_test_timeout_plugin" in out
                    and "ModuleNotFoundError" in out):
                # distinct from a real test failure: the harness's own
                # plugin could not be imported, so none of the
                # candidate tests actually ran (issue #2326 round 4
                # finding -- this used to render identically to N real
                # broken tests).
                failures.append(
                    "harness internal error (not a real test failure): "
                    "otr_lint_test_timeout_plugin could not be "
                    "imported -- impacted tests (%s) did not actually "
                    "run:\n%s" % (candidate_list, out))
            else:
                failures.append(
                    "impacted test failed (%s):\n%s"
                    % (candidate_list, out))
        elif ok is None:
            confirmed = _extract_confirmed_failures(out or "")
            if confirmed:
                failures.append(
                    "budget exceeded mid-run (%s) -- %d test(s) ALREADY "
                    "CONFIRMED FAILING before the timeout (scan "
                    "incomplete, more may be broken): %s"
                    % (candidate_list, len(confirmed),
                       ", ".join(confirmed)))
            # else: no evidence recovered either way -- falls through
            # to the explicit budget-exceeded/INCOMPLETE report below,
            # never a silent no-op.
    # no matching test file -- skipped silently, this is import-graph
    # selection on the edited module's stem, not full test-impact
    # analysis (e.g. it will not catch a test that reaches the edited
    # module only transitively through another module it imports)

if failures:
    _emit("\n\n".join(failures))
elif budget_hit:
    _emit(
        "budget exceeded (%ss) -- verdict INCOMPLETE, NOT verified clean: "
        "lint/test checks for %s did not finish in time"
        % (os.environ.get("OTR_LTE_BUDGET_S", "15"), rel))

sys.exit(0)
PY
rc=$?
trap - EXIT
exit "$rc"
