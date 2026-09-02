---
issue: 3091
role: independent-verification-2
author: independent-verification-2
verifies_subject: true
code_under_review: 6df0350a9d4a7ae04a640446e218f8615a421c5c
type: verification-record
breaking: "false"
verdict: PASS
loop_state: landed
upstream:
  - path: PR #3111 (tokenmaxxxer/on-the-record), head 6df0350a9d4a7ae04a640446e218f8615a421c5c
    sha: 6df0350a9d4a7ae04a640446e218f8615a421c5c
---

# issue-3091 — independent-verification-2 record

## What was done

Independent, builder-blind verification of PR #3111 (branch
`issue-3091/diagnose-first+silent-failure-audit+test-derivation-7248afd6`,
head `6df0350a`) against issue #3091's three acceptance checks and its
must-not clauses.

canonical: `gh pr view 3111` output (state: OPEN, head `6df0350a`)

Fetched the PR's head into a separate git worktree
(`git worktree add /tmp/pr3111-check pr-3111-review`, `pr-3111-review` =
`origin/issue-3091/diagnose-first+silent-failure-audit+test-derivation-7248afd6`)
and re-ran all three acceptance checks from a clean checkout rather than
trusting the record's pasted output.

acceptance: `bash -c "python3 -m pytest test/ -q"` — result:
```
$ cd /tmp/pr3111-check && python3 -m pytest test/ -q
563 passed, 3 xfailed in 31.68s
```
Matches the PR record's claim exactly.

acceptance: `bash -c "python3 -m pytest tests/ -q"` — result:
```
$ cd /tmp/pr3111-check && python3 -m pytest tests/ -q
5 failed, 182 passed, 2 warnings in 9.26s
```
Same 5 node IDs the PR record names (`test_respawn_deliverable_gate.py`
x4, `test_spawn_gate_wiring.py` x1).

acceptance: `bash -c "python3 gates/probe_full_suite_is_one_command.py"` — result:
```
$ cd /tmp/pr3111-check && python3 gates/probe_full_suite_is_one_command.py; echo exit=$?
FAIL: 2 shell test file(s) exist that `python3 -m pytest` can never collect: ['tests/check-write-set-conflicts.test.sh', 'tests/claim-scan-preflight.test.sh'] -- ...
exit=1
```
Matches; the issue explicitly requires this gate to fail against the
current tree, which it does.

**Base-branch timing check (the one thing that looked suspicious):** the
PR record says PR #3089 (issue-3083) was "OPEN ... not yet merged" to
its base, and attributes `tests/`'s 5 failures to that still-open PR.
But this session's own `gitStatus` shows PR #3089 already MERGED to
`main` (`7ee16612`, merged 2026-09-02T16:54:49+09:00), 3 minutes before
PR #3111's last commit (`6df0350a`, 16:57:52). That looked like it could
be a stale/inaccurate citation, so I checked directly rather than taking
the record's word for it:

canonical: `gh pr view 3089` output (state: MERGED)

derived: `git merge-base --is-ancestor 7ee16612 pr-3111-review` — not an
ancestor; `git log --oneline pr-3111-review` shows PR #3111 branched
from `573e7382` (issue-3053, #3074), which predates #3089's merge. The
record's claim is accurate as of when the branch was cut — PR #3111 was
built against a `main` snapshot that genuinely did not yet have #3089's
fix.

I then checked what happens once PR #3111 actually lands on top of
today's real `main` (post-#3089), since that is what matters for
landing, not the snapshot the branch happened to fork from:

derived: `git rebase main-latest` (main-latest = current `origin/main`,
`7ee16612`) from the PR's branch — rebased cleanly, no conflicts (PR
#3111 touches `test/`, `gates/`, `docs/issue-3091/`; #3089 touched
`tests/`, `on-the-record/hooks/hooks.json` — disjoint file sets).
Re-ran all three checks against the rebased tree:
```
$ python3 -m pytest test/ -q
563 passed, 3 xfailed in 31.95s
$ python3 -m pytest tests/ -q
216 passed, 2 warnings in 9.43s
$ python3 gates/probe_full_suite_is_one_command.py; echo exit=$?
FAIL: ... (same two .test.sh files)
exit=1
```
`tests/` is now fully green (PR #3089's fix landed), `test/` is fully
green (this PR's fix), and the gate still correctly fails on the
unrelated `.test.sh` shape. No conflict, no regression, nothing this PR
needs to change — the record's citation was accurate for its own branch
point and the discrepancy resolves itself on rebase.

**Spot-checked the diagnosis table's citations** rather than trusting
the prose:

derived: `git log --oneline --diff-filter=A -- 'test/*.py' 'test/*.sh' | wc -l`
```
54
```
matching the "54 separate commits" claim.

derived: `git log --oneline -1 2cc6d108`, `git log --oneline -1
0879f12a`, `git log --oneline -1 a4d85dbb`
```
2cc6d108 issue-2432: branch/record naming to skill axis + lease disambiguator (dual-scheme, stage 4)
0879f12a issue-2507: consult.py task-composed skills, pipeline.py preflight migration, full roles/ disposition sweep (#2536)
a4d85dbb issue-2537: Stage 6A — retire consult.py's roles/ dependency, document 3 blockers (#2541)
```
all three resolve to the exact commits the diagnosis table cites.

derived: `grep -n "checkout_issue_branch\|_checkout_named_branch" spawn.py`
```
609:checkout_issue_branch = _pipeline_mod.checkout_issue_branch
...
4108:                br = checkout_issue_branch_for_skill(cwd, issue, skill_slug,
4117:                br = _checkout_named_branch(cwd, f"issue-{issue}/{skill}")
```
confirms `checkout_issue_branch` is imported at module level but
`_spawn_one`'s actual checkout call sites use
`checkout_issue_branch_for_skill` / `_checkout_named_branch` instead —
the "dead mock target" claim underlying 8 of the 15 fixes checks out.

**Must-not compliance**, checked against the actual diff (`gh pr diff
3111`, read in full this session), not the record's own summary of
itself:
- No test was deleted or skipped (no `@unittest.skip`, no
  `pytest.mark.skip`, no test removal) anywhere in the diff — every one
  of the 15 stale tests still runs and still asserts something, just
  against the current-correct value/target.
- No failure was classified as an environment artifact (the diagnosis
  table's "Made stale by" column names a commit for all 15; none say
  "environment").
- The `test/`→`tests/` merge was not performed; the record explains why
  and defers it to a follow-up, as the issue requires.
- The skill-layer bearing-on-#3053 analysis treats each of the 12
  failures individually rather than dismissing the group as cosmetic,
  and does surface one (`Bm25CrossFamilySkillMatchesTest`) as a genuine
  measurement-relevant change rather than pure test rot.

## Why

Verification-only session (`verifies_subject: true`): audit PR #3111
against issue #3091's acceptance criteria and must-not clauses, and
report the result in this record per
`docs/handbooks/observer-verification.md`. Re-ran every acceptance
command from a clean worktree rather than reusing the PR's pasted
output, and chased the one detail (PR #3089's merge-state citation)
that looked like it might be stale, because a citation that turns out
wrong on a currently-open PR is exactly the kind of thing an
independent verifier exists to catch — it turned out accurate for the
branch point it was made from, and harmless on rebase.

## What did not work

None.

## Upstream basis

canonical: `gh pr view 3111` output (state: OPEN, head `6df0350a`) —
the deliverable under review.

- PR #3111 (tokenmaxxxer/on-the-record), head
  `6df0350a9d4a7ae04a640446e218f8615a421c5c`.
- `6df0350a:docs/issue-3091/reports/diagnose-first+silent-failure-audit+test-derivation-7248afd6.md`
  (untracked on this branch — lives on the PR #3111 branch, not this
  `independent-verification-2` branch) — the record being audited, read
  in full via `gh pr diff 3111` this session.
- Issue #3091, verbatim acceptance criteria (`gh issue view 3091`, read
  in full this session).
- canonical: `gh pr view 3089` output (state: MERGED, mergeCommit
  `7ee16612`) — cross-checked against the PR #3111 record's own
  citation of #3089 as OPEN; the discrepancy is resolved above under
  "What was done" (accurate for #3111's branch point, harmless on
  rebase — reproduced via `git rebase main-latest` in this session's
  own worktree, results pasted above).

## Open findings

canonical: this session's own rebase-and-rerun transcript in "What was
done" above (`git rebase main-latest` + the three re-run acceptance
commands) — that is the concrete check that closed the one candidate
finding (the #3089 merge-state citation). No other finding survived
review.

## Next steps

None.

acceptance: `bash -c "python3 -m pytest test/ -q"` — result:
```
563 passed, 3 xfailed in 31.68s
```
Reproduced again after rebase onto current `main` (`git rebase
main-latest`, see "What was done"):
```
563 passed, 3 xfailed in 31.95s
```
Both runs are this session's own executed evidence, not a reused
citation. `loop_state: landed`, `verdict: PASS`.

skill-verdict: work-in-english — applied: invoked; wrote this record's body in English (repo-bound artifact) per the skill, reserving Korean for the end-of-turn user-facing summary
skill-verdict: other mounted skills: not triggered
