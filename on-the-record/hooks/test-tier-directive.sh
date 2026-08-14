#!/usr/bin/env bash
# UserPromptSubmit: observe-only directive for the test-tier contract
# convention (issue #1518) -- a target repo may declare
# `.on-the-record/test-tiers.json` (fast command + budget_seconds,
# optional slow command + trigger_change_classes) mirroring #1490's
# landed pytest-tier shape (fast default <=300s, slow keyed to a change
# class). This hook only reminds; it never blocks a tool call. Gating
# (refusing an over-budget silent run) is explicitly deferred per the
# issue's req 4 until the convention has >=1 real target-repo adoption.
# Fails open, kill switch ORCHESTRATE_OFF=1 (same convention as every
# other on-the-record directive hook).
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac

cat <<'TXT'
<test-tier-directive priority="observe-only">
TEST-TIER CONTRACT (issue #1518): before running a target repo's test
suite, check that repo's root for `.on-the-record/test-tiers.json`. If
present, run its `fast` command by default (budget: its
`budget_seconds`, default 300) and its `slow` command only when the
current diff matches a declared `trigger_change_classes` entry. If
absent, never run a silent full suite: measure the full run's
wall-clock cost, record that measurement plus a tiering-gap note in this
session's own record, and proceed -- the gap is surfaced, never quietly
absorbed. This directive is observe-only at this stage; it does not
refuse an over-budget run.
</test-tier-directive>
TXT

trap - EXIT
exit 0
