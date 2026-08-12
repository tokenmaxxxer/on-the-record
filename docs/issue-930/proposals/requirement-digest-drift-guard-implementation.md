---
subject: issue-930
kind: proposal
status: proposed
files:
  - docs/specs/requirement-digest.md
  - gates/requirement_digest.py
  - gates/test_requirement_digest.py
  - on-the-record/hooks/requirement-digest-preflight.sh
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/directive.sh
  - docs/specs/requirements.md
  - gates/ci.py
  - spawn.py
  - docs/specs/enforcement-boundary.md
  - harness/fixture-requirement-digest
  - harness/README.md
---

# Proposal — build the requirement digest & drift guard (issue #930, implementation)

## Request

Build the design already approved by the `product-discovery` role for
issue #930 (northpole req#6): a self-maintaining, condensed
requirement-ledger (`docs/specs/requirement-digest.md`) plus an
advisory drift guard, wired only as hook/plugin elements per req#7
(no CI/Actions primary path, no mandatory explicit skill invocation,
default-on once installed). Prove it with a harness scenario that
seeds many requirements and many records, asserts the digest stays
condensed to requirement-count (not record-count), and shows a fresh
session reading only the digest picks a goal-aligned next task.

## Constraints

- Reuse the already-merged design in
  `docs/issue-930/proposals/requirement-digest-drift-guard.md` verbatim
  — this is a build proposal, not a re-design; any deviation from that
  document's shape needs its own justification here.
- req#7: the digest's commit-time regeneration lives in
  `on-the-record/hooks/hooks.json`'s `PreToolUse`/`Bash` group; `.github/workflows/`
  stays untouched; the `gates/ci.py` addition is a backstop only.
- Drift guard is advisory/non-blocking — never added to
  `_board_wide_sweep()`'s `anomaly_count`, matching
  `accumulation_trend()`'s existing contract in the same function.
- Digest render cost must stay O(requirement count), independent of
  total historical record volume — the failure mode the issue names.
- `role-handoff contract v3 s19`: this is phase 1 for the
  `implementation` role — this proposal, once committed and opened as a
  PR, must stop before any code lands, pending an `APPROVE
  issue-930/implementation` comment or a PR review Approve from an
  `docs/specs/approvers.md` account distinct from the PR author.

## Rationale

Considered building the digest generator as a method on the existing
`gates/gates.py::requirement_registry` function instead of a separate
`gates/requirement_digest.py` module (folding condensation into the
existing check rather than adding a new file). Rejected: the merged
design's own RICE table already weighed a fold-in variant (its
candidate B, "fold digest content into requirements.md itself, no
separate drift check") and scored it lower on Impact because it drops
the drift-guard half of req#6 entirely; extending that same reasoning,
collapsing the *generator* into `requirement_registry` would couple two
functions with different callers and different failure semantics
(`requirement_registry` is a CI-failing check with no `--update` mode;
the digest generator needs `parse`/`render`/`update` symmetry with
`gates/spec_index.py`) — the existing `spec_index.py` precedent already
proves the standalone-module shape works at this repo's scale, so this
build proposal keeps `gates/requirement_digest.py` as its own module
rather than retrofitting `requirement_registry`.

## What will be done

1. `gates/requirement_digest.py` — new module mirroring
   `gates/spec_index.py`'s shape: `parse(requirements.md)` extracting
   each `## R###` block's `quote`/`source_issue`/`check`/`status`
   fields; `render()` emitting one condensed line per non-`stale`
   entry (`- R###: <paraphrase, ~120 chars> [status] (source: #<issue>)`)
   plus a header naming the source file and regen command; `update()`
   writing `docs/specs/requirement-digest.md`; `check()` comparing
   current digest content to the freshly rendered content and
   returning block reasons (empty list = pass); before rendering,
   re-verify each entry's `check` path and rewrite that entry's
   `status:` line in `requirements.md` to `stale` in place when it no
   longer resolves (closing the dead-`stale`-transition gap the
   product-discovery hunt found — the one write this module makes to
   the raw registry, scoped to the field the registry's own doc already
   promises is computed); `main()` with the same `[<repo>] [--update]`
   CLI contract as `spec_index.py`.
2. `gates/test_requirement_digest.py` — unit tests for `parse`/`render`/
   `update`/`check`/the `stale`-rewrite path/the empty-registry
   documented-empty-state line, following `gates/test_accumulation.py`'s
   structure.
3. `on-the-record/hooks/requirement-digest-preflight.sh` — new hook,
   added to `hooks.json`'s existing `PreToolUse`/`Bash` group alongside
   `spec-index-preflight.sh`: on a `git commit` whose staged diff
   touches `docs/specs/requirements.md`, recompute the expected digest
   from the staged blob and deny the commit unless
   `docs/specs/requirement-digest.md` is staged with matching content.
4. `on-the-record/hooks/directive.sh` — one added line naming
   `docs/specs/requirement-digest.md` as the condensed live-requirement
   pointer, delivered on `UserPromptSubmit` like the directive's other
   standing lines.
5. `gates/ci.py` — one added call to the new digest `check()` next to
   the existing `gates.requirement_registry(repo, {})` call, as a
   CI-timing backstop.
6. `spawn.py` — new `requirement_drift()` function, called from
   `_board_wide_sweep()` next to `accumulation_trend()`: read live
   (non-`stale`) requirement IDs from the digest, scan open issues/PRs
   already available to that sweep for a `northpole req#<n>` mention or
   `R###` trailer, print (never count into `anomaly_count`) any digest
   requirement with zero referencing open work and any open
   proposal/PR citing no requirement ID.
7. `docs/specs/enforcement-boundary.md` — one added table row for
   `requirement_drift()`, matching the `accumulation_trend()` row's
   shape (advisory, board-wide, non-blocking).
8. `harness/fixture-requirement-digest` + a driver-registered scenario
   (touching `harness/README.md` if the driver's scenario list needs a
   new entry) implementing the four-part acceptance check from the
   merged design: seeded multi-requirement/multi-record state → digest
   reflects the live set at O(requirement count) → fresh digest-only
   session picks a goal-aligned task → drift guard advisory findings
   fire without blocking.
9. `gates/test_hooks_parity.py` needs no edit: it auto-derives its
   expected hook set from `hooks.json` itself (confirmed in the
   implementation-role survey), so the new hook registers there for
   free once step 3 lands.

## Out of scope

- Any change to the design itself — that was `product-discovery`'s
  phase-1 decision, already merged; this proposal only builds it.
- Rewriting `requirements.md`'s registration workflow.
- Making the drift guard blocking.
- `.github/workflows/` — untouched, asserted directly in the harness
  scenario per req#7.
- `docs/specs/requirements.md` changes beyond the in-place `stale`
  status rewrite the digest generator performs — no new requirement
  entries are authored by this build.

## How you'll know it worked

- `python3 gates/requirement_digest.py --update` regenerates
  `docs/specs/requirement-digest.md` from the current
  `docs/specs/requirements.md`, producing a line count equal to the
  number of non-`stale` `## R###` entries.
- `python3 gates/test_requirement_digest.py` passes.
- A commit that edits `requirements.md` without staging a matching
  regenerated digest is denied by `requirement-digest-preflight.sh`;
  one that stages both is allowed.
- The new `harness/fixture-requirement-digest` scenario, run through
  `harness/driver.py`, asserts all four acceptance points from the
  merged design (digest reflects live set at O(requirement count),
  hook deny/allow, fresh digest-only session selects a requirement-
  aligned task, drift guard fires advisory-only and never blocks).
- `git diff --stat main...HEAD -- .github/workflows/` reports no
  changes.

## Accumulation

Unchanged from the merged design's own Accumulation section: digest
render cost is O(requirement-count entries in `requirements.md`) per
regeneration, gated only on commits touching that file; the drift
guard's per-tick cost is O(open issues/PRs) plus O(digest requirement
count), the same order `accumulation_trend()` already pays on the same
tick. No cost in this build scales with total historical record count.

## What did not work

None.
