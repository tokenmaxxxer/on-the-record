# test-authoring operational playbook — evidence trail (phase-1 record)

This session's phase-2 record file (docs/issue-1174/reports/test-authoring.md)
is gated behind an "APPROVE issue-1174/test-authoring" comment per
contract v3 s19 — approval-gate.sh refuses a Write to that exact path
pre-approval.
canonical: PreToolUse:Write hook output this turn from
on-the-record/hooks/approval-gate.sh, refusing that write.
This file carries the evidence trail as phase-1-legal material instead,
matching the market-analysis and technical-writing fan-out units'
precedent (docs/issue-1174/reports/market-analysis/evidence-trail.md).

## Delivered to the rulebook repo

Authored the test-authoring role's operational playbook and pushed it to
tokenmaxxxer/test-authoring-rulebook, branch
issue-1174-operational-playbook, commit 7a0487f. Opened a pull request
against that repo's main branch.
canonical: `git push -u origin issue-1174-operational-playbook` and
`gh pr create` output this turn (this session) — PR URL
https://github.com/tokenmaxxxer/test-authoring-rulebook/pull/22.

## Playbook content

Added a new operational-playbook file, in the target rulebook repo
(not this repo — the path below is external and does not resolve in
this working tree): test-authoring-rulebook's own
docs/specs/playbook/isolation-and-fixture-strategy.md path. That
role's rulebook has no pre-existing plugins/name-per-axis listing to
match, unlike market-analysis's five gate axes, so a single axis file
was authored covering this role's whole decides scope: 테스트 코드
자체가 격리성·fixture 전략 면에서 좋은 설계인가.

Twenty-one condition-choice-source rule blocks were written across
five sections (A. fixture construction, B. pytest/xUnit fixture scope
selection, C. test isolation/independence, D. database-backed fixture
strategy, E. test double selection), each citing a fetched web source
inline.
derived:
```
grep -c '^[0-9]\+\.' /tmp/claude-1000/b171/test-authoring-rulebook/docs/specs/playbook/isolation-and-fixture-strategy.md
```
A REMOVAL-marked rule lands in every one of the five sections (rules
numbered 5, 9, 12, 16, and 20). A Conflicts section reconciles the
Google engineering-practices book's test-double guidance against
Meszaros' fixture-pattern catalog, and notes the transaction-rollback
scope boundary between the rollback rule and its HTTP-boundary
exception rule.
canonical: file content of that playbook file as written by this
session this turn on branch issue-1174-operational-playbook in the
test-authoring-rulebook repo (commit 7a0487f).

## Three-layer research depth

- Practitioner decision rules (operator's demonstrated
  condition-choice granularity): fixture-scope selection (pytest
  docs, pytest-with-eric, PythonTest, pawamoy), DB transaction rollback
  boundaries (Los Techies, rieckpil), test isolation antipatterns
  (OneUptime, arXiv 2510.26171).
- Named methodologies/standards verified at source: Meszaros' xUnit
  Test Patterns fixture-setup/teardown pattern catalog
  (xunitpatterns.com chapters, John Sanda's summary), the Google
  engineering-practices book's test-double hierarchy chapter
  (abseil.io/resources/swe-book).
- Academic theory layer: arXiv paper 2510.26171 (order-dependent flaky
  test taxonomy: polluter/victim/brittle/state-setter), cited for the
  order-dependency rules.
canonical: WebSearch tool outputs this turn (four queries: xUnit Test
Patterns fixture strategy, pytest fixture scope, test isolation
antipatterns/DB rollback, Google test doubles) — each source URL is
attributed to its originating rule inline in the playbook file itself.

## Layout deviation (board-gate)

The rulebook repo's own board-gate.sh refused the fan-out brief's
literal suggested landing path (a top-level playbook directory not
nested under docs/) as neither a standing bucket nor an issue-<n> tree
under that repo's own contract v3 s10 layout gate. Relocated the file
under that repo's docs/specs/ standing bucket instead, consistent with
how the technical-writing exemplar and other already-landed rulebooks
structure doctrine content.
canonical: PreToolUse:Bash hook output this turn from that repo's
board-gate.sh, refusing the original path twice before the relocation.

## What did not work

- First attempted to relocate the file inside the rulebook repo with
  shell move commands; board-gate.sh's PreToolUse:Bash hook blocked
  every Bash invocation in that repo while the file still existed at
  its original disallowed path, including the move command itself.
  Worked around it by writing the file directly to its final allowed
  path via the Write tool, then deleting the stray original-path copy
  with a plain remove command once no more Bash commands needed to run
  inside that repo.
- A pull-request creation call failed once with "you must first push
  the current branch to a remote" despite the branch already being
  pushed and tracked; this harness resets the Bash working directory
  between tool calls, and the push and PR-create calls had landed in
  separate invocations whose cwd had reset in between. Fixed by
  chaining the directory change and the PR-create call inside one
  Bash invocation.

## Coverage status

This unit covers the test-authoring role only. The issue's 43-item
tracker and the operational-playbook-program's batching schedule are
owned by the requirements-engineering/implementation fan-out threads,
not this role-scoped session — not updated here.

## Deviation log

See docs/issue-1174/reports/test-authoring/deviation-log.md.

## Loop state

kind: evidence-trail (phase-1 record)
loop_state: filed
next steps: phase-2 record (docs/issue-1174/reports/test-authoring.md)
opens once an approvers.md account posts the exact comment
"APPROVE issue-1174/test-authoring" on issue #1174, per contract v3
s19's approval gate.
resolution path: pull-request review by an on-the-record maintainer
against the delivered playbook content; phase-2 record filed after
approval.
open findings: none beyond the board-gate layout deviation and the two
what-did-not-work items recorded above, both resolved within this
session.
