# Deviation log — issue-2331 / conformance-review

- 2026-08-25T05:10:00Z | inline | did not delegate any repo/env Bash or
  Read calls to a background `freelunch:freelunch-worker` despite the
  freelunch-protocol directive's mechanical "any repo/env tool call:
  DELEGATED, always" rule for a single (width-1) unit — this task's
  substance is independent verification/judgment (re-deriving evidence
  against real historical commits, writing adversarial fixtures, applying
  the mounted conformance-review-* skills, builder-blind reasoning that
  must stay internally consistent across one session) which a
  freelunch-worker cannot do (it is directed to "skip verification and
  deliver raw"); per contract v3 s22's explicit headless-session
  alternative ("wait for the delegated result ... or do not delegate that
  unit at all"), chose not to delegate and ran every step inline instead.
  No separate fix issue filed — a one-session procedural choice, not a
  defect in the delivered record.
- 2026-08-25T05:10:00Z | inline | did not dispatch a background
  `warrant:warrant-hunter` before landing. The write set was a single new
  file under `docs/issue-2331/reports/` (plus an auto-appended
  `.orchestrate-hook-fires.log` line) — every touched path under `docs/`
  qualifies for the warrant-protocol's own "DOCS-ONLY FAST PATH: ... the
  before-landing dispatch is skipped," and there was no after-proposal
  transition to dispatch from either (build-now bypass, no proposal
  round). The directive's own text asks that a fast-path skip still
  "append a section to the hunt record naming the reason" so the skip is
  never silent; no dedicated hunt-record file was created for that
  skip-line at landing time — this entry is that missing record, filed
  after the fact rather than at the moment of the skip. No separate fix
  issue filed.
