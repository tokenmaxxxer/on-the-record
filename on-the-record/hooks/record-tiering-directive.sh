#!/usr/bin/env bash
# UserPromptSubmit: was record-tiering-guard.sh's proactive statement of
# its self-declared-empty `## What did not work` shape (issue #760 —
# citation-informed section tiering,
# docs/issue-745/proposals/product-discovery.md Item 2 candidate 1).
#
# REVERTED (issue #745, PR #1509 measurement verdict = kill for the
# `reports/<role>.md` category — this directive's entire scope, since it
# only ever targeted docs/issue-<n>/reports/implementation.md): primary
# metric moved +19.1% instead of the pre-registered -30%, and the
# cross_issue_citation_rate guardrail breached by -15pp against a 5pp
# tolerance. Per the pre-registered revert condition, tiering for this
# category is removed. proposals/*.md and docs/reports/*.md carried no
# verdict and are unaffected — this directive never touched them anyway.
#
# Kept as an inert no-op file (not deleted) so hooks.json's reference and
# this history stay traceable; it now always exits 0 with no output.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

trap - EXIT
exit 0
