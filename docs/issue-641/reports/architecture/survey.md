# Current-state survey — issue #641: architecture (phase 1)

## The gap (confirmed by inspection)

`on-the-record/commands/run.md` step 6 ("PR 을 설명한다", lines 98-155) instructs the
orchestrator to read a role's PR/diff and produce a decision-support summary for the
operator (what changed, why, how verified, flow/stage/next framing, #320's
problem/cost/possible/remaining framing). Nothing in this section, or anywhere else in
run.md (`grep -n "review\|feedback\|검토\|비평" run.md` — only line 309's step-4 role
name and line 256's `gh pr review --approve` procedural mention), states that producing
*review findings on a deliverable* is different work from *summarizing a deliverable for
a decision*. The live consumer-repo evidence in the issue body is exactly this slide: an
orchestrator planning "제가 직접 검토해서 문제점 피드백을 PR 코멘트로 게시" under the
same step-6 instruction that legitimately asks it to summarize.

## Shipped machinery available to reuse (confirmed, not re-derived)

- `roles/conformance-review.json` — existing role, `decides: "산출물 vs 명세 일치"`,
  `use_when` fires on `board_condition: an implementation commit landed AND no
  conformance-review record exists yet for this commit sha`, `produces:` Present/Surface/
  Absent/Incorrect/Unverifiable per requirement with cited evidence, `write_scope:
  docs/issue-<n>/reports/conformance-review.md`. This is the role for spec-conformance
  review the issue names.
- `gates/role_spec_shape.py` `_JUDGMENT_AXES` (5, closed set, ownership matrix complete
  per `docs/decisions/2026-08-10-judgment-axis-matrix.md`, PR #590): `alignment` →
  conformance-review, `maintenance_complexity` → architecture, `external_burden` →
  capacity-planning, `attack_potential` → security-threat-model, `performance` →
  performance-engineering. This is the "axis panel" the issue names for methodology
  judgments.
- `check_open_decision_item` (function in `gates/role_spec_shape.py`, issue #609) — the
  shape a role uses to hand an unresolved item to the panel: `{item, source_role,
  source_path, candidate_axes}`, `candidate_axes` validated against `_JUDGMENT_AXES`. This
  is the "shipped triage machinery" (#573/#609) the issue points at: routing an open
  question to the role(s) that own the implicated axis/axes is already a mechanical lookup
  (`target_path` resolved against `write_scope`, unioned with `judgment_axes`, per
  `docs/issue-573/proposals/architecture.md` section 9), not something to reinvent.
- `on-the-record/hooks/delegated-judgment-gate.sh` — PreToolUse/Bash hook, zero-install
  (no `gates/` import, reversibility grade ported inline into the hook's own heredoc so it
  runs in a target repo that never clones this checkout). Confirmed firing conditions
  (script header, lines 24-32): `gh pr create` on an `issue-<n>/<role>` branch, and (issue
  #597) `gh pr merge` / `gh issue reopen <n>` / `gh issue close <n>`. **Not currently
  wired to fire on `gh pr comment`** — confirmed by grep, no case arm for it anywhere in
  the script. This is the natural extension point: it is already a PreToolUse hook that
  inspects orchestrator-issued `gh` Bash calls and posts its own audit comment without
  ever blocking the underlying command (fail-open posture, stated explicitly in its own
  header comment and in `_gh()`'s docstring).

## Detection-surface inventory (what else exists, and why each doesn't fit)

- `gates/claim_scan.py` (#476 H1) — scans *records/PR bodies already in the repo diff* for
  claim words (`reproduced|verified|confirmed|passed`) needing adjacent evidence. Built
  for evidence-adjacency, not review-authorship attribution; operates on committed text,
  not on an interactive `gh pr comment` call as it happens.
- `gates/pr_reference.py` (#126) — checks a PR body links back to its issue. Orthogonal:
  says nothing about who authored what inside the body.
- `gates/record_lint.py` / `record-claim-guard.sh` — govern `docs/issue-<n>/reports/<role>.md`
  record shape, not free-text PR comments.
- None of the file/diff-scoped gates can see a `gh pr comment` call before it posts — only
  a PreToolUse Bash hook (the same class `delegated-judgment-gate.sh` already is) sees the
  command text before it runs. This is the one honest detection point in the deployed
  surface today.

## Constraint this creates for the proposal

run.md's own #320 framing mandate (lines 138-143) *requires* the orchestrator's PR/board
summaries to state "어떤 문제가 해결/제거됐는가" (what problem was solved) — problem-shaped
language is not itself evidence of a violation; it is mandated decision-support prose. A
detector that fires on generic problem/issue vocabulary will collide with this mandate
constantly. Any detection design has to trigger on something narrower than "mentions a
problem" — confirmed as the key false-positive risk to state explicitly in the proposal's
detectability verdict, not discovered later as a surprise gate flood (the #419 precedent
already named in run.md line 539 for exactly this failure shape).
