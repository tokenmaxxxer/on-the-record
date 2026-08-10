---
code_under_review:
  - docs/specs/generated-paths.md
  - on-the-record/hooks/product-capture-stopgate.sh
  - on-the-record/hooks/test_product_capture_stopgate.py
  - gates/test_generated_paths.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# issue-684 phase 2 — implementation record

## Upstream basis

docs/issue-684/proposals/2026-08-11-generated-path-disjointness.md, approved
via issue comment `APPROVE issue-684/implementation`.

## What was done

1. `docs/specs/generated-paths.md`: golden-reference table, one row per
   write-producing generator found in the phase-1 survey, mirroring
   `docs/specs/enforcement-boundary.md`'s shape.
2. `on-the-record/hooks/product-capture-stopgate.sh`: the one collision-risk
   generator the survey found — `docs/product/<cat>.md`, keyed only by a
   fixed category name — now derives `<n>` from the current git branch
   (`issue-<n>/<role>`, same convention `delegated-judgment-gate.sh` already
   uses) and writes `docs/issue-<n>/product/<cat>.md`. Off an issue-scoped
   branch the hook now no-ops (fail-closed: no safe issue-scoped path to
   derive).
3. `on-the-record/hooks/test_product_capture_stopgate.py`: existing tests
   updated to run on an `issue-123/product-capture` branch and assert the
   new `docs/issue-123/product/<cat>.md` path; one new test asserts the
   off-issue-branch no-op.
4. `gates/test_generated_paths.py`: derives the generator inventory by
   parsing `on-the-record/hooks/*.sh` for write-producing calls
   (Python `write_text`/`open(...,'w')`/`.mkdir(`/`shutil.copy`/`move`,
   and bash `mkdir -p`/`git clone`), classifies each recorded generator as
   out-of-tree/issue-scoped/n/a, cross-checks completeness against
   `docs/specs/generated-paths.md`, and runs a two-issue (100 vs 200)
   simulation asserting disjoint write sets for `record-scaffold.sh`,
   `delegated-judgment-gate.sh`, and the fixed `product-capture-stopgate.sh`.

## Why

Issue #684 acceptance requires every target-repo write path to be
out-of-tree or issue-scoped, with a filesystem-derived enforcement test
(not a hand-maintained list) — same shape as `gates/test_boundary.py`. The
survey found exactly one violating generator; this delivery fixes it and
adds the derived-inventory test the proposal's `## What will be done`
specifies.

## What did not work

- First cut of `gates/test_generated_paths.py`'s write-call regex only
  matched Python-shaped calls (`write_text(`, `open(...,'w'`, `.mkdir(`,
  `shutil.copy/move`) and missed that `self-update.sh`, `directive.sh`,
  `impact-guard.sh`, `decision-queue-stopgate.sh` write via bash
  `mkdir -p` + `git clone` — the completeness check flagged all four as
  falsely recorded. Fixed by extending the regex to also match
  `\bmkdir\s+-p\b` and `\bgit\s+clone\b`.

## Open findings

Before-landing warrant hunt (stance 4, docs/reports/2026-08-11-hunt-generated-path-disjointness.md)
found: `on-the-record/hooks/delegated-judgment-gate.sh` line 367
(`corpus_dir = TARGET / "docs" / "product"`) still globs the retired
global product-doc corpus and was not updated when this delivery moved
`product-capture-stopgate.sh`'s write target to the new issue-scoped
path. `delegated-judgment-gate.sh` is outside this proposal's frozen
write set (docs/issue-684/proposals/2026-08-11-generated-path-disjointness.md
`files:`), so per the scope-exceeded rule this delivery stops at what the
proposal covers and reports the finding rather than widening mid-build.
The hook's existing "empty corpus escalates, never crashes" design (its
own header comment) means this degrades to always-escalate for the depth
axis rather than failing unsafely — not a crash, but a real functional
regression this delivery caused.

Resolution path: a follow-up issue/proposal should update
`delegated-judgment-gate.sh`'s corpus-directory glob to match the new
issue-scoped location (scoped to the issue the PR's branch carries, same
convention this delivery used) and add that read-path to
`docs/specs/generated-paths.md`'s scope for a future pass.

## Rationale for deviations

No deviation in delivered code — the frozen write set (`docs/specs/
generated-paths.md`, `on-the-record/hooks/product-capture-stopgate.sh`,
`on-the-record/hooks/test_product_capture_stopgate.py`,
`gates/test_generated_paths.py`) was implemented as proposed, with no
files touched outside it. The scope-exceeded rule triggered only for the
open finding above: fixing `delegated-judgment-gate.sh`'s stale
retired-corpus glob would require editing a file outside the frozen
write set, so this delivery stops at what the proposal covers and reports
the finding instead of widening mid-build.

## loop_state

landed
