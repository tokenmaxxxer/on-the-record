---
status: proposed
files:
  - docs/issue-705/reports/product-discovery/current-state-survey.md
  - docs/issue-705/proposals/2026-08-12-close-705-and-scope-branch-staleness-followup.md
---

kind: proposal
subject: issue-705

## Intent

Issue #705's literal ask — align post-PR hunt/record write guidance with
what `board-gate`/`record-claim-guard`/`record-fields-gate` actually
check — was delivered by merged PR #710 (see
docs/issue-705/reports/product-discovery/current-state-survey.md,
Background section, for the citation). This proposal's job is: (1) state
that plainly instead of re-doing already-landed work, and (2) register a
narrower, separately-scoped follow-up hypothesis for the one adjacent gap
this session actually read in `spawn.py` — a reused (non-absorbed) local
role branch is checked out with no fetch/rebase against current main
first, unlike the fresh-branch and fully-absorbed-branch arms, which
already do rebase or recut.

This proposal does **not** adopt the invoking prompt's "approval-gate
strandings" / "5 duplicate-docs conflicts from stale-base branching"
framing: those citations (#750, #791, #941, #951, #954, #959, #969) were
checked against GitHub this session and do not support that framing (see
survey's "Note on the invoking prompt's citations"). No design work in
this proposal is built on them.

## Constraints

- Per role-handoff contract v3 s19, this session's own work is phase-1
  only (survey + proposal); no phase-2 record or code lands without an
  approval on this branch.
- Per contract v3, this role's write set stays inside
  `docs/issue-705/**`. No changes to `spawn.py` are proposed to be *made*
  by this session — only a hypothesis for a possible future fix is
  registered, targeting a different (implementation-role) session under
  its own approval gate.

## What will be done (this PR)

1. Land the current-state survey (already written) documenting: issue
   #705's real ask, that it is closed by PR #710, and the one
   `spawn.py`-verified gap (`checkout_issue_branch`'s reused-branch arm).
2. Land this proposal, recommending the issue be treated as resolved on
   its literal terms, and registering the pre-committed hypothesis below
   for whoever picks up the narrower follow-up (a new issue, out of this
   session's scope to file — per contract v3 s19, only the user files
   issues).

## Pre-registered hypothesis for the follow-up (hypothesis-testing skill)

- **Primary metric**: rate of role-session `checkout_issue_branch` calls
  that reuse an existing non-absorbed local branch AND subsequently hit
  a push/PR conflict traceable to that branch being behind current main
  at spawn time, measured over the next 20 role-session spawns after
  instrumentation lands.
- **Threshold / decision rule**: if that rate is >= 1/20 (5%), go — add a
  fetch-and-fast-forward-or-flag step to the reused-branch arm before
  handoff to the role session. If < 1/20, kill — the existing
  recut-on-full-absorption path already covers the practical case and a
  rebase-at-reuse step is not worth the added complexity/risk of
  rewriting a session's in-flight commits.
- **Guardrail metric**: rate of `checkout_issue_branch` calls that
  destroy or rewrite a role session's own uncommitted/committed work as
  a side effect of the new fetch/rebase step (must stay at 0/20 — a
  fix that trades stale-branch conflicts for silent work loss is a
  reduced-trust result, not a win, even if the primary metric improves).
- **Pre-committed ITWWS follow-up**: if this works (go), extend the same
  fetch-and-flag treatment to the orchestrator's stale-workspace roster
  checks (`spawn.py` roster/watchdog paths), which share the same
  "branch state read once at spawn, never refreshed mid-session" shape.

## Out of scope

- Filing the follow-up GitHub issue itself — issues are user-authored
  only per contract v3.
- Any change to `spawn.py`, `checkout_issue_branch`, or
  `_recut_absorbed_branch` — this is a phase-1 proposal; no approval
  exists yet for phase-2 work, and the write set above does not include
  `spawn.py`.
- Re-litigating or re-doing PR #710's already-merged guidance-text fixes.
- The invoking prompt's approval-gate-stranding and duplicate-docs-conflict
  claims — not used, as documented in the survey.

## How you will know it worked

- The survey and this proposal land as this PR's phase-1 content and the
  PR references issue #705 (no `Closes`/`Fixes`/`Resolves` trailer, per
  contract v3's phase-1/phase-2 trailer split).
- A human reader of this PR can, from the survey alone, verify: (a) PR
  #710's merged state via the cited `gh pr view 710` output, and (b) the
  `checkout_issue_branch` reused-branch gap via the cited `spawn.py`
  line range — without re-running anything themselves.
- If/when a follow-up issue is filed and approved, its phase-2 work is
  judged against the pre-registered hypothesis above, mechanically —
  not by fresh judgment once the 20-spawn sample is collected.

## Accumulation

Not accumulation-cost-shaped: this proposal's own write set is two new
files (survey + this proposal), not a recurring or compounding cost
across issues. The follow-up work it registers a hypothesis for is
future, separately-scoped, and separately approved — its own
accumulation profile (if any) is that follow-up's proposal's concern,
not this one's.
