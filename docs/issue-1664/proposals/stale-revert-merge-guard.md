---
status: proposed
files:
  - gates/stale_revert_guard.py
  - gates/merge_gate.py
  - tests/test_stale_revert_guard.py
  - tests/test_merge_gate.py
---

## Request

Extend the merge gate with a deterministic check that refuses a PR whose merge would delete content added to the base branch after the PR's merge-base — a stale revert. northpole req#6. Motivated by a real incident (2026-08-16): PR #1662 was cut before PR #1661's security-fix amend landed on base; merging #1662 as-is would have deleted that fix. A human caught it by reading the diff; this closes the gap deterministically.

## Constraints

- Pure `classify()` function over three file-content snapshots (base HEAD, PR merge-base, PR head) — no network, no `gh` call inside `classify()` itself.
- REFUSE only when the merge-base is STALE relative to a later base commit that added the now-missing content — a branch with an up-to-date merge-base that intentionally removes lines must ALLOW.
- A PR whose merge-base equals base HEAD must ALLOW byte-identical to today (no new refusal path taken) — the empty-state acceptance criterion.
- No new dependency, no CI workflow file (this repo has no CI surface, per merge_gate.py's own header comment).

## Rationale

Considered folding the stale-revert check directly into `merge_gate.evaluate()` as inline logic, rather than a separate module. Rejected: `merge_gate.py`'s existing shape is one check per concern, each a thin function evaluate() composes reasons from (check-runner result, required verification records) — inlining a third, more complex concern (git plumbing + per-path content diff) would blur that composition and make the pure classify() function harder to unit-test in isolation from `evaluate()`'s `gh`-touching parts. A sibling module (`gates/stale_revert_guard.py`) mirrors the issue's own suggested shape ("a sibling gates/stale_revert_guard.py in its shape") and keeps the acceptance criterion's "pure function, no network" boundary structurally enforced — classify() cannot accidentally reach for `gh` because it lives in a module with no gh import at all.

Considered doing a full three-way (base/merge-base/head) diff at the repo level. Rejected as unnecessary scope: the acceptance criteria only require catching deletion/overwrite of content that existed at base HEAD but not at the PR's merge-base — a per-path compare (for each path present in the base-HEAD ↔ merge-base diff, check whether the PR head still carries those added lines) covers the acceptance criteria without building a general three-way merge simulator.

## What will be done

- `gates/stale_revert_guard.py`: `classify(base_head_content: str, merge_base_content: str, head_content: str) -> dict` — REFUSE when merge_base_content != base_head_content (the merge-base is stale for this path) AND the lines present in base_head_content but absent from merge_base_content (i.e. added between merge-base and base HEAD) are also absent from head_content (the PR would revert them). ALLOW otherwise — including when merge_base_content == base_head_content (up to date) or when the PR head still carries the added lines. A thin `collect_snapshots(repo, base_ref, pr_merge_base_ref, pr_head_ref, path)` helper wraps `git show`/`git merge-base` to build these three strings per changed path — this is the only non-pure part, isolated from `classify()`.
- `gates/merge_gate.py`: `evaluate()` gains a stale-revert pass over the PR's changed paths (via the new helper), appending a REFUSE reason naming each reverted path when `classify()` returns REFUSE for any of them.
- `tests/test_stale_revert_guard.py`: unit tests for `classify()` — REFUSE (stale merge-base + reverted lines, naming the path), ALLOW (merge-base includes the later commit), ALLOW (up-to-date merge-base with intentional removal), and the empty-state case (merge-base content == base-HEAD content).
- `tests/test_merge_gate.py`: extend with a live fixture-repo reconstruction of the PR #1662-vs-#1661 shape — a base branch that gets a later commit adding lines, a stale branch (branched before that commit) that lacks them → REFUSE; the same branch rebased onto base HEAD → ALLOW.

## Out of scope

- No CI workflow wiring (no CI surface in this repo).
- No general three-way merge/conflict simulation — only the deletion-of-previously-added-content case the issue names.
- No change to `merge_gate.py`'s existing check-runner or verification-record checks.

## Accumulation

`gates/merge_gate.py`'s `evaluate()` already composes reasons from multiple independent checks (check-runner result, required verification records); this proposal adds a third by calling into `gates/stale_revert_guard.py`, not by adding another inline `subprocess`/`gh` call site — `evaluate()` still has exactly one `gh`-touching helper (`latest_check_runner_comment`), and the new git-plumbing calls (`git show`/`git merge-base`) live entirely inside `collect_snapshots()` in the new sibling module. If N more deterministic merge-time checks are added later, each should follow the same shape — a pure `classify()`-style function in its own module, called from `evaluate()` and contributing to the same `reasons` list — rather than growing `evaluate()` itself with inline logic per check; that keeps `evaluate()` a thin composer indefinitely instead of accumulating N bespoke inline blocks.

## How you'll know it worked

`python3 -m pytest tests/test_stale_revert_guard.py tests/test_merge_gate.py` passes, covering: unit REFUSE/ALLOW/intentional-removal/empty-state cases (acceptance criterion 1 and the empty-state criterion) and the live PR #1662-vs-#1661 fixture reconstruction, both stale (REFUSE) and rebased (ALLOW) (acceptance criterion 2).
