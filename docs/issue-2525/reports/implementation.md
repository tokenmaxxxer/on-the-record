---
issue: 2525
role: implementation
author: implementation
loop_state: in-progress
upstream:
  - path: docs/issue-2137 (record-is-the-regression-suite decision)
    sha: same-commit
code_under_review:
  - PLACEHOLDER: path/to/file
type: chore
breaking: removes the plugin's own pytest suite (tests/*.py, gates/test_*.py, on-the-record/hooks/test_*.py, conftest.py, tests/data/, tests/fixtures/); nothing in shipped gate/hook behavior changes
verdict: fail
---

# issue-2525 — implementation record

## What was done

Removed the plugin's own pytest suite via `git rm`, per the operator's #2525
decision extending #2137 ("the record IS the regression suite") to the
plugin's own tooling. acceptance: `git status --short | grep -c '^D '` —
result: PASS derived: `git status --short | grep -c '^D '` — output: 232.

Scope removed: all of `tests/*.py`, all of `gates/test_*.py` except one
exception below, all of `on-the-record/hooks/test_*.py`, plus `conftest.py`
and the support directories `tests/data/` (untracked, deleted this commit)
and `tests/fixtures/` (untracked, deleted this commit).

**Exception, load-bearing:** `gates/test_tier_contract.py` matches the
`gates/test_*.py` glob but is NOT a test — its own docstring states "Sole
live consumer: watchdog.py's standing_red_check". derived: `grep -n
test_tier_contract watchdog.py` — result:
```
1339:    import test_tier_contract
1340:    return test_tier_contract.load_contract(root)
```
Deleting it would ImportError watchdog.py's standing-red-zero check at
runtime, so it was excluded from removal and left in place.

## Why

canonical: issue #2525 body (`gh issue view 2525`, read this session). The
issue body states, as already-measured harm (quoted from the issue, not
re-derived this session): fixture-repo leaks into `/tmp`, nested
pytest/xdist/concurrent-session load, and that #2516's own retirement
session stalled by running the suite it was meant to retire.

## Mid-flight scope correction — not executed

amendments-reconciled: issuecomment-5421024494 — derived: `gh api
/repos/{owner}/{repo}/issues/comments/5421024494 --jq .body`, read this
session (truncated to first 600 chars of the fetched body). The operator
posted, after this session started, a correction withdrawing the
capability-mapping ask and instead directing: delete the suite AND the
guards that police it — `acceptance-command-real-run-guard.sh`,
`live-fire-claim-real-run-guard.sh`, `live-fire-test-guard.sh` — unregister
them from `pretooluse_dispatcher.py`'s `GATES` and `hooks.json`, then delete
the scripts. **This was NOT executed this session** — read too late, with no
turn budget left to act on it. The rest of this record (below) reflects the
ORIGINAL issue-body scope (keep both real-run guards), which this comment
supersedes. Resolution path: next session re-fetches the full comment body
(only the first 600 chars were read here), reconciles with the operator if
still ambiguous, deletes the three named guard scripts and their
registrations, and updates this record's verdict.

## Capability inventory (no silent drops)

canonical: four parallel read-only research-agent transcripts from this
session (full output in this turn's tool-result history, not separately
persisted — see Open findings, finding 4).

- **`gates/test_*.py`:** most map 1:1 to a `gates/<stem>.py` module
  registered in `docs/specs/enforcement-boundary.md` or with a confirmed live
  in-process caller (agents confirmed by grep, e.g. `evidence_check`→
  `consult.py`, `gh_cache`/`gh_delta`→`watchdog.py`,
  `requirement_met`/`human_comprehensibility`→`gates/ci.py`) — status
  `covered-by-gate`. A named subset has no gate/CI caller found and is
  **OPEN GAP**: `test_boundary_workflow_migration.py`,
  `test_call_shape_and_report_framing_docs.py`, `test_capability_gates.py`,
  `test_clean_reconcile_safety.py`, `test_consult_gate_lib_env.py`,
  `test_consult_json_parse.py`, `test_consult_siblings.py`,
  `test_consult_verdict_parsing.py`, `test_design_bearing_classifier_live_fire.py`,
  `test_hooks_parity.py`, `test_measure_skill_reflection.py`,
  `test_merge_state_gate.py`, `test_poll_heartbeat_delta.py`,
  `test_poll_heartbeat_patrol.py`, `test_product_capture_vs_deliverable_guard.py`,
  `test_assumption_ledger.py`, `test_constitution_check.py`,
  `test_frozen_decisions.py`, `test_report_contract_directive.py`,
  `test_requirement_drift.py`, `test_requirement_linkage_rest.py`,
  `test_role_utilization_report.py`, `test_scope_option_directive.py`,
  `test_secure_coding_routing.py`, `test_skill_outcome_contrast.py`,
  `test_role_spec_shape_open_decision.py`.

- **`on-the-record/hooks/test_*.py`:** files for hooks wired in
  `hooks.json`/the dispatcher are `covered-by-hook` — derived: reading
  `on-the-record/hooks/hooks.json` this session. A subset was already
  DEMOTED (deregistered per #2138/#2144) before this issue existed:
  `absorbed-branch-recut-guard.sh`, `call-shape-guard.sh`,
  `decision-queue-stopgate.sh`, `delegated-judgment-gate.sh`,
  `delegation-post-gate.sh`, `deviation-log-guard.sh`, `live-fire-test-guard.sh`,
  `product-capture-stopgate.sh`, `quality-bar-gate.sh`, `report-framing-check.sh`,
  `role-deviation-directive.sh`, `record-claim-shape-directive.sh` — their
  unit tests were the last thing verifying that dormant behavior, so those
  are **OPEN GAP**, pre-existing. `test_record_scaffold.py` is also
  **OPEN GAP** (CLI-only, never hook-wired).

- **`tests/*.py`:** the majority are **OPEN GAP** — internal
  spawn.py/lifecycle.py/watchdog orchestration-loop correctness runs live in
  production (reachable) but had no check besides the deleted unit test. One
  research agent's row wrongly claimed `tests/test_repo_scope_gate.py`
  (untracked, deleted this commit) was covered by `gates/test_repo_scope.py`
  (untracked, deleted this commit) — both were removed by this same commit,
  so true status is OPEN GAP, corrected here rather than trusted as reported.

## Guards still deny a fabricated result (original scope — see correction above)

Not executed live this session — turn-budget ran out before staging a
throwaway commit. Verified instead by reading both scripts this session:

- `on-the-record/hooks/acceptance-command-real-run-guard.sh` — derived:
  reading the script — re-runs the cited `acceptance: <cmd>` argv against the
  `docs/specs/acceptance-commands.md` registry via `subprocess.run`, never
  touches `gates/test_*.py`/`hooks/test_*.py`.
- `on-the-record/hooks/live-fire-claim-real-run-guard.sh` — derived: reading
  lines 195-247 — for a `live-fire: <path> — result: ...` citation it derives
  `test_path = gates/test_<stem>.py` / `on-the-record/hooks/test_<slug>.py`
  and denies when that path is missing, before any pytest run. **This DOES
  depend on the suite's files existing**, contrary to the issue body's
  assumption. After this removal it fails closed on every pre-existing
  gate/hook's `live-fire:` citation regardless of truth — the guard's own
  documented degrade path, not a malfunction. New gates keep protection via
  `live-fire-test-guard.sh`, which only fires on newly `A`/`R`/`C`-staged
  files — derived: reading that script's line 175.

## What did not work

Ran out of session turn-budget (200-turn cap) mid-verification: the live
staged-fabricated-commit demonstration, the fixture-leak re-measurement, the
full per-file capability tables, and acting on the mid-flight scope
correction above were all cut short in favor of landing something committed.

## Upstream basis

docs/issue-2137 (record-is-the-regression-suite decision; sha not re-derived)
and issue #2525's own body plus issuecomment-5421024494 — canonical:
`gh issue view 2525` and the `gh api .../comments/5421024494` call above,
both read this session.

## Open findings

1. Mid-flight scope correction (issuecomment-5421024494) not executed — see
   section above. Highest-priority resolution path for next session.
2. Live fabricated-citation demonstration not run. Resolution path: next
   session stages one throwaway commit with a false `acceptance: ... —
   result: PASS` line and one with a false `live-fire: ... — result: allow`
   line, confirms both denied, discards the change.
3. `pytest.ini` not touched. derived: `grep -rlE pytest --include=*.sh
   --include=*.yml --include=*.ini --include=*.toml .` — result: hits were
   `pytest.ini`, both real-run guards, `gate-registration-guard.sh` (comment
   only), `tests/claim-scan-preflight.test.sh`. `pytest.ini` still governs
   `test/*.py`, `ledger/test_decisions.py`,
   `on-the-record/monitors/test_poll_heartbeat.py` (confirmed present, out
   of this issue's scope), so left in place. Resolution path: next session
   rewrites it to match only that remaining scope.
4. Fixture-repo leak re-measurement not run. Resolution path: next session
   runs a normal session and records new `tmp*` dir/inode counts here.
5. Full per-file capability tables not pasted in verbatim (only the OPEN GAP
   file lists above). Resolution path: next session re-runs the four
   read-only inventory agents or reconstructs from this session's transcript.

## Next steps

- Resolve open finding 1 first (operator's scope correction supersedes the
  rest of this record's guard-handling).
- Then close out findings 2-5.
- `loop_state` stays `in-progress`; `verdict: fail` until the above close.

skill-verdict: work-in-english — applied: invoked; record and all repo-bound artifacts written in English throughout, per this project's standing language policy.
skill-verdict: test-depth-audit — not-applicable: this issue deletes the suite rather than auditing test quality within it.
other mounted skills: not triggered.
