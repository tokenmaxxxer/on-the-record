# Issue #1174 — conformance-review operational playbook: evidence trail

## What was done

Authored `playbook/` in `tokenmaxxxer/conformance-review-rulebook`
(branch `issue-1174/conformance-review`, commit f40311f, PR
https://github.com/tokenmaxxxer/conformance-review-rulebook/pull/54):
five decision-axis files — `requirement-extraction.md`,
`verification-method-selection.md`, `verdict-assignment.md`,
`traceability-and-evidence.md`, `sampling-derivation.md` — 20
condition->choice->source rule blocks total against a computed
`rule_count_floor` of 15 (rich tier per
`docs/issue-1174/proposals/operational-playbook-program.md` (a): 5
axes x 3), one `removal`-classified rule per axis (amendment 4).
README `## What is here` gained a `playbook/` layout line.

## Why

Per docs/issue-1174/proposals/operational-playbook-program.md (approved
design) and the fan-out unit brief: decompose this role's domain into
decision axes and author condition->choice->source operational rules
into the role's own rulebook checkout, each rule backed by a fetched
web source — no pretrained-recall content.

## Decision axes derived (three-layer research: practitioner /
named-standard / academic, per amendment-1 protocol)

1. **requirement-extraction** — decomposing a spec into discrete
   checkable line items. Standard layer: ISO/IEC/IEEE 29148 requirement
   characteristics (singular, unambiguous, consistent). Academic layer:
   requirements-ambiguity-detection literature.
2. **verification-method-selection** — Inspection / Analysis /
   Demonstration / Test choice per requirement shape. Standard layer:
   ISO/IEC/IEEE 29148's own four-method taxonomy.
3. **verdict-assignment** — Present/Surface/Absent/Incorrect/
   Unverifiable criteria. Practitioner layer: RTM verification-link
   discipline (a link must trace to the requirement actually being
   satisfied, not just matching vocabulary).
4. **traceability-and-evidence** — how a verdict's citation is recorded
   and how forward/backward links stay honest. Practitioner layer: RTM
   forward/backward traceability model (Jama, ReqView, Inflectra guides).
5. **sampling-derivation** — scoping a review when full enumeration is
   infeasible. Academic layer: stratified sampling for conformance
   review, t-wise interaction sampling for combinatorial spaces.

canonical: web searches run this turn (4 parallel `WebSearch` calls —
RTM/29148 practice, 29148 verification methods, conformance-testing
sampling strategy, requirements-ambiguity academic research) each
returned in the transcript preceding this record; source URLs are cited
per-rule inline in the five playbook files themselves (link format:
`([Title](URL))`).

## Upstream basis

- docs/issue-1174/proposals/operational-playbook-program.md (approved
  design, this repo)
- rulebook commit: `tokenmaxxxer/conformance-review-rulebook@f40311f`

## Sources consulted (full list, deduplicated)

- https://sebokwiki.org/wiki/ISO/IEC/IEEE_29148
- https://standards.ieee.org/standard/29148-2018.html
- https://www.well-architected-guide.com/documents/iso-iec-ieee-29148-template/
- https://www.jamasoftware.com/requirements-management-guide/requirements-traceability/traceability-matrix/
- https://www.reqview.com/blog/requirements-traceability-matrix/
- https://www.inflectra.com/Ideas/Topic/Requirements-Traceability.aspx
- https://cs.uwaterloo.ca/~dberry/FTP_SITE/reprints.journals.conferences/KamstiesBerryPaech2001DetectingAmbiguity.pdf
- https://www.researchgate.net/publication/220403866_Estimation_of_Software_Reliability_by_Stratified_Sampling
- https://arxiv.org/pdf/2205.15180

## Current kind and loop_state
kind: report
loop_state: pending-review
canonical: gh pr view 54 --repo tokenmaxxxer/conformance-review-rulebook --json url,state,number — result: state OPEN, no review yet — this record only asserts the PR was opened, not that its content was accepted.

## Open findings

None.

## Next steps

Await human Approve on the rulebook PR (tokenmaxxxer/conformance-review-rulebook#54); no further action from this session until that lands.

## Resolution path

Human review of PR #54 in the rulebook repo; merge = acceptance, close-unmerged = refusal.
