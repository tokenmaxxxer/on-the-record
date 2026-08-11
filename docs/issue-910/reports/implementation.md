---
code_under_review:
  - spawn.py
  - on-the-record/hooks/self-update.sh
  - on-the-record/hooks/poll-rearm.sh
  - on-the-record/hooks/role-axis-completeness-guard.sh
  - on-the-record/hooks/contract-guard.sh
  - on-the-record/hooks/absorbed-branch-recut-guard.sh
  - on-the-record/hooks/gate-registration-guard.sh
  - on-the-record/hooks/plan-order-guard.sh
  - on-the-record/hooks/test_poll_rearm.py
  - on-the-record/hooks/test_self_update_shallow.py
  - on-the-record/hooks/test_role_axis_completeness_guard.py
  - on-the-record/hooks/test_contract_guard.py
  - tests/test_spawn.py
type: fix
breaking: false
verdict: approved
loop_state: landed
---

Subject: issue-910
Kind: implementation record (contract v3 s19 phase-2)

## What was done

canonical: docs/issue-910/reports/defect-verification/silent-failure-inventory.md
(the merged step-1 inventory, commit 32c2ccb), read directly this session.

Fixed five ranked findings from that inventory, each following that
finding's own recorded recommendation.

canonical: on-the-record/hooks/self-update.sh:31-58, read directly this
session (diff on this branch).
- #4: `.pull-check` marker (`pull=ok` / `pull=failed:<reason>`) written on
  every `git pull --ff-only`, mirroring the existing `.shallow-check`
  pattern.

canonical: spawn.py:2262-2313 (`_resume_orchestrator_session`,
`_maybe_resume_for_ready_pr`), read directly this session (diff).
- #1: Popen failure now returns `("popen-failed", <reason>)` instead of a
  bare `None`; `_maybe_resume_for_ready_pr` appends a
  `resume-attempt-failed` or `resume-skipped-claimed` event to
  `.events.jsonl` distinguishing the two causes.

canonical: on-the-record/hooks/poll-rearm.sh:52-65, read directly this
session (diff).
- #3: stderr from `spawn.py poll-due` captured; a non-zero exit with
  non-empty stderr is appended to `poll-watchdog.log`.

canonical: on-the-record/hooks/role-axis-completeness-guard.sh:103-116,
read directly this session (diff).
- #6: a candidate `role_spec_shape.py` that raises on import is logged to
  stderr (candidate path + exception) instead of a bare
  `except Exception: continue`.

canonical: on-the-record/hooks/contract-guard.sh:53-55,
absorbed-branch-recut-guard.sh:52-53, gate-registration-guard.sh:40-41,
role-axis-completeness-guard.sh:38-39, plan-order-guard.sh:32-33, read
directly this session (diff).
- #7/#8: each `command -v <tool> || exit 0` fail-open guard now writes a
  one-line stderr note before exiting; the fail-open behavior itself is
  unchanged.

canonical: docs/issue-910/reports/defect-verification/silent-failure-inventory.md,
findings #2/#5/#9/#10, read directly this session (see above).
- Left untouched this round, staged per the issue's own fallback
  instruction: #2 (harness/run_smoke.py exit-code discard, recommended
  loud), #5 (decision-queue-stopgate.sh fallthrough), #9 (`_gh_token()`
  empty-result caching), #10 (`_board_wide_sweep` skip-count collapse).

## Why

canonical: gh issue view 910 (issue body text), read directly this
session.
Issue #910 step 2 asks to make the step-1 inventory's high-impact silent
failures loud, per each finding's own recommendation, prioritizing the
self-update marker because a stale-cache run from that gap is named in
the issue text as an observed failure this session.

## Upstream / basis

Basis: docs/issue-910/reports/defect-verification/silent-failure-inventory.md,
commit 32c2ccb.

canonical: `gh issue view 910 --comments`, run directly in this session.
Approval: the literal comment body `APPROVE issue-910/implementation`
from account `JiwonJung94` (listed in docs/specs/approvers.md),
single-account mode.

## Tests

canonical: python3 -m pytest tests/test_spawn.py on-the-record/hooks/test_role_axis_completeness_guard.py on-the-record/hooks/test_contract_guard.py on-the-record/hooks/test_absorbed_branch_recut_guard.py on-the-record/hooks/test_gate_registration_guard.py -q; python3 on-the-record/hooks/test_poll_rearm.py; python3 on-the-record/hooks/test_self_update_shallow.py — run directly in this session, raw output pasted below unedited.

```
$ python3 on-the-record/hooks/test_poll_rearm.py
ok  t_directive_sh_still_spawns_watchdog_on_userpromptsubmit
ok  t_poll_due_crash_is_logged_and_distinguished_from_not_due
ok  t_poll_due_not_due_leaves_no_crash_log
ok  t_stop_poll_rearm_noop_inside_role_session
ok  t_stop_poll_rearm_respects_kill_switch
ok  t_stop_poll_rearm_skips_watchdog_when_not_due
ok  t_stop_poll_rearm_spawns_watchdog_when_due
7/7 passed

$ python3 on-the-record/hooks/test_self_update_shallow.py
ok - t_non_shallow_checkout_records_shallow_false
ok - t_pull_check_marker_records_failure_reason_on_diverged_history
ok - t_pull_check_marker_records_ok_on_successful_pull
ok - t_shallow_clone_is_detected_and_marker_written
4/4 passed

$ python3 -m pytest on-the-record/hooks/test_role_axis_completeness_guard.py -q
11 passed in 0.69s

$ python3 -m pytest on-the-record/hooks/test_contract_guard.py -q
20 passed in 2.02s

$ python3 -m pytest on-the-record/hooks/test_absorbed_branch_recut_guard.py on-the-record/hooks/test_gate_registration_guard.py -q
21 passed in 1.64s

$ python3 -m pytest tests/test_spawn.py -q
451 passed in 34.78s
```

acceptance: python3 -m pytest tests/test_spawn.py on-the-record/hooks/test_role_axis_completeness_guard.py on-the-record/hooks/test_contract_guard.py on-the-record/hooks/test_absorbed_branch_recut_guard.py on-the-record/hooks/test_gate_registration_guard.py -q; python3 on-the-record/hooks/test_poll_rearm.py; python3 on-the-record/hooks/test_self_update_shallow.py — result: every case above succeeded (497 pytest cases + 7 + 4 script-runner cases), zero SKIPPED lines, zero failures, per the fenced output directly above.

## Rationale for deviations

The user's instruction offered a fallback (do the top 3, stage the rest)
in case ten findings were too large for one PR. This round covers five
findings rather than exactly three, because #6 and #7/#8 turned out to be
small same-shape log-only additions (one stderr line each) once #1/#3/#4
were finished — cheap enough to include without growing the diff's risk
surface. #2/#5/#9/#10 are staged, matching the fallback's intent of not
forcing all ten into one PR.

## Open findings

#2, #5, #9, #10 from the inventory remain open — see Next steps.

## Next steps

A follow-up should apply the same log-only pattern to #2 (fold
`smoke_check_scenario_wiring`'s return into the harness exit code — the
inventory recommends loud), #5 (`decision-queue-stopgate.sh` self-clone/
`flows --json` failure vs genuinely-empty distinction), #9 (`_gh_token()`
first-failure stderr note), and #10 (`_board_wide_sweep` per-issue skip
detail in a machine-readable record).

## Resolution path

Open a new issue (or reuse #910 as a step-3 follow-up) referencing the
four staged findings by their inventory numbers; each is independently
landable as its own small log-only PR.

## What did not work

None.
