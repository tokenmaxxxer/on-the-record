---
status: proposed
files:
  - docs/issue-1097/reports/execution-observation.md
---

## Request
Issue #1097 asks the execution-observation role to judge whether the implementation role's phase-1→phase-2 execution on issue #1097 was sound, by reading the actual landed artifacts — never by re-executing the observed task. Trigger: spawn_on_pr.py auto-spawned this session because commits landed on `issue-1097/implementation` (PRs #1103, #1104) with no execution-observation record yet.

## Constraints
- Never edit `gates/`, `spawn.py`, `tests/`, or `docs/issue-1097/reports/implementation*` — this role's own record is the only writable surface.
- Never re-run `spawn.py consult` against a real model session as a re-execution of the observed task; the survey's live `python3 gates/test_consult_verdict_parsing.py` run and its isolated mock repro are admissible because they exercise the shipped artifact's own regression test and internal call shape, not a re-performance of the implementation role's judgment work.
- Record all three verdict levels even when one does not apply, per the spec's per-claim vocabulary.

## Rationale
All three verdict levels named up front, and the evidence class each will draw on — no verdict is rendered here, only the plan:

- **outcome** — did the delivered fix satisfy issue #1097's acceptance criterion (a test in `tests/`/`gates/` asserting the judgment-JSON parse path against a captured real transcript, plus a live `spawn.py consult` smoke run), recomputed as the worst case among the record's own cited step-level results. The survey (`docs/issue-1097/reports/execution-observation/survey.md`, item 5) found that `gates/test_consult_verdict_parsing.py` — the exact test PR #1103/#1104 attach as the acceptance test — fails deterministically when run live against current `main` today, though for a reason traced to later, unrelated drift (`_commit_consult_trace()`, issue #1134) rather than a defect in PR #1103/#1104's own diff hunks. Whether that later-drift-caused failure should still weigh down the outcome verdict (since the acceptance test as currently landed on `main` no longer passes, regardless of blame) or should be scoped out as "not this PR's own defect" is exactly what the outcome verdict will resolve, citing the survey's isolated repro.
- **trajectory** — three named pass/fail/not-applicable checks: scouted-when-required (implementation role's own `docs/issue-1097/reports/implementation/survey.md`, whether it recorded a scout pass or a skip reason for this bugfix-shaped task), surveyed-before-proposing (that same survey file precedes proposal-shaped language within PR #1103's single commit `a19456bf`), approved-by-human (the exact `APPROVE issue-1097/implementation` issue comment from approvers.md account `JiwonJung94`, single-account mode since the PR author is the same account, per survey item 4).
- **step** — any specific artifact found deficient, each with subject/test/result/assertedBy in the spec's per-claim vocabulary, drawn only from diff hunks the survey already logged as touched by PRs #1103/#1104 (the diff-scope rule) or from a live command this session ran directly against the shipped code. The leading candidate is `gates/test_consult_verdict_parsing.py`'s `t_retries_once_and_recovers_when_first_attempt_has_no_json` test, mode `command` (this session ran it directly, twice, both times deterministic) — supports a `failed` result for "does this test currently pass against `main`" even though the root cause traces outside PR #1103/#1104's own hunks.

## Accumulation
Not accumulation-cost-shaped — one observation record for one already-closed issue's two already-merged PRs, not a per-item or repeated-cost pattern.

## What will be done
Write `docs/issue-1097/reports/execution-observation.md` per the spec's required fields (`code_under_review:` as a file list, `loop_state:`, etc.), citing PRs #1103/#1104's diffs/commits, the implementation role's own record (`docs/issue-1097/reports/implementation.md`), the issue-level APPROVE trail, and this session's own live `gates/test_consult_verdict_parsing.py` run and isolated repro, then commit and push it in the same PR that carries this proposal, once phase-2 opens.

## Out of scope
Any change to the observed artifact itself (`docs/issue-1097/reports/implementation*`, `spawn.py`, `gates/`, `tests/`), and any new issue filing (issues are user-authored only under contract v3) — including for the `_commit_consult_trace()`-caused test failure the survey found, which stays as a step-level finding in this role's own record for the human to act on.

## How you'll know it worked
`docs/issue-1097/reports/execution-observation.md` exists on the branch with `loop_state: handed-off`, all three verdict levels present (outcome/trajectory/step, each addressed even if not applicable), and every verdict sentence citing a commit SHA, file:line, or PR comment URL, with evidence mode stated inline for any asserted-mode claim.
