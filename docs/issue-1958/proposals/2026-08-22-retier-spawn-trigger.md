---
status: proposed
files:
  - .on-the-record/test-tiers.json
  - docs/issue-1958/reports/implementation/survey.md
  - docs/issue-1958/proposals/2026-08-22-retier-spawn-trigger.md
---

## Request

Re-tier `.on-the-record/test-tiers.json` so a `spawn.py` diff does not
unconditionally trigger the slow test tier: issue #1955's dead-code removal
in `spawn.py` paid ~10 fix-rerun iterations at 4-5 min each under the
current whole-file trigger, even though that diff touched none of
`tests/test_spawn.py`'s 63 slow-marked integration tests.

## Constraints

- Write set frozen to `.on-the-record/test-tiers.json` and `docs/` — no
  change to `gates/test_tier_contract.py` (the matcher) or to `spawn.py` /
  `tests/test_spawn.py` themselves.
- `python3 -m pytest -q -m "not slow"` must stay under the 300s
  `budget_seconds` on a clean checkout.
- Either the bare `spawn.py` whole-file trigger must go, or the doc must
  record the measured reason it stays (issue #1958 acceptance check 2's own
  either/or).

## Rationale

The survey (`docs/issue-1958/reports/implementation/survey.md`) established
two facts that decide this: (1) `select_tier` in
`gates/test_tier_contract.py` matches only on whole relative file paths via
`fnmatch.fnmatch` — there is no diff-hunk- or symbol-level input anywhere in
that file; and (2) `spawn.py` is a single 8413-line, unsplit module holding
all orchestration/judge/gh-CLI/subprocess logic together, with its 63
slow-marked tests (of 524 total in `tests/test_spawn.py`) covering
integration surfaces scattered non-locally through that one file.

**Alternative considered and rejected: drop `spawn.py` from
`trigger_change_classes` entirely.** This is the most direct reading of the
issue title ("no longer lists bare spawn.py") and would fully restore fast
iteration for every `spawn.py` diff. It was rejected because it trades a
known, bounded cost (slow-tier reruns on `spawn.py` diffs) for an unbounded,
silent one: a diff that *does* regress one of the 63 slow-marked
integration behaviors (subprocess spawn call-count budgets, judge daemon
lifecycle, gh CLI wrapper behavior) would no longer trigger the tests that
catch it, and nothing in this issue's frozen scope (JSON + docs only) can
add a narrower, still-safe replacement trigger — because the matcher cannot
see which lines changed, and `spawn.py` has no submodule boundary to key a
narrower glob on. Removing the trigger outright converts a measured
iteration-cost problem into an unmeasured regression-detection gap, which
is a worse trade for a file that is this central to the plugin's
orchestration surface.

**Chosen approach: keep the bare `spawn.py` (and `tests/test_spawn.py`)
triggers, and record the measured reason in the tiering doc**, per issue
#1958 acceptance check 2's explicit second branch. This is honest about
what is and is not achievable inside this issue's scope: true change-class
granularity for `spawn.py` needs either a matcher capable of reading diff
content (a `gates/test_tier_contract.py` change) or a `spawn.py` split along
module boundaries (a large, separate refactor) — both out of scope here.
Documenting the constraint, rather than pretending a JSON-only tweak can
solve it, is the accurate outcome; a follow-up issue can propose the matcher
or module-split work if the iteration cost recurs often enough to justify
it.

## What will be done

1. Leave `.on-the-record/test-tiers.json`'s `trigger_change_classes`
   unchanged (`spawn.py`, `tests/test_spawn.py`,
   `on-the-record/hooks/*.sh`, `on-the-record/hooks/test_*.py` all stay).
2. Add a comment/note file — `docs/issue-1958/reports/implementation/survey.md`
   already carries the measured matcher-granularity finding; the phase-2
   record (`docs/issue-1958/reports/implementation.md`, once approved) will
   cross-reference it as the tiering doc's measured-reason record required
   by acceptance check 2.
3. No change to `spawn.py`, `tests/test_spawn.py`, or
   `gates/test_tier_contract.py`.

## Out of scope

- Splitting `spawn.py` into modules to enable directory-level trigger
  globbing.
- Teaching `gates/test_tier_contract.py` to match on diff content/symbols
  instead of whole file paths.
- Any change to the `fast`/`slow` pytest commands themselves.

## How you'll know it worked

- `python3 -m pytest -q -m "not slow"` completes in ~39s on a clean
  checkout, under the 300s budget (already measured in the survey; re-check
  at phase-2 landing).
- `trigger_change_classes` still lists `spawn.py`, and
  `docs/issue-1958/reports/implementation/survey.md` (cross-referenced from
  the phase-2 record) states the measured reason it stays — satisfying
  issue #1958 acceptance check 2's second branch.
