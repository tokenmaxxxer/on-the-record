#!/usr/bin/env bash
# UserPromptSubmit: proactive statement of record-claim-guard.sh's
# claim-citation shape (issue #730) — states the same record_lint.py
# checks BEFORE a role session's first record write, instead of a role
# learning the shape only from the PreToolUse refusal.
#
# Generates its text from record_lint.py's own check-function docstrings
# (the same functions record-claim-guard.sh imports and calls) rather than
# a hand-typed prose copy, so a wording/logic change to a check does not
# need a second, driftable edit here — the issue's own named failure mode.
#
# Fires only for a spawned role session (CLAUDE_ROLE set) — the audience
# that actually hits the gate. hooks/directive.sh is the orchestrator's own
# directive and deliberately excludes role sessions already; this hook is
# role-session-scoped the other way around, mirroring that split rather
# than folding into it.
#
# Fails open (silent no-op, exit 0) when gates/record_lint.py cannot be
# resolved or imported — a missing proactive directive is not worth
# blocking the turn for; record-claim-guard.sh still enforces regardless.
# Kill switch: ORCHESTRATE_OFF=1 (matches record-claim-guard.sh).
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
[ -n "${CLAUDE_ROLE:-}" ] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
gates_dir=""
if [ -d "$script_dir/../gates" ]; then
    gates_dir="$(cd "$script_dir/../gates" && pwd)"
elif [ -d "$script_dir/../../gates" ]; then
    gates_dir="$(cd "$script_dir/../../gates" && pwd)"
fi
[ -n "$gates_dir" ] || exit 0

RCG_GATES_DIR="$gates_dir" python3 - <<'PY' || exit 0
import os
import sys

gates_dir = os.environ.get("RCG_GATES_DIR") or ""
try:
    sys.path.insert(0, gates_dir)
    import record_lint
except ImportError:
    sys.exit(0)

# Same four checks, same order record-claim-guard.sh imports and calls
# them in (gates/record_lint.py's own lint_record() call order) — this
# list is the frozen contract with that hook, not a separate authoring
# decision.
CHECKS = [
    record_lint.unverifiable_reason_check,
    record_lint.checked_claim_reason_check,
    record_lint.bare_count_claim_check,
    record_lint.orphaned_path_reference_check,
]


def rule_text(fn):
    # Docstrings wrap across source lines mid-sentence — join on
    # whitespace so the printed rule isn't cut off mid-word.
    doc = fn.__doc__ or ""
    joined = " ".join(doc.split())
    return joined if joined else fn.__name__


print("<record-claim-citation-directive>")
print("This session's own docs/issue-*/reports/** writes are checked by "
      "record-claim-guard.sh (on-the-record/gates/record_lint.py) for this "
      "claim-citation shape. State it right the first time, not after a "
      "refusal:")
print()
for i, fn in enumerate(CHECKS, 1):
    print(f"{i}. {fn.__name__}: {rule_text(fn)}")
print()
print("Examples: a bare count needs a code fence or a `derived: ...` tag "
      "immediately after it on the same line; an `unverifiable:` or "
      "`checked: ... — result: unverifiable` line needs a reason after "
      "it; a backtick-quoted path must resolve in the working tree.")
print("</record-claim-citation-directive>")
PY
