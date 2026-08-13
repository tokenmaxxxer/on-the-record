---
status: proposed
files:
  - docs/issue-1129/reports/product-discovery.md
---

# issue-1129: unused-role diagnosis (proposal)

kind: proposal
subject: issue-1129

Proposal: docs/issue-1129/proposals/unused-role-diagnosis.md

## Intent

Deliver the measured diagnosis issue #1129 asks for: classify each of
the 33 zero-record roles into a candidate cause (workload never
triggers domain / routing absorbs the domain into implementation /
consult-path friction / no standing duty wired), with per-cause counts
recomputable from `docs/issue-*/reports/` and `consult-log.md` (the
issue-named `runs/ledger.jsonl` does not exist in this tree — see
current-state survey), plus an IS/IS-NOT contrast naming at least 3
discriminating factors between the 10 used and 33 unused roles. Read
evidence: `docs/issue-1129/reports/product-discovery/survey.md`.

## Constraints stated so far

- No remedy work in this issue (issue body, explicit) — remediation is
  #1130's scope; this record classifies causes only.
- Acceptance requires the classification table and IS/IS-NOT section to
  land in `docs/issue-1129/reports/product-discovery.md`, with table
  figures recomputable by a committed aggregation approach over
  `runs/ledger.jsonl` and `docs/issue-*/reports/`. Since
  `runs/ledger.jsonl` does not exist, the record instead cites the exact
  `find`/`python3` commands run against `docs/issue-*/reports/` and
  `consult-log.md` that produced each count — reproducible the same way,
  against the data sources that actually exist.
- Roles whose cause cannot be separated from available data must be
  listed with what instrumentation would be needed (issue's own empty-
  state acceptance line) — the survey already identifies this gap for
  cause (b)'s 6 roles and cause (d)'s 14 roles (no orchestrator-side
  routing log exists to distinguish "never considered" from "considered
  and passed over").
- Per contract v3 s19, phase-1 output stays inside
  `docs/issue-1129/reports/product-discovery/` and
  `docs/issue-1129/proposals/`; the acceptance-required record file
  `docs/issue-1129/reports/product-discovery.md` is phase-2 output and
  waits for human Approve.

## Pre-registration (this issue's decision rule)

This issue is a measurement task, not a go/kill/pivot product bet — the
registered rule below governs whether the diagnosis itself is complete,
not a future product decision.

- **Metric**: fraction of the 33 unused roles assigned to exactly one
  named cause ((a)/(b)/(c)/(d), or an explicitly-labeled
  "insufficient instrumentation" empty state per the issue's own
  allowance), each backed by a `derived:`-cited, recomputable count.
- **Threshold**: 33/33 (100%) — every unused role must land in the
  table, no role omitted and none double-counted (cause counts must sum
  to exactly 33).
- **Decision rule**: threshold met → diagnosis is `validated` and ready
  to hand off as scoping input to #1130. Threshold not met (a role
  neither classified nor explicitly logged as an empty state) →
  `invalidated`, record what blocked it, phase 2 does not close.
- **Guardrail metric**: cause counts must sum to exactly 33 (no
  role counted in more than one cause) — a table that reaches 33/33
  coverage but double-counts a role is a reduced-trust result, not a
  clean pass, and must be corrected before the record can read
  `validated`.
- **Pre-committed ITWWS follow-up**: if this validates cleanly (all 33
  classified, sums correct), the next action is filing/scoping issue
  #1130 against exactly the per-cause groupings this record produces —
  not a fresh re-diagnosis.

The survey (`docs/issue-1129/reports/product-discovery/survey.md`)
already reaches 33/33 classified (13 cause-a, 6 cause-b, 0 cause-c, 14
cause-d, summing to 33) with every count backed by a `derived:` line.
Phase 2 copies that classification into the acceptance-required record
file and applies this rule mechanically: 33/33 achieved, sums correct →
`validated`.

## Guardrail metrics

- Cause-count sum guardrail (see above): 13+6+0+14 = 33, checked
  arithmetically in the survey and re-checked in phase 2's record.
- Citation guardrail: every count claim in the phase-2 record must carry
  a `derived:` or `canonical:` tag per this repo's own
  `record-claim-guard.sh` — the survey was written under that same gate
  and passed it, so phase 2 reuses its exact phrasing rather than
  re-deriving new prose that could drop a citation.

## Evidence citations (Mom Test / observation, not preference)

All evidence backing the classification is repo-internal, machine-read
artifacts (spec files, board record file listings, hook classifications
in `docs/specs/role-invariant-coverage.md`) — not stated preference or
hypothetical response, so the Mom Test admissibility question does not
apply the way it would to interview data. Each count in the survey cites
the exact command or file read that produced it (see survey's `derived:`
/`canonical:` tags).

## What will be done (phase 2, on Approve)

1. Copy the survey's classification table, IS/IS-NOT section, and
   empty-state note into `docs/issue-1129/reports/product-discovery.md`,
   with `kind: record`, `loop_state: validated` (per the pre-registered
   rule above, since 33/33 is already reached), citing this proposal as
   upstream basis.
2. State the guardrail check result (sum = 33) explicitly next to the
   metric value, per this role's execution-judgment quality bar.
3. Action the pre-committed ITWWS follow-up by stating, in the record's
   next-steps, that #1130 should scope remediation against the four
   cause groupings produced here — filing #1130 itself is out of scope
   for this session (a role session does not open issues on its own
   initiative).

## Out of scope (this proposal)

- Any remedy: adding hooks, wiring standing duties, changing routing,
  or reducing consult friction. That is #1130's scope per the issue
  body.
- Building the missing `runs/ledger.jsonl` instrumentation — its
  absence is documented as a finding, not fixed here.
- Re-deriving counts phase 2 hasn't already reproduced in the survey —
  phase 2 copies and re-verifies the survey's own commands, it does not
  invent a new methodology.

## How we'll know it worked

- `docs/issue-1129/reports/product-discovery.md` exists with a
  33-row-covering classification table, an IS/IS-NOT section naming
  >=3 discriminating factors, and passes `record-claim-guard.sh` /
  `record_lint.py` on write (mechanical: the write itself fails loudly
  if a claim is uncited, so a landed record proves the citation
  guardrail held).
- Cause-count arithmetic in the landed record sums to 33.
