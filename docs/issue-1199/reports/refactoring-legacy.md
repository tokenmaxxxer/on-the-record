---
subject: issue-1199
role: refactoring-legacy
kind: record
loop_state: landed
---

# Record: refactoring-legacy Claude Code plugin-ecosystem fold-in (issue-1199)

refactoring_name: rulebook-native-learning-fold-in (adding one native
judgment rule per axis file, sourced from surveyed Claude Code
plugin/skill design moves, no structural code change involved — this
unit restructures the rulebook's own rule set, not application code)
motivation: this role's rulebook (built under #1174) had not yet
learned from the Claude Code plugin/skill ecosystem specifically, per
issue-1199's 2026-08-14 operator amendment requiring that survey
target; each added rule closes one identified gap in existing
coverage (see `## Why` below)
mechanics: survey two adoption-evidenced Claude Code plugin/skill
sources → extract one design move per source not already covered by
an existing rule → append that move as a new rule 7, paraphrased with
no tool-name/source framing, to the one axis file it matches → commit,
push, open PR in the rulebook repo
verdict: landed — 4 files changed in the rulebook repo (canonical: the
`git -C .../refactoring-legacy-rulebook diff main
issue-1199/refactoring-legacy --stat` citation below, run this
session), PR #27 opened against `tokenmaxxxer/refactoring-legacy-rulebook`

## What was done

Executed the phase-2 fold-in unlocked by the `APPROVE
issue-1199/refactoring-legacy` comment on this issue (single-account
mode; canonical: `gh issue view 1199 --json comments -q '.comments[] |
select(.body=="APPROVE issue-1199/refactoring-legacy") |
"\(.author.login) \(.createdAt)"'`, run this session, output
`JiwonJung94 2026-08-13T07:37:03Z` and `JiwonJung94
2026-08-15T02:35:51Z` — `JiwonJung94` is listed in
`docs/specs/approvers.md`, both comment bodies are the exact required
string).

Per the 2026-08-14 operator amendment on this issue, the survey target
is the CLAUDE CODE PLUGIN/SKILL ecosystem specifically (not general
domain tooling), using the tech-feasibility adoption-evidence method.
Surveyed two plugin/skill sources with strong, independently-verified
adoption evidence, both directly relevant to this role's domain
(behavior-preserving restructuring of existing code):

- **`obra/superpowers`** — the largest community Claude Code skill
  collection, including a `test-driven-development` skill whose
  `SKILL.md` names Refactor as one of TDD's "Always" use cases and
  states the Red-Green-Refactor cycle's `verify_red` step as
  non-optional ("If you didn't watch the test fail, you don't know if
  it tests the right thing"). derived: `curl -s
  https://api.github.com/repos/obra/superpowers` →
  `"stargazers_count": 272200, "forks_count": 24338`. canonical: `gh
  api repos/obra/superpowers/contents/skills/test-driven-development/SKILL.md
  --jq .content | base64 -d`, run this session — quoted section reads
  "**Core principle:** If you didn't watch the test fail, you don't
  know if it tests the right thing." and the Red-Green-Refactor graph
  includes a `verify_red [label="Verify fails\ncorrectly"]` node with
  an edge back to `red` on `"wrong\nfailure"`.
  Design problem this skill targets: a test never observed to fail can
  turn out to trivially succeed (e.g. it never actually reaches the
  code path under change), so the author gains false confidence in it.
  Its answer: make "watch it fail, for the right reason" a mechanical
  checkpoint before the test is trusted, rather than trusting a test
  the moment it is written. Learning folded in →
  `playbook/characterization-test-scope.md` rule 7: characterization
  tests exist to be a safety net during structural change, so the same
  false-confidence risk applies — this role's rulebook did not
  previously require confirming a captured test can actually detect a
  real behavior change, only that it runs cleanly against current
  behavior.

- **`rohitg00/awesome-claude-code-toolkit`** — a Claude Code
  agent/skill/plugin collection with a `developer-experience/legacy-modernizer`
  agent. derived: `curl -s
  https://api.github.com/repos/rohitg00/awesome-claude-code-toolkit` →
  `"stargazers_count": 2509, "forks_count": 890`. canonical: `gh api
  repos/rohitg00/awesome-claude-code-toolkit/contents/agents/developer-experience/legacy-modernizer.md
  --jq .content | base64 -d`, run this session — quoted text: "Interview
  the codebase through reading to discover implicit business rules,
  undocumented edge cases, and load-bearing workarounds that tests may
  not cover", "The anti-corruption layer must prevent legacy concepts
  from leaking into the modern codebase and vice versa", "Assess
  migration risk for each component by scoring on dimensions of
  business criticality, test coverage, coupling to other modules, and
  team familiarity."
  Design problems this agent spec targets (three distinct moves in one
  spec): (1) a seam or migration boundary chosen from visible code
  structure alone can miss business logic that exists only as an
  undocumented workaround; (2) a facade routing between legacy and
  modern implementations can let either side's internal concepts leak
  across if no translation point is named; (3) ordering migration work
  by a single signal (e.g. change frequency) undercounts risk that
  comes from low test coverage or dense coupling instead. Its answers:
  (1) a dedicated business-rule-discovery sweep before structural
  decisions; (2) an explicit adapter/anti-corruption layer at the
  routing boundary; (3) a multi-dimension risk score driving migration
  order. Learnings folded in → `playbook/seam-selection.md` rule 7
  (read for undocumented business rules before choosing a seam),
  `playbook/strangler-fig-migration.md` rule 7 (explicit adapter layer
  at the facade boundary, concepts forbidden from crossing it
  directly), and `playbook/refactoring-step-decomposition.md` rule 7
  (multi-dimension risk score — business criticality, test coverage,
  coupling, team familiarity — replaces change-frequency-only
  prioritization for what to refactor/migrate first).

A third source (a `mcpmarket.com` skill listing describing a five-phase
strangler-fig workflow: debt assessment, characterization tests,
incremental migration via a routing gateway, parallel-run comparison,
decommissioning) corroborated the same strangler-fig/characterization
shape already covered by this rulebook's existing rules and the
`legacy-modernizer` agent above; it added no rule beyond what the two
sourced entries already cover, so no separate rule was drawn from it.
unverifiable: the mcpmarket.com page itself returned HTTP 429 on
`WebFetch` this session and could not be re-fetched for a direct quote
within this turn's budget — its content is cited only via the
WebSearch result summary, not treated as a rule source.

Applied all four learnings directly into the named target files in the
separate rulebook repo (`tokenmaxxxer/refactoring-legacy-rulebook`,
mounted at
`/home/jwjung/tokenmaxxxer/rulebooks/refactoring-legacy-rulebook`), on
branch `issue-1199/refactoring-legacy` — one new rule 7 appended to
each of `playbook/characterization-test-scope.md`,
`playbook/seam-selection.md`, `playbook/strangler-fig-migration.md`,
and `playbook/refactoring-step-decomposition.md` (canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/refactoring-legacy-rulebook diff
main issue-1199/refactoring-legacy --stat`, run this session — 4 files
changed, 8 insertions). Per the operator's native-application amendment
(2026-08-13T06:36:54Z comment on this issue): no `source: <tool repo>`
framing and no tool-catalog section in the rulebook itself — each new
rule reads as this role's own judgment; the tool names, adoption
evidence, and per-insight mapping live only in this record. No verbatim
text copied from either surveyed repo — every rule is paraphrased
insight. `playbook/verification-cadence.md` was surveyed against but
received no new rule: its existing rules 1 and 5 already cover the
per-step-verification and stop-on-failure ground the TDD skill's
Red-Green-Refactor cycle would otherwise have suggested, so adding a
near-duplicate rule there would not have been a distinct learning.

Committed in the rulebook repo (commit
`a75b0821044f173279a228382879271c1b7d9ac3`, subject: issue-1199;
canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/refactoring-legacy-rulebook log -1
--stat`, run this session), pushed to
`origin/issue-1199/refactoring-legacy`, PR opened against
`tokenmaxxxer/refactoring-legacy-rulebook`. canonical:
`gh pr view 27 --repo tokenmaxxxer/refactoring-legacy-rulebook --json url,state`,
run this session, output url
`https://github.com/tokenmaxxxer/refactoring-legacy-rulebook/pull/27`,
state `OPEN` (Part of #1199).

## Seam: rulebook Rules-list append point
The enabling seam for this fold-in is each axis file's `## Rules`
numbered-list append point — a new rule is a new list item after the
existing highest-numbered rule, never a change to an existing item.
This docs-only rulebook change has no dedicated characterization-test
suite of its own; the nearest on-disk stand-in (the accepted-shape
report this record mirrors) is cited below, and the actual
characterization check run this session is the diff command on the
`canonical:` line.
motivation: keep the existing rule catalog byte-identical while adding rule 7
characterization_tests_path: docs/issue-1199/reports/conformance-review.md
canonical: `git -C /home/jwjung/tokenmaxxxer/rulebooks/refactoring-legacy-rulebook diff main issue-1199/refactoring-legacy -- playbook/*.md | grep -c '^-[^-]'`, run this session, output `0`
test_run: PASS (canonical command directly above)
verdict: pass

## Refactoring steps
refactoring_name: Introduce Assertion (Fowler catalog) — applied four
times, once per axis file, each occurrence appending one new list item
after the file's existing rule 6, no existing rule text touched:
- Introduce Assertion: playbook/characterization-test-scope.md rule 7
- Introduce Assertion: playbook/seam-selection.md rule 7
- Introduce Assertion: playbook/strangler-fig-migration.md rule 7
- Introduce Assertion: playbook/refactoring-step-decomposition.md rule 7

## Equivalence
mechanics: Introduce Assertion applied once per axis file — a pure
addition, no existing rule text touched.
canonical: `git -C /home/jwjung/tokenmaxxxer/rulebooks/refactoring-legacy-rulebook diff main issue-1199/refactoring-legacy -- playbook/*.md`, run this session — every changed hunk shows only `+` lines, zero `-` lines
rules 1-6 in each of the four files are therefore byte-identical before and after this change.

## code_under_review
- playbook/characterization-test-scope.md (refactoring-legacy-rulebook repo)
- playbook/seam-selection.md (refactoring-legacy-rulebook repo)
- playbook/strangler-fig-migration.md (refactoring-legacy-rulebook repo)
- playbook/refactoring-step-decomposition.md (refactoring-legacy-rulebook repo)

## Why
Per issue-1199 (northpole req#1) and the 2026-08-14 operator amendment:
this role's own rulebook (built under #1174) encoded refactoring
methodology from the practitioner/academic literature (Feathers,
Fowler, Azure/AWS pattern pages) but had not surveyed the Claude Code
plugin/skill ecosystem specifically — the tool landscape this role's
own users actually run inside. Two independently-adopted sources
(a 272k-star skill collection's TDD discipline, a 2.5k-star toolkit's
purpose-built legacy-modernization agent) both target this exact
domain and each surfaced a design move this rulebook was missing.

## Upstream basis
docs/issue-1199 (issue body, northpole req#1); operator amendments on
this issue at 2026-08-13T06:35:54Z (apply-not-reference),
2026-08-13T06:36:54Z (native application, no tool-attribution
catalogs), and 2026-08-14 (Claude Code plugin-ecosystem survey target).
canonical: `gh issue view 1199 --repo tokenmaxxxer/on-the-record --json
comments`, read this session, for the amendment comment texts and
timestamps. Report-shape basis: canonical: `find docs/issue-1199 -iname
"conformance-review.md"`, run this session — this file's frontmatter
and section-heading set mirror
`docs/issue-1199/reports/conformance-review.md`, the accepted shape
named in this session's invocation.

## What did not work
The `mcpmarket.com` strangler-fig skill page returned HTTP 429 on
`WebFetch` and could not be directly quoted within this turn's
research budget; it was cited only as corroboration via its
WebSearch summary and contributed no independent rule (see the
`unverifiable:` line above).

## Open findings
None.
