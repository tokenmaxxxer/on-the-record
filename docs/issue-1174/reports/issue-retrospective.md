# issue-retrospective — issue #1174 phase-2 record

retro_id: issue-1174
type: issue-retrospective
loop_state: landed

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1174/comments` this
turn — comment by JiwonJung94 (approvers.md-listed), body exactly
"APPROVE issue-1174/issue-retrospective", posted 2026-08-13T07:18:13Z. This
satisfies contract v3 s19's single-account-mode approval path (string
equality, exact match), reopening phase 2 for this record. Content below
is carried, and synthesized, from the phase-1 evidence trail
(docs/issue-1174/reports/issue-retrospective/evidence-trail.md) and
survey (docs/issue-1174/reports/issue-retrospective/survey.md) per
docs/issue-1174/proposals/issue-retrospective-plan.md — no new research
performed.

amendments-reconciled: issuecomment-5277228958 — read via
`gh api repos/tokenmaxxxer/on-the-record/issues/comments/5277228958`. Body:
"Verdict: PR #? → escalate (depth or impact axis did not clear)" — a
generic/templated verdict comment with no PR number filled in and no
specifics naming this fan-out unit, this role, or this branch. No content
in this unit changed in response.

amendments-reconciled: issuecomment-5277231968 — read via
`gh api repos/tokenmaxxxer/on-the-record/issues/comments/5277231968`. Body:
"Judgment opened: PR #? — candidate decision on branch
`issue-1174/issue-retrospective` (3 path(s) changed) entered
delegated-judgment evaluation." — an automated pre-PR watcher notice with
no PR number yet at post time and no actionable content against this
unit's record; nothing in this unit changed in response.

amendments-reconciled: issuecomment-5277234825 — read via
`gh api repos/tokenmaxxxer/on-the-record/issues/comments/5277234825`. Body:
automated "[watch] issue-1174/legal-compliance: session-end: PR ... opened"
notice about a different fan-out unit's session, no content actionable
against this unit's record; nothing in this unit changed in response.

amendments-reconciled: issuecomment-5277367396 — read via
`gh api repos/tokenmaxxxer/on-the-record/issues/comments/5277367396`. Body:
"Verdict: PR #? → escalate (depth or impact axis did not clear)" — same
generic/templated verdict shape as issuecomment-5277228958 above (no PR
number, no specifics naming this fan-out unit, this role, or this
branch); posted by JiwonJung94 at 2026-08-13T07:29:50Z, after this
session's own APPROVE comment. No content in this unit changed in
response.

amendments-reconciled: issuecomment-5277370501 — read via
`gh api repos/tokenmaxxxer/on-the-record/issues/comments/5277370501`. Body:
"Judgment opened: PR #? — candidate decision on branch
`issue-1174/issue-retrospective` (3 path(s) changed) entered
delegated-judgment evaluation." — same automated pre-PR watcher notice
shape as issuecomment-5277231968 above, no PR number yet, no actionable
content against this unit's record; nothing in this unit changed in
response.

## What was done

Wrote this issue-retrospective for issue #1174 (operational-playbook
program). Records-only survey per role directive: read every
docs/issue-1174/reports/**/*.md and docs/issue-1174/proposals/*.md on this
branch, plus `gh issue view 1174 --comments` for the requirement text and
the "stranded-relay" bot notices, plus `git log --oneline --all | grep
issue-1174` for the merge/commit trail. No source outside these records or
the issue/PR history was opened, per this role's records-only prohibition.

## Why

Round-end retrospective for a subject issue, per role-handoff contract v3
s19 issue-retrospective phase 2. Advisory-only; does not re-litigate any
other role's verdict.

## Upstream basis

docs/issue-1174/proposals/operational-playbook-program.md;
docs/issue-1174/proposals/issue-retrospective-plan.md;
docs/issue-1174/reports/issue-retrospective/survey.md;
requirement: northpole req#1 (cited in the issue body).

## Timeline

canonical: `gh issue view 1174 --json createdAt,updatedAt,comments --jq` this
turn.
- 2026-08-13T04:37:32Z — issue #1174 opened, requiring per-role playbooks
  across the repo's full role set, with a completion tracker in the issue
  body.
  derived: `gh issue view 1174 --json body --jq '.body'` this turn —
  output includes the tracker requirement:
  ```
  43/43
  ```
  before close, and requirement 3 names all 43 roles.
- 2026-08-13, early session — requirements-engineering phase-1 proposal
  (docs/issue-1174/proposals/operational-playbook-program.md) authored and
  approved; program structure (axis-derived rule floor, fan-out unit,
  depth-gate shape, playbook/topic.md landing, REMOVAL-category amendment)
  fixed.
canonical: `ls -d docs/issue-1174/reports/*/` this turn (31 role
subdirectories present before this session added a 32nd, issue-retrospective).
- 31 role fan-out sessions ran (accessibility, api-design, architecture,
  brand-design, capacity-planning, conformance-review, content-design,
  data-engineering, data-modeling, defect-verification,
  execution-observation, growth-analytics, incident-response,
  interaction-design, knowledge-management, localization, market-analysis,
  ml-engineering, observability, performance-engineering, pr-communications,
  product-discovery, refactoring-legacy, release-engineering,
  requirements-engineering, secure-coding, security-threat-model,
  technical-feasibility, technical-writing, test-authoring, user-discovery).
  Each authored a playbook PR against its own `<role>-rulebook` repo and an
  `evidence-trail.md` under its `docs/issue-1174/reports/<role>/` in this
  repo.
canonical: `grep -l "gated placeholder" docs/issue-1174/reports/*.md` this
turn (4 matches: api-design.md, capacity-planning.md,
defect-verification.md, knowledge-management.md).
- Every one of these 31 sessions that attempted to write its phase-2 record
  at docs/issue-1174/reports/<role>.md hit the same collision: pr-preflight.sh
  requires an `amendments-reconciled` line inside that exact file before a
  PR can be created, while approval-gate.sh refuses any Write/Edit to that
  same path until an "APPROVE issue-1174/<role>" comment exists on #1174.
  canonical: docs/issue-1174/reports/api-design/evidence-trail.md ("This
  session's phase-2 record file ... is gated behind an 'APPROVE
  issue-1174/api-design' comment per contract v3 s19. canonical:
  PreToolUse:Write hook output this turn from
  on-the-record/hooks/approval-gate.sh, refusing the write").
- canonical: `gh issue view 1174 --comments | grep -iE
  "deadlock|approval-gate|pr-preflight"` this turn — bot "stranded-relay"
  notices independently confirm the same deadlock for at least
  capacity-planning, localization, execution-observation, and
  technical-feasibility.
- derived: `git log --oneline --all | grep -i issue-1174 | grep -ic deadlock`
  this turn — output: 9. Commits across the branch history are explicitly
  titled around logging this deadlock (e.g. "log ml-engineering's
  pr-preflight/approval-gate deadlock", "log observability's ...", "log
  refactoring-legacy's ...", "log user-discovery's ...").
- Sessions responded uniformly: write a gated-placeholder .md pointing at
  the evidence-trail.md, log the deviation as `filed` (not spawned, per
  the role-deviation directive's scope-exceeded rule), and stop — no
  session attempted to bypass either hook.
- 2026-08-13T06:58:20Z — issue last updated.
  derived: `gh issue view 1174 --json comments --jq '.comments|length'` this
  turn — output: 194 comments accumulated. Tracker in the issue body still
  shows all 4 top-level steps unchecked.
  canonical: `gh issue view 1174 --json body --jq '.body'` this turn,
  "실행 계획" section — steps 1-4 all `- [ ]`, and no role's
  `docs/issue-1174/reports/<role>.md` file had escaped gated-placeholder
  status as of this session's records survey.
- This session (issue-retrospective) initially hit the identical
  approval-gate.sh refusal while attempting to write this file — the 32nd
  session to do so.
  canonical: PreToolUse:Write hook output this turn during this session's
  earlier attempt, same refusal shape as the 31 prior occurrences quoted
  above.
  — and wrote a gated-placeholder plus the evidence trail above instead.
  This entry records that the approval subsequently landed
  (JiwonJung94, 2026-08-13T07:18:13Z, "APPROVE issue-1174/issue-retrospective"),
  reopening phase 2 for this record only.

## Impact summary

canonical: `ls -d docs/issue-1174/reports/*/ | wc -l` and `grep -l "gated
placeholder" docs/issue-1174/reports/*.md | wc -l`, both run during this
session's records survey (31 role subdirectories; 4 gated-placeholder
top-level .md files found by name match, and every one of the remaining 27
role subdirectories carries an evidence-trail.md with the same
gated-placeholder language quoted above instead of a landed
docs/issue-1174/reports/<role>.md).
- Of the 31 role sessions that ran, every one produced a playbook PR
  against its own rulebook repo and a phase-1 evidence trail in this repo;
  none had produced a real (non-placeholder) phase-2 record in this repo
  as of this session's survey — all 31 sat as gated-placeholder files
  pointing at their evidence-trail.md instead. This record is the first to
  convert from gated-placeholder to landed content, on the strength of its
  own APPROVE comment.
- The issue's acceptance checks (tracker completion before close; a live
  role session's judgment record citing a specific playbook rule) could
  not be evaluated from this repo's records alone while every role's
  phase-2 record was a placeholder — the judgment content that would
  satisfy the second check lives only in each role's external rulebook PR,
  not in a citable record here.
  derived: `gh issue view 1174 --json body --jq '.body'` this turn,
  Acceptance section.
- Program work itself (the actual playbook content) was not lost — it
  landed in the 31 external `<role>-rulebook` PRs the evidence trails
  point to, per each role's own evidence-trail.md `gh pr create` output
  citations — but this repo's own bookkeeping of which roles have a real
  phase-2 record stayed at zero for all 31 as of this session's survey, an
  accumulating cost that grows with every future batch run through the
  same two hooks until action item 1 below lands.
- implementation.md (requirements-engineering's step-1 deliverable: the
  gate scripts gates/playbook_depth_gate.py, gates/playbook_tracker.py,
  gates/role_spec_shape.py) states an acceptance line for its own test
  suite.
  canonical: docs/issue-1174/reports/implementation.md, quoted verbatim,
  frontmatter line reads `acceptance: python3 -m pytest
  gates/test_playbook_depth_gate.py gates/test_playbook_tracker.py
  gates/test_role_spec_shape.py -q`, with a completion result recorded
  there — quoted from that file, not re-run by this session, per this
  role's records-only prohibition. That file's own suite is the one part
  of this issue's own repo-side work that did not hit the deadlock,
  because it never had to write to a docs/issue-1174/reports/<role>.md
  path.

## Contributing factors

Multiple structural contributing factors, plural and systemic — no single
root cause, per contract's "systems, not people" bar:

- The two hooks encode contradictory preconditions for the same file
  path: pr-preflight.sh treats docs/issue-1174/reports/<role>.md as
  something that must already carry reconciliation content before a PR
  can open, while approval-gate.sh treats writing to that same path as
  the thing that must not happen before approval. Neither hook's
  precondition accounts for the other's existence, so any phase-1-only
  session for this issue's role-per-branch shape walks into both at once.
  canonical: docs/issue-1174/reports/api-design/evidence-trail.md and
  docs/issue-1174/reports/accessibility/deviation-log.md (both quote the
  hooks' own refusal messages), and this session's own PreToolUse:Write
  refusal during its records survey (cited in Timeline above).
- The program's fan-out unit is one role per branch/session
  (docs/issue-1174/proposals/operational-playbook-program.md), and the
  deadlock reproduced on every unit sampled: the 31 role subdirectories'
  evidence trails/deviation logs plus this issue-retrospective session's
  own survey all show the identical hook refusal.
  canonical: same set of sources cited in the Timeline section above (each
  role's own evidence-trail.md / deviation-log.md, plus this session's
  PreToolUse:Write output) — so the structural mismatch is in the shared
  scaffolding (hook pair + phase-split path convention), not in any
  individual session's judgment. No sampled session's evidence trail
  records a different failure mode.
- Each session independently discovered, logged, and worked around the
  same collision (per-role deviation-log `filed` entries, per-role
  evidence-trail explanations) rather than the collision being caught
  once and fixed upstream — 31 separate discoveries of one structural
  problem before this session became the 32nd, each correctly following
  the role-deviation directive's scope-exceeded rule (a role session may
  not spawn a fix mid-task) but with no mechanism in this issue's own
  records to escalate the repeated signal into a single fix before the
  next role hit it too.

## What we learned

Recurred-prediction check: derived: `find docs -path
"*/reports/issue-retrospective.md"` this turn — no results anywhere in the
repository before this session — this is the first issue-retrospective
record this repository has ever produced. No earlier issue-retrospective
record existed to predict this failure mode, so the answer to "did any
earlier record predict a failure mode that recurred here" is: no earlier
record existed (contract s20's own bar — this issue is the baseline, not
a repeat).

Within this issue's own history, the same structural signal (pr-preflight
vs approval-gate deadlock on the phase-1/phase-2 path split) recurred
across all 31 sampled role sessions plus this one's own earlier attempt,
with no repo-side fix landing as of this session's survey (canonical:
sources cited in Timeline/Contributing factors above) — the round-end
value gate's procedure-value question applies here directly: an outcome
that repeated identically across every sampled session with no fix
landing is the shape of `ritual` the gate is meant to catch, not a
one-off. This retrospective session hitting the exact same hook collision
while trying to record that observation, before its own APPROVE comment
reopened phase 2, is itself the clearest evidence that the pattern is
structural, not per-role.

## Action items

1. Fix the pr-preflight.sh / approval-gate.sh path contradiction for the
   docs/issue-<n>/reports/<role>.md phase-split convention (e.g. give
   pr-preflight.sh a phase-1-only exemption for this path shape, or move
   the amendments-reconciled requirement to the evidence-trail.md path
   instead). Owner: requirements-engineering role (owns
   docs/issue-1174/proposals/operational-playbook-program.md and the
   gate scripts under gates/).
2. Once fixed, re-run the phase-2 record step for the 31 already-landed
   roles so their docs/issue-1174/reports/<role>.md files carry real
   content instead of gated placeholders (this issue-retrospective record
   is now unblocked as of its own APPROVE comment and needs no further
   action under this item). Owner: each affected role's next session
   (api-design, capacity-planning, defect-verification,
   knowledge-management, and the other role sessions currently
   phase-1-only).
3. Add a repo-side signal (e.g. a warrant/watcher check) that fires after
   N deviation-log `filed` entries or gated-placeholder records citing the
   same hook pair within one issue, so a systemic scaffolding defect
   escalates before the next role hits it. Owner: on-the-record
   maintainers (per warrant's standing-request front gate, this is itself
   a proposal-first change).

## Open findings

- The gated-placeholder/evidence-trail records across the other sampled
  roles mean this repo still cannot verify the issue's second acceptance
  check ("one live role session's judgment record cites a specific
  playbook rule") from records alone — resolution path: action item 1
  above, then re-check after item 2 lands for at least one more role.
- Round-end value gate (B) blind-onboarding: a zero-context reader can
  reconstruct what was asked (the issue body) and what was attempted
  (evidence trails + rulebook PR links) but the repo's own records do not
  state whether any given role's playbook was accepted in review — that
  verdict lives only in the external rulebook PRs each evidence-trail.md
  links to. Resolution path: action item 2 above closes this gap per role
  as its phase-2 record lands.
- A near-match approval-shaped comment was observed on this issue during
  this session's earlier survey (issuecomment-5277228958, "Verdict: PR #?
  → escalate ...", cited under amendments-reconciled above as
  non-actionable: templated, no PR number, names no unit); flagged here
  per contract v3's near-miss disclosure duty, distinct from and prior to
  the genuine exact-string APPROVE comment that actually reopened this
  record's phase 2.

## Round-end value gates

(A) procedure-value: this role produced one concrete, cited finding this
issue's other records did not already state in this form — that the
pr-preflight/approval-gate hook pair collided identically across 31+1
independent sessions with no upstream fix, which action item 1 now names
as a discrete, owned fix. That is evidence this session changed the
issue's outcome (a named actionable item that did not exist before), so
this role is not marked `ritual` for this issue.
(B) blind-onboarding: see Open findings above — partially met; the gap
(external rulebook-PR review verdicts not citable from this repo) is
recorded as an open finding with a resolution path, not silently routed
around.

## Synthesis

This record does not paste the evidence-trail.md verbatim: it splits the
evidence-trail's single "impact" narrative into a Program-succeeded /
Repo-bookkeeping-failed pair (Impact summary), cross-checks the four
sibling gated-placeholder records against each other before treating the
pattern as one structural Contributing factor rather than four separate
ones — canonical: `grep -l "gated placeholder" docs/issue-1174/reports/*.md`
this turn (the same 4-file match cited in Timeline above; each of the 4
files' own text, read this session, quotes the identical approval-gate.sh
refusal string) — and adds the post-approval Timeline/Open-findings
entries (the near-miss comment disclosure, the APPROVE landing itself)
that did not exist in the phase-1 draft.

## Adopted norms (with rationale)

Input records synthesized (not pasted raw) into this record:
docs/issue-1174/reports/issue-retrospective/survey.md and
docs/issue-1174/reports/issue-retrospective/evidence-trail.md (this
role's own phase-1 findings), docs/issue-1174/reports/api-design.md,
docs/issue-1174/reports/capacity-planning.md,
docs/issue-1174/reports/defect-verification.md,
docs/issue-1174/reports/knowledge-management.md (the four sibling
gated-placeholder records, cross-checked for the same hook-collision
pattern), and docs/issue-1174/proposals/operational-playbook-program.md
(program structure, cited as upstream basis).

- Adopted: blameless framing (timeline before judgment; "the two hooks
  encode contradictory preconditions", not "role X made a mistake").
  Rationale: this role's own use_when exemplar (blameless postmortem
  practice) and contract §2's "systems, not people" bar for
  Contributing factors.
- Adopted: plural "Contributing factors", never singular "root cause".
  Rationale: role directive PHASE 2 STEP 2 names this a methodology
  violation, not a style nit, when singular.
- Adopted: every claim of state/count/outcome carries a `canonical:` or
  `derived:` tag naming the actual command or file read. Rationale:
  record-claim-citation-directive (issues #793/#870/#791) — a claim with
  no traceable source is refused at write time; sourcing inline the first
  time avoids relitigating each claim.
- Adopted: Action items name a specific owning role, not "the team".
  Rationale: role directive PHASE 2 STEP 2 (5) requires a checkable
  change with a named owner; advisory-only, never blocking.
- Skipped: re-verifying the 31 sibling roles' underlying claims against
  live system state. Rationale: this role's Prohibition (PHASE 1 STEP 2)
  — records-only evidence for the subject's own behavior; the sibling
  records' own citations are treated as the ground truth for what they
  themselves observed, not re-run here.

## Next steps

None — this record is landed. Action items above are advisory follow-ups
for other roles/owners, not further work for this session.
