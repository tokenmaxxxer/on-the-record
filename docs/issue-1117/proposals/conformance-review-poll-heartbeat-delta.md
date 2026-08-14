---
status: proposed
files:
  - docs/issue-1117/reports/conformance-review.md
---

# Conformance review of issue #1117's poll-heartbeat delta-suppression delivery

## Intent

Board condition per the marketplace conformance-review role spec (issue-521): an implementation commit landed on `issue-1117/implementation` (merged as `1a259a65`, PR #1122) and no conformance-review record exists yet for that commit. This proposal is phase 1 (survey + requirement list, already committed at `docs/issue-1117/reports/conformance-review/survey.md`) for the phase 2 work: rendering a Present/Surface/Absent/Incorrect/Unverifiable verdict for each of the six requirement items extracted from issue #1117.

## Constraints

- Working from the artifact (`on-the-record/monitors/poll-heartbeat.sh`, `gates/test_poll_heartbeat_delta.py`, `docs/issue-1117/decisions/priorities.md`) and the issue text only — not the implementation session's stated intent.
- `docs/issue-1117/reports/conformance-review.md` cannot be written before an `approvers.md`-listed account approves this proposal (role-handoff contract v3 s19).
- Findings, if any, are handed off to the owning role (implementation) — never fixed by this role.

## What will be done (phase 2, after approval)

1. Re-verify the current-state facts already gathered in the phase-1 survey are still current (re-run the two test suites against the merge commit).
2. For each of Req-1 through Req-6, render one verdict via `review-traceability:finding-record` into `docs/issue-1117/reports/conformance-review.md`, citing file:line/test-name evidence.
3. Where a requirement uses permissive language ("may"), record it as Surface/deferred rather than Absent, per the survey's Req-3 note that cadence-relax was deliberately deferred and accepted as such in the issue's own approval thread.
4. Where a requirement's stated path (`docs/product/priorities.md`) was substituted for a different path for a documented, gate-driven reason, record it as Present-with-documented-deviation rather than Incorrect, and cite the deviation-log entry.

## Out of scope

- Fixing anything found.
- Re-litigating whether the `docs/issue-1117/implementation` approval was validly granted (approval-channel conformance is a different question from this issue's delta-suppression requirements).
- Any file outside `docs/issue-1117/reports/conformance-review.md` and its own `conformance-review/` subtree.

## Accumulation

N/A — this proposal adds no inline subprocess/`gh` call sites and touches no `roles/*.json`; it is a documentation/review deliverable.

## How you'll know it worked

`docs/issue-1117/reports/conformance-review.md` contains one verdict row per requirement item (Req-1 through Req-6) with cited evidence, satisfying the traceability/record-norm checks this role's output is checked against.

## What did not work

- Early drafts of the phase-1 survey were refused three times by `record-claim-guard.sh` (issues #333/#793/#870/#330): a bare "N/N passed" count typed outside a fence, an outcome claim ("both suites pass") whose nearest `canonical:` tag cited a file-read instead of an executed-live transcript, and a `docs/product/priorities.md` path reference typed as inline backticks instead of inside a fenced block. Fixed by moving every count/outcome into a fenced `derived:` transcript with an adjacent `canonical:` tag naming that same transcript, and confining the nonexistent path to a fenced block.
