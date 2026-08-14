---
subject: issue-301
role: execution-observation
observed_role: implementation
observed_pr: 302
phase: 1
---

# Observation plan — issue #301, PR #302 (`implementation` role, B2 half)

## Verdict levels this plan will render (declared before any evidence)

Phase 2 will render all three levels of the role-handoff contract's
verdict, each against the evidence named beside it. No level is rendered
here, and no provisional judgment of PR #302 appears anywhere in this
document.

1. **Outcome** — did commits `d1a3293` (phase 1, survey + proposal) and
   `5ea00d1` (phase 2, code) land what issue #301's three acceptance items
   ask, one item at a time. Evidence: issue #301's body text (three items:
   push-rejection distinguishability; workflow-push capability or a
   contract statement naming who has it; the stranded `issue-290/implementation`
   work landing), `git show 5ea00d1 -- spawn.py`, `git show 5ea00d1 --
   tests/test_spawn.py`, `d1a3293:docs/issue-301/reports/implementation.md`,
   re-running `python3 -m pytest tests/test_spawn.py -k EnsurePushedResult`
   against the current tree, and `gh pr list --search "issue-290"` for the
   third item.
2. **Trajectory** — was the observed role's phase-1 → phase-2 path sound.
   Evidence: commit dates on `issue-301/implementation`, the issue-301
   comment whose entire body is `APPROVE issue-301/implementation` with its
   author/association/timestamp (`gh issue view 301 --json comments`),
   `docs/specs/approvers.md`, and `gh pr view 302 --json files` against the
   proposal's frozen write set.
3. **Step** — which specific artifact, if any, is deficient. Evidence:
   whichever check below does not close, carried in the four-part
   blameless shape (impact, timeline/root cause, action item). Includes
   whether the issue's own closure (via PR #302's `Closes #301`) is
   supported by all three acceptance items being met, given B1 (workflow
   scope) is explicitly out of scope for this PR.

## Request

Issue #301's `## 실행 계획` step 2 is `execution-observation` for PR #302.
The invoking scope fixes two judgment items: (a) whether `ensure_pushed`'s
new `{"status", "reason"}` return and `_spawn_one`'s `push-rejected`
upgrade actually produce, for the three scenarios the issue names, events
and ledger rows distinguishable from `silent-failure`, with no existing
`session-end` event consumer broken by the payload widening from a bare
string to a dict; (b) whether issue #301's closure is fully backed —
specifically, whether acceptance item 2 (workflow-push capability or a
named contract statement) is met anywhere in the repo, since PR #302 itself
declares it out of scope.

## Constraints

- **No re-execution beyond re-running the delivered tests.** Admissible
  evidence is the commits' diff text, the observed role's own record and
  survey, the issue/PR text and comments, and `python3 -m pytest
  tests/test_spawn.py -k EnsurePushedResult` run against the current
  working tree (the delivered test file itself, not new tests authored by
  this role).
- **No edits outside this role's own paths.** Nothing under `spawn.py`,
  `tests/test_spawn.py`, `docs/issue-301/proposals/2026-08-07-push-rejection-visibility.md`,
  or `docs/issue-301/reports/implementation*` is written or edited.
- **No issue filing.** Contract v3: issues are user-authored only. Any
  confirmed deficiency (including the acceptance-item-2 gap) returns as a
  finding in this role's record for the human to judge.
- **Citation adjacency.** Every verdict-bearing sentence in the phase-2
  record names its source (SHA, `file:line`, comment URL, or a `derived:`
  command) adjacent to the verdict, and the independence statement
  precedes all verdict language.
- **Phase gating.** `docs/issue-301/reports/execution-observation.md` is
  phase-2 output, written only after an approvers.md-listed account posts
  an issue comment on #301 whose entire body is exactly
  `APPROVE issue-301/execution-observation` (single-account mode) or a PR
  Approve review on this branch's PR.

## Checks planned for phase 2

1. **`three-scenario-distinguishability`** — for each of the three
   scenarios the issue names (rejected push, unpushed-for-another-reason,
   genuinely-nothing), confirm the delivered test asserts a distinct
   `outcome` label and re-run it against the current tree.
2. **`session-end-consumer-sweep`** — grep the current `spawn.py` for every
   reader of a `session-end` event's `detail` field and confirm none reads
   it as a bare string in a way the new dict payload would break.
3. **`acceptance-item-2-closure-check`** — grep `docs/**/*.md` for any
   statement that role sessions can or cannot push workflow files, dated at
   or after issue #301's closure, and check the issue's own timeline event
   for whether the closing PR's body qualifies the closure as partial.
4. **`stranded-work-landed-check`** — confirm via `gh pr list --search
   "issue-290"` and `git log --all` that the commits issue #301's body
   names as stranded actually landed, and on what PR/date relative to
   PR #302.

## Out of scope

- Any change to `spawn.py` or `tests/test_spawn.py`. This role does not
  fix.
- B1 (the missing `workflow` OAuth scope) itself — out of scope for the
  observed PR and for this observation; only whether its acceptance-item
  status is accurately reflected is in scope.
- The phase-2 record itself, written only after approval.

## How you'll know it worked

- `docs/issue-301/reports/execution-observation.md` exists on this branch,
  committed, with the independence statement preceding every
  verdict-bearing sentence, and all three levels — outcome, trajectory,
  step — addressed explicitly.
- Each of the four checks above is answered in the record with an adjacent
  citation.
- The acceptance-item-2 question is answered with a definite yes/no plus
  citation, not left implicit.
