---
kind: current-state-survey
subject: issue-1117
code_under_review:
- on-the-record/monitors/poll-heartbeat.sh
- gates/test_poll_heartbeat_delta.py
- docs/issue-1117/decisions/priorities.md
- docs/issue-1117/reports/implementation.md
- docs/issue-1117/reports/implementation/deviation-log.md
---

# Current-state survey — conformance review of issue #1117 (poll-heartbeat delta-suppression)

## Background

canonical: `gh issue view 1117`, read this session — closed issue, Requirements/Acceptance sections quoted verbatim below.

canonical: `gh pr view 1122 --json mergeCommit,files,state,title,body`, read this session — PR #1122 (branch `issue-1117/implementation`), merged as commit `1a259a653d9b149b5b82cc813bcc94fc47b15ea0`, 5 files changed.

No prior conformance-review record exists for this subject.

derived: `find docs/issue-1117 -type f`, run this session:
```
docs/issue-1117/reports/implementation.md
docs/issue-1117/decisions/priorities.md
docs/issue-1117/proposals/poll-heartbeat-delta-suppression.md
docs/issue-1117/reports/implementation/hunt-poll-heartbeat-delta-suppression.md
docs/issue-1117/reports/implementation/survey.md
docs/issue-1117/reports/implementation/deviation-log.md
```

## Requirement list (extracted verbatim from issue #1117)

- **Req-1 (suppression)**: "Suppress the Monitor notification/interject on a due tick whose captured watchdog output is unchanged from the previous emitted tick (e.g. hash comparison persisted next to the poll TTL stamp)."
- **Req-2 (coverage floor, #90)**: "A tick whose output differs in any way MUST emit — no coverage regression (watch-coverage inviolable, #90)."
- **Req-3 (cadence-relax, stated as "may")**: "When zero role sessions are running AND board signals are unchanged, cadence may be relaxed; first tick after any change always emits."
- **Req-4 (priority record)**: "Record the operator priority ordering above as a structured entry in docs/product/priorities.md (discharges the product-capture-stopgate flag ...)."
- **Req-5 (acceptance test)**: "gates/test_poll_heartbeat_delta.py (new): drives monitors/poll-heartbeat.sh via POLL_HEARTBEAT_MAX_TICKS/POLL_HEARTBEAT_SLEEP_SECONDS with (a) two consecutive identical watchdog outputs — second tick emits nothing; (b) changed output — emits; (c) change-after-suppression — emits."
- **Req-6 (empty-state acceptance)**: "empty state: first-ever tick (no stored hash) must emit — covered by the test's fresh-state case."

Six requirement items, no sampling — full set reviewed (issue is small: 4 Requirements bullets + 2 Acceptance bullets, folded into 6 above since the acceptance bullets each name a distinct test case already covered 1:1 by Req-5's sub-clauses).

## Current-state facts (no verdict — phase 2 only)

canonical: on-the-record/monitors/poll-heartbeat.sh's due-tick branch, read this session — computes `new_hash` over the exact printed text (report or the rc-fallback line), compares to `prev_hash` read from `runs/poll_heartbeat_last_hash`, and only `printf`s the tick and rewrites the hash file when the hashes differ, per the diff below.

derived: `git diff c5bc2052 024056a4 -- on-the-record/monitors/poll-heartbeat.sh`, run this session (c5bc2052 = merge parent before, 024056a4 = branch tip merged in):
```
+    hash_state_file="${CHECKOUT}/runs/poll_heartbeat_last_hash"
+    new_hash="$(printf '%s' "${printed_text}" | sha256sum | cut -d' ' -f1)"
+    prev_hash=""
+    if [ -f "${hash_state_file}" ]; then
+      prev_hash="$(cat "${hash_state_file}" 2>/dev/null || true)"
+    fi
+    if [ "${new_hash}" != "${prev_hash}" ]; then
+      printf '%s\n' "${printed_text}"
+      mkdir -p "${CHECKOUT}/runs" 2>/dev/null
+      printf '%s' "${new_hash}" >"${hash_state_file}" 2>/dev/null || true
+    fi
```

derived: `git worktree add /tmp/otr-1117-check 1a259a65`, then `python3 gates/test_poll_heartbeat_delta.py && python3 on-the-record/monitors/test_poll_heartbeat.py`, run this session against that worktree (the exact merge commit, not the current branch tip):
```
4/4 passed
5/5 passed
```
canonical: same executed transcript above, run this session — both suites pass at the commit under review, matching PR #1122's stated test plan.

derived: `python3 gates/test_poll_heartbeat_delta.py` and `python3 on-the-record/monitors/test_poll_heartbeat.py`, re-run this session against the current branch tip (not the merge commit):
```
gates/test_poll_heartbeat_delta.py: 13/13 passed
on-the-record/monitors/test_poll_heartbeat.py: 3 failed of 8 (t_heartbeat_attaches_on_board_repo, t_heartbeat_refuses_to_arm_on_non_git_root, t_heartbeat_skips_attachment_on_non_board_repo)
```
canonical: `git log --oneline -- on-the-record/monitors/test_poll_heartbeat.py`, run this session — the failures above trace to commits `c490bc47` (issue-1245 board-gate attachment) and `bc32816c` (non-git-root refusal), both landed after `1a259a65`; unrelated to issue-1117's own change set.

canonical: docs/issue-1117/decisions/priorities.md, read this session — contains the operator priority ordering (watch-coverage inviolable #90 > delta-suppression #1117 > `ORCHESTRATE_OFF=1` last resort). The issue text names a different target path for this record:
```
docs/product/priorities.md
```

canonical: docs/issue-1117/reports/implementation/deviation-log.md, read this session — records the path shown in the fence above as substituted for docs/issue-1117/decisions/priorities.md, reason given: board-gate.sh refuses that layout.

canonical: `gh issue view 1117 --comments`, read this session — an `APPROVE issue-1117/implementation` comment from account `JiwonJung94`, followed by a reply accepting the proposal as written and naming the plain-sibling-file hash location as sound. Whether that account is listed in `docs/specs/approvers.md` is out of scope for this requirement-list survey — #1117's own requirements are about delta-suppression behavior, not approval-channel conformance.

## What did not work

None.
