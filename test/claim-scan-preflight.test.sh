#!/usr/bin/env bash
# Test for on-the-record/hooks/claim-scan-preflight.sh (issue #476 H1b).
# Invokes the hook as a subprocess with constructed JSON payloads on stdin
# and asserts on exit code / stdout / stderr, the same end-to-end shape
# test_pr_preflight.py's sibling shell tests use for this hook family.
set -uo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
hook="$repo_root/on-the-record/hooks/claim-scan-preflight.sh"

failures=0

run_hook() {
    # $1 = payload json, remaining env already exported by caller
    printf '%s' "$1" | "$hook"
}

case_ok() {
    local name="$1"
    echo "PASS: $name"
}

case_fail() {
    local name="$1"
    echo "FAIL: $name"
    failures=$((failures + 1))
}

payload() {
    local body="$1"
    python3 - "$body" <<'PY'
import json, sys
print(json.dumps({"tool_name": "Bash", "tool_input": {"command": "gh pr create --body \"" + sys.argv[1].replace('"', '\\"') + "\""}}))
PY
}

# --- case 1: claim with adjacent Repro: evidence -> exit 0, no additionalContext.
body1='Verified the fix.
Repro: python3 -m pytest test/foo.py'
out1="$(run_hook "$(payload "$body1")")"
rc1=$?
if [ "$rc1" -eq 0 ] && ! echo "$out1" | grep -q additionalContext; then
    case_ok "claim-with-adjacent-evidence exits 0 with no additionalContext"
else
    case_fail "claim-with-adjacent-evidence exits 0 with no additionalContext (rc=$rc1, out=$out1)"
fi

# --- case 2: claim with no evidence -> exit 0, additionalContext + mirrored stderr.
body2='I confirmed the change works as expected with no other detail nearby.'
stderr_file="$(mktemp)"
out2="$(run_hook "$(payload "$body2")" 2>"$stderr_file")"
rc2=$?
err2="$(cat "$stderr_file")"; rm -f "$stderr_file"
if [ "$rc2" -eq 0 ] && echo "$out2" | grep -q additionalContext && echo "$err2" | grep -q "confirmed"; then
    case_ok "claim-with-no-evidence exits 0 with additionalContext and mirrored stderr"
else
    case_fail "claim-with-no-evidence exits 0 with additionalContext and mirrored stderr (rc=$rc2, out=$out2, err=$err2)"
fi

# --- case 3: non gh-pr-create/edit command -> exit 0 silently.
payload3='{"tool_name": "Bash", "tool_input": {"command": "gh pr view 1"}}'
out3="$(printf '%s' "$payload3" | "$hook")"
rc3=$?
if [ "$rc3" -eq 0 ] && [ -z "$out3" ]; then
    case_ok "non gh pr create/edit command exits 0 silently"
else
    case_fail "non gh pr create/edit command exits 0 silently (rc=$rc3, out=$out3)"
fi

# --- case 4: ORCHESTRATE_OFF set -> exit 0 before any parsing, even with a
# payload that would otherwise trigger the positive-hit branch.
body4='Verified with no evidence at all nearby.'
set +o pipefail
out4="$(printf '%s' "$(payload "$body4")" | ORCHESTRATE_OFF=1 "$hook")"
rc4=$?
set -o pipefail
if [ "$rc4" -eq 0 ] && [ -z "$out4" ]; then
    case_ok "ORCHESTRATE_OFF set exits 0 before parsing"
else
    case_fail "ORCHESTRATE_OFF set exits 0 before parsing (rc=$rc4, out=$out4)"
fi

if [ "$failures" -ne 0 ]; then
    echo ""
    echo "$failures failure(s)"
    exit 1
fi
echo ""
echo "All checks passed"
exit 0
