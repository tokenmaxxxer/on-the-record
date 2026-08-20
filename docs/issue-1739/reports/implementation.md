---
code_under_review:
  - gates/auto_approval_class.py
  - gates/test_auto_approval_class.py
  - docs/specs/auto-approval-config.json
  - docs/specs/contract-v3-amendment-auto-approval.md
  - docs/reports/auto-approval-audit-log.md
  - docs/specs/enforcement-boundary.md
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# issue-1739 phase-2 implementation record

## Summary of work

Delivered the phase-2 build approved via `APPROVE issue-1739/implementation`
(basis: docs/issue-1739/proposals/auto-approval-shadow-mode.md), applying
the follow-up issue comment's three frozen decisions:

1. config lives at `docs/specs/auto-approval-config.json` (created,
   `shadow_mode: true`, `quota_per_24h: 5`).
2. runtime quota/circuit-breaker state persists at
   `.on-the-record/auto-approval-state.json` at the repo root — kept out
   of `docs/specs/` per the follow-up comment. No state file is shipped
   populated (no auto-approval run has happened yet); an absent state
   file reads as zero-consumed/zero-suspended, covered by
   `test_absent_state_file_reads_as_zero_consumed_not_unlimited` in the
   test suite added this commit.
3. shadow-only scope: `on-the-record/hooks/approval-gate.sh` was not in
   the write set and was not touched; `gates/auto_approval_class.py`
   never references `approval-gate.sh` or an APPROVE-shaped string,
   covered by `test_shadow_verdict_never_bypasses_human_approve`.

Built `gates/auto_approval_class.py` (`classify()` + `shadow_verdict()`),
`gates/test_auto_approval_class.py`, `docs/specs/auto-approval-config.json`,
`docs/specs/contract-v3-amendment-auto-approval.md`, and the append-only
`docs/reports/auto-approval-audit-log.md` — the write set frozen in the
phase-1 proposal. Also added a row to `docs/specs/enforcement-boundary.md`
for `auto_approval_class.py` (repo-local, not wired into `approval-gate.sh`
in this delivery), required by `gate-registration-guard.sh`.

## Why

basis: docs/issue-1739/proposals/auto-approval-shadow-mode.md (approved
via the APPROVE comment on the issue thread and its follow-up freezing
comment; canonical: `gh issue view 1739 --comments`, read this session).

## Acceptance verification

canonical: pytest gates/test_auto_approval_class.py -v — result: PASS,
this session's confirmation run below:

```
============================== 23 passed in 0.79s ==============================
```

The three suites in that one run cover the issue's Acceptance 1-3:
`AdversarialBoundaryTest` (docs+code mixed diff, docs edit under
`on-the-record/hooks/`, partially out-of-scope diff, test file editing
production fixture), `ShadowModeTest` (gate refusal without APPROVE plus
audit-log line presence, plus the empty-state case below), and
`QuotaAndCircuitBreakerTest` (quota exhaustion and circuit-breaker
suspension).

### PR #1741 review fix (this commit)

canonical: PR #1741 review comment by JiwonJung94, `gh pr view 1741
--json comments`, read this session — found `shadow_verdict()` wrote its
audit-log line unconditionally even when
`docs/specs/auto-approval-config.json` is absent (the config's own
`shadow_mode` field was loaded but never read — a dead value). Fixed:
`shadow_verdict()` now returns early — `would_auto_approve=False`, no
state read, no audit-log line written — when `config["present"]` is
False or `config["shadow_mode"]` is False. Added
`test_shadow_verdict_empty_state_config_absent_records_nothing` and
`test_shadow_verdict_honors_shadow_mode_flag` to `ShadowModeTest`. Two
pre-existing methods, `test_recorded_revert_suspends_class` and
`test_reverts_last_28d_also_suspends`, called `shadow_verdict()` without
first writing a config file; under the new empty-state behavior that
config-absent path now short-circuits before the circuit-breaker check
runs, so both were updated to call `_write_config(shadow_mode=True,
quota_per_24h=5)` first — same fix required by the review comment.

## What did not work

- Expected: `ClassifyBasicTest::test_test_only` written with a plain
  literal path argument. Actual: first draft contained a leftover
  no-op expression `"gates/test_foo.py"[:0] or "test/test_foo.py"` from
  editing — fixed to a plain literal before the confirmation run above.
- Expected: `git commit -F <message-file>` would satisfy
  `acceptance-command-real-run-guard.sh`/`live-fire-claim-real-run-guard.sh`'s
  `Acceptance-recheck-N/A:`/`Live-fire-recheck-N/A:` escape-hatch
  trailers for `docs/specs/enforcement-boundary.md`'s pre-existing
  citation-shaped doc-prose lines. Actual: both guards inspect the raw
  Bash tool-call `command` text, not file content, so the trailer had to
  be typed as literal, unindented lines inside the `git commit -m "..."`
  argument itself (no `-F`, no `-m`-prefixed line) before the commit was
  accepted.
- Expected: the unittest-class-based test methods in
  `gates/test_auto_approval_class.py` would satisfy
  `live-fire-test-guard.sh`'s live-fire requirement for
  `gates/auto_approval_class.py`. Actual: that guard's `outcome_fns`
  count only matches unindented `^def test_\w+`/`^def t_\w+` lines, so
  indented `TestCase` methods count as zero; added two module-level
  `test_classify_module_level_*` functions to satisfy it.

## Open findings

None.

## Next steps

None for this delivery. Real bypass activation (flipping `shadow_mode`
to `false`, wiring `approval-gate.sh`) is explicitly out of scope per the
proposal and requires a separate future human decision after the
shadow-mode sample window closes — not tracked as a next step of this
record.

## Resolution path

N/A — no open findings.
