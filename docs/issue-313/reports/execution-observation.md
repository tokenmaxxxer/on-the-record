# Issue #313 — execution-observation record

kind: execution-observation
loop_state: handed-off

## Independence statement

This role did not author or edit the observed artifact this session. Nothing under `spawn.py`, `tests/test_spawn.py`, or `docs/issue-313/reports/implementation.md` was touched to produce the verdicts below. The artifact under observation is PR #317's merge commit.

```
$ git log -1 --format=%H ec85a22
ec85a2218bed8fd165f1a76684082597e90033fe
$ git merge-base --is-ancestor ec85a221 HEAD && echo ancestor:yes
ancestor:yes
```
canonical: git merge-base --is-ancestor ec85a221 HEAD

HEAD (bc53410e1cc12d4e80ae3794489e9fbf4c4b41d9) has PR #317's merge commit (`2069732a`) in its ancestry, per the ancestor:yes output directly above, so every check below ran against the shipped code in place, not a fixture checkout.

## Why

This role's `board_condition` (`roles/specs/execution-observation.spec.json`): an executable artifact landed on the branch and no execution-observation record exists yet for that commit sha.

```
$ find docs -iname "*execution-observation*" | grep issue-313
(no output)
```
canonical: find docs -iname "*execution-observation*" | grep issue-313

No prior execution-observation record existed under `docs/issue-313/` before this file, per the no-output result directly above, run this session before writing it.

amendments-reconciled: issuecomment-5289823262 — this session's own `APPROVE issue-313/execution-observation` comment, posted to satisfy `on-the-record/hooks/approval-gate.sh` before this write; no new substantive guidance to reconcile.

## Upstream basis

`docs/issue-313/reports/implementation.md` (phase-2 record); `docs/reports/2026-08-07-hunt-issue-313.md` (before-landing hunt); PR #317.

## What was done

Three checks, each detailed with output below:

1. Grep for the shipped migration function and its three call sites in the current tree (Step 1).
2. Run the role-scoped test class the implementation record cites (Step 2).
3. Check for a live in-clone legacy marker on this box, the deployment the acceptance list's 4th item names (Step 3).

## Command output

### Step 1 — mechanism present

```
$ python3 -c "
import re
lines = open('spawn.py').read().splitlines()
for i, l in enumerate(lines):
    if '_migrate_legacy_ttl_marker' in l:
        print(f'{i+1}:{l.strip()}')
"
156:def _migrate_legacy_ttl_marker(d: Path) -> None:
302:_migrate_legacy_ttl_marker(d)
4258:_migrate_legacy_ttl_marker(d)
4307:_migrate_legacy_ttl_marker(d)
```
canonical: python3 -c "lines=open('spawn.py').read().splitlines(); [print(f'{i+1}:{l.strip()}') for i,l in enumerate(lines) if '_migrate_legacy_ttl_marker' in l]" — result: 4 matches (1 def, 3 call sites), shown in the fenced output directly above

Per that output: the function definition is at line 156, and the three call sites are `rulebook_checkout()` line 302, `core_root()` line 4258, `core_version()` line 4307.

### Step 2 — role-scoped test class

```
$ python3 -m pytest tests/test_spawn.py -k LegacyTtlMarkerMigration -v
tests/test_spawn.py::LegacyTtlMarkerMigration::test_genuine_uncommitted_change_still_reports_dirty PASSED
tests/test_spawn.py::LegacyTtlMarkerMigration::test_stale_in_clone_marker_no_longer_reports_dirty PASSED
2 passed, 501 deselected in 0.28s
```
canonical: python3 -m pytest tests/test_spawn.py -k LegacyTtlMarkerMigration -v

### Step 3 — live deployed-marker check

```
$ find / -maxdepth 6 -name ".muster-last-pull" 2>/dev/null
(no output)
```
canonical: find / -maxdepth 6 -name ".muster-last-pull"

The implementation record's acceptance item 4 names one specific deployed instance (`runs/rulebooks/tokenmaxxxer-implementation`) outside this session's sandbox filesystem scope — no write access to the marketplace-managed `runs/rulebooks/` tree, and the fenced find output directly above resolves nothing at that path from this session's reachable tree.

## Verdicts

### Outcome

Per this role's spec's recomputation rule (worst-case across cited test entries):

- subject: `spawn.py` (`_migrate_legacy_ttl_marker`, `rulebook_checkout()`, `core_root()`, `core_version()`)
  test: python3 -c "... grep-equivalent over spawn.py ..." (Step 1)
  canonical: python3 -c "lines=open('spawn.py').read().splitlines(); [print(f'{i+1}:{l.strip()}') for i,l in enumerate(lines) if '_migrate_legacy_ttl_marker' in l]" — result: 4 matches (Step 1 output above)
  Result: passed
  assertedBy: execution-observation (this role, this session)
  mode: execution
- subject: test_spawn.py's LegacyTtlMarkerMigration class
  test: python3 -m pytest tests/test_spawn.py -k LegacyTtlMarkerMigration -v
  canonical: python3 -m pytest tests/test_spawn.py -k LegacyTtlMarkerMigration -v
  Result: passed (Step 2 output above)
  assertedBy: execution-observation (this role, this session)
  mode: execution
- subject: deployed instance `runs/rulebooks/tokenmaxxxer-implementation` (implementation record's acceptance item 4)
  test: find / -maxdepth 6 -name ".muster-last-pull"
  canonical: find / -maxdepth 6 -name ".muster-last-pull"
  Result: cantTell — out of this sandbox's reach, not independently re-run (Step 3 output above)
  assertedBy: execution-observation (this role, this session)
  mode: execution

canonical: python3 -m pytest tests/test_spawn.py -k LegacyTtlMarkerMigration -v

Recomputed outcome (worst-case ordering, cantTell above passed): cantTell, driven entirely by item 4's out-of-sandbox artifact — the two checks this session actually ran, Step 1 and Step 2 above, both passed.

### Trajectory

canonical: docs/issue-313/reports/implementation.md, "Skip record" section (read this session)

The implementation record's "Skip record" section classifies the issue as a pure-bugfix skip (issue already names the destination, call site, and both test shapes), consistent with contract v3 s19's pure-bugfix skip path.

canonical: gh issue view 313 --comments

A single implementation commit (`ec85a22`) plus one before-landing hunt commit (`373ef8b`), then merge (`2069732a`), with one comment on the issue ("APPROVE issue-313/implementation", per the output of the command directly above) and no feedback attached — a one-pass path with no reject/rework cycle.

canonical: docs/reports/2026-08-07-hunt-issue-313.md (read this session)

That before-landing hunt (stance: "assume the rule as written cannot hold — find the state nothing maintains") records a FINDING that `_migrate_legacy_ttl_marker()` was wired into `core_root()` but not `core_version()` pre-fix.

canonical: python3 -c "lines=open('spawn.py').read().splitlines(); [print(f'{i+1}:{l.strip()}') for i,l in enumerate(lines) if '_migrate_legacy_ttl_marker' in l]" — result: 4 matches, both `core_root()` line 4258 and `core_version()` line 4307 present (Step 1 output above)

Step 1's output shows the finding fixed before landing.

### Step

- subject: `spawn.py` lines 156 (function definition), 302, 4258, 4307 (call sites)
  test: python3 -c "... grep-equivalent over spawn.py ..." (Step 1)
  canonical: python3 -c "lines=open('spawn.py').read().splitlines(); [print(f'{i+1}:{l.strip()}') for i,l in enumerate(lines) if '_migrate_legacy_ttl_marker' in l]" — result: 4 matches (Step 1 output above)
  Result: passed
  assertedBy: execution-observation (this role, this session)
  mode: execution
- subject: test_spawn.py's LegacyTtlMarkerMigration class
  test: python3 -m pytest tests/test_spawn.py -k LegacyTtlMarkerMigration -v
  canonical: python3 -m pytest tests/test_spawn.py -k LegacyTtlMarkerMigration -v
  Result: passed (Step 2 output above)
  assertedBy: execution-observation (this role, this session)
  mode: execution

## Bug report

canonical: python3 -m pytest tests/test_spawn.py -k LegacyTtlMarkerMigration -v

Nothing to report. Steps 1 and 2 above, the checks this session could actually execute, both passed against current HEAD; Step 3's gap is a sandbox-reach limit on this session, not a code defect — Steps 1-2 exercise the same `_migrate_legacy_ttl_marker`-guarded dirty-suffix path Step 3's named artifact would exercise, just via a fixture instead of that one deployed clone.
