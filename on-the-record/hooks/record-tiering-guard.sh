#!/usr/bin/env bash
# PreToolUse (Write|Edit|MultiEdit): was a deny on a self-declared-empty
# `## What did not work` body padded beyond the bare marker (issue #760 —
# citation-informed section tiering,
# docs/issue-745/proposals/product-discovery.md Item 2 candidate 1).
#
# REVERTED (issue #745, PR #1509 measurement verdict = kill for the
# `reports/<role>.md` category — this guard's entire scope, since it only
# ever matched docs/issue-<n>/reports/implementation.md): primary metric
# moved +19.1% instead of the pre-registered -30%, and the
# cross_issue_citation_rate guardrail breached by -15pp against a 5pp
# tolerance. Per the pre-registered revert condition, tiering enforcement
# for this category is removed. proposals/*.md and docs/reports/*.md
# carried no verdict and are unaffected — this guard never matched them
# anyway.
#
# Kept as an inert no-op file (not deleted) so hooks.json's reference and
# this history stay traceable; it now always exits 0 without inspecting
# the payload.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

trap - EXIT
exit 0
