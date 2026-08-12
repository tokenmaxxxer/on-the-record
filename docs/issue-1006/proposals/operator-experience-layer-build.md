---
status: proposed
files:
  - on-the-record/hooks/directive.sh
  - docs/handbooks/operator-experience.md
  - harness/fixture-operator-experience/test_flow.py
  - harness/fixture-operator-experience/seed_vague.json
  - harness/fixture-operator-experience/seed_precise.json
  - gates/operator_experience.py
---

Subject: issue-1006

## Request

Build blocks A-E of the operator-experience layer exactly as designed in
the merged `docs/issue-1006/proposals/operator-experience-layer.md`
(product-discovery phase-1, PR #1009): first-contact guidance block,
requirement-elicitation trigger, mid-flight narration line, requirement-
traceability at completion, and the `harness/fixture-operator-experience`
end-to-end scenario.

## Constraints

- Skip condition (scout-directive): the spec leaves no design decision
  open. The merged design already names the exact insertion points
  (`directive.sh`'s existing "Requirements become ISSUES" line, the
  TURN-BUDGET RULES arming point, the AUTONOMOUS ASYNC COMPLETION verify
  step), the exact gating mechanism (`.orchestrate-greeted` marker), and
  the exact file/fixture shape to mirror
  (`fixture-requirement-digest` + `gates/requirement_digest.py`). No
  survey or scout pass is run this turn; this proposal cites that skip
  condition instead of re-deriving the design.
- Do not recreate `docs/issue-1006/proposals/operator-experience-layer.md`
  or its survey — this proposal is a thin phase-1 wrapper authorizing
  this role's own branch/PR to build the already-approved design, per
  role-handoff contract v3 s19 (phase-2 build requires an approval act
  scoped to this role's own branch, `issue-1006/implementation`, distinct
  from the approval already given to `issue-1006/product-discovery`).
- Plugin elements only, default-on (issue req#7, carried from the
  upstream design).

## Rationale

Considered building directly without a phase-1 proposal on this branch,
since the design itself was already approved on the product-discovery
branch. Rejected: role-handoff contract v3 s19's phase-2 gate is scoped
per role/branch — the only approval comment found on issue #1006 is
`APPROVE issue-1006/product-discovery`, not `APPROVE issue-1006/implementation`,
and `CORE_BUILD_NOW` is unset in this session's environment, so the
build-now bypass does not apply either. Skipping straight to code would
mean this role authorized its own phase 2, which the contract forbids.
A minimal proposal that references (not repeats) the existing design
keeps the record honest without re-litigating decisions already made.

## What will be done

Once this proposal is approved for `issue-1006/implementation`
specifically, build exactly blocks A-E as specified in the upstream
design doc's "What will be done" section — no reinterpretation:

- **A.** First-contact guidance block appended to `directive.sh`'s
  heredoc, gated by a `.orchestrate-greeted` marker file so it fires
  once per workspace.
- **B.** Elicitation branch inserted before the "Requirements become
  ISSUES" line, routed through `requirements-quality`/`user-discovery`
  per their existing trigger conditions.
- **C.** One narration sentence at the TURN-BUDGET RULES arming point.
- **D.** One clause in the AUTONOMOUS ASYNC COMPLETION verify step citing
  the requirement/issue number the merged PR answers.
- **E.** `harness/fixture-operator-experience/test_flow.py` plus
  `seed_vague.json`/`seed_precise.json`, mirroring the
  `fixture-requirement-digest` pairing shape, plus
  `gates/operator_experience.py` per the frozen write set.
- `docs/issue-1006/reports/implementation.md` recording the build.

## Out of scope

- Redesigning A-E or the upstream design doc.
- Any change to `spawn.py`, role rulebooks, or gate mechanics beyond
  `gates/operator_experience.py` and the fixture pair.
- Panel (#985) composition — still absent from this tree per the
  upstream survey.

## How you'll know it worked

- `harness/fixture-operator-experience/test_flow.py` passes locally,
  demonstrating vague ask -> elicitation -> precise requirement captured
  -> delegated run -> legible narration -> role-verified completion
  report.
- The precise-ask seed skips straight to delegation (empty-state check).

## What did not work

None.
