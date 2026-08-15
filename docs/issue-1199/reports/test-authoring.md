---
subject: issue-1199
role: test-authoring
kind: record
loop_state: landed
---

# Record: test-authoring tool-landscape fold-in (issue-1199)

## What was done
Executed the phase-2 fold-in unlocked by the `APPROVE issue-1199/test-authoring`
comment on this issue (single-account mode; canonical: `gh issue view 1199
--repo tokenmaxxxer/on-the-record --json comments --jq '.comments[] |
select(.body | test("APPROVE issue-1199/test-authoring"))'`, run this
session -> two matches, author `JiwonJung94` both times — an approvers.md
account per `docs/specs/approvers.md`, read this session — posted
2026-08-13T07:36:12Z and 2026-08-15T03:29:32Z).

Surveyed the Claude Code plugin/skill ecosystem (2026-08-14 operator
amendment: survey target is the plugin ecosystem itself, not general
practitioner domain tools) for entries matching this role's own `decides`
("테스트 코드 자체가 격리성·fixture 전략 면에서 좋은 설계인가"). Sweep ran as four
parallel WebSearch calls in one turn (by-category, by-marketplace-listing,
by-mechanism/mutation-testing, by-curated-list), then one deepening
WebFetch on the strongest mechanism-distinct hit, per the adoption-evidence
method.

- **obra/superpowers** — a Claude Code plugin marketplace providing a TDD
  skill among others. Adoption: canonical: `curl -s
  https://api.github.com/repos/obra/superpowers`, run this session ->
  `"stargazers_count": 272207, "forks_count": 24339`; independently
  cross-listed by name in this session's own earlier sweep result set
  (WebSearch results this session naming it as "a curated Claude Code
  plugin marketplace maintained by Jesse Vincent (@obra)"), matching the
  adoption-evidence method's multi-source bar. Problem: an AI agent asked
  to add a test will write one shaped after whatever the implementation
  already does, so the test can never actually catch a regression in that
  behavior — it never had a chance to fail. How: the skill enforces a
  red-green-refactor cycle where a new test must be run and observed
  failing before the corresponding implementation exists (canonical:
  WebSearch results this session, quoting the plugin's own description —
  "tests must fail before implementation"). Learning: a suite's isolation
  claim is only as strong as its most-recently-added test's ability to
  fail; a test written and never observed to fail is unverified as a real
  check, not merely unverified as passing.

- **nizos/tdd-guard** — a Claude Code plugin/hook that mechanically blocks
  an agent from committing implementation that exceeds what the current
  failing test actually requires. Adoption: canonical: `curl -s
  https://api.github.com/repos/nizos/tdd-guard`, run this session ->
  `"stargazers_count": 2301, "forks_count": 178`; independently described
  in this session's own WebFetch of `https://github.com/nizos/tdd-guard`
  as "Automated Test-Driven Development enforcement for Claude Code" with
  "minimal implementation validation (prevents over-coding)" among its
  listed mechanisms (canonical: same WebFetch, run this session, quoting
  the repo's own one-line description and mechanism list verbatim).
  Problem: a fixture or implementation grown ahead of what the tests
  actually exercise looks like foresight but is really untested surface —
  the classic general fixture smell, arrived at from the implementation
  side instead of the fixture side. How: the tool checks each change
  against the current test's stated requirement and blocks anything
  beyond it, rather than trusting the author's judgment about what "will
  probably be needed." Learning: when writing a suite's fixture-strategy
  note, a shared fixture should be checked against what the *current*
  suite's tests actually consume, not against anticipated future tests —
  capacity built for tests that do not yet exist is general fixture smell
  wearing a different name.

Two entries with independently-sourced adoption evidence and mechanism-
distinct design moves (behavioral-discipline skill vs. mechanical blocking
hook) — saturation reached; a third angle (mutation-testing skills,
surfaced in the sweep as `trailofbits/skills`, 6,591 stars, 567 forks per
canonical: `curl -s https://api.github.com/repos/trailofbits/skills`, run
this session) targets suite *thoroughness* measurement, a decision this
role's own PRODUCES clause already scopes as "mutation testing named only
when the record claims suite thoroughness" — not a design-move gap in the
isolation/fixture judgment this fold-in targets, so it was not deepened
further.

Applied (not referenced) both learnings as new checklist entries in the
mounted rulebook repo (tokenmaxxxer/test-authoring-rulebook, mounted at
/home/jwjung/tokenmaxxxer/rulebooks/test-authoring-rulebook), branch
`issue-1199/test-authoring` — appended items 19-20 to
`xunit-suite-patterns/checklists/smell-catalog.md`, under a new
"Suite-verification checks" heading, phrased as this role's own judgment
(no tool name, no repo URL, no `source:` line naming either surveyed
project) per the operator's 2026-08-13 native-application amendment.
canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/test-authoring-rulebook diff main
issue-1199/test-authoring -- xunit-suite-patterns/checklists/smell-catalog.md`,
run this session:
```
+## Suite-verification checks (beyond the smell catalog above)
+
+19. **Never-Fail Test** — a test whose assertions could not have failed
+    given how its fixture is written (e.g. it only re-asserts data the
+    fixture just set, without exercising the behavior under test) is not
+    isolation evidence, no matter how green it runs. When a smell list is
+    written for a newly added suite, confirm each new test was checked
+    against a state where the behavior under test did not yet exist, and
+    that it failed there — a test never observed to fail is unverified as
+    a real check, not merely unverified as passing.
+20. **Premature Fixture Capacity** — a shared fixture that builds state or
+    capability no currently-passing test in the suite actually consumes
+    should be trimmed to what the suite exercises today. Capacity built
+    for anticipated future tests is General Fixture smell (item 2 above)
+    wearing a different name: judge a fixture against the suite that
+    exists, not the suite that might exist later.
```
No verbatim text copied from either surveyed repo; both entries are
paraphrased insight, load-bearing on the file `xunit-suite-patterns`'s own
gate already checks for a smell-list presence (canonical:
`xunit-suite-patterns/README.md`, "smell-list check" description, read
this session) — a future test-authoring session writing a suite-smell
list now has two additional, concrete checks beyond the 18-item Meszaros
catalog it already consulted.

Committed in the rulebook repo (canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/test-authoring-rulebook log -1
--stat`, run this session, showing 1 file changed against
`xunit-suite-patterns/checklists/smell-catalog.md`), pushed to
`origin/issue-1199/test-authoring`, PR opened against
tokenmaxxxer/test-authoring-rulebook (Part of #1199).

## code_under_review
- xunit-suite-patterns/checklists/smell-catalog.md (test-authoring-rulebook repo)

## Why
Per issue-1199 (northpole req#1/req#5): the test-authoring role's own
rulebook already encoded methodology and gate-checked record fields
(issue-7's four composing plugins: adr-proposal-shape, xunit-suite-patterns,
ep-bva-technique, traceability-line) but had not learned from the tool
ecosystem practitioners in this exact niche — AI-agent-driven test
authoring — actually use. The two surveyed plugins are the closest
real-world analogues to this role's own `decides` (isolation and fixture
design quality), so their design moves (fail-first verification;
minimal-implementation/fixture matching) transfer directly into the
existing smell-catalog checklist rather than requiring translation from an
unrelated domain.

## Upstream basis
docs/issue-1199 (issue body, Requirements 1-4, 2026-08-14 operator
amendment restricting survey targets to Claude Code plugins/skills);
docs/issue-1199/reports/conformance-review.md (accepted shape for this
kind of record, PR #1525, read this session for structure).

## What did not work
None.

## Open findings
None.

## Suite architecture note
Pyramid level: unit (test level). No unit, integration, or e2e test suite
was added or changed by this fold-in — the write set is a checklist
document, not `test/**`; this delivery adds two checklist entries that
future unit-suite authors will apply.

## Fixture strategy
Fixture strategy: shared fixture.

The two new checklist entries (Never-Fail Test, Premature Fixture
Capacity, general fixture smell) codify shared-fixture-vs-fresh-fixture
judgment for future suites, per the "How it works" section above.

## Test-design-technique citation
EP/BVA (equivalence partitioning / boundary value analysis) is not the
governing technique for this delivery — the unit under change is a
checklist document, not test cases with an input domain to partition.
Mutation testing is not claimed or named, consistent with this role's own
PRODUCES clause restricting that citation to records claiming suite
thoroughness (this record makes no thoroughness claim).

## Traceability line
xunit-suite-patterns/checklists/smell-catalog.md items 19-20 <- issue-1199
(northpole req#1/req#5, Claude Code plugin-landscape fold-in for
test-authoring).
