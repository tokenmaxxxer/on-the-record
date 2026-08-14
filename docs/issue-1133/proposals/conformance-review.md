---
status: proposed
files:
  - docs/issue-1133/reports/conformance-review.md
---

# issue #1133 — conformance review requirement list

Intent: check whether the merged fix (PRs #1138/#1143/#1149, all landed on
main via issue-1133/implementation) actually delivers what issue #1133
specified, one per-requirement verdict at a time
(Present/Surface/Absent/Incorrect/Unverifiable) — never a holistic
code-quality judgment, never a fix applied here.

Constraints: this is northpole req#1-linked (watchdog signal
trustworthiness) per the issue's own citation; verdicts are checked
against spawn.py and gates/test_watch_rearm_registry.py as they exist in
the current tree, not against the building agent's stated intent in
docs/issue-1133/reports/implementation.md.

## What will be done

Phase 2 (after Approve) records one verdict per line below in
docs/issue-1133/reports/conformance-review.md, working from spawn.py and
the gate test directly:

- R1 — "Re-arm (watch) updates the same registry/roster entry the
  watchdog reads, so a successfully re-armed watcher clears the
  watcher-dead signal on the next tick."
- R2 — "watcher-dead's remediation text names a non-blocking form (no
  --follow, or an explicit note to background it)."
- R3 — "Regression guard: watch-coverage inviolable — the fix must not
  reduce observation (watchdog keeps flagging genuinely dead
  watchers)."
- A1 — "new gate test in gates/ (e.g. test_watch_rearm_registry.py): arm
  a watcher, kill it, re-arm via the watch code path, assert the
  watchdog scan reports no watcher-dead for that entry and the registry
  holds the new pid."
- A2 — "the watcher-dead message string in the watchdog code contains no
  bare --follow instruction (or carries an explicit background note);
  asserted by the same gate test."

Each verdict re-runs `python3 -m pytest gates/test_watch_rearm_registry.py -v`
live rather than trusting the implementation record's pasted transcript,
and reads the current spawn.py source directly for R1–R3/A2. The
survey's two scope notes (WORKSPACE_INDEX's `"issue"`-key omission; the
two residual `--follow`-worded stall/wall-clock strings inside `_watch()`
at spawn.py:3995-3996 and spawn.py:4072-4073) are carried into phase 2 as
explicit scope questions for R1 and R2 respectively, not pre-decided.

## Out of scope

Fixing anything found Absent/Incorrect — findings route back to the
implementation role per the hand-off contract. No code edit to spawn.py
or the gate test happens in this role.

## How it will be known to have worked

The phase-2 record carries exactly one verdict line per requirement
above (5 total), each with a canonical citation to a live-executed
command or a current-tree read, plus the record's own kind/loop_state
and upstream-basis fields per contract v3 s19/§20.

## What did not work

None.
