---
issue: 2288
role: execution-observation
author: execution-observation
loop_state: landed
upstream:
  - path: docs/issue-2288/reports/implementation.md
    sha: 10510bec7282217610465630d4c2e17b639b3b06
  - path: docs/issue-2241/proposals/2026-08-25-stage-5-observer-record-kind.md
    sha: 135712e8e4c56195aa0dedab6060db1610f3dc13
code_under_review:
  - gates/merge_gate.py
  - gates/spawn_on_pr.py
  - gates/test_merge_gate.py
  - tests/test_spawn_on_pr.py
  - test/test_merge_gate_record_kind.py
  - docs/handbooks/observer-verification.md
type: refactor
breaking: "None beyond the implementation record's own disclosure (internal
  rename PR_TRIGGERED_ROLES -> PR_TRIGGERED_RECORD_KINDS,
  applicable_roles() -> applicable_record_kinds(), _exempt_own_role() ->
  _exempt_own_record_kind()); independently re-verified below that no stale
  reference remains."
verdict: pass
assertedBy: execution-observation
---

# issue-2288 — execution-observation record

## What was done

Independently re-ran PR #2480's own acceptance evidence from a clean
checkout of this branch (which is cut from current `main`), rather than
reviewing the builder's transcript.

`docs/issue-2288/reports/implementation.md` (untracked in this working
tree — it lands on the not-yet-merged `origin/issue-2288/implementation`
branch, sha `10510bec7282217610465630d4c2e17b639b3b06`, and is not present
on `main` or on this `issue-2288/execution-observation` branch) is the
record under observation. canonical:

```
$ git cat-file -e origin/issue-2288/implementation:docs/issue-2288/reports/implementation.md && echo EXISTS-ON-REMOTE-BRANCH
EXISTS-ON-REMOTE-BRANCH
$ git cat-file -e HEAD:docs/issue-2288/reports/implementation.md
fatal: path 'docs/issue-2288/reports/implementation.md' does not exist in 'HEAD'
```

Because that record and its code are not locally present, PR #2480's diff
was fetched with `gh pr diff 2480` (saved to `/tmp/pr2480.diff`) and
applied to this branch's tree with `git apply`, tested (see Acceptance
below), then reverted with `git apply -R` before this commit — this
record's own commit carries no code changes, only this record file, per
the execution-observation role's write scope.

## Why

`origin/issue-2288/implementation` is cut from an older `main` and has
since diverged from unrelated merges (issue-2379 records, `pipeline.py`/
`spawn.py` churn) that are not part of PR #2480's change — diffing the two
branches directly pulled in ~580 unrelated deletions. Applying the PR's own
saved diff in isolation instead reproduces exactly PR #2480's change
against current `main`, independent of that drift.

## Upstream basis

`docs/issue-2288/reports/implementation.md` (untracked locally; on
`origin/issue-2288/implementation`, sha
`10510bec7282217610465630d4c2e17b639b3b06`) is the record under
observation. Its own upstream,
`docs/issue-2241/proposals/2026-08-25-stage-5-observer-record-kind.md`
(sha `135712e8e4c56195aa0dedab6060db1610f3dc13`, present on this branch),
was read directly and its `files:`, Constraints, and What-will-be-done
sections were checked against the diff itself, not against the
implementation record's paraphrase of them.

## Acceptance

acceptance: `git apply --check /tmp/pr2480.diff` (PR #2480's diff, saved
via `gh pr diff 2480`, applied against this branch's clean tree at
current `main`) — result:

```
$ git apply --check /tmp/pr2480.diff && echo "APPLIES CLEANLY"
APPLIES CLEANLY
```

acceptance: full test command from the implementation record, re-run
verbatim after applying the patch — result:

```
$ python3 -m pytest gates/test_merge_gate.py tests/test_spawn_on_pr.py \
    test/test_merge_gate_record_kind.py test/test_record_kind_field.py \
    gates/test_record_lint.py -q
........................................................................ [ 48%]
........................................................................ [ 97%]
...                                                                      [100%]
147 passed in 6.09s
```

acceptance: grep for stale references to the renamed symbols, re-run
myself — result:

```
$ grep -rln "PR_TRIGGERED_ROLES\|applicable_roles\b\|_exempt_own_role\b" --include="*.py" .
(no output, exit 1)
```

acceptance: live parity check script from the implementation record,
re-run verbatim against this repo's current board — result:

```
$ python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, 'gates')
import spawn, spawn_on_pr

root = Path('.').resolve()
b = spawn.board(root)
mismatches = []
for subject, subject_board in b.items():
    kinds = spawn_on_pr.PR_TRIGGERED_RECORD_KINDS
    old_missing = [r for r in kinds if r not in subject_board]
    subject_author = subject_board.get('implementation', {}).get('author')
    new_missing = spawn_on_pr.applicable_record_kinds(subject_board, subject_author=subject_author)
    if set(old_missing) != set(new_missing):
        mismatches.append((subject, old_missing, new_missing))
print(f'subjects checked: {len(b)}')
print(f'mismatches: {len(mismatches)}')
"
subjects checked: 592
mismatches: 0
```

derived: the implementation record (canonical:
`origin/issue-2288/implementation:docs/issue-2288/reports/implementation.md`
lines 322-326) reports 591 subjects for the same script; this re-run one
session later reports 592 — corpus growth between the two sessions, not a
discrepancy in the check itself. `mismatches: 0` held at both counts.

acceptance: the implementation record's "what did not work" section cites
`docs/issue-228/reports/execution-observation.md` as carrying an
off-vocabulary `kind:` value — read directly, on this branch, to confirm
rather than trusting the citation — result:

```
$ sed -n '1,8p' docs/issue-228/reports/execution-observation.md
role: execution-observation
issue: 228
phase: 2
kind: record
loop_state: landed
observed_role: implementation
observed_pr: 231
---
```

canonical: `docs/issue-228/reports/execution-observation.md` line 4 —
`kind: record` is present and off-vocabulary (populated, not absent),
exactly the case an absent-only fallback would mis-handle and the shipped
OR-of-both-signals fallback handles correctly. canonical:
`/tmp/pr2480.diff` (PR #2480's diff, `gates/spawn_on_pr.py` hunk defining
`applicable_record_kinds`, diff lines 480-514) shows the kind-field-or-
filename OR check that handles this case.

acceptance: diff read for all renamed-symbol call sites (not just the
implementation record's list of them) — result:

```
$ grep -n "applicable_record_kinds\|_exempt_own_record_kind\|PR_TRIGGERED_RECORD_KINDS" gates/merge_gate.py gates/spawn_on_pr.py
gates/merge_gate.py:160:    missing = spawn_on_pr.applicable_record_kinds(subject_board, subject_author=subject_author)
gates/merge_gate.py:164:        missing = _exempt_own_record_kind(missing, subject, own_branch)
gates/spawn_on_pr.py:39:PR_TRIGGERED_RECORD_KINDS = ("execution-observation", "conformance-review")
gates/spawn_on_pr.py:70:def applicable_record_kinds(...)
gates/spawn_on_pr.py:222:        missing = applicable_record_kinds(subject_board, subject_author=subject_author)
gates/spawn_on_pr.py:506:        missing = applicable_record_kinds(subject_board, subject_author=subject_author)
```

canonical: (patch applied at time of this command, per Acceptance above)
all three call sites (`gates/merge_gate.py:160`, `gates/spawn_on_pr.py:222`,
`gates/spawn_on_pr.py:506`) thread `subject_author` through to the
self-verification guard; none was missed.

## Open findings

None — every claim in `docs/issue-2288/reports/implementation.md`
(untracked locally; canonical:
`origin/issue-2288/implementation:docs/issue-2288/reports/implementation.md`)'s
Acceptance section reproduced under the independent re-execution above,
and the diff matches the stage-5 proposal's `files:`, Constraints, and
What-will-be-done sections. The two additional pre-existing test files it
touches (`gates/test_merge_gate.py`, `tests/test_spawn_on_pr.py`) are
disclosed in the implementation record as required-but-outside-`files:`;
canonical: `/tmp/pr2480.diff` diff hunks for those two files (diff lines
538-577 and 686-731) show only rename edits, no new behavior.

## What did not work

Nothing — every re-run reproduced the implementation record's claims (see
Acceptance above); no discrepancy required a retry or a fix.

## Next steps

None. `loop_state: landed` — this record is terminal; stage 6 (role enum
deletion) is out of scope for issue #2288 per the issue's own text.
