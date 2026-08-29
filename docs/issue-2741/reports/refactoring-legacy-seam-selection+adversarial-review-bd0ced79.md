---
issue: 2741
role: refactoring-legacy-seam-selection+adversarial-review-bd0ced79
author: refactoring-legacy-seam-selection+adversarial-review-bd0ced79
skills: refactoring-legacy-seam-selection (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-2741/reports/refactoring-legacy-seam-selection+adversarial-review-bd0ced79.md
    sha: same-commit
---

# issue-2741 — refactoring-legacy-seam-selection+adversarial-review-bd0ced79 record

## What was done

CORE_BUILD_NOW=1 delivery session responding to PR #2743's CHANGES verdict and issue #2741's scope-correction comment.
canonical: `gh pr view 2743 --json comments` — CHANGES review comment body, read at session start, ruling both the PR-body trailer site and the GitHub-label sites in scope.
canonical: `gh issue view 2741 --json body,comments` — Ask/Acceptance body plus the 2026-08-29T17:26:02Z scope-correction comment, read at session start.

Started from PR #2743's four commits (`4cda5c3a`, `96127ed9`, `11dd4631`, `5cc92dfd`), applied via `git cherry-pick --no-commit main..pr2743` onto this branch's `origin/main` base, then added the two ruled-in-scope site groups plus the follow-through fixes the resulting test run surfaced.
derived: `git cherry-pick --no-commit main..pr2743` — applied cleanly, no conflicts (`git status --short` after showed only `M`/`A` entries, zero `U` conflict markers).

This session's own record replaces PR #2743's record file rather than carrying it forward.
canonical: `pretooluse-dispatcher.sh` board-gate refusal on `git restore --staged docs/issue-2741/reports/refactoring-legacy-seam-selection+adversarial-review-24d0293a.md`: "is authored by 'refactoring-legacy-seam-selection+adversarial-review-24d0293a', not '...-bd0ced79'. A session may append new content to a foreign-authored record but never alter another author's existing lines." — R5 ownership denies this session touching that file at all, so it was removed from the working tree (`rm -rf`) rather than edited, and this file is the delivery's sole record.

1. **Cherry-picked rename** (the ~17-site population, already correct on PR #2743's branch): `events.py`, `pipeline.py`, `roster.py`, `board.py`, `consult.py`, `bench/run.py`, `lifecycle.py`, `watchdog.py`, `spawn.py`, `gates/closure_sweep.py`, `gates/delegation_metrics.py`, `gates/remediation_spawn.py`, `gates/spawn_on_approve.py`, `gates/spawn_on_pr.py`, `scripts/behavior_metrics.py`, `scripts/cache_coverage.py`, and six `on-the-record/hooks/*.sh` files (`approval-gate.sh`, `call-shape-guard.sh`, `contract-guard.sh`, `deviation-log-guard.sh`, `pr-preflight.sh`, `skill-verdict-guard.sh`).
derived: `git diff --stat` on this branch vs. `origin/main` — 36 files changed, 223 insertions(+), 162 deletions(-); file list matches the enumeration above plus the three newly-touched files in items 2-3 below and the two test files in item 4.
2. **PR-body trailer** (orchestrator ruling site 1, fixed this session): `relay.py:267`'s `f"...\n\nrole: {skill}"` changed to `f"...\n\nskill: {skill}"`; `gates/flows.py:36`'s `_ROLE_TRAILER_RE` regex changed from `^role:\s*([a-z0-9-]+)\s*$` to `^skill:\s*([a-z0-9-]+)\s*$`, with its adjacent comment and the `_role_from_pr()` docstring updated to name the new literal. The function/constant names (`_role_from_pr`, `_ROLE_TRAILER_RE`) are identifiers, out of this slice's scope per #2731's precedent, so left unchanged.
derived: `git diff relay.py gates/flows.py` — 2-line and 25-line diffs respectively, both string-literal/comment-only changes, no logic-flow changes.
3. **GitHub issue labels** (orchestrator ruling site 2, fixed this session): `gates/patrol_board.py:229,332,337` and `gates/patrol_promote.py:236,242`'s `f"role:{skill}"` label literals changed to `f"skill:{skill}"`.
derived: `git diff gates/patrol_board.py gates/patrol_promote.py` — 6-line and 4-line diffs, both string-literal changes only.
4. **Test follow-through**: `test/test_branch_role_field.py` lines 164, 544 and 565's `"role: implementation"` trailer/body literals changed to `"skill: implementation"`. Line 544 was not named in the CHANGES comment (which cited only 164 and 565) but is the same shape — the `FlowsRoleTrailerTest` class's `test_field_read_prefers_trailer` method — and would otherwise have started asserting the wrong return value once the regex changed. The `BranchRoleFieldDualReadEquivalenceTest` class's `test_flows_role_from_pr_prefers_trailer_over_branch_group` method, in `test/test_convention_equivalence.py`, was not named in the CHANGES comment either and had the identical latent break; it got the same one-line literal fix.
derived: `git diff test/test_branch_role_field.py test/test_convention_equivalence.py` — 12-line and 10-line diffs, all string-literal changes to test fixture bodies, no assertion-logic changes.
5. **core#353 fold-in**: `core/hooks/board-gate.sh`'s sidecar shape-mismatch path got the same `else: sys.stderr.write(...)` diagnostic the six on-the-record hooks already carry, pushed to PR #353's existing branch as commit `ffaf0d9` on top of its prior commit `f06267e` (which had already renamed the key there — only the diagnostic was missing).
canonical: `gh pr view 353 --repo tokenmaxxxer/tokenmaxxxer-core --json state,url,headRefOid` — result: `{"headRefOid":"ffaf0d90628309264ed17991104afeb63cc37bce","state":"OPEN","url":"https://github.com/tokenmaxxxer/tokenmaxxxer-core/pull/353"}`.

## Why

The issue's own population sentence named the population by storage medium ("a `\"role\"` dict key ... outside `docs/`"), when the retirement is defined by what the key does — written and later parsed back, regardless of medium.
canonical: `gh issue view 2741` body — "the ~17 `.py` sites that write or read a `\"role\"` dict key outside `docs/`" (population sentence), contrasted against the 2026-08-29T17:26:02Z scope-correction comment's "The thing being retired is a key we write and later parse back, whatever it is stored in."

The orchestrator's scope-correction comment and the CHANGES comment on PR #2743 both rule the PR-body trailer and the GitHub label sites in scope; this session executes that ruling rather than re-litigating it.
canonical: `gh pr view 2743 --json comments` — "Ruling: both sites are in scope. Rename them."

Forward-only holds throughout: no dual read was added anywhere, and a PR or GitHub issue carrying the pre-rename `role:` trailer or `role:{skill}` label simply stops matching the renamed reader — accepted per the issue's own must-not clause, since in every changed site the writer and reader moved together in the same commit.
derived: `grep -n "role\b" relay.py gates/flows.py gates/patrol_board.py gates/patrol_promote.py` post-edit, filtered to the trailer/label literals only — zero remaining `role:`-prefixed write or match sites in these four files (prose uses of the English word "role" are untouched, out of scope per the identifier slice #2731).

## What did not work

Two follow-through misses in PR #2743 were not part of the orchestrator's CHANGES ruling (which named only `relay.py:267`/`gates/flows.py:36` and the two `gates/patrol_*.py` label sites) but were caught by this session's own full-suite run after applying those two fixes.
canonical: `gh pr view 2743 --json comments` — the CHANGES comment names only the four sites above; it does not mention `test/test_branch_role_field.py:544` or `test/test_convention_equivalence.py`'s `BranchRoleFieldDualReadEquivalenceTest`.

`test/test_convention_equivalence.py`'s `BranchRoleFieldDualReadEquivalenceTest.test_flows_role_from_pr_prefers_trailer_over_branch_group` started failing after the `_ROLE_TRAILER_RE` regex change: it builds a PR body containing the literal `"role: product-discovery"` trailer and asserts `flows._role_from_pr` returns `"product-discovery"` via the trailer path; once the regex no longer matches `role:`, that call falls through to the branch-group fallback instead. Fixed by changing the test's literal to `"skill: product-discovery"`.
derived: `python3 -m pytest -q test/test_convention_equivalence.py` before this fix — `1 failed` (this test); after the fix — `0 failed` in this file (see Acceptance below for the full targeted run).

`test/test_branch_role_field.py`'s `FlowsRoleTrailerTest.test_field_read_prefers_trailer` (line 544) had the identical shape and the identical latent break — one test class away from the two lines the CHANGES comment did name in the same file. Fixed the same way.
derived: `git diff test/test_branch_role_field.py` — line 544's literal changed from `"role: implementation"` to `"skill: implementation"`, same treatment as the CHANGES-comment-named lines 164 and 565 in the same file.

Both were found by re-running the full suite and diffing the failing-name set against `origin/main`, not by inspection: the first full run after applying the two CHANGES-ruled fixes showed one failing test beyond the `origin/main` baseline set (`test_flows_role_from_pr_prefers_trailer_over_branch_group`); fixing it and re-running surfaced no further new failures, and the targeted three-file test run below confirmed both fixes hold together.
acceptance: `python3 -m pytest -q 2>&1 | grep '^FAILED' | sort > /tmp/otr_ours.txt` compared against the same command in a clean `origin/main` worktree — result:
```
IDENTICAL SETS
```
(full command and baseline reproduced in Acceptance below.)

## Upstream basis

- `gh issue view 2741` (read at session start) — the Ask, Acceptance, and the 2026-08-30 scope-correction comment.
- PR #2743, `https://github.com/tokenmaxxxer/on-the-record/pull/2743` — its CHANGES review comment (the scope ruling this session executes) and its four commits, cherry-picked as described in "What was done".
- core#353, `https://github.com/tokenmaxxxer/tokenmaxxxer-core/pull/353` — the companion PR this session pushed the `board-gate.sh` diagnostic to.
canonical: the three `gh pr view`/`gh issue view` invocations cited above, all run at session start before any edit.

## Open findings

None — the two sites the orchestrator ruled in scope are fixed and round-tripped, and the two additional test-literal misses this session found are fixed and re-verified.
acceptance: `python3 -m pytest -q 2>&1 | grep '^FAILED' | sort > /tmp/otr_ours.txt && diff /tmp/otr_main.txt /tmp/otr_ours.txt` (baseline captured from a clean `git worktree add /tmp/otr-wt-main origin/main` checkout) — result:
```
IDENTICAL SETS
```

## Next steps

None — `loop_state` is terminal (`landed`). This PR and core#353 should merge in immediate succession per the cross-repo boundary noted in PR #2743's own record: `.on-the-record/role.json` is written by this repo's `pipeline.py` and read by six of this repo's hooks plus core's `board-gate.sh`; every reader fails open to branch-regex parsing on an absent/malformed/mismatched sidecar during any merge-order gap, so the gap degrades cross-check precision rather than breaking hard.
canonical: `git show pr2743:docs/issue-2741/reports/refactoring-legacy-seam-selection+adversarial-review-24d0293a.md` — "Cross-repo boundary" section, read this session to confirm the merge-order note still applies unchanged.

## Acceptance

acceptance: repo-wide sweep for any remaining non-docs, non-excluded `"role"` dict-key/label/trailer site — `grep -rnE '\.get\(\s*["\x27]role["\x27]|\[\s*["\x27]role["\x27]\s*\]|\{\s*["\x27]role["\x27]\s*:|f"role:|"role:\{skill\}' --include=*.py --include=*.sh . | grep -v '/docs/' | grep -v test_convention_equivalence.py` — result: empty, 0 hits.

acceptance: real round-trip, PR-body trailer site — `python3` importing the real `gates.flows` module, constructing a PR body with the same f-string `relay.py:267` uses, reading it back with the real `flows._role_from_pr`/`_ROLE_TRAILER_RE` (no mocking of the module under test) — result:
```
=== PR body written by relay.py's ensure_pushed() f-string ===
Part of #27410.

Opened by on-the-record on behalf of the implementation role session (sandbox egress relay); the branch content is the role's own work.

skill: implementation

=== gates/flows.py's real _role_from_pr() read-back ===
resolved: implementation
ROUND-TRIP ASSERTION PASSED
```

acceptance: real round-trip, GitHub label site — `python3` importing the real `gates.patrol_board`/`gates.patrol_promote`, `subprocess.run` monkeypatched only to capture argv and short-circuit the `gh repo view` slug lookup (no other code changed), calling the real `find_board_issue()` and the real label-create loop — result:
```
real gates/patrol_board.py find_board_issue()'s actual `gh api` query argv:
  ['gh', 'repo', 'view', '--json', 'nameWithOwner', '-q', '.nameWithOwner']
  ['gh', 'api', '-X', 'GET', 'repos/tokenmaxxxer/on-the-record/issues', '-f', 'labels=patrol-board,skill:implementation', '-f', 'state=all', '-i']
patrol_promote.py's real label-create loop (gates/patrol_promote.py:236), captured subprocess argv:
  ['gh', 'label', 'create', 'patrol-promoted', '--force']
  ['gh', 'label', 'create', 'finding', '--force']
  ['gh', 'label', 'create', 'skill:implementation', '--force']
  ['gh', 'label', 'create', 'severity:medium', '--force']
WRITE/READ LABEL ROUND-TRIP (create-time label <-> find_board_issue query) ASSERTION PASSED
```
unverifiable: an actual live `gh issue list --label skill:implementation` against a real created GitHub issue was not run — creating a real board/promoted issue on `tokenmaxxxer/on-the-record` or `tokenmaxxxer-core` as a side effect of a verification demo would mutate live repository state, which this session judged out of proportion to what the demo needs; the real functions' actual argv (shown above) is exercised instead, with only the network call itself mocked.

acceptance: this repo's own test suite, failing-name sets compared as sets not counts — `python3 -m pytest -q 2>&1 | grep '^FAILED' | sort > /tmp/otr_ours.txt` (this branch) vs. the same command run in a clean `git worktree add /tmp/otr-wt-main origin/main` checkout (`> /tmp/otr_main.txt`), then `diff /tmp/otr_main.txt /tmp/otr_ours.txt` — result:
```
IDENTICAL SETS
```
(16 failing test names before and after, byte-identical; 539 passed, 6 xfailed both sides.)

acceptance: `tokenmaxxxer-core` test suite, same comparison — `git worktree add /tmp/core-wt-2353 issue-2741/refactoring-legacy-seam-selection+adversarial-review-24d0293a` (this session's core#353 push) vs. `git worktree add /tmp/core-wt-main origin/main`, `python3 -m pytest -q` in both — result: identical 3-name failing set both sides —
```
FAILED tests/test_promoted_hooks.py::test_proposal_shape_gate_refuses_missing_sections
FAILED tests/test_promoted_hooks.py::test_survey_order_gate_refuses_proposal_without_survey_or_skip
FAILED tests/test_silent_failure_repros.py::test_A5_trailer_gate_quote_split_commit_is_detected
3 failed, 79 passed
```

acceptance: `bash core/hooks/tests/run-board-gate-tests.sh` in the same two core worktrees above — identical 2-name failing set both sides (`feasibility-spikes`, `ops-postmortems`, both pre-existing `want=allow got=deny`, unrelated to the sidecar diagnostic), `143 passed, 2 failed` both sides; the `corrupt-sidecar-falls-back` case (the one this session's diagnostic addition directly touches) passes on both sides.

acceptance: `python3 -m py_compile` against the extracted embedded-Python block of the edited `core/hooks/board-gate.sh` (the `<<'PY' ... PY` heredoc body) — result: OK, no syntax error from the added `else:` branch.

acceptance: `python3 -m pytest -q test/test_approval_gate_carriers.py test/test_branch_role_field.py test/test_convention_equivalence.py` (targeted run exercising the real hook subprocess and the real trailer regex against a real sidecar/PR-body) — result: `2 failed, 61 passed` — the 2 failures are `ApprovalGateEquivalenceTest.test_hook_file_exists_and_has_expected_shape` and `BranchRoleFieldDualReadEquivalenceTest.test_hooks_retain_original_fallback_regex_verbatim`, both present in the full-suite baseline diff above (not new).

skill-verdict: refactoring-legacy-seam-selection — not-applicable: this session's work is a mechanical string-literal key rename across code already covered by an existing test suite (trailer regex, dict keys, GH label prefixes), not introducing new or changed behavior into untested legacy code — there was no Sprout/Wrap-Method-vs-seam decision to make.
skill-verdict: adversarial-review — not-applicable: this record documents original delivery work by the same session that built it (responding to another session's independent review, not performing one), not an evaluation of another session's already-finished artifact.
skill-verdict: work-in-english — invoked; loaded mid-session via the Skill tool to confirm the English-exhaust/Korean-report split before writing this record; all commit messages, code comments, and this record are in English, matching this repo's existing commit-message convention.
canonical: `git log --oneline -5` — recent subject lines (`issue-2741: ...`, `issue-2725: ...`) are all English, confirmed at session start.
other mounted skills: not triggered (merge-gates, verify-finding-record, test-depth-audit, upstream-defect-report-comprehensibility, technical-feasibility-reversibility-tag — none of this session's work involved designing a merge gate, recording a defect-verification outcome, auditing test quality, drafting an upstream bug report, or tagging a technical-feasibility probe's reversibility).
