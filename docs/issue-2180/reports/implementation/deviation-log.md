# Deviation log — issue-2180 / implementation

- 2026-08-24T19:15:00+09:00, inline. canonical:
  docs/issue-2180/reports/implementation/2026-08-24-hunt-returned-pr-signal-shape.md
  (the before-landing `warrant-hunter` dispatch, stance 0 — "assume the
  gate just touched is bypassable"). The initial `[new-returned-pr]`
  one-shot marker keyed off the same phase-qualified diff key as the
  plain `[returned-pr]` line diffing, so a phase1->phase2 transition on
  an already-surfaced, still-open PR silently re-fired the marker as if
  it were new — same file already inside scope, mechanical re-keying
  (persisted `surfaced_returned_pr_issues` set keyed by bare `#<issue>`
  token instead), no change to what the deliverable claims to do. Fixed
  and regression-pinned in the same commit before landing.
  on-the-record/monitors/poll-heartbeat.sh (the `returned-pr:` branch
  and the new `surfaced_issues` pruning block) /
  on-the-record/monitors/test_poll_heartbeat.py
  (`t_returned_pr_phase_transition_does_not_refire_new_marker`).
