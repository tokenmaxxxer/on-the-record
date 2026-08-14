---
status: proposed
files:
  - docs/issue-1326/reports/legal-compliance.md
---

## Request

Issue #1326, legal-compliance half: read the IMDA Model AI Governance
Framework for Agentic AI (Jan 2026, primary text) and the EU AI Act as
they bear on autonomous software agents, and produce the
framework-requirement side of the gap table — grading criteria stated
up front, one row per IMDA best-practice item with its section/page
citation, one row per selected EU AI Act obligation with either a
clause citation or an explicit [interpretation] marker — plus the
framework-driven ranking input for the remediation backlog.

## Scope and boundary

Scope boundary: in scope is reading/citing the two named frameworks and authoring the framework-requirement gap-table rows plus backlog ranking; out of scope is the machinery-side column, any change to on-the-record's trace mechanisms, and any regulation outside the two named in the issue.

The machinery-side column (on-the-record's actual trace mechanisms) is
the architecture role's boundary on this same issue tree.

## Regulations enumerated

- IMDA Model AI Governance Framework for Agentic AI (Jan 2026 v1.0 /
  May 2026 v1.5), §Agent identity (Identification, Authorisation) and
  the Logging-and-monitoring control category — non-binding best-
  practice guidance, not a statute.
- EU AI Act Art. 12 (record-keeping, providers) and Art. 26 (deployer
  obligations, log retention), read for applicability to autonomous
  software agents.

Exclusions: this proposal excludes EU AI Act provisions outside Art. 12
and Art. 26 (e.g. Annex III risk-classification criteria in full,
conformity-assessment procedures, GPAI-model-specific obligations) and
excludes any jurisdiction's AI regulation other than these two named
sources, since the issue scopes the deliverable to exactly IMDA and the
EU AI Act.

## Constraints

- Precondition first: verify IMDA primary-text access before grading;
  downgrade source tier and record the fallback if inaccessible.
  Resolved this session — reachable, see
  docs/issue-1326/reports/legal-compliance/scout-brief.md.
- Every EU AI Act row must carry a clause citation or the
  [interpretation] marker, never neither and never a citation dressed
  up as more literal than it is — the Act has no autonomous-software-
  agent-specific text (confirmed this session for Art. 12/Art. 26).
  Citing a clause where the mapping is actually analogical would
  misstate confidence disproportionate to the source's actual scope;
  the necessity for citing at all is bounded by what the Act's own
  text supports, and the [interpretation] marker is the mitigation for
  the gap between clause text and agent-specific applicability.
- Every IMDA row cites a clause/section; the source uses section
  headings (§Agent identity etc.), not numbered clauses (confirmed this
  session), so citation is by heading + PDF page, stated as convention
  in the record's Grading-criteria section.
- Docs-only, this role's own record area only
  (docs/issue-1326/reports/legal-compliance.md) — never
  docs/issue-1326/reports/architecture/.

## Evidence / rationale

- IMDA §Agent identity (p.22-23 of the fetched PDF) defines the
  Identification bullets (Unique, Accounted-for, Differentiated-by-
  capacity, Catalogued) and the Authorisation bullets (Scoped/least-
  privilege/non-transferable, Bounded-by-authorising-human) — these
  become the IMDA gap-table rows.
- IMDA's agent-architecture enumeration names §Logging and monitoring
  as component 8 ("Records agent actions, decisions, and interactions
  ... to enable monitoring, debugging, and accountability") — becomes
  its own gap-table row.
- EU AI Act Art. 12 requires automatic event logging over a high-risk
  system's lifetime for risk-identification, post-market monitoring,
  and operational-monitoring purposes.
- EU AI Act Art. 26 requires deployers to retain automatically
  generated logs for at least six months and assign human oversight.
- Whether on-the-record's role agents fall under the Act's high-risk classification at all (assumption, unsourced) is not settled by Art. 12 or Art. 26's own fetched text — this is why every EU row is expected to carry [interpretation] rather than a bare clause cite.

## What will be done (phase 2, after approval)

- docs/issue-1326/reports/legal-compliance.md: Grading criteria section
  first (what counts as covered/partial/missing, stated so the
  judgment is reproducible), then the framework-requirement gap-table
  rows (IMDA rows per above, each with section+page citation; EU AI Act
  rows per above, each with Art. citation plus [interpretation] where
  the mapping is analogical), then the framework-driven
  remediation-backlog ranking input, then the record's required done/
  why/upstream/kind/loop_state/open-findings fields per contract v3.
- No code changes; no edits to docs/issue-1326/reports/architecture/**.

## How you will know it worked

- docs/issue-1326/reports/legal-compliance.md exists, states its
  citation convention in a Grading-criteria section before any table
  row, and every EU AI Act row in it carries a clause citation or the
  [interpretation] marker (grep-verifiable per the issue's own
  Acceptance).
- Every IMDA row cites a section/page locator, consistent with the
  primary PDF confirmed accessible this session.
