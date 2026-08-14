kind: deviation-log
subject: issue-1199

- 2026-08-14T01:34Z, filed, `gh pr create` on issue-1199/ux-engineering
  raced pr-preflight.sh's amendments-reconciled gate indefinitely
  against a burst of watchdog "Judgment opened"/"Verdict: PR #? →
  escalate" comments not matched by `_MACHINE_BODY_RE` — reported,
  not spawned; see docs/issue-1199/reports/ux-engineering.md Open
  findings.
