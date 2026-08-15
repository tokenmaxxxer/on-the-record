---
subject: issue-1199
role: issue-retrospective
kind: scout-brief
loop_state: gathering
---

# Scout brief: incident-postmortem tooling (issue-1199, issue-retrospective unit)

Mode: 3 parallel WebSearch angles, one round (sweep), plus one
snowball-deepening round on the strongest overlap hit — 2 stages total,
well under the 5-stage/3min budget; stopped at judge point 2 (further
rounds would not have changed a build decision — the three angles
already converged on the same three moves).

## Category must-bes (what the strong hits assume)

- Automated/immutable timeline capture during the incident, not
  reconstructed afterward — PagerDuty and incident.io both build the
  timeline from tool/chat activity as it happens; incident.io reports
  this can cut postmortem-authoring time 75-83%.
- Action items with a named owner, due date, and an automatic
  tracker-ticket link (incident.io auto-creates Jira/Linear tickets
  from follow-up actions).
- A forward-built timeline, explicitly ordered from before the incident
  toward resolution, not backward from the known outcome — named
  directly by PagerDuty's own postmortem documentation as a hindsight-
  bias guard.
- Contributing-factors framing over "root cause," and a stated
  separation between the narrative "what we learned" and the
  "what we're doing about it" action-item list — the Jeli/PagerDuty
  Howie guide's stated design move, at the sociotechnical-systems level.

## Performance axes the field competes on

1. How much of the timeline is captured live vs. reconstructed by
   memory after the fact.
2. Whether action items close the loop into a real tracker or stay
   prose-only.
3. Whether "learning" and "action item" are kept as visibly distinct
   record sections or blurred into one bullet list.

## Adopt / skip

- Adopt: forward-chronological timeline construction as an explicit
  hindsight-bias guard; prefer the earliest-timestamped record entry
  when two records disagree on when something happened.
- Adopt: keep the learning narrative distinct from the action-item
  list (Howie's framing), and require each action item to name how its
  completion would be verified.
- Skip: automated live-capture and tracker-ticket integration
  themselves — this role's contract is explicitly records-only
  (reads other roles' already-written records, never a live system),
  so "capture during the incident" has no analog here; noted as a gap
  the tooling field assumes that this role's own contract structurally
  cannot adopt (see Gap line).

## Gap line

The field's core must-be — live/automated timeline capture — does not
apply to this role: its contract already forbids opening any non-record
source to verify a claim (records-only). What the survey *can* adopt is
the ordering discipline (forward-from-earliest, not backward-from-
outcome) and the learning/action-item separation, both of which are
about how the already-written records get read and organized, not about
capturing new data.

## Segment fit

One line: this role retrospects on other roles' written records inside
one issue's history, not live incidents with paging/on-call tooling —
so the fit is with the postmortem *methodology* layer (Howie's
narrative-over-checklist framing, PagerDuty's ordering discipline), not
with the paging/automation layer (incident.io's live-capture
automation), which the Gap line above already explains is structurally
inapplicable.

Stages used: 2 (sweep + one deepening round on the Jeli/Howie hit,
which the sweep's three angles converged on). Mode: parallel (three
WebSearch calls issued in one turn).

## Sources

- https://webflow.rootly.com/blog/best-incident-postmortem-software-2026
- https://incident.io/blog/post-mortem-automation-incident-management
- https://docs.incident.io/post-incident/postmortems-overview
- https://www.pagerduty.com/blog/better-incident-post-mortems/
- https://postmortems.pagerduty.com/meeting/
- https://postmortems.pagerduty.com/how_to_write/writing/
- https://response.pagerduty.com/after/post_mortem_process/
- https://howie-guide.pagerduty.com/
- https://howie-guide.pagerduty.com/analyze/
- https://www.pagerduty.com/platform/jeli/
