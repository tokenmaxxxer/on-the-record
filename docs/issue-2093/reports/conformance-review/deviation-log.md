# Deviation log — issue #2093, conformance-review role

- 2026-08-23 | filed | `approval-gate.sh` refuses any phase-1 write to
  docs/issue-2093/reports/conformance-review.md (path-based, unconditional),
  while `skill-verdict-guard.sh` requires the seven mounted skills'
  `skill-verdict:` lines in that same file at Stop. A phase-1
  conformance-review session cannot satisfy both. Worked around by recording
  the seven lines in the phase-1 home —
  docs/issue-2093/proposals/conformance-review-plan.md, `## Skill verdicts`.
  `board-gate.sh` also refuses this role's write to
  docs/issue-2093/reports/deviation-log.md, so this log lives in the role's
  own directory instead. Reported, not spawned.
