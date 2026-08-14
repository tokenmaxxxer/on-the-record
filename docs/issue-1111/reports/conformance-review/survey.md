---
kind: current-state-survey
subject: issue-1111
code_under_review:
- on-the-record/hooks/deliverable-guard.sh
- on-the-record/hooks/product-capture-stopgate.sh
- on-the-record/hooks/test_deliverable_guard.py
- on-the-record/hooks/test_product_capture_stopgate.py
- docs/reports/product/priorities.md
---

# Current-state survey — conformance review of issue #1111 (northpole req#5)

## Background

Issue #1111 cites northpole req#5 ("problems are not pushed back to the
human") as the requirement its fix serves. Board condition (issue-521):
an implementation commit landed on main for this subject with no
conformance-review record yet.

derived: `git log origin/main --oneline | grep issue-1111`, run this
session:
```
57acada8 issue-1111 phase-2: resolve product-capture/deliverable-guard deadlock (#1114)
300e6c63 issue-1111 phase-1: product-capture gate ownership proposal (#1113)
```
canonical: same command output above, run this session — target artifact
for this review is commit 57acada8 (phase-2 delivery, merged via PR
#1114), the landed implementation commit; 300e6c63 is the phase-1
proposal-only commit (no code under `on-the-record/`).

## Method

Read northpole.md §5's requirement text and traceability line, decomposed
it into checkable sub-claims, then located the evidence each sub-claim
needs inside the artifacts commit 57acada8 actually changed plus the
issue-1111 record tree.

## northpole req#5, verbatim

canonical: docs/specs/northpole.md lines 79-95, read this session:
> Problems are not pushed back to the human — a mid-course problem is
> solved by spawning the role-appropriate agent(s) to research AND discuss
> the fix WITH those agents, producing a working deliverable that truly
> satisfies the requirement; the whole process (decisions and discussion
> included) is transparently recorded in the repo.

Traceability line names two mechanisms: `gates/remediation_spawn.py`
(auto-spawn on open remediation finding) and
`on-the-record/hooks/delegated-judgment-gate.sh` (panel auto-approve/
auto-reject, escalating only on missing precondition) plus
`docs/issue-<n>/decisions/` as "the transparent record of the discussion
this requirement demands."

## Derived sub-claims

A. The mid-course problem was solved by spawning role-appropriate
   agent(s) to research the fix (not solved by the human directly).
B. That research included discussion WITH the spawned agent(s), not a
   single one-shot question.
C. The result is a working deliverable that satisfies the requirement
   (the deadlock no longer reproduces).
D. The decisions-and-discussion process is transparently recorded in the
   repo, at the path northpole.md's own traceability line names (a
   per-issue decisions subdirectory).

## Findings

### Sub-claims A and B

canonical: `git show 300e6c63:docs/issue-1111/reports/consult-log.md`, run
this session:
```
- 2026-08-12T17:35:11.815009+00:00 | role=requirements-engineering | issue=1111 | question='Gate 소유권 충돌 해소: ...' | outcome='ok: ...'
```
canonical: same command output above, run this session — one consult
call recorded, one question paired with one outcome: a single
round-trip, not a multi-turn discussion transcript.

derived: `find docs/issue-1111 -type f`, run this session:
```
docs/issue-1111/reports/consult-log.md
docs/issue-1111/reports/implementation.md
docs/issue-1111/proposals/2026-08-13-product-capture-ownership.md
docs/issue-1111/reports/implementation/hunt-product-capture-ownership.md
docs/issue-1111/reports/implementation/survey.md
docs/issue-1111/reports/implementation/2026-08-13-hunt-before-landing.md
docs/issue-1111/reports/implementation/deviation-log.md
```
canonical: same listing above, run this session — two hunt records
(`hunt-product-capture-ownership.md`, `2026-08-13-hunt-before-landing.md`)
are spawned-hunter research artifacts present in the tree; no decisions
subdirectory appears in this listing.

### Sub-claim C

canonical: `git show 57acada8:docs/issue-1111/reports/implementation.md`
Acceptance section, read this session — cites live-executed
`test_deliverable_guard.py` and `test_product_capture_stopgate.py`
passing plus a live hook invocation against a fresh non-board repo.
Independently re-ran below.

derived: `python3 on-the-record/hooks/test_deliverable_guard.py -q`, run
this session:
```
...................                                                      [100%]
19 passed in 0.40s
```
canonical: `python3 on-the-record/hooks/test_deliverable_guard.py -q`
(executed this session, output immediately above) — the live re-run
reproduces the implementation record's cited pass result.

### Sub-claim D

canonical: docs/specs/northpole.md lines 94-95, read this session — the
requirement's own traceability line names a per-issue decisions
subdirectory (pattern `docs/issue-<n>/decisions/`) as where "the whole
process (decisions and discussion included)" must be transparently
recorded.

canonical: the `find docs/issue-1111 -type f` listing quoted under
Sub-claims A and B above, this session — no decisions subdirectory
appears for issue-1111; the decision rationale instead lives inside
`docs/issue-1111/reports/implementation.md`'s "Why" section and the
phase-1 proposal. The content itself is present and legible, but not at
the path the requirement's own traceability names — a candidate for a
phase-2 Present-vs-Incorrect split, not resolved here since phase 1 does
not render verdicts.

## Panel/escalation evidence (delegated-judgment-gate.sh)

canonical: `gh issue view 1111 --json comments`, read this session:
```
Judgment opened: PR #? (5 paths) -> delegated-judgment evaluation
Verdict: PR #? -> escalate (depth or impact axis did not clear)
[watch] PR #1113 opened
APPROVE issue-1111/implementation
Judgment opened: PR #? (12 paths) -> delegated-judgment evaluation
Verdict: PR #? -> escalate (depth or impact axis did not clear)
```
canonical: same comment thread above, this session — both the phase-1 and
phase-2 candidate decisions were routed through delegated-judgment-gate.sh
and both escalated (precondition not met for auto-decision); a human
APPROVE comment closed phase-1's escalation.

canonical: `git log origin/main --oneline | grep issue-1111` output
quoted in the Background section above, this session — PR #1114
(phase-2) is present on main, so its merge is the phase-2 acceptance act
per contract v3's board-is-merged rule; the comment thread quoted above
carries no separate APPROVE-string comment for phase-2.

## Sampling

Single artifact, single cited requirement (northpole req#5) — no sampling
was needed; all four derived sub-claims were checked directly.
