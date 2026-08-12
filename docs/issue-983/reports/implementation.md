---
code_under_review:
- on-the-record/hooks/role-deviation-directive.sh
- on-the-record/hooks/deviation-log-guard.sh
- on-the-record/hooks/hooks.json
- on-the-record/hooks/test_deviation_log_guard.py
- on-the-record/hooks/test_role_deviation_directive.py
- docs/handbooks/deviation-loop.md
type: feature
breaking: false
canonical: python3 -m pytest on-the-record/hooks/test_role_deviation_directive.py on-the-record/hooks/test_deviation_log_guard.py -v run this session, 12 passed
verdict: pass
loop_state: landed
---

# Implementation record (issue #983)

## What was done

Extended the #958/#803 self-driven loop (directive text + Stop-hook
guard) to bind inside a spawned role session, not only the orchestrator.

canonical: docs/issue-754/reports/defect-verification.md, Attempt 3
(`sed -n '1,12p' on-the-record/hooks/directive.sh`, re-derived this
session against current HEAD). Audit E Finding 1 found the loop
structurally orchestrator-only via `directive.sh`'s `CLAUDE_ROLE`-unset
gate and `deviation-log-guard.sh`'s matching `CLAUDE_ROLE`-unset early
exit.

- Added `on-the-record/hooks/role-deviation-directive.sh`: a new
  `UserPromptSubmit` hook, gated the opposite way from `directive.sh`
  (`CLAUDE_ROLE`-set only, mirroring `record-tiering-directive.sh`'s
  skeleton). Injects the RECOGNIZE/CLASSIFY/RESOLVE paragraph. The
  inline-fix resolution matches the orchestrator variant exactly. The
  file-as-issue resolution differs: a role session cannot spawn a peer
  role or open an issue on its own initiative mid-task (role-handoff
  contract v3's SCOPE-EXCEEDED RULE), so it resolves to finish-what's-
  covered / STOP / report, with a `filed` log line noting the item was
  reported rather than spawned.
- Registered the new hook in `on-the-record/hooks/hooks.json`'s
  `UserPromptSubmit` array.
- Removed `deviation-log-guard.sh`'s `CLAUDE_ROLE`-unset early exit
  (previously line 29) so the Stop-hook guard now binds for role
  sessions too. No other change to the guard was needed — its existing
  branch-to-path regex (`^issue-(\d+)/([\w-]+)$`) already resolves a
  role session's own `issue-<n>/<role>` branch to the correct per-issue
  log path.
- Added a role-session subsection to `docs/handbooks/deviation-loop.md`
  cross-referencing the new directive and its file-as-issue resolution.
- Added test cases to `on-the-record/hooks/test_deviation_log_guard.py`:
  `t_role_session_traceless_deviation_is_blocked`, testing that the
  guard binds and refuses when `CLAUDE_ROLE` is set, a recognized
  marker is present, and no log line landed;
  `t_role_session_no_deviation_is_silent`, the empty-state case (no
  marker -> no log requirement, silent exit); and
  `t_role_session_logged_deviation_passes`, a properly logged
  role-session entry producing a silent exit. Replaced the old
  `t_claude_role_set_is_noop` case, whose assertion encoded the bug this
  issue fixes (it asserted the guard stayed silent when `CLAUDE_ROLE`
  was set even with an unmatched marker present), with the new binding
  test above.

## Why

Mid-task problems surface in role sessions, not the orchestrator's own
conversation — a role session that hits an out-of-scope judgment and
silently drops it (no inline fix logged, no issue filed) leaves no
trace anywhere. The existing loop only reached the orchestrator's
`/run` conversation because both the steering text (`directive.sh`) and
its enforcement (`deviation-log-guard.sh`) were gated to fire
exclusively when `CLAUDE_ROLE` was unset.

## Upstream basis

- docs/issue-754/reports/defect-verification.md — audit E Finding 1,
  the gap this issue closes.
- docs/issue-983/proposals/2026-08-12-role-session-deviation-loop.md —
  the approved phase-1 proposal this record delivers against. Approved
  via the issue-level comment `APPROVE issue-983/implementation`
  (single-account mode, an account listed in docs/specs/approvers.md).
- docs/handbooks/deviation-loop.md — pre-existing reference doc,
  extended rather than replaced.

## Rationale for deviations

No divergence from the approved phase-1 proposal's planned-work section
occurred during execution. This heading is present only because
`record-shape-gate.sh` keys off the bare substring naming the loop
feature anywhere in the record body, and this record's subject matter
(extending that loop to role sessions) necessarily contains that word
throughout — stated here to satisfy the mechanical gate, not because a
scope-exceeded stop or an alternative-swap actually happened.

## Acceptance verification

canonical: this session's own run,
`python3 -m pytest on-the-record/hooks/test_role_deviation_directive.py on-the-record/hooks/test_deviation_log_guard.py -v`:
```
test_role_deviation_directive.py::t_directive_states_role_variant_deviation_loop PASSED
test_role_deviation_directive.py::t_directive_is_silent_without_claude_role PASSED
test_role_deviation_directive.py::t_directive_fails_open_when_orchestrate_off_set PASSED
test_deviation_log_guard.py::t_no_marker_is_silent PASSED
test_deviation_log_guard.py::t_traceless_deviation_is_blocked PASSED
test_deviation_log_guard.py::t_logged_deviation_passes PASSED
test_deviation_log_guard.py::t_role_session_traceless_deviation_is_blocked PASSED
test_deviation_log_guard.py::t_role_session_no_deviation_is_silent PASSED
test_deviation_log_guard.py::t_role_session_logged_deviation_passes PASSED
test_deviation_log_guard.py::t_orchestrate_off_is_noop PASSED
test_deviation_log_guard.py::t_missing_transcript_path_fails_closed_silently PASSED
test_deviation_log_guard.py::t_off_issue_branch_uses_docs_reports_path PASSED
12 passed in 0.42s
```
Above run covers both required acceptance cases directly:
`t_role_session_traceless_deviation_is_blocked` is the role-session-
context binding case (guard refuses with `CLAUDE_ROLE` set and an
unmatched recognized marker); `t_role_session_no_deviation_is_silent` is
the empty-state case (role session, no recognized marker, silent exit,
no log required). `t_directive_states_role_variant_deviation_loop`,
this record's live-fire test for `role-deviation-directive.sh`
(required by `live-fire-test-guard.sh`), exercises the new hook as a
real `UserPromptSubmit`-style invocation and checks its role-variant
text appears under a set `CLAUDE_ROLE`.

## Hunt

closed_checks:
- before-landing warrant hunt, stance 0 (assume the gate just touched
  is bypassable — find the bypass), NO FINDING —
  docs/issue-983/reports/implementation/2026-08-12-hunt-role-session-deviation-loop.md,
  code_under_review as above.

After-proposal dispatch was skipped for this transition: the proposal
was approved via a pre-existing issue-level `APPROVE` comment posted
before phase-1 content existed on the branch, so there was no
after-proposal diff yet to seed a hunt against; the before-landing
dispatch above is the only hunt this record carries.

## What did not work

None.

## Open findings

None.
