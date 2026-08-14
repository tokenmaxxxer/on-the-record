# Issue #459 — execution-observation record

kind: execution-observation
loop_state: handed-off

## Independence statement

This role did not author the observed artifact this session. The two hooks under review
(`on-the-record/hooks/pr-preflight.sh`, `on-the-record/hooks/spec-index-preflight.sh`) and their
test files landed on the `issue-459/implementation` branch.
canonical: `git log -1 --format=%H 9be65e8a` — commit 9be65e8ab0d6436725039b9f86b45ef30db3b651.
This session made no edit to either hook, their tests, or `docs/specs/enforcement-boundary.md`.

## What was done

Spawned per `gates/spawn_on_pr.py`'s PR-triggered board sweep (issue #1360). No
`execution-observation.md` sibling existed at session start.
canonical: `ls docs/issue-459/reports/` — output listed only `implementation.md` and
`implementation/`.

Ran the shipped, unmodified test files and the boundary-spec gate against the current working
tree.
canonical: `git log -1 --format=%H` — commit bc53410e (branch tip at session start).

```
$ python3 on-the-record/hooks/test_pr_preflight.py
... (16 cases)
All checks passed
$ echo $?
0

$ python3 on-the-record/hooks/test_spec_index_preflight.py
... (14 cases)
all tests passed
$ echo $?
0

$ python3 gates/test_boundary.py
...
AssertionError: acceptance_authoring_rule.py 가 docs/specs/enforcement-boundary.md 에 판정(verdict)이
기록된 행으로 없다 — 기록되지 않은 게이트가 조용히 존재한다(#441).
check_runner.py ... merge_gate.py ... spawn_on_pr.py ... tool_learnings_gate.py ...
tool_learnings_tracker.py ... (same message)
$ echo $?
1
```
canonical: the fenced transcript above, this session's own terminal output.

Executable-bit check on both hook files.
canonical: `ls -la on-the-record/hooks/pr-preflight.sh on-the-record/hooks/spec-index-preflight.sh`
— output: `-rwxrwxr-x` on both files.

Attribution check for the `test_boundary.py` failure against issue-459's two shipped files.
canonical: `grep -n "pr-preflight\|spec-index-preflight" docs/specs/enforcement-boundary.md` —
output: two matching lines, 89 and 91, each opening with `new (#459):` provenance prose. Neither
of the six module names the `test_boundary.py` transcript above flags (`acceptance_authoring_rule.py`,
`check_runner.py`, `merge_gate.py`, `spawn_on_pr.py`, `tool_learnings_gate.py`,
`tool_learnings_tracker.py`) appears in this grep's output.

## Why

`gates/spawn_on_pr.py`'s PR-triggered sweep spawns this role once a subject's implementation PR
merges and no execution-observation record exists yet for it.
canonical: `roles/specs/execution-observation.spec.json` `use_when.board_condition` field.

## Upstream basis

`docs/issue-459/reports/implementation.md` (this issue's own implementation record, its
`resolved_findings` frontmatter naming the executable-bit fix).
canonical: `git rev-parse 36039df0` — PR #461, landed as commit
36039df00063a9aa0b86cf10efbd92eebdd8f994.

`docs/issue-459/proposals/2026-08-08-pr-and-spec-index-preflight-hooks.md` (approved phase-1
proposal).

Approved via issue-level comment `APPROVE issue-459/execution-observation` by JiwonJung94
(approvers.md, single-account mode).

amendments-reconciled: issuecomment-5290026148 (`APPROVE issue-459/conformance-review`, posted
after this session started) — a different role's approval comment, no content bearing on this
record's execution-observation findings.

## Verdicts

### Outcome

Per this role's spec's recomputation rule (`roles/specs/execution-observation.spec.json`:
"overall verdict = the worst-case result across all cited test entries"), the two artifacts this
issue shipped both exit 0 on this session's own run.
canonical: python3 on-the-record/hooks/test_pr_preflight.py — result: PASS (exit 0, "All checks
passed", fenced transcript above)
canonical: python3 on-the-record/hooks/test_spec_index_preflight.py — result: PASS (exit 0, "all
tests passed", fenced transcript above)

The pre-existing, unrelated `test_boundary.py` non-zero exit (six modules from later issues, none
from PR #461, per the attribution check above) is out of this issue's scope and is not folded
into this issue's worst-case recomputation.

canonical: python3 on-the-record/hooks/test_pr_preflight.py && python3 on-the-record/hooks/test_spec_index_preflight.py — result: PASS (both exit 0, fenced transcript above)

Recomputed outcome for issue-459's two shipped artifacts, worst case across the two entries above:
**passed.**

### Trajectory

Sound. The implementation record's single `resolved_findings` entry names an executable-bit fix;
the current tree still carries that fix, per the `ls -la` check above (`-rwxrwxr-x` on both
files).

Both hooks' rows in `docs/specs/enforcement-boundary.md` are present with verdict prose, per the
`grep` cross-check above (lines 89, 91), matching the doc-placement ladder the implementation
record checked off.

### Step

- subject: `on-the-record/hooks/pr-preflight.sh`
  test: `python3 on-the-record/hooks/test_pr_preflight.py`, this session
  canonical: python3 on-the-record/hooks/test_pr_preflight.py — result: PASS (exit 0, fenced transcript above)
  result: passed
  assertedBy: execution-observation (this role, this session)

- subject: `on-the-record/hooks/spec-index-preflight.sh`
  test: `python3 on-the-record/hooks/test_spec_index_preflight.py`, this session
  canonical: python3 on-the-record/hooks/test_spec_index_preflight.py — result: PASS (exit 0, fenced transcript above)
  result: passed
  assertedBy: execution-observation (this role, this session)

- subject: `docs/specs/enforcement-boundary.md` rows for both new `.sh` files
  test: `python3 gates/test_boundary.py`, this session
  canonical: python3 gates/test_boundary.py — result: FAIL (exit 1, fenced transcript above)
  result: cantTell
  assertedBy: execution-observation (this role, this session)
  note: the run exits 1, but every flagged module postdates PR #461 and is outside this issue's
  write set (attribution check above). The two rows this issue is responsible for are present and
  verdict-bearing (lines 89, 91). Marked `cantTell` rather than a clean result because the
  command's own exit code is non-zero and this role's spec bars asserting a standalone summary
  independent of the cited command result.

## Open findings

None attributable to issue-459's shipped artifacts. The `test_boundary.py` non-zero exit is a
board-wide drift matter (unrecorded gates from later, unrelated PRs, per the attribution check
above) — out of this issue's scope; not filed here since this role does not open issues
(`produces`: "버그 리포트(레코드로; 이슈는 사용자가)").

## Next steps

canonical: python3 on-the-record/hooks/test_pr_preflight.py && python3 on-the-record/hooks/test_spec_index_preflight.py — result: PASS (both exit 0, fenced transcript above; executable bits confirmed via the `ls -la` check above)

None for issue-459. Both shipped hooks run correctly and the executable-bit fix the
implementation record names holds.
