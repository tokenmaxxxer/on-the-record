---
code_under_review:
  - on-the-record/hooks/approval-gate.sh
  - on-the-record/hooks/test_approval_gate.py
  - test/test_approval_gate_carriers.py
  - test/test_branch_role_field.py
loop_state: landed
type: bugfix
breaking: false
verdict: pass
---

## Summary of work

Added a build-now bypass to `on-the-record/hooks/approval-gate.sh` (issue #608
step 2's gate). When `CORE_BUILD_NOW=1` is present in the gate process's env
at the point a phase-2-shaped write (record file or src/test path) is
checked, the gate now exits 0 (allow) immediately after the phase-2-shaped
target check and before the `approvers.md`-presence check, writing a stderr
log line naming the bypass, the issue, the role, and the write path. Without
the env var (unset, empty, or any value other than the literal string `"1"`),
execution falls straight through to the pre-existing approvers.md/APPROVE-
comment logic, unchanged.

Also fixed two other test helpers (`test/test_approval_gate_carriers.py`'s
`_run_gate` and `test/test_branch_role_field.py`'s `_run_approval_gate`) to
strip `CORE_BUILD_NOW` from the subprocess env before invoking
`approval-gate.sh` — these helpers build `env = dict(os.environ)` and did not
previously pop this var, so a session that happens to carry
`CORE_BUILD_NOW=1` itself (as this one does, under the build-now bypass) was
leaking that value into their fixture runs and flipping asserted-deny cases
to allow. This is the same env-hygiene fix the new gate tests themselves
needed (`on-the-record/hooks/test_approval_gate.py`'s `_run`/`_run_with_session`).

## Why

Issue #2007: a spawned single-phase (`CORE_BUILD_NOW=1`) session hit
approval-gate.sh mid-delivery and was denied because no APPROVE comment had
been posted — the gate had no way to recognize the operator-level bypass
authorization the spawner's own env var represents, so every earlier
single-phase success only worked because an orchestrator had pre-posted the
token by hand. The fix makes the env var itself satisfy the phase-2
precondition, since setting it is already operator-authorized at spawn time
(contract v3 s19a) and a session cannot grant itself the bypass by exporting
the var on its own (the var only has effect because it arrives in the
spawned env, not because a running session could set it after the fact).

## Upstream / basis

on-the-record/hooks/approval-gate.sh (issue #608 step 2, #698, #707, #1814,
#1821 dual-read layering) — this change adds one more early-exit branch
inside the same PY heredoc, after the phase-2-shaped-target check and before
the approvers.md-presence check.

## What did not work

None of substance — the early-exit branch needed no rework; the only
follow-up was env-hygiene in three test helper functions that were leaking
the ambient session's own `CORE_BUILD_NOW=1` into fixture runs (this session
runs under the same bypass it's implementing).

## Testing

canonical: python3 -m pytest on-the-record/hooks/test_approval_gate.py -q
acceptance: python3 -m pytest on-the-record/hooks/test_approval_gate.py -q — result: 32 passed
(29 pre-existing + 3 new: `test_build_now_bypasses_without_approve_and_logs`
parametrized over record/src/test paths, `test_build_now_bypasses_even_with_approvers_absent`,
`test_build_now_unset_or_non_one_behaves_as_today` parametrized over
`"0"`/`"false"`/`""`/`"yes"`), asserting live: with `CORE_BUILD_NOW=1` an
implementation write proceeds (rc=0) without an APPROVE comment and the
stderr log names the bypass; without it (or with any non-`"1"` value)
returncode and stderr are byte-identical to the pre-existing baseline run.

canonical: python3 -m pytest test/test_approval_gate_carriers.py test/test_branch_role_field.py -q
acceptance: python3 -m pytest test/test_approval_gate_carriers.py test/test_branch_role_field.py -q — result: 30 passed
(regression check on the two other test files whose helper functions also
invoke approval-gate.sh; they needed the same `CORE_BUILD_NOW` env-hygiene
fix noted above).

canonical: python3 -m pytest -q -m "not slow"
acceptance: python3 -m pytest -q -m "not slow" — result: 2479 passed, 19 xfailed, 2 xpassed, 0 failed
(fast tier per `.on-the-record/test-tiers.json`).

This change touches `on-the-record/hooks/*.sh` and
`on-the-record/hooks/test_*.py`, both named in test-tiers.json's
`trigger_change_classes`, so the slow tier (`python3 -m pytest -q -m slow`)
was also run to completion before delivery.

canonical: python3 -m pytest -q -m slow
acceptance: python3 -m pytest -q -m slow — result: 1 failed, 105 passed, 2 xfailed (255.50s)

The one failure, in test/test_spawn_directive_assembly.py (test class
SinglePhaseSignal, test method test_without_flag_is_byte_identical_to_today),
is unrelated to this issue's write set — see Open findings.

## Open findings

The slow-tier run above surfaced 1 failure outside this issue's frozen write
set, in test/test_spawn_directive_assembly.py (test class SinglePhaseSignal,
test method test_without_flag_is_byte_identical_to_today): it asserts a
plain dict it builds itself (env_a = {}) excludes "CORE_BUILD_NOW", but this
build-now session's own ambient CORE_BUILD_NOW=1 leaks into it via
os.environ somewhere inside that test's own _run helper.

canonical: python3 -m pytest test/test_spawn_directive_assembly.py -k test_without_flag_is_byte_identical_to_today -q (rerun with CORE_BUILD_NOW unset)
acceptance: python3 -m pytest test/test_spawn_directive_assembly.py -k test_without_flag_is_byte_identical_to_today -q — result: 1 passed once CORE_BUILD_NOW is unset

Re-running that same test with CORE_BUILD_NOW explicitly unset passes clean,
per the canonical citation above, confirming this is a pre-existing
ambient-env leak in that test file's own env-construction, not something
this issue's approval-gate.sh diff caused. Filed as a deviation
(docs/reports/deviation-log.md, 2026-08-22T08:40:07Z) rather than fixed here,
since test/test_spawn_directive_assembly.py is outside this issue's frozen
write set. Resolution path: a follow-up issue should strip CORE_BUILD_NOW
from that test's own env construction the same way this issue's three test
helpers were fixed.

## Rationale for deviations

None — build-now bypass (contract v3 s19a) applied from the start: this
session's own env carries `CORE_BUILD_NOW=1`, so delivery proceeded directly
without a phase-1 proposal round, per the spawning task's explicit
authorization.
