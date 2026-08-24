# Deviation log — issue #2166 (conformance-review)

- 2026-08-24T08:30:00Z | inline | the phase-1 proposal's step 4 originally
  set the record's overall `result` field by directly substituting REQ-8's
  `Incorrect` finding-verdict as the EARL `result` value `failed` — a 1:1
  swap conformance-review-finding-record's own rule 3.3 explicitly
  disclaims: "the value sets do not map 1:1, this is vocabulary alignment,
  not a swap" (that skill is one this proposal's own "Skill verdicts"
  section marks `applied: invoked`). A background warrant-hunter,
  dispatched after this proposal's first commit per the warrant protocol,
  caught it — its hunt record sits in this same directory, dated
  2026-08-24, filename prefixed `hunt-conformance-review-issue-2166`.

  Fixed inline in
  docs/issue-2166/proposals/2026-08-24-conformance-review-issue-2166.md:
  step 4 now states an explicit verdict-to-result mapping:

  ```
  Present  -> passed
  Surface  -> failed
  Absent   -> failed
  Incorrect -> failed
  Unverifiable -> cantTell
  ```

  and computes `result` as the worst-case across each finding's own
  mapped value, per `roles/specs/conformance-review.spec.json`'s
  `recomputation.rule`. REQ-6 is also split into REQ-6a/REQ-6b (one
  verdict per finding, matching the skill's own "exactly one of five
  verdicts per requirement" rule) so the worst-case rule has one mapped
  value per finding rather than a finding carrying two.

  Stays inside this session's frozen write set (the phase-1 proposal
  file itself, still unapproved); a mechanical vocabulary-alignment fix
  per an explicitly cited rule, no new design/architecture/security
  judgment; does not change any of REQ-1..REQ-8's own individual
  verdicts, only how the top-level `result` is derived from them;
  one-off.
