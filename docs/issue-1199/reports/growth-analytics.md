---
subject: issue-1199
role: growth-analytics
kind: record
loop_state: landed
---

# Record: growth-analytics tool-landscape fold-in (issue-1199)

## What was done
Executed the phase-2 fold-in approved by the `APPROVE
issue-1199/growth-analytics` comment on this issue (single-account mode;
canonical: `gh issue view 1199 --comments`, read this session — a
trailing comment body exactly matching `APPROVE
issue-1199/growth-analytics`).

Ran the adoption-evidence tool-landscape survey covering the domain's
real tool categories: open-source variant-testing/feature-flag
platforms, open-source product analytics, warehouse-native statistics
engines, and hosted product-analytics platforms. Per-tool table below.
Sweep mode: batched-sequential fallback, stated per the scout directive
— the GrowthBook, PostHog, and Eppo angles ran as parallel WebSearch
calls in one turn (canonical: this session's own tool-call transcript —
the three WebSearch invocations issued together earlier in this turn),
then the Amplitude/Mixpanel angle ran as one follow-up call after
reading those three results, since the result needed to be read before
deciding a fourth angle was still needed (saturation check: the first
three angles already gave non-overlapping design moves, so the fourth
targeted the one still-missing category — hosted platforms — rather
than re-covering ground).

Applied the resulting design-move learnings directly into
tokenmaxxxer/growth-analytics-rulebook (mounted at
/home/jwjung/tokenmaxxxer/rulebooks/growth-analytics-rulebook), off
main at commit fe9263a as of this session — no rulebook branch existed
yet for issue-1199, so work landed on a new `issue-1199/growth-analytics`
rulebook branch:

- `ga-trust/agents/trust-gate-walker.md`, step 1: renamed "SRM check" to
  "SRM check + exposure integrity" and added a requirement to also ask
  whether any unit was exposed to more than one variant (cross-arm
  contamination), treating a detected multiple-exposure rate above
  tolerance as a hard-stop the same as a detected SRM.
- `ga-funnel/agents/funnel-localizer.md`, step 3 (segment breakdown):
  added a requirement that the segment axis be a named, reusable
  definition (e.g. "paid social — first-touch, last 30d") rather than an
  ad hoc unlabeled filter, so the same cell can be looked up again in a
  later stage walkthrough on the same issue.
- `ga-funnel/agents/funnel-localizer.md`, step 4 (bottleneck hypothesis):
  added a requirement that the causal claim name at least one piece of
  corroborating evidence beyond the step-2 number (session recording,
  support ticket, error log, qualitative note tied to the concentrated
  cell), so the hypothesis rests on more than a bare numeric
  correlation.
- `ga-prereg/hooks/directive.sh`, step 3 (sample size + duration + power
  basis): added a requirement that, when a pre-experiment baseline value
  of the primary metric is available per unit, the sample-size line
  states explicitly whether the power basis accounts for the variance
  reduction that baseline adjustment buys.

canonical: `cd /home/jwjung/tokenmaxxxer/rulebooks/growth-analytics-rulebook
&& git diff --stat`, run this session (output below) — no gate `.sh`
enforcement logic was touched (all three edits are to prose
walkthrough/directive files, not to the mechanical checks in
`ga-prereg-gate.sh` / `ga-funnel-gate.sh` / `ga-trust-gate.sh`), no tool
name or "learned from X" attribution appears in any of the three edited
files, and no source text was copied verbatim — each edit restates the
design move as the role's own rule.

derived:
```
cd /home/jwjung/tokenmaxxxer/rulebooks/growth-analytics-rulebook && git diff --stat
```
```
 ga-funnel/agents/funnel-localizer.md | 16 +++++++++++++++-
 ga-prereg/hooks/directive.sh         |  7 ++++++-
 ga-trust/agents/trust-gate-walker.md | 13 +++++++++----
 3 files changed, 30 insertions(+), 6 deletions(-)
```

## Tool-landscape survey (evidence trail — full detail; rulebook carries no catalog)

| # | Tool | Category | Adoption evidence (source) | Problem it solves | HOW (design move) | Learning applied |
|---|------|----------|------------------------------|--------------------|--------------------|-------------------|
| 1 | GrowthBook | Open-source variant-testing / feature-flag platform | 8,119 GitHub stars on growthbook/growthbook (MIT-licensed open core) — [github.com/growthbook/growthbook](https://github.com/growthbook/growthbook) | Teams trust a variant-test result before checking whether the underlying randomization was actually clean. | Ships a dedicated "Health" tab that runs SRM *and* multiple-exposure detection as a gating check before any result is shown as trustworthy, rather than leaving contamination checks to a separate, optional step. | ga-trust step 1 upgraded: a clean SRM chi-square no longer stands alone — cross-arm exposure contamination is now checked and hard-stops the walk the same way SRM does. |
| 2 | PostHog | Open-source product analytics | 30,000+ GitHub stars, MIT-licensed, self-hostable full stack — [github.com/PostHog-UserAnalytics](https://github.com/PostHog-UserAnalytics/), [posthog.com/blog/best-open-source-analytics-tools](https://posthog.com/blog/best-open-source-analytics-tools) | A numeric drop-off at a stage tells you *where* users left, not *why* — teams report a bottleneck number with no causal grounding. | Pairs quantitative funnel/cohort breakdowns with session-replay recordings scoped to the same segment, so a stated drop-off comes with directly-observable qualitative evidence attached to the same cell. | Funnel walkthrough step 4 upgraded: the bottleneck hypothesis must now name at least one piece of corroborating evidence (recording/ticket/log/note) tied to the concentrated cell, not just restate the step-2 number as if correlation were causation. |
| 3 | Eppo (statistics engine, since folded into Datadog Experiments) | Warehouse-native statistics engine | Statistical methods reach enterprise adoption at Microsoft/Google/Meta-scale customers via its content platform (4,000+ monthly readers) and were acquired into Datadog Experiments — [docs.geteppo.com/statistics](https://docs.geteppo.com/statistics/), [geteppo.com/blog/cuped-bending-time-in-experimentation](https://www.geteppo.com/blog/cuped-bending-time-in-experimentation) | A power analysis run on raw between-arm variance overstates the sample/duration a test actually needs when a strong pre-period baseline exists for the same unit. | CUPED-style variance reduction: regresses out pre-experiment covariate information from the outcome metric before computing significance, cutting required variance by a reported 14–86% depending on historical correlation. | ga-prereg step 3 upgraded: when a pre-experiment baseline value of the primary metric exists per unit, the power-basis line must now state whether that variance-reduction opportunity was accounted for, instead of silently defaulting to a raw-comparison sample size. |
| 4 | Amplitude / Mixpanel | Hosted product-analytics platforms | Amplitude reported as the most widely used product-analytics platform at enterprise scale (Walmart, DoorDash, Adidas, Capital One accounts); Mixpanel dominant among startup/mid-market — [mcgaw.io/blog/mixpanel-vs-amplitude](https://mcgaw.io/blog/mixpanel-vs-amplitude/), [ramp.com/vendors/amplitude/alternatives/amplitude-vs-mixpanel](https://ramp.com/vendors/amplitude/alternatives/amplitude-vs-mixpanel) | An ad hoc segment filter defined once for a report can't be reliably reused for the next analysis on the same product, so segment definitions drift between walkthroughs. | Behavioral cohorts as first-class, named, shared assets reusable across dashboards and teams, rather than one-off inline filters. | Funnel walkthrough step 3 upgraded: the segment axis must now be given as a named, reusable definition, so a later stage walkthrough on the same issue can look up the same cell instead of redefining it from scratch. |

## Why
Per issue-1199 (northpole req#1: specialist delegation at real
practitioner completeness — practitioners' tools encode their field's
solved problems). The prior growth-analytics rulebook methodology
(built across earlier issues in the rulebook repo's own history — see
that repo's git log for issue-7, issue-10, issue-13, issue-17) built its
pre-registration/funnel/trust-gate methodology from first principles
(Kohavi's trustworthy-experiments literature and the AARRR funnel
framework) but never checked what real growth-analytics tooling had
already learned about the failure modes that methodology leaves open:
contamination that survives a clean SRM, drop-off numbers reported with
no causal grounding, sample sizes computed without accounting for
available baseline covariates, and segment definitions that don't
survive to the next walkthrough. The four applied learnings close
exactly those four gaps, each traced to a real tool's design move with
adoption evidence, per this turn's operator instruction that the
evidence trail belongs here and the rulebook itself carries only the
resulting native rule.

## Upstream basis
docs/issue-1199/proposals/2026-08-13-growth-analytics-tool-landscape.md

## Open findings
pr-preflight.sh's amendments-reconciled check raced 4 consecutive `gh pr
create` attempts against 4 new issue-1199 comments arriving during this
session (issuecomment-5277558036, -5277561352, -5277564262,
-5277568927 — canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/1199/comments --paginate`, read
this session), reconciling the first 3 in turn; a 5th comment
(issuecomment-5277568927) arrived on the 4th attempt. Stopping
`gh pr create` retries after this turn's budget, per the identical
precedent already logged in docs/issue-1174/reports/issue-retrospective/
deviation-log.md (accessibility, api-design, capacity-planning, and
issue-retrospective all hit the same race). Commit
5111eb6013397ee42ffa3870e0203abd3f622c5d is pushed to
origin/issue-1199/growth-analytics on the rulebook repo for
on-the-record's outside relay to open the rulebook-repo PR.

A 5th comment (issuecomment-5277576564 — canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/1199/comments --paginate`, read
this session) then raced the on-the-record-repo `gh pr create` attempt
itself. Per the same precedent, retries are stopped here too; commit
d5d6136 (and this amendment) is pushed to
origin/issue-1199/growth-analytics on the on-the-record repo for
outside relay to open this repo's PR as well.

amendments-reconciled: issuecomment-5277558036 ("Judgment opened: PR #?
— candidate decision on branch `issue-1199/defect-verification` (1
path(s) changed) entered delegated-judgment evaluation.") is a
delegated-judgment notice for a different role's branch
(issue-1199/defect-verification), not growth-analytics — canonical: `gh
api repos/tokenmaxxxer/on-the-record/issues/1199/comments --paginate`,
read this session. It does not name or reference this growth-analytics
unit's PR or its rulebook-repo counterpart, so no content amendment to
this record is warranted.

amendments-reconciled: issuecomment-5277564262 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") — same unnumbered-PR
delegated-judgment verdict pattern as issuecomment-5277561352 above;
canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments
--paginate`, read this session. No content amendment warranted.

amendments-reconciled: issuecomment-5277561352 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") is a delegated-judgment
verdict for an unnumbered candidate PR — canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/1199/comments --paginate`, read
this session. It carries no PR number or branch name that identifies it
as this growth-analytics unit's PR or its rulebook-repo counterpart, so
no content amendment to this record is warranted.
