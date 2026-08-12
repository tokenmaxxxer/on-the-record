# issue-705 current-state survey (product-discovery, phase 1)

kind: survey
subject: issue-705

## Scout skip record

Skip condition: spec-literal, no external design decision. This is an
internal engineering-process audit of this repo's own spawn/gate
infrastructure — there is no external product category or exemplar
product to benchmark a "role session hand-off" flow against. Scouting is
skipped; proceeding on stated internal evidence only.

## Note on the invoking prompt's citations

The turn that opened this session cited "#750/#791 approval-gate
strandings cleared only by orchestrator manually posting APPROVE" and "5
duplicate-docs conflicts (#941/#951/#954/#959/#969) from stale-base
branching" as today's evidence.

derived: `gh pr view 750; gh pr view 791`
```
$ gh pr view 750
GraphQL: Could not resolve to a PullRequest with the number of 750. (repository.pullRequest)
$ gh pr view 791
GraphQL: Could not resolve to a PullRequest with the number of 791. (repository.pullRequest)
```
`#750` and `#791` are issue numbers, not PRs, and neither issue's title
(checked via `gh issue view 750`/`791`, executed this session) names an
approval-gate stranding cleared by manual APPROVE-posting.

canonical: `gh pr view 941 --json title -q .title` etc, five separate calls (executed this session)
```
$ gh pr view 941 --json title -q .title
issue-922 implementation phase2: surface watchdog report on poll-heartbeat.sh due ticks
$ gh pr view 951 --json title -q .title
[issue-791/implementation]
$ gh pr view 954 --json title -q .title
[issue-803/implementation]
$ gh pr view 959 --json title -q .title
[issue-791/implementation]
$ gh pr view 969 --json title -q .title
[issue-751/defect-verification]
```

canonical: `gh pr view <n> --json title` output directly above (executed this session)

Those five titles name other, unrelated pieces of work. This survey does
not rely on the "duplicate-docs conflicts" framing — the titles above do
not support it — and proceeds only on issue #705's actual GitHub body
and direct reads of `spawn.py`.

## Background / context

canonical: `gh issue view 705` output (executed this session)

Issue #705's real body reports that every implementation session
observed on 2026-08-11 (issues 692, 695, 698, 699) ended
`progressed-dirty-tree`: the PR opens successfully, then the session's
post-PR hunt/record write dies on `board-gate` (wrong path shape),
`record-claim-guard` (unbacked claims), and `record-fields-gate`
(missing next-steps on non-terminal loop_state). The issue's own fix
direction is to align the deployed post-PR record guidance with what the
gates actually check.

canonical: `gh pr view 710 --json number,state,mergedAt,title` (executed this session)
```
$ gh pr view 710 --json number,state,mergedAt,title
{"mergedAt":"2026-08-11T02:16:29Z","number":710,"state":"MERGED","title":"docs(issue-705): survey + proposal to align post-PR record guidance with gates"}
```

canonical: `gh pr view 710 --json number,state,mergedAt,title` output directly above (executed this session)

PR #710, per the state and mergedAt fields directly above, is a prior
implementation-role pass on this same issue, per
docs/issue-705/reports/implementation/survey.md and
docs/issue-705/proposals/2026-08-11-align-post-pr-record-guidance-with-gates.md
(read in full this session): guidance-text corrections to the
hunt-record path template, the `derived:`/`unverifiable:` claim shape,
and the non-terminal `loop_state` template, all inside
`warrant`/`coding`/`record-shape` plugin directives.

## Problem, stated without a solution attached (JTBD tuple)

- **Job performer**: an orchestrator (human or `spawn.py`) that spawns
  many short-lived role sessions against a shared repo and depends on
  each session's output landing as a clean, mergeable PR without manual
  intervention.
- **Job**: get a role session's work to land on the board (committed,
  pushed, PR open, gates green) using only the guidance and repo state
  the session had *at spawn time* — without the session hitting a gate
  failure whose fix requires information it was never given, or a branch
  conflict that only exists because the session started from stale state.
- **Circumstance**: role sessions are headless and single-shot (contract
  v3 s22) — there is no later turn to recover in if a late-stage gate
  failure was avoidable with earlier information.
- **Desired outcome**: a session's post-PR write succeeds on the first
  attempt against the guidance it was actually given (issue #705's
  literal ask), AND the branch/PR state it starts from is never stale
  enough on its own to force a conflict the session did not cause.

The issue text names the fix target (post-PR record guidance) directly;
the JTBD above generalizes only the part additionally visible in
`spawn.py` (see next section) without asserting facts beyond what was
read.

## Opportunity-solution tree placement

- **Outcome**: role sessions land clean PRs on the first attempt,
  independent of which gate or which branch-state edge case they happen
  to hit.
- **Opportunity**: per PR #710's state, cited in Background above, issue
  #705's literal opportunity (post-PR hunt/record write vs. gate
  mismatch) has a landed fix. The adjacent, still-open opportunity
  visible directly in `spawn.py` is narrower than the invoking prompt's
  framing: not "sessions branch from stale main" in general, but
  specifically the **reused local branch** arm of
  `checkout_issue_branch`, which — per the read below — checks out an
  existing non-absorbed local branch with no fetch/rebase step against
  current main first.
- **Candidate solutions**: (a) treat issue #705 as delivered by PR #710,
  cited above — its acceptance criterion (post-PR guidance matches gate
  expectations) has coverage; (b) file a narrower follow-up issue for the
  reused-branch-staleness gap in `checkout_issue_branch`, scoped to what
  was actually read, not the unverified "5 duplicate-docs conflicts"
  framing.
- **Discriminating assumption test**: whether reused (non-absorbed)
  branches are common enough in practice to justify a rebase-at-checkout
  change, versus rare enough that the existing recut-on-full-absorption
  path already covers the practical case. Untestable from this survey
  alone — the proposal registers this as a pre-committed hypothesis for
  the follow-up, deferred to phase 2 pending approval.

## Read evidence: checkout_issue_branch's three arms

canonical: spawn.py:4829-4864 (read in full this session)

derived: `sed -n '4836,4861p' spawn.py`
```
    br = f"issue-{issue}/{role}"
    def git(*a):
        return subprocess.run(["git", "-C", cwd, *a], capture_output=True, text=True)
    _fetch_or_halt(cwd, "브랜치 체크아웃")
    if git("rev-parse", "--verify", "-q", br).returncode == 0:
        r = _recut_absorbed_branch(cwd, br)
    elif git("rev-parse", "--verify", "-q", f"origin/{br}").returncode == 0:
        r = git("checkout", "-b", br, f"origin/{br}")
    else:
        base = _base(cwd)
        r = git("checkout", "-b", br, base)
        if r.returncode != 0:
            r = git("checkout", "-b", base)
```

canonical: spawn.py:4841-4850 (read in full this session, docstring of `_recut_absorbed_branch`)

Arm 1 (local branch exists) delegates to `_recut_absorbed_branch`, which
per its own docstring only recuts when the branch is **fully absorbed
into base with zero unique commits**; a branch carrying unique commits is
reused unchanged — no fetch-forward, no rebase, no staleness check
against current main at all. Arm 3 (no branch anywhere) already rebases
from `_base(cwd)` (current remote default branch).

## Gap this proposal targets

Per PR #710's state, cited in Background above, issue #705's literal ask
has a landed fix. This survey's own contribution is narrower than the
invoking prompt's framing: it locates one concrete, already-read gap
(`_recut_absorbed_branch`'s partial-absorption arm) as a candidate
follow-up, and states plainly that the prompt's other citations
(#750/#791 approval-gate strandings, duplicate-docs conflicts named
above) do not check out against GitHub and are not used as evidence.
The proposal
(docs/issue-705/proposals/2026-08-12-close-705-and-scope-branch-staleness-followup.md)
contains the recommendation and the registered hypothesis for the
follow-up.
