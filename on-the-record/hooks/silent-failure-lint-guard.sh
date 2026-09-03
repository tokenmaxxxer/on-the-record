#!/usr/bin/env bash
# PreToolUse (Write|Edit|MultiEdit): deny-only, session-side, write-time
# mirror of scripts/lint/silent_failure.py's SF001 rule (issue #3228
# round 2).
#
# Round 1 (PR #3233) built the AST lint but wired it nowhere a session
# actually runs it against new code -- it only scans its own bundled
# fixtures plus one hardcoded regression target (independent
# verification, PR #3237). This closes that gap for the ONE rule safe
# to check from a write-time fragment alone: SF001 (a
# `subprocess.run`/`Popen`/`check_output`/`check_call` call with no
# `timeout=` keyword). This is genuinely ENFORCING, not advisory: a
# `PreToolUse` deny (exit 2) refuses the Write/Edit/MultiEdit before it
# lands, the same way `record-claim-guard.sh`/`credential-record-guard.sh`
# already deny a write in this dispatcher.
#
# Scope, and why it stops at SF001: `gates.py`'s own established
# convention for a `PreToolUse` content gate (`record-claim-guard.sh`'s
# docstring: "a PreToolUse hook only ever sees one write's resulting
# content, so this is a write-time approximation of the same intent, not
# a byte-identical port") is to scan Write's `content` / Edit's
# `new_string` / MultiEdit's `edits[].new_string` DIRECTLY -- never a
# full-file re-derivation. SF001 is purely call-node-local (no
# enclosing-function context needed), so that fragment-only scan is
# exact. SF002 (unchecked returncode ANYWHERE in the enclosing function)
# and SF003 (compared against every OTHER return in the same function)
# both need whole-function context this gate does not have; scanning a
# fragment alone for those would false-deny a legitimate author whose
# returncode check or distinguishing return sits outside the edited
# lines -- exactly the harm issue #3228's own "must not" clause forbids.
# Those two stay advisory-only, reported by `gates.silent_failure_new_
# findings` (gates/gates.py, wired into gates/ci.py's check()) against
# the PR diff's newly-added lines, where the full post-edit file is
# available to read. Only the `subprocess.<attr>(...)` dotted-attribute
# call shape is matched here (never a bare `run(...)`/`Popen(...)` name)
# -- recognizing that shape needs no import-tracking context the
# fragment might not carry, so it cannot mistake an unrelated function
# literally named `run`/`Popen` for a subprocess call the way a
# name-only match could.
#
# A fragment that does not parse standalone (common for an Edit/
# MultiEdit new_string: an indented statement or two with no enclosing
# `def` in the fragment itself) is retried dedented, then wrapped as a
# synthetic function body -- if none of the three parse, this gate skips
# that fragment rather than false-denying (best-effort, same posture as
# every other write-time content gate in this dispatcher: never guess a
# violation from unparseable text).
#
# A trailing `# silent-failure: allow <reason>` anywhere in the edit's
# own fragment exempts that whole fragment (coarser than
# `scripts/lint/silent_failure.py`'s own per-call-site marker, since
# this gate has no reliable per-fragment line numbering to scope it
# tighter -- the safe direction for a hard denial is to under- rather
# than over-block).
#
# Fails closed (trap remaps non-0/2 exit to 2), matching this plugin's
# house style. Kill switch: ORCHESTRATE_OFF=1.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 2

IFS='' read -r -d '' GUARD <<'PY' || true
import ast, json, os, sys, textwrap

def deny(msg):
    sys.stderr.write("silent-failure-lint-guard: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("SFLG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict):
    sys.exit(0)
if (e.get("tool_name") or "") not in ("Write", "Edit", "MultiEdit"):
    sys.exit(0)
ti = e.get("tool_input") or {}
if not isinstance(ti, dict):
    sys.exit(0)
p = ti.get("file_path")
if not isinstance(p, str) or not p.endswith(".py"):
    sys.exit(0)

content_parts = []
nc = ti.get("content")
if isinstance(nc, str):
    content_parts.append(nc)
ns = ti.get("new_string")
if isinstance(ns, str):
    content_parts.append(ns)
edits = ti.get("edits")
if isinstance(edits, list):
    for ed in edits:
        if isinstance(ed, dict) and isinstance(ed.get("new_string"), str):
            content_parts.append(ed["new_string"])

_ALLOW = "silent-failure: allow"
_ATTRS = ("run", "Popen", "check_output", "check_call")
bad_count = 0

for frag in content_parts:
    if "subprocess" not in frag or _ALLOW in frag:
        continue
    dedented = textwrap.dedent(frag)
    synthetic = "def _sf_synthetic():\n" + "\n".join(
        "    " + ln for ln in dedented.splitlines())
    tree = None
    for cand in (frag, dedented, synthetic):
        try:
            tree = ast.parse(cand)
            break
        except SyntaxError:
            continue
    if tree is None:
        continue
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_subproc = (
            isinstance(func, ast.Attribute) and func.attr in _ATTRS
            and isinstance(func.value, ast.Name) and func.value.id == "subprocess")
        if not is_subproc:
            continue
        if not any(kw.arg == "timeout" for kw in node.keywords):
            bad_count += 1

if bad_count:
    deny(
        "this write adds %d new subprocess.run/Popen/check_output/"
        "check_call call site(s) with no explicit timeout= keyword "
        "(issue #3228 SF001: a hung child process blocks forever instead "
        "of ever reporting it could not observe). Add timeout=<seconds> "
        "and handle subprocess.TimeoutExpired, or add a trailing "
        "'# silent-failure: allow <reason>' comment on the call's own "
        "line (or anywhere else in this edit) if a hang here is "
        "genuinely impossible. This is SF001 of "
        "scripts/lint/silent_failure.py's three-rule scan -- run "
        "`python3 scripts/lint/silent_failure.py %s` for the full "
        "SF001/SF002/SF003 result (SF002/SF003 need whole-function "
        "context this write-time check does not have)." % (bad_count, p))
sys.exit(0)
PY

SFLG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
