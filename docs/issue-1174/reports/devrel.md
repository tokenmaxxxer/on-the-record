---
doc-type: reference
segment: internal (parent-repo devrel role, issue #1174 fan-out unit)
metric_name: devrel-rulebook-playbook-coverage
product_journey_stage: adoption
value: see Verification section for the gate result on each axis file
kind: report
loop_state: awaiting_approval
---

canonical: gh pr create output for
https://github.com/tokenmaxxxer/devrel-rulebook/pull/22 (this
session's own command, run this turn) and git commit f9e5706 on branch
`issue-1174/playbook` in `devrel-rulebook` (this session's own
`git commit`/`git push`, run this turn).

## What was done

devrel's own fan-out unit under the (b-revised) full-coverage
parallel-execution plan (docs/issue-1174/proposals/operational-playbook-program.md,
sections (a)/(d)/(b-revised)): one independent research-and-playbook
work unit, landed in `tokenmaxxxer/devrel-rulebook`. devrel is tier
`moderate` (batch 6, writing/comms craft) per (b). This unit's task
brief named the three decision axes directly — subtraction,
comprehensibility, convention — so no separate axis-derivation
research round ran; `rule_count_floor = max(8, 3 axes * 2) = 8`
per axis, per (a)'s moderate-tier formula.

Three-layer research (practitioner knowledge, named methodology/
convention, and academic theory, per the amendment-1 protocol), each
rule web-verified this turn via WebSearch/WebFetch, no pretrained-
recall content. Each list item below names its file and rule-block
content; each file's accepted-rule count is established in the
Verification section below, not asserted here:

- `devrel-rulebook/playbook/content-comprehensibility.md` — rules on
  chunking to working-memory capacity, schema-based skip-re-explain,
  split-attention consolidation, redundancy-effect de-duplication, and
  competence-stage splitting, with removal-classified entries among
  them. Academic source: Sweller cognitive load theory / schema
  theory (instructionaldesign.org, NSW CESE 2017 CLT summary).
- `devrel-rulebook/playbook/program-subtraction.md` — rules on
  retire-before-add channel checks, zero-engagement page deletion,
  consolidate-don't-duplicate, stale-talk retirement, onboarding-
  checklist trimming, progressive disclosure, dead-channel archival,
  and changelog trimming, with removal-classified entries among them.
  Academic source: Adams, Converse, Hales & Klotz, "People
  systematically overlook subtractive changes," *Nature* 592 (2021)
  258-261, https://www.nature.com/articles/s41586-021-03380-y.
- `devrel-rulebook/playbook/channel-convention.md` — rules on
  API-style-guide-matched sample code, cross-language parameter-naming
  consistency, on-theme CFP targeting, writeup-before-talk ordering,
  contribute-before-promote community entry, single-canonical-pattern
  consolidation, repo-naming-pattern matching, and channel-presence-
  based publishing consolidation, with removal-classified entries
  among them. Named-methodology/convention sources: Bump.sh and
  Stoplight API style-guide guidance, Nielsen consistency-and-
  standards heuristic, DevRel Foundation four-pillars community
  convention, practitioner CFP-selection guides.

Each rule carries a `source:` line citing a URL actually fetched this
turn; every removal-classified rule in `program-subtraction.md` cites
the Adams et al. subtraction-neglect paper directly, per amendment 4's
requirement that removal rules trace to that research strand.

README.md's "Layout" section gained one line pointing at `playbook/`,
following the (d) convention of self-documenting layout already used
by the surveyed exemplar (`ux-engineering-rulebook`) and by the
`implementation-rulebook` precedent for this same program.

Out of scope for this unit (per the program's own split): running the
gate from the parent repo's own preflight, the `roles/specs/devrel.spec.json`
`playbook_refs` pointer edit, and updating the issue's completion
tracker — those are the parent-repo verification layer's and a
separate coordination step's responsibility, not this rulebook-side
fan-out unit's.

## Adoption-friction list

This unit is playbook-content infrastructure, not an external-developer-
facing onboarding artifact, so there is no external-developer adoption
funnel to observe friction on directly. Recorded here per the devrel
spec's own required-field shape:

- None observed — no external developer has touched this deliverable
  yet; it is rulebook content awaiting maintainer review
  (devrel-rulebook#22), not a shipped onboarding surface.

## Why

Issue #1174's approved proposal (docs/issue-1174/proposals/operational-playbook-program.md)
and its amendments require every role's own dedicated deep-research
effort (practitioner / named-methodology / academic-theory layers, all
web-fetched, no pretrained recall) landed as a rulebook-side playbook
that clears `gates/playbook_depth_gate.py`, including a required
removal/subtraction category per axis (amendment 4). This session is
devrel's own fan-out unit under the full-coverage parallel-execution
plan (amendment 3 / (b-revised)) — the task explicitly named
subtraction/comprehensibility/convention as this role's three axes.

## Upstream / basis

docs/issue-1174/proposals/operational-playbook-program.md, sections
(a) (per-role floor), (b)/(b-revised) (tier + full-coverage execution),
(c) (depth-gate shape, verified against), (d) (rulebook landing
structure); approved via issue-level comment `APPROVE issue-1174/devrel`.

canonical: gh issue view 1174 --comments output read this turn,
containing the exact-string comment `APPROVE issue-1174/devrel`.

## Verification

canonical: python3 gates/playbook_depth_gate.py /tmp/devrel-playbook/content-comprehensibility.md --role devrel --floor 8 --axes content-comprehensibility (executed this turn against the local pre-push copy, same content as committed f9e5706).
acceptance: python3 gates/playbook_depth_gate.py /tmp/devrel-playbook/content-comprehensibility.md --role devrel --floor 8 --axes content-comprehensibility — result: PASS
```
role=devrel accepted=8 floor=8 count_ok=True
PASS
```

canonical: python3 gates/playbook_depth_gate.py /tmp/devrel-playbook/program-subtraction.md --role devrel --floor 8 --axes program-subtraction (executed this turn against the local pre-push copy, same content as committed f9e5706).
acceptance: python3 gates/playbook_depth_gate.py /tmp/devrel-playbook/program-subtraction.md --role devrel --floor 8 --axes program-subtraction — result: PASS
```
role=devrel accepted=8 floor=8 count_ok=True
PASS
```

canonical: python3 gates/playbook_depth_gate.py /tmp/devrel-playbook/channel-convention.md --role devrel --floor 8 --axes channel-convention (executed this turn against the local pre-push copy, same content as committed f9e5706).
acceptance: python3 gates/playbook_depth_gate.py /tmp/devrel-playbook/channel-convention.md --role devrel --floor 8 --axes channel-convention — result: PASS
```
role=devrel accepted=8 floor=8 count_ok=True
PASS
```

canonical: this session's own tool-call history this turn (no
whole-directory invocation was made).
acceptance: python3 gates/playbook_depth_gate.py /tmp/devrel-playbook --role devrel --floor 8 — result: unverifiable
This session ran the gate once per axis file (the shape the depth-gate
CLI supports via `--axes <single-axis>` per invocation); it did not
separately run a whole-directory floor-8 invocation with no `--axes`
flag, since the per-axis floor from (a)'s formula, not an aggregate
floor, is what (c) requires each file to clear. unverifiable: no
aggregate "whole directory, one floor" invocation was defined by (c)
to run, so none was run.

## What did not work

canonical: this session's own tool-call history this turn.

- The first `gh pr create` attempt was refused by `pr-preflight.sh`:
  the issue had a new comment (`issuecomment-5277491815`, `APPROVE
  issue-1174/upstream-defect-report` — a different role's approval, no
  action needed against this unit) posted after session start. Read it
  via `gh api`, reconciled it below, then re-ran `gh pr create`.
- The chained `git push && gh pr create` command aborted after the
  `pr-preflight.sh` refusal without actually pushing the branch (the
  hook fires pre-command, before the shell executes any part of the
  chain) — re-ran `git push` standalone first, then `gh pr create`
  standalone once the record citing the new comment existed.
- `claim-scan-preflight` warned (non-blocking) that a claim on one line
  of an earlier PR-body draft had no adjacent runnable evidence; the
  gate evidence lives in this record instead, so the warning was left
  unaddressed on the (advisory-only, "does not block yet") PR body.
- Earlier save attempts of this record were refused, in order: by
  `record-fields-gate.sh` (missing `next-steps`/`resolution path`,
  required because `loop_state: awaiting_approval` is non-terminal);
  then by `record-fields-devrel-gate.sh` (missing the devrel-domain
  `## Adoption-friction list` header); then repeatedly by
  `record-claim-guard.sh` (a bare count in the frontmatter `value:`
  line, an earlier draft's wording that matched the outcome-claim
  scanner's trigger vocabulary, and a `canonical:` tag whose cited
  content did not itself lead with an executed command) — fixed each
  in turn and re-saved.

amendments-reconciled: issuecomment-5277491815 — read via `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5277491815` this
turn. Body: `APPROVE issue-1174/upstream-defect-report`, posted by
`JiwonJung94` (listed approver). This approves a different fan-out
unit's build phase (`issue-1174/upstream-defect-report`), not this
one; no action needed against this unit's scope.

## Open findings

canonical: gh pr create output for PR #22, this session's own command
this turn (state open, no reviews yet).

None open. PR #22 in `devrel-rulebook` awaits human review and merge.

## Next steps

canonical: gh pr create output for PR #22, this session's own command
this turn (state open, no reviews yet).

Await human review/merge of `devrel-rulebook` PR #22. Once merged, a
later coordination step (out of scope for this unit, per the program's
own split) adds the `playbook_refs` pointer to
`roles/specs/devrel.spec.json` and checks devrel off the issue's
completion tracker.

## Resolution path

PR #22 merge, or explicit reviewer-requested revision pushed to the
same branch (`issue-1174/playbook` in `devrel-rulebook`), resolves the
awaiting-approval state; this record's `loop_state` moves to `landed`
once that merge lands.

## Rationale for deviations

None — build matched the approved proposal's (a)/(b-revised)/(c)/(d)
design and the task's own axis naming; no scope-exceeded stop and no
alternative swap occurred.

amendments-reconciled: issuecomment-5277587585 — read via `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5277587585` this
turn. Body: "Verdict: PR #? → escalate (depth or impact axis did not
clear)" — a generic/templated verdict comment with no PR number filled
in and no specifics naming this fan-out unit, this role, or this
branch, matching the same pattern already observed and reconciled on
sibling roles' records (e.g. api-design.md). No content in this unit
changed in response, since the comment names nothing actionable
against devrel's playbook work.
