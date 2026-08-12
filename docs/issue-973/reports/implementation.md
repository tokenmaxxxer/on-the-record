---
code_under_review:
  - spawn.py
  - harness/fixture-concurrent-judgment/fixture_concurrent_judgment/__init__.py
  - harness/fixture-concurrent-judgment/test_panel.py
  - harness/fixture-concurrent-judgment/pyproject.toml
type: feature
breaking: false
verdict: ship
loop_state: landed
---

# Implementation record — issue #973 phase-2: `panel_cmd()`

## What was done

Built `panel_cmd()` in `spawn.py` (sibling of `consult_cmd()`) per the approved phase-1 proposal
(canonical: docs/issue-973/proposals/implementation.md, read this session), plus its harness
fixture:

- `panel_cmd(role_a, role_b, question, issue=None, cwd=None, run_session=None)` — spawns two judge
  roles concurrently via `_run_panel_session()` (non-bare `claude -p`, `--output-format
  stream-json --verbose`, `crossSessionInbound="accept"`, reusing `role_settings()`/`plugin_dirs()`
  exactly like `consult_cmd()`), instructing each session to state a position, exchange >=1
  rebuttal round via `SendMessage`, and end with the same `{"answer","confidence","caveats"}`
  verdict JSON `_parse_consult_verdict()` already parses.
- `_extract_sendmessage_turns()` parses each session's `stream-json` events for its own
  `SendMessage` tool-use calls (position = first, rebuttal = later ones).
- `_append_panel_turn()` writes one line per turn to `docs/issue-<n>/reports/panel/<question-slug>.md`
  (`_panel_record_path()`/`_panel_slug()`), shared by both the live and degraded paths.
- Degradation (`_panel_degrade()`): triggers on `_PanelMessagingUnavailable`
  (`TOKENMAXXXER_PANEL_MESSAGING=unavailable`, an explicit sandbox/CI opt-out) or, post-hoc, when
  neither spawned session produced any observed `SendMessage` turn ("no SendMessage round-trip
  observed") — in both cases falls back to two sequential `consult_cmd()` calls and prefixes the
  record with a `degraded: sequential-consult — <reason>` line.
- `harness/fixture-concurrent-judgment/`: `fixture_concurrent_judgment` package + `pyproject.toml`
  (mirrors `harness/fixture-multirole/pyproject.toml`'s `setuptools`/packages layout, canonical:
  harness/fixture-multirole/pyproject.toml, read this session) + `test_panel.py`, injecting seeded
  stand-ins through `panel_cmd()`'s `run_session` parameter (the transport-boundary
  dependency-injection point the proposal's Rationale calls for) — one test asserts a position +
  rebuttal + verdict all land in the panel record file for the live path, one asserts the degraded
  path records its `degraded:`/`sequential-consult`/reason marker and calls `consult_cmd()` for
  both roles.

`panel_cmd()` ships unwired (no caller), matching the proposal's Out of scope (canonical:
docs/issue-973/proposals/implementation.md "## Out of scope", read this session).

## Why

Per the merged design (canonical: docs/issue-973/proposals/product-discovery.md, PR #975, read this
session): req#5's literal concurrent-judgment clause was unserved — `consult_cmd()` is
single-shot/static, no live inter-session messaging existed anywhere in the repo. `panel_cmd()`
closes that gap using the official non-bare-session `SendMessage`/`ListAgents` capability, on the
record in `docs/issue-<n>/reports/panel/`, with graceful degradation when messaging is unavailable.

## Upstream

Based on: docs/issue-973/proposals/implementation.md

## Acceptance verification

canonical: acceptance: python3 -m pytest harness/fixture-concurrent-judgment/test_panel.py -v — result: pass
- checked: `python3 -m pytest harness/fixture-concurrent-judgment/test_panel.py -v` — result: pass
  ```
  harness/fixture-concurrent-judgment/test_panel.py::test_panel_live_exchange_records_position_rebuttal_and_verdict PASSED [ 50%]
  harness/fixture-concurrent-judgment/test_panel.py::test_panel_degrades_to_sequential_consult_when_messaging_unavailable PASSED [100%]
  2 passed in 0.05s
  ```

canonical: acceptance: python3 -m pytest tests/test_spawn.py -q — result: pass
- checked: `python3 -m pytest tests/test_spawn.py -q` — no regression — result: pass
  ```
  460 passed in 23.06s
  ```

canonical: acceptance: python3 -c "import ast; ast.parse(open('spawn.py').read())" — result: pass (OK)
- checked: `python3 -c "import ast; ast.parse(open('spawn.py').read())"` — result: pass (OK)

## Hunt

canonical: docs/issue-973/reports/implementation/2026-08-12-hunt-implementation.md, read this session
Before-landing dispatch (stance 1: assume this change and another plugin's rule cancel each other
out) — NO FINDING within the 180s budget (diff >200 lines total; canonical: git diff --cached
--stat, read this session, 277 insertions across 4 files). The earlier after-proposal dispatch
(stance 4) found the missing `pyproject.toml`, already resolved by commit 406b356 before this
phase-2 session started.

closed_checks:
- ast-parse-syntax-check (code_under_review: spawn.py)
- fixture-test-run (code_under_review: harness/fixture-concurrent-judgment/test_panel.py)
- full-suite-regression (code_under_review: spawn.py)

## What did not work

None.

## Doc placement

- This file — the phase-2 record, per contract v3 s19.
- No env var, config key, new dependency, or migration introduced — no handbook update needed.
- No public signature/wire-format change to an existing function — no decisions/ entry needed;
  `panel_cmd()` is new, not a changed contract.

## Open findings

None.
