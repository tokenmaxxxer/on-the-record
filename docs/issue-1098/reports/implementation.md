---
code_under_review:
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/post-landing-obligation-gate.sh
  - on-the-record/hooks/test_post_landing_obligation_gate.py
  - gates/landing_obligation.py
  - gates/test_landing_obligation.py
  - gates/landing_readiness.py
  - gates/test_landing_readiness.py
  - docs/handbooks/hooks.md
  - docs/issue-1098/decisions/2026-08-12-post-landing-obligation.md
  - docs/specs/enforcement-boundary.md
  - docs/specs/generated-paths.md
type: feature
breaking: false
canonical: python3 -m pytest gates/test_landing_obligation.py gates/test_landing_readiness.py on-the-record/hooks/test_post_landing_obligation_gate.py -q — result: pass, 37 passed, executed this turn against sha 7df3f55
verdict: pass
loop_state: committing
---

## What was done

canonical: docs/issue-1098/proposals/2026-08-12-post-landing-verify-refile-loop.md
Built the post-landing verify-refile loop per the approved phase-1
proposal's work list, all landed in commit 7df3f55:

1. `gates/landing_obligation.py` (canonical:
   gates/landing_obligation.py) — new module, same shape as
   `reexecution_gate.py`: `open_obligation`,
   `resolve_with_reexecution_verdict`, `list_open_obligations`, writing/
   reading `.landing-obligations/<issue>-<role>-<pr>.json`.
2. `gates/landing_readiness.py` (canonical: gates/landing_readiness.py,
   the new `obligation_blocking_cause` function) — scoped to the PR's
   own record path, same shape as `reexecution_blocking_cause`.
3. `on-the-record/hooks/post-landing-obligation-gate.sh` (canonical:
   on-the-record/hooks/post-landing-obligation-gate.sh) — new
   `PostToolUse` (`Bash`) hook, registered in `hooks.json`'s existing
   `Write|Edit|MultiEdit|Bash` PostToolUse group (canonical:
   on-the-record/hooks/hooks.json). Reuses `merge-allow-gate.sh`'s
   strict shlex-based `gh pr merge` command-shape check; resolves
   issue/role via `gh pr view <pr> --json headRefName,mergeCommit`.
4. `docs/handbooks/hooks.md` (canonical: docs/handbooks/hooks.md) — new
   `post-landing-obligation-gate.sh` section.
5. `docs/issue-1098/decisions/2026-08-12-post-landing-obligation.md`
   (canonical: same path) — ADR.
6. `docs/specs/enforcement-boundary.md` and
   `docs/specs/generated-paths.md` (canonical: both paths) gained rows
   for the two new modules, required by `gate-registration-guard.sh`'s
   mechanical newly-added-module check.

canonical: docs/issue-1098/proposals/2026-08-12-post-landing-verify-refile-loop.md
Refiling (loop step 2) is intentionally left to `roles_due.py`'s
existing board-condition trigger — the proposal itself cuts that scope.

## Why

canonical: docs/issue-1098/proposals/2026-08-12-post-landing-verify-refile-loop.md
Requirement (northpole req#3, req#5): after a landing, verification and
refiling of found defects must become the default next step, with no
operator prompt required each round.

canonical: `gh issue view 1098` comment thread, read at session start
Approved via the issue-comment `APPROVE issue-1098/implementation` path
per contract v3 s19's single-account mode.

## Upstream

Based on: docs/issue-1098/proposals/2026-08-12-post-landing-verify-refile-loop.md

## What did not work

canonical: on-the-record/hooks/merge-allow-gate.sh (lines 134-153,
orchestrator-only `if role: sys.exit(0)` block)
- Wrote `post-landing-obligation-gate.sh`'s issue/role resolution to read
  the calling session's current branch (`git branch --show-current`)
  against the `issue-<n>/<role>` shape.
  canonical: warrant-hunter agent reply, this session, before-landing
  dispatch (stance: assume this change and another plugin's rule cancel
  each other)
  The hunt found this never matches on a real merge: the orchestrator
  merges from the base checkout, never from the PR's own
  `issue-<n>/<role>` branch, per the cited merge-allow-gate.sh
  invariant — the hook silently no-opened on every real merge.
  canonical: on-the-record/hooks/post-landing-obligation-gate.sh (the
  "issue/role resolution from the PR's own head branch" block)
  Fixed by resolving issue/role from the merged PR's own `headRefName`
  via `gh pr view` instead of the caller's branch, and added a
  regression test in `test_post_landing_obligation_gate.py`
  (`t_merge_from_orchestrator_base_branch_still_resolves_via_pr_view`).
- `git commit` denied twice on false-positive matches inside
  `docs/specs/enforcement-boundary.md`'s own pre-existing prose (rows
  documenting the `acceptance: ...`/`live-fire: ...` citation shapes as
  placeholder examples, which the citation-scanning gates matched as
  real citations).
  canonical: commit 7df3f55's own trailer text
  Worked around via the documented `Acceptance-recheck-N/A:`/
  `Live-fire-recheck-N/A:` commit-trailer escape hatches — no code
  change.
- `gates/test_landing_obligation.py` was first written with
  `unittest.TestCase` classes.
  canonical: on-the-record/hooks/live-fire-test-guard.sh (the
  `outcome_fns` regex)
  `live-fire-test-guard.sh` denied the commit because its regex only
  counts top-level, unindented `def t_*`/`def test_*` functions, not
  indented class methods. Rewrote the file as top-level `t_*`
  pytest-style functions to satisfy the mechanical count.
- `post-landing-obligation-gate.sh` genuinely has exactly one exit-code
  outcome (`PostToolUse` cannot deny), so `live-fire-test-guard.sh`'s
  ">= 2 distinct returncode ==" requirement cannot be satisfied by
  design. Used the guard's own documented `Live-fire-N/A: <reason>`
  commit-trailer escape hatch instead of fabricating a second exit path.

## Open findings

canonical: warrant-hunter agent reply, this session, before-landing
dispatch (stance: assume this change and another plugin's rule cancel
each other)
None open — the one finding surfaced (branch-resolution mismatch
against `merge-allow-gate.sh`'s orchestrator-only invariant) is resolved
in commit 7df3f55, per "## What did not work" above. The hunter could
not persist its own record file under
`docs/issue-1098/reports/architecture/` — `board-gate.sh` scopes that
subtree to the `architecture` role, and this session runs as
`implementation` — so it relayed the finding directly in its reply
instead of bypassing the scope gate.

canonical: python3 -m pytest gates/test_landing_obligation.py gates/test_landing_readiness.py on-the-record/hooks/test_post_landing_obligation_gate.py -q — result: pass, executed this turn against sha 7df3f55
closed_checks:
```
$ python3 -m pytest gates/test_landing_obligation.py gates/test_landing_readiness.py on-the-record/hooks/test_post_landing_obligation_gate.py -q
.....................................
37 passed in 0.47s
```
- gates/test_landing_obligation.py — covered above.
- gates/test_landing_readiness.py's `ObligationBlockingCause` class — covered above.
- on-the-record/hooks/test_post_landing_obligation_gate.py — covered above.

## Next steps

canonical: docs/issue-1098/decisions/2026-08-12-post-landing-obligation.md
No action from this record is needed to open the PR. A follow-up sweep
(periodic/`Stop`-hook-driven, reading `gh pr list --json state` for
merges that bypass `gh pr merge`) is named as future work in the cited
ADR's "## Known gap" section and stays out of this proposal's scope.

## Resolution path

N/A — no open findings remain blocking landing.
