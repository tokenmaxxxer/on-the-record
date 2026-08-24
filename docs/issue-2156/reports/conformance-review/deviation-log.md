# Deviation log — issue-2156/conformance-review

(Written under this role's own subtree per board-gate.sh R5 — a role
session may not write docs/issue-<n>/reports/deviation-log.md directly,
only <role>.md and <role>/**.)

canonical: this session's own PreToolUse hook output when it attempted a
`Write` to this role's phase-2 record path earlier this turn —
`approval-gate: no matching 'APPROVE issue-2156/conformance-review'
issue comment ... found ... this phase-2-shaped write ... needs phase-2
approval first.`

2026-08-24T15:40:00+09:00 | inline | `on-the-record/hooks/skill-verdict-guard.sh:326`
(read directly this session) hardcodes the skill-verdict-line home as
this role's phase-2 record path.
canonical: `on-the-record/hooks/skill-verdict-guard.sh` line 326 (read
directly this session).
`approval-gate.sh` refused that exact `Write` this session (canonical
tag above) because no `APPROVE issue-2156/conformance-review` comment
exists yet — phase-2 is gated behind human Approve per contract v3 s19.
`skill-verdict-guard.sh` is advisory-only
(`additionalContext`, never `decision: block`) per its own header
comment, read directly this session, and does not gate session end, so
this deviation is logged rather than forced past the approval-gate.

The six invoked skills are recorded here, under this role's
phase-1-writable subtree, for traceability now, and will be carried
into the phase-2 record once approved. Each already backs specific
content in this session's committed phase-1 files.
canonical: `git show fca59e11 --stat` (executed this session) — result:
`docs/issue-2156/proposals/conformance-review.md`,
`docs/issue-2156/reports/conformance-review/survey.md`,
`docs/issue-2156/reports/conformance-review/2026-08-24-hunt-conformance-review.md`
all created in that commit.

- `conformance-review-requirement-extraction` — applied: invoked; used
  rule 1 (split issue #2156's Change paragraph into R2-R6, one
  obligation per line) and rule 6 (dimension-tagged R1-R8) to build the
  requirement list committed in `fca59e11`'s survey.md.
- `conformance-review-verification-method-selection` — applied: invoked;
  used rule 1 (Inspection for R1-R7, structural text-presence) and rule 4
  (reuse an existing check rather than re-deriving a parallel manual one
  for R8's grep), reflected in `fca59e11`'s proposal.md.
- `conformance-review-verdict-assignment` — applied: invoked; used rule 3
  (re-derive from the artifact directly, not the builder's self-report)
  as the basis for `fca59e11`'s proposal.md Rationale, which rejects
  trusting the implementer's own Acceptance-evidence section on its own.
- `conformance-review-traceability-and-evidence` — applied: invoked; used
  rule 1 (file:line-range + commit sha, not a bare path) as the citation
  shape stated for phase 2 in `fca59e11`'s proposal.md.
- `conformance-review-finding-record` — applied: invoked; used the field
  list (requirement/spec_ref/verdict/evidence/rationale) to shape the 8
  requirement items in `fca59e11`'s survey.md, ready for phase 2 to fill
  with verdicts.
- `implementation-audit` — applied: invoked; its two-session evaluator
  framing backs `fca59e11`'s proposal.md Rationale, which re-derives
  verdicts directly against the artifact rather than accepting the
  implementer's own self-assessment.

`conformance-review-sampling-derivation` and
`conformance-review-severity-classification` were judged not-applicable
this session (stated in `fca59e11`'s survey.md/proposal.md reasoning)
and were never invoked via the Skill tool, so per issue #2153's scoping
they owe no line here.
