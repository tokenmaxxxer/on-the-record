kind: report
subject: issue-1199
doc-type: reference

# customer-support — issue #1199 scout brief

canonical: this turn's tool transcript — four WebSearch calls dispatched in one message (Zendesk, Intercom, KCS/Consortium, Nicereply/Delighted queries)
Stages used: 1 sweep (4 parallel WebSearch angles), 0 deepening rounds.
Judge point 1: strong cross-angle agreement — each tool/methodology is
the named category leader with multi-source adoption evidence, aimed
at the four gaps `survey.md` (this issue) named. Judge point 2:
another round would not change any build decision (the four gaps
already have a clear design-move answer each), so deepening stopped
after the sweep. Mode: parallel (four WebSearch calls dispatched in
one turn).

## Sweep angle 1 — ticketing/help-desk platforms (Zendesk)

Zendesk holds roughly 28% help-desk-software market share and is used
by 100,000+ companies; Freshdesk (~18%) and Salesforce Service Cloud
(~20%) are the next-largest category peers. Category must-be: a
support scenario is never "just a script" — the platform bundles the
response text with structured ticket actions (tags, priority set, a
named macro id) as one atomic unit, so any agent hitting the same
trigger reproduces the same resolution instead of re-composing it.
Sources:
- https://expandedramblings.com/index.php/zendesk-facts-and-statistics/
- https://sqmagazine.co.uk/zendesk-statistics/

## Sweep angle 2 — live chat / messaging deflection (Intercom)

Intercom's Fin agent resolves roughly 66% of customer questions
automatically before any human agent touches the ticket, with that
rate reported as still climbing. Category must-be: a defined
automated-deflection step precedes human triage as its own tier, with
its own resolution-rate signal tracked apart from human-tier
resolution — not folded into a single blended "L1" number.
Sources:
- https://research.com/software/reviews/intercom
- https://greetnow.com/blog/live-chat-statistics

## Sweep angle 3 — KCS methodology / Consortium for Service Innovation

The Consortium for Service Innovation is KCS's sole certifying body;
adopting organizations report up to 50% improved first-resolution time
within 3-9 months, and a recurring practice across cited adopters
(Autodesk, Dell, HP Enterprise, Salesforce, others) is the "Evolve
Loop" — search/reuse an existing article before drafting a new
resolution, then flag it for update only when no match exists.
Category must-be: reuse-before-create is a named playbook step, not an
implicit expectation.
Sources:
- https://invgate.com/itsm/knowledge-management/kcs
- https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Adoption_Guide/000_Introduction/020_KCS_Benefits

## Sweep angle 4 — CSAT/NPS survey tooling (Nicereply / Delighted)

Nicereply's category-distinguishing design move (vs. Delighted's
generic periodic NPS/CSAT sends) is embedding a one-click survey
directly into the support workflow at ticket close, tying the score
back to the specific ticket and, by extension, the agent/scenario that
produced it. Category must-be: a CSAT score is meaningful only when
attributable to the specific resolution path that preceded it — a
score collected in a later, disconnected batch send cannot be traced
back to which script/escalation path earned it.
Sources:
- https://www.zigpoll.com/content/nicereply-vs-delighted-features-pricing-verdict
- https://www.nicereply.com/more/delighted-vs-nicereply

## Adopt / skip

Adopt: (1) bundle each playbook scenario's script with structured
ticket actions (tag/priority/macro id); (2) add a pre-L1 self-serve/
deflection escalation tier (L0) with its own named owner and timeout,
tracked separately from L1-L3; (3) a reuse-before-drafting step ahead
of scenario authoring; (4) tie `csat_score`'s survey trigger to ticket
close and require `resolution_summary` to name the resolving scenario
for later attribution.

Skip: adopting KCS's full certification/training program, Zendesk's
or Intercom's actual product surface (routing UI, bot-confidence
scoring internals), and Nicereply's specific survey-channel mechanics
(email/SMS/in-app) — those are vendor implementation detail, not a
methodology gap this single-operator rulebook needs to encode.

Gap line: the current handbook already meets the field's SLA-tiering
and escalation-ownership must-bes (§1/§2's Impact×Urgency derivation
and named-owner/timeout escalation rows already match the category
norm); what it was missing is the four items adopted above — a
pre-human deflection tier, action/script bundling, reuse-before-create,
and close-time CSAT attribution.
