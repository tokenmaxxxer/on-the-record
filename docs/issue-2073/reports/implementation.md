---
kind: implementation
code_under_review:
  - gates/artifact_smoke_rule.py
  - gates/test_artifact_smoke_rule.py
  - gates/design_artifacts_gate.py
  - gates/check_runner.py
  - gates/test_check_runner.py
  - on-the-record/hooks/directive.sh
  - on-the-record/hooks/pr-preflight.sh
  - on-the-record/hooks/test_pr_preflight.py
  - spawn.py
  - tests/test_spawn_directive_assembly.py
  - docs/specs/artifact-smoke-contract.md
  - docs/specs/enforcement-boundary.md
  - docs/specs/reconciled-index.md
loop_state: committing
type: feature
breaking: false
verdict: delivered
---

# Artifact-smoke acceptance — phase 2 implementation record (issue #2073)

upstream: issue #2073; approved proposal
`docs/issue-2073/proposals/artifact-smoke-acceptance.md`; survey
`docs/issue-2073/reports/implementation/survey.md`; scout brief
`docs/issue-2073/reports/implementation/scout-brief.md`; branch base
85a168400f1b2dd3a5b662ce8eb22925481bd9bc.

canonical: gh issue view 2073 --json comments, read in this session
Phase 2 opened in single-account mode: the issue carries an issue-level
comment whose entire body is the exact string `APPROVE
issue-2073/implementation`, from `JiwonJung94`, an account listed in
`docs/specs/approvers.md`.

## What was done

Summary of work — the approved proposal's seven items, in the staging
order it named:

1. `docs/specs/artifact-smoke-contract.md` — the declaration contract:
   the `runtime-artifacts:` tag shape (bare tag line, then a bullet list
   or a fenced block, reused verbatim from the `design-artifacts:`
   contract), the parse/execute verb allowlist, the
   `artifact-smoke-override: yes` escape, and the postures. The spec
   index was regenerated with `python3 gates/spec_index.py --update` in
   the same commit (it came out identical — neither this file nor
   `docs/specs/enforcement-boundary.md` is on the index's
   tracked-document list).
2. `gates/artifact_smoke_rule.py` + `gates/test_artifact_smoke_rule.py` —
   the leaf gate. `check_issue_body(issue, body)` returns refusal strings
   when `runtime-artifacts:` is declared and no `check:`/`gate:` line in
   an `## Acceptance` section names a declared path under an allowlisted
   verb, and an empty list when the tag is absent. `check(repo, issue)`
   fetches the body and refuses rather than passing when it cannot read
   it. `advisory_line` is the non-refusing drafting hint for an
   undeclared but artifact-smelling body. The module imports no
   `spawn.py`, per the proposal's dependency-direction constraint.
3. `gates/check_runner.py` + `gates/test_check_runner.py` — `parse_checks`
   gained an optional `runtime_artifacts` argument and the
   `artifact-smoke` check type, `run_checks` executes that type the same
   way it executes `test`, and `node`/`npx`/`deno`/`bun` joined the
   interpreter allowlist. The verb/path matching rule is imported from
   `artifact_smoke_rule.command_touches_artifact` rather than
   reimplemented, so the gate cannot refuse a shape the runner would run.
4. `on-the-record/hooks/directive.sh` — the `ARTIFACT-SMOKE (issue #2073)`
   and `VISUAL-VERIFICATION (issue #2073)` bullets, next to
   `ACCEPTANCE FORMAT` and `COMMAND-IDENTITY`.
5. `on-the-record/hooks/pr-preflight.sh` +
   `on-the-record/hooks/test_pr_preflight.py` — on a phase-2 PR whose
   issue declares a storyboard among its `design-artifacts:`, refuses
   `gh pr create`/`gh pr edit` unless a record under the issue's own
   reports bucket carries a `screen-verified: <path> — <verdict>` line
   whose cited screenshot exists. Presence and existence only.
6. `spawn.py` + `tests/test_spawn_directive_assembly.py` —
   `_artifact_smoke_task_lines(body)` appends up to two conditional lines
   at the existing #2014 insertion point, from the body already fetched
   (no new `gh` call). Empty string when neither condition holds.
7. This record.

### Doc-placement ladder outcomes

- `docs/specs/artifact-smoke-contract.md` — new standing spec (the
  contract is repo-wide and outlives this issue), not an issue-scoped
  document.
- `docs/specs/enforcement-boundary.md` — one new row for
  `gates/artifact_smoke_rule.py`, one extended row for
  `on-the-record/hooks/pr-preflight.sh`.
- `docs/specs/reconciled-index.md` — regenerated, identical.
- This file — the phase-2 record, under the issue's own reports bucket.
- `docs/issue-2073/reports/implementation/deviation-log.md` — extended
  with the two inline divergences below.
- No handbook change: no operational-surface file was staged.

## Why

Acceptance for a generated or browser-rendered deliverable was allowed to
be indirect — a unit test over the sources, or diff-equality over
regenerated output — and neither form ever parses or runs the bytes that
ship. That is the structural hole `tm-dicequest#26` and `#44` fell
through on the same day with every check green. The fix has to live in
the acceptance contract itself, not in advice: both failures happened in
sessions that had read the directive surface. The declaration plus the
literal artifact-naming rule keeps the runtime-fidelity requirement while
leaving the boot command in the deliverable repo, where a browser and a
build actually exist — the headless-browser-in-the-runner alternative the
proposal rejected would have degraded into a skip on this runner's
browser-less PR checkout, reproducing the very class #2073 exists to
close.

## Acceptance verification

canonical: python3 -m pytest gates/test_artifact_smoke_rule.py -q -p no:randomly -o addopts="" — executed live in this session
- checked: the artifact-smoke rule's unit suite — result: 14 passed

canonical: python3 -m pytest gates/test_check_runner.py -q -p no:randomly -o addopts="" — executed live in this session
- checked: the check-runner unit suite — result: 17 passed

canonical: python3 -m pytest tests/test_spawn_directive_assembly.py -q -p no:randomly -o addopts="" — executed live in this session
- checked: the spawn directive-assembly suite — result: 29 passed

canonical: python3 -m pytest on-the-record/hooks/test_pr_preflight.py -q -p no:randomly -o addopts="" — executed live in this session
- checked: the pr-preflight end-to-end suite — result: 30 passed

canonical: python3 -m pytest -q -m "not slow" — executed live in this session, fast tier per .on-the-record/test-tiers.json
- checked: the fast-tier regression floor — result: 2643 passed, 18
  xfailed, 3 xpassed in 40.63s, no SKIPPED lines in the summary, inside
  the tier's 300s budget

The three checks the issue's own Acceptance names are the first three
entries above. The regression floor the proposal reserved for an
independent verifier was nonetheless run here because the
duplicate-basename divergence below could only surface by running it —
the builder-blind re-run still belongs to the verification role.

## What did not work

- The first attempt at `gates/test_check_runner.py` collided with an
  existing module of the same basename, breaking pytest collection
  repo-wide. Resolved by consolidation (divergence 2 below), not by
  renaming the path the issue's Acceptance names.
- Three commit attempts were refused by gates before landing:
  `test-authoring-invariant-guard` (staging and committing in one Bash
  call leaves nothing staged when the hook reads the index),
  `gate-registration-guard` (a new gate module needs its
  `docs/specs/enforcement-boundary.md` row in the same commit), and
  `trailer-gate` (a `;` inside a `-m` message body truncates the gate's
  static parse of that message, so the `Subject:` trailer reads as
  absent). All three are authoring-order facts, not defects in the
  delivered change.

## Rationale for deviations

canonical: docs/issue-2073/reports/implementation/deviation-log.md, written in this session
Two divergences from the proposal's plan, both inline, both logged:

1. `acceptance-command-real-run-guard.sh` and
   `live-fire-claim-real-run-guard.sh` refuse any commit staging
   `docs/specs/enforcement-boundary.md`, because that file's own
   descriptive rows quote verbatim the citation shapes those guards scan
   staged content for. The write set requires adding a row there. Used
   each guard's documented `-N/A:` trailer, with the reason naming the
   pre-existing prose row.
2. A module of the basename `test_check_runner.py` already existed under
   `tests/`, so creating `gates/test_check_runner.py` — the path the
   issue's Acceptance names — produced a duplicate test-module basename
   and a pytest collection failure. Consolidated both files into
   `gates/test_check_runner.py`, next to the module they exercise, and
   removed the older path. That removal is outside the proposal's frozen
   write set. No coverage was dropped and no assertion changed.

## Skill verdicts

- skill-verdict: implementation-complexity-coupling-management — applied: invoked; rule 4 widened an existing contract instead of adding a cross-module dependency edge.
  It decided two calls — the
  `design_artifacts_gate.parse_declaration` tag parameter instead of a
  copied per-tag parser, and `check_runner.parse_checks` taking
  `runtime_artifacts` instead of importing a second declaration source.
- skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-shaped indirection was under consideration, the gate being three module-level functions over text.
- skill-verdict: implementation-performance-data-structure-choice — not-applicable: the hot structures are a frozenset verb allowlist and a declaration list of single-digit length, with no asymptotic choice open.
- skill-verdict: implementation-blueprint — not-applicable: the module
  boundaries, write set and staging order were frozen by the approved
  phase-1 proposal, so no structural decision remained open for the
  skill to route.
- skill-verdict: work-in-english — applied: invoked; commit messages,
  the spec, this record and all new code comments are English or match
  the surrounding Korean convention per the skill's project-convention
  rule, and the session's Korean summary is the only Korean output.

## Open findings

1. `gates/artifact_smoke_rule.py` is not yet reachable from any
   automatic surface — it is a standalone CLI, like
   `gates/acceptance_authoring_rule.py`, and is not called from
   `gates/ci.py`'s check graph or ported into a hook. A drafting session
   that never runs it sees only the directive bullet.
   resolution path: wire it into the issue-drafting call site the
   proposal's Accumulation section names (the existing
   `acceptance_authoring_rule` call site, with the body already in
   hand), as a follow-up issue — the proposal scoped this delivery to
   the module plus the directive/spawn surface.
2. `command_touches_artifact` matches a declared path against a token
   with a substring test, so an unusual argv could match a declared path
   embedded in a longer token. It is deliberately loose in the admitting
   direction — the refusal is what this gate exists for, and a false
   admission still requires an allowlisted parse/execute verb.
   resolution path: tighten to prefix/suffix matching if a real false
   admission is ever observed on a consumer repo; no such observation
   exists today.
3. The `pr-preflight.sh` screen-verified trigger fires on a declared
   storyboard alone, while `spawn.py`'s co-injected line additionally
   requires the design-bearing classifier. The gate is the narrower of
   the two on purpose (precision-first), but the two conditions are not
   identical and could drift.
   resolution path: if the classifier's verdict is ever needed at
   preflight time, port `design_bearing_classifier.check_issue_body`
   inline the same way `parse_declaration` already is, and pin the
   parity with a test.

## Next steps

- Push the branch and update PR #2084 with a phase-2 body carrying
  `Closes #2073`.
- Independent verification: the regression floor and the acceptance
  re-run belong to the check-runner or a verification role, not the
  builder.
- Open finding 1 is the natural follow-up issue for the user to file.
