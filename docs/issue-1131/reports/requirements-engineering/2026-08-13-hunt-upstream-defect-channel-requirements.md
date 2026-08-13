---
proposal: docs/issue-1131/proposals/2026-08-13-upstream-defect-channel-requirements.md
---

# Hunt record --- upstream-defect-channel-requirements (issue #1131)

## after-proposal --- stance 0: assume the gate just touched is bypassable --- find the bypass

Verdict: FINDING --- the described upstream-defect-scope-guard mechanism (part of #1131's phase-1 plan) is scoped to the literal `gh pr create` command shape (checking cwd / --repo), which leaves other pull-request-opening call shapes unguarded: `gh api -X POST repos/{owner}/{repo}/pulls`, `gh api graphql` with a createPullRequest mutation, GH_REPO-env-var-driven `gh pr create` with no --repo flag and cwd not literally the upstream repo (e.g. a worktree/symlink), or hub pull-request / a raw curl against the GitHub REST API.
Kind: design-error
Seed: docs/issue-1131/proposals/2026-08-13-upstream-defect-channel-requirements.md (item 5 -- the new hook file description); compared against the existing shape-keyed convention in on-the-record/hooks/gh-write-allow-gate.sh (five verb shapes, `gh pr create` itself intentionally absent from it).
cap_seconds: 180
tier: size:large
diff_stat_lines: 313
started_at: 2026-08-13T00:00:00Z
ended_at: 2026-08-13T00:05:00Z

### Reproduce
The proposal text (item 5) states the guard's check as a PreToolUse
(Bash) deny gate that refuses any `gh pr create` invocation whose
working directory or --repo argument resolves to the upstream
on-the-record repo from within this channel's own code path.

Given that description, a call shape that never invokes the literal
`gh pr create` verb, or that resolves the target repo through a
mechanism other than cwd/--repo, is not covered by the stated check
surface. Two concrete evasions implied directly by the proposal's own
wording:

1. `gh api -X POST repos/tokenmaxxxer/on-the-record/pulls -f title=... -f head=... -f base=main` -- same effect as `gh pr create` (opens a pull request against upstream), but the command's verb/subcommand is `api`, not the create verb, so a guard keyed on the specific verb (matching the sibling gh-write-allow-gate.sh's documented shape-only, verb-keyed matching convention) would not recognize it as the shape to deny.
2. `GH_REPO=tokenmaxxxer/on-the-record gh pr create --title ... --body ...` run from a directory that is not itself the upstream repo (e.g. the consumer repo, or any scratch dir) -- the proposal's stated check surface is "working directory or --repo argument"; the GH_REPO environment variable is a third, standard gh resolution path (documented gh behavior: env var takes precedence over cwd-inferred repo when no --repo flag is given) that the stated check does not mention inspecting.

### Observed
The proposal's plan (as written) defines the guard's detection surface as
exactly two signals -- cwd and --repo -- on exactly one command verb. No
mention of gh api POST-to-/pulls, GraphQL createPullRequest, GH_REPO,
or non-gh pull-request-opening tooling (hub, raw curl) appears anywhere
in the proposal or its linked artifacts (current-state-survey.md, scout
brief). A consumer session's report-upstream command path filing through
any of these alternate shapes would open an upstream pull request while
the "issues only, never PRs" structural guarantee the operator
constraint demands is silently not enforced for that call.

### Expected
Either the guard's detection surface should be stated broadly enough to
cover the actual defect surface (any request that opens a pull request
against the upstream repo -- via gh api, GraphQL, GH_REPO, or non-gh
tooling), or the proposal should explicitly scope the guarantee down to
covering only the one command verb it names, and note the remaining gap
as an accepted residual risk, the same way it explicitly scoped out
touching gh-write-allow-gate.sh. As written, the "structurally enforced,
not advisory" claim in the Constraints section is broader than what the
described mechanism in item 5 can actually deliver.

(issue #1131)
