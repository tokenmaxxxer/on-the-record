---
code_under_review:
  - spawn.py
  - gates/test_clean_reconcile_safety.py
type: fix
breaking: false
# canonical: python3 -m pytest gates/test_clean_reconcile_safety.py -q — result: 4 passed (executed live this session, fenced output below)
verdict: pass
loop_state: landed
---

Subject: issue-1124

## What was done

canonical: docs/issue-1124/proposals/clean-reconcile-safety.md (read
this session, status: approved) — approved via the issue-level comment
`APPROVE issue-1124/implementation` (gh issue view 1124 --comments,
read this session); commit 58d2bfc (git log --oneline -3, read this
session) landed the code on this branch.

Implemented the approved phase-1 proposal's write set
(`spawn.py`, `gates/test_clean_reconcile_safety.py`) one-for-one:

- Added `LANDED_OUTCOMES = {"progressed", "progressed-dirty-tree"}`
  next to `classify()` (spawn.py).
- Added `_ledger_log_outcomes()` (spawn.py), reading
  `runs/ledger.jsonl` into `{log path: last outcome}`; returns `{}`
  when the file is absent.
- Extracted the `clean` role's inline `main()` branch into
  `roster_clean(wb: Path, issue: int | None) -> int` (spawn.py). Its
  sibling-file loop now checks each sibling against
  `_ledger_log_outcomes()`: a sibling matching a ledger `log` path
  whose outcome is not in `LANDED_OUTCOMES` moves to
  `<work-base>/.archived-logs/` instead of being unlinked; siblings
  absent from the ledger and landed-outcome logs keep the prior
  unconditional-delete behavior.
- Added an existence check in `_roster_reconcile_unreported`: right
  after reading an entry's `work` path, `Path(work).exists()` false
  prints a skip note and `continue`s instead of calling into
  `session_end_verdict`/`_issue_comments`.
- Added `gates/test_clean_reconcile_safety.py`, four cases matching the
  proposal's Acceptance section: (a) reconcile over a missing-workspace
  entry, (b) clean over a `refused`-outcome session, (c) clean over a
  `progressed`-outcome session, (d) empty state (no `runs/ledger.jsonl`,
  empty work dir, no roster/workspace-index).

canonical: python3 -m pytest gates/test_clean_reconcile_safety.py -q — result: 4 passed (executed live this session)

```
$ python3 -m pytest gates/test_clean_reconcile_safety.py -q
....                                                                     [100%]
4 passed in 0.04s
```

No SKIPPED lines in the output; hand-typed count (4) matches the pasted
summary.

## Why

Basis: docs/issue-1124/proposals/clean-reconcile-safety.md (approved).
Two live failures motivated the fix (issue #1124 body): `clean` deleted
the only durable evidence of a `refused` session (session 581a8f7e),
and `reconcile --unreported` crashed with `FileNotFoundError` on a
workspace `clean` had already removed.

## Upstream / basis

Based on: docs/issue-1124/proposals/clean-reconcile-safety.md

## What did not work

None.

## Rationale for deviations

None — implementation followed the approved proposal's planned items
one-for-one; no scope-exceeded stop and no alternative swap occurred.

## Open findings

canonical: docs/issue-1124/reports/implementation/2026-08-13-hunt-clean-reconcile-safety.md (read this session)

Phase-1's after-proposal hunt recorded no finding for this transition.
A before-landing hunt dispatch was not run this session: this session
is headless/single-shot (contract v3 s22), which requires any
delegated background result to be consumed within the same turn before
ending it, and no further turn remained after the landing commit to
wait on and act on a background hunter's result — recorded here as a
gap rather than launched-and-abandoned. Diff for this transition:
2 files changed (spawn.py, gates/test_clean_reconcile_safety.py),
237 insertions(+) / 69 deletions(-) (git show --stat 58d2bfc, read this
session) — within the "120s, one stance" tier had a hunt run.
