---
issue: 2229
role: execution-observation
loop_state: reported
upstream:
  - path: docs/issue-2229/reports/implementation.md (PR #2242 branch, not present on this branch)
    sha: f90ab303ec88f57e9e56e5de0b0234ef9e1c508a
subject: f90ab303ec88f57e9e56e5de0b0234ef9e1c508a
test: python3 gates/test_acceptance_gate.py
result: passed
assertedBy: execution-observation session, issue-2229, this turn
---

# issue-2229 — execution-observation record

## What was done

Independent execution-observation of PR #2242 (branch
`issue-2229/implementation` into `main`, head
`f90ab303ec88f57e9e56e5de0b0234ef9e1c508a`, state OPEN) against issue
#2229's three acceptance bullets. Per the
defect-verification-independence skill, every scenario below was
designed and run by this session first, in a detached read-only
worktree (`git worktree add --detach /tmp/eo2229-pr-worktree
origin/issue-2229/implementation`) plus a second worktree of
`origin/main` for a control comparison. The implementation role's own
report (which lives only on the PR's branch, not this branch's tree)
was read only afterward, to check the right bullets were targeted;
none of the command output below is copied from it.

**1) `gate:` bullet — `gates/test_acceptance_gate.py`, re-run by this
session:**

canonical: python3 gates/test_acceptance_gate.py (this session, PR-branch worktree)
```
ok - t_acceptance_heading_case_and_level_insensitive
ok - t_all_three_violations_reported_together
ok - t_artifact_reference_passes
ok - t_artifact_reference_without_empty_state_or_provenance_blocks
ok - t_empty_state_and_provenance_present_passes
ok - t_empty_state_not_applicable_passes
ok - t_format_sweep_report_empty_is_clean
ok - t_format_sweep_report_lists_each_issue
ok - t_gate_colon_line_passes
ok - t_gates_workflow_path_no_longer_passes
ok - t_issue_2085_all_three_named_in_single_refusal
ok - t_issue_2229_own_repro_shape_caught_at_authoring_time
ok - t_missing_acceptance_section_blocks
ok - t_missing_section_message_points_at_format_doc
ok - t_only_reads_acceptance_section_not_whole_body
ok - t_other_three_violation_messages_point_at_format_doc
ok - t_prose_only_acceptance_blocks
ok - t_sweep_empty_open_issues_returns_empty_dict
ok - t_sweep_reports_only_violating_issues
ok - t_sweep_skips_entries_with_no_number
ok - t_unverifiable_escape_passes
ok - t_unverifiable_exempts_empty_state_and_provenance
ok - t_well_formed_test_issue_passes_at_authoring_time
23/23 passed
```
canonical: python3 gates/test_acceptance_gate.py (same run quoted immediately above, this session)
Every case reports `ok`, no `FAILED` line, 23/23 — this session's own
re-run in a clean process. The issue text itself names a nonexistent
two-segment path under tests/; the real file this repo's
`check_issue_body` unit tests live in, both before and after this
change, is `gates/test_acceptance_gate.py` — this session located that
substitution by grepping the repo for `check_issue_body` before
running anything.

**2) `empty state:` bullet — self-devised, full CLI path (not the
PR's own unit-test shortcut of calling the pure function directly):**

Built a scratch `gh` shim on `PATH` that prints `[]` (zero open
issues) and ran the real subprocess-backed CLI against it.

canonical: PATH="/tmp/eo2229-fakegh-bin:$PATH" python3 gates/acceptance_gate.py --sweep --repo /tmp/eo2229-fakegh-repo (this session, scratch repo + scratch `gh` shim, PR-branch worktree)
```
acceptance-sweep: 스폰 불가능한 열린 이슈 없음
```
canonical: echo $? immediately after the command above (this session)
```
0
```
Clean report through the real `gh`-subprocess code path (not only the
pure function in isolation), zero exit, no exception — the empty-state
bullet's own wording ("report an empty result cleanly, not error")
holds against this run.

canonical: python3 -c "import sys; sys.path.insert(0,'gates'); import acceptance_gate as ag; print(ag.sweep_issue_bodies([]))" (this session, PR-branch worktree)
```
{}
```

**3) `provenance: executed-live` bullet:**

canonical: python3 gates/acceptance_gate.py --sweep (this session, PR-branch worktree, run before this session opened the implementation role's own report)
```
acceptance-sweep: 스폰 불가능한 열린 이슈 8건
  이슈 #1595: 이슈 #1595 본문에 '## Acceptance' 절이 없다 ... 통과하는 형식은 on-the-record/directive/acceptance-format.md 를 봐라.
  이슈 #2011: ...'provenance: ...' 줄이 없다... 통과하는 형식은 on-the-record/directive/acceptance-format.md 를 봐라.
  이슈 #2071: 이슈 #2071 본문에 '## Acceptance' 절이 없다 ... 통과하는 형식은 on-the-record/directive/acceptance-format.md 를 봐라.
  이슈 #2079: ...'empty state: ...' 및 'provenance: ...' 줄이 없다... (두 줄 다 pointer 포함)
  이슈 #2147: ...'provenance: ...' 줄이 없다... 통과하는 형식은 on-the-record/directive/acceptance-format.md 를 봐라.
  이슈 #2152: 프로즈뿐 + empty state/provenance 없다 (세 줄 모두 pointer 포함)
  이슈 #2153: 프로즈뿐 + empty state/provenance 없다 (세 줄 모두 pointer 포함)
  이슈 #2159: 프로즈뿐 + empty state/provenance 없다 (세 줄 모두 pointer 포함)
exit=1
```
canonical: python3 gates/acceptance_gate.py --sweep (same run quoted immediately above, this session)
This session's sweep landed on issue numbers 1595, 2011, 2071, 2079,
2147, 2152, 2153, and 2159 on its own — written down before this
session read the implementation role's own report — and every printed
violation line carries the `on-the-record/directive/acceptance-format.md`
pointer sentence, checked directly in the raw output above.

canonical: python3 spawn.py acceptance-sweep > /tmp/spawn_sweep.out; python3 gates/acceptance_gate.py --sweep > /tmp/direct_sweep.out; diff /tmp/direct_sweep.out /tmp/spawn_sweep.out (this session, PR-branch worktree)
```
(diff produced no output — the two files are byte-identical; both processes exited 1)
```
canonical: diff /tmp/direct_sweep.out /tmp/spawn_sweep.out (same run quoted immediately above)
`spawn.py acceptance-sweep` reproduces the direct
`gates/acceptance_gate.py --sweep` run exactly, same exit code.

canonical: python3 -c "..." feeding a locally-authored malformed body -- a `## Summary` heading plus a prose-only `## Acceptance` bullet with no gate:/empty state:/provenance: lines, authored by this session, not the PR's own fixture string (this session, PR-branch worktree)
```
- 이슈 #9901의 'Acceptance' 절이 프로즈뿐이다 ... 통과하는 형식은 on-the-record/directive/acceptance-format.md 를 봐라.
- 이슈 #9901의 'Acceptance' 절이 ... 'empty state: ...' 줄이 없다 ... 통과하는 형식은 on-the-record/directive/acceptance-format.md 를 봐라.
- 이슈 #9901의 'Acceptance' 절이 ... 'provenance: ...' 줄이 없다 ... 통과하는 형식은 on-the-record/directive/acceptance-format.md 를 봐라.
```
canonical: same script quoted immediately above, this session
This session's own fresh malformed body is caught at authoring time,
three violations, each carrying the format-doc pointer.

canonical: same script, a second locally-authored body carrying `gate:` + `empty state:` + `provenance: executed-live` lines (this session, PR-branch worktree)
```
[]
```
canonical: same script quoted immediately above, this session
Empty list — this session's own fresh well-formed body clears
`check_issue_body` with zero violations.

Edge/negative paths this session added beyond the PR's own fixture set
(independence-skill rule 2 — deliberately more than the happy path):

canonical: python3 -c "..." unverifiable: escape body, authored by this session (this session, PR-branch worktree)
```
[]
```
canonical: python3 -c "..." executable-ref body with `empty state:` present, `provenance:` missing, authored by this session (this session, PR-branch worktree)
```
["이슈 #9904의 'Acceptance' 절이 실행가능 산출물을 참조하지만 'provenance: executed-live|executed-unit|read' 줄이 없다 ... 통과하는 형식은 on-the-record/directive/acceptance-format.md 를 봐라."]
```
canonical: both commands quoted immediately above, this session
Exactly one violation fires (the provenance one) for the second body,
not all three — the three checks are independent of each other, not
all-or-nothing.

canonical: python3 gates/acceptance_gate.py --sweep --repo /tmp/eo2229-not-a-gh-repo (a directory this session created that is not a `gh`-recognized repo, PR-branch worktree)
```
acceptance-sweep: 이슈 목록을 읽을 수 없다 (gh 실패) — 판정 불가
```
canonical: same command quoted immediately above, exit code 1 (this session)
A `gh` read failure reports "cannot judge" on stderr with a nonzero
exit — never silently reported as a clean sweep.

Inheritance check: `board.py`'s spawn-time single-issue path
(`require_acceptance_gate` calling into the same `acceptance_gate.check`
function) was checked directly against a real open issue rather than
taking the PR's own "inherited unmodified" claim on trust.

canonical: python3 -c "import sys; sys.path.insert(0,'gates'); import acceptance_gate as ag; from pathlib import Path; print(ag.check(Path('.'), 1595))" (this session, PR-branch worktree)
```
["이슈 #1595 본문에 '## Acceptance' 절이 없다 ... 통과하는 형식은 on-the-record/directive/acceptance-format.md 를 봐라."]
```
canonical: same command quoted immediately above, this session; grep -n "check_issue_body" board.py showed require_acceptance_gate calling _acceptance_gate.check, which itself calls check_issue_body
The single-issue spawn-time path carries the same pointer this session
checked in the sweep path above, against the same real issue #1595.

canonical: python3 spawn.py lint --issue 2229 (this session, PR-branch worktree)
```
이슈 #2229 lint: 위반 없음
```
canonical: same command quoted immediately above, exit 0 (this session)
Self-referential sanity check: issue #2229's own `## Acceptance`
section clears the same check it's asking to be swept.

**4) Regression, re-run and extended beyond the PR's own claim:**

canonical: python3 -m pytest -q gates/test_closes_gate_ci.py tests/test_spawn_pipeline.py -n0 (this session, PR-branch worktree)
```
137 passed in 11.28s
```
canonical: python3 -m pytest -q gates/test_closes_gate_ci.py tests/test_spawn_pipeline.py -n0 (same run quoted immediately above, this session)
The pasted summary line reads 137 passed, no failed line and no
skipped line follow it — matches this session's own hand-typed
tally above.

This session then went further (independence-skill rule 4: do not
stop looking after one clean result) and re-ran the same two files
WITH default xdist parallelism three separate times.

canonical: python3 -m pytest -q gates/test_closes_gate_ci.py tests/test_spawn_pipeline.py, first repeat (this session, PR-branch worktree)
```
FAILED tests/test_spawn_pipeline.py::DryRunModelReflection::test_whitespace_only_output_reflects_builtin_default
FAILED tests/test_spawn_pipeline.py::SpawnCmd::test_role_model_whitespace_only_config_uses_builtin_default
2 failed, 135 passed in 1.39s
```
canonical: same command, second repeat (this session, PR-branch worktree)
```
FAILED tests/test_spawn_pipeline.py::DryRunModelReflection::test_whitespace_only_output_reflects_builtin_default
FAILED tests/test_spawn_pipeline.py::SpawnCmd::test_role_model_unset_uses_builtin_default
3 failed, 134 passed in 1.52s
```
canonical: same command, third repeat (this session, PR-branch worktree)
```
FAILED tests/test_spawn_pipeline.py::DryRunModelReflection::test_unset_output_reflects_builtin_default
FAILED tests/test_spawn_pipeline.py::SpawnCmd::test_role_model_whitespace_only_uses_builtin_default
4 failed, 133 passed in 1.31s
```
canonical: the three repeats quoted immediately above, this session
A different pair (or more) of test names fails each repeat under
default parallelism — wider than the two specific names the PR's own
single sample cited, though every failing name is drawn from the same
`test_role_model_*`/model-reflection cluster.

To check whether this predates the PR's diff, this session checked out
a separate `origin/main` worktree (not the PR's own `git stash`
method) and ran the identical command three times there.

canonical: python3 -m pytest -q gates/test_closes_gate_ci.py tests/test_spawn_pipeline.py, `origin/main` worktree head 75573112, first repeat (this session)
```
FAILED tests/test_spawn_pipeline.py::SpawnCmd::test_role_model_unset_uses_builtin_default
1 failed, 136 passed in 10.63s
```
canonical: same command, `origin/main` worktree, second repeat (this session)
```
137 passed in 1.36s
```
canonical: same command, `origin/main` worktree, third repeat (this session)
```
FAILED tests/test_spawn_pipeline.py::SpawnCmd::test_role_model_whitespace_only_config_uses_builtin_default
1 failed, 136 passed in 1.35s
```
canonical: the three `origin/main` repeats quoted immediately above, this session
The same nondeterministic failure family reproduces on `main` at
75573112 too, on a tree this PR's diff never touched — an
independently chosen control (a clean `main` worktree, not a re-run of
the PR's own `git stash` recipe) landing on the same read the PR's own
report separately reached: pre-existing, not from this diff. Recorded
as an open finding below, not a defect in issue #2229's own
deliverable.

canonical: python3 -m py_compile spawn.py gates/acceptance_gate.py gates/test_acceptance_gate.py (this session, PR-branch worktree)
```
(no output, exit 0)
```

## Why

Verify-at-landing requires independently re-executing the issue's own
named acceptance criteria rather than citing the PR's pasted output;
the defect-verification-independence skill further requires designing
self-devised scenarios (edge/negative paths beyond the PR's own
fixtures, a control comparison against `main`) before reading the
upstream role's own report, so its clean verdict does not pre-shape
which checks this session ran or how many. All three acceptance
bullets were re-run from scratch in a separate worktree; CLI wiring,
the `board.py` inheritance claim, and the flakiness aside were each
independently re-derived rather than trusted from that report's prose.

## Upstream basis

The implementation role's own report at
`f90ab303ec88f57e9e56e5de0b0234ef9e1c508a` (PR #2242, branch
`issue-2229/implementation` — that report lives only on that branch,
out-of-scope for this branch's own tree), read only after this
session's own scenarios were designed and run.

## Open findings

1. The xdist-parallel flakiness in `tests/test_spawn_pipeline.py`'s
   model-routing tests is wider than the PR's own single sample
   captured (varying test names and failure counts across three
   repeated runs, both on the PR branch and on `main`), though this
   session's own independent `main`-worktree control shows it predates
   and is unrelated to this PR's diff. Resolution path: file a
   separate issue for the xdist worker-pollution itself — out of scope
   for #2229, whose actual deliverable (the sweep and the format-doc
   pointer) touches none of the affected model-routing code; until
   then, the `-n0` invocation remains the reliable one for this test
   pair.

## Next steps

None — loop_state is terminal (`reported`) for this record kind.

## Verdict

canonical: python3 gates/test_acceptance_gate.py, this session's own re-run pasted in full under bullet 1 above
23/23 ok, zero FAILED — the named gate suite.

canonical: PATH="/tmp/eo2229-fakegh-bin:$PATH" python3 gates/acceptance_gate.py --sweep --repo /tmp/eo2229-fakegh-repo, this session's own run pasted under bullet 2 above
Zero-open-issues sweep exits clean, no error — the empty-state bullet.

canonical: python3 gates/acceptance_gate.py --sweep, this session's own run pasted under bullet 3 above
Live sweep independently lands on the same 8 currently-unspawnable
open issues; this session's own fresh malformed and well-formed
bodies are caught and cleared respectively, `spawn.py acceptance-sweep`
matches byte-for-byte, and `board.py`'s spawn-time path was checked
directly against real issue #1595 rather than taken on trust — the
provenance bullet.

Issue #2229's three acceptance bullets all hold, independently
reproduced against PR #2242's branch, per the citations above.
