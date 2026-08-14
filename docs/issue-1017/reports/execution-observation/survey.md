# Current-state survey — execution-observation on issue #1017

## Scope

Observed: role `implementation`, issue #1017, on branch `issue-1017/implementation`.

canonical: `gh issue view 1017 --comments` (read this session)
The comment thread traces, in order: a delegated-judgment escalation on the first candidate
PR; `[watch] ... PR https://github.com/tokenmaxxxer/on-the-record/pull/1020 opened`; `APPROVE
issue-1017/implementation`; then another delegated-judgment escalation on a later candidate PR.

canonical: `gh pr list --search "1017" --state all --json number,title,headRefName,state,mergedAt`
(read this session)
Head ref `issue-1017/implementation` carries PR #1020, titled `issue-1017 phase-1: requirement
linkage anchor proposal`, state MERGED.

canonical: `gh pr list --search "1017" --state all --json number,title,headRefName,state,mergedAt`
(read this session)
Head ref `issue-1017/implementation` also carries PR #1026, titled `issue-1017 phase-2:
requirement linkage anchor`, state MERGED.

canonical: `gh pr view 1026 --json body` (read this session)
PR #1026's body opens with `Closes #1017`.

## What was read (fresh-eyes ordering)

`gh pr diff 1026` (read this session, full diff) was read before
`docs/issue-1017/reports/implementation.md`'s own narrative. Diff hunks actually read: the new
`docs/issue-1017/reports/implementation.md`; the appended hunk in
`docs/issue-1017/reports/implementation/hunt-2026-08-12-requirement-linkage-anchor.md`
(before-landing warrant-hunt stance 1); the added row in `docs/specs/enforcement-boundary.md`;
the new `gates/requirement_linkage.py`; the appended linkage-case hunk in
`gates/test_requirement_digest.py`; the new `gates/test_requirement_linkage.py`; the `spawn.py`
hunks for `require_requirement_linkage()`, its `main()` call site, `requirement_drift()`'s
rewritten next-action block, and `_spawn_one`'s req-line threading.

canonical: `git show e884e45a22f0bdb98031906e4758f3a420ff4775 --stat` (executed this session,
mode: command)
Commit `e884e45a` carries both `docs/issue-1017/proposals/2026-08-12-requirement-linkage-anchor.md`
and `docs/issue-1017/reports/implementation/survey.md` in the same commit, survey listed after
the proposal in the diffstat's file order.

canonical: `git show e884e45a22f0bdb98031906e4758f3a420ff4775:docs/issue-1017/reports/implementation/survey.md`
(executed this session, mode: command, full file read)
That survey's content is descriptive current-state prose about `requirement_digest.py`,
`requirement_drift()`, and `acceptance_gate.py`'s existing shape — no proposal-shaped or
verdict-shaped language appears in it.

canonical: `docs/specs/approvers.md` (read this session, full file)
Two accounts are listed: `JiwonJung94`, `jjongkwann`.

canonical: `gh pr view 1020 --json author` and `gh pr view 1026 --json author` (both read this
session)
Both PRs share author login `JiwonJung94`, matching the `APPROVE issue-1017/implementation`
comment's author — single-account mode is the applicable approval path for judging that
comment, not two-account review-Approve mode.

## Independent re-run of the phase-2 record's cited commands

canonical: `python3 gates/test_requirement_digest.py` (executed this session, mode: command, on
`main` HEAD)
```
$ python3 gates/test_requirement_digest.py
PASS t_check_empty_registry_documented_empty_state
PASS t_check_flags_drift_after_hand_edit
PASS t_check_flags_missing_digest
PASS t_check_no_registry_passes_nothing_to_check
PASS t_check_passes_after_update
PASS t_linkage_cited_ids_dedupes_preserving_order
PASS t_linkage_flags_untagged_body_with_no_requirement_citation
PASS t_linkage_passes_body_citing_northpole_req_form
PASS t_linkage_passes_body_citing_real_requirement_id
PASS t_linkage_passes_infrastructure_tagged_body
PASS t_parse_extracts_all_required_fields
PASS t_render_drops_stale_and_keeps_live
PASS t_render_line_count_is_o_of_live_requirement_count_not_record_count
PASS t_update_rewrites_status_to_stale_when_check_path_missing
```

canonical: `python3 gates/test_requirement_linkage.py` (executed this session, mode: command,
on `main` HEAD)
```
$ python3 gates/test_requirement_linkage.py
ok - t_check_issue_body_allows_body_citing_a_requirement_id
ok - t_check_issue_body_allows_infrastructure_tagged_body
ok - t_check_issue_body_denies_body_with_no_requirement_citation
3/3 passed
```

canonical: the two fenced re-runs directly above (executed this session, mode: command)
Compared line-by-line against `docs/issue-1017/reports/implementation.md`'s own pasted output
(read this session, full file), the two outputs match verbatim.

## What the phase-2 record (implementation.md) itself states

canonical: `docs/issue-1017/reports/implementation.md` frontmatter (read this session, full
file)
```
verdict: pass
loop_state: landed
```

canonical: `docs/issue-1017/reports/implementation.md`, section `## What did not work` (read
this session)
It names gate-required additions outside the frozen write set —
`gates/test_requirement_linkage.py` (live-fire-test-guard.sh), `docs/specs/enforcement-boundary.md`
(gate-registration-guard.sh), and a fix to `require_requirement_linkage`'s "existing issue"
test — and cites `docs/issue-1017/reports/implementation/hunt-2026-08-12-requirement-linkage-anchor.md`
as the source of the last one.

canonical: `docs/issue-1017/reports/implementation.md`, section `## Open findings` (read this
session)
It marks the hunt finding as `resolved_findings`.

## Gap noted (fact only — classification deferred to phase 2)

canonical: `docs/issue-1017/reports/implementation.md` (read this session, full-file search)
No verbatim watchdog-tick output appears anywhere in the file, though the issue's Acceptance
section asks for a provenance quote of "today's watchdog tick output" in the record. The
record's `## Acceptance verification` section shows unit-test output there instead. Whether
this is a step-level deficiency is a phase-2 judgment call, withheld here.

## Approval status

canonical: `gh issue view 1017 --json comments` (read this session, full comment thread; none
of its entries is `APPROVE issue-1017/execution-observation` or a delegation-backed
equivalent)
No approval exists yet for this role's phase 2 on issue #1017. A phase-2-shaped write attempted
this session was refused by `approval-gate.sh` (hook error, this session) for that reason. This
session stops at phase 1 per contract v3 s19: proposal follows, no record.md this turn.
