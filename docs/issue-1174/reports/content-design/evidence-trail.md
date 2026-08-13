# content-design operational playbook — evidence trail (phase-1 record)

This session's phase-2 record file is gated behind an
"APPROVE issue-1174/content-design" comment per contract v3 s19; no such
comment exists yet.
canonical: `gh issue view 1174 --comments` output this turn, grep for
"APPROVE issue-1174/content-design" returning no match. This file
carries the evidence trail as allowed phase-1 material instead, so the
research trail is not lost between sessions.

## What was done (delivered to the rulebook repo, outside this repo's gate)

Authored the content-design role's operational playbook and opened it
as a pull request against tokenmaxxxer/content-design-rulebook, branch
issue-1174/content-design.
canonical: `gh pr create` output this turn, returning
https://github.com/tokenmaxxxer/content-design-rulebook/pull/21 — the
PR's open/merged state was not re-checked after creation; treat it as
open as of this turn's `gh pr create` call, not confirmed merged.

The PR adds playbook/operational-playbook.md: 25 rule blocks (condition
-> choice -> source), grouped into 5 axes — error messages, buttons/
CTAs and confirmation dialogs, plain language and readability, empty
states and progressive disclosure, and NN/G tone-axis application —
each axis carrying at least one rule marked **REMOVAL** (5 total, one
per axis), per the issue's requirement 4.
canonical: file content of playbook/operational-playbook.md as written
this session this turn (see the git diff on branch
issue-1174/content-design in the content-design-rulebook repo, commit
f86351d).

## Research protocol (three layers)

Layer 1 (practitioner decision rules, demonstrated depth):
- query: "Nielsen Norman Group UX writing microcopy decision rules
  button label error message guidelines" -> nngroup.com error-message
  scoring rubric + microcopy button-label guidance.
- query: "Google Material Design content design guidelines button label
  confirmation destructive action wording" -> uxplanet.org confirmation
  dialog analysis, designsystemscollective.com destructive-button
  guidance.
- query: "GOV.UK content design style guide error messages form labels
  writing rules" -> design-system.service.gov.uk error message
  component, designsystem.parliament.uk forms guidance.

Layer 2 (named methodology/standard, verified at source):
- fetch: https://www.nngroup.com/articles/error-messages-scoring-rubric/
  -> full 12-criteria rubric (visibility/communication/efficiency
  dimensions), used verbatim as the source for rules 1, 5-10, 24, 25.
- fetch: https://design-system.service.gov.uk/components/error-message/
  -> wording patterns, format rules, banned-word list, used as the
  source for rules 2, 3, 4, 6, 8, 9.

Layer 3 (academic/empirical theory layer):
- query: "plain language guidelines readability sentence length
  microcopy A/B testing best practices" -> readability formula synthesis
  (Flesch-Kincaid, MSKTC plain-language tool), sentence-length findings
  used for rules 16-19.
- query: "academic research empty state design UX writing progressive
  disclosure onboarding cognitive load study" -> Nielsen's 1995
  progressive-disclosure origin, task-completion-time (20-40% reduction)
  and support-ticket (35% reduction) empirical findings, used for rules
  20-23.

canonical: WebSearch/WebFetch tool results returned this turn for each
query/URL listed above (session transcript, this turn).

Per-rule mapping: each of the 25 rule blocks carries its own source
line resolving to one of the URLs above.
canonical: playbook/operational-playbook.md, "Evidence trail (fetched
sources)" section, as committed in commit f86351d on branch
issue-1174/content-design in the content-design-rulebook repo (full
per-rule citations live there to avoid duplicating primary content
across two repos).

## Depth self-assessment

25 rules, 5 REMOVAL-category (one per axis).
canonical: playbook/operational-playbook.md, "Depth note" section,
commit f86351d, content-design-rulebook repo — states the count and
names the uncovered follow-up axes (localization interplay,
voice-and-tone per product surface, notification copy) explicitly as
open for a follow-up batch, rather than claiming full coverage.

## Why

Requirement: tokenmaxxxer/on-the-record#1174 requirement 1 (per-role
operational playbook, condition->choice->source granularity) and
requirement 2 (thorough web-verified research per rule, evidence-graded,
sources cited inline). This session covers content-design as one unit
of the issue's batch-1 UX/design family fan-out.
Upstream basis: docs/issue-1174/proposals/operational-playbook-program.md
(approved program design); role-invocation prompt naming this as "YOUR
OWN operational playbook."

## kind / loop_state

kind: evidence-trail
loop_state: awaiting-approval

## Open findings

- content-design-rulebook#21 has not been re-checked for merge status
  after this turn's `gh pr create` call; landing depends on a human
  review this session does not control.
- Rule count (25) is below the technical-writing exemplar's 50 rules;
  whether 25 clears the not-yet-negotiated phase-1 N floor for
  content-design is open for the batch gate script / reviewer
  spot-check named in the issue's acceptance criteria.
- The issue's acceptance criterion "one live role session's judgment
  record cites a specific playbook rule" has not been attempted for
  content-design in this session.

## Next steps

- Re-check content-design-rulebook#21's review/merge status in a
  subsequent session (`gh pr view 21 --repo tokenmaxxxer/content-design-rulebook`).
- After merge, a follow-up session should add a spec pointer to
  playbook/operational-playbook.md per issue requirement 5; this
  session's write set did not include the spec file.
  canonical: `git status --short` this turn showed no spec file staged.
- Resolution path: a human approver posts "APPROVE issue-1174/content-design"
  on issue #1174 (single-account mode) or a PR review Approve, opening
  phase 2, where the batch gate script and live-citation check can run
  against this repo.
