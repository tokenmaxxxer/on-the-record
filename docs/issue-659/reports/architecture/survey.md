# Current-state survey — issue #659 (architecture, phase 1)

Scout: skipped. This is internal repo-tooling component design with no external product category
to benchmark; the field to survey is this repo's own existing gate modules, per
`docs/handbooks/architecture-methodology.md`'s scout-applicability note and the scout-directive's
skip condition ("spec literally leaves no design decision open" does not apply here, but "internal
repo tooling, no product category" is the same class product-discovery already recorded a skip for
on this same issue).

## Background / context

Confirmed by inspection (`gates/risk_report.py`, `gates/flows.py`, `on-the-record/hooks/`):

- `gates/risk_report.py` already contains a **distinct, deployed** batch mechanism that issue #659
  does not name and that must not be conflated with what Axis 1 asks for: `classify_axes` (function
  in that file) grades four risk axes (`blast_radius`, `reversibility`, `propagation`,
  `existing_signals`) per open proposal (`docs/proposals/*.md` / `docs/issue-*/proposals/*.md` with
  `status: proposed`), and `batch_blocked` (function, same file) flags any proposal whose
  `reversibility` axis hits `AXIS_MAX` as requiring individual approval (`axes["batchable"] = not
  axes["requires_individual_approval"]`). `on-the-record/hooks/impact-guard.sh` calls
  `scan_open_proposals` then `batch_blocked` and denies the whole command if any blocked proposal is
  present. This answers "is this proposal too risky to ever be batched with anything" — a permission
  gate on individual proposals, not a grouping computation over a set. Issue #659 Axis 1 asks for
  the opposite direction: given a set of already-permissible pending PRs, which subset is mutually
  safe to approve together because their own write-sets don't collide. Both are real and both stay
  — Axis 1 is a new stage that runs *after* `batch_blocked` has already cleared a PR as
  batchable-in-principle, not a replacement for it.
- `_glob_matches` (function, same file, fnmatch with `**`-prefix fallback) is the one overlap
  primitive `blast_radius_grade` and `propagation_grade` already use, comparing a proposal's own
  `files:` list against role `write_scope` globs (`_role_write_scopes`). Product-discovery's
  current-state.md already confirmed this is the reusable primitive for Axis 1's pairwise PR-vs-PR
  write-set comparison — it compares a path against a glob, not a path-set against a path-set, so
  pairwise PR comparison needs a small (path-set, path-set) -> bool wrapper around it, not a new
  comparison algorithm.
- `gates/flows.py` (function `_plan_from_body`, issue #189/#197) is the deployed, real parser for
  `## 실행 계획` bodies, returning `[{step: int, roles: [...], done: bool}, ...]` with `‖`-joined
  roles within one step. `flows_payload` (function, same file) is what assembles the full per-PR/
  per-issue status payload consumed by `on-the-record/commands/run.md` and the watch tooling; grep
  of both `gates/risk_report.py` and `gates/flows.py` for any caller that reads `done` across steps
  to gate a spawn or merge action returns nothing — confirms product-discovery's finding that Axis 2
  is unimplemented, not just unwired.
- Existing hook wiring pattern: `on-the-record/hooks/impact-guard.sh` is the one precedent for "a
  deployed hook that imports a `gates/*.py` function and denies a command based on its return
  value" — the same shape issue #659's two axes need, at two different lifecycle points (batch
  approval framing vs. spawn/merge command).
- Existing schema pattern: no `roles/*.json` field concerns either axis. Axis 1 and Axis 2 both
  operate over PR/issue *state* (diffs, plan bodies), not over role identity or write_scope
  ownership — unlike issue #573's `judgment_axes` schema addition, this issue adds no new
  `roles/*.json` field. Confirmed by grep: no existing `roles/*.json` field encodes cross-PR or
  cross-step relationships today.
- `docs/specs/approvers.md`-gated approval flow (contract v3 s19) and `on-the-record/commands/
  run.md`'s spawn logic are the two existing consumers whose behavior either axis's gate output
  would need to reach — confirmed as the deployment surface, not modified in this phase.

## Problem, stated without the proposed solution

Carried forward from `docs/issue-659/reports/product-discovery/current-state.md` (merged); not
re-derived here. Architecture's own gap is narrower: given that Axis 1 and Axis 2 are both wanted
as *mechanical, re-derivable* gates (product-discovery's finding), where do their computations and
audit-record writes live such that (a) neither duplicates `_glob_matches`/`_plan_from_body`, (b)
neither is confused with the existing `batch_blocked` risk gate, and (c) the audit-record write
path matches this repo's existing `docs/issue-<n>/decisions/*.md` convention rather than inventing
a new record location.

## Degradation, stated explicitly

Without an architecture decision, implementation would face an unconstrained choice between at
least three plausible-looking wrong shapes already visible in this repo's own history: (1) extending
`risk_report.py`'s `batch_blocked` in place, silently conflating risk-based batch permission with
write-set-based batch grouping — two orthogonal signals, the same anti-pattern issue #573's own
proposal rejected for its own axes (`docs/specs/impact-classification.md`, "Rejected: weighted
composite"); (2) a single combined gate for both axes, which the product-discovery proposal already
rejected (RICE candidate #2) for the approval-act layer and which applies with equal force one level
down at the module-boundary layer — a PR that fails ordering but passes write-set overlap must not
round up to eligible through a shared code path; (3) inventing a new audit-record location instead
of reusing `docs/issue-<n>/decisions/*.md`, breaking `git log --grep`/directory-convention
discoverability this repo already depends on. Left undecided, implementation resolves these by
guessing, one level of the same #476 anti-theater failure this whole issue exists to close.
