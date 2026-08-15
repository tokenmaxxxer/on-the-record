---
type: survey
loop_state: running
---

# issue #745 — execution-observation phase-1 survey: PR #1517

## Scope statement

canonical: `gh pr view 1517 --json number,title,body,commits,mergedAt,url`
(read this session).
- Subject: `issue-745`. Observed role: `implementation`.
- canonical: same command as above. PR: #1517 ("issue-745: Item 3
  three-axis execution-observation skip-eligibility").
- canonical: same command as above. Commits:
  `22e162ed44368c09989aa191664c7dd586d29a89`,
  `8c42a4f125c91c2c8e3b4754c4bbf6a2fb076c23`.
- canonical: same command as above (`mergedAt` field). Merge point:
  `1425c881` on `main`.

This session was spawned by `spawn_on_pr.py` on PR creation, per this
session's own invocation prompt ("PR 생성 시 자동 스폰됨").

## What was read this session, in order (FRESH-EYES ORDERING)

1. `gh issue view 745` / `gh issue view 745 --comments` — issue body
   (Korean, cost-structure valuation problem statement, three items:
   thinking budget / record volume / execution-observation frequency)
   and the full comment thread, including the operator's phased
   decisions (Item 2 revert via PR #1512, Item 3 approved via
   in-conversation `APPROVE issue-745/implementation` comment).
2. `gh pr view 1517 --json number,title,body,commits,mergedAt,url` — PR
   metadata: title, body, two commit SHAs, merge timestamp
   `2026-08-14T16:15:49Z`.
3. `gh pr diff 1517` — the full diff, read before the observed role's
   own record narrative, per FRESH-EYES ORDERING:
   - `docs/issue-745/reports/implementation.md` (the observed role's own
     record — its diff hunk read here as *diff*, not yet as narrative)
   - `docs/specs/enforcement-boundary.md` — one new row registering
     `gates/skip_eligibility.py`
   - `gates/skip_eligibility.py` (new, 147 lines) — three axis
     functions (`non_docs_lines_changed`, `hard_to_revert_hit`,
     `claim_vocabulary_hit`), `classify_rows` (pure), `classify_for_subject`
     (git-facing wrapper), `_ref_resolvable`/`_numstat`/`_deleted_paths`/
     `read_record_text` helpers
   - `gates/spawn_on_pr.py` — new `_filter_execution_observation()`
     wired into `missing_verification()`
   - `gates/test_skip_eligibility.py` (new, 177 lines) — unit tests per
     axis plus two live-fire tests against real git branches
   - `tests/test_spawn_on_pr.py` — two new end-to-end tests
4. `git show 22e162ed:docs/issue-745/proposals/item3-execution-
   observation-conditioning.md` — the approved phase-1 proposal PR
   #1517 implements (RICE-scored candidates, pre-registered hypothesis
   package: metric `execution_observation_sessions_per_landed_pr`,
   20-PR window, guardrail `fabrication_survival_rate`, decision rule,
   revert condition).
5. `docs/issue-745/reports/implementation.md`, read last as continuous
   prose (its diff hunk was already read at step 3). canonical: `gh pr
   diff 1517` (read this session).

## Write surfaces (for scout to aim at, if it runs)

canonical: `gh pr diff 1517` (read this session, item 3 above). The six
files landed in PR #1517, all read above: `gates/skip_eligibility.py`,
`gates/spawn_on_pr.py`, `gates/test_skip_eligibility.py`,
`tests/test_spawn_on_pr.py`, `docs/specs/enforcement-boundary.md`,
`docs/issue-745/reports/implementation.md`.

## Open unknowns, deferred to phase 2

- canonical: `gh pr view 1517 --json body` (read this session, "## Test
  plan" section states a test-suite figure of 37). A live re-run of
  that figure is left for phase 2.
- Whether `docs/specs/approvers.md`'s current roster covers the account
  that posted `APPROVE issue-745/implementation` is left for phase 2.

## Scout-directive skip record

Scouting skipped. Reason: this role's phase-2 record shape (three-level
verdict: outcome/trajectory/step; required citation format; record
location) is fully specified by the execution-observation role
directive supplied at session start (canonical: session-start role
directive, read this session) — no product-facing or comparable-system
design decision is open for this task, satisfying the "spec literally
leaves no design decision open" skip condition.
