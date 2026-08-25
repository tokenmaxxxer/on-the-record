---
issue: 2285
role: execution-observation
author: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2285/reports/implementation.md
    sha: f50e689f2a1509cedc1192cdf755b9ddc513887e
  - path: consult.py
    sha: f50e689f2a1509cedc1192cdf755b9ddc513887e
  - path: docs/specs/consult-guidance-source.md
    sha: f50e689f2a1509cedc1192cdf755b9ddc513887e
subject: PR #2344 (issue-2285, issue-2241 stage 2 "confirm consult.py's
  guidance source, role identity stays exposed"), branch
  issue-2285/implementation, commit f50e689f2a1509cedc1192cdf755b9ddc513887e
test: independent re-execution of the regression guard test file and the
  behavioral resolve_role_source() check it contains, from a fresh git
  worktree checkout of the PR branch, plus a citation check of the new
  spec doc against the PR's own consult.py/skills.py line numbers
result: passed
assertedBy: execution-observation session for issue-2285, independent of
  PR #2344's authoring (implementation) session
---

# issue-2285 — execution-observation record

## What was done

canonical: `git fetch origin pull/2344/head:pr-2344-check` and
`git worktree add /tmp/pr2344-wt pr-2344-check` -- an independent
checkout of the PR's `consult.py` comment addition, its new spec doc,
and its new regression-guard test file (both untracked in this branch's
own tree; see Upstream basis), never the PR's pasted test output taken
as given. Spawning prompt scoped this observation to two specific
re-executions: the regression guard and the behavioral
`resolve_role_source()` check.

canonical: `gh pr view 2344 --json headRefName,headRefOid,state,mergedAt`
-- result:
```
branch=issue-2285/implementation sha=f50e689f2a1509cedc1192cdf755b9ddc513887e state=OPEN mergedAt=null
```
Confirms PR #2344 is open, not yet merged to main; its files are
therefore untracked in this branch's own tree and were read from the
independent worktree checkout below instead.

### Regression guard -- reproduced exactly

canonical: `python3 -m pytest test/test_consult_no_rulebook_identity_regression.py -v`
(PR worktree) -- result:
```
test_consult_py_carries_no_forbidden_rulebook_identifiers PASSED
test_unmapped_role_still_resolves_through_resolve_role_source PASSED
test_mapped_role_takes_the_same_single_path PASSED
3 passed in 0.84s
```
Matches the record's claim exactly: 3 passed.

### Regression guard -- mutation-tested against two reintroduced regressions

canonical: this session deliberately reintroduced, in the worktree copy
only, the two regressions the guard exists to catch, then reverted --
inserted `# rulebook_checkout marker` into the worktree's `consult.py`
and ran
`pytest test/test_consult_no_rulebook_identity_regression.py::NoRulebookIdentityInSource -q`
-- result:
```
E       - ['rulebook_checkout']
E       + [] : consult.py 가 은퇴한 rulebook/allowlist 식별자를 다시 물었다: ['rulebook_checkout']
FAILED test/test_consult_no_rulebook_identity_regression.py::NoRulebookIdentityInSource::test_consult_py_carries_no_forbidden_rulebook_identifiers
1 failed in 1.37s
```
The static guard fails when a forbidden identifier is reintroduced.

canonical: patched the worktree's `_readonly_plugin_dirs()` to branch on
`role not in _sp._ROLE_SKILLS` (skipping `resolve_role_source()` for
unmapped roles -- the allowlist-style branch #1955 removed and this
guard exists to catch) and ran
`pytest test/test_consult_no_rulebook_identity_regression.py::ReadonlyPluginDirsUnconditionalSkillRepo -v`
-- result:
```
E       AssertionError: Lists differ: [] != ['no-such-role-anywhere']
FAILED test/test_consult_no_rulebook_identity_regression.py::ReadonlyPluginDirsUnconditionalSkillRepo::test_unmapped_role_still_resolves_through_resolve_role_source
1 failed, 1 passed in 3.36s
```
The unmapped-role test fails under this mutation while its sibling
mapped-role test stays green in the same run, matching the expected
blast radius (the mutation only touches the unmapped branch).

canonical: `git status --porcelain && git diff --stat` in the worktree
after reverting both mutations -- result:
```
 M .orchestrate-hook-fires.log
 .orchestrate-hook-fires.log | 18 ++++++++++++++++++
 1 file changed, 18 insertions(+)
```
Only an unrelated hook log differs; `consult.py` itself was restored
byte-for-byte before the next check.

### Declared gates -- reproduced exactly

canonical: `python3 -m pytest tests/test_spawn_consult_panel.py -q` (PR
worktree) -- result: `58 passed, 1 xfailed in 1.04s`, matching the PR's
own Test plan count and pre-existing xfail.

canonical: `python3 -m pytest test/test_spawn_role_skill_resolution.py -q`
(PR worktree) -- result: `9 passed`.

canonical: `python3 gates/spec_index.py` (PR worktree) -- result:
`통과: 모든 spec 문서가 기록된 해시와 일치한다` (passes, no drift). All
three match the PR's claims.

### Spec citation check -- one discrepancy found

The proposal's "How you'll know it worked" requires the new spec's
citations to resolve against the current `consult.py`/`skills.py` line
ranges. This session read every cited line/range in the PR worktree's
copy of the new spec doc (untracked in this tree; see Upstream basis)
and checked it against `grep -n` output over the same worktree's
`consult.py`/`skills.py`.

canonical: `grep -n "ROOT / \"roles\" / f\"{role}.json\"" consult.py`,
`grep -n "resolve_role_source(" consult.py`, and manual inspection of
`skills.py:286-336` / `skills.py:354-375` (PR worktree) -- result:
```
resolve_role_source() calls found at: 642, 916, 1309
roles/<role>.json existence checks found at: 355, 690, 816, 1155, 1304
skills.py _ROLE_SKILLS: 286-337 (dict body ends 336, closing brace 337)
skills.py resolve_role_source(): 354-375
```
The spec doc's own cited numbers for the same eight `consult.py`
targets are `636/910/1303` (the three `resolve_role_source()` calls) and
`349/684/810/1149/1298` (the five existence checks); its two
`skills.py` citations are `286-336` and `354-375`. The `skills.py`
citations resolve exactly against the grep output above. Every one of
the eight `consult.py` citations lands 6 lines before its actual
target -- a uniform +6 offset, consistent with those citations having
been computed before the PR's own 6-line Korean comment block was
inserted above the first existence check (`consult.py:349-355` in the
PR diff's hunk), and never renumbered afterward.

## Why

Delegated scope was re-execution of the two named checks (regression
guard, behavioral `resolve_role_source()` check), not re-derivation of
new claims -- consistent with the posture prior execution-observation
records in this repo (issue-2227, issue-2298, issue-2314) have taken
toward PR-pasted evidence: re-run from an independent checkout, and
where a test's own detection power is asserted rather than just its
green result, mutation-test it (canonical: see the Regression guard --
mutation-tested subsection above for the pytest output this produced).
The spec-citation check was added on top of the two named
re-executions because the proposal's own "How you'll know it worked"
names citation resolution as an acceptance bar, and this session was
already reading the cited `consult.py`/`skills.py` line ranges to
locate the behavioral test's target function (`_readonly_plugin_dirs()`),
so checking them against the PR worktree's actual line numbers was a
small addition with its own dedicated evidence, captured above.

## Upstream basis

- `docs/issue-2285/reports/implementation.md` (untracked in this tree --
  lives on branch `issue-2285/implementation` at commit
  `f50e689f2a1509cedc1192cdf755b9ddc513887e`, PR #2344; see the `gh pr
  view 2344` citation under What was done for the open/unmerged status)
  -- the record whose acceptance evidence this session re-executed.
- `consult.py`, `skills.py` at the same commit (untracked in this tree,
  same branch) -- read from the independent worktree checkout, not this
  branch (which does not carry the PR's changes).
- The PR's new spec doc (`docs/specs/consult-guidance-source.md`,
  untracked in this tree, lives on `issue-2285/implementation`) and its
  new regression-guard test file
  (`test/test_consult_no_rulebook_identity_regression.py`, same commit,
  same untracked status) -- both read from the independent worktree
  checkout only.
- `docs/issue-2241/proposals/2026-08-25-stage-2-consult-skill-source-confirmation.md`
  (on `main`, present in this tree) -- the authoritative scope and "How
  you'll know it worked" bar this observation checked the delivered PR
  against.

## Open findings

- The PR's new spec doc's eight `consult.py` line citations (three
  `resolve_role_source()` call sites, five `roles/<role>.json` existence
  checks) each resolve 6 lines short of their actual target in the PR's
  own shipped `consult.py`; its three `skills.py` citations are
  accurate (canonical: see the Spec citation check evidence above for
  the full grep-vs-cited-number comparison). Per the same canonical
  evidence plus the Regression guard -- reproduced exactly and --
  mutation-tested subsections above, this finding does not disturb this
  record's own two delegated re-executions: those reproduced green and
  failed as expected under reintroduced regressions regardless of the
  spec's citation offsets. It does mean the proposal's own "How you'll
  know it worked" bar on citation resolution is not fully met as
  shipped. Resolution path: a one-line fix in the spec doc (shift the
  eight `consult.py` line numbers by +6) before or alongside merge;
  flagged here rather than fixed in this record because this role's
  scope is observation, not edit of another role's delivered files.

## Next steps

None -- `loop_state` above is this record kind's terminal value,
`handed-off`.
