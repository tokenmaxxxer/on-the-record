#!/usr/bin/env bash
# Fail-open ledger wrapper (issue #2093).
#
# Every hooks.json registration runs through here.  This script execs the
# real hook with its original argv and its original stdin, re-emits the
# child's stdout, stderr and exit code UNCHANGED, and -- when the child
# failed open (exited nonzero-and-not-2, or sprayed a Traceback) -- appends
# one line to the fail-open ledger.
#
# Why a wrapper process and not a sourced preamble: a preamble cannot
# observe a crash it is running inside, and cannot see stderr after the
# fact.  The cost is one extra `bash` exec per hook invocation.
#
# Verdict-neutral by construction: the child's exit code is forwarded
# verbatim, and every ledger step is best-effort.  A wrapper that could
# change a verdict would be a worse defect than the one it records.
#
# usage: fail-open-wrapper.sh <hook-script> [args...]

set -uo pipefail

if [ "$#" -eq 0 ]; then
    # Nothing to wrap.  Non-blocking by the platform's own table.
    exit 0
fi

_wrapper_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd -P)" || _wrapper_dir=""
_hook_path="$1"
_hook_name="$(basename "$_hook_path" 2>/dev/null || printf '%s' "$_hook_path")"

_tmpdir="${TMPDIR:-/tmp}"
_in_file="$(mktemp "${_tmpdir%/}/otr-fow-in.XXXXXX" 2>/dev/null)" || _in_file=""
_err_file="$(mktemp "${_tmpdir%/}/otr-fow-err.XXXXXX" 2>/dev/null)" || _err_file=""

_cleanup() { [ -n "$_in_file" ] && rm -f "$_in_file"; [ -n "$_err_file" ] && rm -f "$_err_file"; return 0; }
trap _cleanup EXIT

if [ -n "$_in_file" ]; then
    cat >"$_in_file" 2>/dev/null || true
fi

rc=0
if [ -n "$_in_file" ] && [ -n "$_err_file" ]; then
    "$@" <"$_in_file" 2>"$_err_file"
    rc=$?
    cat "$_err_file" >&2 2>/dev/null || true
elif [ -n "$_in_file" ]; then
    "$@" <"$_in_file"
    rc=$?
else
    # No temp file available: degrade to a straight pass-through.  The
    # wrapper stops observing, it never stops the hook from running.
    "$@"
    rc=$?
fi

_failed_open=""
if [ "$rc" -ne 0 ] && [ "$rc" -ne 2 ]; then
    _failed_open="nonzero-exit"
elif [ -n "$_err_file" ] && grep -q 'Traceback (most recent call last)' "$_err_file" 2>/dev/null; then
    # Exit 0/2 with a traceback on stderr: the verdict may be sound but a
    # subprocess inside the hook crashed.  Still a fail-open to record.
    _failed_open="traceback"
fi

# issue #2962: invariant-injecting vs observability class, shell-builtins
# only (`case` is a bash builtin; no python3, no disk read/write) -- the
# step that surfaces a fail-open must not depend on the thing that just
# failed. Kept in sync with hook_classification.json by
# test_hook_classification.py, which cross-checks this list against that
# file's invariant-injecting entries rather than trusting a comment here.
# pretooluse-dispatcher.sh is deliberately absent: it never reaches this
# wrapper (fail-closed, unwrapped by design) so it can never match here.
_fallback_fired=0
if [ -n "$_failed_open" ]; then
    case "$_hook_name" in
        session-role-bind.sh|directive.sh|post-landing-obligation-gate.sh|stop-gate.sh|skill-verdict-guard.sh)
            _fallback_fired=1
            # Visible in-band degraded notice (issue #2962): a distinct,
            # unambiguous line -- not the raw traceback standing in for it
            # -- so a dead invariant-injecting hook stops reporting itself
            # as success. Printed via `printf` alone, before the
            # python3/disk-dependent ledger step below, so it fires even
            # when that step cannot.
            printf '[fail-open][DEGRADED] %s failed open (exit=%s, %s) -- this session is running WITHOUT the invariant(s) this hook injects/enforces.\n' \
                "$_hook_name" "$rc" "$_failed_open"
            ;;
        *) ;;
    esac
fi

if [ -n "$_failed_open" ]; then
    if command -v python3 >/dev/null 2>&1 && [ -n "$_wrapper_dir" ] \
       && [ -f "$_wrapper_dir/hook_ledger.py" ]; then
        OTR_FAIL_OPEN_INPUT="$([ -n "$_in_file" ] && cat "$_in_file" 2>/dev/null || true)" \
            python3 "$_wrapper_dir/hook_ledger.py" \
            "$_hook_name" "$rc" "$_failed_open" "$_fallback_fired" "$@" >/dev/null 2>&1 || true
    fi
fi

exit "$rc"
