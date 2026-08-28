#!/usr/bin/env bash
# PreToolUse (Bash): deny-before-effect gate on a spawned session's `git push`
# whose destination ref resolves to the repo's own default branch — issue
# #2617.
#
# Incident (issue #2617, self-disclosed in PR #2614's "What did not work"):
# a spawned session ran `git push origin HEAD:main` against the real
# remote. Git's own non-fast-forward rule rejected it — main happened to
# have advanced past the session's HEAD — but nothing in this plugin would
# have stopped a fast-forward push from landing outside the PR flow, past
# every merge gate (`grep -rln 'git push' on-the-record/hooks/*.sh`
# returned nothing before this file). This gate closes that: it does not
# make the push succeed or fail on git's own ancestry rule (that rule
# stays exactly as unreliable as it always was), it adds an independent,
# local, fail-closed check that never depends on it.
#
# Scope: spawned sessions only (`TOKENMAXXXER_SPAWNED` resolves non-empty via
# the same SessionStart-snapshot-first / live-env-var-fallback primitive
# gh-write-allow-gate.sh / heredoc-command-refusal-gate.sh already use).
# The orchestrator session (`spawn.py init --push`'s own `git push
# --set-upstream origin <branch>` in board.py, run against whatever branch
# the human operator is currently on — frequently the default branch
# itself, as part of legitimately bootstrapping a fresh board) is
# untouched by this gate entirely; it is a distinct, human-driven entry
# path this issue's "must not rely on remote branch protection" clause
# does not reach, and gating it would break board bootstrap. See the
# issue-2617 record for the disposition this design choice produces.
#
# Detection is two-tier, deliberately not one shlex-strict shape check
# (issue #824/#834's design, used by gh-write-allow-gate.sh) — that shape
# is right for a narrow ALLOW list, wrong here: a deny gate that only
# recognizes one tokenization shape lets every other shape bypass it
# silently, which is exactly the failure this issue exists to close.
# Instead:
#   1. cheap bash-level pre-filter: both substrings "git" and "push"
#      present anywhere in the raw command (issue #876/#866 precedent,
#      ported from gate-registration-guard.sh's git-commit detection —
#      a `\bgit\s+push\b`-shaped regex would itself be bypassed by
#      `git -c foo=bar push ...`, the same global-option-insertion class
#      #876 already found and fixed for `git commit`).
#   2. authoritative python-side check: the whole command is tokenized
#      (shlex, posix=True, punctuation_chars=True — same primitive as
#      gh-write-allow-gate.sh), split into `&&`/`;`/`|`/`||`-delimited
#      segments, and each segment independently checked for a `git push`
#      invocation (leading `NAME=value` env-assignment tokens and global
#      options — including `-c <key>=<val>` / `-C <dir>`, the same
#      value-taking-option class #876 covers — are skipped before the
#      subcommand-name comparison). A bare `\n` inside the command is
#      ALSO a segment boundary here, not ordinary whitespace (shlex's
#      default `punctuation_chars` set does not include it, so an
#      ordinary multi-line Bash-tool command like `true\ngit push
#      origin main` would otherwise fuse into one segment starting with
#      `true`, never recognized as a push at all — found live by this
#      issue's own before-landing warrant-hunter dispatch).
#
# Every resolution subprocess call (current branch, configured remote,
# `ls-remote` default-branch lookup) runs with `cwd=` the PreToolUse
# payload's own `"cwd"` field (or an in-command `-C <dir>`, when
# present) — never this hook subprocess's own inherited cwd, which is
# not guaranteed to be the directory the pending command will actually
# run from (same primitive `gate-registration-guard.sh` already uses,
# for the same reason: this issue's own root-cause note is a `git push`
# that ran "from the wrong directory against the wrong repo" after an
# unchained `cd` — resolving against the wrong directory here would
# silently recreate that).
#
# For every recognized `git push` invocation, the destination branch
# name(s) are extracted from its refspec argument(s) (falling back to the
# current local branch when no refspec/remote is given, matching git's
# own push.default=simple behavior). A destination shaped like this
# system's own branches (`issue-<n>/<slug>`) is allowed with no
# network call at all — the fast, common-case path every legitimate
# session push takes. Only a destination NOT shaped that way (`main`,
# `master`, anything else, or `--all`/`--mirror`) triggers a
# `git ls-remote --symref <remote> HEAD` lookup of the remote's actual
# default branch (never a hardcoded literal — the issue's explicit "do
# not special-case main" requirement, and never the remote's branch
# protection API, which this system does not control in an arbitrary
# consumer repo). A destination equal to that resolved name is denied. A
# lookup that cannot resolve (offline, no `gh`/network reachability) also
# denies — fail CLOSED on ambiguity, same posture as pr-base-guard.sh's
# defaultBranchRef lookup failure, and the only posture that keeps this
# gate meaningful when the remote is briefly unreachable rather than
# silently waving the push through.
#
# Kill switch: ORCHESTRATE_OFF=1 (same convention as every other gate here).
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
# issue #2016 phase 2 / issue #876 precedent: a plain two-substring grep,
# never a `\bgit\s+push\b`-anchored regex — see the header note above for
# why an anchored shape is itself bypassable here.
{ grep -qF 'git' <<<"$payload" && grep -qF 'push' <<<"$payload"; } || exit 0
command -v python3 >/dev/null 2>&1 || exit 0

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, shlex, subprocess, sys

def deny(msg, hint):
    sys.stderr.write("git-push-guard: %s\n" % msg)
    sys.stderr.write("git-push-guard: instead: %s\n" % hint)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("GPUG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str) or not cmd.strip():
    sys.exit(0)

# --- identity: SessionStart snapshot first, live env var fallback ----------
# Identical primitive to heredoc-command-refusal-gate.sh: this gate is
# role-session-scoped, the mirror image of gh-write-allow-gate.sh's
# orchestrator-only scope.
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
if not spawned:
    sys.exit(0)  # orchestrator session — this gate's job is role-session containment only

# --- tokenize the whole command into operator-delimited segments -----------
# A literal newline is an unquoted statement separator in Bash (an
# ordinary multi-line Bash-tool command, `true\ngit push origin main`) —
# shlex's default punctuation_chars set ('();<>|&') does not include it,
# and shlex.shlex() always keeps '\n' in `self.whitespace`, so by default
# it is silently swallowed as plain whitespace instead of ending a
# segment: `git push` on line 2 would fuse into the same segment as line
# 1's unrelated leading token and never be recognized as a push at all
# (found live by this issue's before-landing warrant-hunter dispatch).
# Explicitly dropping '\n' from `self.whitespace` after construction (while
# it stays a punctuation_chars entry) routes it through the punctuation
# path instead — it becomes its own operator token when unquoted, and
# stays embedded verbatim inside a quoted token when it isn't (verified:
# a `-m "line1\nline2"` commit-message body is untouched).
try:
    _lexer = shlex.shlex(cmd, posix=True, punctuation_chars="();<>|&\n")
    _lexer.whitespace_split = True
    _lexer.whitespace = " \t\r"
    tokens = list(_lexer)
except ValueError:
    sys.exit(0)  # unbalanced quoting — unresolvable, not this gate's problem

OPERATOR_CHARS = set(_lexer.punctuation_chars) | {";"}


def _is_operator_token(tok):
    return bool(tok) and all(c in OPERATOR_CHARS for c in tok)


segments = [[]]
for t in tokens:
    if _is_operator_token(t):
        segments.append([])
    else:
        segments[-1].append(t)

_ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_VALUE_TAKING_GLOBAL_OPTS = {"-C", "-c"}


def _push_argv(seg):
    """Return (argv following `git push`, explicit `-C DIR` value or None)
    for this segment, or None if it is not a `git push` invocation. The
    `-C` value is surfaced (not just skipped) so callers resolve branch/
    remote state against the directory THIS command actually targets —
    same fix class as the issue's own root-cause note about a push
    running "from the wrong directory against the wrong repo"."""
    i = 0
    while i < len(seg) and _ASSIGNMENT_RE.match(seg[i]):
        i += 1  # leading NAME=value assignments (e.g. `FOO=bar git push ...`)
    if i >= len(seg) or seg[i] != "git":
        return None
    i += 1
    explicit_dir = None
    while i < len(seg) and seg[i].startswith("-"):
        if seg[i] == "-C" and i + 1 < len(seg):
            explicit_dir = seg[i + 1]  # last -C wins, matching real git
            i += 2
        elif seg[i] in _VALUE_TAKING_GLOBAL_OPTS and i + 1 < len(seg):
            i += 2
        else:
            i += 1
    if i < len(seg) and seg[i] == "push":
        return seg[i + 1:], explicit_dir
    return None


push_invocations = [r for seg in segments if (r := _push_argv(seg)) is not None]
if not push_invocations:
    sys.exit(0)

# --- resolution context: the harness-tracked actual cwd, not whatever cwd
# this hook subprocess happens to have inherited — the PreToolUse payload's
# own "cwd" field is the primitive gate-registration-guard.sh already uses
# for the identical reason (a hook process's inherited cwd is not
# guaranteed to be the directory the pending Bash command will run from).
_HARNESS_CWD = e.get("cwd") or os.getcwd()

# --- local, no-network helpers ----------------------------------------------
_ROLE_BRANCH_RE = re.compile(r"^issue-\d+/")


def _current_branch(cwd):
    try:
        r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                            capture_output=True, text=True, timeout=20, cwd=cwd)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    b = r.stdout.strip()
    return b if b and b != "HEAD" else None


def _push_argv_shape(argv):
    """(remote, refspecs, all_or_mirror) from a `git push` argv, positional-
    only (git push [options] [<repository> [<refspec>...]]) — flags with a
    separate value argument beyond --all/--mirror/--tags (e.g. -o, --repo)
    are skipped by their known arity so they never get misread as the
    remote/refspec positionals."""
    remote = None
    refspecs = []
    all_or_mirror = False
    _FLAGS_WITH_VALUE = {"-o", "--push-option", "--receive-pack", "--repo"}
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok in ("--all", "--mirror"):
            all_or_mirror = True
            i += 1
        elif tok in _FLAGS_WITH_VALUE:
            i += 2
        elif tok.startswith("-") and tok != "-":
            i += 1
        elif remote is None:
            remote = tok
            i += 1
        else:
            refspecs.append(tok)
            i += 1
    return remote, refspecs, all_or_mirror


def _refspec_dst(refspec, current_branch):
    ref = refspec[1:] if refspec.startswith("+") else refspec
    if ":" in ref:
        src, dst = ref.split(":", 1)
        if not dst:
            dst = src  # `:branch`-only forms already have a non-empty dst;
            # this covers the degenerate `branch:` (delete via empty dst)
    else:
        src = dst = ref
    if dst in ("HEAD", ""):
        dst = current_branch
    if dst and dst.startswith("refs/heads/"):
        dst = dst[len("refs/heads/"):]
    return dst


def _resolve_remote_name(explicit, current_branch, cwd):
    if explicit:
        return explicit
    if current_branch:
        try:
            r = subprocess.run(
                ["git", "config", "--get", "branch.%s.remote" % current_branch],
                capture_output=True, text=True, timeout=20, cwd=cwd)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
    return "origin"


def _resolve_default_branch(remote_name, cwd):
    """The remote's own advertised HEAD symref — never a hardcoded branch
    name, never the remote's branch-protection API. None on any lookup
    failure (offline, unknown remote, no `git`) — callers fail CLOSED."""
    try:
        r = subprocess.run(["git", "ls-remote", "--symref", remote_name, "HEAD"],
                            capture_output=True, text=True, timeout=20, cwd=cwd)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    m = re.search(r"^ref:\s+refs/heads/(\S+)\s+HEAD", r.stdout, re.MULTILINE)
    return m.group(1) if m else None


for argv, explicit_dir in push_invocations:
    # a relative `-C DIR` resolves against the directory the command runs
    # FROM (the harness cwd), never this hook subprocess's own inherited
    # cwd — same distinction the fix above makes for the no-`-C` case.
    if explicit_dir:
        cwd = explicit_dir if os.path.isabs(explicit_dir) else os.path.join(_HARNESS_CWD, explicit_dir)
    else:
        cwd = _HARNESS_CWD
    current_branch = _current_branch(cwd)
    remote, refspecs, all_or_mirror = _push_argv_shape(argv)

    if all_or_mirror:
        dsts = None  # every branch, definitionally including the default one
    elif refspecs:
        dsts = {d for d in (_refspec_dst(rs, current_branch) for rs in refspecs) if d}
    elif current_branch:
        dsts = {current_branch}
    else:
        dsts = set()  # detached HEAD, no refspec — git itself refuses this

    if dsts is not None and dsts and all(_ROLE_BRANCH_RE.match(d) for d in dsts):
        continue  # fast path: every destination is this system's own role-branch shape

    if dsts is not None and not dsts:
        continue  # nothing resolvable to push — not this gate's problem

    remote_name = _resolve_remote_name(remote, current_branch, cwd)
    default_branch = _resolve_default_branch(remote_name, cwd)
    if default_branch is None:
        deny(
            "cannot resolve the default branch of remote '%s' to verify "
            "this `git push` destination is safe — denying (fail-closed, "
            "issue #2617)." % remote_name,
            "push your own role branch instead: `git push -u origin HEAD` "
            "(current branch must be issue-<n>/<slug>-shaped), or retry "
            "once the remote is reachable.",
        )

    if all_or_mirror or default_branch in dsts:
        deny(
            "a role session may not push directly to the remote's default "
            "branch ('%s') — that moves it outside the PR flow, past every "
            "merge gate (issue #2617)." % default_branch,
            "push your own role branch and open a PR: "
            "`git push -u origin HEAD` (current branch must be "
            "issue-<n>/<slug>-shaped).",
        )

sys.exit(0)
PY

GPUG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
