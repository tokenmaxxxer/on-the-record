---
status: proposed
files:
  - docs/issue-847/proposals/2026-08-11-faithful-github-host-for-steady-state-harness.md
  - docs/issue-847/reports/technical-feasibility/survey.md
  - docs/issue-847/reports/technical-feasibility/scout-brief.md
---

# Proposal — faithful GitHub host for the #776 steady-state harness (issue #847, phase 1: design)

market_argument_supplied: false

## Intent

Recommend how the #776 steady-state scenario gets a FAITHFUL GitHub host so a delegated role can
open and merge a PR and `final_report` can materialize, so northpole reqs #1/#4 (and transitively
#2/#6/#7) can score a real PASS/FAIL instead of UNMEASURED — without forcing network/CI onto a
normal plugin user's install (northpole req #7 governs the product install, not the harness), and
never yielding a false PASS when run against a non-GitHub stand-in.

## Constraints found so far

- The harness's current `seed_remote_dir` (PR #840) seeds a local bare (`file://`) repo, which
  satisfies `git remote get-url origin` but is not a host `gh` recognizes — canonical: issue #847
  body's quoted `session-end` refusal text, sourced from PR #845 §step 5.
- This is a routed-forward decision, not a fresh problem: `docs/issue-776/reports/execution-observation.md`
  open finding 2 already named this exact gap and explicitly deferred it to a future design
  decision — canonical: that file's "Open findings" item 2, read this session (survey.md
  "Current-state survey").
- Two other independent blockers exist on the same PR-open path (missing fixture-side
  `docs/specs/approvers.md`; the top-level `-p` session's background watch dying with its parent
  turn) — canonical: same file, "Open findings" items 1 and 3. Both are out of this issue's scope
  (issue #847's step 1 asks only for the GitHub-host judgment) and are not re-adjudicated here.
- `gh` reads `GH_TOKEN`/`GITHUB_TOKEN` for github.com auth with no `gh auth login` step, and
  fine-grained PATs scope to exactly one named repo with per-resource read/write permission
  (survey.md Probe 1 findings 1-2).
- No maintained, general-purpose GitHub-API mock exists at the fidelity `gh`'s issue/PR/merge
  calls would need to be fooled end-to-end; the closest community want (Probot) is a still-open,
  unresolved request (survey.md Probe 1 finding 3).

## Timebox and acceptance criteria

**Timebox:** single research session, live 2026-08-11, within the 1-3 day spike convention — one
parallel scouting round (2 angles) plus direct repo inspection. No further phase-1 timebox
requested. Phase 2 (wiring the chosen host into `harness/driver.py`'s scenario, issue #847's own
execution-plan step 2) is scoped and timeboxed separately at approval.

**Acceptance criteria** (carried verbatim from issue #847's own Acceptance section): in the #776
steady-state scenario, a delegated role opens and merges a PR against the harness's GitHub host
and the session produces a `final_report`; where no host/token is available the scenario reports
UNMEASURED explicitly, never PASS. Empty state: no token/host available → UNMEASURED with a clear
reason, not a crash and not a false PASS. Provenance: executed-live.

## Candidates considered

1. **Throwaway real GitHub repo under a harness-controlled test account, scoped fine-grained PAT
   in the harness env only** (issue's candidate a) — evaluated in survey.md Probes 1-4. Fully
   satisfies `gh`'s host check unmodified (no `gh` patch), costs one harness-only env var, and has
   no license/DPIA exposure (survey.md Probe 3). Rejection reasons for the alternatives below
   apply relative to this candidate.
2. **Faithful `gh` mock / local GitHub-API stand-in** (issue's candidate b) — rejected: no
   maintained project exists at the needed fidelity (survey.md Probe 1 finding 3, Probe 2); what
   exists is either in-process Go transport stubbing usable only inside `gh`'s own test binary
   (`pkg/httpmock`), or generic mock-server libraries with no GitHub preset to adopt — building one
   faithful enough is open-ended, ongoing-maintenance "build," not "buy" (survey.md Probe 2
   verdict), with a real, documented fidelity ceiling on server-side semantics like merge-queue
   check timing (survey.md Probe 1 finding 4, STRIDE row 5).
3. **Hybrid: real host when a token is present, explicit UNMEASURED-with-reason otherwise, never a
   false PASS** (issue's candidate c, and the issue's own stated non-negotiable bar) — **chosen**,
   layered on top of candidate 1 rather than as an alternative to it: candidate 1 supplies the
   real-host mechanism; this candidate's contribution is the explicit empty-state branch so the
   scenario degrades to UNMEASURED, never crashes and never silently reports PASS, exactly when no
   token/host is configured. Not a separate technical approach from candidate 1 — the acceptance
   criteria (carried above) require both halves together.

## Verdict

**Decision: conditional**

**Chosen direction:** candidate 1 (real throwaway GitHub repo + harness-only scoped fine-grained
PAT) as the host mechanism, with candidate 3's explicit-UNMEASURED empty-state branch as a
required, non-optional part of the same change — together these are what satisfies the issue's
acceptance criteria in full; neither alone does.

**Conditions (blocking, resolvable within this repo's own phase-2 work, not external):**
- Phase 2 must add a harness-only env var (e.g. `NORTHPOLE_HARNESS_GH_TOKEN` plus a
  harness-controlled `NORTHPOLE_HARNESS_GH_REPO`) that `harness/driver.py`'s steady-state scenario
  reads to seed a real GitHub remote instead of (or in addition to) `seed_remote_dir`'s bare repo,
  and must add the explicit UNMEASURED-with-reason branch to the scenario/signals path when that
  var is unset — this is in-repo implementation work, not an external dependency, so it is listed
  under `conditions:` (blocking until built) rather than the `verdict_provisional` convention.
- A throwaway GitHub account/repo and its scoped PAT must actually be provisioned before phase 2's
  own re-run (issue #847 execution-plan step 3) can produce a real PASS/FAIL — this provisioning
  step is external to this repository (a GitHub-side account/token action, not a code change), so
  it is the blocking condition this verdict is conditional on, distinct from the in-repo wiring
  work above.

`verdict_provisional: feasible-with-conditions` — the mechanism (candidate 1 + candidate 3's
empty-state branch) is architecturally sound and buildable now, per survey.md Probes 1-4; it is
blocked only on the two conditions named above (in-repo wiring, and the external account/token
provisioning step), matching issue #847's own step 2/step 3 split.

## Safety argument

- **Never a false PASS on a non-GitHub stand-in.** The empty-state branch (candidate 3) is not an
  optional nicety — it is layered directly onto the same code path that reads the harness-only
  token var, so "no token" and "wrong host" both resolve to the same explicit UNMEASURED outcome
  `docs/specs/northpole-harness.md` §3 already establishes the precedent for (empty-state column,
  row 1), never a silently-passed default.
- **The product install stays untouched.** The token variable is harness-scenario-only, read by
  `harness/driver.py`, never by anything a normal plugin install path reads or ships — northpole
  req #7 governs the *product's* install surface, and this proposal adds nothing there (survey.md
  "Deploy/runtime config surface" note).
- **The token cannot reach anything beyond the throwaway repo.** Fine-grained PAT scoping is
  enforced by GitHub server-side, not by harness code discipline (STRIDE row 2, survey.md Probe
  4) — even a leaked token cannot touch the org's real repos.
- **Bounded usage stays within GitHub's own limits.** A single-scenario run's call volume (one
  issue, one PR, one merge) sits far under GitHub's documented REST rate limits and AUP bar
  (survey.md Probe 3), so this does not introduce an abuse-policy risk to the harness-controlled
  account.

## Measurement design

Phase 2, if approved, must record: the raw `gh issue create`/`gh pr create`/`gh pr merge` output
from one live steady-state re-run against the real throwaway repo (showing `final_report`
materializing and northpole reqs #1/#4 scoring a real PASS/FAIL, not UNMEASURED-from-missing-host);
and a second run with the harness-only token var deliberately unset, showing the scenario reports
UNMEASURED-with-reason rather than crashing or falsely passing. Both raw outputs get pasted into
the phase-2 record per this repo's provenance convention, not summarized only, matching this
issue's own step 3 (execution-observation re-run) and its Acceptance section's empty-state clause.

## What did not work

None.
