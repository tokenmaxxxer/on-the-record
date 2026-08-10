---
code_under_review: HEAD
type: feature
breaking: false
verdict: landed
loop_state: landed
---

# Phase-2 implementation record — issue #597

## What was done

Added a sixth firing condition to `on-the-record/hooks/delegated-judgment-gate.sh`
per `docs/issue-597/proposals/implementation.md`: three new `PreToolUse`
dispatch arms detect `gh pr merge <ref>`, `gh issue reopen <n>`, and
`gh issue close <n>` Bash commands and post a four-element framing
snapshot (`Resolved problem` / `Prior cost` / `Newly possible` /
`Still broken`) as an issue comment, using the exact
`## Framing snapshot — <transition> (<issue-#> / <PR-# if applicable>)`
header from `docs/issue-597/proposals/architecture.md` section 3.

New helpers, all inline (no `gates`/`record_lint` import, matching the
file's zero-install header):
- `resolve_citation(target, value)` — a citation resolves if it is a
  7-40 char hex sha, a real path under the target repo, or the
  no-prior-record baseline marker (`"<issue> (no prior record; issue
  body is the baseline)"`) — the last case per architecture.md section 5
  ("the mechanized resolvability check ... still has something real to
  verify").
- `gather_citable_records(target, issue)` — lists
  `docs/issue-<n>/reports/*.md` and `docs/issue-<n>/decisions/*.md`.
- `_field_and_citation` / `_first_heading_prose` — pull a
  `key: value` field or a heading's first prose paragraph out of a
  record, with an optional immediately-following `Citation: ...` line
  that overrides the default citation (the record's own path).
- `build_framing_snapshot(target, issue, transition, pr_ref)` —
  synthesizes all four elements from `gather_citable_records`' output
  (decision records for resolved/still-broken, role-record prose for
  prior-cost/newly-possible), or the explicit no-prior-record baseline
  when the issue has no records yet. Every element's citation is run
  through `resolve_citation` before the function returns a body; any
  failure returns `None`, and the dispatch loop then skips posting
  entirely (fail-closed, per architecture.md section 4).

Extended `on-the-record/hooks/test_delegated_judgment_gate.py` with five
tests: the no-prior-record baseline on `delivery-merged`, citation from a
role record's `## What was done` / `## What did not work` prose on
`issue-reopened`, citation from a decision record's `decision:` field on
`issue-closed`, and a fail-closed case where an embedded `Citation:`
line points at a nonexistent path.

## Why

Per `docs/issue-597/proposals/implementation.md`'s Rationale: `gh pr
merge` is detected directly (not via a `spawn.py` merge-signal, which
doesn't exist in merge-distinguishable form) to keep the entire write
set inside `on-the-record/hooks/`; the citation-resolvability check is
ported inline rather than importing `record_lint` from `gates/`, per
this file's own zero-install header constraint.

## Upstream / basis

`docs/issue-597/proposals/implementation.md`,
`docs/issue-597/proposals/architecture.md` sections 1-5.

## What did not work

- First test draft asserted the framing-snapshot body against the `gh`
  stub log, but the existing `_stub_gh` fixture only logs argv, not
  stdin — this hook posts multi-line bodies via `--body-file -`
  (stdin), so the body never appeared in the log and the assertions
  failed. Fixed by adding a second stub, `_stub_gh_with_stdin`, used
  only by the new framing-snapshot tests, that also appends stdin to the
  log; the original `_stub_gh` and its existing callers are untouched.

## Open findings

None blocking. The hunt below found a non-blocking design point (already
consistent with this file's own existing convention), not a defect.

## closed_checks

- check: warrant-hunter, stance "assume this guard goes silent when its
  own input is malformed — make it go silent", one probe, before
  phase-2 completion.
  code_sha: HEAD
  result: `gh pr merge` on a transition detected from
  `git rev-parse --abbrev-ref HEAD` silently no-ops when the current
  branch doesn't match `issue-<n>/<role>` (e.g. merging from `main`).
  This mirrors the existing `gh pr create` dispatch arm in the same
  file, which has the identical branch-match precondition and the same
  silent-exit-0 behavior on mismatch (see line ~84-86 of this file,
  pre-existing). The implementation proposal's Rationale explicitly
  chose this convention ("matching how `gh pr create` detection already
  works today"), so this is the accepted, in-scope behavior, not a
  regression — recorded here as a closed check per the hunt-cadence
  requirement, not carried forward as an open finding.
  Full hunt record: `docs/reports/2026-08-10-hunt-issue-597-implementation.md`
  (written by the dispatched hunter agent).

## Tests run

Run once, no failures to fix (11 pre-existing + 5 new):

```
$ python3 on-the-record/hooks/test_delegated_judgment_gate.py
  ok  t_all_five_issue_timeline_events_fire_across_reject_flow
  ok  t_auto_approve_single_role
  ok  t_auto_reject_with_finding_and_remediation
  ok  t_escalate_on_empty_corpus
  ok  t_escalate_on_no_quorum
  ok  t_framing_snapshot_baseline_on_delivery_merged_no_prior_records
  ok  t_framing_snapshot_fails_closed_on_unresolvable_citation
  ok  t_framing_snapshot_on_issue_closed_cites_decision_record
  ok  t_framing_snapshot_on_issue_reopened_cites_role_record
  ok  t_kill_switch_disables_the_gate
  ok  t_loop_bound_exhausted_escalates_at_round_4
  ok  t_multi_role_panel_quorum_and_unanimous_support_approves
  ok  t_no_import_gates_and_no_checkout_resolve_in_the_hook_source
  ok  t_no_trigger_no_side_effects
  ok  t_partial_support_with_no_opinion_escalates_not_approves
  ok  t_repeat_contradiction_from_same_role_escalates_before_round_3

16 passed
```

## Next steps

None for this delivery. Step 3 (conformance-review) remains open per
the issue's 실행 계획 — the orchestrator reopens #597 for that step once
this PR merges.

## Resolution path

Not applicable — no open findings.
