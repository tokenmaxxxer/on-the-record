Subject: issue-1326 (legal-compliance, survey)

## Scope split (from the issue body)

canonical: gh issue view 1326 (read this session) — "Deliverable is
docs-only ... Roles: legal-compliance (framework reading), architecture
(machinery-side mapping)." This role owns the framework-requirement
column of the eventual gap table (grading criteria, IMDA clause
citations, EU AI Act citation-or-[interpretation] labeling) and the
remediation backlog's framework-driven priority ordering. The
machinery-side column (grep of consult-log/issue-record/PR-record/
approval-comment/watcher-log fields against each requirement) belongs to
the architecture role on this same issue tree; no
docs/issue-1326/reports/architecture/ tree exists yet in this working
tree.
derived: find docs/issue-1326 -type f
```
docs/issue-1326/reports/legal-compliance/scout-brief.md
docs/issue-1326/reports/legal-compliance/survey.md
```

## Framework primary-text access (issue's precondition)

Both primary sources were reachable and read this session — see
[[scout-brief]] (docs/issue-1326/reports/legal-compliance/scout-brief.md)
for the fetch/extraction record. No source-tier downgrade needed for
either framework.

## What this role's phase-2 record will need to carry

- A "Grading criteria" section stated before the gap table (issue
  Acceptance requirement 2), defining what trace-field evidence counts
  as covered/partial/missing for a framework requirement — this is a
  judgment call this role makes, not derivable from the frameworks
  alone, so it belongs in the proposal's Rationale for the human
  approver to review before phase 2.
- One row per IMDA best-practice bullet (Identification: Unique,
  Accounted-for, Differentiated-by-capacity, Catalogued; Authorisation:
  Scoped/least-privilege/non-transferable, Bounded-by-authorising-
  human) plus the Logging-and-monitoring control category, each citing
  its section heading + PDF page.
- One row per EU AI Act obligation this role selects as relevant
  (record-keeping/logging, deployer log-retention, human-oversight
  assignment), each carrying either a direct clause citation or the
  [interpretation] marker. canonical:
  docs/issue-1326/reports/legal-compliance/scout-brief.md (this
  session) — no fetched article names agents specifically, so expect
  all EU rows to carry [interpretation].
- A remediation-backlog line per partial/missing gap, ranked by
  framework provenance (an IMDA-sourced gap with a concrete clause is a
  firmer backlog candidate than an EU-sourced [interpretation] gap).

## Unknowns for phase 2 (not blocking the proposal)

- Assigning each row a covered/partial/missing label is future work: it
  needs a grep sweep over on-the-record's trace files (consult-log,
  issue/PR records, approval comments, watcher logs), read against the
  criteria section. That sweep belongs to the architecture role, or is
  joint work, under the two-phase contract's phase 2 — and stays
  outside this role's write set either way (this role does not edit
  machinery-mapping files).
