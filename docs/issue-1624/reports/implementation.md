---
code_under_review:
  - docs/issue-711/reports/implementation.md
  - docs/issue-476/reports/implementation.md
  - docs/issue-1461/reports/implementation.md
type: fix
breaking: false
verdict: blocked
loop_state: commit-unreachable
---

## What was done

canonical: docs/issue-711/reports/implementation.md (working tree, HEAD 2a6d5638)

Attempted the fix `#1624` describes as an `Edit` against
`docs/issue-711/reports/implementation.md`. The edit was refused at
tool-use time by `core/hooks/board-gate.sh`'s R4 branch check:

```
board-gate: writing docs/issue-711/ requires branch issue-711/implementation
(current: issue-1624/implementation). Every role output reaches main only
through a PR the human merges — never a direct write from another branch.
(contract v3 s10)
```

canonical: core/hooks/board-gate.sh (working tree, R4 block)

```
for parts in issue_hits:
    issue_dir = parts[0]
    expected = "%s/%s" % (issue_dir, role)
    if branch != expected:
        deny("writing docs/%s/ requires branch %s (current: %s) ..."
             % (issue_dir, expected, branch))
```

R4 keys off the write target's own issue number, not the writing session's
subject issue; it carries no exception for a subject issue whose body names
the foreign records it means to fix.

derived: `python3 gates/precision_measure.py sample . --seed 1 --out /tmp/sample.json`

```
wrote 9 sample items (population 9) to /tmp/sample.json
{'path': 'docs/issue-1461/reports/implementation.md', 'excerpt': 'on-the-record/hooks/test_pr_base_guard.py'}
{'path': 'docs/issue-476/reports/implementation.md', 'excerpt': 'test/claim-scan-preflight.test.sh'}
{'path': 'docs/issue-476/reports/implementation.md', 'excerpt': 'gates/test_gates.py'}
{'path': 'docs/issue-711/reports/implementation.md', 'excerpt': 'test/test_bootstrap_timing.py'}
```

Those four sample items are the same 4 citations `#1624` names: two under
issue-476 (the claim-scan preflight test and the test_gates module, actual
`tests/` prefix in both cases), one under issue-1461 (actual file suffixed
`_hook.py`), one under issue-711 (actual `tests/` prefix). No new or
different rule-330 findings turned up in this sample.

## Why

canonical: gh pr view 1622 --json body (`## Out of scope / deviation` section, this session)

```
Acceptance bullet 3 (fixing the 4 genuine test/->tests/ citation breaks in
their own issues' records) could not be done from this branch —
core/hooks/board-gate.sh refuses writes touching another issue's
docs/issue-<n>/ tree. Filed as a deviation in the record for those issues'
own roles.
```

`#1624`'s premise was that being the subject of its own issue would let this
branch write those foreign trees; the reproduction above shows the gate
denies on branch-vs-target-tree alone, with no such exception, so this
session hit the identical blocker PR #1622 already recorded.

## Upstream

canonical: docs/issue-1624 (this issue, `gh issue view 1624`) and PR #1622 (merged as 2a6d5638)

Based on `#1624`'s own body and the matching deviation note quoted above
from PR #1622.

## What did not work

- Attempted `Edit` of `docs/issue-711/reports/implementation.md` from branch
  `issue-1624/implementation`. Expected: `#1624`'s stated re-scope would let
  this branch write `docs/issue-711/`. Actual: `board-gate.sh` R4 denied it.

## Open findings

None raised beyond the blocker documented above. The 4 citations remain
broken. Delivering the actual text fix requires either a session running on
each target issue's own branch (`issue-711/implementation`,
`issue-476/implementation`, `issue-1461/implementation`) or a change to
`board-gate.sh` letting a record-hygiene-scoped session cross issue trees —
the latter is a design decision outside this issue's write set, not a
mechanical fix.

resolution path: file the board-gate cross-tree question as its own issue,
or dispatch three role sessions on their respective issue branches to apply
the corrections the sample above identifies: a `test/` to `tests/` prefix
fix in two records, and a `_hook.py` suffix fix in the third.

next steps: none for this session — the blocker is structural, not a
scoping choice this session can resolve by continuing.

## Rationale for deviations

The approved scope (fix the 4 citations in place) could not be executed at
all — not partially, not with a substitute approach — because the write
target is outside what this branch's board-gate identity can ever write,
regardless of the issue body's framing. No code or foreign-record change was
made; this record and the deviation log are the full output of this
session.
