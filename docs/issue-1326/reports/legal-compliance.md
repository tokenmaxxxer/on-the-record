Subject: issue-1326 (legal-compliance, phase-2 gap-table record)

kind: report
loop_state: reviewing

## What was done

canonical: docs/issue-1326/reports/legal-compliance/scout-brief.md (this
issue tree, primary-text fetch record) and this session's direct fetches
of https://artificialintelligenceact.eu/article/12/,
.../article/13/, .../article/26/, .../article/50/.
Authored the framework-requirement gap-table rows for IMDA Model AI
Governance Framework for Agentic AI (Jan 2026 v1.0) and EU AI Act
Art. 12 and Art. 26, each row citing a section+page (IMDA) or an
Art./paragraph (EU) — no row carries a bare `[interpretation]` tag with
no clause number, per the reconciliation consult's correction (a).
Resolved correction (b) (the "transparency about AI-generated origin"
row) by checking Art. 13 and Art. 50 before deciding; neither grounds it
under this issue's two named sources, so it is marked out-of-scope
rather than kept as an unanchored `[interpretation]` row. Reconciled
every row against docs/issue-1326/reports/architecture.md's
covered/partial/missing grades, matching or correcting each one.

## Why

issue #1326, implication 2 of
docs/reports/product/2026-08-14-hiring-market-recon.md. This record
fulfills the issue's Acceptance items 1-2 (grading criteria stated up
front; every EU row carries a clause citation, an [interpretation]
marker anchored to a clause, or an explicit out-of-scope marking) plus
this delivery's own instruction to fold in the reconciliation consult's
three corrections.

## Upstream

Based on: docs/issue-1326/proposals/2026-08-14-framework-gap-table-legal-compliance.md
(approved via issue comment "APPROVE issue-1326/legal-compliance"),
docs/issue-1326/reports/legal-compliance/{survey,scout-brief}.md, and
docs/issue-1326/reports/architecture.md (machinery-mapping half, PR
#1328, landed on main at commit 2a5fa462).

## Grading criteria (fixed up front, applies to every row below)

Adopting docs/issue-1326/reports/architecture.md's criteria verbatim for
consistency across the two halves of this gap table (a single
covered/partial/missing rubric, not two divergent ones):

- **covered** — the requirement's field is captured in a structured,
  machine-parseable location (frontmatter field, dedicated log schema
  key) **and** a gate refuses to let the record land without it (commit
  hook, PR preflight, or CI check).
- **partial** — the requirement is captured in some form but at least
  one of: (a) free-text only, not structured/queryable; (b) not
  gate-enforced (absence doesn't block landing); (c) covers only a
  subset of the requirement's scope.
- **missing** — no mechanism in the repository captures this
  requirement in any form.

Citation convention (per the approved proposal): IMDA has no numbered
clauses in its source PDF, so IMDA rows cite section heading + PDF page
(pdftotext locator). EU AI Act rows cite Article + paragraph number.
Every EU row carries a real Art./paragraph citation or is marked
**out-of-scope** — never a bare `[interpretation]` tag standing alone
with no clause number, correcting this issue's original acceptance
wording (which allowed an unanchored `[interpretation]` marker) per the
reconciliation consult.

## Regulations and standards enumerated

The regulations and standards graded in this report:

- IMDA Model AI Governance Framework for Agentic AI (Jan 2026 v1.0 / May
  2026 v1.5) — non-binding best-practice guidance/standard — §Agent
  identity (Identification, Authorisation) and §Logging and monitoring.
- EU AI Act Art. 12 (record-keeping, providers) and Art. 26 (deployer
  obligations) — this issue's named regulation scope.
- EU AI Act Art. 13 (transparency to deployers) and Art. 50 (synthetic
  content / deepfake transparency) — checked as candidate homes for one
  row (see correction (b) below) and ruled out; not adopted as
  regulation sources for this gap table, listed here only for the audit
  trail of what was checked.

## IMDA framework-requirement rows

canonical: docs/issue-1326/reports/legal-compliance/scout-brief.md lines
13-29, citing /tmp/mgf.txt:1008-1073 (this session's pdftotext of the
fetched primary PDF, IMDA MGF for Agentic AI v1.0, 22 Jan 2026).

**Row 1 — Identification: agent is Unique, Accounted-for,
Differentiated-by-capacity, Catalogued.**
canonical: gates/quality_bar.py lines 9-19 (this session's read).
Citation: §Agent identity, "Identification" bullets, p.22. Machinery
mapped (architecture.md): `CLAUDE_ROLE` self-declared string;
account-level resolution exists only inside the verdict-authorship
check. Grade: partial. Reconciliation: matches architecture.md's grade
— the Identification bullets require a persistent per-agent identifier
independent of self-declaration, and only one narrow check resolves to
a real account.

**Row 2 — Authorisation: Scoped/least-privilege/non-transferable,
Bounded-by-authorising-human.**
canonical: gates/repo_scope.py (this session's read, full file).
Citation: §Agent identity, "Authorisation" bullets, p.22-23. Machinery
mapped: `WRITE_SCOPE` declared in role directive text; no committed
gate confirmed enforcing diff-subset-of-scope (repo_scope.py checks
scope-tagging of capability-absence claims, not write-scope
enforcement). Grade: partial. Reconciliation: matches architecture.md's
grade, with architecture's own caveat carried forward — the search over
gates/*.py (derived: `ls gates/*.py | grep -v '^gates/test_' | wc -l`,
architecture.md's own count) was targeted, not exhaustive, so "missing"
is not asserted.

**Row 3 — Authorisation: Bounded-by-authorising-human (the approval
event itself).**
canonical: gates/ci.py, function `_phase_from_approval` (this session's
read).
Citation: §Agent identity, "Authorisation" bullet "Bounded by the
authorising human", p.22-23. Machinery mapped: exact-string `APPROVE
issue-<n>/<role>` match resolved to a docs/specs/approvers.md GitHub
login. Grade: covered. Reconciliation: matches architecture.md's grade
— structured, gate-enforced (blocks the phase-two transition when
absent), resolves to a real account per the bullet's own language.

**Row 4 — Logging and monitoring: records agent actions, decisions,
interactions (agent-architecture component 8; recurs as a pillar-3
technical control).**
canonical: gates/record_lint.py, module docstring (this session's read).
Citation: §Logging and monitoring (component 8 / pillar 3 control
category), same page range per scout-brief's structure note. Machinery
mapped: consult-log.md (append-only per header) plus role-record
frontmatter, shape-checked. Grade: covered. Reconciliation: matches
architecture.md's grade — structured, shape-gated.

**Row 5 — Logging and monitoring: tamper-evidence of the trail.**
canonical: docs/reports/consult-log.md header line (this session's
read); no matching enforcement hook turned up in this session's listing
of on-the-record/hooks/.
Citation: same section as row 4. Machinery mapped: consult-log.md
"never hand-edited" convention, undocumented as a gate. Grade: partial.
Reconciliation: matches architecture.md's grade — git history is
tamper-evident by construction, but the specific append-only convention
has no enforcement hook.

**Row 6 — Logging and monitoring: retention/retrievability of the
trail.**
canonical: derived: `grep -n "^runs" .gitignore` → `1:runs/` (this
session's rerun of architecture.md's own derivation).
Citation: same section as row 4. Machinery mapped: board-facing
artifacts retained indefinitely (git); process-level `runs/`
roster/ledger gitignored, local-only. Grade: partial. Reconciliation:
matches architecture.md's split grade — committed trail is retained,
process-level trail is not.

## EU AI Act rows (Art. 12 and Art. 26 only, per this issue's scope)

canonical: this session's fetches of
https://artificialintelligenceact.eu/article/12/ and
https://artificialintelligenceact.eu/article/26/ (paragraph text quoted
below), and docs/issue-1326/reports/legal-compliance/scout-brief.md
lines 31-48. Neither article names "autonomous software agent"; the
Act's high-risk classification turns on sector/use-case, not agent
autonomy — whether on-the-record's role agents are a "high-risk AI
system" at all is left open by the fetched article text. This
unresolved-applicability point is why every row below still carries
`[interpretation]` alongside its clause citation, per correction (a):
the clause is real and specific, but its applicability to this
repository's tooling is analogical, not settled.

**Row 1 — Automatic event logging over the system's lifetime.**
canonical: https://artificialintelligenceact.eu/article/12/ (this
session's fetch), Art. 12(1).
Citation: Art. 12(1) — "technically allow for the automatic recording of
events (logs) over the lifetime of the system" [interpretation: on-the-
record is not a classified high-risk AI system under the Act; mapped by
analogy to its own autonomous-agent tooling]. Machinery mapped:
consult-log.md, append-only, one line per `spawn.py consult` call.
Grade: covered. Reconciliation: matches architecture.md's grade.

**Row 2 — Traceability: logs must support identifying risky situations,
post-market monitoring, operational oversight.**
canonical: https://artificialintelligenceact.eu/article/12/ (this
session's fetch), Art. 12(2).
Citation: Art. 12(2) [interpretation, same applicability caveat as row
1]. Machinery mapped: docs/handbooks/operations.md board-read
mechanism; no field turned up tying a board entry to a specific
model/version. Grade: partial. Reconciliation: matches architecture.md's
grade and sharpens the clause — architecture's "no field tying a board
entry back to a specific model/version" observation lines up directly
with Art. 12(2)'s "identifying situations that may result in the AI
system presenting a risk" language, so this row absorbs
architecture.md's separate "traceability of functioning across the
system's lifecycle" row (both cite the same paragraph; kept as one row
here to avoid double-counting a single Art. 12(2) obligation).

**Row 3 — Human oversight: deployer assigns oversight to competent,
authorised natural persons.**
canonical: https://artificialintelligenceact.eu/article/26/ (this
session's fetch), Art. 26(2).
Citation: Art. 26(2) — "assign human oversight to natural persons who
have the necessary competence, training and authority" [interpretation:
on-the-record's role-session operators are not "deployers" of a
classified high-risk system under the Act; mapped by analogy]. Machinery
mapped: gates/ci.py `_phase_from_approval` plus docs/specs/approvers.md
— delivery work is blocked pending a listed human's exact-string
approval. Grade: covered. Reconciliation: matches architecture.md's
grade.

**Row 4 — Log retention: deployer retains automatically generated logs,
appropriate to purpose, at least six months.**
canonical: https://artificialintelligenceact.eu/article/26/ (this
session's fetch), Art. 26(6).
Citation: Art. 26(6) — the "at least six months" floor [interpretation,
same deployer-mapping caveat as row 3]. Machinery mapped: board
artifacts retained indefinitely (git); `runs/` roster/ledger gitignored,
local-only. Grade: partial. Reconciliation: matches architecture.md's
split grade — the committed trail exceeds the six-month floor by
construction (indefinite git retention); the gitignored roster/ledger is
the actual gap.

## Correction (b): "transparency about AI-generated origin" is out-of-scope for Art. 12 / Art. 26

canonical: this session's fetches of
https://artificialintelligenceact.eu/article/13/ and
https://artificialintelligenceact.eu/article/50/.

Architecture's original row ("Transparency to downstream reviewers about
AI-generated origin [interpretation, analogous to the Act's transparency
obligation]: partial") does not sit under Art. 12 or Art. 26 — neither
article addresses disclosure of AI origin; both are
record-keeping/retention/oversight obligations. Checked the two
candidate homes before deciding:

- **Art. 13** ("transparency and provision of information to
  deployers"): requires a high-risk system's operation to be
  "sufficiently transparent to enable deployers to interpret a system's
  output and use it appropriately," delivered via instructions for use
  (intended purpose, accuracy, limitations). This is deployer-facing
  interpretability of system behavior, not disclosure that a given
  artifact was AI-generated. Does not fit.
- **Art. 50** ("transparency obligations for certain AI systems"):
  requires providers to mark synthetic audio/image/video/text as
  machine-detectable, and requires deployers to disclose deepfakes and
  AI-generated text "published to inform the public on matters of public
  interest" (exempted where the content underwent human editorial
  review). on-the-record's commit trailers, PR bodies, and role records
  are internal engineering artifacts read by other role sessions and
  human approvers within the same repository — not audio/image/video
  synthesis, and not text "published to inform the public." They also
  already carry human editorial control (the approval gate). Does not
  fit either.

**Verdict on this one row: out-of-scope for this issue's two named
sources.** It is dropped from the gap table above rather than kept as an
unanchored `[interpretation]` row. It is not re-graded covered/partial/
missing under any clause here — recording the mismatch is the
correction, not a new grade. A future issue that wants to track
AI-origin disclosure in commit trailers as a documentation-quality
question would rest on a product decision, not on Art. 12, Art. 13,
Art. 26, or Art. 50, so it belongs to a separate issue rather than this
gap table.

## Remediation backlog (framework-driven ranking, one line per partial/missing gap)

Ranked by citation firmness: an IMDA row with a specific bulleted
requirement outranks an EU row still carrying the applicability caveat
above, since the latter's underlying "is this even a high-risk system"
question stays open in both roles' fetched text.

1. **(IMDA §Agent identity "Identification", row 1, amber/partial)** Add
   a gate-enforced, general per-agent identity field (resolved
   GitHub/git account, not bare `CLAUDE_ROLE`) to the role-record
   schema, extending quality_bar.py's anti-circularity resolution beyond
   the verdict-authorship check.
2. **(IMDA §Agent identity "Authorisation", row 2, amber/partial)**
   Verify whether a merge-time write-scope enforcement gate exists under
   a name this session's search did not try; if none exists, file one
   that checks a landed diff's file set against the producing role's
   declared `WRITE_SCOPE`.
3. **(IMDA §Logging and monitoring, tamper-evidence, row 5,
   amber/partial)** Mechanically enforce consult-log.md's
   never-hand-edited convention (a hook rejecting any diff touching
   existing consult-log lines, only appends).
4. **(IMDA §Logging and monitoring retention, row 6, and EU AI Act
   Art. 26 log retention, row 4, both amber/partial)** Decide and
   document a retention policy for the process-level `runs/`
   roster/ledger trace — either commit a redacted summary to the board
   or explicitly accept it as ephemeral.
5. **(EU AI Act Art. 12 traceability, row 2, amber/partial)** Add a
   model/version-identity field to the board record schema so a given
   entry traces back to the producing model, not just the role name —
   this is the one gap this table identified under an EU clause with no
   IMDA equivalent bullet, so it is worth tracking even though the
   row's applicability itself is `[interpretation]`.

Architecture's original backlog item for an AI-authorship disclosure
field is dropped from this backlog, consistent with correction (b)
above: it was ranked against an EU row that does not survive
reconciliation as an Art. 12 or Art. 26 gap.

## Risk rating (per gap-table row, red/amber/green)

Mapped from this report's covered/partial/missing grades: covered =
green, partial = amber, missing = red. No row above is graded missing,
so no red rows exist in this table.

- Green (covered): IMDA §Agent identity "Authorisation"/approval-event
  row 3; IMDA §Logging and monitoring row 4; EU AI Act Art. 12(1) row 1;
  EU AI Act Art. 26(2) row 3.
- Amber (partial): IMDA §Agent identity "Identification" row 1; IMDA
  §Agent identity "Authorisation"/write-scope row 2; IMDA §Logging and
  monitoring tamper-evidence row 5; IMDA §Logging and monitoring
  retention row 6; EU AI Act Art. 12(2) row 2; EU AI Act Art. 26(6)
  row 4.
- Red (missing): none.

This is a machinery-completeness rating against the two named
regulations/standards' best-practice/clause text, not a determination
that any amber row constitutes present legal non-compliance — see the
Open findings entry on unresolved Act applicability below.

## Mitigations mapped to risks

Each amber row's mitigation is its corresponding remediation-backlog
item above, named against the regulation/standard it was risk-rated
under (per the Regulations and standards enumerated section):

- Risk: IMDA Model AI Governance Framework for Agentic AI, §Agent
  identity "Identification" (row 1, amber) → Mitigation: backlog item 1,
  gate-enforced per-agent identity field.
- Risk: IMDA Model AI Governance Framework for Agentic AI, §Agent
  identity "Authorisation" (row 2, amber) → Mitigation: backlog item 2,
  verify/add write-scope enforcement gate.
- Risk: IMDA Model AI Governance Framework for Agentic AI, §Logging and
  monitoring, tamper-evidence (row 5, amber) → Mitigation: backlog item
  3, enforce consult-log append-only convention.
- Risk: IMDA Model AI Governance Framework for Agentic AI, §Logging and
  monitoring, retention (row 6, amber) and EU AI Act Art. 26 log
  retention (row 4, amber) → Mitigation: backlog item 4, retention
  policy for `runs/` roster/ledger.
- Risk: EU AI Act Art. 12 traceability (row 2, amber) → Mitigation:
  backlog item 5, model/version-identity field on board records.

No red rows, so no red-tier mitigation is required for this table.

## Final verdict

canonical: acceptance: docs-only judgment-based gap-table grade, no acceptance command on record for this target — result: UNMEASURED

**pass-with-mitigations.** No requirement is graded missing; six amber
gaps each have a named, scoped remediation-backlog candidate above.
Verdict is scoped to this issue's two named regulations/standards only
(IMDA best-practice guidance and EU AI Act Art. 12 and Art. 26) and is
conditioned on the unresolved Act-applicability point in Open findings
below — it is a research/documentation-completeness verdict, not a
legal-compliance sign-off.

## Processing description

Not a personal-data-processing assessment: this deliverable maps
on-the-record's internal engineering trace mechanisms (consult-log,
role records, approval comments, commit trailers, PR linkage, process
roster) against IMDA/EU-AI-Act audit-trail requirements. No personal
data of end users is processed by the mechanisms graded here; the
"processing" in scope is repository-internal event logging of
role-session actions (timestamps, role identifiers, issue numbers,
approval logins), read directly from the artifacts cited per-row above.

## Necessity assessment

Producing this gap table is the issue's own deliverable (implication 2
of the landed hiring-market recon report) and is proportionate to it:
docs-only, read-only against existing artifacts, no new trace mechanism
built or data collected. The remediation-backlog items it recommends are
each scoped to a single named gap (one schema field, one hook) and are
not proposed as new data collection beyond what's already logged —
consistent with a necessity/proportionality read even though this is a
documentation deliverable, not a DPIA on personal-data processing.

## Open findings

- The EU AI Act applicability question itself — whether on-the-record's
  role-agent tooling is a "high-risk AI system" and its operators are
  "deployers" under the Act at all — stays open after this session's and
  architecture's fetched article text (Art. 12, Art. 13, Art. 26, and
  Art. 50). Every EU row above is graded conditional on the analogical
  mapping holding; none of this report's `[interpretation]` markers
  should be read as a settled legal position. resolution path: this is
  a genuine legal question outside a docs-only research role's
  authority to resolve — flag for a qualified legal review if the
  remediation backlog items above are ever escalated to a
  compliance-driven (rather than engineering-quality-driven)
  justification.
- IMDA row 2 (Authorisation/write-scope) and its backlog item 2 stay
  graded partial rather than missing because this session did not
  exhaustively read every gates/*.py module — same caveat
  architecture.md's own record already carried. resolution path: a
  future session doing a full gates/*.py sweep can upgrade or affirm
  this grade.

## Next steps

- resolution path: file the five remediation backlog items above as
  individual issues (contract v3 s19a build-now bypass or normal
  two-phase flow, per whoever picks this up) — this role does not
  self-spawn new issues per the deviation-loop's scope-exceeded rule.
- resolution path: if a future session wants to settle the Art. 12 /
  Art. 26 applicability question itself (not just grade against it),
  that is a distinct legal-research task, not an extension of this gap
  table.

## What did not work

None.
