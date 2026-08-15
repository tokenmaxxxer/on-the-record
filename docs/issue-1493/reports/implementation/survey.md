# Survey — issue-1493 (verification-cost deduplication, phase-1)

## Write set under consideration

- docs/issue-1493/proposals/check-run-artifact-design.md (this survey's
  output — the phase-1 proposal itself, to be created)
- No code files: phase-1 for #1493 is design-only per the issue body
  ("Deliver a phase-1 design record ... as a PR — design only, no
  pipeline changes yet").

## What already exists (#1323 — check-runner, landed)

canonical: gates/check_runner.py (read in full this session)

`gates/check_runner.py` is the deterministic check-runner #1323 landed:
- `parse_checks(section)` classifies each Acceptance `check:`/`gate:`
  line into `test` (backticked shell/pytest command), `grep`
  (`grep:`-prefixed pattern), `file-existence` (bare path), or
  `judgment` (refused, never silently skipped).
- `run_checks(repo, checks)` executes `test`/`grep`/`file-existence`
  checks via `subprocess.run` against a PR branch checkout and raises
  `JudgmentCheckError` for anything unclassifiable.
- `format_comment`/`post_comment` post one structured PR comment.
- What it does not have today: no persisted artifact. Each invocation
  runs checks fresh and produces a comment; nothing is written to disk
  that a later layer could read instead of re-running. There is no
  schema field for tree hash, env fingerprint, or output hash. This gap
  is what #1493 req 1 asks to fill.

derived:
```
$ wc -l gates/check_runner.py
171 gates/check_runner.py
```

docs/issue-1323/proposals/2026-08-14-acceptance-authoring-rule-and-check-runner.md
scoped the spawn-on-PR and merge-gate phases as explicitly out of
scope, sequenced after #1320. #1493 is the next link in that chain: it
proposes a reusable artifact so the downstream roles (and the builder's
own in-workspace run) could in principle consume one run instead of
re-executing independently each time.

## Tiering precedent (#1518)

canonical: docs/issue-1518/proposals/2026-08-15-test-tier-contract.md

That proposal established a `.on-the-record/test-tiers.json` config
(fast/slow commands, budget_seconds, trigger_change_classes) and an
observe-only directive (present in this session's own system reminders)
that checks a target repo's tiers file before running its suite.

derived:
```
$ test -f .on-the-record/test-tiers.json && echo present || echo absent
absent
```

#1493's artifact schema should compose with, not duplicate, this
tiering contract: the artifact should record which tier ran (fast, slow,
or full) so a downstream consumer can tell whether a cached run covered
the tier it needed — this is a design requirement carried into the
proposal, not a verified outcome.

## Bootstrap-cost precedent (#1490) and req 4 scoping

canonical: docs/issue-1490/reports/implementation.md and
docs/issue-1490/proposals/conformance-review-1490.md (both present in
the tree per `ls docs/issue-1490/`; contents not read in full for this
survey — noted as existing, not summarized)

#1493's bootstrap-efficiency requirement is a separate requirement from
the artifact schema requirements. The issue body scope-limits it to
"report + mechanical wins" — a measurement task distinct from schema
design. This phase-1 proposal treats that requirement as out of scope
for the design record itself, flagged explicitly rather than silently
dropped, since #1493's own acceptance criteria list a separate
bootstrap-cost report deliverable alongside the four schema/behavior
tests.

## Ordering precondition (#1491)

canonical: git log --oneline -5 (below)
```
$ git log --oneline -5
8ffb37b3 Merge pull request #1527 from tokenmaxxxer/issue-1491/implementation
2f13d557 issue-1491: phase-2 implementation record for standing-red zero policy
484dc453 issue-1491: implement standing-red zero policy watchdog check
d74be2f5 Merge pull request #1525 from tokenmaxxxer/issue-1199/conformance-review
027729a8 Merge origin/main into issue-1199/conformance-review (resolve stale-branch conflict)
```

#1493 is blocked-by #1491 per the issue body ("caching a red run via
tree-hash match would be worse than today's redundancy"). Commit
484dc453 and merge commit 8ffb37b3 above show #1491's watchdog check
landed on main ahead of this branch's current HEAD.
#1490's blocking status was not independently re-verified this session;
the phase-1 deliverable here is a design record only, which does not
require #1490's cost-curve numbers to exist yet beyond the qualitative
motivation already stated in the issue body.

## Consult constraints (binding, restated from issue body)

1. Orchestrator must keep BOTH schema validation AND random-sample
   re-execution (rate is a phase-1 decision, never zero) — artifact
   presence alone is never sufficient.
2. Tree-hash fingerprint scope must be explicit — non-hermetic deps
   (network fixtures, clock, test ordering) are a named false-skip risk.
3. Verification roles (conformance-review, execution-observation) exist
   for independent re-observation; the design must state per-role what
   is consumed vs. still independently executed — reuse must not hollow
   their purpose.
4. Artifact forgery mitigation (hash-of-output binding) is named as an
   open gap — to be designed, not assumed solved.

## Alternatives space (for the proposal's Rationale)

- Alternative A: extend `gates/check_runner.py` in place to write an
  artifact as a side effect of `run_checks()`.
- Alternative B: a new standalone module with schema read/write
  functions, imported by the check-runner but independently
  testable/schema-versionable on its own.
- Alternative C: no shared schema — each consumer (orchestrator, each
  verification role) parses the check-runner's existing PR-comment
  Markdown output instead of a structured artifact.

These are weighed in the proposal's `## Rationale` section.
