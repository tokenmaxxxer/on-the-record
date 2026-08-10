# defect-verification survey — issue #653 / PR #665

## Subject

PR #665, `implementation: broker-attach Closes trailer at merge (#653)`,
branch `issue-653/implementation`, code_under_review:
`d1d1002` (tip of PR #665 at survey time).

## Records read

- Coding's record on PR #665's branch (report at reports/implementation.md
  under issue-653, on issue-653/implementation — not present on this
  defect-verification branch since that PR has not merged) — claims
  `on-the-record/hooks/contract-guard.sh`'s phase-2 merge check no longer
  denies outright on a missing/wrong `Closes #<issue>` trailer; it now
  builds a corrected PR body and calls `gh pr edit` before allowing the
  merge, and `deny(...)` fires only when that `gh pr edit` write itself
  fails. Reports its own pytest run passing in full, including a new
  `test_write_failure_still_denies_merge` red case and multiple
  auto-attach green cases (derived: `gh pr diff 665` tail —
  `` ============================== 12 passed in 0.97s ============================== ``).
- No `qa` or `review` record exists under `docs/issue-653/` on main or on
  PR #665 — this issue's pipeline ran architecture -> implementation
  directly. No `closed_checks` entries to cite; every attempt below is
  self-devised from coding's record and the PR body's own two claims.
- Architecture's approved ADR (`docs/issue-653/proposals/2026-08-10-closes-trailer-preflight-hardening.md`,
  `issue-653/architecture` branch) — states the same two-behavior shape:
  auto-attach on merge, deny only on write failure.

## Current-state check already done (informs attempt framing)

Read `on-the-record/hooks/contract-guard.sh` in full at PR #665's tip
(`d1d1002`, via `git worktree add` from `refs/pull/665/head`). The
relevant branch (previously an unconditional `deny(...)` on
`not closes_m or int(closes_m.group(2)) != issue`) now: builds a
corrected body (append `Closes #<issue>` if absent; would fix a wrong
`#<m>` digit in place if that sub-branch were reachable — coding's record
already flags this specific sub-branch as dead code, since `issue` is
itself derived from `closes_m` whenever `closes_m` matches, so the
wrong-number half of the condition can never be true), calls
`gh pr edit <pr> --body <corrected> [-R <repo>]`, and `deny()`s only if
that call's exit code is non-zero; otherwise falls through to
`sys.exit(0)`.

## Attempt list (phase-1 promise)

| # | Source (verbatim) | Attempt |
|---|---|---|
| 1 | PR #665 body / coding's record, "What changed": "the hook now attaches/corrects it via \`gh pr edit\` before allowing the merge" | Self-devised: independently invoke `contract-guard.sh` (not the PR's own pytest harness — a hand-built fake `gh` shim plus fixture repo, run directly by this role) against a phase-2-approved PR whose body has no `Closes` trailer at all, with the fake `gh pr edit` succeeding. Expect: exit 0, and the `gh pr edit` call's `--body` argument contains `Closes #<issue>`. |
| 2 | PR #665 body / coding's record, "What changed": "\`deny(...)\` remains only as the fallback when that write itself fails" | Self-devised: same setup as #1, but the fake `gh pr edit` exits non-zero. Expect: exit 2, stderr names the issue and mentions the failed `gh pr edit` attempt — i.e. auto-attach must never silently wave the merge through on a write failure. |

closed_checks cited: none (no review record exists for this issue to cite
from). Both attempts re-derive from coding's record and the code itself,
using an independently hand-built harness (not the PR's own
`test_contract_guard.py` fixtures) to avoid re-litigating the author's own
test verdict as if it were the attempt.

## Basis

Upstream: PR #665's coding record (reports/implementation.md under
issue-653, on branch issue-653/implementation), sha `d1d1002`.
