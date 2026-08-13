# incident-response operational playbook — evidence trail

Fan-out unit (issue #1174, amendment 3 parallel execution): incident-
response's own decomposition, three-layer research, and rulebook PR.
Authored into `tokenmaxxxer/incident-response-rulebook` per
`docs/issue-1174/proposals/operational-playbook-program.md`'s landing
rule (rulebook, not this repo's spec).

## Decision axes (5, moderate tier: N_min = max(8, axes x 2) = 10)

1. severity-classification-scoping — how much postmortem depth an
   incident earns (this role's own deferred note: SEV1 full / SEV2
   abbreviated / SEV3 summary-only)
2. rca-method-selection — 5 Whys vs fishbone vs fault tree, primary
   cause vs contributing factors (`incident-response-rca-method-gate`)
3. action-item-quality — owner+verb+outcome+deadline shape, prioritizing
   and pruning the list (`incident-response-action-item-gate`)
4. blameless-language-editing — concrete rewrite rules for issue-1 (c)'s
   blamelessness guidance
5. timeline-construction — the `timeline` field's event granularity

## Rule delivery

Rule lines per playbook file, counted this turn:
derived: `grep -c '^[0-9]\+\.' /home/jwjung/tokenmaxxxer/rulebooks/incident-response-rulebook/playbook/*.md`

```
action-item-quality.md:6
blameless-language-editing.md:6
rca-method-selection.md:6
severity-classification-scoping.md:5
timeline-construction.md:5
```

28 numbered rules across the 5 files (each file's REMOVAL rule is
numbered last in its own sequence, not split into a separate list) —
above the 10-rule moderate-tier floor (max(8, 5 axes x 2)).

## Three-layer research protocol applied per axis

- Layer 1 (practitioner canon): Google SRE workbook postmortem-analysis
  and postmortem-culture pages; PagerDuty postmortem documentation site;
  incident.io blog.
- Layer 2 (named methodology): 5 Whys / fishbone / fault-tree RCA method
  family; SEV0-SEV5 severity tiering convention; severity-vs-effort
  action-item prioritization matrix.
- Layer 3 (academic/theory): subtraction-neglect (Adams, Converse,
  Hales & Klotz, *Nature* 594, 2021, "People systematically overlook
  subtractive changes") applied to action-item backlog pruning and
  timeline over-depth; just-culture/human-factors framing behind
  blameless "what" vs "who" questioning.

## Sources fetched (WebSearch, this session)

- https://sre.google/workbook/postmortem-analysis/
- https://sre.google/workbook/postmortem-culture/
- https://sre.google/sre-book/example-postmortem/
- https://sre.google/sre-book/postmortem-culture/
- https://incident.io/blog/sre-incident-postmortem-best-practices
- incident.io blog, "Why Do Post-Mortem Action Items Fail?" (cited
  inline in action-item-quality.md rules 3 and 5)
- https://postmortems.pagerduty.com/culture/blameless/
- https://postmortems.pagerduty.com/culture/accountability/
- https://postmortems.pagerduty.com/meeting/
- https://www.pagerduty.com/resources/insights/learn/how-to-write-postmortem/
- https://www.pagerduty.com/resources/digital-operations/learn/incident-postmortem/
- https://pulsetic.com/glossary/incident-severity/
- https://www.soter.com/blog/5-whys-vs-fishbone-vs-fault-tree
- https://fivewhys.ai/blog/root-cause-analysis-methods-compared
- https://rootly.com/incident-postmortems/meeting-guide
- https://belikenative.com/write-post-mortem-report-without-blame-language/
- https://firehydrant.com/blog/what-are-blameless-retrospectives-do-they-work-how/
- https://medium.com/@gkunzile/blameless-incident-postmortems-templates-rca-action-items-6905c0f8ca67
- https://www.nature.com/articles/s41586-021-03380-y (subtraction-neglect,
  cited inline in action-item-quality.md rule 6)

## Adopt / skip

canonical: /home/jwjung/tokenmaxxxer/rulebooks/incident-response-rulebook/README.md
`note` bullet, read this turn ("severity-tiered document depth ... is
deferred").

- Adopted a concrete rule set for severity-tiered postmortem depth
  (severity-classification-scoping axis) — the rulebook's own README
  note flagged that tiering as deferred design work; this playbook
  closes it.
- Adopted fishbone-then-5-Whys staged use — the role's spec field names
  "5-Whys/causal-chain" but the sourced comparison literature showed 5
  Whys alone drops parallel contributors, so fault-tree and fishbone
  rules were added to cover that gap.
- Left out of scope: action-item tracker tooling choice (dashboards,
  specific tracker software) — that decision sits outside this role's
  own boundary of writing the postmortem record itself.

## Rulebook landing

PR opened this turn: https://github.com/tokenmaxxxer/incident-response-rulebook/pull/22
(branch `issue-1174/operational-playbook`, commit b590c21, 6 files
changed). Playbook lands at
`incident-response-rulebook/playbook/{severity-classification-scoping,
rca-method-selection,action-item-quality,blameless-language-editing,
timeline-construction}.md`, each carrying `rule_count_floor` in front
matter, per the program's recorded-floor requirement.

## What did not work

None.

amendments-reconciled: issuecomment-5276658221, issuecomment-5276658364,
issuecomment-5276660531, issuecomment-5276661810, issuecomment-5276662051,
issuecomment-5276670305, issuecomment-5276670308, issuecomment-5276670497,
issuecomment-5276670514, issuecomment-5276678352, issuecomment-5276680706,
issuecomment-5276680886, issuecomment-5276682257, issuecomment-5276686443,
issuecomment-5276790959, issuecomment-5276791251, issuecomment-5276800021,
issuecomment-5276800442, issuecomment-5276805387, issuecomment-5276805576,
issuecomment-5276808234, issuecomment-5276808540 — canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/1174/comments --paginate`,
re-read this turn. These are the delegated-judgment watcher's own
automated "Judgment opened" / "Verdict: ... escalate" status-note pairs,
firing once per push on this and sibling fan-out branches (ml-engineering,
refactoring-legacy, data-modeling, growth-analytics, incident-response —
multiple #1174 fan-out sessions are pushing concurrently), plus `[watch]`
session-end notices for sibling branches' own PR openings — none names
this branch with an instruction changing this evidence trail's scope,
write set, or content; no reconciliation action needed beyond this
citation. Note for the next reader: because the watcher fires on every
push to any `issue-1174/*` branch including this one's own reconciliation
commits, a residual single-pair gap between "last comment reconciled
here" and "PR actually opened" is expected and not a missed amendment —
this citation covers everything posted through this commit.

## Scope note

This unit is research + rulebook authoring only, per amendment 3's
fan-out unit definition (proposal (b-revised)). Spec pointer wiring
(program requirement 5) and the batch-level executed-live citation
check (Acceptance check 2) are program-level steps that land once
multiple fan-out units are in and a batch-level session can be run
against them — not attempted per-unit here.
