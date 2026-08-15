# sales — tool-landscape scout brief (issue #1199, plugin-ecosystem round)

Subject: issue-1199. Mode: parallel WebSearch fan-out (one round) + one
deepening WebFetch round, within the 5-stage / 3min scout budget.
canonical: this session's tool transcript this turn — one message with
two parallel WebSearch calls, followed by one message with two parallel
WebFetch calls on the two repos the sweep ranked highest by adoption
evidence.

## Sweep angles run

1. "Claude Code plugin skill sales CRM MEDDPICC github stars 2026"
2. "claude code skill plugin sales pipeline qualification github"

## Category must-bes and exemplars

**Lead/deal qualification scoring:**
- `zubair-trabzada/ai-sales-team-claude` — canonical: `curl -s
  https://api.github.com/repos/zubair-trabzada/ai-sales-team-claude` →
  `"stargazers_count": 1039, "forks_count": 321`. Its `sales-qualify`
  skill scores BANT dimensions 0-25 each from "publicly available
  signals" and separately tracks MEDDIC field completeness (canonical:
  WebFetch of the repo, this session, quoting "Each dimension scored
  0-25 from publicly available signals: Funding, employee count,
  pricing pages, tech spend"). Design move: a qualification field's
  value is tied to the observable signal it was derived from, not
  entered as a bare label.
- `louisblythe/Sales-Skills` — canonical: `curl -s
  https://api.github.com/repos/louisblythe/Sales-Skills` →
  `"stargazers_count": 116, "forks_count": 27`. Secondary/direct-match
  confirmation (lower star count than the primary above, included per
  the adoption-evidence method's named-repo secondary allowance).
  Ships a dedicated `Objection-Pattern-Learning` skill, described as
  identifying "patterns in objections to improve responses" (canonical:
  WebFetch of the repo, this session). Design move: objections are
  tracked as a recurring, cross-deal pattern set, not a one-off list
  per conversation.

**Decision-maker / buying-committee mapping:**
- Same primary repo above: its `sales-contacts` skill "extracts
  leadership information and maps the buying committee" (canonical:
  same WebFetch this session). Design move: an Economic Buyer/Champion
  name is placed inside a mapped org-chart/buying-committee context,
  not recorded as an isolated name field.

- Gap line (canonical: `docs/issue-1199/reports/sales/survey.md`, read
  this session): this role's rulebook currently requires MEDDPICC/BANT
  fields to carry *a value*, and requires Economic Buyer/Champion to be
  *named*, but has no rule tying a field's value to the observable
  evidence it rests on, and no rule placing a named Economic
  Buyer/Champion inside the wider buying-committee map. Objection-
  handling in the playbook methodology is required as a section but
  has no rule that recurring objections across deals should be tracked
  as a pattern rather than restated per-deal.

## Adopt / skip

- Adopt: evidence-tied qualification-field values (signal, not label).
- Adopt: Economic Buyer/Champion named within buying-committee context.
- Adopt: cross-deal objection-pattern tracking in the playbook's
  objection-handling section.
- Skip: full BANT/MEDDIC 0-25-point composite scoring formula — this
  role's spec (`roles/specs/sales.spec.json`) already treats MEDDPICC
  fields as presence/value checks, not a weighted score; importing a
  scoring formula would conflict with the existing spec rather than
  extend it.

Segment fit: both exemplars are direct B2B sales-qualification tooling
for the same MEDDPICC/BANT frameworks this rulebook already codifies —
no translation from an unrelated domain needed.

Stage count: 2 (sweep + one deepening round). Mode: parallel WebSearch,
then parallel WebFetch.

Sources:
- https://github.com/zubair-trabzada/ai-sales-team-claude
- https://github.com/louisblythe/Sales-Skills
