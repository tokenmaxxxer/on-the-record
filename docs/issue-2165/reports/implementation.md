---
issue: 2165
role: implementation
loop_state: landed
upstream:
  - path: docs/issue-2165/proposals/2026-08-24-sticky-merged-confirmation-cache.md
    sha: same-commit
  - path: docs/issue-2165/reports/implementation/survey.md
    sha: same-commit
code_under_review: same-commit
commit_sha: same-commit
type: fix
breaking: none
verdict: pass
---

# issue-2165 — implementation record

## What was done

canonical: docs/issue-2165/proposals/2026-08-24-sticky-merged-confirmation-cache.md
This diff covers the approved proposal's four build-plan items, within its stated files: scope (`gates/spawn_on_pr.py`, `tests/test_spawn_on_pr.py`).

Adds `MERGED_SEEN_STATE_REL`, a sibling constant of the existing `PARK_STATE_REL`.
canonical: gates/spawn_on_pr.py:56-63

Adds `load_merged_seen(root)` / `_save_merged_seen(root, seen)`, mirroring `closure_sweep._load_out_of_index_seen` / `_save_out_of_index_seen`.
canonical: gates/spawn_on_pr.py:275-293

The mirrored helpers store a JSON list-of-strings on disk and load it into an in-memory `set[str]`, returning an empty set on a missing/corrupt file.
canonical: gates/closure_sweep.py:297-316

Inside `missing_verification()`, a lazy-loaded merged-seen check sits between the `if not missing: continue` line and the first `gh`-dependent call (`_pr_number_for_branch`).
canonical: gates/spawn_on_pr.py:184-193

A subject already present in the merged-seen set is skipped there, before any further per-subject lookup runs that tick.
canonical: gates/spawn_on_pr.py:189-193

Inside the existing `if pr_state == "MERGED":` branch, the subject is added to the set and persisted via `_save_merged_seen()`.
canonical: gates/spawn_on_pr.py:216-221

The pre-existing `ledger_write`/`print` calls in that branch are unchanged by this diff.
canonical: gates/spawn_on_pr.py:216-224

`tests/test_spawn_on_pr.py` gains `test_missing_verification_sticky_merged_cache_survives_flaky_reconfirm`, a confirmed-merge tick followed by 3 flaky-reconfirm ticks that asserts the subject stays excluded and that `_pr_open_or_merged_for_branch` is never called again on the later ticks.
canonical: tests/test_spawn_on_pr.py:319-350

It also gains `test_spawn_missing_for_pr_sticky_merged_cache_zero_spawns_across_ticks`, driving `spawn_missing_for_pr()` across 1 confirmed tick plus 10 flaky-reconfirm ticks.
canonical: tests/test_spawn_on_pr.py:353-388

## Why

canonical: docs/issue-2165/reports/implementation/survey.md (`## The actual gap: merge-confirmation is re-derived live every tick, never remembered`)
Before this diff, `missing_verification()`'s merge-skip branch read and wrote no cross-tick state — every tick re-derived `pr_state == "MERGED"` from scratch.

`_pr_state_for_branch`'s own docstring documents that a `gh` call failing on any one later tick falls open back to `"OPEN"`, which could re-trigger a spawn for an already-merged subject.
canonical: gates/spawn_on_pr.py:90-112

`closure_sweep.py` already carries this exact shape for a structurally identical problem (a subject classified once as out-of-scope is never reclassified).
canonical: gates/closure_sweep.py:297-316

The proposal's Rationale names two rejected alternatives — collapsing the two-call `gh` fallback, and widening park's `blocked` semantics into a general skip — and explains why mirroring `closure_sweep.py` instead keeps the fix additive to the existing park mechanism (issue #1476) rather than touching shared code paths.
canonical: docs/issue-2165/proposals/2026-08-24-sticky-merged-confirmation-cache.md (`## Rationale`)

## Upstream basis

The proposal was approved via an issue-level `APPROVE issue-2165/implementation` comment.
canonical: https://github.com/tokenmaxxxer/on-the-record/issues/2165#issuecomment-5391946937

Proposal and survey paths are listed in this record's frontmatter `upstream:` and land in this same commit.

`closure_sweep.py`'s out-of-index-seen cache is the mirrored precedent.
canonical: gates/closure_sweep.py:297-316

## Skill checks

skill-verdict: implementation-performance-data-structure-choice — applied: invoked; checked the cache design against rule 6 (read every tick per open subject, written once per subject only on its terminal merge confirmation) and rule 1 (membership test runs inside the per-tick subject loop, so `load_merged_seen()` returns `set[str]`, not a list).
canonical: gates/spawn_on_pr.py:275-288 (`load_merged_seen` return type)

other mounted skills: not triggered (single-file change mirroring an existing in-repo pattern; no coupling-threshold, GoF-pattern, or multi-module structural decision arose).

## Verification

canonical: python3 -m pytest tests/test_spawn_on_pr.py tests/test_spawn_on_pr_park.py -q — result: 28 passed, 0 failed, 0 skipped (hand count equals the pasted summary count below; includes both new regression tests, no existing test's assertions changed in this diff)
```
............................                                             [100%]
28 passed in 1.13s
```

Neighbor sanity check (`watchdog.py` calls into `spawn_on_pr.py` but this diff adds no new call signature):
canonical: python3 -m pytest tests/test_watchdog_local_signals.py tests/test_watchdog_freshness.py -q — result: 20 passed, 0 failed, 0 skipped
```
....................                                                     [100%]
20 passed in 0.92s
```

## What did not work

None.

## Open findings

None required by this issue's acceptance criterion. Candidate follow-ups from the proposal's `## Out of scope`, not required here:

Root cause of sustained `gh` flakiness in the external target repo #513 ran in remains unresolved — this session has no access to that environment.
canonical: docs/issue-2165/reports/implementation/survey.md (stated evidence gap)

Collapsing `_pr_state_for_branch()`'s two-call fallback into one `gh` call was rejected as the primary fix.
canonical: docs/issue-2165/proposals/2026-08-24-sticky-merged-confirmation-cache.md (`## Rationale`, rejected alternative 1)
