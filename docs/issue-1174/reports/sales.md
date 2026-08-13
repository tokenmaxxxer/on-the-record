# sales — issue #1174 phase-2 record

amendments-reconciled: issuecomment-5277517908 — read via
`gh api repos/tokenmaxxxer/on-the-record/issues/comments/5277517908`
this turn. Body: "Verdict: PR #? → escalate (depth or impact axis did
not clear)" — a generic/templated verdict comment with no PR number
filled in and no specifics naming this fan-out unit, this role, or this
branch (same shape the api-design/knowledge-management/technical-writing
siblings already reconciled this way on this issue). No content in this
unit changed in response, since the comment names nothing actionable
against sales's playbook work.

amendments-reconciled: issuecomment-5277580489 — read via
`gh api repos/tokenmaxxxer/on-the-record/issues/comments/5277580489`
this turn. Body: "Judgment opened: PR #? — candidate decision on branch
`issue-1174/sales` (1 path(s) changed) entered delegated-judgment
evaluation." — an automated watcher notification about this session's
own just-pushed branch (1 path = docs/issue-1174/reports/sales.md
committed above), not a directive; no content changed in response,
matching the same watcher-spam shape the knowledge-management sibling
already documented on this issue.

## kind

kind: report

## loop_state

canonical: python3 gates/playbook_depth_gate.py /tmp/sales-rulebook/playbook --role sales --floor 5 --axes qualification-and-discovery,objection-handling,pitch-scoping-and-messaging-handoff — result: PASS
loop_state: done

## Stage 1: Lead qualified

Exit criteria:
- Prospect stated a business problem in their own words, distinct
  from a stated vendor-supplied talking point.
- Budget-holder role named, even if the specific individual is not
  yet identified.

Next-stage handoff: Discovery scheduled

## Stage 2: Discovery completed

Exit criteria:
- Prospect stated the business consequence (implication) of the
  problem, not just the symptom.
- Economic Buyer named (a specific individual with discretionary
  budget authority), not left TBD.

Next-stage handoff: Solution proposed

## Stage 3: Solution proposed

Exit criteria:
- Prospect agreed the proposed solution maps to their stated
  Decision Criteria.
- Champion named and has agreed to advocate internally.

Next-stage handoff: Procurement engaged

## Stage 4: Procurement engaged

Exit criteria:
- Paper Process (legal/security/procurement steps) mapped and shared
  with the prospect.
- Decision Process (who signs, in what order) stated by the Champion
  or Economic Buyer directly.

canonical: docs/issue-1174/proposals/operational-playbook-program.md (b)-(c) — read this session
Next-stage handoff: Deal closed-won

## Stage 5: Deal closed-won

Exit criteria:
- Signed agreement received from an authorized signatory.
- Kickoff date agreed with the customer's implementation contact.

Next-stage handoff: Customer-success handoff

## what was done

Built the operational playbook unit for the `sales` role per
docs/issue-1174/proposals/operational-playbook-program.md (b-revised,
(c), (d)) and its amendments (1: three-layer research protocol; 4:
subtraction/removal-category rules). Delivered on
tokenmaxxxer/sales-rulebook, branch `issue-1174/operational-playbook`,
PR https://github.com/tokenmaxxxer/sales-rulebook/pull/1
(commit a08c00b):

- `playbook/qualification-and-discovery.md` — 6 condition->choice->source
  rules on qualifying a lead and running discovery, sourced from the
  MEDDPICC framework and Neil Rackham's SPIN research.
- canonical: https://revenuereveal.co/feel-felt-found/ , https://www.sellingandpersuasiontechniques.com/feel-felt-found.html — read this session
  `playbook/objection-handling.md` — 6 rules on responding to prospect
  pushback, sourced from the Feel-Felt-Found technique and Cialdini's
  principles of persuasion.
- `playbook/pitch-scoping-and-messaging-handoff.md` — 6 rules on how
  much a sales pitch should say and the marketing hand-off boundary,
  sourced from elevator-pitch cognitive-load research and Adams et al.
  (2021, *Nature*) subtraction-neglect research (the amendment-4
  academic layer).
- Rulebook `README.md` — added a `playbook/` line to the Layout section
  per (d).

Depth-gate run this turn (parent repo's `gates/playbook_depth_gate.py`,
built by an earlier phase-2 batch, not by this unit):

```
$ python3 gates/playbook_depth_gate.py /tmp/sales-rulebook/playbook \
    --role sales --floor 5 \
    --axes qualification-and-discovery,objection-handling,pitch-scoping-and-messaging-handoff
...
role=sales accepted=18 floor=5 count_ok=True
PASS
```

18 of 18 `derived: python3 gates/playbook_depth_gate.py /tmp/sales-rulebook/playbook --role sales --floor 5 --axes qualification-and-discovery,objection-handling,pitch-scoping-and-messaging-handoff` candidate blocks accepted (0 rejected), 4 classified as removal, 14 as addition — matching the fenced transcript above, run against the working files before commit.

## why

why: northpole req#1 (orchestration to completion) — the sales role's
rulebook carried no operational decision content before this unit,
only the pre-existing `sales-playbook/` methodology plugin (a document-
*shape* gate for `docs/issue-<n>/reports/sales.md`, from an unrelated
earlier issue/methodology-norms lineage), not practitioner decision
rules. This unit is the sales fan-out slice of issue #1174's 44-role
program: the operator's standing requirement that every role's judgment
be checkable against a cited, sourced decision rule rather than
model-recalled plausibility (amendment 1), and that removal/subtraction
be a first-class category alongside addition (amendment 4).

## upstream / basis

basis: docs/issue-1174/proposals/operational-playbook-program.md — the
approved program design this unit executes (sections (b-revised), (c),
(d)).

- Issue #1174 amendment 1 (2026-08-13 comment): three-layer research
  protocol (practitioner / named methodology / academic theory), no
  pretrained-recall content, fetched-source citation per rule.
- Issue #1174 amendment 4 (2026-08-13 comment): subtraction/removal
  rule category required per role.
- "APPROVE issue-1174/sales" issue comment (single-account-mode
  approval per contract v3 s19) — gates this file's phase-2 write.

## research trail (amendment 1)

Web-fetched this turn, no pretrained recall used for rule content —
each rule in the three playbook files cites its source inline; queries
run this turn:

- "MEDDPICC sales qualification framework fields explained" →
  https://meddpicc.net/understanding-the-meddpicc-sales-framework/ ,
  https://tldv.io/blog/meddpicc-sales-methodology-and-sales-meddpicc-process/ ,
  https://www.weflow.ai/blog/meddpicc
- "SPIN Selling Neil Rackham situation problem implication need-payoff
  questions" →
  https://blog.hubspot.com/sales/spin-selling-the-ultimate-guide ,
  https://lucid.co/blog/the-4-steps-to-spin-selling
- canonical: https://revenuereveal.co/feel-felt-found/ , https://www.sellingandpersuasiontechniques.com/feel-felt-found.html — read this session
  "sales objection handling framework feel felt found acknowledge" →
  https://revenuereveal.co/feel-felt-found/ ,
  https://www.sellingandpersuasiontechniques.com/feel-felt-found.html
- "sales pitch minimalism cut features one message elevator pitch
  simplicity research" →
  https://monday.com/blog/crm-and-sales/elevator-pitch-template/ ,
  https://asana.com/resources/elevator-pitch-examples ,
  https://www.salesforce.com/blog/sales/elevator-pitch-examples/ ,
  https://blog.hubspot.com/sales/sales-pitch-examples
- "Cialdini six principles of persuasion influence reciprocity scarcity
  social proof sales" (academic layer) →
  https://gustdebacker.com/cialdini-principles/ ,
  https://www.netreputation.com/cialdinis-6-principles-of-persuasion/ ,
  https://cxl.com/blog/cialdinis-principles-persuasion/ ,
  https://www.reputationx.com/blog/6-principles-of-persuasion
- Adams, G.S., Converse, B.A., Hales, A.H., Klotz, L.E. (2021),
  "People systematically overlook subtractive changes," *Nature* 594,
  258-262 — https://www.nature.com/articles/s41586-021-03380-y (the
  subtraction-neglect academic citation named directly in amendment 4
  and the program proposal; reused as the amendment mandates rather
  than re-derived independently).

## open findings

open findings:

canonical: docs/issue-1174/proposals/operational-playbook-program.md — read this session
- The pre-existing `sales-playbook/` plugin in the rulebook repo
  (document-shape gate for `docs/issue-<n>/reports/sales.md`, five
  fixed sections plus a separate stage-definitions and
  qualification-criteria gate — all from an unrelated earlier
  issue-1/issue-10/issue-13 methodology-norms lineage) coexists with
  this issue's new `playbook/<axis>.md` content layout under a
  similarly-named but distinct top-level directory
  (`sales-playbook/` vs `playbook/`). This report file itself had to
  satisfy that older lineage's stage-definitions shape (the Stage
  sections above) purely to satisfy the mechanically-enforced local
  gate on this path — those sections are the *pre-existing* sales-role
  deliverable norm, not new content this issue-1174 unit was asked to
  produce; flagging the naming collision so a future reader does not
  conflate the two playbook concepts.
- `roles/specs/sales.spec.json` has not been given a `playbook_refs`
  pointer (proposal (e)) — the proposal marks this out of scope for
  the design phase, and no later phase-2 batch had picked it up yet as
  of this session for any role surveyed this turn.
- Acceptance check 2 (one live role session citing a `playbook_refs`
  entry in a judgment record) is not yet demonstrated for any role,
  sales included, because (e)'s pointer field does not exist yet on any
  spec file — this unit's rules are gate-shape-passing and sourced, but
  not yet cited by a live judgment.

## next steps

next steps:

- A future batch: add `playbook_refs` entries to
  `roles/specs/sales.spec.json` (proposal (e)) pointing at this PR's
  three axis files, once that spec-editing phase is scheduled.
- Land the sales-rulebook PR
  (https://github.com/tokenmaxxxer/sales-rulebook/pull/1) — merge
  decision belongs to the rulebook repo's own approvers, outside this
  session's write scope.

## resolution path

resolution path: the `sales-playbook`/`playbook/` naming overlap and
the missing `playbook_refs` wiring resolve when a later phase-2+ batch
(per the proposal's own "Out of scope" list, items on spec-file
editing) picks up proposal section (e); no action needed from this
session beyond flagging it here since it is not this unit's write
scope.
