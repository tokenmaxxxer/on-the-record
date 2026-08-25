# Record-kind vocabulary

Issue #2241 stage 1: a record's `kind:` frontmatter line has been used ad
hoc since before this spec existed — a repo-wide sweep found it in 420+
files under 40+ distinct spellings (`survey` vs `current-state-survey`,
`report` vs `record`, a dozen role-specific `-record` suffixes, ...).
This document formalizes that field into a closed vocabulary: a value not
listed here is not wrong by construction, but it should either match an
existing entry or be added here rather than spawning a new synonym.

This spec is **additive, not retroactive**: a record written before this
stage carries no `kind:` line at all, and that is not a violation — see
"Empty state" below. Every record gains a `kind:` line going forward.

Per the stage-1 proposal's Constraints, a `kind:` value outside this
vocabulary is **advisory only** at this stage
(`gates/record_lint.py::record_kind_vocabulary_check`) — it is never
wired into a blocking check here. A later stage (3 or 5, per
`docs/issue-2241/proposals/`) may promote it once the record-kind field
itself becomes load-bearing for observer verification.

## Vocabulary

Research/discovery records:
- `survey` — a role's current-state survey (scout-order directive's
  required pre-proposal artifact)
- `current-state-survey` — synonym for `survey`, still in wide use;
  kept rather than forcing a mechanical rename across the corpus
- `scout-brief` — the scout-protocol directive's parallel-sweep artifact
- `research-evidence-log` — a standalone evidence trail for a research
  question, distinct from a role's own survey
- `evidence-trail` — a running citation log backing a record's claims

Proposal/decision records:
- `proposal` — a phase-1 proposal (`docs/issue-<n>/proposals/`)
- `coding-proposal` — a proposal specifically for a coding/implementation
  unit of work
- `build-proposal` — a proposal for a build/release unit of work
- `decision` — an architecture decision record's body when not tagged `adr`
- `adr` — an architecture decision record (equivalent to `decision`; both
  are kept because the corpus already uses both)
- `decision-record` — a decision captured inside a role's own report file
  rather than under `docs/issue-<n>/decisions/`

Delivery/coding records:
- `coding-record` — a coding role's phase-2 delivery record
- `implementation` — an implementation role's phase-2 delivery record
- `implementation-record` — synonym for `implementation`
- `implementation-survey` — an implementation role's pre-work survey
- `build-report` — a release-engineering build's delivery record
- `role-deliverable-record` — a generic phase-2 deliverable record for a
  role with no more specific kind listed here

Verification/observation records:
- `verify-record` — a defect-verification role's terminal record
- `verify-survey` — a defect-verification role's pre-work survey
- `verify-proposal` — a defect-verification role's phase-1 proposal
- `execution-observation` — an execution-observation role's record
- `execution-observation-report` — synonym for `execution-observation`
- `observation-record` — a generic observation record outside the
  execution-observation role
- `review-record` — a conformance-review role's terminal record
- `conformance-review` — synonym for `review-record`
- `defect-verification-record` — synonym for `verify-record`
- `qa-record` — a qa/test role's terminal record
- `hunt-record` — a before-landing/after-proposal hunt's findings record
- `fan-out-record` — a fan-out worker's individual contribution record
- `hypothesis-testing` — a record whose primary content is falsifying or
  confirming a stated hypothesis
- `reflect-record` — a reflect-round record (guidance-reflection loop)
- `realization-record` — a record documenting that a previously-deferred
  item was realized/actioned
- `product-discovery-record` — a product-discovery role's record
- `requirements-engineering` — a requirements-engineering role's record
- `security-threat-model` — a security-threat-model role's record
- `content-design` — a content-design role's record

Generic/legacy:
- `record` — a generic role record predating a more specific kind
- `report` — synonym for `record`, still in wide use
- `resolution` — a record documenting how an open finding was resolved
- `deviation-log` — a record's own log of deviations from its approved
  proposal
- `superseded` — marks a record as no longer authoritative; the
  superseding record is cited in its own body

## Empty state

A record with no `kind:` frontmatter line at all (the entire corpus
before this stage) is not a violation of this spec and produces no
advisory — the field is additive only. A record whose `kind:` value is
present but not in this list also does not block anything at this
stage; it produces an advisory only, per the Constraints above.

## Extending this vocabulary

Add a new bullet under the closest matching category rather than
introducing a new category for one record. Removing a value here is a
breaking change for any existing record that carries it — do not
retroactively demand a rename.
