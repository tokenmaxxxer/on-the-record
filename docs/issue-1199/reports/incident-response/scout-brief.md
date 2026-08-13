---
subject: issue-1199
role: incident-response
kind: scout-brief
---

# Scout brief: incident-response tool landscape (issue-1199)

Mode: parallel WebSearch fan-out, 4 angles in one turn (incident-
management/postmortem-platform comparison; on-call/paging adoption;
blameless-postmortem tool design; status-page/incident-communication
tool adoption), then one judge point, no further deepening (saturation:
the four angles covered every category the current-state survey's gap
line named; none introduced a fifth category needing a round-2 search).
1 sweep stage, 1 judge point, well under the 5-stage / 3-min budget.

## Category: incident-management / postmortem platforms

- **Rootly** — enterprise SRE-automation-heavy incident platform;
  workflow/trigger primitives model an org's exact process; automated
  postmortem generation with AI-drafted RCA and timeline auto-captured
  from Slack/Teams/Google Chat, per sources list below.
- **incident.io** — Slack-native incident tool, named the top pick for
  chat-first orgs across independent comparisons (sources list below);
  also the source of the action-item best-practice URL the current
  rulebook already cites as prose, never as a tool.
- **FireHydrant** — Freshworks (Freshservice) acquisition, $88.7M,
  reported effective 2026-01-01 per sources list below — an
  enterprise-market adoption signal distinct from stars/downloads.

Must-be (all three, per sources list below): auto-captured, timestamped
timeline built from the chat transcript itself, not hand-typed after
the fact.

## Category: on-call / paging

- **PagerDuty** — reported >28,000 customers as of 2024 per sources
  list below; standalone incident-management category leader;
  escalation-chain routing to service owners.
- **Opsgenie** — Atlassian-aligned (Jira-integrated), reported roughly
  half PagerDuty's price at comparable tiers per sources list below.

Must-be: severity/urgency drives escalation-chain shape, not a flat
notify-everyone default.

## Category: blameless-postmortem tool design (cross-cutting)

Pattern repeated across the Rootly/incident.io sources listed below:
(1) blameless framing so responders report truthfully, (2) automated
timeline capture removing manual reconstruction, (3) action items
created WITH owner + priority + due date + verification criteria inside
the same interface that later shows status pulled back from
Jira/Linear/Asana. Point 3 is a design move the current
`action-item-quality.md` axis states as a *rule* (owner+verb+outcome+
deadline) but never as something a tool structurally enforces by
refusing to let an item be created without those fields.

## Category: status-page / incident-communication (open source, real
adoption numbers)

- **Upptime** — 17.1k GitHub stars per sources list below;
  GitHub-Actions-native, serverless: scheduled checks open/close GitHub
  Issues on downtime, building a public incident history as a byproduct
  of the issue tracker itself rather than a separate authored document.
- **Cachet** — 15.2k GitHub stars per sources list below; traditional
  self-hosted status-page model (closer to Atlassian Statuspage's
  mental model).

Must-be: the incident record and the public communication artifact stay
structurally linked (Upptime: the same GitHub Issue) rather than
hand-copied between a postmortem doc and a status page.

## Judge point (saturation)

Four categories map onto the four decision surfaces the current axis
files already own (severity/on-call routing ~ severity-classification-
scoping; RCA/timeline capture ~ rca-method-selection +
timeline-construction; action-item structural enforcement ~
action-item-quality; blameless framing repeated independently across
several sources ~ blameless-language-editing). No fifth category
surfaced that the axis files don't already cover, so a second deepening
round would not change any adopt/skip call — stopped here.

## Adopt / skip

- **Adopt**: auto-timeline-capture discipline (Rootly/incident.io) →
  upgrades `timeline-construction.md`'s event-logging rule with a
  "capture at record time, not after" move.
- **Adopt**: severity-tiered escalation-chain shape (PagerDuty/Opsgenie)
  → upgrades `severity-classification-scoping.md`, currently silent on
  *who gets paged*, only on document depth.
- **Adopt**: structurally-enforced action-item fields (Rootly/
  incident.io pattern) → upgrades `action-item-quality.md`'s rule 1 from
  a prose shape check to a "treat a missing field as a blocking gap, the
  same way the tool refuses to let the item exist" framing.
- **Adopt**: issue-tracker-linked incident record (Upptime) →
  upgrades `timeline-construction.md`/`blameless-language-editing.md`
  with a link-don't-duplicate move between the postmortem doc and
  wherever the org already tracks the live incident.
- **Skip**: FireHydrant's specific UI, Rootly's specific workflow-
  primitive taxonomy, PagerDuty's specific escalation-policy schema —
  cloning any one vendor's exact model would violate the scout
  directive's never-clone-the-exemplar rule; only the design MOVE is
  adopted, not the product.

## Sources

```
https://rootly.com/sre/best-incident-management-platform-2026-rootly-vs-top-rivals-9eff7
https://pingfatigue.com/rootly-vs-firehydrant-vs-incident-io
https://rootly.com/sre/rootly-vs-firehydrant-alert-management-software-comparison
https://rootly.com/sre/ai-generated-postmortems-rootlys-automated-rca-tool
https://rootly.com/sre/rootly-automate-postmortems-action-item-tracking
https://incident.io/blog/why-do-post-mortem-action-items-fail-how-to-make-incident-follow-ups-actually-get-done
https://www.onpage.com/pagerduty-vs-opsgenie-vs-onpage-which-on-call-alerting-tool-is-right-for-your-team/
https://neubird.ai/blog/pagerduty-vs-opsgenie
https://github.com/upptime/upptime
https://oneuptime.com/blog/post/2026-04-14-self-hosted-status-page-comparison/view
https://www.openstatus.dev/guides/best-opensource-status-page-2026
```
