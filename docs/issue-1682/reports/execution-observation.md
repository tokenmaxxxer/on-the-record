---
code_under_review:
  - gates/gh_delta.py
  - gates/gh_cache.py
  - gates/test_gh_delta.py
  - gates/test_gh_cache.py
  - docs/issue-1682/reports/implementation.md
  - docs/issue-1682/reports/implementation/2026-08-16-hunt-change-cursor-shared-cache.md
type: observation
loop_state: handed-off
---

# issue-1682 execution-observation

## Summary of work

This session independently read the phase-1 and phase-2 PRs for issue #1682 (canonical: `gh pr diff 1687` and `gh pr view 1687 --json commits,files,body,reviews`, read this session; canonical: `gh pr list --state all --search "1682" --json ...`, read this session, for PR #1683's merge state), along with the observed role's own record embedded in PR #1687's diff, and produced this three-level verdict record: outcome recomputed against the issue's own four Acceptance checks (two satisfied, one satisfied under an approved amendment, one — the live 10-minute quiet-window measurement — not yet executed by anyone), trajectory (all three named checks hold), and one open step-level finding disclosing the unexecuted live check with no confirmed successor issue.

## Why

canonical: `gh issue view 1682 --comments` output read this session — the session was auto-spawned on PR creation per this branch's issue thread (the last comment in the thread, "[watch] issue-1682/implementation: session-end: PR ... #1687 opened," names the observed PR this record judges).

## Upstream basis

canonical: docs/issue-1682/proposals/change-cursor-shared-cache.md, read directly in this working tree this session (PR #1683, merged). canonical: `gh pr view 1687 --json commits`, read this session (issue-1682/implementation, commits f21d5209 and 8db254f7).

## Independence statement

This session did not author or edit gates/gh_delta.py, gates/gh_cache.py, their tests, or the observed role's own record — those files live only on the issue-1682/implementation branch, not this branch's working tree. canonical: `gh pr diff 1687` (full diff, read this session) and `gh pr view 1687 --json commits,files,body,reviews` (read this session) are the sources for the observed artifact; no code in gh_delta.py/gh_cache.py was re-run this session.

## Scope statement

Subject: issue #1682. Observed role: implementation, session issue-1682-implementation. Observed artifacts: PR #1683 (phase-1 proposal) and PR #1687 (phase-2 delivery, head commits f21d5209 and 8db254f7). canonical: `gh pr list --state all --search "1682" --json number,title,headRefName,baseRefName,state,mergedAt,url` (read this session), which returned PR #1683 with `"mergedAt":"2026-08-16T13:07:39Z"` and PR #1687 with `"state":"OPEN"`.

Read this session, in this order: `gh issue view 1682` (body + acceptance criteria) and `gh issue view 1682 --comments` (full comment thread), then `gh pr diff 1687` (all 843 lines) and `gh pr view 1687 --json commits,files,body,reviews`, before reading the observed role's own record narrative embedded in that same diff (docs/issue-1682/reports/implementation.md, part of PR #1687's diff). Diff hunks cited below: gh_delta.py (diff lines 328-539), gh_cache.py (190-322), test_gh_delta.py (628-844), test_gh_cache.py (540-628) — PR #1687's diff is one contiguous set of ADDED-file hunks (all six files are new), so every citation below falls inside a hunk the PR actually touched.

## Verdict scope

All three verdict levels are addressed below: outcome (recomputed from step-level results, worst case governs), trajectory (three named checks), and step (per-artifact findings). No verdict language precedes this line.

## Outcome

canonical: `gh issue view 1682` body, Acceptance section (read this session) — names four checks: two `unit`, one `live`, one `empty state`.

- Check 1 (unit, change-cursor helper): satisfied by the artifact. canonical: PR #1687 diff, test_gh_delta.py::test_delta_returns_items_since_cursor_and_persists_advanced_cursor (diff lines 656-682), ::test_no_change_tick_makes_exactly_one_probe_and_zero_detail_fetches (685-706, asserts `len(calls) == 1`), ::test_corrupted_cursor_file_classifies_full_rescan (708-720). mode: read (file evidence; no test run executed this session).
- Check 2 (unit, shared cache): satisfied by the artifact, under an amended wording (see Trajectory / approved-by-human). canonical: PR #1687 diff, test_gh_cache.py::test_two_consumers_second_gets_304_revalidation_from_disk (diff lines 558-582), asserting `len(calls) == 2` (one unconditional fetch + one 304 revalidation) with the second consumer's body served from disk, not the empty 304 response. mode: read.
- Check 3 (live, 10-minute quiet-window measurement): not present on this branch or on main. canonical: PR #1687 diff, docs/issue-1682/reports/implementation.md "## Next steps" (diff lines 116-121), stating the watchdog wiring and the live measurement are deferred to "a sequenced follow-up issue." mode: read. That deferral was itself proposed in advance, not improvised: canonical: docs/issue-1682/proposals/change-cursor-shared-cache.md "## Out of scope" (read directly in this working tree this session), same wording, and PR #1683 carrying that proposal shows `"mergedAt":"2026-08-16T13:07:39Z"` in the `gh pr list` output cited in the Scope statement above — a human merge decision under this role's own merge-is-acceptance rule. Whether a successor issue for the sweep-wiring step exists is untracked by this session — this session's read was limited to issue #1682's own comment thread (canonical: `gh issue view 1682 --comments`, read this session, no successor-issue number appears in it) and did not search the wider issue tracker.
- Check 4 (empty state): satisfied by the artifact. canonical: PR #1687 diff, test_gh_cache.py::test_cold_cache_behaves_like_unconditional_fetch (diff lines 585-599). mode: read.

Recomputed outcome, worst case across the four cited step-level results: mixed / cantTell. The two `unit` checks and the `empty state` check are satisfied by artifacts read this session; the `live` check, which the issue's own Acceptance list requires (`provenance: executed-live`), has not been executed by anyone as of this session.

## Trajectory

- scouted-when-required: holds. canonical: docs/issue-1682/proposals/change-cursor-shared-cache.md "## Rationale" (read directly in this working tree this session), documenting two considered-and-rejected alternatives (extending closure_sweep.py's `_conditional_issue_list` in place vs. new sibling modules; webhook-push vs. ETag-polled cursor), grounded in file:line citations to spawn.py:1284-1420 and gates/closure_sweep.py:73-132 that appear in docs/issue-1682/reports/implementation/survey.md "## Existing ETag precedent" (also read directly in this working tree this session).
- surveyed-before-proposing: holds. canonical: docs/issue-1682/reports/implementation/survey.md (read this session), which states a scout-skip rationale and enumerates the planned write set and a precedent read (gates/gh_rest.py:1-93) ahead of the proposal file's own design section restating the same write set as a build commitment; both files landed in one commit per `gh pr view 1683 --json commits` (read this session, commit `68db7d8c`), so within-session ordering by timestamp is not independently reconstructible from git history — this check is graded on content structure (survey's findings precede and inform the proposal's design section), stated here as the caveat this role's own evidence-mode discipline requires.
- approved-by-human: holds. canonical: `gh issue view 1682 --comments` (read this session) — a comment authored by JiwonJung94 (association: member, and listed in docs/specs/approvers.md, read this session) with body exactly "APPROVE issue-1682/implementation", posted after the same author's prior comment carrying the "ACCEPTANCE AMENDMENT" and five "BINDING PHASE-2 CONDITIONS," and before PR #1687 was opened per the thread's chronological order.

Trajectory verdict: all three named checks hold, per the citations above.

## Step-level findings

1. subject: docs/issue-1682/reports/implementation.md "## Next steps" (PR #1687 diff lines 116-121). test: does the acceptance-check-3 (live quiet-window measurement) gap have a tracked successor. result: cantTell. assertedBy: this role, citing itself. mode: read. Impact: the issue's own Acceptance list still carries an unexecuted `provenance: executed-live` check — a reader who treats PR #1687 alone as landing issue #1682 would be missing that gap. Timeline: descoped in the phase-1 proposal (PR #1683) and reaffirmed in the phase-2 record (PR #1687, commit 8db254f7). Root cause: the phase-1 proposal correctly identified that a module-+-tests-only PR cannot itself execute a live watchdog measurement and split the work, but no successor-issue number appears in issue #1682's own comment thread as read this session — canonical: `gh issue view 1682 --comments`, read this session, last comment is a `[watch]` session-end note naming PR #1687 with no new issue number attached. Action item: a follow-up issue for wiring gh_delta/gh_cache into closure_sweep.py/watchdog ticks and running the live measurement needs to exist and be tracked before issue #1682 is treated as landed; this role does not file it (issues are user-authored only under contract v3), so this finding is the disclosure mechanism.
2. subject: gh_cache.py / gh_delta.py `_atomic_write_json` (PR #1687 diff lines 252-268, 391-405). test: does a cache/cursor persistence-write failure fail open instead of crashing the caller. result: satisfied by the artifact. assertedBy: this role, citing the PR's own hunt record docs/issue-1682/reports/implementation/2026-08-16-hunt-change-cursor-shared-cache.md (diff lines 126-185, part of PR #1687's diff) plus the fix read directly in the diff — both `_atomic_write_json` implementations wrap `mkdir`/`mkstemp` in their own `try/except OSError: return` (gh_cache.py lines 254-258, gh_delta.py lines 392-396), closing the gap the hunt record's own reproduction (`chmod 0o500` on the cache dir causing an uncaught PermissionError) had identified. mode: read. This item was found and its fix landed by the observed role itself, within the same PR, before this session's read — listed here for completeness, not as an open item.

## Open findings

Item 1 (live acceptance check 3, unexecuted, tracked successor unverified) is the only open item this session raises. Item 2 has a fix already in the diff, per the citations above.

## Next steps

Human review of open item 1: verify whether a sweep-wiring follow-up issue already exists (this session's search covered only issue #1682's own comment thread) and, if not, file one — this role does not.

## Resolution path

Open item 1 resolves once a follow-up issue implementing the closure_sweep.py/watchdog wiring exists and its own live 10-minute quiet-window measurement (before/after `rate_limit` remaining delta) has been executed and recorded, satisfying issue #1682's acceptance check 3.
