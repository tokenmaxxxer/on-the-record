---
issue: 2980
role: adversarial-review-70dec1c4
author: adversarial-review-70dec1c4
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: 00fe6e15f25c2c85d8fc7c3e741bf3581e88c7b6
loop_state: landed
type: code
breaking: false
verdict: pass
upstream:
  - path: watchdog.py
    sha: 00fe6e15f25c2c85d8fc7c3e741bf3581e88c7b6
  - path: tests/test_requirement_drift_third_state_2980.py
    sha: 00fe6e15f25c2c85d8fc7c3e741bf3581e88c7b6
---

# issue-2980 — adversarial-review-70dec1c4 record

## What was done

Independently verified PR #3023 (branch `pr-3023-review`, head
`00fe6e15f25c2c85d8fc7c3e741bf3581e88c7b6`) — issue #2980's fix making
`watchdog.requirement_drift()` report a failed lookup as its own state,
mark a retained cached verdict with when it was observed, and report
`unknown` for a subject with no prior verdict.

canonical: `gh pr view 3023` output fetched this turn (state: OPEN, head
`00fe6e15f25c2c85d8fc7c3e741bf3581e88c7b6`, base `main`).

Fetched the PR head into an isolated `git worktree`
(`git fetch origin pull/3023/head:pr-3023-review && git worktree add
/tmp/pr3023-review pr-3023-review` — the sandbox later renamed this path
to `/tmp/pr3023-review-1d3b7bc4`, same worktree/commit throughout) and
re-ran all three issue-#2980 acceptance checks myself inside it, without
citing PR #3023's own pasted test-plan results as evidence. Note:
`tests/test_requirement_drift_third_state_2980.py` is untracked on this
session's own branch (`issue-2980/adversarial-review-70dec1c4`) and
exists only on the PR branch/worktree cited below.

- acceptance: `python3 -m pytest tests/ -k requirement_drift_lookup_failure_state -q` — result:
  ```
  2 passed in 0.91s
  ```
- acceptance: `python3 -m pytest tests/ -k requirement_drift_cached_verdict_marked -q` — result:
  ```
  1 passed in 0.91s
  ```
- acceptance: `python3 -m pytest tests/ -k requirement_drift_no_prior_reports_unknown -q` — result:
  ```
  2 passed in 0.90s
  ```
- acceptance: `python3 -m pytest tests/test_requirement_drift_third_state_2980.py -v` (PR's own claimed full suite, untracked path above) — result:
  ```
  7 passed in 0.86s
  ```

Broader regression sweep (not claimed line-for-line, cross-checked
against the PR's pasted numbers) — acceptance: `python3 -m pytest test/
tests/ -q` inside the worktree — result:
```
20 failed, 690 passed, 3 xfailed in 31.66s
```
Re-ran the identical sweep against current `main` tip
(`7ee493e5`, separate worktree `/tmp/main-review-2980`) — acceptance:
same command — result:
```
20 failed, 694 passed, 3 xfailed in 31.91s
```
derived: `diff <(grep '^FAILED' main-run) <(grep '^FAILED' pr-run) | sort`
— empty diff, i.e. the 20 failing test names are byte-identical between
main tip and the PR head. The passed-count gap (694 vs. 690) is `main`
having advanced past this PR's branch point with unrelated commits
(issue-2982's `test_skill_candidates_floor.py` etc., confirmed via `git
diff --stat $(git merge-base main HEAD) main`), not a regression this PR
introduces.

derived: `python3 -m pytest test/ tests/ -q --collect-only` run in each
worktree:
```
main:    717 tests collected
PR head: 715 tests collected
```
715 - 7 (this PR's own new tests) = 708 shared tests; 717 - 708 = 9
tests that exist only on `main`'s post-branch-point commits, consistent
with the "main advanced past this PR's branch point" explanation above.

canonical: `git diff main...HEAD -- watchdog.py`, read in full this turn
inside the worktree — `must not` list audit against that diff, below.

## Why

Followed the adversarial-review protocol's core mechanism even though
this is a verification task rather than a fresh-artifact critique:
re-derived every claim from primary evidence in an isolated worktree
rather than trusting PR #3023's pasted test-plan output, per
`defect-verification-independence-from-upstream-verdicts` (skill invoked
this session) rule 3 (re-derive rather than cite against a stale sha)
and rule 2 (include edge/negative paths beyond the PR's own happy-path
tests).

The task specifically named two probes the PR's own test file doesn't
cover — a cached verdict stale by a long interval, and an intermittent
(not persistent) lookup failure — plus a check against issue #2978's
inverse defect (a discriminator that conflated two states and swallowed
a genuine report). All three are addressed under `## Open findings`.

## Upstream basis

PR #3023, branch `issue-2980/observability-signal-golden`
(fetched as `pr-3023-review`):
- `d0aca5a1` — the code fix (`watchdog.py`, new test file
  `tests/test_requirement_drift_third_state_2980.py`, untracked on this
  session's own branch)
- `9738f595` — before-landing warrant-hunter fix round, narrowing the new
  `if not all_items: return` guard to `if failed_numbers and not
  all_items: return`
- `e7172edf` — PR #3023's own session record
- `35f6e9ae` — PR #3023's own record correction (work-in-english
  skill-verdict wording)
- `00fe6e15` — PR #3023's own deviation log for the warrant-hunter fix

## Open findings

None. All three acceptance checks re-derived independently and pass
(transcripts above); the `must not` list is satisfied; the two
adversarially-chosen edge probes and the #2978-inverse check found no
swallowed report.

canonical: the diff read in `## What was done` above, plus four
self-constructed probes below (not fixtures from PR #3023's own test
file), all run this turn inside `/tmp/pr3023-review-1d3b7bc4`.

1. **Must-not #1 (failed lookup not resolved as pass or violation) —
   holds.** `watchdog.py:966-970` (full mode) and `watchdog.py:1030-1034`
   (delta mode, total-outage case) print under a distinct
   `requirement-drift-lookup-failed:` tag and, in the full-mode case,
   `return` before any verdict computation — reproduced via
   `TestLookupFailureState` (PR's own test, re-run above): no
   `requirement-drift: ` verdict line, no `인용되지 않는다` (positive-verdict
   wording), no `전혀 인용하지 않는` (violation wording) in the output.

2. **Must-not #2 (retention on a genuine prior must not stop) —
   holds, and the old silent-drop bug is fixed.** `watchdog.py:1006-1024`
   now tracks `fetched_numbers` (only numbers actually fetched *this*
   tick) separately from `changed_numbers`, so the cache-reuse pass
   (`for key, val in cache.items(): if key_num in fetched_numbers:
   continue`) still re-includes a changed-but-failed number that has a
   genuine prior cache entry into `all_items` — confirmed via PR's own
   `test_requirement_drift_cached_verdict_retention_not_dropped` (re-run
   above) and independently re-derived: with a two-tick construction
   (tick 1 caches `#2960` citing `R001`, tick 2's fetch for `#2960`
   fails), `R001` is not reported as unmentioned, i.e. the retained body
   still counts toward the verdict.

3. **Must-not #3 (lookup-failure report stays visible, not suppressed as
   noise) — holds.** The per-number `requirement-drift-cache-retained:`
   / `requirement-drift-unknown:` lines (`watchdog.py:1036-1049`) print
   unconditionally on `failed_numbers`, independent of the
   `_watchdog_note_gh_failure` consecutive-failure counter that gates
   only the connectivity-outage `lookup-failed` advisory line. Probed
   this directly with a self-constructed **intermittent-failure**
   sequence (fail, succeed, fail again, same number, three separate
   ticks) — `spawn.requirement_drift` invoked three times with
   `_fetch_issue_or_pr_via_cache` returning `None`, an item, then `None`:
   tick 1 prints `requirement-drift-unknown:` (no prior yet), tick 3
   prints `requirement-drift-cache-retained: ... 2960` (prior from tick
   2) — neither failing tick goes silent despite never reaching the
   N-tick consecutive-failure threshold that gates the full-outage
   message. Also probed a **stale-by-a-long-interval** cached verdict
   (a cache entry dated `2020-01-01T00:00:00+00:00` retained on today's
   failed refetch): the retained line printed that real, year-old
   timestamp verbatim (`관측: 2020-01-01T00:00:00+00:00`), not a
   fabricated fresh one. A third self-constructed probe covered a case
   the PR's schema change itself creates a gap for — a **legacy cache
   entry with no `cached_at` key at all** (written before this PR's
   change to start recording it): `cache.get(str(n), {}).get
   ("cached_at", "unknown")` falls back to the honest `관측: unknown`
   marker rather than crashing or fabricating a timestamp — confirmed
   this does not regress must-not #2 either (the entry is still
   retained, just with an honest "unknown" observation time).

4. **#2978-inverse check (a new discriminator swallowing what used to
   surface) — no equivalent found.** Issue #2978's defect was a single
   boolean (`_slug is None`) collapsing two structurally distinct
   conditions into one, silently dropping a genuine report for the
   collapsed-but-different case. This PR's delta-mode guard
   (`watchdog.py:1050-1051`, `if failed_numbers and not all_items:
   return`) is the one place in this diff with the same shape of risk —
   and it is the guard PR #3023's own before-landing warrant-hunter
   already found and narrowed (an earlier, unconditional `if not
   all_items: return` swallowed a genuine zero-failure violation). Re-ran
   the regression test guarding that fix (`TestNoFailureStillComputesVerdict`,
   in the acceptance transcripts above) and independently re-derived it
   is now gated on `failed_numbers` too, so a real zero-failure
   empty-items tick (the only cached number confirmed closed on refetch)
   still computes and prints its verdict instead of returning early. No
   other conditional in this diff merges two states the acceptance
   criteria require to stay distinct.

## Next steps

None — no further routing is needed given the acceptance and probe
results captured in `## What was done` and `## Open findings` above
(all executed this turn: three acceptance checks, the PR's own 7-test
suite, the regression sweep on both the PR head and `main` tip, and the
four independently-constructed edge probes).

skill-verdict: adversarial-review — applied: invoked; used its
blind-evaluator discipline (evidence-located findings, no trusting the
builder's self-report) to structure the diff audit and the must-not-list
check above, adapted to a verification target rather than a fresh
artifact
skill-verdict: defect-verification-independence-from-upstream-verdicts —
applied: invoked; re-derived all three acceptance checks and the
regression sweep from a freshly fetched worktree rather than citing PR
#3023's pasted results, and constructed four additional edge cases
(stale-interval retention, intermittent failure, legacy cache without
`cached_at`, and the #2978-inverse discriminator check) beyond the PR's
own test fixtures per rule 2
skill-verdict: verify-finding-record — not-applicable: this session's
assigned record area is
docs/issue-2980/reports/adversarial-review-70dec1c4.md, not
docs/issue-2980/reports/defect-verification.md, which this skill writes
to exclusively
skill-verdict: conformance-review-finding-record — not-applicable: this
task is an adversarial re-verification of a PR's own claimed acceptance
results, not a conformance-review requirement check writing to
docs/issue-<n>/reports/conformance-review.md
skill-verdict: technical-feasibility-verdict-and-timebox-selection —
not-applicable: no feasibility spike or timebox was in play here; this
task set a bare defect-verification outcome, not a feasibility go
decision
skill-verdict: test-depth-audit — not-applicable: the task was
re-deriving whether the PR's fix and its own tests hold up under
independent adversarial probing, not classifying the depth/genuineness
of an existing test suite as its own deliverable
other mounted skills: not triggered (work-in-english guidance was
followed — this record, all commands, and all commit messages are in
English — but attaches as a core-hook-enforced guidance for this task's
configuration, not a Skill-tool call, so it gets no skill-verdict line)

## What did not work

None.
