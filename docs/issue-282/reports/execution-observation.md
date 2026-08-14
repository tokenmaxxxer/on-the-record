---
code_under_review: [spawn.py, tests/test_spawn.py]
loop_state: handed-off
---

# execution-observation record — issue-282

## Approval

canonical: gh issue view 282 --comments (read this session) —
https://github.com/tokenmaxxxer/on-the-record/issues/282#issuecomment-5289720747
Issue comment `APPROVE issue-282/execution-observation` posted by `JiwonJung94` (approvers.md-listed
account, single-account mode).

## Independence statement

canonical: gh pr view 283 --json mergeCommit,files (read this session) — merge commit
`cefd9b480693aedb07f9bbd021aa7cae724e793c`; files touched: `spawn.py`, `test_spawn.py`,
`tests/fixtures/rulebooks/tokenmaxxxer-core/.claude-plugin/marketplace.json`.
This role did not author the observed change. `spawn.py`'s `core_plugin_dirs()` (`spawn.py:4312`)
and `tests/test_spawn.py`'s two pinning tests were authored by the implementation role and landed
via PR #283, per the citation directly above.

This record independently re-runs the shipped code, live, from a fresh session with no edits to
the observed files this session.

## What was done

Ran the two tests PR #283 added, live, against this branch's current `HEAD`
(`bc53410e1cc12d4e80ae3794489e9fbf4c4b41d9`, `git rev-parse HEAD`, read this session):

canonical: python3 -m pytest tests/test_spawn.py -k "core_plugin_dirs" -v — result: 2 passed
```
$ python3 -m pytest tests/test_spawn.py -k "core_plugin_dirs" -v
tests/test_spawn.py::SpawnCmd::test_core_plugin_dirs_halts_on_missing_plugin_dir PASSED [ 50%]
tests/test_spawn.py::SpawnCmd::test_core_plugin_dirs_pins_five_plugin_set PASSED [100%]
2 passed, 501 deselected in 0.23s
```
canonical: python3 -m pytest tests/test_spawn.py -k "core_plugin_dirs" -v — result: 2 passed
(transcript directly above).
Both pinning tests pass at current `HEAD`, per the citation directly above.

Then, independent of the test suite's own fixtures, called the shipped `core_plugin_dirs()`
directly against a real `tokenmaxxxer-core` checkout on this host
(`/home/jwjung/tokenmaxxxer/tokenmaxxxer-core`) by monkeypatching only `core_root()` to point at
it:

canonical: python3 -c "import spawn; spawn.core_root = lambda: Path(...); core_plugin_dirs()" —
result: all five plugin names returned
```
$ python3 -c "
import spawn
from pathlib import Path
spawn.core_root = lambda: Path('/home/jwjung/tokenmaxxxer/tokenmaxxxer-core')
dirs = spawn.core_plugin_dirs()
print(sorted(d.name for d in dirs))
"
['core', 'freelunch', 'scout', 'terse', 'warrant']
```
canonical: python3 -c "...core_plugin_dirs()..." (transcript directly above) — result: all five
plugin names returned.
All five resolved, `warrant` included, per the citation directly above — the exact plugin
issue #282 reported as never attaching under the old hardcoded 4-name tuple. The
`marketplace.json` at that checkout was also read directly this session and declares exactly
those five plugin names.

## Why

canonical: gh issue view 282 (issue body, "Fix direction" / "Acceptance" sections), read this
session.
Issue #282 asks for a record confirming the code that landed on `issue-282/implementation`
(PR #283) behaves as claimed once merged, per the citation directly above, since
`spawn_on_pr.py` auto-spawns this role on PR landing and no execution-observation record existed
yet for this commit sha.

## Upstream basis

canonical: gh pr view 283 --json mergeCommit,mergedAt, read this session.
PR #283, merged, merge commit `cefd9b480693aedb07f9bbd021aa7cae724e793c`, per the citation
directly above.

`docs/issue-282/reports/implementation.md` (its own prior claims re-verified live above rather
than taken on trust); `docs/issue-282/proposals/plan.md`.

## Verdicts

### Outcome

canonical: python3 -m pytest tests/test_spawn.py -k "core_plugin_dirs" -v — result: 2 passed
(transcript under "What was done").
canonical: python3 -c "...core_plugin_dirs()..." against the real tokenmaxxxer-core checkout —
result: all five plugins returned (transcript under "What was done").
Per the role spec's recomputation rule (worst-case across all cited test entries), and the two
citations directly above, the recomputed outcome is **passed**.

- subject: `spawn.py:4312` (`core_plugin_dirs()`)
  test: `test_spawn.py` test `test_core_plugin_dirs_pins_five_plugin_set` (`tests/test_spawn.py`)
  canonical: python3 -m pytest tests/test_spawn.py -k "core_plugin_dirs" -v — result: 2 passed
  (transcript under "What was done").
  result: passed
- subject: `spawn.py:4312` (`core_plugin_dirs()`, missing-plugin-dir branch)
  test: `test_spawn.py` test `test_core_plugin_dirs_halts_on_missing_plugin_dir`
  (`tests/test_spawn.py`)
  canonical: python3 -m pytest tests/test_spawn.py -k "core_plugin_dirs" -v — result: 2 passed
  (transcript under "What was done").
  result: passed
- subject: `spawn.py:4312` (`core_plugin_dirs()`)
  test: live call against `/home/jwjung/tokenmaxxxer/tokenmaxxxer-core`'s real five-plugin
  `marketplace.json`
  canonical: python3 -c "...core_plugin_dirs()..." — result: all five plugins returned
  (transcript under "What was done").
  result: passed

### Trajectory

canonical: gh pr view 283 --json reviews,mergedAt, read this session — PR #283 shows an approval
via issue comment `APPROVE issue-282/implementation` and a merge timestamp preceding this record's
session.
canonical: gh pr view 283 --json reviews,mergedAt, read this session (repeated for proximity).
Sound: PR #283 was approved via issue comment `APPROVE issue-282/implementation` (single-account
mode) and merged before this record was spawned.

### Step

canonical: python3 -m pytest tests/test_spawn.py -k "core_plugin_dirs" -v — result: 2 passed
(transcript under "What was done").
Zero deficiencies found this round, per the citation directly above: the shipped code reads the
marketplace, halts loudly and names the plugin when a declared plugin's directory is missing
(second test, cited above).

canonical: python3 -c "...core_plugin_dirs()..." against the real tokenmaxxxer-core checkout —
result: all five plugins returned (transcript under "What was done").
It also resolves all five plugins including `warrant` against a real checkout, per the citation
directly above.

## assertedBy

execution-observation role, this session, `2026-08-14`.
