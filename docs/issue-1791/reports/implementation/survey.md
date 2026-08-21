---
subject: issue-1791
kind: survey
---

# Survey: shadow-wiring call site for auto-approval (issue #1791)

## What #1739 already shipped

`gates/auto_approval_class.py` provides two entry points:

canonical: gates/auto_approval_class.py:1-297 (read in full this session)

- `classify(diff_paths, out_of_scope_paths=(), production_fixture_paths=())
  -> (class_, reason)` — pure, fail-closed diff classifier
  (`docs_only`/`test_only`/`not_eligible`).
- `shadow_verdict(diff_paths, gate_results, issue, pr, timestamp,
  out_of_scope_paths=(), production_fixture_paths=(), config_path=...,
  state_path=..., audit_log_path=...) -> ShadowVerdict` — composes
  `classify()` with three named boolean gate results
  (`gate_results: {"scope_adherence": bool, "stale_revert_guard": bool,
  "requirement_met": bool}`) plus quota/circuit-breaker state read from
  `.on-the-record/auto-approval-state.json`, and appends one line to
  `docs/reports/auto-approval-audit-log.md` in the same call
  (gates/auto_approval_class.py:212-268).
  - Empty state: absent `docs/specs/auto-approval-config.json`, or
    `shadow_mode: false`, makes it return immediately with
    `would_auto_approve=False` and writes nothing (no audit line, no
    state read) — gates/auto_approval_class.py:227-236.
  - It never calls or edits `on-the-record/hooks/approval-gate.sh`; the
    returned verdict is a label only (module docstring,
    gates/auto_approval_class.py:1-24).

`shadow_verdict()` has no call site anywhere in this tree today:

canonical: derived — `grep -rn "shadow_verdict(" --include=*.py .` (run
this session) matches only its own definition
(gates/auto_approval_class.py:212), its dataclass field name
(gates/auto_approval_class.py:118, unrelated), the audit-log f-string
inside its own body (gates/auto_approval_class.py:268), and its own
test file (gates/test_auto_approval_class.py); no other `.py` file in
the tree calls it. This is the gap the issue names.

`.on-the-record/auto-approval-state.json` is also absent from this
working tree — `load_state()`'s absent-file default (empty lists,
gates/auto_approval_class.py:154-165) is the state every first live
call will actually observe.

## Where an approval decision becomes observable to orchestration

Searched spawn.py and gates/*.py for where an APPROVE token or PR merge
for a phase-1 proposal is turned into a phase transition the
orchestration machinery acts on.

canonical: gates/ci.py:182-221, gates/ci.py:347-455 (read in full this
session)

1. `gates/ci.py:_phase_from_approval(repo, pr, issue, role)`
   (gates/ci.py:206-221) is the phase computation itself: it reads
   `_approved_roles_on_issue()` (issue-level `APPROVE issue-<n>/<role>`
   comments, allowlist-checked exact string match, gates/ci.py:182-203)
   and `_pr_reviews()` (PR-review Approve from an allowlisted, differing
   account) and returns `"phase2"` if either signal fired, else
   `"phase1"`. It is called from `_autodetect_issue_phase()`
   (gates/ci.py:347-385, call at line 384) when `--phase` was not
   supplied by the caller, which is itself invoked from `check()`
   (gates/ci.py:388 onward) — the CI entry point re-run on every
   PR-status-check tick.
   - This is a poll path in the issue's sense: `check()` re-runs against
     the PR's current comment/review state each tick, so an approval
     landing between ticks is observed on the next run.
   - Both approval-signal shapes the issue names (APPROVE issue comment,
     PR review Approve) are already unified here into one
     `phase1`/`phase2` value.

2. spawn.py's watchers (`_watch`, `_watch_all`, `_rearm_watcher_detached`,
   spawn.py:4817 onward) watch a spawned session's own event-log file
   (session-end/stall/crash) — not GitHub comments or reviews.

   canonical: derived — `grep -n "APPROVE" spawn.py` (run this session)
   matches only two unrelated string literals: spawn.py:1051 (a
   docstring sentence) and spawn.py:1553 (a different token,
   `APPROVE {subject}/scope`, used for a scope-approval check, not
   role-phase approval). Ruled out as the call site: no approval-signal
   read exists on this path.

3. `gates/spawn_on_pr.py` function `is_approval_blocked` (gates/spawn_on_pr.py:
   256-260) calls the same `_ci._approved_roles_on_issue()`, but only to
   decide whether to withhold auto-spawning `execution-observation`/
   `conformance-review` roles (`PR_TRIGGERED_ROLES`,
   gates/spawn_on_pr.py:34) — a narrower, differently-scoped consumer of
   the same underlying signal, not the phase-1-proposal to phase-2
   observation point the issue names.

Conclusion: `_phase_from_approval()` (gates/ci.py:206) is the
approval-observation call site — the one place that already polls,
unifies both approval-signal shapes, and sits upstream of behavior (its
return value gates whether phase-2 rules apply in `check()`).

## What the shadow call needs beyond `_phase_from_approval`'s current scope

`shadow_verdict()` requires `diff_paths` and a `gate_results` dict for
three gates. `_phase_from_approval()` currently reads only
comments/reviews. The three gates exist as independent modules, none
currently composed together:

canonical: gates/scope_adherence.py:1-100, gates/stale_revert_guard.py:
1-150, gates/requirement_met.py:280-332, gates/merge_gate.py:1-30 (read
this session)

- `gates/scope_adherence.py:check(root, issue, pr) -> (status, reason)`
  (status constants defined at gates/scope_adherence.py:26-28: one
  meaning success, plus `BLOCKED`/`ADVISORY`).
- `gates/stale_revert_guard.py:check_pr(repo, base_ref,
  pr_merge_base_ref, pr_head_ref) -> list[dict]` (empty list means the
  gate raised no objection).
- `gates/requirement_met.py:check(repo, issue, pr, ...)`.

`gates/merge_gate.py`'s `evaluate()` — the closest existing
cross-gate composition point — calls `check_runner`, `stale_revert_guard`,
and required-verification-record checks, but not `scope_adherence` or
`requirement_met`:

derived: `grep -n "scope_adherence\|requirement_met" gates/merge_gate.py`
— no match.

So wiring the shadow call means calling all three gates fresh at (or
immediately around) the `_phase_from_approval()` call site to build
`gate_results`, plus a PR-file list (`gates.changed_files(repo)` or the
PR-diff equivalent already used elsewhere in gates/ci.py) to build
`diff_paths`.

## Existing test conventions to reuse

canonical: gates/test_auto_approval_class.py:1-40, gates/test_closes_gate_ci.py:
160-272 (read this session)

`gates/test_auto_approval_class.py` exercises `classify()` and
`shadow_verdict()` directly against temp dirs with monkeypatched
`config_path`/`state_path`/`audit_log_path` — no `gh` calls, no
subprocess. `gates/test_closes_gate_ci.py` exercises
`_phase_from_approval()` by monkeypatching `spawn._issue_comments`,
`spawn._approvers`, and `ci._pr_reviews` (gates/test_closes_gate_ci.py:
173-272) — this is the pattern the new wiring test should follow for a
simulated-approval-event case, since it avoids any real `gh` invocation
while still exercising the real call path.

## Skip-condition check (scout-directive)

This issue's open decision is *where* inside this repo's own gate
modules to place the shadow call and how to source `gate_results`
without duplicating gate logic — an internal wiring decision resolved
by reading this repo's existing gate-composition patterns
(gates/merge_gate.py, gates/test_closes_gate_ci.py), which this survey
already did. There is no comparable external product/system to scout
against (shadow-mode wiring for this repo's own role-handoff contract
has no external analog), so the product-research sweep does not apply;
the decision itself is real and is argued in the proposal's Rationale,
not skipped.
