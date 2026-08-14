---
status: proposed
files:
  - docs/issue-1035/reports/conformance-review/survey.md
  - docs/issue-1035/proposals/2026-08-14-conformance-review-decision-queue-scope.md
  - docs/issue-1035/reports/conformance-review.md
---

## Intent

Conformance-review the merged PR #1053 delivery for issue #1035 against
R001 (decision_queue session-ownership scoping): render a per-requirement
verdict, not re-derive or re-decide the fix itself.

## Constraints

- Evidence must be re-run this session against the current working
  tree, not a restatement of `docs/issue-1035/reports/implementation.md`'s
  own claims.
- No fixes performed here; this role hands off findings, it does not
  edit `gates/flows.py`/`spawn.py`/`tests/test_flows.py`.

## What was done

canonical: `docs/issue-1035/reports/conformance-review/survey.md`, this
session's own phase-1 survey — re-ran `python3 -m pytest
tests/test_flows.py -k decision -v`, the exact command issue #1035's
Acceptance block names, and read the `gates/flows.py`/`spawn.py` diff
in merge commit `846e3a8d`. All 3 named acceptance cases (foreign item
excluded by default, own item still included, `--all` lists both)
reproduce green; the diff's `_own_item()` gating and `--all` threading
match the issue's Direction section. Preliminary verdict: R001 Present.

## Out of scope

- Filing or fixing anything in `gates/flows.py`, `spawn.py`, or
  `tests/test_flows.py` — this role only verdicts.
- Re-litigating #1013's or #1021's prior scoping decisions this issue
  builds on.

## How you'll know it worked

`docs/issue-1035/reports/conformance-review.md` exists (phase 2),
states a Present/Surface/Absent/Incorrect/Unverifiable verdict for R001
against PR #1053's merged diff, citing this session's own re-run
evidence.

## What did not work

None.
