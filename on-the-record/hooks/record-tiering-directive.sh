#!/usr/bin/env bash
# UserPromptSubmit: states record-tiering-guard.sh's self-declared-empty
# shape for `## What did not work` PROACTIVELY, before the PreToolUse
# gate ever fires (issue #760 — citation-informed section tiering,
# docs/issue-745/proposals/product-discovery.md Item 2 candidate 1).
#
# Audience: a spawned ROLE session only (CLAUDE_ROLE set) — the
# orchestrator never writes docs/issue-*/reports/implementation.md
# itself, so it is never the audience for this shape. Mirrors
# record-claim-shape-directive.sh's/directive.sh's own CLAUDE_ROLE gate.
#
# Scope, narrowly: `docs/issue-<n>/reports/implementation.md`'s
# `## What did not work` section only — the one section
# docs/issue-745/reports/product-discovery/current-state.md measured at
# zero cross-issue citation (derived: grep -c against every H2 heading
# repo-wide, cross-checked against the citation script's citer list).
# No other section, and no other record file, is touched by this rule.
#
# Fails open: no CLAUDE_ROLE -> silent no-op, never blocks the turn.
# Kill switch: ORCHESTRATE_OFF=1.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ -n "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }

cat <<'TXT'
<record-tiering-directive>
record-tiering-guard.sh checks docs/issue-<n>/reports/implementation.md's
`## What did not work` section mechanically, not just as a norm (issue
#760):

When writing that section and nothing was actually undone/replaced and
no expectation actually failed during the build, write the section
body as the bare marker `None.` — no restated summary of what did go
to plan. Elaborate only when there is a real entry (something written
then undone, or an expectation that did not hold) — real content of
any length is never denied, only a padded "None ..." body is.
</record-tiering-directive>
TXT

trap - EXIT
exit 0
