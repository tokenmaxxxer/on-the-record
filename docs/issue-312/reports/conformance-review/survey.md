# Survey — issue-312 conformance review

Subject: issue-312

## Upstream / basis

canonical: `gh issue view 312` (issue body + comments), `gh pr view 314
--json title,body,mergeCommit,files`. Issue #312, closed via PR #314.
Proposal: `docs/issue-312/proposals/2026-08-07-closes-gate-issue-level-phase-and-evidence-bearing-refusal.md`.
Decision: `docs/issue-312/decisions/phase-is-an-issue-property.md`.
Delivered implementation: PR #314, commit
`3e3038690098a9efb686c47b6fb9cfb37de2ccb8`, `gates/ci.py`,
`gates/test_closes_gate_ci.py`, `docs/issue-312/reports/implementation.md`.

## What was surveyed

Read `gates/ci.py`'s `_approved_roles_on_issue` (gates/ci.py:181),
`_phase_from_approval` (gates/ci.py:205), `_phase1_surface_mismatch`
(gates/ci.py:327), and the `check()` orchestration (gates/ci.py:428)
that assembles the evidence-bearing refusal. Read
`t_autodetect_cross_role_handoff_304_307_shape_is_phase2_no_mismatch`
and
`t_autodetect_missing_approval_refusal_names_role_searched_and_approvals_present`
in `gates/test_closes_gate_ci.py` for the two acceptance-mapped tests.
Ran the full gate test suite:

```
$ python3 gates/test_closes_gate_ci.py
54 passed
```

Attempted the issue's third acceptance bullet — re-running
`python3 gates/ci.py . --pr 307 --issue 304 --autodetect --closes-only`
against real GitHub state:

```
$ python3 gates/ci.py . --pr 307 --issue 304 --autodetect --closes-only
게이트 차단:
  - PR #307 커밋 목록을 읽을 수 없다(`gh api` 실패) — 검사 불가는 통과가 아니다.
$ gh api repos/tokenmaxxxer/on-the-record/pulls/307/commits
{"message":"API rate limit exceeded for user ID 87398933." ...}
```

unverifiable: the live GitHub re-run of PR #307 could not be reproduced
in this session — `gh api` returned HTTP 403 (rate limit exceeded) for
this session's authenticated user, not a gate-code failure. The claim in
PR #314's body ("Live-checked ... → 게이트 통과") was made in the
implementation session; canonical: `gh pr view 314 --json body` for that
prior claim's text — this survey did not reproduce it live.

## Requirement extraction

canonical: issue #312 body `## Scope`/`## Acceptance` sections (`gh
issue view 312`). Extracted requirement list with sources and checks:
`docs/issue-312/proposals/conformance-review.md`.

## What did not work

None.
