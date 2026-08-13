---
code_under_review:
  - spawn.py
  - gates/test_requirement_drift.py
type: fix
breaking: false
canonical: pytest run pasted verbatim in this file's "## Acceptance" section, executed this turn
acceptance: python3 -m pytest gates/test_requirement_drift.py -q — result: pass, 6 passed, 0 skipped
verdict: pass
loop_state: landed
---

# issue-1142 phase-2: implementation record

## What was done

canonical: gh issue view 1142 (APPROVE issue-1142/implementation posted by an approvers.md account; docs/issue-1142/proposals/2026-08-13-drift-check-enforced-exclusion.md was merged via PR #1144, per `git log --grep 'issue-1142'`)

Implemented the approved proposal
`docs/issue-1142/proposals/2026-08-13-drift-check-enforced-exclusion.md`.

- `spawn.py::requirement_drift()`: the digest-line regex now captures
  the status group (`live_entries` values are now
  `(paraphrase, status, source_issue)` instead of
  `(paraphrase, source_issue)`). `unmentioned_live` is filtered down to
  entries whose parsed status is `open` before the drift print loop —
  digest ids with status `enforced` no longer print a drift line for
  missing citation, even when no open issue/PR mentions them. An id
  with no parseable digest entry (defensive fallback) keeps the prior
  conservative behavior (treated as `open`, still flagged).
- `gates/test_requirement_drift.py`: added three cases —
  `test_enforced_uncited_requirement_not_flagged`,
  `test_open_uncited_requirement_still_flagged`,
  `test_empty_digest_produces_no_flags`.

## Why

The watchdog previously flagged `enforced` (delivered, live
enforcement path) requirements as drifted purely for lacking a
citation in an open issue/PR — noise, since delivered requirements
have no open work item left to cite them. Only `open` (not-yet-
delivered) requirements need a live citation to prove they are being
tracked.

## Upstream

Basis: docs/issue-1142/proposals/2026-08-13-drift-check-enforced-exclusion.md

## What did not work

None.

## Acceptance

canonical: this turn's own pytest run below (transcript pasted verbatim)

acceptance: python3 -m pytest gates/test_requirement_drift.py -q — result: pass, 6 passed, 0 skipped.

```
$ python3 -m pytest gates/test_requirement_drift.py -q
......                                                                   [100%]
6 passed in 0.06s
```

## Doc placement

No env var, config key, dependency, migration, or setup step was
added — no handbook update needed. No public signature or wire format
changed outside the frozen write set — no decisions-doc entry needed.
No benchmark/investigation numbers produced.

## Open findings

None open.

## Hunt

canonical: docs/issue-1142/reports/implementation/hunt-drift-check-enforced-exclusion.md — warrant-hunter dispatched this turn, before-landing transition, stance "assume the rule as written cannot hold — find the state nothing maintains", diff confined to spawn.py::requirement_drift() and gates/test_requirement_drift.py (~20 lines net per `git diff --stat`), cap 60s.

Result: NO FINDING.

closed_checks:
- name: before-landing hunt, stance "assume the rule as written cannot hold"
  code_sha: (working tree, pre-commit) spawn.py, gates/test_requirement_drift.py — same file list as code_under_review above
