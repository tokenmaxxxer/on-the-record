---
subject: issue-322
role: execution-observation
observed_role: implementation
observed_pr: 351
phase: 1
---

# Observation plan — issue #322, PR #351 (`implementation` role)

Survey: `docs/issue-322/reports/execution-observation/survey.md` (facts,
scout-skip record, three open questions this plan answers below).

## Verdict levels this plan will render (declared before any evidence)

Phase 2 renders the three verdict levels this repo's role-handoff contract
uses, each against evidence named here in advance. No verdict, provisional or
otherwise, appears in this document.

1. **Outcome** — did commits `2c27d14` / `539dad6` / `abd6e71` (PR #351) land
   what issue #322 asked. Evidence: issue #322's body and Acceptance section,
   `git show abd6e71 -- ledger/decisions.py ledger/test_decisions.py`, and
   `docs/issue-322/reports/implementation.md`.
2. **Trajectory** — was the `implementation` role's phase-1 → phase-2 path
   sound: survey/scout before proposal, a real approval before phase-2 work,
   and phase-2 output confined to the approved write set. Evidence: commit
   order/timestamps, the issue comment whose entire body is exactly
   `APPROVE issue-322/implementation` (author, association, timestamp via
   `gh api .../issues/322/comments`), `docs/specs/approvers.md`, and
   `docs/issue-322/reports/implementation/survey.md`.
3. **Step** — which specific artifact, if any, is deficient: `ledger/decisions.py`,
   `ledger/test_decisions.py`, or the record's own claims. Any level found not
   to apply is written as "not applicable, because X" rather than omitted.

## Request

Issue #322's Acceptance clause (added per #310) requires an executable artifact
that fails when the requirement regresses, not prose. `ledger/decisions.py` +
`ledger/test_decisions.py` are that artifact. This role's own spec
(`roles/specs/execution-observation.spec.json`) is explicitly about whether the
landed thing **actually runs** — EARL-shaped: `subject`/`test` refs resolving to
a repo path or a command actually run, `result` from a fixed enum, worst-case
recomputation across cited entries. Phase 2 will therefore re-run the two
commands this issue's acceptance names and cite their live output, not just
read the implementation record's transcription of a prior run:

- `python3 ledger/test_decisions.py` — the paired fixture suite (6 tests).
- `python3 ledger/decisions.py .` — run against this repo's own real
  `docs/issue-*/reports/*.md` history, the corpus the tool exists to mine.

This re-execution is not a deviation from this role's usual no-re-execution
posture (contrast `docs/issue-235/proposals/execution-observation-plan.md`'s
"No re-execution" constraint) — it is what this specific role's spec and this
specific issue's acceptance clause both ask for: the tool's entire claim is
that it runs and exits non-zero on a real unconfirmed recurrence, and that
claim is only checkable by running it.

## Constraints

- **No re-execution beyond the two named commands above.** No editing of
  `ledger/decisions.py`/`ledger/test_decisions.py` to explore behavior beyond
  what those two invocations plus reading their source shows.
- **No edits outside this role's own paths.** Nothing under `ledger/`,
  `docs/issue-322/proposals/2026-08-07-decision-mining.md`, or
  `docs/issue-322/reports/implementation*` is written or edited.
- **No issue filing.** Contract v3: issues are user-authored only. A confirmed
  deficiency is reported as a finding in this role's own record for the human
  to judge.
- **Citation adjacency.** Every verdict-bearing sentence in the phase-2 record
  cites a SHA, `file:line`, comment URL, or a command actually run, adjacent to
  the verdict.
- **Phase gating.** `docs/issue-322/reports/execution-observation.md` is
  phase-2 output — not written until an approver listed in
  `docs/specs/approvers.md` posts a PR Approve review on this branch's PR, or
  (single-account mode) an issue comment on #322 whose entire body is exactly
  `APPROVE issue-322/execution-observation`.

## What phase 2 checks, beyond a bare pass/fail

- **Acceptance-clause fit.** #322's Acceptance text asks specifically for an
  artifact that "fails when this regresses" and, if not mechanically checkable,
  a record saying so and why. `python3 ledger/test_decisions.py` exercises the
  regression case directly (`t_second_occurrence_across_subjects_flags_and_exits_nonzero`)
  — check that this test's assertion actually reproduces the shape #322
  describes (a correction repeated across distinct subjects with no confirmed
  `docs/decisions/*.md` entry), not a weaker proxy for it.
- **Live-corpus claim.** The implementation record's "Beyond its own acceptance
  criteria" section claims the tool "already found and named one genuine
  unconfirmed recurring correction that predates this build" (issue-218 /
  issue-220). Phase 2 re-runs `python3 ledger/decisions.py .` against the
  current branch tip and checks whether that specific claim still holds
  verbatim, or whether the live corpus has moved (more subjects landed further
  "What did not work" bullets since 2026-08-07) and the record's claim is now
  stale in either direction — fewer or more candidates than claimed.
- **Scope-of-mining check.** The proposal's Constraints commit to reading only
  `## What did not work` / `## Rationale for deviations` sections, mechanical
  substring matching, no LLM. Check that `ledger/decisions.py`'s source matches
  that commitment exactly (no semantic/fuzzy step slipped in) and that the
  `THRESHOLD`/`normalize()` behavior match what the record and tests claim for
  them.
- **Operator-authorship boundary.** Issue #322's central constraint is that a
  mined pattern is "a proposal, never a fact" and confirmation must stay a
  human act through an operator-authored `docs/decisions/*.md` entry. Check
  that nothing in `ledger/decisions.py` auto-writes to `docs/decisions/` or
  otherwise short-circuits that boundary — the tool's own exit code must be the
  only enforcement surface, with no write path of its own.

## Out of scope

- Any change to `ledger/decisions.py` or `ledger/test_decisions.py`. This role
  does not fix.
- Wiring the detector into a merge gate, or filing/confirming the
  issue-218/issue-220 (or any newly-surfaced) recurrence into
  `docs/decisions/*.md` — the implementation proposal explicitly deferred
  these; re-scoping them here would exceed this role's write set.
- The phase-2 record itself, written only after approval.

## How you'll know it worked

- `docs/issue-322/reports/execution-observation.md` exists on this branch,
  committed, with an independence statement preceding every verdict-bearing
  sentence, and all three levels — outcome, trajectory, step — addressed
  explicitly.
- Both named commands (`python3 ledger/test_decisions.py`,
  `python3 ledger/decisions.py .`) are cited with their actual exit code and
  output from a run executed in the phase-2 session, not transcribed from the
  implementation record.
- Every verdict-bearing sentence carries an adjacent SHA, `file:line`, comment
  URL, or command-output citation, and no code claim cites a working-tree path
  where a commit-blob citation is available instead.
- Any deficiency is recorded in the four-part blameless shape (impact,
  timeline, root cause, action item), and nothing under `ledger/` or the
  observed role's `docs/issue-322/` paths is modified.
