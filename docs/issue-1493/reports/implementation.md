---
code_under_review:
  - gates/check_run_artifact.py
  - gates/check_runner.py
  - gates/merge_gate.py
  - tests/test_check_run_artifact.py
loop_state: landed
type: feature
breaking: false
canonical: pytest tests/test_check_run_artifact.py tests/test_check_runner.py tests/test_merge_gate.py -q
verdict: pass
---

## What was done

Phase-2 delivery for #1493, implementing the approved design.

canonical: docs/issue-1493/proposals/check-run-artifact-design.md (read this session)

- `gates/check_run_artifact.py` (new, commit d8019030): standalone schema
  module (Alternative B per the design's Rationale) — `build_artifact`,
  `validate`, `write_artifact`, `read_artifact`, `sample_eligible`,
  `select_sample`.
- `gates/check_runner.py`: `main()` now writes the artifact after posting
  the PR comment; `run_checks()` result entries now also carry the
  original check's `command`/`pattern`/`path`, and the `grep` check
  excludes `.on-the-record` from its search.

canonical: git show d8019030 -- gates/merge_gate.py (read this session)

- `gates/merge_gate.py`: new `verify_artifact(repo)` — fail-closed on
  missing/invalid artifact or tree-hash mismatch; on match,
  schema-validate then re-execute every `non_hermetic` entry (mandatory)
  plus a random sample of the rest (floor >=20% or >=3); any live
  divergence flags the whole artifact untrusted.

`verify_artifact()` is exposed standalone and is not wired into
`evaluate()`'s existing gh-comment-based gate — that is a larger
integration than this write set covers, left as follow-up (see Out of
scope).

## Why

canonical: docs/issue-1493/proposals/check-run-artifact-design.md, issue #1493 requirements 1-2 (both read this session)

Basis for the schema/write-side/read-side split above: the approved
phase-1 design record, merged via PR #1534.

canonical: gh issue view 1493 --comments (run this session)

Approval: an issue-level comment whose body is exactly `APPROVE
issue-1493/implementation`, posted by JiwonJung94 — an approvers.md
account, single-account mode (PR author and approver are the same
account).

## No-mock confirmation run

canonical: python3 -m pytest tests/test_check_run_artifact.py tests/test_check_runner.py -q -p no:warnings (run this session)

```
..................
18 passed in 2.15s
```

canonical: python3 -m pytest tests/test_merge_gate.py -q -p no:warnings (run this session)

```
..........
10 passed in 0.83s
```

28 total, 0 skipped, 0 failed.

## Hermetic-flag heuristic (implementation decision)

canonical: gates/check_runner.py:1-60 (read this session)

check_runner has no pytest-marker introspection layer — its checks are
`test`/`grep`/`file-existence` entries parsed from acceptance-section
text, not collected pytest items. This implementation maps the design's
"assume non-hermetic when no marker present" default onto that type
system: `grep`/`file-existence` are deterministic filesystem reads
(`non_hermetic=False`); `test` shells out to an arbitrary command and is
treated non-hermetic by default (`non_hermetic=True`).

## What did not work

- First version of `verify_artifact()`'s sample re-execution failed
  `test_matching_tree_hash_trusts_after_sample_reexecution`: expected
  the live re-run to reproduce the artifact's stored result when nothing
  changed; actual result diverged, because the grep-type check's live
  re-run matched an extra hit inside the just-written artifact JSON file
  itself (which embeds prior checks' captured output). Fixed by adding
  `--exclude-dir=.on-the-record` to the grep invocation in
  `gates/check_runner.py`.

## Doc placement

No new env var, dependency, migration, or setup step; no
library-or-alternative choice beyond what phase-1's Rationale already
recorded — no handbook or decisions/ entry required.

## Open findings

None.

## Out of scope (per approved phase-1 proposal)

- Per-role (`conformance-review`/`execution-observation`) artifact
  consumption wiring — design specifies the policy; wiring those roles'
  own sessions is separate role-spec work.
- `output_hash` normalization (timestamp/path stripping) beyond raw
  sha256 — named as phase-2-open in the design.
- Wiring `verify_artifact()` into `merge_gate.evaluate()`'s existing
  gh-comment gate.
