# issue-retrospective — phase-1 proposal for issue #1174

status: approved
files:
  - docs/issue-1174/reports/issue-retrospective.md

## Intent

Write the round-end retrospective record for issue #1174 (the operational
playbook program): what its history shows went well, what failed, and
what pattern should change next time. Advisory only; does not re-litigate
any other role's verdict.

## Constraints

- Role directive PHASE 1 STEP 2: evidence is the subject's other role
  records ONLY — every docs/issue-1174/reports/*.md,
  docs/issue-1174/reports/<role>/*.md, and docs/issue-1174/proposals/*.md
  file on this branch, plus `gh issue view 1174` for the requirement text
  and comment history. No source outside these records or the issue/PR
  history will be opened.
- Round-end value gates (docs/handbooks/round-end-value-gates.md):
  (A) procedure-value — does this role cite evidence it changed the
  issue's outcome; (B) blind-onboarding — can a zero-context reader
  reconstruct what was asked/built/decided/next from records alone.
- Record body order is fixed: Timeline (records-only, precedes causal
  claims) → Impact summary → Contributing factors (plural, structural,
  never "root cause") → What we learned (must answer the
  recurred-prediction question) → Action items (required section, each
  item names a concrete owner).
- Phase 2 (the actual record content) is gated behind an "APPROVE
  issue-1174/issue-retrospective" comment from a docs/specs/approvers.md
  account per contract v3 s19.

## Named input records

- docs/issue-1174/reports/issue-retrospective/survey.md — the
  current-state survey (PHASE 1 STEP 2) this proposal's scout/current-
  state pass produced; names every record read and states the
  scout-skip rationale.
- docs/issue-1174/reports/issue-retrospective/evidence-trail.md — this
  role's own phase-1 findings, answers Timeline/Impact/Contributing
  factors/What we learned/Action items.
- docs/issue-1174/proposals/operational-playbook-program.md — answers
  Upstream basis (program structure, requirement text).
- docs/issue-1174/reports/api-design.md,
  docs/issue-1174/reports/capacity-planning.md,
  docs/issue-1174/reports/defect-verification.md,
  docs/issue-1174/reports/knowledge-management.md — the four sibling
  gated-placeholder records, cross-checked for whether the same
  hook-collision pattern recurs (answers the recurred-prediction
  question's within-issue variant).
- `gh issue view 1174 --json createdAt,updatedAt,comments,body` — answers
  Timeline dates and Acceptance-check text cited in Impact summary.
- `git log --oneline --all | grep issue-1174` — answers the commit-trail
  portion of Timeline.
- Round-end value gates: will be run and their verdict stated in the
  record's own "Round-end value gates" section (A and B, above).

## Synthesis (not raw paste)

The named records above are not one coherent narrative on their own: the
evidence-trail is this role's own draft, the four sibling
gated-placeholder records each independently document the *same* hook
collision from a different role's vantage point, and the program proposal
states the intended structure the collision then blocked. The proposed
record synthesizes these by (a) treating the sibling records as
independent replications of one structural finding rather than four
separate findings — cross-checking that each cites the identical
approval-gate.sh/pr-preflight.sh refusal text before folding them into a
single Contributing-factors claim; (b) separating what the program
achieved (31 external rulebook PRs — real, per each evidence-trail's own
`gh pr create` citation) from what this repo's bookkeeping failed to
capture (zero landed phase-2 records) — the evidence-trail conflates
these as one "impact" narrative, the proposed record's Impact summary
splits them explicitly; (c) resolving the recurred-prediction question at
two levels — no prior issue-retrospective record exists at all (this
repo's first), but within issue #1174 itself the same signal repeated 31+
times with no fix landing, which the record's own round-end gate (A)
treats as the load-bearing finding rather than a footnote.

## Adopted norms (with rationale)

- Adopted: blameless framing throughout (timeline before judgment,
  "systems, not people" in Contributing factors). Rationale: this role's
  use_when exemplar (blameless postmortem practice) and contract §2.
- Adopted: plural "Contributing factors", never singular "root cause".
  Rationale: role directive PHASE 2 STEP 2 names singular attribution a
  methodology violation, not a style nit.
- Adopted: every state/count/outcome claim carries a `canonical:` or
  `derived:` tag citing the actual command/file read. Rationale:
  record-claim-citation-directive (issues #793/#870/#791) — sourcing
  inline the first time avoids a write-time refusal and a rewrite.
  Adopted from the same convention already used in this branch's sibling
  evidence-trail.md files (api-design, capacity-planning,
  defect-verification, knowledge-management), for consistency across the
  32 records this issue now carries.
- Adopted: Action items each name one concrete owning role, never "the
  team". Rationale: role directive PHASE 2 STEP 2 (5).
- Skipped/out of scope: re-verifying sibling roles' underlying claims
  against live system state, and fixing the hook collision itself.
  Rationale: this role's records-only prohibition, and contract's
  no-mid-task role-spawning rule (a retrospective files findings, it does
  not build fixes).

## Scout: skip statement

Scouting skipped. Reason: this role directive's PHASE 1 STEP 1 replaces
the generic scout-directive sweep by name for issue-retrospective — its
"platform scout protocol" here is the current-state survey plus the
recurred-prediction check, both already scoped above and executed in
docs/issue-1174/reports/issue-retrospective/survey.md and
docs/issue-1174/reports/issue-retrospective/evidence-trail.md's own "What
we learned" section. There is no separate scout-brief.md for this role;
the survey.md file is the equivalent artifact this role's own directive
substitutes.

## What will be done

Read the named records above, build the Timeline first, then Impact
summary, Contributing factors, What we learned (answering the
recurred-prediction question), and Action items (each with a named
owner) in that fixed order, run the round-end value gates, and write the
result to docs/issue-1174/reports/issue-retrospective.md once the
APPROVE comment is present.

## Out of scope

Fixing the pr-preflight.sh / approval-gate.sh collision itself (that is
an action item for requirements-engineering, not this role); re-verifying
sibling roles' claims against live system state (records-only
prohibition); re-litigating any other role's verdict.

## How you'll know it worked

docs/issue-1174/reports/issue-retrospective.md exists with all five
required sections in order, loop_state: landed, an Action items section
with named owners, and a Round-end value gates section stating both A and
B verdicts with citations.
