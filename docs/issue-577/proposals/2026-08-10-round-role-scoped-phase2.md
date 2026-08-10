files:
  - on-the-record/hooks/contract-guard.sh
  - on-the-record/hooks/test_contract_guard.py

## Request

`contract-guard.sh`'s phase-2 check treats an issue as phase-2 if ANY
`APPROVE issue-<n>/<role>` comment ever existed on it, regardless of role or
round. On a multi-round issue this denies every new round's phase-1
proposal PR (no `Closes` obligation should apply to it), which forced an
`ORCHESTRATE_OFF=1` bypass live on issue #476. Scope the phase-2 obligation
to the delivering PR of the same (role, round): a prior-round approval must
not block a new phase-1 PR; a same-round approval must still require the
delivering PR's `Closes`.

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
two different roles approve back-to-back within the same round window, and
it does not fix the role-blindness half of the defect at all — the issue's
acceptance explicitly requires the fix to be both round- and role-aware, not
just round-aware.

Chosen approach: scope the phase-2 scan two ways simultaneously —
(a) **role-match**: build the approval prefix from the PR's own role
(`headRefName`'s `issue-<n>/<role>` suffix), not just the issue number, so
an approval for a different role never counts; (b) **time-match**: only
comments with `createdAt` strictly newer than the head branch's first
commit's `committedDate` count. Both signals are already present in fields
`gh pr view` already returns; only the requested field list needs widening
(`headRefName`, `commits`), plus selecting `createdAt` on the existing issue
comments query. This is the minimum-viable variant the issue itself names,
using only calls the script already performs.

## What will be done

In `contract-guard.sh`:
- Widen `pr_data = gh_json("pr", "view", pr, "--json", "body,number")` to
  also request `headRefName,commits`.
- Derive `role = pr_data.get("headRefName", "").rsplit("/", 1)[-1]` (empty
  string if unparseable — falls through to fail-open below).
- Derive `first_commit_at` from `pr_data.get("commits") or []` — the
  earliest `committedDate` among the PR's commits (empty list -> `None`).
- Widen the issue-comments query's `-q` projection so each comment object
  keeps `createdAt` alongside `body`/`author`.
- Replace `prefix = "APPROVE issue-%d/" % issue` with a role-scoped prefix
  `"APPROVE issue-%d/%s" % (issue, role)` — only used when `role` is
  non-empty; when `role` can't be parsed from `headRefName`, fall back to
  the current issue-number-only prefix (fail-open: an unparseable branch
  name must not silently start allowing bypasses in the other direction —
  see Out of scope).
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
- Extend `FAKE_GH`'s `pr view` branch to also emit `headRefName` and
  `commits` (a list of `{"committedDate": ...}`) from the fixture.
- Extend `FAKE_GH`'s `issue view` branch to pass through `createdAt` on each
  comment object already present in the fixture.
- Extend `_approve_comment` to accept `role` and `created_at` parameters
  (defaulted to keep the 7 existing call sites unchanged).
- Add the acceptance's test matrix as new test functions:
  - prior-round approval present (older than head branch's first commit, OR
    for a different role) + new phase-1 PR body (no closing keyword) ->
    `returncode == 0` (allow).
  - same-round approval present (newer than head branch's first commit,
    matching role) + delivering PR body without `Closes` -> `returncode ==
    2` (deny), matching today's existing denial-path assertions.
  - same-round approval present + delivering PR body WITH `Closes #<n>` ->
    `returncode == 0` (allow) — confirms the fix doesn't turn same-round
    delivery into a false denial.

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
the 7 existing target-repo tests unchanged, plus the 3 new round/role-matrix
tests (prior-round-allow, same-round-deny, same-round-with-Closes-allow)
covering the issue's stated acceptance check.

Irony noted per instruction: the delivering (phase-2) PR for this very issue
will itself need `Closes #577` in its body, and will be evaluated by the
pre-fix version of this same gate until the fix it contains lands — i.e.
the delivering PR judges itself with the old, later-corrected logic. This is
unavoidable (a gate cannot retroactively apply its own not-yet-merged fix to
its own merge), and is not a defect in the fix, just a one-time bootstrap
quirk worth recording.
