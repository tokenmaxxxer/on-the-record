---
subject: issue-752
kind: verify-record
loop_state: cleared
---

# defect-verification record: core judgment capability (Audit C, #752)

canonical: `gh issue view 752`, read live in this session.
canonical: APPROVE issue-752/defect-verification, posted as an issue comment, read live via
`gh issue view 752 --comments` in this session.
what was done: promoted the already-gathered phase-1 survey at
`docs/issue-752/reports/defect-verification/survey.md` (merged in PR #967) into this gated
phase-2 record, per the approved proposal at
`docs/issue-752/proposals/2026-08-12-defect-verification-audit-c.md`. No new attempts run; this
record adds >=3-line verbatim excerpts backing each of the three findings, per record_lint #963.

why: #752 asks what structurally forces a role session to render a judgment rather than only
produce an artifact.

canonical: `docs/issue-752/reports/architecture/survey.md`, read in full in the phase-1 session.
This role's job is to independently reproduce the architecture role's merged phase-1 survey
claims (PR #758) against live repo state, never to re-litigate its per-requirement verdicts or
propose a fix.

canonical: same architecture-survey read above.
upstream: the architecture role's phase-1 survey, merged PR #758; this role's own phase-1
survey and proposal, merged PR #967.

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

## Attempt list

canonical: `docs/issue-752/reports/architecture/survey.md` sections 2 and 4, read in full in the
phase-1 session.
1. Source: architecture survey section 2, verbatim — "trace file exists but is header-only; no
   evidence consult has been exercised yet." Self-devised extension: check EVERY
   `consult-log.md` in the repo, not only the one file the survey cites.

canonical: `docs/issue-752/reports/architecture/survey.md` section 4, read in full in the
phase-1 session.
2. Source: architecture survey section 4, verbatim — "No gate found that helps an agent
   enumerate options or weigh them against criteria before commitment." Re-derive against
   `role-axis-completeness-guard.sh`, a hook the survey did not name directly.

canonical: `gh issue view 586 --json state,title,body`, run live in the phase-1 session.
3. Source: task invocation, verbatim — "judgment_axes coverage across role specs (#586
   incomplete)." Self-devised: diff #586's acceptance criteria against current `roles/*.json`
   and `docs/handbooks/*.md`.

canonical: `gh pr view` for PRs 955, 954, and 959, run live in the phase-1 session.
4. Source: task invocation, verbatim — "the #955 refusal (a real judgment) vs docs-only
   deliveries #954/#959 (production without judgment)." Self-devised: read all three PRs' actual
   diffs and merge state.

closed_checks cited (not re-derived): none — #752 has no prior verify-role record and no review
record; the architecture survey's file:line evidence is re-derived, not cited as closed_checks.

## Outcomes

### Attempt 1 — reproduced

canonical: `find docs -name "consult-log.md" -exec wc -l {} \;`, run live in the phase-1
session.
derived: `find docs -name "consult-log.md" -exec wc -l {} \;`
```
6 docs/reports/consult-log.md
```
canonical: same command output above.
Only one `consult-log.md` file exists repo-wide, 6 lines, header only, zero data rows — extends
the architecture survey's file-scoped claim to the whole repo.

### Attempt 2 — reproduced (survey's own characterization holds under re-derivation)

canonical: `on-the-record/hooks/role-axis-completeness-guard.sh` lines 1-16 and
`on-the-record/hooks/hooks.json` line 44, read in full in the phase-1 session.
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

canonical: `gh issue view 586 --json state,title,body`, run live in the phase-1 session.
Issue #586 state: open. Body requires (a) `judgment_axes` assigned across every role spec with
single ownership, machine-checked, and (b) each axis-owning role's rulebook gains an evaluation
procedure (READ/EXECUTE/CRITERIA shape), not a self-report.

canonical: `grep -c "judgment_axes" roles/security-threat-model.json roles/performance-engineering.json roles/capacity-planning.json roles/architecture.json roles/conformance-review.json`, run live in the phase-1 session.
derived: same command
```
roles/security-threat-model.json:1
roles/performance-engineering.json:1
roles/capacity-planning.json:1
roles/architecture.json:1
roles/conformance-review.json:1
```
canonical: `ls roles/specs/*.spec.json | wc -l`, run live in the phase-1 session.
derived: same command
```
43
```
canonical: both command outputs directly above.
Five role spec files carry `judgment_axes` out of the 43-file set — the five axes named in the
2026-08-10 ADR are each singly owned, matching that ADR's closed-matrix claim, but #586's own
acceptance scope is the full role-spec set and the remainder are unassigned, still open per the
issue's own state read above.

canonical: `grep -rln "axis_evaluation\|axis-evaluation\|READ/EXECUTE/CRITERIA" docs/handbooks/`, run live in the phase-1 session.
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

canonical: `gh pr view 955 --json title,body,state,mergedAt`, run live in the phase-1 session.
PR #955 (`docs/issue-566/reports/implementation.md`) state: merged. Its body states a judgment
outright — "no unapproved-scope work was started" — and the committed record carries four
`canonical:`-tagged citations grounding an explicit refuse verdict on a specific proposed scope
extension, as durable repo state, not a conversational reply.

canonical: `gh pr view 954 --json state,mergedAt,additions,deletions,files`, run live in the
phase-1 session.
PR #954 (`[issue-803/implementation]`) state: closed, not merged. Diff: three new files — a
proposal, a survey, a hunt record. No file in the diff states an accept/refuse/flag verdict on
anything.

canonical: `gh pr view 959 --json state,mergedAt,additions,deletions,files`, run live in the
phase-1 session.
PR #959 (`[issue-791/implementation]`) state: closed, not merged. Diff: three new files — same
shape as #954: proposal, survey, hunt record, no verdict.

canonical: the three `gh pr view` reads directly above (PR 955, PR 954, PR 959).
Grounded in those three live-read PR states: the pipeline lets a role session open an entire PR
(survey, proposal, hunt record — contract-shaped, hook-passing) with zero judgment content, and
nothing found in this survey's code_under_review blocked that from being opened.

canonical: the same three `gh pr view` reads above.
PR #954 and PR #959 were closed by human action after the fact, not by any located gate, while
PR #955's judgment content is what the human merged.

## Findings (advisory-severity)

### Finding 1 — no structural gate distinguishes "artifact produced" from "judgment rendered"

- severity: Medium -> advisory (deterministic band: no Critical/High evidence of an active
  security/data-loss/build-break condition — a missing-mechanism design gap, not a regression in
  already-shipped enforcement)
- addressed_to: architecture (owns `roles/specs/*.spec.json` per the earlier survey's own
  section-5 routing) and product-discovery/core (owns the role-handoff contract and hook surface)
- canonical: Attempt 4 above, this record's own live `gh pr view` reads.
- evidence (verbatim, `on-the-record/hooks/role-axis-completeness-guard.sh` lines 9-13, the only
  gate located anywhere in this record's code_under_review that touches judgment-adjacent
  content):
  ```
  # (issue-573) are real, unit-tested functions with zero operational
  # caller — the exact dead-code class already fixed once in #594/#586, now
  # recurring. This hook wires a real caller: on a `git commit` attempt it
  # reads the staged `roles/*.json` set (git show :<path> for staged paths,
  # falling back to the working tree for any roles/*.json not itself staged,
  # since axis ownership is evaluated across the WHOLE set) and denies the
  # commit when an axis is owned by zero or by more than one role, or a
  ```
  canonical: the same hook-file excerpt directly above, plus Attempt 4's three `gh pr view`
  reads.
  This gate denies on missing/duplicate axis *ownership bookkeeping* only — it has no branch
  that inspects a PR's diff content for a rendered verdict. No hook or spec field anywhere in
  this record's code_under_review requires a session to assert a verdict before a PR is openable
  or mergeable.

  canonical: Attempt 4's three `gh pr view` reads above (PR 955, PR 954, PR 959).
  PR #954 and PR #959 (closed unmerged, artifact-only diffs, zero verdict content) against PR
  #955 (merged, explicit refuse verdict, four citations) is live proof the gap is not
  theoretical. Restates and independently reproduces the earlier survey's own rank-1 conclusion
  with live session-history evidence rather than design-reading alone.

### Finding 2 — consult (#699) channel is fully unexercised, repo-wide

- severity: Low -> advisory
- addressed_to: product-discovery/core (owns #699's channel design)
- canonical: Attempt 1 above, this record's own live `find`/`wc` run.
- evidence (verbatim, the entire contents of the repo's only `consult-log.md`,
  `docs/reports/consult-log.md`, all 6 lines):
  ```
  # Consult trace log

  One line per `spawn.py consult` call made with no `--issue` (issue-scoped
  calls trace to `docs/issue-<n>/reports/consult-log.md` instead) — success
  or failure alike. See `on-the-record/commands/consult.md` and
  `spawn.py:consult_cmd`. Appended by `spawn.py`, never hand-edited.
  ```
  The file is header-only prose describing the log format — zero appended data rows exist, i.e.
  zero recorded `spawn.py consult` calls repo-wide. `on-the-record/commands/consult.md` lines
  14-16 (verbatim) describe exactly the judgment-channel role this gap leaves unexercised:
  ```
  **자문(consult)** 은 역할의 룰북을 로드해 판단 하나를 돌려받는 것이다
  (이슈 #699 R1) — `spawn.py <역할> "<일>" --issue <n>` 이 여는
  issue → 브랜치 → 커밋 → PR 파이프라인 전체가 아니라, 질문 하나에 답 하나다.
  ```
  ("Consult loads a role's rulebook and returns one judgment... one question, one answer" — the
  channel exists as spec but has zero recorded invocations.)

### Finding 3 — #586 (judgment taxonomy) is open at both its acceptance criteria, not just role coverage

- severity: Medium -> advisory
- addressed_to: architecture (owns the batch program per #586's own step list)
- canonical: Attempt 3 above, this record's own live `gh issue view`/`grep` reads.
- evidence (verbatim, `docs/handbooks/architecture-methodology.md` lines 42-45, the only
  axis-evaluation procedure section found anywhere under `docs/handbooks/`):
  ```
  rulebook session fills the four blanks (READ/EXECUTE/CRITERIA/CITATION)
  for its own axis using its own domain knowledge. `EXECUTE` steps must be
  mechanical (read a file, run a diff, check a field) so the verdict is
  "expertise exercised," not a self-report; a step that reduces to
  ```
  canonical: same handbook excerpt directly above, plus Attempt 3's `grep -c`/`ls` reads.
  Five of 43 role spec files carry `judgment_axes`; of those five, only architecture has this
  kind of procedure section — security-threat-model, performance-engineering,
  capacity-planning, and conformance-review each own an axis by schema field alone, with no
  mechanical READ/EXECUTE/CRITERIA procedure a session must run to reach a verdict.

  canonical: Attempt 3's `grep -c` (5-file count) and `ls roles/specs/*.spec.json | wc -l`
  (43-file count) reads above.
  derived: `python3 -c "print(43-5)"`
  ```
  38
  ```
  canonical: same derived count directly above, plus Attempt 3's `gh issue view 586` read.
  The 2026-08-10 ADR closed only the axis-ownership half of #586's scope, per that issue read;
  the derived count above is the role-spec count with no `judgment_axes` field at all, and the
  axis-evaluation-procedure half remains open for four of the five roles that do own an axis.

## Open findings

canonical: Findings 1-3 above, each carrying its own Attempt citation and verbatim excerpt.
Findings 1-3, all reproduced, all advisory per the deterministic band lookup. No blocking
finding — none evidences an active break of already-shipped enforcement; all three evidence an
absent mechanism, consistent with the earlier architecture survey's own MET/PARTIAL/GAP read and
with #586 and #699 already being open, in-scope tracked work.

## Eligibility for cleared

canonical: Open findings section directly above.
No unresolved blocking finding exists (all three findings are advisory), so this record is
eligible for `loop_state: cleared` without a human waiver.

next steps: none for this role — findings 1-3 route onward to architecture and
product-discovery/core through their own next work units on #586, #699, and any #752 follow-up.

open findings resolution path: findings 1-3 resolve through architecture's and
product-discovery/core's own future work on #586 (judgment-axis rollout) and #699 (consult
channel adoption) — not through further action by this role.

Proposal: docs/issue-752/proposals/2026-08-12-defect-verification-audit-c.md
