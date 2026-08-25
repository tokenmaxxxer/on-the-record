---
issue: 2266
role: conformance-review
kind: review-record
loop_state: reported
upstream:
  - path: on-the-record/monitors/poll-heartbeat.sh
    sha: 416009c6dd9ed442f38ceaeaa2310d9034d6b606
  - path: on-the-record/monitors/poll_heartbeat_delta.py
    sha: 416009c6dd9ed442f38ceaeaa2310d9034d6b606
  - path: on-the-record/monitors/test_poll_heartbeat.py
    sha: 416009c6dd9ed442f38ceaeaa2310d9034d6b606
  - path: docs/issue-2266/reports/implementation.md
    sha: 416009c6dd9ed442f38ceaeaa2310d9034d6b606
subject: PR #2273 (merged 416009c6dd9ed442f38ceaeaa2310d9034d6b606, "issue-2266: remove poll-heartbeat.sh's bash 3.2 heredoc landmine structurally")
test: issue #2266 Acceptance section (verbatim, gate/empty-state/provenance clauses) plus the issue's numbered Ask, vs the merged commit's diff and its own docs/issue-2266/reports/implementation.md record
result: passed
assertedBy: issue-2266/conformance-review (builder-blind independent post-merge review, this session)
---

# issue-2266 — conformance-review record

## What was done

Post-merge, builder-blind conformance review of PR #2273 against issue
#2266's frozen Acceptance section and its numbered Ask — read
independently, no access to the builder session's own reasoning beyond
what is committed in the diff and its own record.

canonical: gh issue view 2266 (fetched live at review time; the source
this record grades PR #2273 against).

This branch's HEAD already is the merged commit, so no separate worktree
checkout of the PR was needed (unlike an open-PR review) — every check
below ran directly against this checkout:

canonical: git merge-base HEAD 416009c6
```
416009c6dd9ed442f38ceaeaa2310d9034d6b606
```

Extracted the issue's Ask + Acceptance section into 8 separately-verdicted
requirements (conformance-review-requirement-extraction rule 1: split the
bundled provenance sentence into its 3 independent clauses; rule 5: kept
the bash-3.2-reachability clause as its own conditional item with the
dependency stated inline; rule 6: dimension-tagged each). Findings below.

## Why

Every requirement below was checked by independently re-running the
actual command, not by re-reading the builder's own pasted transcript in
docs/issue-2266/reports/implementation.md — this issue's own Acceptance
clause frames provenance as "executed-live," and a conformance review
that only re-read the record would be checking that the builder
transcribed its own terminal correctly, not that the fix and its gate
actually hold. Inspection was used for the two static-shape requirements
(R1/R2 — conformance-review-verification-method-selection rule 1); Test
was used for the six requirements that already have an executable check
in the repo (R3-R8 — rule 4: reuse the existing test/command rather than
deriving a parallel manual check), each re-executed fresh this session.

## Findings

---
requirement: "Remove the landmine rather than re-balancing the apostrophe count (a heredoc lexically nested inside an unclosed `$( )` no longer exists in poll-heartbeat.sh)"
spec_ref: "issue #2266 Ask item 1"
verdict: Present
evidence: "416009c6:on-the-record/monitors/poll-heartbeat.sh:246-256 (comment + extraction call site); 416009c6:on-the-record/monitors/poll_heartbeat_delta.py:1-22 (docstring states the same rationale)"
canonical: grep -c '<<' on-the-record/monitors/poll-heartbeat.sh
```
0
```
rationale: Inspection (static/structural property) of the merged file
shows zero heredocs of any kind anywhere in poll-heartbeat.sh, which
trivially satisfies "no heredoc nested in an unclosed `$( )`" — a
stronger result than the minimum the Ask requires. The former inline
`python3 - <<'PY'` block now lives in on-the-record/monitors/poll_heartbeat_delta.py,
invoked from poll-heartbeat.sh:256 via a plain `python3 <path> ...` call
(no heredoc).
---
requirement: "The fix is structural (comment relocation or extraction), not a re-balancing of the heredoc body's apostrophe count"
spec_ref: "issue #2266 Ask item 1 (both named acceptable options) and body text \"parity-maintenance is not a fix\")"
verdict: Present
evidence: "416009c6:on-the-record/monitors/poll_heartbeat_delta.py (whole file, standalone .py, not a heredoc); 416009c6:on-the-record/monitors/poll-heartbeat.sh:256"
canonical: sed -n '256p' on-the-record/monitors/poll-heartbeat.sh
```
    diff_output="$(POLL_HEARTBEAT_TEXT="${printed_text}" python3 "${SCRIPT_DIR}/poll_heartbeat_delta.py" "${CHECKOUT}/runs/poll_heartbeat_last_state.json" "$(date +%s)")"
```
rationale: extraction is one of the two options the issue itself names as
acceptable; the invocation above is a plain script call with no heredoc
and no apostrophe-count arithmetic anywhere in the diff.
---
requirement: "A regression smoke exists in the issue's named gate that structurally detects the landmine shape"
spec_ref: "issue #2266 Ask item 2 (\"the minimal proxy is asserting the structural property\")"
verdict: Present
evidence: "416009c6:on-the-record/monitors/test_poll_heartbeat.py:895-931 (_find_command_substitution_wrapped_heredocs depth-tracking scanner), :934-942 (t_no_command_substitution_wrapped_heredoc_in_script), :945-961 (t_command_substitution_wrapped_heredoc_detector_catches_multiline_shape, synthetic-sample self-check)"
canonical: python3 on-the-record/monitors/test_poll_heartbeat.py
```
ok  t_board_sweep_lock_skip_treated_as_no_change
ok  t_command_substitution_wrapped_heredoc_detector_catches_multiline_shape
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
derived: all 30 lines read "ok", 0 "FAIL" lines appear in the transcript above, matching the trailing "30/30 passed" summary the suite itself prints.
rationale: Test method reused (existing test re-executed, rule 4) — this
is this review session's own fresh run, not a re-paste of
docs/issue-2266/reports/implementation.md's transcript. The self-check
test additionally confirms the detector would catch the multi-line
variant a before-landing warrant-hunt found the first draft's same-line
regex missed (docs/issue-2266/reports/implementation/2026-08-25-hunt-poll-heartbeat-bash32-heredoc-fix.md) —
a gap already closed pre-merge, not one this review is newly surfacing.
---
requirement: "The regression gate also includes a `bash -n` proxy check under whatever bash the host ships"
spec_ref: "issue #2266 Ask item 2 (\"plus bash -n under whatever bash ships\")"
verdict: Present
evidence: "416009c6:on-the-record/monitors/test_poll_heartbeat.py:964-971 (t_poll_heartbeat_bash_syntax_is_clean); this test is part of the suite run cited under the requirement above"
canonical: bash -n on-the-record/monitors/poll-heartbeat.sh && echo BASH_N_CLEAN
```
BASH_N_CLEAN
```
rationale: Test method (existing test reused, rule 4) plus a standalone
re-run outside the suite as a cross-check; both agree.
---
requirement: "Audit the repo's other `<<'...'` heredocs inside `$( )` for the same shape"
spec_ref: "issue #2266 Ask item 3"
verdict: Present
evidence: "independently re-implemented the same depth-tracking algorithm as 416009c6:on-the-record/monitors/test_poll_heartbeat.py:895-931 in a standalone script and ran it over every git-tracked *.sh file"
canonical: git ls-files '*.sh' | wc -l
```
188
```
canonical: python3 /tmp/sweep_heredoc.py (independent re-implementation of the depth-tracking scanner, this session; script removed after use)
```
scanned 188 files, 0 command-substitution-wrapped heredoc hits
```
derived: 188 == 188, matching docs/issue-2266/reports/implementation.md:246's own "scanned 188 .sh files (git-tracked)" count.
rationale: Test method — an independent re-implementation over the same
file set (not just re-running the builder's own script) rules out the
possibility that the builder's scanner and its repo-wide sweep share a
common blind spot; both independently agree on the same file count and
zero-hit result.
---
requirement: "Acceptance provenance clause 1: `bash -n` output pasted for the fixed file"
spec_ref: "issue #2266 Acceptance, provenance line, clause 1"
verdict: Present
evidence: "this session's own re-run (same command as the requirement above) reproduces a clean bash -n independent of docs/issue-2266/reports/implementation.md:201-210's pasted transcript"
canonical: bash --version | head -1
```
GNU bash, 버전 5.1.16(1)-release (x86_64-pc-linux-gnu)
```
rationale: Test method, directly re-executed rather than trusting the
pasted transcript in the implementation record.
---
requirement: "Acceptance provenance clause 2: structural-audit sweep output pasted, showing zero remaining command-substitution-wrapped heredocs with apostrophe-bearing bodies"
spec_ref: "issue #2266 Acceptance, provenance line, clause 2"
verdict: Present
evidence: "see the Ask-item-3 requirement above — independently reproduced 188 files scanned / 0 hits"
canonical: (same sweep command and output as the requirement above; not re-run twice in this record)
rationale: Test method, independently re-derived rather than merely
re-read from docs/issue-2266/reports/implementation.md:239-254's pasted
sweep output.
---
requirement: "Acceptance provenance clause 3 (conditional): if a bash 3.2 binary is reachable, paste its bash -n too; otherwise state verification is by structural elimination"
spec_ref: "issue #2266 Acceptance, provenance line, clause 3"
verdict: Present
evidence: "docker is reachable in this review session, so the \"reachable\" branch of the condition applies, not the structural-elimination fallback"
canonical: docker --version
```
Docker version 27.1.1, build 6312585
```
canonical: docker run --rm -v "$(pwd)/on-the-record/monitors/poll-heartbeat.sh:/tmp/poll-heartbeat.sh:ro" bash:3.2 bash -n /tmp/poll-heartbeat.sh; echo "EXIT=$?"
```
EXIT=0
```
rationale: Test method — a second, independently-invoked real bash 3.2
container run (different mount path than
docs/issue-2266/reports/implementation.md:212-225's own container run)
confirms the same clean result, rather than accepting the builder's own
container run as sufficient on its own.
---

## Upstream basis

- Issue #2266 (this record's subject).
canonical: gh issue view 2266
- PR #2273 / merge commit `416009c6dd9ed442f38ceaeaa2310d9034d6b606`.
canonical: gh pr view 2273 --json title,body,mergedAt,mergeCommit,files
- docs/issue-2266/reports/implementation.md (sha `416009c6`, same commit
  as the merge) — the builder's own record, cross-checked but not relied
  on in itself: every claim it makes that overlaps this review's
  Findings above was independently re-derived, not re-quoted.
- docs/issue-2266/reports/implementation/2026-08-25-hunt-poll-heartbeat-bash32-heredoc-fix.md
  (sha `416009c6`) — the before-landing warrant-hunt finding (same-line
  regex missed the multi-line landmine variant) and its resolution,
  referenced in the R3 finding's rationale above.

## Open findings

None. All 8 extracted requirements verdict Present under independent
re-execution; no Surface, Absent, Incorrect, or Unverifiable findings.

## Next steps

loop_state: reported is this record kind's terminal state
(session-protocol section 2, review-record -> reported); no further
action is required from this review role on issue #2266.

## Skill verdicts

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split issue #2266's Ask + Acceptance section into the 8 requirement blocks above (rule 1: split the bundled provenance sentence into 3 clauses; rule 5: kept the bash-3.2-reachability clause as its own conditional item with the dependency stated inline; rule 6: dimension-tagged each requirement inline in its own summary).

skill-verdict: conformance-review-verification-method-selection — applied: invoked; selected Inspection for the two static-shape requirements and Test for the six requirements with an existing executable check, each independently re-run this session rather than re-derived by hand (rule 4).

skill-verdict: conformance-review-verdict-assignment — applied: invoked; all 8 requirements assigned Present per rule 1's bar (implemented AND independently reproduced as reachable/active, not merely present in the diff) — none qualified for Surface, Absent, Incorrect, or Unverifiable.

skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every Finding above cites a commit-pinned `416009c6:file:line` location plus a `canonical:` command with its actual fenced output; the repo-wide-sweep requirement's evidence spans two independent runs (the file-count command and the scanner re-implementation), both cited as separate `canonical:` links per rule 2.

skill-verdict: conformance-review-finding-record — applied: invoked; wrote all 8 requirement blocks into this file (and only this file) with the full requirement/spec_ref/verdict/evidence/rationale field set; no block needed spec_vs_built since none verdicted Incorrect.

skill-verdict: implementation-audit — not-applicable: this repo's own conformance-review-* skill family (requirement-extraction, verification-method-selection, verdict-assignment, traceability-and-evidence, finding-record) already governs this exact task with repo-specific mechanics (record path, five-verdict vocabulary, skill-verdict logging) that implementation-audit's generic two-session protocol would only duplicate, not add to — there is also no separate builder session here to hand claims to; this single review session re-executes every check itself against the already-merged commit.

other mounted skills: dataviz, run, code-review, simplify,
security-review, update-config, keybindings-help, claude-api, init,
loop, schedule, freelunch:freelunch-code-fanout,
freelunch:freelunch-site-fanout, terse — not triggered (unrelated to
this review's task).
