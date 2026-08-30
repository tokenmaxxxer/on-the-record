---
issue: 2326
role: adversarial-review-0b66ea80
author: adversarial-review-0b66ea80
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
loop_state: landed
upstream:
  - path: docs/issue-2326/reports/silent-failure-audit-316cb9e0.md
    sha: 1da2433e27251540d2203e3c2a37b79a73da92ab
---

# issue-2326 — adversarial-review-0b66ea80 record

skill-verdict: adversarial-review — applied: invoked; this record's evaluator role is a fresh session with no stake in defending PR #2879 — every claim in the PR's own record was re-derived independently (own fixtures, own worktrees, own stress parameters) rather than accepted, per Step 2's evidence-requirement (every finding below cites a command/output or file:line).

## What was done

Independent verification of PR #2879 (branch `issue-2326/silent-failure-audit-316cb9e0`, tip `1da2433e27251540d2203e3c2a37b79a73da92ab`), round 5 on issue #2326, which removed the advisory `flock` lock round 4 added.

canonical: `1da2433e27251540d2203e3c2a37b79a73da92ab:docs/issue-2326/reports/silent-failure-audit-316cb9e0.md` — PR #2879's own record, read via `git show`.

Four independent verification units ran in parallel, each in its own git worktree off `origin/issue-2326/silent-failure-audit-316cb9e0`, none reusing the round's own fixtures:

1. Silent-failure reopening stress test — rebuilt the round's own 8-way `spawn.py` concurrency scenario from scratch and pushed it past the round's own validated range.
2. Lock-removal completeness audit — diffed round 5 against round 4's own branch tip in isolation.
3. Overhead re-measurement — built fixtures sharing no files/tests with round 5's `mod1-4`/`spawn.py` fixtures.
4. Single-shape measurement-habit audit — read the 517-line hook end to end and live-tested three untested concurrency/usage shapes.

derived: `git worktree add /tmp/unitA-wt origin/issue-2326/silent-failure-audit-316cb9e0` (and unitB/unitC/unitD analogously) — each unit's full command transcript is in this session's task-notification history for agent IDs a0c7e03e/a92d17ec/a15df397/abe01fb2.

## Why

Round 4 added the lock to reduce budget-exhaustion *frequency*; round 5's claim is that the durable-evidence mechanism, not the lock, is what makes a budget-exceeded run reportable, so removing the lock should only make exhaustion more frequent, never silent. That is a falsifiable, narrow claim, tested directly by adversarial stress rather than accepted from the round's own 3-trial measurement. Independently-constructed fixtures were used for the overhead re-derivation because the round's own overhead fix was itself validated only against PR #2878's exact fixture — reusing it again would repeat the identical-shape blind spot that let the original regression through undetected for an entire round.

## Upstream basis

- `1da2433e27251540d2203e3c2a37b79a73da92ab:docs/issue-2326/reports/silent-failure-audit-316cb9e0.md` — PR #2879's own record, the subject of this verification.
- `docs/issue-2326/reports/adversarial-review-813a3aa7.md` (present on this branch, HEAD `d514d2c7`) — PR #2878's verification record for round 4; read for the 8-way fixture's prose description (its script was never committed, only run from `/tmp`) and for round 4's own outcome-distribution baseline, cited but not reused as evidence for this round's own findings.
- `efd3d777bdbe1f0467efd022dee6852910f58213:on-the-record/hooks/lint-test-on-edit.sh` — round 4's branch tip (PR #2875), the pre-lock-removal code used as the WITH-lock cross-check baseline.

## Open findings

### 1. Central claim CONFIRMED — no silent pass on budget exhaustion

derived: `python3 /tmp/repro_8way.py /tmp/otr-repro-src/repo 8 15` × 5 trials, then `... 8 0.5`, `... 8 0.05`, `... 8 0`, `... 16 15`, `... 24 15`, `... 32 15`, all against `1da2433e27251540d2203e3c2a37b79a73da92ab:on-the-record/hooks/lint-test-on-edit.sh`.

```
=== TRIAL 1 === (8-way, budget=15s)
run 0: rc=0 dur=9.16s  shape=FULL-FAILURE-REPORT
run 1: rc=0 dur=15.04s shape=PARTIAL-RECOVERED
... (8 runs)
$ python3 /tmp/repro_8way.py /tmp/otr-repro-src/repo 32 15
run 0: rc=0 dur=15.13s shape=PARTIAL-RECOVERED   [runs 1-31 all PARTIAL-RECOVERED, dur 15.10-15.18s]
```

Tally across 5×8-way + 16-way + 24-way + 32-way = 136 total invocations, budgets 0s-15s: 0 EMPTY-OR-SILENT, 0 UNRECOGNIZED. Every budget-exceeded invocation reported either a full failure report or an explicit `PARTIAL-RECOVERED`/`EXPLICIT-INCOMPLETE` marker. Contrast case (genuine clean pass, no budget pressure) verified separately:

```
$ echo '{"tool_input":{"file_path":".../pipeline.py"},"cwd":"..."}' | OTR_LINT_TEST_BUDGET_S=60 bash <round-5-tip-hook> post
[rc=0 -- empty stdout above is the LEGITIMATE clean-pass state, distinct from a budget-exceeded run]
```

Budget-exhaustion frequency rose as expected without the lock (~35% at 8-way to ~100% at 24/32-way) — this is the allowed cost, not a failure. No resolution needed.

### 2. Overhead invariant CONFIRMED on independently-constructed fixtures

derived: 5-module disjoint fixture (`ledger_amortizer`/`webhook_signer`/`geo_bucketer`/`feature_flagger`/`audit_redactor`, none shared with round 5's own `mod1-4`), 3 runs each against round 5's tip and against `efd3d777bdbe1f0467efd022dee6852910f58213:on-the-record/hooks/lint-test-on-edit.sh` (round 4, WITH lock):

```
$ bash /tmp/run_disjointB.sh /tmp/unitC-wt/on-the-record/hooks/lint-test-on-edit.sh 3
=== run 1 TOTAL=2.644181360s ===
=== run 2 TOTAL=2.675497892s ===
=== run 3 TOTAL=2.725153491s ===
$ bash /tmp/run_disjointB.sh /tmp/hooks_with_lock/lint-test-on-edit.sh 3
=== run 1 TOTAL=10.821495503s ===
=== run 2 TOTAL=11.733564895s ===
=== run 3 TOTAL=12.088834434s ===
```

~4.1-4.6x overhead reproduced on a fixture PR #2878/#2879 never touched.

derived: same-file 6-way overlap fixture (`billing_core.py`, not `spawn.py`):

```
$ bash /tmp/run_overlapB.sh <no-lock hook> 3
TALLY (each of 3 runs): full-report=0/6 incomplete=0/6 recovered=0/6 empty-clean-pass=6/6, TOTAL≈6.6s
$ bash /tmp/run_overlapB.sh <with-lock hook, efd3d777> 3
TALLY (each of 3 runs): full-report=0/6 incomplete=4/6 recovered=0/6 empty-clean-pass=2/6, TOTAL≈15.1s
```

No resolution needed.

### 3. PR #2879's "no stale lock path left behind" is not literally true, though the removal itself is clean

derived:

```
$ git show efd3d777bdbe1f0467efd022dee6852910f58213:on-the-record/hooks/lint-test-on-edit.sh | grep -n "_acquire_repo_lock\|_release_repo_lock" -A3
lock_dir = os.path.join(tempfile.gettempdir(), "otr-lint-test-on-edit-locks")
digest = hashlib.sha1(root_dir.encode("utf-8", "replace")).hexdigest()[:16]
lock_path = os.path.join(lock_dir, digest + ".lock")
fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
# _release_repo_lock body: fcntl.flock(fd, LOCK_UN); os.close(fd) -- no unlink/os.remove anywhere on lock_dir/lock_path
$ git grep -n "_acquire_repo_lock\|_release_repo_lock\|otr-lint-test-on-edit-locks" origin/issue-2326/silent-failure-audit-316cb9e0
docs/issue-2326/reports/adversarial-review-813a3aa7.md (prose only)
docs/issue-2326/reports/silent-failure-audit-316cb9e0.md (prose only)
```

The lock file lived at a deterministic path under the system temp dir (`$TMPDIR/otr-lint-test-on-edit-locks/<sha1(repo_root)[:16]>.lock`, not the repo root), created but never deleted by round 4's code. Round 5's removal is clean (zero remaining code/test references at `1da2433e27251540d2203e3c2a37b79a73da92ab`), but any checkout that ran round 4's hook even once left an inert 0-byte file at that path with nothing in round 5 (or any prior round) cleaning it up. Severity: low — inert, tmp-dir-scoped, subject to OS tmp-reaping, not a correctness risk. Resolution path: optional follow-up cleanup; not blocking for this PR since it's a pre-existing round-4 artifact, not something round 5 newly creates.

### 4. Disjoint-concurrency shape still has no committed CI regression test

derived:

```
$ git grep -n "disjoint\|different file" origin/issue-2326/silent-failure-audit-316cb9e0 -- tests/test_spawn_gate_wiring.py
(no matches)
$ git show origin/issue-2326/silent-failure-audit-316cb9e0:tests/test_spawn_gate_wiring.py | sed -n '626,691p'
class ConcurrentInvocationsNeverReportSilently(...):
    # 6 threads, all editing the SAME file "shared_thing.py" -- not distinct files
```

The disjoint-files shape (the one that hid round 4's regression) is verified in this round and in #2878 only by ad hoc, uncommitted `/tmp` scripts. Resolution path: follow-up issue to commit a disjoint-edit concurrency test (mirroring `ConcurrentInvocationsNeverReportSilently` but across distinct files) so a future round reintroducing per-repo serialization is caught automatically rather than by manual review.

### 5. `_find_impacted`'s scan runs outside the hook's own budget accounting

canonical: `1da2433e27251540d2203e3c2a37b79a73da92ab:on-the-record/hooks/lint-test-on-edit.sh:413-432` (`_find_impacted`, executes before the first `_run()` call) and `:296-325` (`_run`'s `_remaining() <= 0` check — the only budget check in the file). Currently 1.4ms on this repo's 47-file test tree (measured live by the auditing worker), but structurally unbounded — the same unbounded-fan-in shape the hook's design otherwise guards against for the test-run portion. Not introduced by round 5:

```
$ git diff --stat 967e8c19..1da2433e
 on-the-record/hooks/lint-test-on-edit.sh                  | 57 +-------------
 docs/issue-2326/reports/silent-failure-audit-316cb9e0.md  | ...
```

(only the lock-removal hunk and the round's own report changed; `_find_impacted` is untouched). Failure mode if it ever ran long would still be non-silent. Resolution path: follow-up issue to time-box the scan itself, out of scope for this round.

### 6. Budget near-miss produces reproducible false "verdict INCOMPLETE" for tests that would have passed

derived:

```
$ OTR_LINT_TEST_BUDGET_S=1.15 <round-5-tip hook against a 1.0s-sleep passing test> × 8 trials
trial 0: dt=1.193 rc=0 stdout='...budget exceeded (1.15s) -- verdict INCOMPLETE, NOT ve...'
trial 1: dt=1.217 ... (identical outcome, 8/8 trials)
```

Not a crash or flakiness bug (stable, consistent, never silent), but previously undocumented: the effective usable budget is `budget_s` minus a real ~150-200ms fixed per-invocation overhead, not `budget_s` itself. Resolution path: document in the hook's header comment or widen the default budget slightly; not blocking, no correctness impact.

### 7. Four standing invariants, independently re-derived, all passing

derived: role-axis — prior gating pattern `\brole\b` cannot match "roles" (word-boundary fails after trailing `s`):

```
$ git diff 967e8c19..1da2433e -- on-the-record/hooks/lint-test-on-edit.sh | grep -nE "^[+-].*\brole(s)?\b"; echo "grep_exit=$?"
grep_exit=1
$ git show 1da2433e:on-the-record/hooks/lint-test-on-edit.sh | grep -nE "\brole(s)?\b"
139:# No role-axis: this hook keys nothing on a role/skill identity ...
143:# gates, per the retired-role-axis decision
144:# (docs/decisions/2026-08-25-retire-role-axis-staging.md).
```

derived: no new bug — `pytest . -q` from repo root, both trees:

```
$ (cd origin/main-worktree && python3 -m pytest . -q --collect-only 2>&1 | tail -1)
614 tests collected in 0.80s
$ (cd round5-tip-worktree && python3 -m pytest . -q --collect-only 2>&1 | tail -1)
641 tests collected in 1.03s
$ diff <(sort main_failed_root.txt) <(sort branch_failed_root.txt) && echo "IDENTICAL SETS"
IDENTICAL SETS
```

Both FAILED node-id sets are 16 items, byte-identical, including `harness/fixture-operator-experience/test_flow.py::test_first_contact_fires_once_per_workspace` — a failure that a `test/ tests/`-scoped comparison (prior rounds' scope) would have missed entirely.

Finding (c), overhead: see finding 2 above (same evidence, not repeated).

derived: monitor/watch —

```
$ python3 -m pytest test/ tests/ -q -k "monitor or watch"   # both trees
15 passed in ~1.05s   (identical on origin/main and round-5 tip)
$ python3 -m pytest . -q -k "monitor or watch"               # repo-root scope, both trees
45 passed in ~3.7s    (identical on origin/main and round-5 tip)
$ diff main_monitor_watch_verbose.txt branch_monitor_watch_verbose.txt && echo IDENTICAL
IDENTICAL
$ git diff efd3d777bdbe1f0467efd022dee6852910f58213..1da2433e -- watchdog.py on-the-record/monitors/
(empty output)
```

`watchdog.py`/`on-the-record/monitors/` are byte-identical between round 4 and round 5 (round 5's diff touches only the hook file and its own report), so there is no code path by which this round could have made monitor/watch quieter. No resolution needed for (a)-(d).

## Next steps

None required for this PR to land — findings 3, 4, 5, and 6 are non-blocking follow-up recommendations, not defects introduced by round 5's change. `loop_state: landed`.
