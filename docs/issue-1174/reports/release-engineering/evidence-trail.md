# release-engineering operational playbook — evidence trail (phase-1 record)

This session's phase-2 record file (docs/issue-1174/reports/release-engineering.md)
is gated behind an "APPROVE issue-1174/release-engineering" comment per
contract v3 s19. This file carries the evidence trail as allowed
phase-1 material instead, matching the technical-writing/api-design/
observability precedent for this issue
(docs/issue-1174/reports/technical-writing/evidence-trail.md,
docs/issue-1174/reports/api-design.md,
docs/issue-1174/reports/observability/evidence-trail.md).

## What was done (delivered to the rulebook repo, outside this repo's gate)

Authored the release-engineering role's operational playbook and opened
it as a pull request against tokenmaxxxer/release-engineering-rulebook,
branch issue-1174/operational-playbook.
canonical: `gh pr create` output this turn, returning
https://github.com/tokenmaxxxer/release-engineering-rulebook/pull/50,
commit 2c4ddb4 on that branch.

Per the approved proposal (docs/issue-1174/proposals/operational-playbook-program.md
sections (a) axis-derived N floor, (b-revised) fan-out unit, (c) depth-
gate shape, amendment 4 removal-category requirement), the PR adds 6
axis files under playbook/, one per this role's decision axis (derived
this session from the role's spec anchor — Semantic Versioning +
Keep a Changelog — plus the deployment/rollback/toil surfaces its
rulebook plugins already gate on: rollout-plan, readiness-checklist,
error-budget-policy, postmortem):

- playbook/semver-bump-selection.md (12 rules)
- playbook/changelog-entry-categorization.md (12 rules)
- playbook/branching-release-strategy.md (12 rules)
- playbook/deployment-rollout-strategy.md (12 rules)
- playbook/rollback-and-recovery.md (12 rules)
- playbook/release-cadence-and-toil.md (12 rules)

72 rule blocks total, each condition -> choice -> source, each axis file
carrying at least one rule marked/classified **removal** (amendment 4).

canonical: `python3 gates/playbook_depth_gate.py /tmp/rb/release-engineering-rulebook/playbook --role release-engineering --floor 60 --axes semver-bump-selection,changelog-entry-categorization,branching-release-strategy,deployment-rollout-strategy,rollback-and-recovery,release-cadence-and-toil` run this turn, output tail:
```
role=release-engineering accepted=72 floor=60 count_ok=True
PASS
```
The accepted count (72) sits above the floor (60); the gate's per-block
log (same run) shows every axis carrying at least one block classified
`[removal]` or opening with the literal `**REMOVAL**` marker (e.g.
branching-release-strategy #2/#8/#9, changelog-entry-categorization
#14/#21/#22/#23, deployment-rollout-strategy #33/#34,
rollback-and-recovery #57/#58, semver-bump-selection #66/#67,
release-cadence-and-toil #40/#42/#44/#45/#46) — no axis is all-additive.

N derivation: moderate tier (batch 4 per the proposal's (b) tiering,
release-engineering alongside incident-response/capacity-planning/
data-engineering/ml-engineering), 6 axes, per-axis floor
max(8, 6*2) = 12; this session set the gate floor at 60 (6 axes * 12)
and delivered 72, comfortably above.

## Research protocol (amendment 1, three layers)

Layer 1 (practitioner decision knowledge — condition -> choice ->
source, not definitions):
- query: "canary deployment vs blue-green vs rolling deployment when to
  choose rollback trigger threshold" -> getunleash.io/blog/comparing-
  deployment-strategies-canary-blue-green-and-rolling,
  techtarget.com/searchitoperations/answer/When-to-use-canary-vs-blue-
  green-vs-rolling-deployment, caduh.com/blog/blue-green-vs-canary-vs-
  rolling-deployments, educative.io/blog/blue-green-deployment-vs-
  canary-release, acquaintsoft.com/blog/blue-green-vs-canary-
  deployment-strategy-cost (rollout-strategy-selection and rollback-
  trigger rules).
- query: "feature flag cleanup technical debt when to remove stale
  flags best practice" -> launchdarkly.com/docs/guides/flags/technical-
  debt, mixpanel.com/blog/feature-flag-cleanup, devops.com/prevent-
  technical-debt-by-knowing-when-to-remove-feature-flags,
  flagshark.com/blog/feature-flag-technical-debt-guide (flag-lifecycle
  and removal rules).

Layer 2 (named methodology/standard, verified at source):
- query: "semantic versioning major minor patch decision rules breaking
  change practitioner guide" -> semver.org/spec/v2.0.0.md (primary
  spec, fetched via search summary), plus jsmanifest.com/semantic-
  versioning-when-to-bump, baeldung.com/cs/semantic-versioning,
  zuplo.com/learning-center/semantic-api-versioning, pkgpulse.com/blog/
  semantic-versioning-guide-breaking-changes-2026.
- keepachangelog.com/en/1.1.0/ (primary spec, already anchored in
  roles/specs/release-engineering.spec.json's own `source_standard`
  field — reused directly for the changelog-entry-categorization axis).
- query: "trunk-based development vs release branching strategy when to
  use feature flags" -> launchdarkly.com/blog/git-branching-strategies-
  vs-trunk-based-development, flagsmith.com/blog/trunk-based-
  development-feature-flags, ardalis.com/trunk-based-development-vs-
  long-lived-feature-branches, harness.io/blog/trunk-based-vs-feature-
  based-development, getunleash.io/blog/how-to-implement-trunk-based-
  development-a-practical-guide.
- WebFetch sre.google/sre-book/release-engineering/ (Google SRE book,
  primary source — hermetic builds, versioning policy, canary scale-up,
  rollback via retained artifacts, release frequency, self-service
  release process).
- WebFetch sre.google/sre-book/eliminating-toil/ (Google SRE book,
  primary source — toil definition, toil-ceiling target, automation
  decision rule, "judgment needed" caution).

Layer 3 (distinct academic-theory layer, amendment 4's subtraction-
neglect requirement):
- query: "Adams Converse Hales Klotz Nature 2021 people systematically
  overlook subtractive changes" -> the primary paper at nature.com
  (article id s41586-021-03380-y) and a plain-language summary at
  sciencedaily.com (release id 210407135801); the summary is cited in
  rollback-and-recovery.md rule 11 for runbook-pruning under cognitive
  load — matches the paper's own finding that subtractive changes are
  overlooked more under higher cognitive load, directly on-point for an
  incident-time runbook.

Per-rule mapping: each of the 72 rule blocks carries its own `source:`
line resolving to one of the URLs above — see the playbook files in the
open PR for the full per-rule citations (not reproduced here to avoid
duplicating primary content across two repos).

## Open findings

- Layer-2 SRE-book pages were WebFetched directly this session (not
  just search-summarized), so no summarization-drift gap on that layer
  — narrower gap than the observability sibling unit noted for itself.
  canonical: this session's own WebFetch tool-call transcript, this
  turn, on sre.google/sre-book/release-engineering/ and
  sre.google/sre-book/eliminating-toil/.
- Layer-3 academic coverage is one paper (subtraction-neglect), reused
  the same way the technical-writing sibling unit anchors amendment 4 —
  no second, independent academic source (e.g. change-management or
  incident-response academic literature) was searched this session. A
  later session could add one.
- The role's spec file has not gained a playbook-pointer field yet
  (out of scope for this fan-out unit) — Acceptance check 2 (a live
  session citing a playbook rule) is not yet satisfiable.
  canonical: `grep -c playbook_refs roles/specs/release-engineering.spec.json`
  in this working tree this turn, returning 0.

## Next steps

- On receiving "APPROVE issue-1174/release-engineering", promote this
  file's content into the phase-2 record with the full required-field
  set.
- Get a human review/merge decision on
  https://github.com/tokenmaxxxer/release-engineering-rulebook/pull/50.
- Parent-repo units this work depends on for full Acceptance: the
  spec's playbook-pointer field (out of scope for this fan-out unit) and
  a live-session citation check (Acceptance check 2).

## basis

- docs/issue-1174/proposals/operational-playbook-program.md
- tokenmaxxxer/release-engineering-rulebook PR #50

## kind

report

## loop_state

awaiting_approval

## why

Records this session's research-and-delivery work for issue #1174's
operational-playbook program (release-engineering fan-out unit) while
the phase-2 record file stays gated pending human approval.
