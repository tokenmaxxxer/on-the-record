# Proposal — execution-observation of issue #289's delivery (PR #300 + PR #421)

Phase 1 for the `execution-observation` role, spawned on PR creation
per `spawn_on_pr.py`. Issue #289 is closed; both PRs that closed it
(#300, merged `09be57b0`; #421, merged `9907b40`) are already on `main`.
No `docs/issue-289/reports/execution-observation.md` exists yet, so this
role's own record is still owed.

## What this role will check (phase 2, once approved)

Not by relaying either PR's self-reported verification, but by
re-deriving each acceptance criterion live against the current tree
(`bc53410e`):

1. **H1** — `issue_workspace()`'s `.git/info/exclude` covers the full
   home-dotfile set the issue's `git status` excerpt listed.
   Check: run `tests/test_spawn.py::WorkspaceExcludesHomeDotfiles::test_fresh_workspace_excludes_dotfile_set`
   directly rather than reading the write in isolation.
2. **H2** — a sandbox-denied `.git/config` write classifies as
   `sandbox-refusal`, not `gate-refusal` or `unclassified-refusal`.
   Check: run `tests/test_spawn.py::...::test_git_lock_masquerade_is_classified_as_sandbox_refusal`
   directly.
3. **Spec-index staleness** (the defect #421 itself fixed) —
   `docs/specs/reconciled-index.md`'s recorded hash for `protocol.md`
   matches an independently recomputed `sha256`. Check:
   `tests/test_spec_index.py::t_baseline_repo_passes`, plus a live
   `sha256` recomputation in-session rather than trusting the recorded
   value.

## Evidence already gathered this session

All three checks above were already run live in this session, ahead of
phase-2 approval, since they are read-only and reversible:

- `pytest -q tests/test_spawn.py -k "test_fresh_workspace_excludes_dotfile_set or test_git_lock_masquerade_is_classified_as_sandbox_refusal"`
  → `2 passed`.
- `pytest -q tests/test_spec_index.py -k t_baseline_repo_passes` →
  `1 passed`.
- `sha256(protocol.md)` computed in-session: `84addaa507f829b4b9a061dd1c9b5059b087e4e3bcdb1353860de06398d4717d`,
  matching `docs/specs/reconciled-index.md:18`.
- Read `spawn.py:2884` (dotfile-exclude write),
  `spawn.py:3083-3092` (`_SANDBOX_REFUSAL_PATTERNS`, including the H2
  entry and its scoping comment), `protocol.md:218-223`
  (diagnose-don't-delete note), and both PRs' bodies/commits via
  `gh pr view 300` / `gh pr view 421`.

No divergence between either PR's self-report and this session's
independent re-derivation was found. The phase-2 record (once approved)
will state the outcome verdict and cite this evidence by file:line rather
than repeat it.

## Write set for phase 2

`docs/issue-289/reports/execution-observation.md` only. No code file —
this role does not fix, and both PRs are already merged.

## Scout skip record

Skipped: this is a read-only verification pass over already-merged code
with a named, narrow write set (one report file); no exploratory search
of the codebase is needed beyond the files already cited above.
