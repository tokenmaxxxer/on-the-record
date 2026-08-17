---
code_under_review:
  - on-the-record/hooks/stop-gate.sh
  - on-the-record/hooks/deviation-log-guard.sh
  - on-the-record/hooks/role-test-claim-guard.sh
  - on-the-record/hooks/report-framing-check.sh
  - on-the-record/hooks/product-capture-stopgate.sh
  - on-the-record/hooks/test_stop_gate.py
  - on-the-record/hooks/test_deviation_log_guard.py
  - on-the-record/hooks/test_role_test_claim_guard.py
  - on-the-record/hooks/test_report_framing_check_live.py
  - on-the-record/hooks/test_product_capture_stopgate.py
type: fix
breaking: false
verdict: pending
loop_state: landed
---

# Implementation record — issue #1725

## What was done

Ported the `stop_hook_active` short-circuit guard from
`decision-queue-stopgate.sh` (#1718) into the five sibling Stop hooks
named in #1725's acceptance line, exactly per
`docs/issue-1725/proposals/2026-08-17-stop-hook-active-guard-port.md`:

- `stop-gate.sh`, `deviation-log-guard.sh`, `report-framing-check.sh`,
  `product-capture-stopgate.sh` — added the two-line guard directly
  below each file's existing `if not isinstance(e, dict): sys.exit(2)`
  check, before the first other field of `e` is read.
- `role-test-claim-guard.sh` — added the same two-line guard directly
  below its dict-guard (which exits 0, not 2), before role-identity
  resolution begins — matching #1718's own before-role-resolution
  placement per the proposal's Rationale.
- Extended `test_deviation_log_guard.py`, `test_role_test_claim_guard.py`,
  `test_product_capture_stopgate.py` with a `stop_hook_active` parameter
  on each file's `_run()` helper (default `False`) and one new
  `t_stop_hook_active_emits_nothing_for_*` test per file, reusing an
  existing scenario that otherwise produces `additionalContext`.
- Added `test_stop_gate.py` and `test_report_framing_check_live.py` (new,
  neither previously existed in `on-the-record/hooks/`), each with a
  `_run()` helper matching `test_role_test_claim_guard.py`'s
  payload-to-subprocess shape, covering the hook's existing structural
  branches plus the required `stop_hook_active` case. The second file's
  bare name differs from the proposal's frozen `test_report_framing_check.py`
  — see Rationale for deviations.

## Why

basis: `docs/issue-1725/proposals/2026-08-17-stop-hook-active-guard-port.md`

The harness treats a Stop hook's `additionalContext` as inject-and-resume
— the same loop-guard as `decision:"block"` — and forced turns carry
`stop_hook_active: true`. These five hooks could hold a turn open across
up to 8 forced re-entries whenever their trigger condition persisted
across the reply the block itself forced. #1718 already fixed this for
`decision-queue-stopgate.sh`; this closes the identical gap on its five
siblings.

## Rationale for deviations

One alternative-swap from the approved proposal's file list: the new
report-framing-check test file's bare name is `test_report_framing_check_live.py`,
not the proposal's frozen `test_report_framing_check.py`.
canonical: derived: `comm -12 <(find gates -maxdepth 1 -name 'test_*.py' -exec basename {} \; | sort) <(find on-the-record/hooks -maxdepth 1 -name 'test_*.py' -exec basename {} \; | sort)` (this session, run against the frozen name before the rename)
```
test_report_framing_check.py
```
That command's single hit was the only basename collision in the whole
tree — and the only one this session's own new file introduced — against
`gates/test_report_framing_check.py`, which already claims that exact
module basename (neither directory carries an `__init__.py`, so `pytest`
requires unique basenames across a shared collection run). With the
frozen name in place, `pytest` aborted collection for the repo's whole
default test run with an import-file-mismatch error rather than merely
skipping the one file. Considered and rejected: keeping the frozen name
and adding `__init__.py` markers to disambiguate the two directories —
rejected as a larger structural change than a one-file rename, and
outside this issue's frozen write set (it would touch `gates/` and
repo-wide pytest collection behavior, not just the five named hooks and
their tests). Classified INLINE-FIX per the role-deviation-directive:
stays inside `on-the-record/hooks/` (the frozen directory, just not the
frozen leaf filename), mechanical (an import-collision rename, no
design/security/product judgment), does not change what the deliverable
claims to do (same coverage, same assertions), and is a one-off.

Logging this to the shared issue-1725 deviation log (the path the
role-deviation-directive names, docs/issue-1725/reports/deviation-log.md,
sibling to this file) was attempted and blocked: the `Write` tool call
was refused twice this session by `core`'s `board-gate.sh` R5 rule,
which admits only `<role>.md`, `<role>/**`, or a `feasibility`/
`ops`-only extra subtree under `docs/issue-<n>/reports/` — a bare
`deviation-log.md` matches none of those for the `implementation` role.
canonical: `/Users/jk/.claude/plugins/cache/tokenmaxxxer-core/core/d0b6ce3aaddf/hooks/board-gate.sh:77,599-614` (read in full this session)
This is an apparent environment gap between two plugins (on-the-record's
deviation-log convention and core's per-role record-ownership gate),
outside this issue's write set to fix — left as an open finding below
rather than worked around.

## What did not work

Expected: the shared issue-1725 deviation log could be appended with
the inline-fix entry above, per the role-deviation-directive. Actual:
`core`'s `board-gate.sh` refused the write both times this session
("belongs to another role") — see Rationale for deviations above for
the citation. No deviation-log file exists on disk for this issue as a
result.

## Test run

derived:
```
$ python3 -m pytest -o addopts="" on-the-record/hooks/test_stop_gate.py on-the-record/hooks/test_deviation_log_guard.py on-the-record/hooks/test_role_test_claim_guard.py on-the-record/hooks/test_report_framing_check_live.py on-the-record/hooks/test_product_capture_stopgate.py on-the-record/hooks/test_decision_queue_stopgate.py -q
...................................................................      [100%]
67 passed in 7.11s
```

Re-ran collection with the renamed file plus its former collision
partner in the same run, as the live check on the rename above.
canonical: derived: `python3 -m pytest -o addopts="" -q on-the-record/hooks/ gates/test_report_framing_check.py` (this session, after the rename)
```
554 passed, 2 xfailed in 102.08s (0:01:42)
```

The `-o addopts=""` override is needed in this environment because
`pytest.ini`'s own `addopts = -n auto` requires `pytest-xdist`, which
this environment lacks (`pip show pytest-xdist` prints nothing) — an
environment gap, not something introduced by this change.

Also ran the repo's declared fast test tier
(`.on-the-record/test-tiers.json`'s `fast` command, same `-o addopts=""`
override) since this issue's diff matches that same config's `slow`-tier
`trigger_change_classes` too (`on-the-record/hooks/*.sh`,
`on-the-record/hooks/test_*.py`).
canonical: derived: `python3 -m pytest -q -m "not slow" -o addopts=""` (this session)
```
22 failed, 2239 passed, 2 skipped, 102 deselected, 18 xfailed, 3 xpassed in 319.18s (0:05:19)
```
canonical: derived: `git stash -u` then re-running the same 22 failing node IDs with `python3 -m pytest -o addopts="" -q <22 node ids>` against the stashed (pre-change) tree, this session
```
22 failed in 5.10s
```
Same 22 node IDs failed both before and after this change (the two
runs' short summaries were diffed by eye in this session), and none of
the 22 files reference any of the five hooks this issue touches —
pre-existing and unrelated. `git stash pop` restored this change's
edits immediately after.

The 319s wall-clock exceeds the tier config's declared 300s
`budget_seconds` by roughly 19s — noted per the test-tier directive's
observe-only contract, not treated as a refusal condition.

## Open findings

`core`'s `board-gate.sh` R5 rule has no path for any role to write the
shared per-issue deviation-log file that on-the-record's own
`deviation-log-guard.sh` Stop hook (part of this issue's own write set)
and the role-deviation-directive both expect a role session to append to
directly — R5 only admits `<role>.md`, `<role>/**`, or a `feasibility`/
`ops`-only extra subtree.
canonical: `/Users/jk/.claude/plugins/cache/tokenmaxxxer-core/core/d0b6ce3aaddf/hooks/board-gate.sh:599-614` (read in full this session)
resolution path: outside this issue's frozen write set (it lives in the
`core` plugin, not `on-the-record/hooks/`) — worth a separate issue
against core's `board-gate.sh` R5 to add a shared-record exemption for
the deviation log, filed by a future session, not this one (role-session
scope-exceeded rule: report, do not spawn).

## Doc placement

- No env var, config key, new dependency, migration, or setup step was
  introduced — a handbook entry is not needed.
- No library-or-format choice over a named alternative, and no changed
  public signature/wire format — a decisions-bucket entry is not needed.
- No benchmark or investigation numbers beyond the test run itself,
  already recorded above under Test run.

## Hunt

Warrant-hunter dispatched pre-completion, stance: does the
`stop_hook_active` guard port contain a placement / field-shape /
lost-side-effect / test-fidelity defect. NO FINDING, per the hunter's
own report this session.
canonical: derived: the warrant-hunter subagent dispatched this session, whose full report is filed at docs/issue-1725/reports/implementation/2026-08-17-hunt-stop-hook-active-guard-port.md

closed_checks (each per the same hunt report cited above):
- placement: identical across all 5 files, before any other field of
  `e` is read, matching decision-queue-stopgate.sh's own #1718
  placement.
- field shape: all 5 hooks share one `"Stop"` array entry in
  on-the-record/hooks/hooks.json, so `e.get("stop_hook_active")` reads
  the same top-level envelope field for every one of them.
- side effects: only product-capture-stopgate.sh writes state before
  the new short-circuit point, and decision-queue-stopgate.sh's own
  #1718 guard already skips its own analogous state writes at the same
  placement — not a new regression, and the skipped write simply
  re-attempts on the next non-forced Stop.
- test fidelity: every new/edited test invokes the real .sh file by
  subprocess path, and each new stop_hook_active case reuses a scenario
  an existing sibling test already proves triggers real output.

## Landed

canonical: derived: `gh pr view 1728 --json number,state,headRefName,url,commits --jq '{number,state,headRefName,url,lastCommit:(.commits[-1].oid)}'` (this session)
```
{"headRefName":"issue-1725/implementation","lastCommit":"4a78d9dbc652c42ad234e7337cc77fb39ccf9102","number":1728,"state":"OPEN","url":"https://github.com/tokenmaxxxer/on-the-record/pull/1728"}
```
Committed on issue-1725/implementation (commit 4a78d9db, Subject:
issue-1725 trailer present), pushed to origin, and PR #1728 already
open against main carries this commit as its head.
