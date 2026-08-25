# Deviation log — issue-2211/conformance-review

(Written under this role's own subtree per board-gate.sh R5 — a role
session may not write docs/issue-2211/reports/deviation-log.md directly,
only conformance-review.md and conformance-review/**.)

2026-08-25T00:30:00+09:00 | inline | `on-the-record/hooks/skill-verdict-guard.sh`
hardcodes the skill-verdict-line home as this role's phase-2 record path,
docs/issue-2211/reports/conformance-review.md.
canonical: Stop-hook `skill-verdict-guard` output this session, verbatim:
"마운트된 스킬에 skill-verdict 줄이 없다 (issue #2039): 'conformance-review-requirement-extraction'/'conformance-review-sampling-derivation'/'conformance-review-verification-method-selection'
— ... 레코드에 남겨야 한다."
`approval-gate.sh` refuses any write to that phase-2-shaped path this
session, since no `APPROVE issue-2211/conformance-review` comment exists
yet (contract v3 s19).
canonical: this session's own PreToolUse denial, verbatim: "neither the
PR for issue-2211/conformance-review nor issue #2211 carries an approval
from a listed human approver (jiwonjung94, jjongkwann)...phase 2 waits
for the human."
`skill-verdict-guard` runs as an advisory Stop-hook (additionalContext,
not a blocking decision) per this session's own observed hook output
above, and does not block session end, so this deviation is logged
rather than forced past the approval-gate — matching the issue-2156
precedent for this exact conflict.
canonical: `git show 96f9e98d:docs/issue-2156/reports/conformance-review/deviation-log.md`
(read directly, this session).

The three invoked skills are recorded here, under this role's
phase-1-writable subtree, for traceability now, and will be carried into
the phase-2 record once approved. Each already backs specific content in
this session's committed phase-1 files.
canonical: `git show 37cb1d36 --stat` (executed this session) — result:
docs/issue-2211/reports/conformance-review/survey.md and
docs/issue-2211/reports/conformance-review/2026-08-25-hunt-conformance-review.md
both created/updated in that commit (the paired proposal,
docs/issue-2211/proposals/conformance-review.md, landed in the prior
auto-committed `4505728d`).

- `conformance-review-requirement-extraction` — applied: invoked; used
  rule 1 (split issue #2211's bundled "plugin-root, core-root,
  skill-registry, and workspace paths" clause into R1-R4) and rule 2
  (flagged R9's undefined "engineering-class session" term as
  unverifiable-as-written), reflected in survey.md's requirement list.
- `conformance-review-sampling-derivation` — applied: invoked; used
  rule 5 (exempt the highest-impact tier from sampling) to derive the
  full-enumeration, zero-sampling scope stated in survey.md's "Sampling
  scope" section.
- `conformance-review-verification-method-selection` — applied: invoked;
  used rule 1 (Inspection for structural env-dict assignments), rule 3
  (Demonstration for the two live-spawn-only requirements, R6-R8), and
  rule 4 (reuse existing unit tests rather than re-deriving parallel
  manual checks) to assign a method per requirement in survey.md's
  "Verification method per requirement" section.

`conformance-review-traceability-and-evidence`,
`conformance-review-verdict-assignment`, `conformance-review-finding-record`,
and `conformance-review-severity-classification` were judged
not-applicable this session (each is a phase-2 concern per their own
trigger text — rendering verdicts and citing evidence against a
requirement happens once approved, not during phase-1 requirement
extraction) and were never invoked via the Skill tool, so per issue
#2153's scoping they owe no line here.
