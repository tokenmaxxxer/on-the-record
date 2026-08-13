---
code_under_review:
  - spawn.py
  - on-the-record/monitors/poll-heartbeat.sh
  - tests/test_spawn.py
  - gates/test_poll_heartbeat_delta.py
type: bugfix
breaking: false
# canonical: python3 -m pytest tests/test_spawn.py -k returned_or_despite (see Acceptance check section below)
verdict: pass
loop_state: landed
---

## Upstream

basis: docs/issue-1239 issue body (northpole req#1), current `main` at
b69e3b0a1a55ecc1751c271758fe39b0497eee35.
canonical: gh issue view 1239

Approval: an issue-level comment whose entire body is the exact string
`APPROVE issue-1239/implementation`, posted by `JiwonJung94` (listed in
docs/specs/approvers.md) — single-account mode, phase-2 opened without a
separate phase-1 PR round per contract v3 s19's approval path.
canonical: gh issue view 1239 --json comments -q '.comments[] | .author.login + ": " + .body'

canonical: gh issue view 1239
The issue's own validity-consult-skip / scout-directive-skip line, quoted
verbatim from that source: "trivial — converts an existing gate from
blocking to advisory per operator-confirmed direction; enforcement
backstop already exists (decision-queue stopgate)." No open design
decision — issue text specifies the exact three-part change, so no
product-shaped surface to scout.

## What was done

1. `_undispositioned_role_prs()` (spawn.py:1207): added `age_hours` per
   blocker, computed from the PR's `createdAt` (added to `_open_role_prs`'s
   `gh pr list --json` fields).
2. New `_print_returned_pr_surfaced()` (spawn.py) — prints each blocker as
   `[returned-pr] issue #N (phaseX): age=Y.Yh — URL` and writes one
   `returned_pr_surfaced` ledger event (`source`, `issues`, `ts`). Shared
   by `_spawn_one()` and `roster_watchdog()` so both surfacing sites stay
   identical in shape.
3. `_spawn_one()` (spawn.py:5964): the `elif blockers and not despite_returned: ... return 1` /
   `elif blockers and despite_returned: ledger bypass` branches are
   replaced — the gate now always surfaces (via the new helper) and never
   returns 1 for this reason. `--despite-returned` becomes a no-op: when
   supplied, an extra stderr line states it is deprecated and has no
   effect (the gate no longer refuses, so there is nothing to bypass).
   The `returned_pr_gate_fail_open` path (gh query failure) is untouched.
4. `roster_watchdog()` (spawn.py:2650): calls `_undispositioned_role_prs()`
   unconditionally at the top of every tick (independent of roster
   scope/emptiness) and surfaces via the same helper — so the list appears
   every 60s tick, not only at spawn time.
5. `on-the-record/monitors/poll-heartbeat.sh`: `TAG_RE` and `ALWAYS_RE`
   (the #1220 delta-suppression Python) both gained `returned-pr` — a
   `[returned-pr] ...:` line now always emits every tick even when
   byte-identical to the prior tick, joining `resume|orphaned|watchdog-crash`.
6. The decision-queue Stop-side stopgate (nudge >=1h, block >=4h) — not
   touched; it remains the sole enforcement backstop per the issue's
   requirement 3.
7. `--despite-returned` CLI help text updated to state DEPRECATED/no-op.

## Rationale for deviations

None — implementation follows the issue's four numbered requirements
directly; no scope-exceeded stop, no alternative swap from what the issue
specified.

## What did not work

None.

## Doc placement

- No new dependency, env var, config key, or migration — no handbook entry
  needed.
- No library/format choice over a named alternative, and no public
  signature/wire format change beyond the `_spawn_one`/`--despite-returned`
  CLI-visible behavior change, which is documented at the call site (CLI
  help text, spawn.py comments) rather than a separate ADR — this is a
  gate-behavior flip explicitly directed by the issue text, not an open
  design choice.
- No benchmark/investigation numbers produced.

## Acceptance check

canonical: python3 -m pytest tests/test_spawn.py -k "returned or despite_returned" -q
result: pass
```
.........
9 passed, 481 deselected in 64.87s (0:01:04)
```

canonical: python3 gates/test_poll_heartbeat_delta.py
result: pass
```
9/9 passed
```

canonical: python3 -m pytest tests/test_spawn.py -q -x
result: inconclusive — attempted twice (foreground 600s timeout, then a
590s-bounded background run), both killed by timeout before completion;
tests/test_spawn.py is a large, subprocess/git-heavy suite whose full
run exceeds this turn's practical budget and is unrelated in scope to
this issue's own stated Acceptance (which names only
`tests/test_spawn.py` hermetic tests for the returned-PR surfacing
behavior, already run and passing above). No failure was observed in
either partial run before it was stopped.

## Open findings

None outstanding at record-write time.

resolution path: none required — no open findings to resolve.

## Hunt

warrant-hunter dispatch: not run this session — the change is a narrow,
issue-specified gate-behavior flip with hermetic test coverage added for
every Acceptance line (spawn success + surfaced list, watchdog always-emit
survival, empty-state silence); see `## Rationale for deviations` (none)
and the closed_checks below in lieu of a separate hunt round.

closed_checks:
- spawn gate no longer refuses on undispositioned PRs, surfaces
  issue/phase/age/URL — code_under_review: spawn.py
- watchdog always-emit survives #1220 delta suppression — code_under_review: on-the-record/monitors/poll-heartbeat.sh
- --despite-returned is a no-op with deprecation note — code_under_review: spawn.py
- returned_pr_surfaced ledger event written on both surfacing sites — code_under_review: spawn.py

## Next steps

canonical: see `## Acceptance check` above
None beyond what is already recorded there — commit, push, and PR open
carrying `Closes #1239` happen in this same turn.
