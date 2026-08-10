files:
  - on-the-record/hooks/contract-guard.sh
  - on-the-record/hooks/test_contract_guard.py

## Request

`contract-guard.sh`'s phase-2 check treats an issue as phase-2 if ANY
`APPROVE issue-<n>/<role>` comment ever existed on it, regardless of role or
round. On a multi-round issue this denies every new round's phase-1
proposal PR (no `Closes` obligation should apply to it), which forced an
`ORCHESTRATE_OFF=1` bypass live on issue #476. Scope the phase-2 obligation
to the same round: a prior-round approval must not block a new phase-1 PR;
a same-round approval must still require the delivering PR's `Closes`.
Role stays out of the scoping signal — `gates/ci.py._approved_roles_on_issue`
(issue #312) deliberately treats phase-2 as a property of the issue, not
the role, to support cross-role handoff (architect approves, implementation
delivers), and this fix must not diverge from that.

## Constraints

- No new dependency, no new `gh` subcommand — only widen the `--json` field
  lists on calls the script already makes (survey: `pr view`, `issue view`
  both already cover the needed fields).
- Fail-open behavior for `gh` lookup failures/missing fields must be
  preserved (header note: a lookup failure is reported and passed through,
  never silently treated as a positive violation).
- Existing 7 target-repo-resolution tests
  (`on-the-record/hooks/test_contract_guard.py`) must keep passing unchanged
  in behavior (their fixtures use role `implementation` throughout, so a
  role-aware prefix must not break them).

## Rationale

Considered and rejected: matching the approval comment against "the PR's
phase-1 predecessor merge time" (the issue's alternate phrasing — find the
most recent prior phase-1 PR on this branch and require the approval to
postdate *that PR's merge*). Rejected because it requires an extra `gh`
lookup (listing/searching prior PRs on the same head branch, which `gh` has
no direct single-call query for — it would mean listing all PRs for the
issue and filtering by head ref) purely to reconstruct a timestamp that the
branch's own first-commit time already gives for free. The issue's
acceptance text itself names both variants and asks for "the mechanically
simplest sound rule" — first-commit time is available in the same `pr view`
call this script already issues, at zero extra round trips.

Considered and rejected: keeping the scan issue-wide but requiring the
approval comment to be the single most recent one (`max` by `createdAt`)
rather than `any`. Rejected because "most recent" is still round-blind if
two different roles approve back-to-back within the same round window.

Considered and rejected (found by the after-proposal warrant hunt,
`docs/reports/2026-08-10-hunt-round-role-scoped-phase2.md`): the issue's
minimum-viable phrasing also suggests matching the approval token to the
PR's own role. That was this proposal's first draft, and it is wrong —
`gates/ci.py._approved_roles_on_issue` (issue #312) deliberately makes
phase-2 a property of the *issue*, not the role, exactly to support
cross-role handoff (architect proposes, implementation delivers — #304,
#307): an `APPROVE issue-<n>/architect` comment must still gate a *later
implementation* PR's `Closes` obligation. This script's own header already
claims "Phase is determined the same way
`gates/ci.py._approved_roles_on_issue` does" — adding a role filter here
would silently diverge from that claim and reopen the cross-role bypass
`_phase_from_approval` was written to close. Role-matching is dropped
entirely; only the time-match survives.

Chosen approach: scope the phase-2 scan by time alone — only comments with
`createdAt` strictly newer than the PR's own head branch's first commit's
`committedDate` count, regardless of which role token follows the `APPROVE
issue-<n>/` prefix (keeping today's issue-number-only prefix and
`_approved_roles_on_issue`'s role-agnostic stance intact). This one signal
already satisfies both acceptance rows: a prior round's approval predates
the new round's first commit (no longer counts -> allow); a same round's
own approval postdates its own first commit (still counts -> deny without
`Closes`). The field is already present in the same `pr view` call this
script already issues (`commits[].committedDate`); only the requested field
list needs widening, plus selecting `createdAt` on the existing issue
comments query — zero extra `gh` round trips, and no divergence from
`gates/ci.py`'s established role-agnostic phase model.

## What will be done

In `contract-guard.sh`:
- Widen `pr_data = gh_json("pr", "view", pr, "--json", "body,number")` to
  also request `commits`.
- Derive `first_commit_at` from `pr_data.get("commits") or []` — the
  earliest `committedDate` among the PR's commits (empty list -> `None`).
- Widen the issue-comments query's `-q` projection so each comment object
  keeps `createdAt` alongside `body`/`author`.
- Keep `prefix = "APPROVE issue-%d/" % issue` exactly as-is (role-agnostic,
  matching `gates/ci.py._approved_roles_on_issue`).
- Add `and (not first_commit_at or c.get("createdAt", "") > first_commit_at)`
  to the `phase2 = any(...)` predicate — an approval with a missing/older
  timestamp than the branch's first commit no longer counts; a missing
  `first_commit_at` (empty `commits`, `gh` field absent) leaves the
  predicate unchanged from today (fail-open, matching the header's stated
  posture for lookup gaps).
- ISO-8601 `createdAt`/`committedDate` strings compare correctly with plain
  string `>` (both are `gh`'s standard `...Z` UTC format, same precision),
  so no date parsing library is introduced.

In `test_contract_guard.py`:
- Extend `FAKE_GH`'s `pr view` branch to also emit `commits` (a list of
  `{"committedDate": ...}`) from the fixture.
- Extend `FAKE_GH`'s `issue view` branch to pass through `createdAt` on each
  comment object already present in the fixture.
- Extend `_approve_comment` to accept a `created_at` parameter (defaulted to
  keep the 7 existing call sites unchanged).
- Add the acceptance's test matrix as new test functions:
  - prior-round approval present (its `createdAt` older than the new PR's
    head branch's first-commit `committedDate`) + new phase-1 PR body (no
    closing keyword) -> `returncode == 0` (allow).
  - same-round approval present (its `createdAt` newer than the PR's own
    head branch's first commit) + delivering PR body without `Closes` ->
    `returncode == 2` (deny), matching today's existing denial-path
    assertions.
  - same-round approval present + delivering PR body WITH `Closes #<n>` ->
    `returncode == 0` (allow) — confirms the fix doesn't turn same-round
    delivery into a false denial.
  - cross-role handoff regression (issue #312 shape): an approval for a
    *different* role than the PR's own, but newer than the PR's first
    commit, must still count as phase-2 (deny without `Closes`) — proves
    the fix stays role-agnostic and doesn't reintroduce the bypass
    `gates/ci.py._phase_from_approval` was written to close.

## Out of scope

- Reconstructing a first-class "round number" anywhere (branch names, PR
  bodies, comments) — out of scope per the survey: no such field exists in
  this repo's data model, and the issue's acceptance only asks for
  round-scoping via the time/role proxies, not an explicit round counter.
- Changing the branch-naming convention or the `APPROVE issue-<n>/<role>`
  comment format itself — both are contract v3 conventions this fix reads,
  not writes.
- The unreached fail-open paths already covered by issue #443 (cross-repo
  `-R`/URL/`cd` resolution) — untouched by this change, existing tests for
  them stay as regression coverage.

## How you'll know it worked

`python3 -m pytest on-the-record/hooks/test_contract_guard.py -v` passes:
the 7 existing target-repo tests unchanged, plus the 4 new round-scoping
matrix tests (prior-round-allow, same-round-deny, same-round-with-Closes-
allow, cross-role-handoff-still-phase2) covering the issue's stated
acceptance check plus the #312 regression the warrant hunt surfaced.

Irony noted per instruction: the delivering (phase-2) PR for this very issue
will itself need `Closes #577` in its body, and will be evaluated by the
pre-fix version of this same gate until the fix it contains lands — i.e.
the delivering PR judges itself with the old, later-corrected logic. This is
unavoidable (a gate cannot retroactively apply its own not-yet-merged fix to
its own merge), and is not a defect in the fix, just a one-time bootstrap
quirk worth recording.
