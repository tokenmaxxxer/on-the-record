---
kind: product-discovery-record
loop_state: invalidated
---

# Record — issue #586, product-discovery phase-2

## What was done
Attempted to execute the phase-1 proposal's only ask — file the four
tracking issues the proposal names (batch two, batch three, batch
four, batch five) — in the RICE order the proposal set: batch five
first, then batch two and batch four, then batch three. Every
`gh issue create` call was refused before execution by this session's
own `gh-guard.sh` PreToolUse hook.

canonical: gh-guard.sh PreToolUse hook output, this session, verbatim:
"gh-guard: refused for role session 'product-discovery': issues are
the user's requirement backlog, user-authored only (contract v3 s9) —
no role touches them. (two-account model, contract v3 s8)".

code_under_review:
- docs/issue-586/proposals/product-discovery.md
- docs/issue-586/reports/product-discovery/deviation-log.md

## Why
The role-handoff contract (v3 s9, two-account model) reserves GitHub
issue creation to the user only — no role session may file one, a
constraint enforced mechanically at the tool layer, not just
documented. The proposal's hypothesis assumed filing was within this
proposal's own execution authority; that assumption did not hold once
the actual tool call was attempted.

## Upstream basis
docs/issue-586/proposals/product-discovery.md — canonical: PR #991 on
GitHub, state MERGED, per `gh pr list --head issue-586/product-discovery
--state all` output read this session — approved by the exact-string
issue comment "APPROVE issue-586/product-discovery" on issue #586.

## Measured value vs. threshold
Metric: count of new open GitHub issues cross-referencing #586 for the
four target batches, beyond the pre-existing set.
derived:
```
$ gh issue list --search "586" --state all --json number,title
```
Output (this session): eight issues total, none of them a new
batch-tracking issue for this proposal's four targets. Measured value:
zero. Threshold: four. Zero does not meet threshold four.

canonical: same `gh issue list --search "586" --state all --json
number,title` output cited in the derived block above.
Guardrail metric: no filed issue reopens the fixed five-axis
vocabulary or reassigns an existing axis owner. Zero issues were
created by this session, so no issue text exists to breach the
guardrail. Guardrail status: not breached.

## Decision (mechanical application of the registered rule)
The registered "go" branch required reaching the threshold within this
proposal's own execution; the derived block above shows that did not
happen. The registered "kill" branch was marked not applicable at
registration on the assumption that filing was always executable by
this session — that assumption is what failed: the action was never
executable by this role, independent of reversibility. The pivot
condition (a candidate role objecting to its own axis assignment) does
not apply either, since no issue was filed for any role to review.
Mechanical result: invalidated.

## Opportunity-solution tree disposition
Outcome: the #573 delegated-judgment gate renders trustworthy panels
across all axis-owning roles. Opportunity: issue #586's remaining
scope (rulebook procedures for the newly-assigned axis owners, plus
the multi-role panel fixture) has no tracking issue, so it cannot
progress independently of this proposal's own PR. Candidate solution:
file tracking issues to make that opportunity independently trackable.
Discriminating assumption test: "this proposal's own execution can
file the issues" — tested directly via `gh issue create` this session.
canonical: gh-guard.sh PreToolUse hook output quoted above ("gh-guard:
refused for role session 'product-discovery' ... no role touches
them"). Test result: failed. Disposition: pruned as a self-executable
branch — this session cannot promote the candidate solution by acting
on it directly. The opportunity itself is not pruned: it moves one
layer up, to a "user files the tracking issues" branch, carrying the
candidate-solution content (the ready-to-file issue text below)
forward unchanged for that branch to consume.

## ITWWS
Deferred, with reason: the pre-committed follow-up — re-run the
current-state survey once the tracking issues exist — cannot be
actioned this session.
derived: `gh issue list --search "586" --state all --json number,title`
(same command cited above) — zero of the four target issues exist yet,
so the precondition is unmet. Deferred until the user, the only
account contract v3 s9 permits to file issues, files them using the
content below; the ITWWS re-survey becomes actionable at that point.

## Ready-to-file issue content (for the user to file; not filed by this session)
RICE order per the proposal: batch five first, then batch two and
batch four (tied), then batch three.

1. **issue-586 batch five: multi-role panel fixture for the #573 delegated-judgment gate** — extend the delegated-judgment gate's test fixture beyond the two-role seed (architecture, security-threat-model) to three-plus axis-owning roles on one decision, verifying issue #586's third acceptance criterion. Owner: conformance-review's own step three. Refs #586.
2. **issue-586 batch two: conformance-review alignment axis-evaluation procedure** — rulebook READ/EXECUTE/CRITERIA/CITATION procedure for the alignment axis, per the #573/#189 shapes. Cross-repo (rulebook repo). Refs #586.
3. **issue-586 batch four: performance-engineering performance axis-evaluation procedure** — same shape, the performance axis. Cross-repo. Refs #586.
4. **issue-586 batch three: capacity-planning external_burden axis-evaluation procedure** — same shape, the external_burden axis; defer to capacity-planning's own judgment first if it contests the axis assignment. Cross-repo. Refs #586.

## Open findings
- gh-guard.sh's role-session issue-creation block is a hard contract
  constraint (v3 s9), not specific to this proposal.
  canonical: gh-guard.sh PreToolUse hook output quoted above. Any
  future product-discovery, or other role, proposal whose deliverable
  is filing a GitHub issue will hit the same refusal; the proposal did
  not anticipate this at pre-registration time.

## Next steps
- The user files the ready-to-file issues above.
- A later product-discovery iteration, once those issues exist,
  re-runs the current-state survey per the deferred ITWWS.

## Resolution path
User reviews this record's "Ready-to-file issue content" section and
either files the issues directly, or asks a later session to do so
under an account permitted by contract v3 s9.

## What did not work
Attempted `gh issue create` for all four batches, twice — once with a
literal proposal-path reference that a separate methodology gate also
rejected, once without that reference — and both attempts were refused
by gh-guard.sh's role-session issue-creation block before any issue
was created. No workaround was attempted or applied: the block is a
contract-level restriction, not a bug to route around.
