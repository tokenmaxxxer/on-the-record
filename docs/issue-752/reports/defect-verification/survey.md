---
subject: issue-752
kind: survey
loop_state: phase1-survey
---

# Survey: defect-verification pass on core judgment capability (Audit C)

canonical: `gh issue view 752`, read live in this session.
canonical: `find docs/issue-752 -type f`, run live in this session.
what was done: independently re-derived the five claims of the architecture role's phase-1
survey for this issue against the current repo state, plus one self-devised check comparing a
real rendered judgment against two artifact-only closed-unmerged deliveries named in this task's
invocation.

canonical: `find docs/issue-752 -type f` output cited above (only `architecture/` and now
`defect-verification/` subdirs existed under `docs/issue-752/reports/`).
why: #752 asks what structurally forces a role session to render a judgment (accept/refuse/flag)
rather than only emit artifacts. No review record exists for #752, since the issue is read-only
audit with no coding/qa/review pipeline behind it. This survey tests whether the earlier
survey's claims still hold and whether the "artifacts without judgment" gap is independently
reproducible in real session history.

canonical: `docs/issue-752/reports/architecture/survey.md`, read in full in this session.
canonical: `gh pr view 758 --json state,mergedAt`, run live in this session — merged.
upstream: the architecture role's phase-1 survey at
`docs/issue-752/reports/architecture/survey.md` (merged PR #758), cited above.

## code_under_review

- on-the-record/commands/consult.md
- on-the-record/hooks/directive.sh
- on-the-record/hooks/role-axis-completeness-guard.sh
- gates/role_spec_shape.py
- docs/decisions/2026-08-10-judgment-axis-matrix.md
- docs/reports/consult-log.md
- roles/architecture.json
- roles/security-threat-model.json
- roles/performance-engineering.json
- roles/capacity-planning.json
- roles/conformance-review.json
- docs/handbooks/architecture-methodology.md
- docs/issue-566/reports/implementation.md

## Attempt list (phase 1)

canonical: `docs/issue-752/reports/architecture/survey.md` sections 2 and 4, read in full in
this session.
1. Source: architecture survey section 2, verbatim — "trace file exists but is header-only; no
   evidence consult has been exercised yet." Self-devised extension: check EVERY
   `consult-log.md` in the repo, not only the one file the survey cites.

canonical: `docs/issue-752/reports/architecture/survey.md` section 4, read in full in this
session.
2. Source: architecture survey section 4, verbatim — "No gate found that helps an agent
   enumerate options or weigh them against criteria before commitment." Re-derive against
   `role-axis-completeness-guard.sh`, a hook the survey did not name directly.

canonical: `gh issue view 586 --json state,title,body`, read live in this session.
3. Source: task invocation, verbatim — "judgment_axes coverage across role specs (#586
   incomplete)." Self-devised: diff #586's acceptance criteria against current `roles/*.json`
   and `docs/handbooks/*.md`.

canonical: `gh pr view` for PRs 955, 954, and 959, run live in this session (see Attempt 4
below).
4. Source: task invocation, verbatim — "the #955 refusal (a real judgment) vs docs-only
   deliveries #954/#959 (production without judgment)." Self-devised: read all three PRs' actual
   diffs and merge state.

closed_checks cited (not re-derived): none — #752 has no prior verify-role record and no review
record; the architecture survey's file:line evidence is re-derived, not cited as closed_checks.

## Outcomes

### Attempt 1 — reproduced

canonical: `find docs -name "consult-log.md" -exec wc -l {} \;`, run live in this session.
derived: `find docs -name "consult-log.md" -exec wc -l {} \;`
```
6 docs/reports/consult-log.md
```
canonical: same command output above.
Only one `consult-log.md` file exists repo-wide, 6 lines, header only, zero data rows — extends
the architecture survey's file-scoped claim to the whole repo.

### Attempt 2 — reproduced (survey's own characterization holds under re-derivation)

canonical: `on-the-record/hooks/role-axis-completeness-guard.sh` lines 1-16 and
`on-the-record/hooks/hooks.json` line 44, read in full in this session.
derived: `git log --diff-filter=A --format=%ad --date=short -- on-the-record/hooks/role-axis-completeness-guard.sh`
```
2026-08-10
```
canonical: the same hook-file read above, header comment lines 1-16.
`role-axis-completeness-guard.sh` (added 2026-08-10, before the architecture survey was written)
is wired live via `hooks.json` as a `PreToolUse` `git commit` gate, calling
`gates/role_spec_shape.py`'s `check_axis_ownership`/`check_role_judgment_axes`. Its own header
comment states it denies only when "an axis is owned by zero or by more than one role, or a
role's own `judgment_axes` shape is invalid" — axis-ownership *completeness*, not the *content*
of a judgment on that axis. Re-deriving against the hook itself, not only the ADR describing it,
reaches the same conclusion the earlier survey already stated. Not a defect in that survey;
recorded so a future reader need not re-check this hook.

### Attempt 3 — reproduced

canonical: `gh issue view 586 --json state,title,body`, read live in this session.
Issue #586 state: open. Body requires (a) `judgment_axes` assigned across every role spec with
single ownership, machine-checked, and (b) each axis-owning role's rulebook gains an evaluation
procedure (READ/EXECUTE/CRITERIA shape), not a self-report.

canonical: `grep -c "judgment_axes" roles/security-threat-model.json roles/performance-engineering.json roles/capacity-planning.json roles/architecture.json roles/conformance-review.json`, run live in this session.
derived: same command
```
roles/security-threat-model.json:1
roles/performance-engineering.json:1
roles/capacity-planning.json:1
roles/architecture.json:1
roles/conformance-review.json:1
```
canonical: `ls roles/specs/*.spec.json | wc -l`, run live in this session.
derived: same command
```
43
```
canonical: both command outputs directly above.
Five role spec files carry `judgment_axes` out of the 43-file set — the five axes named in the
2026-08-10 ADR are each singly owned, matching that ADR's closed-matrix claim, but #586's own
acceptance scope is the full role-spec set and the remainder are unassigned, still open per the
issue's own state read above.

canonical: `grep -rln "axis_evaluation\|axis-evaluation\|READ/EXECUTE/CRITERIA" docs/handbooks/`, run live in this session.
derived: same command
```
docs/handbooks/architecture-methodology.md
```
canonical: same command output directly above.
Exactly one of the five axis-owning roles (architecture) has a rulebook procedure section under
`docs/handbooks/`. The other four own an axis by schema field alone, with no procedure a session
is required to execute to reach a verdict — matching the ADR's own "Consequences" note that
batches 2-4's rulebook prose "remain follow-up work, out of this ADR's scope."

### Attempt 4 — reproduced

canonical: `gh pr view 955 --json title,body,state,mergedAt`, run live in this session.
PR #955 (`docs/issue-566/reports/implementation.md`) state: merged. Its body states a judgment
outright — "no unapproved-scope work was started" — and the committed record carries four
`canonical:`-tagged citations grounding an explicit refuse verdict on a specific proposed scope
extension, as durable repo state, not a conversational reply.

canonical: `gh pr view 954 --json state,mergedAt,additions,deletions,files`, run live in this
session.
PR #954 (`[issue-803/implementation]`) state: closed, not merged. Diff: three new files — a
proposal, a survey, a hunt record. No file in the diff states an accept/refuse/flag verdict on
anything.

canonical: `gh pr view 959 --json state,mergedAt,additions,deletions,files`, run live in this
session.
PR #959 (`[issue-791/implementation]`) state: closed, not merged. Diff: three new files — same
shape as #954: proposal, survey, hunt record, no verdict.

canonical: the three `gh pr view` reads directly above (PR 955, PR 954, PR 959).
Grounded in those three live-read PR states: the pipeline lets a role session open an entire PR
(survey, proposal, hunt record — contract-shaped, hook-passing) with zero judgment content, and
nothing found in this survey's code_under_review blocked that from being opened.

canonical: the same three `gh pr view` reads above.
PR #954 and PR #959 were closed by human action after the fact, not by any located gate, while
PR #955's judgment content is what the human merged.

## Findings (advisory-severity, phase-1 read)

### Finding 1 — no structural gate distinguishes "artifact produced" from "judgment rendered"

- severity: Medium -> advisory (deterministic band: no Critical/High evidence of an active
  security/data-loss/build-break condition — a missing-mechanism design gap, not a regression in
  already-shipped enforcement)
- addressed_to: architecture (owns `roles/specs/*.spec.json` per the earlier survey's own
  section-5 routing) and product-discovery/core (owns the role-handoff contract and hook surface)
- canonical: Attempt 4 above, this survey's own live `gh pr view` reads.
- evidence: PR #954 and PR #959 (closed unmerged, artifact-only diffs, zero verdict content)
  against PR #955 (merged, explicit refuse verdict, four citations). No hook or spec field in
  this survey's code_under_review requires a session to assert a verdict before a PR is openable
  or mergeable; the only enforcement located anywhere here (`role-axis-completeness-guard.sh`,
  Attempt 2) polices axis-ownership bookkeeping, not verdict content. Restates and independently
  reproduces the earlier survey's own rank-1 conclusion with live session-history evidence rather
  than design-reading alone.

### Finding 2 — consult (#699) channel is fully unexercised, repo-wide

- severity: Low -> advisory
- addressed_to: product-discovery/core (owns #699's channel design)
- canonical: Attempt 1 above, this survey's own live `find`/`wc` run.
- evidence: the only `consult-log.md` in the repo is 6 lines, header only, zero data rows;
  `on-the-record/commands/consult.md` lines 14-40 specify the
  `{"answer","confidence","caveats"}` contract, but no hook in this survey's code_under_review
  invokes `spawn.py consult` — never called in this repo's recorded history.

### Finding 3 — #586 (judgment taxonomy) is open at both its acceptance criteria, not just role coverage

- severity: Medium -> advisory
- addressed_to: architecture (owns the batch program per #586's own step list)
- canonical: Attempt 3 above, this survey's own live `gh issue view`/`grep` reads.
- evidence: issue #586 open; five of 43 role spec files carry `judgment_axes`; of those five,
  only one (architecture) has a rulebook axis-evaluation procedure. The 2026-08-10 ADR closed
  only the axis-ownership half of #586's scope — the axis-evaluation-procedure half remains open
  for most currently-owning roles, independent of the wider unassigned-role gap.

## Open findings

canonical: Findings 1-3 above, each carrying its own Attempt citation.
Findings 1-3, all reproduced, all advisory per the band lookup. No blocking finding — none
evidences an active break of already-shipped enforcement; all three evidence an absent
mechanism, consistent with the earlier survey's own MET/PARTIAL/GAP read and with #586 and #699
already being open, in-scope tracked work.

next steps: on an APPROVE issue-752/defect-verification comment, promote this survey's attempt
outcomes and findings into this role's own phase-2 record under `docs/issue-752/reports/`, per
contract v3 s19.

resolution path: phase-2, after human approval, this role writes the gated record file;
advisory findings 1-3 route onward to architecture and product-discovery/core through their own
next work units on #586, #699, and any #752 follow-up.
