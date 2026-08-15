kind: deviation-log
subject: issue-1199

- 2026-08-14T01:34Z, filed, `gh pr create` on issue-1199/ux-engineering
  raced pr-preflight.sh's amendments-reconciled gate indefinitely
  against a burst of watchdog "Judgment opened"/"Verdict: PR #? →
  escalate" comments not matched by `_MACHINE_BODY_RE` — reported,
  not spawned; see docs/issue-1199/reports/ux-engineering.md Open
  findings.
- 2026-08-15T00:51Z, filed, same PR-gate race recurred on the
  2026-08-14 plugin-ecosystem rework's `gh pr create` attempts (both
  the on-the-record repo PR and the ux-engineering-rulebook repo PR,
  which shares the same mounted pr-preflight.sh hook) — issue #1199 is
  a high-traffic thread with many concurrent role sessions posting the
  same unmatched watchdog comment shape every ~15-90s, so live
  reconciliation cannot converge faster than new comments land.
  Reported, not spawned; commits for both repos are pushed to origin
  regardless. See Open findings in
  docs/issue-1199/reports/ux-engineering.md.
