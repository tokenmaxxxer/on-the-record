---
status: proposed
files:
  - gates/verdict_gate.py
  - gates/test_verdict_gate.py
---

# Verdict-asymmetry merge policy (#1669)

## Request

Build a pure policy function that turns an independent reviewer's MERGE/CHANGES verdict into an orchestrator action, without letting the LLM verdict alone authorize a merge: CHANGES always triggers a respawn (safe to automate); MERGE only becomes ALLOW_MERGE when the existing deterministic gate (`gates/merge_gate.py`'s `evaluate()` — check-runner all-pass, required verification records, stale-revert guard) also allows AND declared tests pass; any other MERGE case, or an unparseable/garbled/absent verdict, resolves to HOLD (fail-closed — never merge on a parse failure or a refused gate).

## Constraints

- Pure function, no network/`gh` calls inside `classify()` itself (mirrors `merge_gate.evaluate()`'s own constraint that `stale_revert_guard.classify()` stays pure-local — gates/merge_gate.py:119-120).
- Must reuse `merge_gate.evaluate()`'s existing `{"allowed": bool, "reasons": [...]}` shape as the deterministic-gate input, not re-derive check-runner/verification/stale-revert logic in a second place.
- Module + tests only, this issue's frozen write set. No wiring into the orchestrate directive or `spawn.py` — issue #1669 explicitly sequences that as a follow-up.
- Test-tier directive checked: `.on-the-record/test-tiers.json` is absent in this repo, so no tiered test config applies; the new unit test file runs standalone, no network, matching the repo's existing `gates/test_*.py` convention.

## Rationale

Considered wiring `classify()` directly around `merge_gate.evaluate(root, repo, pr, subject)` (calling `gh`/git under the hood) instead of taking a pre-computed `merge_gate_result` dict as a parameter. Rejected: the issue's own acceptance criteria call for a *pure* function testable on fixtures with no network (`check: unit test ... Pure function on fixtures, no network`); baking the `gh`-calling `evaluate()` call inside `classify()` would make the unit-test acceptance check impossible to satisfy without mocking subprocess calls, and would blur which module owns the deterministic-gate logic versus the verdict-arbitration policy. Taking `merge_gate_result` (the dict `evaluate()` already returns) as a plain argument keeps `classify()` a pure 3-input function and lets a separate thin CLI wrapper (`main()`, following `merge_gate.py:178`'s existing pattern) do the actual `evaluate()` call + `gh` posting for the live acceptance check.

## What will be done

- `gates/verdict_gate.py`:
  - `_parse_verdict(text) -> "MERGE" | "CHANGES" | None` — fail-closed extraction of a reviewer verdict keyword from free text; returns `None` on garbled/absent/ambiguous input.
  - `classify(reviewer_verdict, merge_gate_result, tests_pass) -> "ALLOW_MERGE" | "RESPAWN" | "HOLD"`:
    - verdict parses to `"CHANGES"` → `"RESPAWN"`.
    - verdict parses to `"MERGE"` and `merge_gate_result["allowed"]` is `True` and `tests_pass` is `True` → `"ALLOW_MERGE"`.
    - verdict parses to `"MERGE"` and (`merge_gate_result["allowed"]` is `False` or `tests_pass` is `False`) → `"HOLD"`.
    - verdict does not parse (`None`, or `_parse_verdict()` returns `None` on the raw text) → `"HOLD"`.
  - `main()` — CLI wrapper: takes `<pr> <subject> <verdict-text>` (or reads verdict text from stdin), calls `merge_gate.evaluate()` for the deterministic-gate input, resolves `tests_pass` from the check-runner comment (already parsed by `merge_gate.parse_check_runner_result` / `latest_check_runner_comment`), prints the classification and reasons, exit code reflecting HOLD/RESPAWN vs ALLOW_MERGE — this is the "gh/merge_gate-wrapped check" the issue asks for.
- `gates/test_verdict_gate.py`: fixture-based unit tests covering the four acceptance-listed branches plus the malformed-verdict fixture and the unchanged-path regression (MERGE + allow + tests_pass stays ALLOW_MERGE).

## Out of scope

- Wiring `classify()`'s result into the orchestrate directive or `spawn.py`'s respawn/merge action dispatch — explicitly deferred by the issue to a follow-up.
- The live acceptance check (a real MERGE-verdict PR held/merged against real deterministic-gate state) — that exercises the CLI wrapper end-to-end against a live PR, which is out of this phase-1 proposal; it becomes part of phase-2 delivery's confirmation run.
- Multi-judge quorum (2-of-3) — the issue names this as a deferred high-risk-tier follow-up, not part of this build.

## How you'll know it worked

- `python3 gates/test_verdict_gate.py` (or pytest over it) passes with all listed branches green, including the malformed-verdict→HOLD fixture and the CHANGES→RESPAWN case, with zero network calls made.
- `classify()` is importable and callable as a 3-argument pure function matching the signature above; `merge_gate.evaluate()`'s return dict works unmodified as its `merge_gate_result` argument (no adapter needed).
