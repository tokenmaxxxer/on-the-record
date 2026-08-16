---
code_under_review:
  - path: spawn.py
  - path: tests/test_spawn.py
loop_state: reported
type: review
canonical: PR #1691 (issue-1688/implementation, commit 10b23780 + 24a375f2), compared against issue #1688 body
verdict: fail
---

## What was done

Phase-2 conformance review of PR #1691 (`issue-1688/implementation`) against
issue #1688's acceptance criteria. Approval for build-now delivery was
already posted as the exact-string issue comment `APPROVE
issue-1688/conformance-review` by `JiwonJung94` (listed in
docs/specs/approvers.md), so this record and its verdicts are phase-2
output delivered in this same PR.

Read: issue #1688 body (`gh issue view 1688`), the implementation session's
own proposal, survey, and report on branch `issue-1688/implementation`
(commits 10b237807b662ce5c7afa72b1bcb5df60f1bb05c and
24a375f2f6e397e2d4b6ed9d3dd7b4c6567f0688), and the diff
`git diff $(git merge-base issue-1688/implementation origin/main) issue-1688/implementation`
covering `spawn.py` and `tests/test_spawn.py`.

canonical: git worktree add /tmp/wt-1688-impl issue-1688/implementation; cd /tmp/wt-1688-impl && python3 -m pytest -q tests/test_spawn.py -k "board_wide_sweep_no_change or board_wide_sweep_delta_narrows or board_wide_sweep_full_rescan or board_wide_sweep_cold_cursor or board_wide_sweep_gh_delta_error or requirement_drift_delta_mode" — executed live this session

derived:
```
6 passed in 1.29s
```
(worktree checked out at issue-1688/implementation, commit 24a375f2)

## Per-requirement verdicts

1. **No-change tick: exactly one conditional probe, zero sweep detail
   fetches, explicit "no-change (delta empty)" line.**
   Verdict: **Present**. `spawn.py:_board_wide_sweep` calls
   `gh_delta.fetch_delta(root, slug, "issues")` once, and on
   `classification == "no-change"` returns early after
   `_run_local_only_signals(skip_requirement_drift=True)` (which itself
   makes zero `gh` calls) — no `find_violations`, no
   spawn-on-pr/spawn-coverage calls.
   canonical: pytest run above — `test_board_wide_sweep_no_change_skips_detail_fetches` result: pass (`fetch_delta` called once, `find_violations` called zero times, log contains `no-change (delta empty)`)

2. **Delta with 2 changed issues triggers re-evaluation of exactly those
   2 subjects.**
   Verdict: **Present, scoped to issues only** — see finding (a) below for
   the PR gap. For issue-only deltas: `find_violations` receives a
   `subjects` dict filtered to `board(root)` entries whose numeric suffix
   is in the delta's changed-number set, and `requirement_drift(root,
   changed_numbers=...)` re-fetches only those numbers via
   `_fetch_issue_or_pr_via_cache` (routed through `gh_cache.cached_get`),
   reusing `runs/requirement_drift_cache.json` for the rest.
   canonical: pytest run above — `test_board_wide_sweep_delta_narrows_closure_sweep_to_changed_subjects` and `test_requirement_drift_delta_mode_fetches_only_changed_and_reuses_cache` result: pass

3. **Full-rescan classifications flow through with explicit log lines.**
   Verdict: **Present**. `classification == "full-rescan"` prints an
   explicit line naming the possible causes (cursor loss/corruption, page
   overflow, or reconciliation interval) and falls through unchanged to
   the pre-existing full-board logic (`subjects=None`,
   `changed_numbers=None`). `classification == "error"` similarly falls
   through with its own explicit line — not itself in the acceptance
   text but a reasonable conservative extension of the same fall-through
   contract.
   canonical: pytest run above — `test_board_wide_sweep_full_rescan_falls_through_and_logs`, `test_board_wide_sweep_cold_cursor_uses_same_full_rescan_path`, `test_board_wide_sweep_gh_delta_error_falls_back_to_full_logic` result: pass

4. **Detail fetches (issue bodies etc.) go through `gh_cache`'s shared
   read-through cache.**
   Verdict: **Surface**.
   derived: `git diff $(git merge-base issue-1688/implementation origin/main) issue-1688/implementation -- gates/closure_sweep.py` — empty output
   Only `requirement_drift`'s delta-mode per-number recheck
   (`_fetch_issue_or_pr_via_cache`) is routed through `gh_cache.cached_get`.
   `gates/closure_sweep.py` (`_issue_view`, `_pr_view_state_body`,
   `_pr_index_all`) is untouched by this PR and still calls `gh issue
   view` / `gh pr view` via bare `subprocess.run`, bypassing `gh_cache`
   entirely for closure-sweep's own narrowed re-evaluation. The narrowing
   itself (fewer subjects) still cuts total call volume, but the specific
   "route through gh_cache" instruction is only half-wired.

5. **`gh_budget` (#1681) backstop meters the watchdog class as
   last-resort guard.**
   Verdict: **Absent**, and correctly documented as such by the
   implementation session — #1681 has not landed, `gh_budget` does not
   exist in the repo, and the issue's own text allows omitting this
   sub-point. No conformance gap: matches the issue's stated allowance.

6. **Empty state — cold cursor performs one documented initial full-scan,
   then converges to delta mode; no silent fallback to world-rescan
   except the explicit full-rescan classifications.**
   Verdict: **Present**. Cold/missing cursor drives `gh_delta.fetch_delta`
   to return `classification == "full-rescan"` itself (per `gh_delta`'s
   own contract, reviewed under #1682), which the wiring routes through
   the same explicitly-logged fall-through as any other full-rescan — no
   separate silent branch.
   canonical: pytest run above — `test_board_wide_sweep_cold_cursor_uses_same_full_rescan_path` result: pass

7. **Live check — after reinstall, a 15-minute quiet window shows GraphQL
   burn near zero (vs baseline 111/min active; a quiet-window pre-fix
   baseline measured for like-for-like), and watchdog lines show
   "no-change (delta empty)" on quiet ticks.**
   Verdict: **Unverifiable** from this PR's own artifacts.
   unverifiable: the implementation report's Test evidence section
   contains only the two pytest command results (fast + slow suites);
   there is no live-run log, no quiet-window GraphQL burn number, and no
   pre-fix baseline measurement anywhere in the PR. The acceptance item
   is explicitly `provenance: executed-live` — an executed-unit test
   result cannot substitute for it, and no live evidence was produced or
   cited by the implementation session.

## Findings

- **(a) PR changes are invisible to delta mode — "issues incl PRs" is not
  met.** `spawn.py`'s single conditional probe calls
  `gh_delta.fetch_delta(root, slug, "issues")` only.
  derived:
  ```
  sed -n '190,196p' gates/gh_delta.py
      if resource == "pulls":
          filtered = [i for i in items if "pull_request" in i]
      else:
          filtered = [i for i in items if "pull_request" not in i]
  ```
  `resource == "issues"` filters the raw fetch to drop every item carrying
  a `pull_request` key — PR items are excluded from the returned list
  entirely. Classification (`no-change`/`delta`/`full-rescan`) is computed
  from the *unfiltered* `items` before this filter runs, so a tick where
  only a PR changed (no issue changed) yields `classification == "delta"`
  with an **empty** filtered/changed-number set: `_board_wide_sweep`
  narrows `find_violations`'s `subjects` to `{}` and calls
  `requirement_drift(root, changed_numbers=set())`, evaluating zero
  subjects — a narrowed run that looks routine but silently covers less
  than a true no-change skip would announce. Pre-existing
  `requirement_drift` scanned all open issues+PRs every call, and
  closure-sweep's board includes PR-linked subjects — both consumers lose
  PR-triggered re-evaluation under this wiring. The implementation
  session's own survey and its report's "Open findings" section both
  note the `resource="issues"` filter's PR-exclusion behavior, but the PR
  ships with the gap unresolved rather than adding a second
  `resource="pulls"` probe or otherwise reconciling with the "issues incl
  PRs" wording — the issue text's "ONCE per resource (issues incl PRs)"
  most plausibly reads as "one probe, covering the issues+PRs surface",
  not "call once and silently drop half the surface".
  Resolution path: addressed to the implementation role — either add a
  second, separately-budgeted `resource="pulls"` probe (its own delta
  cursor file, already supported by `gh_delta.py`'s per-resource
  `cursor_path`), or union classification/changed-number handling across
  both resources before narrowing `subjects`/`changed_numbers`.

- **(b) Live acceptance check never executed.** See verdict 7 above — the
  PR's only evidence is the unit-test suite; the issue's
  `provenance: executed-live` quiet-window measurement was not performed
  or cited anywhere in the PR.
  Resolution path: addressed to the implementation role — run the
  documented reinstall + 15-minute quiet-window measurement against a
  live repo, record the before/after GraphQL burn numbers and a sample of
  `no-change (delta empty)` log lines in its own report, per the issue's
  acceptance provenance requirement.

## Why

Per the conformance-review role contract: verify what PR #1691 actually
built against issue #1688's stated acceptance criteria, independent of the
implementation session's own narration of intent — reading the diff, the
tests, and running the cited test subset directly rather than trusting the
implementation report's "Test evidence" summary alone.

## Upstream

Based on: issue #1688 (`gh issue view 1688`); PR #1691 / branch
`issue-1688/implementation`, commits 10b237807b662ce5c7afa72b1bcb5df60f1bb05c
and 24a375f2f6e397e2d4b6ed9d3dd7b4c6567f0688; #1682's landed
`gates/gh_delta.py` / `gates/gh_cache.py` (reviewed separately as part of
issue #1682's own conformance review).

## Open findings

- Finding (a): PR-only changes are invisible to delta mode — real gap
  against the "issues incl PRs" wording, and a narrowed-but-empty result
  that reads as a routine successful narrow instead of announcing itself
  as a coverage loss.
  Resolution path: addressed to the implementation role, see above.
- Finding (b): the issue's live acceptance check (quiet-window GraphQL
  burn measurement) was never executed or evidenced.
  Resolution path: addressed to the implementation role, see above.
- Requirement 4 (gh_cache wiring for closure-sweep's own detail fetches)
  is only half-satisfied — `gates/closure_sweep.py`'s `_issue_view` /
  `_pr_view_state_body` / `_pr_index_all` still bypass `gh_cache`.
  Resolution path: addressed to the implementation role — route those
  through `gh_cache.cached_get` as a follow-up, or fold into the same fix
  as finding (a) since both touch the closure-sweep detail-fetch path.

## Next steps

None from this role — findings (a), (b), and the requirement-4 gap are
addressed to the implementation role for its own next PR revision or a
follow-up issue; this role does not edit `spawn.py` or the implementation
record.
