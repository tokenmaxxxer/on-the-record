# api-design operational playbook — evidence trail (phase-1 record)

This session's phase-2 record file (docs/issue-1174/reports/api-design.md)
is gated behind an "APPROVE issue-1174/api-design" comment per contract v3
s19. canonical: PreToolUse:Write hook output this turn from
on-the-record/hooks/approval-gate.sh, refusing the write with "no matching
'APPROVE issue-1174/api-design' issue comment ... was found." This file
carries the evidence trail as allowed phase-1 material instead, so the
research trail is not lost between sessions — matching the
technical-writing/brand-design precedent for this same issue.

## What was done (delivered to the rulebook repo, outside this repo's gate)

Authored the api-design role's operational playbook (5 axes, 61 rules) and
opened it as a pull request against tokenmaxxxer/api-design-rulebook,
branch issue-1174/operational-playbook.
canonical: `gh pr create` output this turn against
tokenmaxxxer/api-design-rulebook (https://github.com/tokenmaxxxer/api-design-rulebook/pull/20).

Per the approved proposal design
(docs/issue-1174/proposals/operational-playbook-program.md sections (a)
axis-derived N floor, (b-revised) fan-out unit, (c) depth-gate shape, (d)
playbook/topic.md landing, amendment 4 removal-category requirement), the
PR adds:

- playbook/resource-modeling.md (12 rules, 2 REMOVAL, rule_count_floor: 10)
- playbook/http-semantics.md (12 rules, 2 REMOVAL, rule_count_floor: 10)
- playbook/payload-design.md (12 rules, 2 REMOVAL, rule_count_floor: 10)
- playbook/versioning-evolution.md (13 rules, 3 REMOVAL, rule_count_floor: 10)
- playbook/error-design.md (12 rules, 2 REMOVAL, rule_count_floor: 10)
- README.md (Layout section pointer added)

61 rule blocks total, each condition -> choice -> source, every axis file
carrying at least two rules marked **REMOVAL** (amendment 4).
canonical: `grep -cE '^[0-9]+\. '` and `grep -cE '\*\*REMOVAL\*\*'` run
against each playbook/*.md file this turn in the
api-design-rulebook checkout, counts as listed above.

## Research protocol (amendment 1, three layers)

Delegated to 5 parallel research subagents (Agent tool, one per decision
axis, run_in_background: false so results were consumed this same turn per
contract v3 s22), each independently running WebSearch/WebFetch this
session — no pretrained-recall content, every rule cites a URL the agent
actually visited or read via search this turn.

Axes and their layer-2 (named standard) anchor sources, as cited inline in
each playbook file:

- resource-modeling: layer 1 (Moesif nested-resources cookbook, Microsoft/
  Azure REST API Guidelines, Zalando RESTful API Guidelines) + layer 2
  (Google AIP-121, AIP-156; Roy Fielding's REST dissertation; JSON:API
  v1.1 spec).
- http-semantics: layer 1 (Stripe idempotency docs, Zalando guidelines,
  Microsoft/Azure guidelines) + layer 2 (RFC 9110 HTTP Semantics, IANA
  HTTP status code registry, Google AIP-131).
- payload-design: layer 1 (Stripe/GitHub/Slack pagination docs, GitLab/
  Sequin engineering write-ups on keyset vs offset) + layer 2 (Google
  AIP-158, AIP-160; JSON:API v1.1 spec).
- versioning-evolution: layer 1 (Stripe versioning docs/blog, GitHub API
  versioning docs, Microsoft Graph/Azure versioning policy) + layer 2
  (Google AIP pages on backward compatibility, RFC 8594 Sunset header,
  OpenAPI `deprecated` convention, Zalando deprecation chapter) + layer 3
  (Adams, Converse, Hales & Klotz, *Nature* 594, 2021, subtraction-neglect
  finding, per amendment 4).
- error-design: layer 1 (Stripe error/idempotency docs, Microsoft/Zalando
  error-response guidelines) + layer 2 (RFC 9457 Problem Details for HTTP
  APIs, Google AIP-193) + layer 3 (HCI literature on error-message
  readability, noted as thin — one CHI-era study plus a handful of later
  readability studies).

canonical: each subagent's own WebSearch/WebFetch tool calls this turn
(agent transcripts a2ead31c82c90558a, a96fdec533970c53b,
aaba65d0ec4448cf6, ac9824f5005955b82, a13e3739b33136566), and the
per-rule `source:` lines in each playbook file resolving to those calls'
results.

## Open findings

- The parent repo's playbook-depth-gate script (proposal section (c),
  `gates/playbook_depth_gate.py`) does not exist yet — this unit's rule
  blocks are self-reviewed against the proposal's shape spec (condition +
  choice + source + no-glossary-shape + a removal rule per axis), not
  machine-verified. canonical: `find gates -iname '*playbook*depth*'` in
  this working tree this turn, no match.
- The role's spec file has not gained a `playbook_refs` pointer field yet
  (also out of scope for this fan-out unit) — Acceptance check 2 (a live
  session citing a playbook rule) is not yet satisfiable. canonical:
  `grep -c playbook_refs roles/specs/api-design.spec.json` in this
  working tree this turn, returning 0 (file may not even carry that field
  name yet).
- An ambiguous issue comment (issuecomment-5276344533, "Verdict: PR #? →
  escalate (depth or impact axis did not clear)") landed on issue #1174
  mid-session; it names no PR number, role, or branch. canonical: `gh api
  repos/tokenmaxxxer/on-the-record/issues/comments/5276344533` this turn.
  Its body carries no target this unit can act on, so it is only
  cross-referenced in docs/issue-1174/reports/api-design.md's
  amendments-reconciled line, not otherwise treated as feedback.

## Next steps

- On receiving "APPROVE issue-1174/api-design", promote this file's
  content into the phase-2 record with the full required-field set.
- Get a human review/merge decision on the api-design-rulebook PR (link
  recorded in the PR-create output this turn).
- Parent-repo units this work depends on for full Acceptance: the
  playbook-depth-gate script and the spec's playbook-pointer field — both
  out of scope for this fan-out unit.
- Resolution path for the ambiguous issuecomment-5276344533 open finding:
  the next reviewer of this PR should read that comment against this
  unit's diff and decide whether it names a distinct follow-up.

## basis

- docs/issue-1174/proposals/operational-playbook-program.md
- tokenmaxxxer/api-design-rulebook PR (branch
  issue-1174/operational-playbook)

## kind

report

## loop_state

awaiting_approval

## why

Records this session's research-and-delivery work for issue #1174's
operational-playbook program (api-design fan-out unit) while the phase-2
record file stays gated pending human approval.
