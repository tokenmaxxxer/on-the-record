---
kind: record
loop_state: handed-off
verdict: failed
---

# Execution observation — issue #2062 (invoke-before-apply obligation)

canonical: `gh issue view 2062` and `gh issue view 2062 --comments`, executed live this session.
skill-verdict: observability-phase-trace — invoked; loaded the full SKILL.md via the Skill tool this session. not-applicable: the skill's RED/USE/Golden-Signals phase-1-to-phase-2 traceability rules govern instrumentation-signal methodology drift, not this observation role's EARL-style pass/fail evidence recomputation over `spawn.py`/`gates/record_lint.py`. Cross-family keyword match per the spawn note (issue #2001); no signal-methodology content applied here.

## What was done

canonical: commands listed below, all executed live this session.

1. Read `gh issue view 2062` (body) and `gh issue view 2062 --comments` — the original acceptance criteria plus two operator scope-addition comments (orchestrator-level invoke-before-apply obligation; plugin's own three skills — `on-the-record:consult`, `on-the-record:run`, `on-the-record:report-upstream`), both timestamped before the implementation commit landed.
2. Ran `gh pr view 2063 --json number,title,state,mergeCommit,commits,files` — branch `issue-2062/implementation`, commit `406a2486627178648978e079ef866ffe1079c6ac`.
3. Ran `git show origin/issue-2062/implementation:docs/issue-2062/reports/implementation.md` to read the implementation role's own delivery report (that path exists only on `issue-2062/implementation`, not on this branch).
4. Checked out that commit into an isolated git worktree (`git worktree add /tmp/wt-2062-impl FETCH_HEAD`, removed after use via `git worktree remove --force`; never committed to this branch) and:
   - Ran `git diff HEAD~1 -- spawn.py` and `git diff HEAD~1 -- gates/record_lint.py` inside the worktree.
   - Fixture-drove `gates.record_lint.skill_verdict_reason_check` directly via `runpy.run_path` (not by re-running its own test file as evidence), with four cases: `applied:` without marker, `applied:` with marker, `not-applicable:`, zero-mounted-skills.
   - Ran `python3 -m pytest on-the-record/hooks/test_skill_verdict_guard.py -q` and `python3 -m pytest tests/test_spawn_directive_assembly.py -q` — the two files the implementation report cited as evidence.
   - Ran `python3 -m pytest -q -m "not slow"` (the fast tier declared in `.on-the-record/test-tiers.json`, budget 300s) — a superset of the two files above, so this is the first session to run the tier's full scope against this commit.
   - On the failure below, reverted `gates/record_lint.py` and `on-the-record/gates/record_lint.py` to parent commit `d4b2cda5` in the worktree and re-ran the single failing test, then restored the changed files.

## Why

canonical: `roles/specs/execution-observation.spec.json` (read this session) — its `use_when` clause: an executable artifact landed on the branch with no execution-observation record yet for this commit sha. PR #2063 (5 non-doc paths across `spawn.py`, `gates/record_lint.py` and its `on-the-record/gates/` mirror, two test files) matches.

## Upstream basis

canonical: `gh pr view 2063 --json state`, executed live this session — result: OPEN, not merged. `406a2486627178648978e079ef866ffe1079c6ac` (PR #2063, branch `issue-2062/implementation`); parent `d4b2cda557da29b6e4263b1f6bc8b1485f4bff61`.

## Fixture drive — skill_verdict_reason_check marker check

canonical: derived reproduction below, executed live this session via `runpy.run_path` against `gates/record_lint.py` at worktree commit `406a2486`.

```
no-marker:     ["applied: 줄에 invoke-before-apply 마커가 없다 (issue #2062): 'diagnose-first' — ..."]
with-marker:   []
not-applicable: []
zero-mounted:  []
```

This matches acceptance criterion 2's shape: `applied:` lines without `invoked;` are refused; `not-applicable:` and zero-skill sessions are byte-unaffected.

## Directive text — spawn.py (acceptance criterion 1, partial)

canonical: `git diff HEAD~1 -- spawn.py`, executed live this session against worktree commit `406a2486`.

The diff shows the 스킬 점검(이슈 #1960) block, inside the existing `if skill_sources or role_source["skills"]:` guard, gained the invoke-before-apply sentence next to the mounted-skill list, and the 스킬-verdict 의무(이슈 #2039) block gained the companion `invoked;`-marker sentence. This satisfies the spawned-role half of acceptance criterion 1.

canonical: `grep -n "orchestrate\|on-the-record:consult\|on-the-record:run\|report-upstream" spawn.py`, executed live this session against worktree commit `406a2486` — result: zero matches. Neither the orchestrator-level obligation nor the plugin's-own-three-skills obligation (both requested in the operator scope-addition comments cited above, before implementation started) is present anywhere in the diff, and the implementation role's own report (canonical: `git show origin/issue-2062/implementation:docs/issue-2062/reports/implementation.md`, executed live this session, item 3 above) does not mention either in its "What was done" section. This is scope the issue's own comment trail added before implementation started, left undelivered.

## Full fast-tier run — regression found

canonical: `python3 -m pytest -q -m "not slow"`, executed live this session against worktree commit `406a2486`.

```
$ python3 -m pytest -q -m "not slow"
...
FAILED gates/test_record_lint.py::t_2039_skill_verdict_satisfied_passes - assert ['docs/issue-...;` 를 붙여야 한다.'] == []
1 failed, 2587 passed, 18 xfailed, 3 xpassed in 40.83s
```

canonical: `python3 -m pytest gates/test_record_lint.py::t_2039_skill_verdict_satisfied_passes -q`, executed live this session against parent commit `d4b2cda5` in the same worktree (changed files reverted then restored, per "What was done" item 4).

```
$ python3 -m pytest gates/test_record_lint.py::t_2039_skill_verdict_satisfied_passes -q
1 passed in 0.87s
```

canonical: the two pytest runs immediately above, both executed live this session. Test `t_2039_skill_verdict_satisfied_passes` in `gates/test_record_lint.py` passes on the parent commit and fails on commit `406a2486` — a regression introduced by this change, not an environmental flake. canonical: `python3 -m pytest tests/test_spawn_directive_assembly.py -q`, executed live this session ("What was done" item 4) — this session reproduced that file clean with no failures, unlike the implementation report's own cited env-leak failure in that same file. The regressing fixture builds a record with an `applied:` line lacking the `invoked;` marker and asserts the guard passes it (issue #2039's original shape contract); the #2062 change now blocks that same fixture, and the pre-existing test was never updated to add the marker. Neither of the implementation report's two cited test-file runs includes `gates/test_record_lint.py`, so this regression was never surfaced before the PR was opened.

## Verdicts

### Outcome

Recomputation per `roles/specs/execution-observation.spec.json`: overall verdict = worst case across cited test entries.

- Acceptance 1 (directive states the obligation next to the mounted-skill list): failed — canonical: `git diff HEAD~1 -- spawn.py` and the `grep` run above (both executed live this session) — met for the spawned-role directive, undelivered for the two operator scope-addition items.
- Acceptance 2 (guard refuses unmarked `applied:`, passes marked, NA/zero-skill unaffected): canonical: the `runpy.run_path` fixture drive and the `pytest -q -m "not slow"` run above (both executed live this session) — passed in the isolated fixture drive, failed in the full fast-tier run (`t_2039_skill_verdict_satisfied_passes` regressed).
- Acceptance 3 (live consumer spawn evidence): canonical: `gh pr view 2063 --json state`, executed live this session, result OPEN — untested; provenance is `executed-live`, deferred by the implementation report to a future post-merge spawn; PR #2063 has not merged.

Worst case across the three cited results: failed.

### Trajectory

canonical: `gh issue view 2062 --comments`, executed live this session. The delegated-judgment gate opened three times on branch `issue-2062/implementation` (comment trail, all at 2026-08-22T16:52Z) and escalated each time ("depth or impact axis did not clear") rather than resolving to a direct verdict; PR #2063 remains OPEN. The implementation session started after both scope-addition comments were already posted (same comment trail), yet its own report (canonical: `git show origin/issue-2062/implementation:docs/issue-2062/reports/implementation.md`, executed live this session, item 3 above) makes no mention of the orchestrator or plugin-skill scope. Trajectory: not sound — the scope gap is silent, not stated as a deferral.

### Step

canonical: the `pytest -q -m "not slow"` run and the `grep` run above (both executed live this session). Two step-level deficiencies found in commit `406a2486627178648978e079ef866ffe1079c6ac`:

1. `gates/record_lint.py` and `on-the-record/gates/record_lint.py` — canonical: the two pytest runs under "Full fast-tier run" above (executed live this session) — the new marker check regresses test `t_2039_skill_verdict_satisfied_passes` in `gates/test_record_lint.py`, confirmed against the parent commit. The implementation report's cited test evidence did not include this file.
2. `spawn.py` — canonical: the `grep` run under "Directive text" above (executed live this session) — the orchestrator-level and plugin's-own-three-skills obligations from the issue's own comment trail are not present in the shipped directive text.

## Open findings

1. Regression (step-level) — canonical: the two pytest runs under "Full fast-tier run" above (executed live this session): commit `406a2486` breaks test `t_2039_skill_verdict_satisfied_passes` in `gates/test_record_lint.py`. Fix: either update that pre-existing fixture to carry the `invoked;` marker (if issue #2039's original contract is superseded by #2062, per this repo's own drift-vs-deviation convention that supersession must be stated) or adjust the new check so the pre-existing #2039 contract is not broken. Whoever resumes PR #2063 should run the full `-m "not slow"` tier, not only the two files the implementation report targeted.
2. Scope gap (trajectory-level) — canonical: the `grep` run under "Directive text" above (executed live this session): the two operator scope-addition comments on issue #2062 (orchestrator directive sentence; plugin's own three skills at their trigger conditions) are not implemented in commit `406a2486`. Not stated as deferred anywhere in the implementation report — a silent gap against the issue's own frozen comment-trail scope, not a considered exclusion.

## Next steps

Report both findings back to the branch (this role does not spawn a peer role or reopen scope on its own initiative — SCOPE-EXCEEDED RULE). Whoever next drives `issue-2062/implementation` should: (a) fix or explain the regression noted above, (b) either deliver the two undelivered scope-addition items or state an explicit, reasoned deferral for them, (c) re-run the full fast tier — canonical: `python3 -m pytest -q -m "not slow"` as run this session, above — before requesting the next judgment review.

## Resolution path

Whoever next observes issue #2062 (or resumes `issue-2062/implementation` toward a merge) re-runs `python3 -m pytest -q -m "not slow"` against the then-current head of that branch — canonical: acceptance: `python3 -m pytest -q -m "not slow"` — result: this session's run above, failed on `t_2039_skill_verdict_satisfied_passes`. If a re-run of that same command later shows the regression noted above resolved and any marker-related tests all clear, and the scope-addition text is present (or explicitly and reasonedly deferred), re-render this record's verdicts to reflect that; otherwise carry the same findings forward with an updated commit sha.

## Amendment — reconciling issuecomment-5381558954

amendments-reconciled: issuecomment-5381558954 (canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/comments/5381558954`, executed live this session) — a new issue-2062 comment landed after this record's first draft, posted 2026-08-22T17:00:35Z by JiwonJung94, claiming: (1) fixture finalization commit `d0c85fec` fixed the regression, fast tier fully green (2588 passed); (2) the orchestrate directive carries the same self-obligation for the orchestrator's own condition-matched skills; (3) the plugin's own three skills (consult/run/report-upstream) are named at their trigger conditions. Verified each claim independently rather than accepting the comment's own assertion:

canonical: `git fetch origin issue-2062/implementation` then `git worktree add /tmp/wt-2062-v2 FETCH_HEAD`, executed live this session — new head `70a6a37e`, with commit `d0c85fec` ("issue-2062: update record_lint fixture for invoked marker") on top of `406a2486`.

- Claim 1 (regression fixed) — canonical: `python3 -m pytest -q -m "not slow"`, executed live this session against worktree commit `70a6a37e`: `2588 passed, 18 xfailed, 3 xpassed in 40.75s`, zero failures. This matches the comment's claim exactly and supersedes the "Full fast-tier run" regression finding above for the branch's current head — **confirmed fixed**. canonical: `git -C /tmp/wt-2062-v2 show --stat d0c85fec`, executed live this session — the fix touches only `gates/test_record_lint.py` (1 insertion, 1 deletion): the pre-existing `t_2039_skill_verdict_satisfied_passes` fixture's `applied:` line now carries the `invoked;` marker.
- Claims 2 and 3 (orchestrate directive + plugin's own three skills) — canonical: `git -C /tmp/wt-2062-v2 grep -n "orchestrate\|on-the-record:consult\|on-the-record:run\|report-upstream" spawn.py`, executed live this session against worktree commit `70a6a37e` — zero matches, same result as against `406a2486` above. canonical: `git -C /tmp/wt-2062-v2 diff 406a2486..70a6a37e --stat`, executed live this session — the only files touched between the two commits are `docs/issue-2062/reports/consult-log.md` and `gates/test_record_lint.py`; `spawn.py` is byte-identical to `406a2486`, which this record already showed lacks any orchestrator/plugin-skill text. **Claims 2 and 3 are not substantiated by the branch's actual content** — the comment asserts structural closure that the shipped diff does not contain.

This does not change the outcome verdict's worst-case result (still **failed**, since acceptance 1's orchestrator/plugin-skill half remains undelivered per the diff evidence, contradicting the comment), but it does supersede the step-level regression finding (item 1 under "Open findings") as resolved, and it adds a new finding: an issue comment asserting delivery of work that isn't in the branch.

## Open findings (amendment)

3. **Unsubstantiated closure claim** — canonical: the `git diff --stat` and `grep` citations immediately above (both executed live this session): issuecomment-5381558954 claims the orchestrate directive and the plugin's own three skills were structurally delivered; the actual diff between `406a2486` and current head `70a6a37e` shows no such change to `spawn.py`. Whoever resumes this issue should treat acceptance criterion 1's orchestrator/plugin-skill half as still open, not closed, regardless of the comment's wording, and should re-verify future "landed"/"closed" claims against the actual diff rather than the claim text.
