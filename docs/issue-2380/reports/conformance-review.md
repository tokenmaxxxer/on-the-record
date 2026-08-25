---
issue: 2380
role: conformance-review
author: conformance-review
loop_state: complete
upstream:
  - path: gates/merge_gate.py
    sha: 296cc92acc68ccbeb63fa757720137dbaea86256
  - path: gates/test_merge_gate.py
    sha: 296cc92acc68ccbeb63fa757720137dbaea86256
subject: PR #2444 (issue-2380/implementation, head 296cc92acc68ccbeb63fa757720137dbaea86256, base main)
test: on-the-record issue #2380 Acceptance section, 3 stated checks
result: passed
assertedBy: issue-2380/conformance-review session (builder-blind), 2026-08-26
---

# issue-2380 — conformance-review record

## What was done

Builder-blind conformance review of PR #2444
(`issue-2380/implementation` @ `296cc92acc68ccbeb63fa757720137dbaea86256`),
the implementation PR closing issue #2380. Extracted the issue's
Acceptance section into 4 checkable requirements (one implicit
scope-boundary requirement made explicit per
conformance-review-requirement-extraction rule 6, since a naive fix
could satisfy the literal wording while over-broadening the exemption),
picked a verification method per requirement, and rendered a verdict for
each. Each requirement subsection below carries its own evidence
citation.

### Requirement 1 — symmetric sibling exemption

requirement: `_exempt_own_role()`/`required_verification_missing()`
recognizes when the PR under evaluation's own branch role is one of the
two sibling observer roles (`execution-observation`,
`conformance-review`) and in that case exempts BOTH roles from
`missing`, symmetrically in either direction — not just its own role.
spec_ref: issue #2380 Acceptance, bullet 1 ("`required_verification_missing()`
... recognizes that a PR IS ITSELF one of the two required observer
records and exempts it from requiring its sibling be pre-merged ...
when both are open in the same review cycle")
verdict: Present
canonical: `296cc92acc68ccbeb63fa757720137dbaea86256:gates/merge_gate.py`
— diff hunk read this session via `gh pr diff 2444 --repo
tokenmaxxxer/on-the-record`, independently re-confirmed byte-for-byte by
a dispatched worker via `git show origin/issue-2380/implementation:gates/merge_gate.py`
diffed against `git show origin/main:gates/merge_gate.py`:
```diff
     if not own_branch or not own_branch.startswith(f"{subject}/"):
         return missing
     own_role = own_branch[len(subject) + 1:]
+    if own_role in spawn_on_pr.PR_TRIGGERED_ROLES:
+        return [r for r in missing if r not in spawn_on_pr.PR_TRIGGERED_ROLES]
     return [r for r in missing if r != own_role]
```
`PR_TRIGGERED_ROLES` confirmed as exactly `("execution-observation",
"conformance-review")` by direct Read of `gates/spawn_on_pr.py:39` on
this session's own branch (main-based; this constant predates and is
unchanged by PR #2444).
acceptance: `python3 -m pytest gates/test_merge_gate.py -q` (dispatched
worker, isolated `git worktree` checkout of
`origin/issue-2380/implementation` @
`296cc92acc68ccbeb63fa757720137dbaea86256`) — result:
```
...........................                                              [100%]
27 passed in 11.80s
```
This run includes `t_exempt_own_role_drops_only_the_supplying_prs_own_role`
(asserts both the `execution-observation`-branch case and the mirrored
`conformance-review`-branch case return `[]`) and
`t_required_verification_missing_exempts_the_observer_pr_that_supplies_it`
(asserts `missing == []`, replacing the pre-fix `missing ==
["conformance-review"]` assertion that had encoded the bug).
evidence: the fenced diff above plus the fenced test-run result above.
rationale: the exemption is symmetric by construction (the branch
condition does not distinguish which of the two roles `own_role` is),
not by coincidence of which case the tests happened to cover.

### Requirement 2 — sibling-pair regression test

requirement: a regression test spawning two sibling observer PRs
against the same issue confirms neither is blocked by the other's
absence from main.
spec_ref: issue #2380 Acceptance, bullet 2
verdict: Present
canonical: `296cc92acc68ccbeb63fa757720137dbaea86256:gates/test_merge_gate.py`
— diff hunk read this session via `gh pr diff 2444`:
```diff
+def t_issue_2380_sibling_observer_prs_neither_blocks_on_the_other(monkeypatch):
+    import spawn
+    monkeypatch.setattr(spawn, "board", lambda root: {"issue-7777": {}})
+    monkeypatch.setattr(merge_gate, "pr_refs",
+                         lambda repo, pr: {"base_ref": "main",
+                                            "head_ref": "issue-7777/execution-observation"})
+    eo_missing = merge_gate.required_verification_missing(
+        Path("."), "issue-7777", Path("."), 9001)
+    assert eo_missing == [], eo_missing
+    monkeypatch.setattr(merge_gate, "pr_refs",
+                         lambda repo, pr: {"base_ref": "main",
+                                            "head_ref": "issue-7777/conformance-review"})
+    cr_missing = merge_gate.required_verification_missing(
+        Path("."), "issue-7777", Path("."), 9002)
+    assert cr_missing == [], cr_missing
```
acceptance: `python3 -m pytest gates/test_merge_gate.py -q` (dispatched
worker, isolated worktree, same run as Requirement 1) — result:
```
...........................                                              [100%]
27 passed in 11.80s
```
evidence: the fenced test source above (also carries
`t_issue_2380_sibling_observer_prs_evaluate_end_to_end`, same shape
through `evaluate()`) plus the fenced passing run above.
rationale: this reproduces exactly the scenario the issue reports as
deadlocking pre-fix and asserts it now clears for both sides.

### Requirement 3 — scope-boundary control case (session-added)

requirement: branches outside the closed two-role set (e.g. the
subject's `implementation` PR) are unaffected by the exemption and still
require both observer records be on main — the fix must not
over-broaden past the pair that was deadlocking.
spec_ref: issue #2380 Acceptance, bullet 1's "vice versa" clause implies
the exemption is scoped to exactly that pair; not a separate issue
bullet — added to the checkable list per
conformance-review-requirement-extraction rule 6 (dimension tagging
surfaces implicit scope-boundary obligations the issue text does not
spell out as their own bullet).
verdict: Present
canonical: `296cc92acc68ccbeb63fa757720137dbaea86256:gates/merge_gate.py`
— same diff hunk fenced under Requirement 1: the `if own_role in
spawn_on_pr.PR_TRIGGERED_ROLES` branch falls through to the original
`return [r for r in missing if r != own_role]` when `own_role` is
outside that set, so non-observer branches keep the pre-#2380
single-role-drop behavior unchanged.
`296cc92acc68ccbeb63fa757720137dbaea86256:gates/test_merge_gate.py`
control-case diff hunk:
```diff
+    monkeypatch.setattr(merge_gate, "pr_refs",
+                         lambda repo, pr: {"base_ref": "main",
+                                            "head_ref": "issue-7777/implementation"})
+    impl_missing = merge_gate.required_verification_missing(
+        Path("."), "issue-7777", Path("."), 9003)
+    assert set(impl_missing) == {"execution-observation", "conformance-review"}, impl_missing
```
acceptance: `python3 -m pytest gates/test_merge_gate.py -q` (dispatched
worker, isolated worktree, same run as Requirement 1) — result:
```
...........................                                              [100%]
27 passed in 11.80s
```
evidence: the two fenced diffs above plus the fenced passing run above.
rationale: the code's structural fallthrough plus a positive assertion
in the diff both exercise the boundary directly.

### Requirement 4 — manual override no longer necessary

requirement: the manual override pattern used 3x this session
(release-eng consult + basis comment) is no longer necessary for a
normal same-cycle observer pair.
spec_ref: issue #2380 Acceptance, bullet 3
verdict: Present
canonical: `296cc92acc68ccbeb63fa757720137dbaea86256:gates/test_merge_gate.py`,
`t_issue_2380_sibling_observer_prs_evaluate_end_to_end` — asserts, with
check-runner and stale-revert held clean, that `evaluate()` for both
sibling PRs returns no reason containing the substring `"검증 기록"`, the
exact substring of `merge_gate.py:evaluate()`'s `f"필요한 검증 기록이 없다:
{missing}"` reason string (direct Read of `gates/merge_gate.py` lines
210-214 on this session's own pre-fix branch; unchanged in this location
by the PR).
acceptance: `python3 -m pytest gates/test_merge_gate.py -q` (dispatched
worker, isolated worktree, same run as Requirement 1) — result:
```
...........................                                              [100%]
27 passed in 11.80s
```
evidence: same canonical citation and fenced run above — the assertion
is the evidence.
rationale: this requirement has no code path of its own to inspect (the
manual override was a human workflow, not a function) — Analysis method
per conformance-review-verification-method-selection rule 2, one
inferential step from Requirements 1-3's Test evidence: since
`evaluate()` no longer emits the blocking reason that previously made a
manual override comment necessary to justify merge order, and the fix
is scoped correctly per Requirement 3, the override pattern is no
longer needed for this normal case. Recorded as one inferential step
removed from a direct assertion, rather than silently upgraded to a
pure Test verdict.

## Why

canonical: this record's own "## What was done" section above (the 4
requirement subsections and their fenced evidence) is the basis for the
method choices summarized here — no new claim is made in this section.

Method selection followed conformance-review-verification-method-selection:
Test method reused throughout (rule 4) since the PR already ships
executable regression tests for Requirements 1-3, rather than
re-deriving a parallel manual check; Analysis (rule 2) for Requirement
4's process clause, since that clause names a human workflow the review
session cannot directly execute. Sampling-derivation and
severity-classification skills were both judged not-applicable (see
skill-verdict lines below): the diff is small enough (2 files, ~108
changed lines) for full enumeration of every requirement, and the
review was not asked to risk-weight any finding — there are no
Absent/Incorrect findings to weight.

## Upstream basis

canonical: `gh issue view 2380 --repo tokenmaxxxer/on-the-record` and
`gh pr view 2444 --repo tokenmaxxxer/on-the-record --json title,body,...`
— both read this session (raw output not re-pasted here; see the
fenced diff/test citations under "## What was done" for the parts of
that output this record's verdicts rely on).

- on-the-record issue #2380 (verbatim Ask/Acceptance, this session's
  work order).
- PR #2444 (`issue-2380/implementation` @
  `296cc92acc68ccbeb63fa757720137dbaea86256`), diffing
  `gates/merge_gate.py` and `gates/test_merge_gate.py` against `main`.
  The PR also carries its own implementation record at
  `296cc92acc68ccbeb63fa757720137dbaea86256:docs/issue-2380/reports/implementation.md`
  (not reachable from this session's own branch, which is main-based).
- Prior fix from issue #2233 (`_exempt_own_role()`'s original
  own-role-only exemption), which this PR extends rather than replaces
  — confirmed by direct Read of the pre-fix function on this session's
  own (main-based) branch, `gates/merge_gate.py:116-127`.

## Open findings

canonical: this record's own "## What was done" section above (4/4
requirements verdict Present) — no derived summary beyond that section's
own fenced evidence.

none — all 4 extracted requirements verdict Present; no Surface, Absent,
Incorrect, or Unverifiable findings.

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split issue #2380's Acceptance bullet 1 by making its implicit scope-boundary obligation an explicit 4th requirement (rule 6, dimension tagging), rather than folding it silently into Requirement 1's Present verdict.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; reused the PR's existing tests as Test-method evidence for Requirements 1-3 (rule 4) and used Analysis for Requirement 4's process clause (rule 2).
skill-verdict: conformance-review-verdict-assignment — applied: invoked; all 4 requirements assigned Present after confirming the evidence is both implemented and reachable (not merely name-matching code), including an independently-executed test run before finalizing rather than trusting the PR's self-reported numbers.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; each finding cites the PR head commit sha (`296cc92acc68ccbeb63fa757720137dbaea86256`) plus file and hunk, with the actual diff/test text fenced inline rather than paraphrased.
skill-verdict: conformance-review-finding-record — applied: invoked; wrote the requirement/spec_ref/verdict/evidence/rationale block per finding directly into this file, no `spec_vs_built` fields needed (no Incorrect verdicts).
skill-verdict: conformance-review-sampling-derivation — not-applicable: full enumeration of the issue's 3 Acceptance bullets (plus 1 implicit scope-boundary requirement) against a 2-file, ~108-line diff was feasible without sampling.
skill-verdict: conformance-review-severity-classification — not-applicable: no Absent/Incorrect finding exists to risk-weight, and the review's scope was not extended into severity banding.
skill-verdict: implementation-audit — not-applicable: this session ran the standard single-session conformance-review protocol (role-handoff contract v3) rather than the two-session Implementation Audit protocol (separate builder-claims-extraction session followed by a structurally independent evaluator session); the cross-family match was keyword-triggered on "audit"/"requirements" language in the task framing, not an actual request to run that protocol.

## Next steps

canonical: this record's own frontmatter (`result: passed`) and "## Open
findings" section above (4/4 Present, none open) are the basis for
closing this loop — no new claim made here.

None — review complete, no open findings, `loop_state: complete`.

Environment note (not a finding against the PR): a background
verification worker dispatched mid-review hit host-level inode
exhaustion (`ENOSPC` from a long-standing, unrelated PyTorch
`torch.distributed` tempdir leak under `/tmp`, unrelated to this repo or
PR) while running the full-suite `python3 -m pytest -q` independently.
acceptance: `python3 -m pytest gates/test_merge_gate.py -q` (dispatched
worker, isolated worktree, captured before the inode exhaustion hit) —
result:
```
...........................                                              [100%]
27 passed in 11.80s
```
This targeted run covers all 4 requirements in this record. The
full-suite number this session did not independently reproduce is the
PR's own self-reported figure, read via `gh pr view 2444 --repo
tokenmaxxxer/on-the-record --json body` this session: PR #2444 body,
Test plan section, states `python3 -m pytest -q (full suite) — 1005
passed, 8 xfailed`. A second dispatched worker later diagnosed and
resolved the inode exhaustion (167,414 orphaned tempdirs removed,
1,656,291 inodes free confirmed via `df -i /` after cleanup), after
which this session's own Bash tool resumed working.
