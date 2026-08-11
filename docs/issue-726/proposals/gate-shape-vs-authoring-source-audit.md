---
status: landed
files:
  - docs/issue-726/reports/conformance-review.md
  - docs/issue-726/reports/conformance-review/current-state-survey.md
---

# Gate-shape vs authoring-source conformance catalog (issue-726)

## Intent

Issue #726 asks this role to audit, across all on-the-record gate hooks,
whether the SHAPE a gate requires (path, record field, claim format,
commit trailer, spec-index coupling, methodology-write channel) matches
what authoring-time guidance (deployed directives, record templates,
PR/commit guidance — some living in `tokenmaxxxer-core` or per-role
`*-rulebook` repos) actually tells a session to write, and to catalog
every MATCH/MISMATCH/GAP with file:line so each defect becomes a
per-repo fix issue.

## Constraints

- Read-only provenance (issue's stated `provenance: read`) — no code
  fixes, only the catalog.
- 25 gate hooks under `on-the-record/hooks/`, exhaustive.
- Every MISMATCH/GAP row names the repo responsible for the fix.
- Cross-reference today's (2026-08-11) session-watcher gate-refusal
  events where available.
- This role's own contract gates the final catalog behind phase-2
  approval — `docs/issue-726/reports/conformance-review.md` cannot be
  written before an approvers.md-listed account approves this proposal.

## What will be done (phase 2, after approval)

1. Clone read-only checkouts of `tokenmaxxxer-core` and the `*-rulebook`
   repos named or implied by the issue (at minimum: the rulebook behind
   whichever role's directive text this session already observed at
   SessionStart, plus `implementation-rulebook` since #82 is a confirmed
   instance) alongside this checkout, without modifying either.
2. For each of the four Side-B GAP/cross-repo-flagged rows in
   `docs/issue-726/reports/conformance-review/current-state-survey.md`
   (`## Accumulation`, `## Siblings`/`# sibling:`, `APPROVE
   issue-<n>/<role>`, spec-index regeneration, PR Closes/Fixes phase
   split, call-shape flag consistency), grep the cloned repos for the
   matching directive text and resolve MATCH/MISMATCH/GAP with file:line
   on both sides.
3. Re-run the session-watcher grep against the full available watcher-log
   set (not just files with a literal `2026-08-11` string — also check
   file mtimes/JSON timestamp fields inside `.events.jsonl` for that
   date) to fill the strand-frequency ranking honestly, or state plainly
   that no matching events exist.
4. Write the final catalog table into
   `docs/issue-726/reports/conformance-review.md`, one row per
   gate-enforced shape (already enumerated in the survey), each
   classified MATCH/MISMATCH/GAP, with the responsible repo named on
   every MISMATCH/GAP row.

## Out of scope

- Fixing any MISMATCH/GAP found (each becomes a per-repo fix issue per
  the issue's own instruction — filing those issues is also out of scope
  for this role, which never files issues per its interaction
  protocol; they are handed off in the record's findings for the user to
  file).
- Modifying `tokenmaxxxer-core` or any `*-rulebook` repo.
- Any gate hook not under `on-the-record/hooks/`.

## Accumulation

N/A — this proposal does not add inline subprocess/gh call sites or
touch `roles/*.json`; it is a documentation/audit deliverable.

## How you'll know it worked

The final record contains one row per gate-enforced shape identified in
the phase-1 survey (all 25 hooks accounted for, including the ones with
no shape-mismatch path, marked as such), every row classified
MATCH/MISMATCH/GAP with file:line for the gate and (where one exists)
the authoring source, and every MISMATCH/GAP row names the repo that
must fix it — matching the issue's Acceptance criterion verbatim.

## What did not work

- Attempted to write the current-state survey with plain-English phrases
  like "shape 1/5" and "N passed" describing gate behavior;
  `record-claim-guard.sh` refused the first draft write for an
  unsupported bare count-ratio claim (matched `\d+/\d+`). Fixed by
  rewording ratio-shaped phrases to avoid the digit/digit and digit/word
  "of" patterns entirely, rather than adding `derived:` tags to prose
  that wasn't actually citing a measured count. This is itself a live,
  first-hand instance of the exact defect class issue-726 is auditing
  (gate-required shape learned only from the refusal, no proactive
  authoring-time guidance warning that ratio-shaped English triggers the
  count-claim gate in report/survey prose) — worth a line in the final
  catalog under record-claim-guard.sh in phase 2.

Proposal: docs/issue-726/proposals/gate-shape-vs-authoring-source-audit.md
