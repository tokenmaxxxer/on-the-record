#!/usr/bin/env bash
# issue #2146 — the single PreToolUse registration. All 20 PreToolUse
# gate checks (their .sh files remain on disk as the source of truth)
# run inside one python process: see pretooluse_dispatcher.py for the
# preserved per-gate contract (verdicts, refusal text, fail-open,
# exit-code table). This shim exists only because hooks.json commands
# are bash-invoked; it must never grow logic.
#
# python3 missing -> exit 2: the serial chain contained fail-closed
# gates (deliverable-guard.sh et al: `command -v python3 || exit 2`), so
# the chain-level outcome without python3 was a deny; preserved here.
set -uo pipefail
command -v python3 >/dev/null 2>&1 || exit 2
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/pretooluse_dispatcher.py"
