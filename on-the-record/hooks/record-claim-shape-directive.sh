#!/usr/bin/env bash
# UserPromptSubmit: states record-claim-guard.sh's citation shape
# PROACTIVELY, before the PreToolUse gate ever fires (issue #730 —
# #726 audit row 9: every role learned this shape only from refusal,
# the single most frequent gate-refusal on 2026-08-11).
#
# Audience: a spawned ROLE session only (CLAUDE_ROLE set) — the
# orchestrator never writes docs/issue-*/reports/** itself, so it is
# never the audience for this shape. Mirrors directive.sh's inverse
# CLAUDE_ROLE gate.
#
# Generated, not hand-typed: the printed text is built at hook-run time
# from gates/record_lint.py's own check functions' docstrings — the
# same functions record-claim-guard.sh calls to enforce the shape — so
# a future change to the check logic's docstring changes what this
# directive states too, with no second copy to keep in sync (the
# drift the issue explicitly warns against).
#
# Fails open: no CLAUDE_ROLE, or record_lint.py not importable ->
# silent no-op, never blocks the turn. Kill switch: ORCHESTRATE_OFF=1.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ -n "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }
command -v python3 >/dev/null 2>&1 || { trap - EXIT; exit 0; }

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
gates_dir=""
if [ -d "$script_dir/../gates" ]; then
    gates_dir="$(cd "$script_dir/../gates" && pwd)"
elif [ -d "$script_dir/../../gates" ]; then
    gates_dir="$(cd "$script_dir/../../gates" && pwd)"
fi
if [ -z "$gates_dir" ]; then
    trap - EXIT
    exit 0
fi

RCSD_GATES_DIR="$gates_dir" python3 - <<'PY' || { trap - EXIT; exit 0; }
import os
import sys

gates_dir = os.environ.get("RCSD_GATES_DIR") or ""
sys.path.insert(0, gates_dir)
try:
    import record_lint
except ImportError:
    sys.exit(0)


def _first_line(fn):
    doc = (fn.__doc__ or "").strip()
    if not doc:
        return "(no docstring)"
    # Docstrings wrap across lines with indentation; collapse to one line.
    return " ".join(doc.split())


# before-landing hunt (issue #730, stance 0): a rename/refactor of any of
# these four record_lint attribute names must not silently kill the whole
# directive (indistinguishable from the intentional no-op paths above) —
# fall back to a visible notice instead of vanishing.
try:
    rules = [
        ("bare count/ratio claim (issue #333)", record_lint.bare_count_claim_check),
        ("`unverifiable:` line (issue #310)", record_lint.unverifiable_reason_check),
        ("`checked: ... — result: unverifiable` line (issue #331)",
         record_lint.checked_claim_reason_check),
        ("backtick-quoted path reference (issue #330)",
         record_lint.orphaned_path_reference_check),
        ("state/defect claim with no canonical source (issue #793)",
         record_lint.canonical_source_claim_check),
        ("outcome claim with no executed-live citation (issue #870)",
         record_lint.outcome_claim_citation_check),
        ("defect/root-cause claim with no grounded citation (issue #791)",
         record_lint.defect_claim_grounding_check),
    ]

    print("<record-claim-citation-directive>")
    print("record-claim-guard.sh (gates/record_lint.py) checks every write under")
    print("docs/issue-*/reports/** for this shape, in this order — cite correctly")
    print("the first time instead of learning it from a refusal:")
    print()
    for i, (label, fn) in enumerate(rules, 1):
        print(f"{i}. {label}: {_first_line(fn)}")
    print("</record-claim-citation-directive>")
except AttributeError as e:
    print("<record-claim-citation-directive>")
    print("record-claim-shape-directive.sh could not generate the citation")
    print(f"shape text from gates/record_lint.py ({e}) — record_lint.py's")
    print("check functions likely changed name/shape. record-claim-guard.sh")
    print("still enforces the shape even though this directive can't state it.")
    print("</record-claim-citation-directive>")
PY

trap - EXIT
exit 0
