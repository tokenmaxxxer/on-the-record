---
proposal: docs/issue-1098/proposals/2026-08-12-post-landing-verify-refile-loop.md
---

# Hunt record — post-landing-verify-refile-loop

## after-proposal — stance 1: assume the gate/mechanism is bypassable — find the bypass

canonical: docs/issue-1098/proposals/2026-08-12-post-landing-verify-refile-loop.md:39-48
Verdict: FINDING — obligation creation is scoped, by the proposal's own text, to "only on a *successful* [merge] for a resolvable PR number", detected by tokenizing one specific Bash command shape (merge-allow-gate.sh's shlex check). No other way of noticing "this PR is now merged" is described anywhere in the proposal.
Kind: design-error
Seed: docs/issue-1098/proposals/2026-08-12-post-landing-verify-refile-loop.md (docs-only, no code yet)
cap_seconds: 60
tier: default
diff_stat_lines: 175 (new proposal file)
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:01:00Z

### Reproduce
canonical: docs/issue-1098/proposals/2026-08-12-post-landing-verify-refile-loop.md:67-76
The proposal's `obligation_blocking_cause` description (cited above) says it adds a blocking cause only when "an 'open' or 'failing' obligation for that PR's own issue/role" is found — i.e. only when the obligation *file* is present on disk. The description names no other input.

canonical: docs/issue-1098/proposals/2026-08-12-post-landing-verify-refile-loop.md:141-142
The proposal's own listed test assertion (cited above) reads: "a landing with no obligation ever opened stays silent (empty-state requirement)". The proposal does not describe any way for that assertion, or for `obligation_blocking_cause`, to distinguish "no obligation file because verification already happened" from "no obligation file because the merge command never matched the hook's tokenizer".

Scenario built from those two citations: take any PR that reaches the repository's landed state through a command shape other than the one the hook tokenizes (e.g. GitHub's web-UI merge button, a raw REST call, an alternate CLI wrapper). No `PostToolUse` event with the recognized shape fires, so per md:36-48 the hook's "one action" (write the obligation record) never runs, and no `.landing-obligations/<issue>-<role>-<pr>.json` file is created for that PR.

### Expected
canonical: docs/issue-1098/proposals/2026-08-12-post-landing-verify-refile-loop.md:17-20
The proposal's stated intent (cited above) is that verification "must become the default next step of any installed session, with no operator prompt required each round".
canonical: docs/issue-1098/proposals/2026-08-12-post-landing-verify-refile-loop.md:36-48
Given the citations above, that guarantee holds only for a PR that lands shaped exactly like the tokenizer's expected command; the proposal names no fallback that derives obligation state from the PR's actual landed status (e.g. via the GitHub API) for PRs landing outside that shape, and the empty-state test criterion at md:141-142 is written in a way that cannot tell the two absent-file cases apart.

## before-landing

canonical: `git status --short` (read directly this turn) — every path
staged this phase sits under `docs/issue-1098/` (the proposal and this
hunt record; no code file exists yet). docs-only fast path applies: no
before-landing hunt dispatch this phase.
