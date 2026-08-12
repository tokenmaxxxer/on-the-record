---
status: proposed
files:
  - docs/issue-1037/reports/conformance-review/survey.md
  - docs/issue-1037/proposals/2026-08-12-conformance-review-northpole-audit.md
  - docs/issue-1037/reports/conformance-review.md
---

## Intent

Conformance-review the phase-1 gap register PR #1040 already delivered for issue #1037 against R001's verify-before-claiming standard: re-run its own cited evidence rather than trust it, per this role's job of rendering per-requirement verdicts against a spec.

## Constraints

- Evidence must be repo actuals re-run this session, not a restatement of PR #1040's own transcripts.
- No fixes performed here; findings route to their existing or a new closing issue.

## What was done

Re-ran every `derived:` command and re-read every `canonical:` source PR #1040's merged gap register cites, one requirement at a time. Result at `docs/issue-1037/reports/conformance-review/survey.md`: requirements #1/#2/#3/#4/#6 reproduce as stated; requirement #5's cited zero-hit grep does not reproduce (`panel_cmd()` exists in `spawn.py` and predates the register's own commit), and a newer record (`docs/issue-1062/reports/implementation.md`, verdict `no-defect-found`) cites two evidence paths that have never existed in this repository's git history; requirement #7's cited transcript omits `gates/roles_due.py`, a real `board_condition` evaluator that also predates the register, though its narrow/advisory scope still leaves PR #1040's "refuted" conclusion for #7 correct on different grounds.

## Out of scope

- Filing new GitHub issues for the two corrected-reasoning findings on req#5/#7 — route through issue #973 (req#5) and issue #896 (req#7), both already open and on-topic.
- Fixing the dangling-citation defect in `docs/issue-1062/reports/implementation.md` — that is a defect in a different subject's record, reported here but not edited here.

## How you'll know it worked

`docs/issue-1037/reports/conformance-review.md` exists (phase 2), states a Present/Incorrect/Unverifiable-shaped verdict for each of the 7 requirements against PR #1040's register, and both open findings (the req#5 dangling citation, the req#5/#7 non-reproducing transcripts) are logged with a resolution path.

## What did not work

None — see `docs/issue-1037/reports/conformance-review/survey.md`'s own "What did not work" section for the record-claim-guard.sh iteration during authoring of that file specifically.
