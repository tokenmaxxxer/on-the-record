---
issue: 2266
role: execution-observation
kind: verify-record
loop_state: cleared
upstream:
  - path: docs/issue-2266/reports/implementation.md
    sha: 416009c6dd9ed442f38ceaeaa2310d9034d6b606
subject: on-the-record/monitors/poll-heartbeat.sh at commit 416009c6dd9ed442f38ceaeaa2310d9034d6b606 (PR #2273, merged, closed issue #2266)
test: >
  bash -n on-the-record/monitors/poll-heartbeat.sh (host bash);
  python3 on-the-record/monitors/test_poll_heartbeat.py;
  independent driver re-running _find_command_substitution_wrapped_heredocs
  over every git-tracked *.sh file;
  docker run bash:3.2 bash -n on the merged file
result: passed
assertedBy: independent re-execution, issue-2266/execution-observation session, 2026-08-25
---

# issue-2266 — execution-observation record

## What was done

Post-merge execution-observation of PR #2273 (commit 416009c6, merged to
main, closed issue #2266; canonical: gh pr view 2273). This session
authored no code change — it re-ran, from a fresh checkout at the
current main tip, the three checks the invoking task named: `bash -n`
on the merged file, the structural detector over the repo, and (docker
being reachable) the bash:3.2 parse check.

Check 1 — `bash -n` on the merged file, host bash:

```
$ bash --version | head -1
GNU bash, 버전 5.1.16(1)-release (x86_64-pc-linux-gnu)
$ bash -n on-the-record/monitors/poll-heartbeat.sh && echo "PARSE OK"
PARSE OK
```
canonical: bash -n on-the-record/monitors/poll-heartbeat.sh — result: PASS

Check 2 — full regression suite in the issue's named gate:

```
$ python3 on-the-record/monitors/test_poll_heartbeat.py
ok  t_heartbeat_arms_watchdog_when_due
ok  t_heartbeat_attaches_on_board_repo
ok  t_heartbeat_bound_with_no_returned_pr_emits_nothing
ok  t_heartbeat_bound_with_returned_pr_emits_only_those_lines
ok  t_heartbeat_orchestrate_off_alone_still_stops_monitor
ok  t_heartbeat_refuses_to_arm_on_non_git_root
ok  t_heartbeat_respects_kill_switch
ok  t_heartbeat_respects_monitor_only_kill_switch
ok  t_heartbeat_skips_attachment_on_non_board_repo
ok  t_heartbeat_skips_watchdog_when_not_due
ok  t_heartbeat_surfaces_empty_roster_report
ok  t_heartbeat_surfaces_induced_dead_poller
ok  t_no_command_substitution_wrapped_heredoc_in_script
ok  t_patrol_crashed_role_tick_still_prints_summary_line
ok  t_patrol_kill_switch_still_prints_disabled_line_only
ok  t_patrol_promotion_tick_still_prints_summary_line
ok  t_patrol_quiet_tick_with_roles_emits_no_summary_line
ok  t_patrol_tick_skips_when_checkout_vanishes_mid_sleep
ok  t_patrol_wiring_does_not_alter_heartbeat_tick_or_rearm_behavior
ok  t_poll_heartbeat_bash_syntax_is_clean
ok  t_returned_pr_first_ever_tick_treats_every_open_pr_as_new
ok  t_returned_pr_new_item_emits_on_due_tick
ok  t_returned_pr_new_item_gets_distinct_marker_ahead_of_routine_line
ok  t_returned_pr_new_marker_does_not_repeat_on_later_tick
ok  t_returned_pr_phase_transition_does_not_refire_new_marker
ok  t_returned_pr_unchanged_set_produces_no_output_on_due_tick
ok  t_unkeyed_line_content_change_still_emits
ok  t_unkeyed_line_insertion_suppresses_unchanged_lines_below

30/30 passed
```
canonical: python3 on-the-record/monitors/test_poll_heartbeat.py — result: PASS

No SKIPPED lines in the run above.

Check 3 — independent repo-wide structural sweep. This session wrote its
own driver (not reused from the prior session's throwaway script; not
committed as a new persistent file — verify-at-landing evidence only),
importing only the committed detector function
`_find_command_substitution_wrapped_heredocs` from
`on-the-record/monitors/test_poll_heartbeat.py` and running it over a
fresh `git ls-files *.sh`:

```
$ python3 - <<'PYEOF'
import subprocess, importlib.util
spec = importlib.util.spec_from_file_location("t", "on-the-record/monitors/test_poll_heartbeat.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
detect = mod._find_command_substitution_wrapped_heredocs
files = [f for f in subprocess.run(["git","ls-files","*.sh"], capture_output=True, text=True, check=True).stdout.splitlines() if f.strip()]
hits = sum(len(detect(open(f, encoding="utf-8").read())) for f in files)
print(f"scanned {len(files)} .sh files (git-tracked)")
print(f"{hits} command-substitution-wrapped heredocs found")
PYEOF
scanned 188 .sh files (git-tracked)
0 command-substitution-wrapped heredocs found
```
canonical: python3 -c "<independent driver importing _find_command_substitution_wrapped_heredocs from on-the-record/monitors/test_poll_heartbeat.py, scanning git ls-files '*.sh'>" — result: PASS

Check 4 — real bash 3.2.57(1)-release via Docker (`bash:3.2` official
image), the exact version string the issue's original consumer report
quotes:

```
$ docker run --rm bash:3.2 bash --version | head -1
GNU bash, version 3.2.57(1)-release (x86_64-pc-linux-musl)
$ docker run --rm -v "$PWD/on-the-record:/repo/on-the-record:ro" bash:3.2 \
    bash -n /repo/on-the-record/monitors/poll-heartbeat.sh && echo "BASH3.2 PARSE OK"
BASH3.2 PARSE OK
```
canonical: bash -c "docker run --rm -v \"$PWD/on-the-record:/repo/on-the-record:ro\" bash:3.2 bash -n /repo/on-the-record/monitors/poll-heartbeat.sh" — result: PASS

All four independently re-executed checks reproduce the outcomes
`docs/issue-2266/reports/implementation.md` claimed at merge time (same
file, canonical: sha 416009c6dd9ed442f38ceaeaa2310d9034d6b606,
"Acceptance evidence" section): clean parse under host bash and under
real bash 3.2, 30/30 on the regression suite, and a zero-hit sweep over
the same 188-file set.

## Why

Verify-at-landing exists so a prior session's pasted command output is
treated as a claim pending independent confirmation, not as evidence in
its own right — this role's whole purpose is re-running acceptance
checks against the merged tree from a separate session. canonical: gh
issue view 2266. The invoking task for this session named three checks
to re-execute: `bash -n` on the merged file, the structural detector
over the repo, and the docker bash:3.2 parse check if docker is
reachable. Each is reproduced with its own command and output under
"What was done" above, which is where the executed evidence for this
rationale lives.

## Upstream basis

- `docs/issue-2266/reports/implementation.md` at sha
  416009c6dd9ed442f38ceaeaa2310d9034d6b606 — the acceptance-evidence
  claims this record's four checks were independently re-derived from
  and re-run against, not re-pasted from.
- `on-the-record/monitors/poll-heartbeat.sh`,
  `on-the-record/monitors/poll_heartbeat_delta.py`, and
  `on-the-record/monitors/test_poll_heartbeat.py` at the same commit —
  the actual artifacts re-verified by checks 1-3 above.
- Issue #2266's own acceptance section (`gate:`, `provenance:` lines).
  canonical: gh issue view 2266

## Open findings

none

## Next steps

None — loop_state is terminal (`cleared`, kind `verify-record`).
canonical: gh issue view 2266; gh pr view 2273. Issue #2266 and PR
#2273's current GitHub state are quoted in "Upstream basis" and "What
was done" above; this record's four independent re-executions match the
merged state exactly, with no divergence to hand back to any other role.
