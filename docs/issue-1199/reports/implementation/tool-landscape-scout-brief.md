# issue-1199 implementation tool-landscape scout brief (step 2: self fold-in)

Scope: survey plugins/tools that coding-implementation practitioners
most use, evidence-based (stars/downloads/multi-source), then fold the
design moves into implementation-rulebook's own playbook — no
per-tool attribution in the public rulebook.

## Sweep (parallel WebSearch, one round, 4 angles)
- ESLint (JS/TS lint) — 27.4K GitHub stars; 140-156M npm weekly
  downloads (eslint.org, npmtrends.com, Snyk, checked 2026-08-13).
- Ruff (Python lint+format, Rust) — 49.2K GitHub stars; ~77M PyPI
  weekly downloads; replaces Black/Flake8/isort/pydocstyle/pyupgrade in
  one binary (astral-sh/ruff GitHub, pypistats.org, checked 2026-08-13).
- ArchUnit (Java architecture-fitness testing) — 3,729 GitHub stars;
  encodes layering/dependency/cycle rules as executable tests run in
  the existing CI build (archunit.org, github.com/TNG/ArchUnit, Baeldung,
  checked 2026-08-13).
- pre-commit (multi-language hook framework) — 15.1K GitHub stars;
  11.4M PyPI weekly downloads; 10.1K dependent repos; orders hooks and
  fails fast on cheap checks before expensive ones (libraries.io,
  github.com/pre-commit/pre-commit, checked 2026-08-13).

## Judge point
All four hit on independent angles (lint-consolidation, architecture
enforcement, hook orchestration) and all clear both stars and
downloads/dependent-repo thresholds well above the field's median
tooling — no swap needed. Saturation reached after one round: a second
round would surface more lint/format tools, not new DESIGN MOVES beyond
what these four already demonstrate (boundary-check-at-write-time,
single-tool consolidation, cheapest-first ordering).

## Must-bes / performance axes extracted
- Must-be: architecture rules that are just prose get violated silently;
  practitioners' tools make the rule an executable, CI-run check instead
  (ArchUnit).
- Must-be: overlapping single-purpose checks (multiple linters covering
  the same violations) create config-drift and get skipped locally when
  slow; practitioners consolidate onto one tool that covers the union
  (Ruff replacing 5+ tools).
- Performance axis: check ordering — cheap/narrow first, expensive/broad
  last, so the pre-merge step stays fast enough to keep running locally
  (pre-commit's hook-ordering convention).
- Adopt: encode the design move (boundary-check-at-write-time,
  consolidation-over-duplication, cheapest-first ordering) as the role's
  own native judgment rule. Skip: naming/recommending the specific tools
  in the public rulebook — that is a catalog, not a rule.

## Gap line
implementation-rulebook's complexity-coupling-management.md already had
6 rules on cohesion/coupling tradeoffs but none addressing (a) enforcing
an architecture boundary at write-time rather than after a cycle forms,
(b) consolidating overlapping local checks, or (c) ordering checks by
cost. All three gaps map directly onto the four surveyed tools' design
moves.

Sources:
- https://eslint.org/
- https://npmtrends.com/eslint
- https://github.com/astral-sh/ruff
- https://pypistats.org/packages/ruff
- https://www.archunit.org/
- https://github.com/TNG/ArchUnit
- https://www.baeldung.com/java-archunit-intro
- https://github.com/pre-commit/pre-commit
- https://libraries.io/pypi/pre-commit

Stages used: 1 sweep + 1 judge point (2 total) — saturated after round 1.
Mode: parallel WebSearch (4 angles in one batch).
