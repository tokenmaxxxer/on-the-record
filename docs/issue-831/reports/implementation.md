---
code_under_review:
  - spawn.py
  - tests/test_spawn.py
  - harness/driver.py
  - harness/signals.py
  - harness/test_driver.py
  - harness/test_signals.py
  - docs/handbooks/setup.md
type: feature
breaking: false
verdict: accepted
loop_state: committing
---

# issue-831 implementation report

Phase 2, per role-handoff contract v3 s19. Approved 2026-08-11
(`APPROVE issue-831/implementation`, single-account mode).

## What was done

canonical: `docs/issue-831/decisions/2026-08-11-setup-preflight-remote-gate.md` (this session)
Built `ensure_target_remote(cwd, unattended)` in `spawn.py` per the
merged ADR: a preflight gate wired before the two `main()` dispatch
branches that can reach `issue_workspace` (`drive`, spawn.py:4162; and
the bottom bare-spawn fallback, spawn.py:4207). No-op when `origin`
resolves; `sys.exit`s with a pre-delegation message when unattended and
no remote (never mid-delegation); offers the `setup.md`-documented
`gh repo create --private --source . --push` / point-at-existing-remote
confirmation via `input()` when attended, and writes a
`remote_setup_confirmed` `ledger_write` event on confirmation — no
silent auto-provision on any path. Uses `--unattended` (not
`sys.stdin.isatty()`) exactly per the ADR's alternatives-considered
rationale, so a scripted harness confirmation over piped stdin is not
misclassified as unattended.

canonical: `spawn.py` (this session, written)
`ensure_target_remote()` + its two `main()` call sites (`drive` branch,
spawn.py:4162; bottom bare-spawn fallback, spawn.py:4207).

canonical: `tests/test_spawn.py` `EnsureTargetRemote` (this session, written and run)
Test class: no-op, unattended fail-fast, attended-confirmed writes ledger
event, attended-refused writes none.
derived: `python3 -m pytest tests/test_spawn.py -k EnsureTargetRemote -q`
```
4 passed, 432 deselected in 0.19s
```

canonical: `harness/driver.py` (this session, written)
`instantiate_fixture_target(..., seed_remote_dir=None)` — steady-state
scenario seeding, per the #776 harness scenario spec.

canonical: `harness/signals.py` (this session, written)
`check_remote_setup_not_silently_bypassed()` — the new #831
no-remote-scenario signal, distinguishing "asked once, confirmed" from a
silent auto-provision.

canonical: `harness/test_driver.py`, `harness/test_signals.py` (this session, written and run)
Coverage for the two functions above.
derived: `cd harness && python3 -m pytest test_driver.py test_signals.py -q`
```
10 passed in 0.11s
```

canonical: `docs/handbooks/setup.md` (read this session)
No wording change: its existing "Once, per target repo" offer text is
what `ensure_target_remote` now prints and executes on confirmation, per
the architecture report's own finding (`docs/issue-831/reports/architecture.md`
"Consequences" section).

canonical: `tests/test_spawn.py` (this session, run)
Full regression, 436-case suite (includes the 4 new cases above).
derived: `python3 -m pytest tests/test_spawn.py -q`
```
436 passed in 35.19s
```

## Why / upstream basis

canonical: `docs/issue-831/reports/architecture.md` "Decision" section (read this session)
Implements the architecture-role hand-off verbatim: `ensure_target_remote()`
plus its two call sites, the `remote_setup_confirmed` harness signal, and
the two #776 fixture scenarios (steady-state remote-present; no-remote
scripted-confirmation graceful-degrade).

canonical: `harness/driver.py`, `harness/README.md` (read this session)
`harness/driver.py` is operator-side helper functions only — it does not
launch a live Claude Code session itself (docstring: "It does not launch
a live Claude Code session itself: that launch is an integration point
the operator wires to their own session-launch mechanism"). The two new
scenarios therefore land as fixture-seeding (`instantiate_fixture_target`)
and a transcript-dict signal check (`signals.py`), matching the existing
shape of every other function in both files — not a live end-to-end run,
which is out of scope for implementation-role and belongs to a future
execution-observation session per the architecture report's hand-off.

## What did not work

None.

## Open findings

None new.

## Next steps

None — this closes issue #831 step 3. An actual live #776 harness re-run
against these two scenarios is a separate future execution-observation
session's job, not implementation-role's.

## Resolution path

n/a
