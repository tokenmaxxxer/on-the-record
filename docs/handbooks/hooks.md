# Commit-time gate hooks

`on-the-record/hooks/hooks.json` registers `PreToolUse` (`Bash`) hooks
that inspect a `git commit` attempt before it lands and can deny it
(exit 2) when they positively determine a violation. All of them fail
open (exit 0) on environment gaps — missing `python3`/`git`, a
non-commit command, or nothing relevant staged — and all respect the
`ORCHESTRATE_OFF` kill switch (any value other than empty/`0`/`false`/
`no`/`off` disables the hook for that invocation).

## role-axis-completeness-guard.sh (issue #650)

Denies `git commit` when the staged `roles/*.json` set violates axis
completeness: `gates/role_spec_shape.py`'s `check_axis_ownership` (each
of the five fixed methodology axes — `alignment`,
`maintenance_complexity`, `external_burden`, `attack_potential`,
`performance` — must be owned by exactly one role across the whole set)
and `check_role_judgment_axes` (a role's own `judgment_axes` array, when
present, must only name axes from that closed set).

Evaluates the WHOLE `roles/*.json` set, not just the staged delta: staged
paths are read via `git show :<path>` (what would actually land), every
other `roles/*.json` file is read from the working tree, since ownership
is a property of the assembled set.

Imports `gates/role_spec_shape.py` rather than re-porting the check logic
(same precedent `role-spec-reference-guard.sh` set for this module). The
packaged `on-the-record/gates` copy of that module can lag the top-level
`gates/` copy — this hook tries each candidate gates directory
(`on-the-record/gates`, then the top-level `gates/`) in turn and uses the
first one that actually exposes both `check_axis_ownership` and
`check_role_judgment_axes`, rather than hard-coding a single path that
may be stale.

Wires a real operational caller for the axis-completeness check
(hunt #628 finding on issue #650): the check previously had a
`--roles-dir` CLI entrypoint with zero callers outside its own unit
tests — the same dead-code class already fixed once in #594/#586.

Regression coverage: `on-the-record/hooks/test_role_axis_completeness_guard.py`
drives the hook script itself (subprocess, real git repo fixtures), not
`role_spec_shape.py`'s CLI.

## post-landing-obligation-gate.sh (issue #1098)

`PostToolUse` (`Bash`), registered alongside `retry-loop-bound.sh post` in
the same `Write|Edit|MultiEdit|Bash` group. Opens a post-landing
verification obligation after a successful `gh pr merge` — northpole
req#3/req#5's "every landed fix is verified by actually running the
changed behavior" needs a default, no-operator-prompt-required tracked
state to hang off of; before this hook, only a human remembering to run
the loop by hand produced that state.

Command-shape detection reuses `merge-allow-gate.sh`'s strict shlex-based
`gh pr merge` / `cd DIR && gh pr merge` tokenization (issue #824) — the
same two recognized shapes, no other chaining/substitution operator
tolerated anywhere in the tail. Success is a heuristic over the
`tool_response` text (no exit-code field is available in the
`PostToolUse` payload for `Bash`) — the same substring-based posture
`gates/landing_readiness.py`'s own `_pr_checks_summary` already uses for
`gh pr checks` output; a handful of known gh-merge failure phrases
("failed to merge", "graphql error", "could not merge", "is not
mergeable") suppress obligation-opening.

Issue/role resolution reads the merged PR's own `headRefName` via
`gh pr view <pr> --json headRefName,mergeCommit` and expects the
`issue-<n>/<role>` shape contract v3 already mandates per branch — NOT
the caller's own current branch (before-landing warrant-hunter finding:
`gh pr merge` is orchestrator-only per `merge-allow-gate.sh`'s own
invariant, and the orchestrator merges from the base/main checkout, so
reading the caller's branch never matched on the one call shape that
actually happens). A `headRefName` that does not match is a no-op (fail
open — no false obligation on an unresolvable branch). On a match, it
shells out to `gates/landing_obligation.py open` to write
`.landing-obligations/<issue>-<role>-<pr>.json`
(`{status: "open", pr, sha, issue, role, opened_at}`), using the PR's
`mergeCommit.oid` when available, else `HEAD` in the caller's checkout.

Resolution composes with the existing `reexecution_gate.py` verdict
instead of re-implementing execution:
`gates/landing_obligation.py:resolve_with_reexecution_verdict` flips the
obligation to `"resolved"` on a `pass` verdict that post-dates
`opened_at`, or to `"failing"` on `fail`/`error`.
`gates/landing_readiness.py:obligation_blocking_cause` turns an
`"open"`/`"failing"` obligation into a `blocking_causes` entry scoped to
the owning PR's own record path (`docs/issue-<n>/reports/<role>.md`),
the same scoping `reexecution_blocking_cause` already established (ADR
§6) to avoid a `gates/`-prefix cause over-covering unrelated PRs.

Known gap (after-proposal hunt,
docs/issue-1098/reports/architecture/2026-08-12-hunt-post-landing-verify-refile-loop.md):
a PR merged through the GitHub web UI, a raw REST call, or another CLI
wrapper never fires this `PostToolUse` command-shape trigger, so no
obligation is opened for it. Resolution path (phase-2, out of this
write set): a periodic or `Stop`-hook-driven reconciliation pass over
`gates/landing_readiness.py`'s existing `gh pr list --json state` read,
treating any actually-merged PR with no obligation on record as
`"open"`.

Regression coverage: `on-the-record/hooks/test_post_landing_obligation_gate.py`
drives the hook script itself (subprocess, real git repo fixtures),
proving it opens an obligation only on an actually-successful `gh pr
merge` for a resolvable PR number on an `issue-<n>/<role>` branch, and is
a no-op for every other Bash command, a failed-merge response, a
chained-command bypass attempt, a non-issue-role branch, and an implicit
current-PR merge.
