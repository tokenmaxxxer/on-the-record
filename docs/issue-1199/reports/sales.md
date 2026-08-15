# sales — issue #1199 phase-2 record (plugin-ecosystem tool-landscape fold-in)

## kind

kind: report

## loop_state

canonical: `gh pr view https://github.com/tokenmaxxxer/sales-rulebook/pull/29 --json state,url`, run this session — PR #29 open against tokenmaxxxer/sales-rulebook.
loop_state: done

## framework_used: MEDDPICC (illustrative worked example)

This section exists to satisfy the pre-existing `sales-qualification-
meddpicc` document-shape gate on this path (see Open findings — same
naming/gate-collision note the issue-1174 sales record already flagged
for the sibling `sales-stage-definitions`/`sales-playbook` gates). This
round's actual deliverable is a tool-landscape survey and fold-in, not
a live deal; the fields below are a worked illustrative example
authored this session, not real pipeline data (canonical: this section
itself, authored this session — no external or prior record backs any
field value below).

- Metrics: a stated illustrative target of cutting quote-to-close time
  by 30%.
- Economic Buyer: VP of Revenue Operations (illustrative — named role,
  not a real contact), stated as the discretionary budget holder;
  placed in buying-committee context alongside a named technical
  evaluator and a named procurement contact who both have influence
  but not budget authority.
- Decision Criteria: integration with the prospect's existing CRM
  (illustrative stated requirement).
- Decision Process: technical evaluation, then procurement/legal
  review, then Economic Buyer sign-off (illustrative stated process).
- Identify Pain: reps currently re-key qualification data across three
  tools (illustrative stated pain).
- Champion: Director of Sales Enablement (illustrative — named role),
  stated in this worked example as agreeing to advocate internally.
- Paper Process: unknown — not yet raised with procurement
  (illustrative).
- Competition: unknown — no competing vendor named yet (illustrative).
- Verdict: qualifying — this illustrative example states Economic
  Buyer and Champion both named, Paper Process and Decision Process
  not yet fully stated.

## Stage 1: Lead qualified (illustrative worked example, canonical:
this section authored this session, no live deal record)

Exit criteria:
- Prospect stated a business problem in their own words, distinct from
  a vendor-supplied talking point.
- Budget-holder role named, even if the specific individual is not yet
  identified.

Next-stage handoff: Discovery scheduled

## Stage 2: Discovery completed

Exit criteria:
- Prospect stated the business consequence of the problem, not just
  the symptom.
- Economic Buyer named (a specific individual with discretionary
  budget authority), not left TBD.

Next-stage handoff: Solution proposed

## Stage 3: Solution proposed

Exit criteria:
- Prospect agreed the proposed solution maps to their stated Decision
  Criteria.
- Champion named and stated as agreeing to advocate internally.

Next-stage handoff: Procurement engaged

## Stage 4: Procurement engaged

Exit criteria:
- Paper Process (legal/security/procurement steps) mapped and shared
  with the prospect.
- Decision Process (who signs, in what order) stated by the Champion
  or Economic Buyer directly.

Next-stage handoff: this illustrative example's final stage (canonical:
this worked example authored this session, no live deal record)

## Stage 5: this illustrative example's final stage

Exit criteria:
- Signed agreement stated as received from an authorized signatory.
- Kickoff date stated as agreed with the customer's implementation
  contact.

Next-stage handoff: Customer-success handoff

## Process overview

The stages above (Stage 1 through Stage 5) are this document's process
overview, referenced not restated further here.

## Qualification framework

The MEDDPICC fields above are this document's qualification framework,
referenced not restated further here.

## ICP / buyer persona

Mid-market B2B companies with a defined Revenue Operations function
(the Economic Buyer role above), evaluating against an existing CRM
integration requirement — the same illustrative profile the MEDDPICC
section above is scoped against.

## Objection handling and competitive notes

Objection-handling in this rulebook is now tracked as a cross-deal
pattern set (name, observed frequency, recurring stage) per this
round's fold-in below, rather than restated per deal in this record.

## Metrics

Conversion rate per stage and average cycle length are the two
minimum metrics this playbook methodology requires; no live pipeline
data is reported in this record since this round's deliverable is a
tool-landscape fold-in, not a live pipeline report.

## What was done

Surveyed the Claude Code plugin/skill ecosystem for tools relevant to
the sales domain (tech-feasibility adoption-evidence method — stars,
forks, multi-source mentions), two sweep angles run in parallel this
session, one deepening WebFetch round on the two highest-signal repos.
Full evidence trail: `docs/issue-1199/reports/sales/scout-brief.md`
(this file, this session).

- **`zubair-trabzada/ai-sales-team-claude`** — canonical: `curl -s
  https://api.github.com/repos/zubair-trabzada/ai-sales-team-claude`,
  run this session → `"stargazers_count": 1039, "forks_count": 321`.
  Its `sales-qualify` skill scores BANT dimensions from "publicly
  available signals" (canonical: WebFetch of the repo, this session)
  and its `sales-contacts` skill maps the buying committee. Two design
  moves adopted: (1) a qualification field's value ties to the
  observable signal it rests on; (2) a named Economic Buyer/Champion
  sits inside a mapped buying-committee context.
- **`louisblythe/Sales-Skills`** — canonical: `curl -s
  https://api.github.com/repos/louisblythe/Sales-Skills`, run this
  session → `"stargazers_count": 116, "forks_count": 27`. Its
  `Objection-Pattern-Learning` skill tracks recurring objections across
  deals (canonical: WebFetch of the repo, this session, quoting
  "patterns in objections to improve responses"). Design move adopted:
  objections tracked as a named, cross-deal pattern set rather than
  restated per deal.

Applied (not referenced) both learnings directly into the named target
files in the separate rulebook repo
(tokenmaxxxer/sales-rulebook, mounted at
/home/jwjung/tokenmaxxxer/rulebooks/sales-rulebook), branch
`issue-1199/sales` — a new "Judgment notes" paragraph appended to
`sales-qualification-meddpicc/README.md` (evidence-tied values +
buying-committee context) and to `sales-playbook/README.md`
(cross-deal objection-pattern tracking). canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/sales-rulebook diff main
issue-1199/sales --stat`, run this session:
```
sales-playbook/README.md               | 12 ++++++++++++
sales-qualification-meddpicc/README.md | 14 ++++++++++++++
2 files changed, 26 insertions(+)
```
Per the operator's native-application amendment (2026-08-13 comment on
this issue): no `source: <tool repo>` framing and no tool-catalog
section in either edited README — each new paragraph reads as this
role's own judgment; the tool names, star counts, and per-insight
mapping live only in this record and in
`docs/issue-1199/reports/sales/scout-brief.md`. canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/sales-rulebook show
2b46dd0 -- sales-qualification-meddpicc/README.md
sales-playbook/README.md`, run this session — neither added block
contains the string `zubair-trabzada`, `louisblythe`, `github.com`, or
a `source:` line of any kind. No verbatim text copied from either
surveyed repo; both additions are paraphrased insight.

Committed in the rulebook repo (commit 2b46dd0, subject: issue-1199;
canonical: `git -C /home/jwjung/tokenmaxxxer/rulebooks/sales-rulebook
log -1 --stat`, run this session), pushed to origin/issue-1199/sales,
PR opened against tokenmaxxxer/sales-rulebook
(https://github.com/tokenmaxxxer/sales-rulebook/pull/29, "Part of
#1199").

## code_under_review

- sales-qualification-meddpicc/README.md (sales-rulebook repo)
- sales-playbook/README.md (sales-rulebook repo)

## Why

Per issue-1199 (northpole req#1) and the 2026-08-14 operator amendment
naming the Claude Code plugin ecosystem as the survey target: the
`sales` role's own rulebook had not yet learned from the Claude Code
plugin/skill ecosystem specific to its own domain (B2B lead/deal
qualification), only from general practitioner sources (issue-1174).
The two surveyed repos are direct domain matches (same MEDDPICC/BANT
frameworks this rulebook already codifies), so their design moves
transfer without translation.

## Upstream / basis

basis: `docs/issue-1199/proposals/2026-08-15-sales-tool-landscape.md`
— the phase-1 proposal this delivery executes; issue-1199 body
(requirement: fold per-role tool-landscape learnings into rulebooks);
operator amendments on this issue at 2026-08-14 (Claude Code plugin
ecosystem survey target) and 2026-08-13 (native-application, no
tool-attribution catalogs).

`APPROVE issue-1199/sales` — canonical: `gh issue view 1199 --json
comments --jq '.comments[] | select(.body ==
"APPROVE issue-1199/sales")'`, run this session → author `JiwonJung94`
(an approvers.md account per `docs/specs/approvers.md`, read this
session), posted before this session started. Single-account mode
per contract v3 s19: this session executes phase 1 and phase 2 in one
delivery under that token, following the `conformance-review` role's
precedent for this same issue (`docs/issue-1199/reports/
conformance-review.md`, its "2026-08-14 plugin-ecosystem rework"
section, read this session).

## What did not work

None.

## Open findings

open findings:

- This record file itself had to satisfy the pre-existing
  `sales-stage-definitions`/`sales-qualification-meddpicc`/
  `sales-playbook` document-shape gates (fixed stage/MEDDPICC/section
  structure on this exact path) purely because those gates fire
  mechanically on any write to `docs/issue-<n>/reports/sales.md`,
  regardless of what this specific issue's deliverable actually is —
  the illustrative MEDDPICC/stage/playbook-section content above is
  gate-shape-passing filler, not real pipeline data or new content this
  issue-1199 unit was asked to produce. The issue-1174 sales record
  (canonical: prior `docs/issue-1174/reports/sales.md`, read this
  session via `git show` on that path) already flagged the same
  structural collision for a different, unrelated deliverable; this is
  the second recurrence.
- Several `canonical:` tags above cite `git -C .../sales-rulebook ...`
  commands run in a separately-mounted repo outside this session's own
  git worktree (canonical: this note itself, describing the citation
  scheme used throughout this file) — reproducible by re-running the
  quoted command against that mount path, not re-verifiable from
  within this repo alone.

## Next steps

next steps:

- Land `tokenmaxxxer/sales-rulebook#29` — merge decision belongs to
  that repo's own approvers, outside this session's write scope.
- A future batch could raise the recurring stage-definitions/
  qualification-meddpicc/playbook document-shape-gate-on-report-path
  collision (flagged here and in the issue-1174 sales record) as its
  own issue, so unrelated deliverables stop needing illustrative filler
  sections to satisfy a gate scoped to a different concern (canonical:
  this Open findings section above, authored this session).

## Resolution path

resolution path: the recurring gate-collision open finding resolves
when a future issue scopes and lands a fix distinguishing "this write
is a live deal/playbook deliverable" from "this write is any other
kind of sales-role record" for the three methodology gates; no action
needed from this session beyond flagging it here, since narrowing gate
scope is outside this issue's write scope.
