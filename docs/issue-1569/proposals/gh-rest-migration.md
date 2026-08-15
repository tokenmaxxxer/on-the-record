---
status: proposed
files:
  - gates/gh_rest.py
  - gates/requirement_linkage.py
  - gates/acceptance_gate.py
  - gates/requirement_intake_consult.py
  - gates/pr_reference.py
  - gates/issue_bundling.py
  - gates/check_runner.py
  - gates/test_gh_rest.py
  - spawn.py
---

## Request

Gate/hook read-only lookups of issue and PR bodies/titles go through
GraphQL-backed `gh issue view` / `gh pr view`, which shares the 5000/hr
GraphQL quota with every other role session's issue/PR reads. When that pool
is exhausted, these gates fail-close and refuse spawns even though the
separate REST quota is alive. Move the single-item read-only lookups to
`gh api repos/{owner}/{repo}/...` REST calls; fail-closed semantics on read
failure are unchanged.

## Constraints

- Fail-closed unchanged: a REST failure still refuses (검사 불가는 통과가
  아니다) — only the cross-pool coupling is removed, not the safety property.
- `gates/requirement_linkage.py::check(root, issue)` is the priority
  instance and must be covered by a hermetic transport-stub test per the
  issue's acceptance criteria.
- Bulk/list operations (`gh pr list`, `gh issue list --search`,
  `gh pr view --json statusCheckRollup`) are a different REST surface and
  volume shape (survey.md) — out of scope here.

## Rationale

Considered keeping `gh issue view`/`gh pr view` and adding a REST fallback
only on GraphQL failure (try GraphQL, catch rate-limit, retry via REST).
Rejected: it still spends a GraphQL call (and its rate-limit error) on every
read before falling back, so a session under sustained GraphQL exhaustion
pays that failed round-trip on every gate check — the coupling issue #1569
describes is reduced, not removed. Migrating outright to REST-only removes
the GraphQL dependency from these paths entirely, matching requirement 1's
literal ask ("replace read-only lookups with REST equivalents").

For the owner/repo needed to build `repos/{owner}/{repo}/...`, considered
`gh repo view --json nameWithOwner` — rejected, since that call is itself
GraphQL-backed and would silently reintroduce a GraphQL dependency in the
same code path being migrated off it. Chose `git remote get-url origin`
instead (no gh call, no quota of either kind).

## What will be done

- Add `gates/gh_rest.py`: `owner_repo()` (via `git remote get-url origin`),
  `fetch_issue()`, `fetch_issue_body()`, `fetch_issue_title()`,
  `fetch_pr_body()`, `fetch_pr_title()`, each wrapping
  `gh api repos/{owner}/{repo}/{issues,pulls}/{n}`, each accepting an
  injectable `run` callable for hermetic testing, each returning `None` on
  any failure (git remote missing, `gh api` non-zero exit, unparsable JSON).
- Replace the seven `gh issue view`/`gh pr view` call sites listed in
  survey.md with calls into `gates/gh_rest.py`, deleting each module's local
  `_issue_view_body`/`_pr_view` duplicate.
- Add `gates/test_gh_rest.py`: hermetic tests using a stub `run` callable —
  (a) REST succeeds -> body returned; (b) REST fails -> `None`; (c) no `gh`
  (non-zero exit stub) -> `None`.
- Add the acceptance-mandated hermetic test for the priority instance: a
  stub `run` that returns a rate-limit-shaped error for any `gh issue
  view`/`gh pr view`-shaped argv and a valid body for `gh api .../issues/<n>`
  argv, proving `requirement_linkage.check()` succeeds purely off the
  REST-shaped path (it no longer calls the GraphQL-shaped command at all).

## Accumulation

Before this change, each gate that needed an issue/PR body copy-pasted its
own `subprocess.run(["gh", "issue"/"pr", "view", ...]) -> json.loads ->
.get(...)` block (survey.md counts seven such copies). Left alone, a future
gate needing the same lookup would add an eighth copy. `gates/gh_rest.py` is
the fix for that: the one place that turns `(repo, issue-or-pr number)` into
a body/title via REST, for any future gate to import instead of
reimplementing the `subprocess.run`/`json.loads` shape again. This proposal
does not add a lint/gate mechanically enforcing that import — no such
enforcement existed for the pre-change duplication either — so recurrence is
addressed by having an obvious shared helper to reach for, not by a
mechanical check.

## Out of scope

- `gates/ci.py`, `gates/closure_sweep.py`, `gates/spawn_on_pr.py`,
  `gates/open_work.py`, `gates/landing_readiness.py` — bulk/list/status-check
  reads, different REST surface and shape (survey.md).
- Any write/mutating `gh` call (`gh pr comment`, `gh pr create`, etc.).

## How you'll know it worked

- `python3 gates/test_gh_rest.py` and the priority-instance hermetic test
  pass.
- `grep -n '"issue", "view"\|"pr", "view"' gates/requirement_linkage.py gates/acceptance_gate.py gates/requirement_intake_consult.py gates/pr_reference.py gates/issue_bundling.py gates/check_runner.py spawn.py` returns no matches in those seven read-lookup paths.
