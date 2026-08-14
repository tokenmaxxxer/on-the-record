---
code_under_review:
  - gates/skip_eligibility.py
  - gates/test_skip_eligibility.py
  - gates/spawn_on_pr.py
  - tests/test_spawn_on_pr.py
type: feature
breaking: false
verdict: shipped-pending-measurement
loop_state: landed
---

# issue #745 — phase 2 record: Item 3 three-axis `execution-observation` skip-eligibility

## Summary of work

Implements the multi-factor conditioning rule from
`docs/issue-745/proposals/item3-execution-observation-conditioning.md`
(approved via `APPROVE issue-745/implementation`): `execution-observation`
is skip-eligible only when ALL three axes read low-risk — non-docs
changed lines under 50, no hard-to-revert path touched, and no
claim-vocabulary match against the landing record. Any single axis
tripping routes the PR to population R (required, unconditioned
behavior, unchanged). `#476`'s `fabrication_survival_rate` guardrail
machinery is untouched — this only conditions whether the role is
spawned, never whether an execution claim gets independently re-executed.

## What was done

- `gates/skip_eligibility.py` (new): three pure axis functions
  (`non_docs_lines_changed`, `hard_to_revert_hit`, `claim_vocabulary_hit`,
  the last reusing `claim_scan.CLAIM_RE` rather than a second regex) and
  `classify_rows()`, a pure classifier over `(added, removed, path)` rows
  + a deleted-path set + record text, returning per-axis trip flags,
  `population` (`"R"`/`"S"`), and `skip_eligible`. `classify_for_subject()`
  is the git-facing wrapper: `git diff --numstat`/`--diff-filter=D
  --name-only` against `gates.BASE...<subject>/implementation`, plus
  `git show <ref>:docs/issue-<n>/reports/implementation.md` for the
  landing record text.

  canonical: `gates/skip_eligibility.py` `_ref_resolvable`/
  `classify_for_subject` functions, read in this same turn while writing
  them.
  When either `ref` or `base` fails `git rev-parse --verify`,
  `classify_for_subject` raises `RuntimeError` instead of falling through
  to zero-signal rows that would otherwise read as low-risk; the caller
  below treats that exception as a signal to keep the role required.

- `gates/spawn_on_pr.py`: `missing_verification()` now calls a new
  `_filter_execution_observation()` whenever `"execution-observation"` is
  in a subject's missing-roles list.

  canonical: `gates/spawn_on_pr.py` `_filter_execution_observation`
  function, read in this same turn while writing it.
  Its `try/except Exception: return missing` wrapping the
  `classify_for_subject` call means any classification exception
  (unresolvable ref, missing branch) leaves `missing` untouched, so
  `"execution-observation"` stays required rather than being dropped on
  an inconclusive classification — the same treatment as the exception
  path above.

  It classifies via `skip_eligibility.classify_for_subject`, writes the
  full classification dict to `runs/ledger.jsonl` via
  `spawn.ledger_write()` (event `execution_observation_classification`,
  carrying `subject`, `ref`, `population`, and all three axis fields) so
  the pre-registered 20-PR measurement window's population membership is
  reproducible from the ledger and diff history alone, and drops
  `"execution-observation"` from the missing list only when
  `skip_eligible` is true.

- `gates/test_skip_eligibility.py` (new): test functions over the pure
  functions and the git-facing wrapper — each axis's trip boundary
  (including the size axis's exact-50 boundary), docs-only rows never
  counting toward size, any deletion tripping reversibility regardless of
  path, the population decision (all-low-risk → S, any single axis → R,
  including a large-but-docs-only diff staying S), plus two live-fire
  tests that build real git repos/branches and call
  `classify_for_subject` end to end for both outcomes.

  derived:
  ```
  $ python3 -m pytest gates/test_skip_eligibility.py --collect-only -q | tail -1
  19 tests collected in 0.01s
  ```

- `tests/test_spawn_on_pr.py`: two new end-to-end tests using real git
  branches (no mocking of `skip_eligibility`) — a small safe diff drops
  `execution-observation` from `missing_verification()`'s output while
  `conformance-review` (unconditioned) still shows; a diff touching
  `gates/*.py` keeps `execution-observation` in the output.
- `docs/specs/enforcement-boundary.md`: added the required row for the
  new `gates/skip_eligibility.py` module (`gate-registration-guard.sh`
  refused the commit without it), same reachability class as
  `spawn_on_pr.py`'s existing row.

derived:
```
$ python3 -m pytest gates/test_skip_eligibility.py tests/test_spawn_on_pr.py tests/test_spawn_on_pr_park.py -q
...................................                                      [100%]
37 passed in 1.59s
```

## Why (rationale)

Per the approved proposal: a single docs-only/not-docs-only axis cannot
distinguish a one-line additive config tweak from a hard-to-revert change
to `gates/*.py` or `on-the-record/hooks/*.sh` — both land in the same
"not docs-only" bucket under a single-axis rule. The three axes (size,
reversibility, claim vocabulary) are each independently checkable against
data already in the diff and the record, with no new instrumentation.

## Upstream basis

- `docs/issue-745/proposals/item3-execution-observation-conditioning.md`
  (approved phase-1 proposal, this issue) — the pre-registered package
  this record implements. canonical:
  `docs/issue-745/reports/product-discovery/current-state.md` §3 backs
  that proposal's own adoption-count framing; this record does not
  re-derive that figure, only cites where it lives.
- `gates/claim_scan.py` (issue #476) — `CLAIM_RE` reused unchanged for
  the claim-vocabulary axis; its independent claim/evidence enforcement
  is untouched by this change.

## What did not work

None.

## Open findings

None new. The proposal's own `결정 유보` section deferred generalizing
this three-axis shape to other `use_when`/`board_condition`-gated roles
to a later session — not actioned here, out of this record's scope.

## Next steps

- Let the pre-registered 20-PR measurement window accumulate
  `execution_observation_classification` ledger entries, then compute
  `execution_observation_sessions_per_landed_pr` for populations R and S
  per the proposal's decision rule.
- Per the proposal's ITWWS: if population S persists at threshold, fold
  the original docs-only `board_condition` candidate into this rule as
  subsumed axis coverage rather than pre-registering it separately.

## Resolution path

No open findings to resolve in this record. The measurement window
above is a scheduled follow-up, not an open finding — its resolution
path is the proposal's own pre-registered decision rule (persist / pivot
/ kill) applied once the 20-PR window closes.
