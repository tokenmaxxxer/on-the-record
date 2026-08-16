---
code_under_review:
  - spawn.py
  - tests/test_spawn.py
  - gates/recovery_policy.py
  - gates/test_boundary.py
  - .gitignore
type: review
loop_state: complete
---

# Conformance review — issue #1678

## What was done

Reviewed issue-1678/implementation as of commit 0aa1ac20 ("fix(issue-1678):
count distinct deaths not watchdog ticks, reset on healthy state" — a
follow-up to 97d556c9, addressing PR #1680 review comments D1/D2) against
issue #1678's three acceptance checks. Per-requirement verdicts below.
canonical: git log origin/issue-1678/implementation --oneline -3 (this session).

### Requirement 1 — unit/integration test

Test class ReconcilePrExpectedMissingRecoveryPolicy covers pre-first-commit-under-cap, has-commit-no-PR, and at-cap/repeat-signature ESCALATE via mock.patch.object(spawn, "_recovery_policy_module", ...), plus two later tests (D1/D2 fix-up) for same-death-multiple-ticks and reset-on-healthy.
canonical: tests/test_spawn.py:4863-5033 (0aa1ac20, read this session).

```
$ python3 -m pytest tests/test_spawn.py -k "Reconcile" -q
35 passed in 2.92s
```
canonical: acceptance: python3 -m pytest tests/test_spawn.py -k Reconcile -q — result: PASS (executed this session).

**Verdict: Present.**

### Requirement 2 — live #1660 reconstruction

test_live_reconstruct_issue_1660_cap_then_escalate drives the real, unmocked recovery_policy.classify_from_state through an isolated tmp state dir across three calls with the same failure signature: first respawns with handoff=True, second and third both move to manual-review.
canonical: tests/test_spawn.py:4936-4967 (0aa1ac20, read this session).

```
$ python3 -m pytest tests/test_spawn.py -k ReconcilePrExpectedMissingRecoveryPolicy -q
8 passed in 1.51s
```
canonical: acceptance: python3 -m pytest tests/test_spawn.py -k ReconcilePrExpectedMissingRecoveryPolicy -q — result: PASS (executed this session; includes test_live_reconstruct_issue_1660_cap_then_escalate).

Scope note: this exercises the real state-I/O path but is a synthetic pytest reconstruction, not an external live invocation against an actual dead orchestrator session.
canonical: git show 0aa1ac20:docs/issue-1678/proposals/2026-08-16-wire-recovery-policy-into-reconcile.md (this session, "Out of scope" section: a real failure_signature extractor is out of scope for this change).

**Verdict: Present, with the scope note above (not a gap).**

### Requirement 3 — empty state

test_healthy_with_pr_triggers_no_action still asserts reconcile() returns [] and classify_from_state is never called when pr_number is set.
canonical: tests/test_spawn.py:4912-4924 (0aa1ac20, read this session).

The 0aa1ac20 fix-up added a reset_state() side effect on the healthy path (an (issue, role) observed with a PR or a normal-verdict session now clears its recovery-state file, so a later real death starts its cap count at 0 rather than inheriting stale flake history).
canonical: spawn.py:2085-2094 (0aa1ac20, read this session, the new reset block in reconcile()).

test_healthy_after_flakes_resets_state_next_death_starts_fresh covers this reset directly.
canonical: tests/test_spawn.py:5001-5033 (0aa1ac20, read this session).

This does not change what a healthy reconcile() call returns to its caller (still []); the acceptance text's "byte-identical to today" is read as the recommendation output, not internal bookkeeping — issue #1678 does not name this bookkeeping detail one way or the other. Not treated as a violation.

```
$ python3 -m pytest tests/test_spawn.py -k ReconcilePrExpectedMissingRecoveryPolicy -q
8 passed in 1.51s
```
canonical: acceptance: python3 -m pytest tests/test_spawn.py -k ReconcilePrExpectedMissingRecoveryPolicy -q — result: PASS (executed this session; includes test_healthy_with_pr_triggers_no_action and test_healthy_after_flakes_resets_state_next_death_starts_fresh).

**Verdict: Present.**

## Supporting checks

_reconcile_pr_expected_missing() maps ESCALATE to next_action="manual-review", the pre-existing closed-set member for surfacing without an automated verb.
canonical: spawn.py:543-548 (0aa1ac20, read this session).

gates/test_boundary.py's issue-492 manifest markers were updated to match reconcile()'s widened signature.
canonical: git show 0aa1ac20:gates/test_boundary.py (this session).

```
$ python3 -m pytest gates/test_boundary.py -q -k "492 or reconcile"
1 passed in 0.81s
```
canonical: acceptance: python3 -m pytest gates/test_boundary.py -q -k "492 or reconcile" — result: PASS (executed this session).

## Why

Issue #1678 (northpole req#6) asks whether the shipped commits actually wire recovery_policy.classify_from_state() into reconcile()'s pr-expected-missing branch, replacing an unconditional respawn with a bounded, failure-classified verdict — this record checks that claim against the diff and re-executed tests rather than trusting the implementation record's own narration, and covers the D1/D2 fix-up commit that landed after the initial implementation commit.
canonical: gh issue view 1678 (issue body, read this session).

## Upstream

Basis: issue-1678/implementation at commit 0aa1ac20, brought into this branch's tree via a local merge so the reviewed code is locally re-executable.
canonical: git log origin/issue-1678/implementation --oneline -3 (run this session).

## Open findings

None open.
canonical: acceptance: python3 -m pytest tests/test_spawn.py -k Reconcile -q — result: PASS (above).

Resolution path: n/a — no open findings.
