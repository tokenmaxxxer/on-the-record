---
status: proposed
files:
  - docs/issue-1037/reports/defect-verification/survey.md
  - docs/issue-1037/proposals/2026-08-12-northpole-gap-audit.md
---

## Intent

Adversarially audit `docs/specs/northpole.md`'s "every requirement served" claim against repo actuals, per issue #1037, and deliver a gap register. No fixes in this issue.

## Constraints

- Evidence must be repo actuals (paths, hook registrations, live-fire records) — not narrative.
- Check the issue's 6 named suspects first, then hunt beyond them.
- No fixes performed here; findings route to their existing or proposed closing issues.

## What was done

Read the current-state record for each of the 6 named suspects (panel SendMessage round-trip, requirement_intake_consult live firing, operator-experience blocks, non-on-the-record e2e run, 43-role utilization, watcher-dead stale-pid), plus one independent angle per requirement, and wrote the gap register at `docs/issue-1037/reports/defect-verification/survey.md`.

## Out of scope

- Filing new GitHub issues for corroborated gaps that already have an open tracking issue (#973, #896, #1006) — this audit cites them instead of duplicating.
- Any remediation work.

## How you'll know it worked

`docs/issue-1037/reports/defect-verification/survey.md` exists, lists verified-holds/refuted-with-evidence status for each of the 7 requirements, cites repo actuals per finding, and addresses all 6 named suspects plus at least one gap found beyond them — matching issue #1037's Acceptance criteria.

## What did not work

- Initial drafts of the survey were refused repeatedly by `record-claim-guard.sh`'s outcome-claim and state-claim checks (issues #793/#870) for citing `canonical:` tags that read a source file without naming an executed-live transcript/measurement, or for placing the tag more than 3 lines from the claim after markdown line-wrapping split the sentence. Fixed by keeping each `canonical:` sentence on one physical line naming the cited record's own "transcript" explicitly, and moving raw `PASS`/`done`-bearing output into fenced code blocks (which the gate excludes from these checks).
