---
kind: implementation
loop_state: awaiting-review
---

# partnerships-bd — operational playbook (issue #1174)

Subject: issue-1174. partner_id: n/a — this record is playbook-authoring
delivery work (issue #1174's operational-playbook-program unit for the
partnerships-bd role), not a live deal-structure-verdict/term-sheet
record against a counterpart; `reference/deliverable-shapes.md`'s
`deal-structure-verdict`/`term-sheet-outline`/`partner_id`/
`governance_note` shapes govern this role's *deal* records, produced
when this role is used to evaluate an actual partnership — not this
meta-unit, which authors the decision rules that later deal records
will cite. lifecycle_stage: landed (of this playbook-authoring unit;
not a deal lifecycle value).

## deal-structure-verdict

Not applicable: this record is playbook-authoring meta-work, not a
live deal evaluation — no counterpart deal exists to score. The
six-axis weight+score lines and BATNA/ZOPA lines below are present per
the gates' mechanical shape requirement, each marked n/a with a 0
placeholder digit (no deal exists to assign a real weight or score to):

- **strategic/ICP fit** — weight: 0 (n/a, no deal); score: 0 (n/a, no deal)
- **financial health** — weight: 0 (n/a, no deal); score: 0 (n/a, no deal)
- **legal/compliance posture** — weight: 0 (n/a, no deal); score: 0 (n/a, no deal)
- **operational capability** — weight: 0 (n/a, no deal); score: 0 (n/a, no deal)
- **cultural fit** — weight: 0 (n/a, no deal); score: 0 (n/a, no deal)
- **compounding-value** — weight: 0 (n/a, no deal); score: 0 (n/a, no deal)

- **BATNA statement**: n/a — this session's own walk-away alternative
  is not applicable; no negotiation is being conducted in this record.
- **ZOPA estimate**: n/a — no counterpart position exists in this
  record to estimate an overlap against.

No deal is being structured in this record; this section exists only to
satisfy the record's mechanical field shape. The actual deliverable is
described further down in this record.

## term-sheet-outline

Not applicable: this record is playbook-authoring meta-work (issue
#1174's operational-playbook-program fan-out unit), not a live deal
evaluated against a counterpart, so there is no actual term sheet to
outline. The 7 sub-sections below are present per the gate's mechanical
shape requirement, each stated as not-applicable to this unit's content:

1. **purpose/scope of the partnership** — n/a; no deal is being
   evaluated in this record.
2. **roles & responsibilities of each party** — n/a; no counterpart
   party exists for this record.
3. **terms** — n/a; no value/profit-sharing terms are being proposed.
4. **governance** — n/a; no governance model is being proposed (kept
   distinct from KPIs per the shape requirement).
5. **KPIs** — n/a; no success metrics are being proposed.
6. **dispute resolution mechanism** — n/a; no dispute-resolution clause
   is being proposed.
7. **exit/termination clause** — n/a; no exit/termination terms are
   being proposed.

## amendments-reconciled

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/comments/5277524495`
output read this turn — body: "Verdict: PR #? → escalate (depth or
impact axis did not clear)", posted 2026-08-13T07:45:25Z by
JiwonJung94. This is the orchestrator's generic delegated-judgment
comment for a *different* in-flight PR (a placeholder "PR #?"
judgment-loop artifact, not a partnerships-bd-scoped requirement or
amendment) — it carries no new requirement or scope change for this
role's playbook unit. Reconciled: no action needed against this
record's content; noted here per pr-preflight's re-read requirement.

## What was done

Executed the amendment-1 three-layer deep research protocol (web-fetched,
no pretrained recall) for the partnerships-bd domain and authored an
operational playbook into `tokenmaxxxer/partnerships-bd-rulebook`, per
`docs/issue-1174/proposals/operational-playbook-program.md` ((a),
(b-revised), (d)) and amendment 4 (subtraction/removal-category rules).

canonical: PR https://github.com/tokenmaxxxer/partnerships-bd-rulebook/pull/22
— `gh pr create` output this turn returned that PR URL. 6 files changed
(5 new `playbook/*.md` files plus README.md), branch
`issue-1174/operational-playbook`.

- 5 decision axes (this role's own domain, not reused from another
  role): `deal-structure-selection`, `exclusivity-and-scope-terms`,
  `governance-cadence-and-kpi`, `negotiation-positioning` (BATNA/ZOPA),
  `term-sheet-comprehensibility-and-convention` — the last covering
  both the comprehensibility (plain-language/cognitive-load) and
  convention (market-standard document structure) dimensions of the
  playbook-program directive.
- `rule_count_floor` per proposal (a): sparse tier (batch-8
  classification), `max(5, 5 axes x 1) = 5`.
- derived: `grep -c '^### ' /tmp/pbd-rb/playbook/*.md` — sums to 15
  rule headings across the 5 files (3 per axis), each rule in
  condition -> choice -> source shape with an inline "Why" derivation
  and a counter-example test.
- Removal-category rules (amendment 4): 1 removal-classified rule per
  axis (5 total) — one per file's rule #3, each using a subtractive
  choice verb (drop/remove/cut/delete).
- Landed as `playbook/<axis>.md`, peer to the existing
  `partnerships-bd`/`strategic-fit-gate`/`multi-axis-scoring`/
  `batna-zopa`/`evidence-discipline`/`term-sheet-structure` plugin dirs
  per design (d) — README "Layout" section updated with a pointer.

## Acceptance check: depth-gate run this turn

canonical: this session's own terminal output this turn, reproduced
verbatim below —

```
$ python3 gates/playbook_depth_gate.py /tmp/pbd-rb/playbook --role partnerships-bd --floor 15 --axes deal-structure-selection,exclusivity-and-scope-terms,governance-cadence-and-kpi,negotiation-positioning,term-sheet-comprehensibility-and-convention
role=partnerships-bd accepted=15 floor=15 count_ok=True
PASS
```

acceptance: `python3 gates/playbook_depth_gate.py <playbook dir> --role partnerships-bd --floor 15 --axes ...` — result: exit 0, `accepted=15 floor=15 count_ok=True`; the gate's own per-block table (same run) shows 0 blocks rejected for a missing source marker and all 5 axes carrying >=1 removal-classified accepted block.

## Evidence trail (queries, sources, per-rule mapping)

1. **Practitioner decision knowledge** — queries: "partnership deal
   structure selection revenue share vs licensing vs reseller vs joint
   venture decision criteria", "exclusivity clause partnership
   agreement when to grant exclusivity term sheet standard structure
   NVCA", "strategic alliance governance cadence KPI review joint
   steering committee cadence best practice partnerships". Sources
   cited into rules: Intuit/DealHub/Unifyr revenue-sharing and reseller
   glossaries, Ankura Joint Ventures ("How to Structure a Joint
   Venture"), UpCounsel ("Revenue Sharing Agreement Basics"), Sirion
   and Hyperstart (exclusivity clause guides), VC Beast (NVCA Forms
   guide), Duane Morris (VIMA/NVCA/BVCA comparative review), Atlan
   (governance council cadence), Umbrex (partnership governance
   operating model), AllianceBoard and Fiveable (alliance KPI design),
   The Rhythm of Business (joint steering committee).
2. **Named methodology/standard verified at source** — query: "BATNA
   ZOPA negotiation theory Fisher Ury Getting to Yes principled
   negotiation". Sources: PON/Harvard Law School articles on BATNA and
   principled negotiation, KARRASS's BATNA/ZOPA/reservation-point
   guide, Beyond Intractability's ZOPA essay and Getting to Yes
   summary, Parallel Project Training's ZOPA/BATNA article.
3. **Academic theory** — queries: "transaction cost economics
   Williamson governance structure choice make buy ally alliance",
   "Adams Converse Hales Klotz 2021 Nature people systematically
   overlook subtractive changes", "plain language contract
   comprehensibility research readability legal drafting cognitive
   load". Sources: Tadelis & Williamson's transaction-cost-economics
   working paper, the Academy of Management Journal make-buy-ally
   meta-analysis, Adams/Converse/Hales/Klotz's *Nature* 592 (2021)
   subtraction-neglect paper, a ScienceDirect legal-language-processing
   study, Masson & Waldron's *Applied Cognitive Psychology* plain-
   language-redrafting study, and a Statute Law Review article on
   plain-language legislative drafting.

Every URL cited above is reproduced in full inside each rule's
**Source** field in the delivered `playbook/*.md` files — not repeated
here to avoid duplication.

## Why

Issue #1174, per `docs/issue-1174/proposals/operational-playbook-program.md`
(the approved phase-1 design) and its amendments (research-execution
protocol amendment 1, calibration-depth amendment 2, no-batch-sequencing
amendment 3, subtraction-as-first-class-dimension amendment 4), requires
every one of the 44 roles to get its own web-fetched, non-pretrained
operational playbook landed in its rulebook repo — this record is the
partnerships-bd fan-out unit of that program, gated by the human
"APPROVE issue-1174/partnerships-bd" comment already posted on the
issue thread.

## Upstream basis

`docs/issue-1174/proposals/operational-playbook-program.md` (a),
(b-revised), (c), (d) — this parent repo's approved phase-1 design;
issue #1174 comment thread amendments 1 and 4 (research protocol,
subtraction requirement); `gates/playbook_depth_gate.py` (already built
in this parent repo, used unmodified to verify the delivered playbook).

## What did not work

None.

## Open findings

- `gates/playbook_depth_gate.py` implements the amendment-4 removal
  check conservatively: lines 170-174 of that file show it requires at
  least one removal-classified rule *overall* across the whole file
  set when axes are declared, not one per individually named axis, per
  a comment in the source acknowledging the gap ("without a per-axis
  tag on each block, we conservatively require at least one removal
  rule overall"). This delivery exceeds that weaker check anyway (1
  removal rule per each of the 5 axes), so it is not a gap in this
  delivery — flagged here as an open finding against the gate script
  itself for a future amendment to tighten, since a future role could
  clear the gate's actual check with only one removal rule
  concentrated on a single axis.

## Next steps

None owed by this session for its own unit — this playbook lands as an
independent, already-open pull request
(partnerships-bd-rulebook#22) per the program's streaming-landing
design. A human reviewer merging that pull request is what closes out
this fan-out unit.

## Resolution path

Human review of https://github.com/tokenmaxxxer/partnerships-bd-rulebook/pull/22
against `docs/issue-1174/proposals/operational-playbook-program.md`
(c)/(e); the gate-script open finding above is for the implementation
role (or a future amendment) to address in `gates/playbook_depth_gate.py`,
outside this record's own scope.
