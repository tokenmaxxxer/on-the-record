---
issue: 2293
role: execution-observation
author: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2293/reports/implementation.md
    sha: 760390cceaa1b4aeac018460a08a39d1076f614b
subject: PR #2306 (branch issue-2293/implementation, untracked on this
  branch — not yet merged to main) — admission-time refusal of
  degenerate/issue-number-shaped tasks, --force-adhoc-task override,
  watchdog adhoc-visibility
test: independent re-execution of the refusal, override, and
  adhoc-visibility cases, plus the acceptance test suites, in a scratch
  git worktree of origin/issue-2293/implementation
  (760390cceaa1b4aeac018460a08a39d1076f614b)
result: passed
assertedBy: execution-observation (this session, own inputs — not copied
  from the PR record's Provenance section)
---

# issue-2293 — execution-observation record

## What was done

Build-now delivery (contract v3 s19a, `CORE_BUILD_NOW=1` set by the
spawner) — no phase-1 proposal round.

Independently re-ran, in a scratch `git worktree` of
`origin/issue-2293/implementation`
(`760390cceaa1b4aeac018460a08a39d1076f614b`, PR #2306, untracked on this
branch), the three case classes named in the assigned task, using inputs
of my own choosing (never the PR record's literal `"538"`/
`"PR 12 를 리뷰해라"` strings), per the
defect-verification-independence-from-upstream-verdicts skill.

canonical: `git diff main...HEAD -- pipeline.py spawn.py watchdog.py`
(run in the scratch worktree against this same commit) — read before any
execution was attempted, confirming the code under review is
`pipeline.py::_admission_check_degenerate_task` (regex
`^[#-]?\d+$`, new `ADMISSION_CHECKS` row), `spawn.py`'s
`--force-adhoc-task` argparse wiring
(`force_adhoc_task=a.force_adhoc_task` into `_spawn_one`, then into
`admission_gate({...})`), and `watchdog.py::diagnose_health()`'s single
`_diagnosis()` wrapper gaining an `adhoc_prefix` computed from
`entry.get("issue") is None`.

1. **Refusal case** — live CLI, no mocks, own inputs:
   acceptance: `python3 spawn.py implementation 42` — result:
```
[admission] degenerate-task: task '42' looks like an issue number; did you mean: spawn.py implementation "<task>" --issue 42
(pass --force-adhoc-task to spawn a genuinely numeric-task adhoc session)
[implementation] admission refused: missing precondition 'degenerate-task' (issue #2100) — no session created, no workspace left behind. This refusal is deterministic and non-retryable: publish the missing precondition, then dispatch again.
RC=1
```
   acceptance: `python3 spawn.py implementation "#7001"` — result:
```
[admission] degenerate-task: task '#7001' looks like an issue number; did you mean: spawn.py implementation "<task>" --issue 7001
(pass --force-adhoc-task to spawn a genuinely numeric-task adhoc session)
[implementation] admission refused: missing precondition 'degenerate-task' (issue #2100) — no session created, no workspace left behind. This refusal is deterministic and non-retryable: publish the missing precondition, then dispatch again.
RC=1
```
   acceptance: `python3 spawn.py implementation "-7001"` (the
   negative-shaped regression the PR's own before-landing hunt caught) —
   result:
```
[admission] degenerate-task: task '-7001' looks like an issue number; did you mean: spawn.py implementation "<task>" --issue 7001
(pass --force-adhoc-task to spawn a genuinely numeric-task adhoc session)
[implementation] admission refused: missing precondition 'degenerate-task' (issue #2100) — no session created, no workspace left behind. This refusal is deterministic and non-retryable: publish the missing precondition, then dispatch again.
RC=1
```
   acceptance: `cat runs/active.json` (same shell, after all three above)
   — result: `cat: runs/active.json: No such file or directory` — no
   roster entry left behind by any of the three refused spawns.

2. **Override case** — direct call of the reviewed predicate,
   `_admission_check_degenerate_task`, with an 8-row truth table of my
   own ctx values (not the PR record's rows). I did not run the full CLI
   with `--force-adhoc-task` because that admits the spawn and forks a
   real nested live session — the PR record's own Provenance section made
   the same choice (direct predicate call, not full CLI) for the same
   reason; the CLI-to-predicate wiring itself was confirmed separately by
   the `canonical:` diff read above, which needs no execution to verify
   (it is argument-plumbing, not branching logic).
   acceptance: `python3 -c "..."` (8-row table: bare numeric with/without
   `force_adhoc_task`, `#`-prefixed, negative-prefixed, free text
   containing digits, numeric task with `--issue` given, empty task,
   missing `task` key) — result:
```
bare numeric, no override: False
bare numeric, override True: True
hash-prefixed numeric, no override: False
negative numeric, no override: False
free text with digits, no override: True
numeric task but --issue given: True
empty task: True
missing task key entirely: True
```
   Every row matches the PR record's claimed contract (refuse
   bare/`#`/`-`-numeric only when `--issue` absent and no override; admit
   everything else).

3. **Adhoc-visibility case** — direct call of `watchdog.diagnose_health()`
   with `watchdog._sp` wired to the real `spawn` module (matching
   production wiring, where `spawn.py` injects itself into `watchdog._sp`
   after import), against three synthetic roster entries of my own
   construction.
   acceptance: `python3 -c "..."` (adhoc entry with a task string, adhoc
   entry with no task field, issue-scoped entry) — result:
```
adhoc w/ task -> 'ADHOC task="debug the flaky race in ci one more" — adhoc/implementation/99999: 최근 로그 성장, RUNNING'
adhoc w/o task -> 'ADHOC (no task recorded) — adhoc/implementation/88888: 최근 로그 성장, RUNNING'
issue-scoped -> 'issue-4242/implementation: 최근 로그 성장, RUNNING'
```
   The `ADHOC task="..." — ` / `ADHOC (no task recorded) — ` prefix
   appears only on the two `issue: None` entries and is byte-absent on
   the issue-scoped entry — matching the PR record's claim that the
   prefix reaches every diagnosis via the single `_diagnosis()` choke
   point.

4. **Acceptance test suites**, re-run serially (`-n0`) in the same
   worktree.
   acceptance: `python3 -m pytest tests/test_admission_checklist.py -n0 -q` — result:
```
30 passed in 4.42s
```
   acceptance: `python3 -m pytest tests/test_spawn_pipeline.py -n0 -q` — result:
```
86 passed in 33.58s
```
   acceptance: `python3 -m pytest tests/test_spawn_gate_wiring.py -n0 -q -k DiagnoseHealth` — result:
```
18 passed in 2.79s
```

5. **Pre-existing-failure claim, checked against both sides** (the PR
   record's `test_toolchain_cache_env_redirected_into_workspace` claim,
   in `tests/test_spawn_gate_wiring.py`, class `Ledger`).
   acceptance: `python3 -m pytest "tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace" -n0 -q` in the PR worktree — result:
```
FAILED tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace
1 failed in 36.06s
```
   acceptance: the same command, re-run in a second scratch `git worktree`
   of `main` (independent of the PR record's own repro) — result:
```
FAILED tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace
1 failed in 38.38s
```
   Same assertion failure on both sides — confirms the PR record's claim
   that this failure pre-exists on `main` and is untouched by this diff.

## Why

Per the assigned task and the mapped skill
(defect-verification-independence-from-upstream-verdicts): re-derive the
PR's Provenance claims from the code and my own inputs rather than
re-running its exact commands and trusting its exact outputs. Using
different numeric values, different task strings, and a from-scratch
truth table rules out the case where the record's specific chosen inputs
happened to hit a narrower code path than the general claim implies.

## Upstream basis

- `docs/issue-2293/reports/implementation.md` (PR #2306 record; untracked
  on this branch, read in the scratch worktree) — named the claims this
  record independently re-executed in `## What was done` items 1–5 above
  (see the `acceptance:`/`canonical:` evidence there).
  sha: 760390cceaa1b4aeac018460a08a39d1076f614b
- `pipeline.py`, `spawn.py`, `watchdog.py` — read directly via the
  `canonical:` diff cited under "What was done" before any execution was
  attempted.
  sha: 760390cceaa1b4aeac018460a08a39d1076f614b

## Open findings

None.
derived: the `acceptance:`/`canonical:` evidence in `## What was done`
items 1–5 above — every re-executed case (refusal, override,
adhoc-visibility, negative-number regression, the three test suites, and
the pre-existing-failure claim checked against both the PR branch and
`main`) reproduced independently, with inputs of my own choosing, and
none contradicted the PR record's claims. Resolution path: none needed —
no divergence found to resolve.

## Next steps

None — loop_state is terminal (`handed-off`).
