---
code_under_review:
  - gates/flows.py
  - test_flows.py
  - test_spawn.py
  - docs/specs/flows-schema.md
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue-674

## What was done

Implemented the approved proposal's "What will be done" section verbatim:

- gates/flows.py, `flows_payload()`: removed the `import closure_sweep` /
  `closure_sweep.find_violations(...)` call entirely. `hygiene.closure_sweep`
  is now a literal `[]`; `hygiene.closure_sweep_skips` is built locally as
  one `{"subject": subject, "reason": "not-run-in-flows"}` record per key of
  `b` (`spawn.board(root)`, already computed earlier in the function),
  sorted by subject for deterministic output.
- test_flows.py: rewrote `test_closure_sweep_skips_surface_in_hygiene`
  (`FlowsStageMapping` class) as the red/green pair — it patches
  `closure_sweep.find_violations` to raise `AssertionError` if called at
  all, writes board records for two subjects, and asserts
  `hygiene.closure_sweep == []` and `hygiene.closure_sweep_skips` carries
  exactly one `not-run-in-flows` record per subject. Dropped the
  now-unused default `find_violations` mock from `setUp` — no other test
  in the file touches `closure_sweep`.
- test_spawn.py: dropped the same now-unused default mock from
  `FlowsPayload.setUp` (the `import closure_sweep` / `self.closure_sweep`
  assignment / default patch), and rewrote
  `test_hygiene_includes_closure_sweep_and_unapproved_prs` to assert the
  new not-run-in-flows shape (`closure_sweep == []`,
  `closure_sweep_skips == [{"subject": "issue-30", "reason":
  "not-run-in-flows"}]`) instead of a `find_violations` pass-through.
- docs/specs/flows-schema.md: updated §2.5's `closure_sweep`/
  `closure_sweep_skips` field notes to describe the new local-computation
  source and the `not-run-in-flows` reason; updated §4 to drop the "up to
  `S` calls — `gh issue view`" bullet (that fallback path no longer runs
  from `flows_payload` at all) and added a paragraph stating
  `hygiene.closure_sweep` is no longer sourced from any `gh`-hitting call;
  updated §7's worked example to show `closure_sweep: []` with a
  `closure_sweep_skips` entry in place of the old violation example.

## Why

repo-status-board's 60s per-repo subprocess budget had been timing out
against this repo's `flows --json` output since 2026-08-08, because
`find_violations()` falls back to a slow per-branch path under conditions
not yet root-caused. The approved proposal
(docs/issue-674/proposals/2026-08-11-flows-json-closure-sweep-not-run.md)
decided to keep the `hygiene.closure_sweep` field (dropping it would force
`schema_version: 2`, which repo-status-board's `SUPPORTED_SCHEMA_VERSION =
1` would reject outright) while removing the call that causes the
timeout, reporting every board subject as unchecked instead.

## Upstream

docs/issue-674/proposals/2026-08-11-flows-json-closure-sweep-not-run.md
(approved via the issue-level comment `APPROVE issue-674/implementation`,
single-account mode), built on
docs/issue-674/reports/implementation/survey.md. Both merged to main in
PR #717.

## Acceptance evidence

### 1. Timed live run — `spawn.py flows --json -C .` inside the 60s budget

derived: `{ time python3 spawn.py flows --json -C . > /tmp/flows_output.json ; }`
```
python3 spawn.py flows --json -C . >   0.30s user 0.21s system 12% cpu 3.968 total
exit=0
```
Real wall-clock 3.968s, exit 0 — well inside repo-status-board's 60s
per-repo timeout.

derived: `python3 -c "import json; d=json.load(open('/tmp/flows_output.json')); print(d['schema_version'], d['hygiene']['closure_sweep'], len(d['hygiene']['closure_sweep_skips']), len(d['flows']))"`
```
1 [] 165 165
```
`schema_version` stays 1, `hygiene.closure_sweep` is empty, and
`hygiene.closure_sweep_skips` carries one `not-run-in-flows` record per
subject currently on this repo's board (165, matching `len(flows)`).

### 2. Red/green unit pair — `find_violations()` never called from `flows_payload`

derived: `python3 -m pytest test_flows.py test_spawn.py -k FlowsPayload -q`
```
13 passed in 0.05s        (test_flows.py)
19 passed, 369 deselected in 0.15s   (test_spawn.py -k FlowsPayload)
```
Both files' rewritten tests patch `closure_sweep.find_violations` to
raise `AssertionError` if invoked (red: a regression that reintroduces
the call fails hard), then assert `hygiene.closure_sweep == []` and
exactly one `{"subject", "reason": "not-run-in-flows"}` record per
board subject in `hygiene.closure_sweep_skips` (green: current code).

### 3. `rsb --json` consumption

`rsb` is not installed as a command in this environment (`which rsb` →
not found; `pip show repo-status-board` → not found), but a checkout of
its source exists elsewhere on this host and is runnable without an
install step via `PYTHONPATH=<its src dir> python3 -m rsb.cli` (stdlib
`tomllib` on this Python 3.11 host covers the TOML-parsing dependency).
The default `~/.config/rsb/boards.toml` was not usable as-is for this
check: its `on-the-record` entry points `command` at a separate
plugin-installed copy of `spawn.py` under `~/.claude/plugins/`, which
does not carry this branch's uncommitted change — running against it
would not exercise the code under review. Instead, a scratch config
(`/tmp/rsb-test-config.toml`, not part of any repository) pointed the
`on-the-record` entry's `path` and `command` at this working checkout,
so rsb's own `flows --json -C <path>` subprocess call runs this
branch's actual `gates/flows.py`.

derived: `PYTHONPATH=<repo-status-board src dir> python3 -m rsb.cli --json --config /tmp/rsb-test-config.toml` (run from that other checkout's directory)
```
exit=0
```
derived: `python3 -c "import json; d=json.load(open('/tmp/rsb_output.json')); print(d['closure_sweep'], d['unapproved_open_prs'], d['errors'])"`
```
[] [] []
```
`errors: []` confirms rsb accepted and normalized the payload without a
schema mismatch or per-repo failure — its `SUPPORTED_SCHEMA_VERSION = 1`
check (the only path that would reject a payload) passed, matching
`gates/flows.py`'s `FLOWS_SCHEMA_VERSION = 1` (unchanged by this fix).
This is a real executed consumption, not the schema-shape fallback the
acceptance criterion allows when rsb cannot be run at all — rsb could be
run here, so that is the evidence recorded.

## Test run (full regression)

derived: `python3 -m pytest test_spawn.py -q`
```
386 passed, 2 skipped in 70.28s
```
derived: `python3 -m pytest test_flows.py -q`
```
13 passed in 0.05s
```

## What did not work

None — the change matched the approved proposal's "What will be done"
section without needing an approach change mid-build.

## Rationale for deviations

None — no deviation from the approved proposal occurred.

## Doc placement

- No new env var, config key, dependency, or migration introduced —
  nothing to add to a handbook.
- No changed public signature or wire format beyond what the proposal's
  `## What will be done` already specified (`hygiene.closure_sweep`
  stays `array`, `hygiene.closure_sweep_skips` stays `array`,
  `schema_version` stays `1`) — updated in place in
  docs/specs/flows-schema.md (§2.5, §4, §7), the system-design home for
  this contract.
- No benchmark/investigation numbers beyond the acceptance evidence
  already recorded above under `## Acceptance evidence`.

## Open findings

None.

## Hunt

- after-proposal (stance 0, phase 1): recorded in
  docs/issue-674/reports/implementation/hunt-flows-json-closure-sweep-not-run.md
  — FINDING against `accumulation-claim-guard.sh` (a gate-hygiene issue
  unrelated to this proposal's own write set; not actionable inside the
  frozen write set for this issue).
- before-landing (stance 1, this turn): dispatched
  `warrant:warrant-hunter`, stance "assume this change and another
  plugin's rule cancel each other — find the pair", 180s cap (diff >200
  lines across 4 files). Result: NO FINDING — no hook under
  on-the-record/hooks/ reads the `hygiene` key of the `flows --json`
  payload at all; `spawn.py`'s `_board_wide_sweep`/`roster_watchdog` and
  `gates/closure_sweep.py`'s own `--post` verb call
  `closure_sweep.find_violations()` directly and independently of
  `gates/flows.py`'s `flows_payload()`, confirmed genuinely untouched by
  this change. Full detail appended to the same hunt record file above
  under its own `## before-landing — stance 1` section. Dispatched and
  consumed synchronously within this turn per contract v3 s22
  (headless/single-shot — no later turn exists to receive an
  asynchronous hunter result).

closed_checks:
  - check: red/green unit pair (test_flows.py::FlowsStageMapping::test_closure_sweep_skips_surface_in_hygiene, test_spawn.py::FlowsPayload::test_hygiene_includes_closure_sweep_and_unapproved_prs)
    code_sha: (working tree at write time; see code_under_review file list above)
    result: both pass — find_violations patched to raise is never triggered
  - check: full existing test suite regression (test_spawn.py, test_flows.py)
    code_sha: (working tree at write time; see code_under_review file list above)
    result: 386 passed 2 skipped (test_spawn.py) + 13 passed (test_flows.py), 0 failed
  - check: before-landing warrant hunt, stance 1 (cancelling-pair)
    code_sha: (working tree at write time; see code_under_review file list above)
    result: NO FINDING — see docs/issue-674/reports/implementation/hunt-flows-json-closure-sweep-not-run.md
