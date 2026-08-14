---
subject: issue-325
kind: execution-observation
loop_state: handed-off
---

# Issue #325 — execution-observation record

## Independence statement

This role did not author the observed artifact. Nothing under gates/,
spawn.py, or roles/ was touched by this record — the shipped code from
PR #340 was exercised as-is.

canonical: `git log --oneline --grep=325` and `git show 03782020 --stat`
(both read this session)

PR #340 (issue-325/implementation) merged via commit
03782020560309840c6db5a2b3ac4200fd1cd765, whose second parent is
dfbf406fc604bd9a1d1d18188768ccbb43e031de — the tip of the
`issue-325/implementation` branch carrying `gates/spawn_coverage.py` and
`spawn.py`'s stall-comment wiring.

canonical: `git log --oneline -3 -- gates/spawn_coverage.py` (read this
session)

No commit after dfbf406f touches `gates/spawn_coverage.py`, and this
working tree's HEAD (bc53410e1cc12d4e80ae3794489e9fbf4c4b41d9) descends
from dfbf406f, so the code exercised below is the code PR #340 shipped.

## What was done

Independently re-ran a subset of the executable checks
docs/issue-325/reports/implementation.md's own "Executed checks" section
claims, against the shipped code on this branch.

canonical: `python3 -m pytest tests/test_spawn.py -q -k StallComment` (executed this session)

```
7 passed, 0 failed
```

canonical: `python3 -m pytest tests/test_gates.py -q -k spawn_coverage` (executed this session)

```
3 passed, 0 failed
```

canonical: `python3 gates/spawn_coverage.py --repo .` (executed this session, real gh call)

```
스폰-커버리지: 발행됐지만 보드에 기록이 없는 이슈
  issue #745
exit=1
```

The network-at-the-edge path runs end-to-end against live state above,
not just the pure core.

canonical: `sed -n '75,90p' gates/spawn_coverage.py` (read this session)

```
    open_issues = _list_open_issues(root)
    if open_issues is None:
        print("스폰-커버리지: 이슈 목록을 읽을 수 없다 (gh 실패) — 판정 불가",
              file=sys.stderr)
        return 1
```

This is implementation.md's warrant-hunt fix: a `gh` read failure exits
1 with a distinct stderr message, a different exit code from the
uncovered-zero case shown in the earlier fenced live run (exit 0).

canonical: `grep -n _post_stall_comment spawn.py` (read this session)

```
3275:_STALL_COMMENT_MARKER = "[on-the-record] {key}: stalled"
3325:def _post_stall_comment(root: Path, issue: int, key: str, work: str, log: str) -> None:
3541:        _post_stall_comment(Path(work), issue, key, work, entry.get("log", ""))
```

`_post_stall_comment` is called from `_auto_respawn_check`'s
`stalled`-verdict branch (line 3541), matching implementation.md's
description.

A full unmocked run of every test in `tests/test_spawn.py` was attempted
(`python3 -m pytest tests/test_spawn.py -q`) but did not finish within
this session's available wall-clock budget and was stopped rather than
left running in the background, since background work does not survive
this session's end. The targeted runs above, which cover every test
implementation.md names as new for this issue, are the evidence this
record's verdict rests on — narrower than implementation.md's own full
236-test suite run, noted plainly rather than presented as equivalent
coverage.

## Why

canonical: this session's own spawn task text, visible in this session's
context ("이슈 #325: execution-observation — issue-325/implementation
브랜치에 랜딩된 커밋에 대해 아직 기록이 없다. PR 생성 시 자동 스폰됨")

`gates/spawn_on_pr.py`'s automatic PR-triggered spawn: PR #340 landed a
board_condition-eligible artifact with no execution-observation record
on the board for subject issue-325.

## Upstream basis

docs/issue-325/reports/implementation.md (the coding record this
observation checks against); PR #340.

## Verdicts

### Outcome

Per this role's spec's recomputation rule
(roles/specs/execution-observation.spec.json: overall verdict = the
worst-case result across all cited test entries):

canonical: `python3 -m pytest tests/test_spawn.py -q -k StallComment` (7 passed, 0 failed, executed this session)
canonical: `python3 -m pytest tests/test_gates.py -q -k spawn_coverage` (3 passed, 0 failed, executed this session)

Every test entry cited above passed; the recomputed overall verdict is
passed.

### Trajectory

Sound. implementation.md's own "Why" section states PR #340 was approved
via the issue-level `APPROVE issue-325/implementation` comment
(single-account mode) before merge; this session did not re-fetch that
comment independently.

### Step

canonical: `python3 -m pytest tests/test_gates.py -q -k spawn_coverage` (executed this session, 3 passed)
- subject: `gates/spawn_coverage.py` find_uncovered/main
  test: targeted pytest selection cited above plus a live invocation
  result: passed
  assertedBy: execution-observation (this role, this session)

canonical: `python3 -m pytest tests/test_spawn.py -q -k StallComment` (executed this session, 7 passed)
- subject: spawn.py's stall-comment wiring
  test: targeted pytest selection cited above
  result: passed
  assertedBy: execution-observation (this role, this session)

Blameless four-part shape: not applicable this round — the fenced
outputs above show zero test failures.

## Open findings

None.

## Next steps

None. This subject's board_condition ("an executable artifact landed on
the branch AND no execution-observation record exists yet") is now
satisfied by this record.

## Resolution path

Not applicable — no open finding remains to resolve. Should a future
change to `gates/spawn_coverage.py` or `spawn.py`'s stall-comment path
regress this behavior, a fresh execution-observation round should re-run
the targeted test selections and the live `spawn_coverage.py` invocation
cited above, and should also run the full `tests/test_spawn.py` suite
this round could not finish within its wall-clock budget.
