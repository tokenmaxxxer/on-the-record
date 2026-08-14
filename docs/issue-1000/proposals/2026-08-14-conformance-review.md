---
status: proposed
files:
  - docs/issue-1000/reports/conformance-review/survey.md
  - docs/issue-1000/proposals/2026-08-14-conformance-review.md
  - docs/issue-1000/reports/conformance-review.md
---

## Scouting

Skipped — this is a mechanical re-verification of an already-merged spec-shape change against fixed acceptance items, not a product-shaped decision with open design choices.

## Intent

Conformance-review the merged issue #1000 delivery (commit 3269ae63, PR #1075: wire capacity-planning's `external_burden` axis-evaluation procedure into `roles/specs/capacity-planning.spec.json`) against issue #1000's four acceptance items, per this role's job of rendering per-requirement verdicts against a spec rather than trusting the delivering role's own claim.

## Constraints

- Evidence must be repo actuals re-run this session, not a restatement of the implementation record's own transcripts.
- No fixes performed here; the one open finding (role-spec-reference-guard.sh's `_VERIFICATION_FAMILY_ROLES` allowlist not covering capacity-planning) routes to a follow-up issue, not an edit in this record's write set.

## What was done

Re-ran every `derived:`/`acceptance:` command the implementation record cites, and independently checked the two acceptance items it cites no command for. Result at `docs/issue-1000/reports/conformance-review/survey.md`: all four acceptance items (rulebook carries the procedure; `gates/role_spec_shape.py` passes for capacity-planning; empty state — no other role spec touched; provenance traces to the merged batch-3 proposal) reproduce as claimed.

## Out of scope

- Filing a follow-up issue for the `_VERIFICATION_FAMILY_ROLES` gap — it is pre-existing (already recorded once for performance-engineering in issue #999) and outside `roles/specs/capacity-planning.spec.json`'s write set.

## How you'll know it worked

`docs/issue-1000/reports/conformance-review.md` exists (phase 2), states a Present/Surface/Absent/Incorrect/Unverifiable verdict for each of the four acceptance items against commit 3269ae63, and the one open finding is logged with a resolution path.

## What did not work

None.
