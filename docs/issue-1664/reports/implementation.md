---
code_under_review:
  - gates/stale_revert_guard.py
  - gates/merge_gate.py
  - tests/test_stale_revert_guard.py
  - tests/test_merge_gate.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Phase 2 delivery for #1664 (northpole req#6), committed on this branch as
11d2041a. Built `gates/stale_revert_guard.py` with a pure
`classify(base_head_content, merge_base_content, head_content, path)` that,
per the binding condition from the independent review on the issue,
does not do a naive 2-way textual compare. It computes a git 3-way merge
of (base HEAD as current | merge-base as ancestor | head as other) via
local `git merge-file` (no network) and REFUSEs only when the simulated
merge result still lacks — cleanly, or via a conflict that keeps base
HEAD's side out of head's side — lines that base HEAD has and that were
added strictly after the PR's merge-base. A stale branch that co-edits a
file the base also grew, with no overlapping hunks, merges cleanly and is
ALLOWed (the review's adversarial case).

canonical: `gh issue view 1664 --comments` — the latest APPROVE comment on
the issue named this as the binding phase-2 condition (naive 2-way compare
manufactures false refusals; feed classify() the simulated merge result).

Wired into `gates/merge_gate.py`'s `evaluate` (gates/merge_gate.py) as a
fourth reason source alongside check-runner result and required
verification records: `pr_refs()` reads the PR's base/head branch names
via `gh pr view`, then `stale_revert_reasons()` computes the merge-base
locally and calls `stale_revert_guard.check_pr()` over the PR's changed
paths, fail-open (`[]`) when refs/merge-base can't be resolved locally.

canonical: this turn's own test run, reproduced below.
derived:
```
$ python3 -m pytest tests/test_stale_revert_guard.py tests/test_merge_gate.py -q
20 passed in 0.92s
```
Covers: unit REFUSE (stale merge-base + overlapping conflict reverting
added lines, path named), unit ALLOW (merge-base includes the later
commit / intentional removal with up-to-date merge-base / byte-identical
merge-base==base-HEAD), unit ALLOW adversarial (no overlapping hunks,
clean 3-way merge), and two live fixture-repo reconstructions of the PR
#1662-vs-#1661 shape (one directly against `stale_revert_guard.check_pr`,
one through `merge_gate.evaluate()` end-to-end) — REFUSE while stale,
ALLOW after rebasing onto base HEAD.

canonical: this turn's own test run, reproduced below.
derived:
```
$ python3 -m pytest -q -m "not slow"
2123 passed, 19 xfailed, 2 xpassed in 21.41s
```
Fast tier per `.on-the-record/test-tiers.json`; no `spawn.py`/hooks touched
so the `slow` tier's trigger classes did not match.

## Why

Northpole req#6 / issue #1664: refuse a PR whose merge would silently delete
content added to base after the PR's merge-base, incident-motivated (PR
#1662 vs #1661, 2026-08-16). basis: docs/issue-1664/proposals/stale-revert-merge-guard.md.

## Rationale for deviations

The proposal's build-plan section (its `## What will be` header) specified
`classify()` as a 2-way diff test: REFUSE when `merge_base_content !=
base_head_content` for a path AND the lines added between merge-base and
base HEAD are absent from head_content — no merge simulation.

canonical: `gh issue view 1664 --comments` (latest APPROVE comment on the
issue) — this named a false-refusal defect in that shape: a stale branch
editing different, non-overlapping lines in a file the base also grew would
trip the same check even though a real 3-way merge integrates both cleanly.

The review made simulating the merge the binding condition for phase 2,
superseding the proposal's literal `classify()` body while keeping its
stated acceptance outcomes (REFUSE stale-and-reverting, ALLOW
up-to-date-or-intentional, ALLOW byte-identical merge-base==base-HEAD, ALLOW
the no-overlap adversarial case) unchanged. Implemented via local
`git merge-file` (diff3 3-way merge) rather than `git merge-tree`
specifically, since `merge-file` operates directly on the three content
strings `classify()` receives without needing a full repo/tree context —
the same simulated-merge semantics the review asked for. The write set is
unchanged from the proposal.

## What did not work

canonical: this turn's own edit/test-run cycle on `gates/stale_revert_guard.py`
and `tests/test_stale_revert_guard.py`.

First `classify()` draft treated any conflict block whose raw text still
contained the added line (inside the conflict markers) as "preserved" and
returned ALLOW even on a genuine overlapping conflict — expected: the
overlap-conflict unit test refuses; actual: it allowed, because raw
substring presence inside conflict markers doesn't distinguish "ours" (base
HEAD's side) from "theirs" (head's side). Fixed by parsing conflict blocks
into (ours, theirs) line pairs and refusing only when an added line sits in
ours but not theirs.

## Open findings

None open.

## Next steps

None — PR ready for review/merge.
