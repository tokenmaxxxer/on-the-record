#!/usr/bin/env bash
# PostToolUse: amendment channel (issue #3129). Registered unmatched (all
# tools) so it fires on every tool call -- the only high-frequency
# in-session channel a headless spawned worker has, since UserPromptSubmit
# (directive.sh) is a one-shot for it.
#
# All logic lives in amendment_channel.py, which never calls `gh` (no
# network round trip on the hot path) and never raises (see its module
# docstring). This wrapper's only job is to hand it the payload and get
# out of the way -- observability class: its absence loses the mid-flight
# correction signal, it enforces no rule and blocks nothing.
#
# Kill switch: ORCHESTRATE_OFF=1, same convention as the other
# orchestrate-machinery hooks in this directory.
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
command -v python3 >/dev/null 2>&1 || exit 0

python3 "$DIR/amendment_channel.py"
exit 0
