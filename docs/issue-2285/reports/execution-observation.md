---
issue: 2285
role: execution-observation
author: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2285/reports/implementation.md
    sha: 28b45e2fca97995a39eb0f7e3bde48c427611e63
  - path: consult.py
    sha: c8c2c0bf226c8d81cfa28f4b84ba75d18c067319
  - path: docs/specs/consult-guidance-source.md
    sha: c8c2c0bf226c8d81cfa28f4b84ba75d18c067319
  - path: test/test_consult_no_rulebook_identity_regression.py
    sha: c8c2c0bf226c8d81cfa28f4b84ba75d18c067319
subject: PR #2367 (issue-2285, redelivered issue #2241 stage 2 "confirm
  consult.py's guidance source, role identity stays exposed"), branch
  issue-2285/implementation, head commit
  28b45e2fca97995a39eb0f7e3bde48c427611e63 (comment/spec/test commit
  c8c2c0bf226c8d81cfa28f4b84ba75d18c067319) -- the redelivery after the
  prior PR #2344 was closed unmerged by the 2026-08-25 history rewrite
test: independent re-execution of the declared gates
  (tests/test_spawn_consult_panel.py, test/test_spawn_role_skill_resolution.py,
  gates/spec_index.py), the new regression guard with both of its
  mutation tests reproduced independently, and a from-scratch citation
  check of every consult.py/skills.py line number in the PR's new spec
  doc against the PR's own worktree -- the exact check the prior
  delivery (PR #2344, R5) failed
result: passed
assertedBy: execution-observation session for issue-2285, independent of
  PR #2367's authoring (implementation) session
---

# issue-2285 — execution-observation record

## What was done

canonical: `git fetch origin pull/2367/head:pr-2367-check` and
`git worktree add /tmp/pr2367-wt pr-2367-check` -- an independent
checkout of the PR's `consult.py` comment addition, its new spec doc,
its new regression-guard test file, and its own implementation record
(all untracked in this branch's own tree; see Upstream basis), never
the PR's pasted evidence taken as given.

canonical: `gh pr view 2367 --json headRefOid` -- result:
`28b45e2fca97995a39eb0f7e3bde48c427611e63`, matching the worktree's
checked-out commit.

### Declared gates -- reproduced exactly

canonical: `python3 -m pytest tests/test_spawn_consult_panel.py -q` (PR
worktree) -- result: `63 passed, 1 xfailed in 1.18s`, matching the
record's claimed `63 passed, 1 xfailed`.

canonical: `python3 -m pytest test/test_spawn_role_skill_resolution.py -q`
(PR worktree) -- result: `9 passed`, matching the record's claim
(unmodified test, no behavior change).

canonical: `python3 gates/spec_index.py` (PR worktree) -- result:
`통과: 모든 spec 문서가 기록된 해시와 일치한다` (passes, no drift),
matching the record's claim.

### Regression guard -- reproduced exactly

canonical: `python3 -m pytest test/test_consult_no_rulebook_identity_regression.py -v`
(PR worktree) -- result:
```
ReadonlyPluginDirsAlwaysSkillRepoTest::test_unmapped_role_still_reaches_resolve_role_source PASSED
ReadonlyPluginDirsAlwaysSkillRepoTest::test_mapped_role_reaches_resolve_role_source PASSED
NoRulebookIdentitySourceStaticScanTest::test_consult_py_never_names_a_retired_rulebook_identifier PASSED
3 passed in 0.85s
```
Matches the record's claim exactly: 3 passed.

### Regression guard -- mutation-tested against two reintroduced regressions

canonical: this session inserted `rulebook_checkout = None` immediately
before `consult_cmd`'s definition in the worktree's `consult.py` (a
forbidden identifier reintroduced) and ran
`python3 -m pytest test/test_consult_no_rulebook_identity_regression.py -v`
-- result:
```
AssertionError: <re.Match object; span=(33257, 33274), match='rulebook_checkout'> is not None : consult.py 가 은퇴한 rulebook 식별자 'rulebook_checkout' 를 다시 쓰고 있다 ...
FAILED test/test_consult_no_rulebook_identity_regression.py::NoRulebookIdentitySourceStaticScanTest::test_consult_py_never_names_a_retired_rulebook_identifier
1 failed, 2 passed in 1.26s
```
The static guard fails when a forbidden identifier is reintroduced; the
two behavioral tests, untouched by this mutation, stay green.

canonical: this session then reverted that mutation and instead patched
`_readonly_plugin_dirs()` in the worktree's `consult.py` to branch on
`role in _sp._ROLE_SKILLS` -- calling `resolve_role_source()` only for
mapped roles and returning `[]` for unmapped ones, the allowlist-style
branch #1955 removed -- and ran the same test command -- result:
```
AssertionError: Lists differ: [] != ['no-such-role']
FAILED test/test_consult_no_rulebook_identity_regression.py::ReadonlyPluginDirsAlwaysSkillRepoTest::test_unmapped_role_still_reaches_resolve_role_source
1 failed, 2 passed in 4.84s
```
The unmapped-role behavioral test fails under this mutation while its
mapped-role sibling and the static scan stay green in the same run,
matching the expected blast radius (the mutation only touches the
unmapped branch).

canonical: `git status --porcelain && git diff --stat
c8c2c0bf226c8d81cfa28f4b84ba75d18c067319~1
c8c2c0bf226c8d81cfa28f4b84ba75d18c067319 -- consult.py` in the worktree
after reverting both mutations (`git checkout -- consult.py`) --
result:
```
 M .orchestrate-hook-fires.log
 consult.py | 6 ++++++
 1 file changed, 6 insertions(+)
```
Only an unrelated hook log differs from the worktree's starting state;
the PR's own `consult.py` change against its parent commit is confirmed
to be exactly the claimed 6-line comment insertion, nothing else.

### Spec citation check -- re-derived from scratch, no discrepancy found

canonical: `docs/issue-2285/reports/conformance-review.md:217-223`
(present in this tree) -- R5's rerun of its own acceptance block
against the prior delivery (PR #2344, commit `0baac6010bb`) found every
`consult.py` citation in the new spec doc landing 6 lines short of its
actual target statement -- computed before that commit's own 6-line
comment insertion, never recomputed after. This redelivery's
implementation record claims to have fixed that by deriving every
citation only after the comment was in place
(`docs/issue-2285/reports/implementation.md`, "Why" section, untracked
in this tree; see Upstream basis). This session re-derived all eleven
cited line numbers independently, without reading the implementation
record's own "Citation self-check" section first, then compared.

canonical: `grep -n 'resolve_role_source(role' consult.py` (PR
worktree) -- result: calls at lines 690, 964, 1357 -- matches the PR's
new spec doc's (`docs/specs/consult-guidance-source.md`, untracked in
this tree; see Upstream basis) citations exactly.

canonical: `grep -n '^def resolve_role_source\|^def resolve_skill_source' skills.py`
(PR worktree) -- result: `resolve_role_source` at 354,
`resolve_skill_source` at 379 -- combined with `sed -n '354,379p'
skills.py` read in full, the function body (docstring, `names = ...` at
366, `skill_dirs = ...` at 367, the `hooked`/`sys.exit` block at
368-373, the `return` statement at 374-376) spans exactly 354-376,
matching the spec doc's citation of `skills.py` lines 354 through 376 and its finer-grained
`366`, `367`, `368-373`, `374-376` citations line-for-line.

canonical: `grep -n 'f = _sp.ROOT / "roles"' consult.py` (PR worktree)
-- result: existence checks at lines 403, 738, 864, 1203, 1352 --
matches the spec doc's five cited existence-check lines exactly.

canonical: `sed -n '286p;336,338p' skills.py` (PR worktree) -- result:
line 286 is `_ROLE_SKILLS = {`, line 337 is the dict's closing `}` --
matches the spec doc's citation of `skills.py` lines 286 through 337
exactly.

Every one of the eleven line citations in the PR's new spec doc (three
`resolve_role_source()` call sites, the `resolve_role_source()`
function's own 354-376 span and its four sub-ranges, five
`roles/<role>.json` existence checks, and the `_ROLE_SKILLS` 286-337
span) resolves exactly against this session's own independently-run
`grep`/`sed` output. Unlike PR #2344, this redelivery shows no citation
drift.

## Why

Delegated scope was independent re-execution of the declared gates and
the regression guard (including mutation-testing it, per the posture
prior execution-observation records in this repo have taken toward
PR-pasted evidence -- re-run from an independent checkout, and where a
test's own detection power is asserted rather than just its green
result, mutation-test it), plus a from-scratch repeat of the spec
citation check this issue's own prior review found the predecessor PR
failing (canonical: `docs/issue-2285/reports/conformance-review.md:217-223`,
R5, cited in full under Spec citation check above). The citation check
was re-derived independently rather than merely re-reading the
implementation record's own "Citation self-check" section, per
`defect-verification-independence-from-upstream-verdicts`: this
session's own `grep`/`sed` output was produced first, and the record's
claimed line numbers were compared against it afterward, not the
reverse.

## Upstream basis

- `docs/issue-2285/reports/implementation.md` (untracked in this tree --
  lives on branch `issue-2285/implementation` at commit
  `28b45e2fca97995a39eb0f7e3bde48c427611e63`, PR #2367) -- the record
  whose acceptance evidence and citation-fix claim this session
  re-executed and independently re-derived.
- `consult.py`, `docs/specs/consult-guidance-source.md`,
  `test/test_consult_no_rulebook_identity_regression.py` (untracked in
  this tree, commit `c8c2c0bf226c8d81cfa28f4b84ba75d18c067319`, same
  branch) -- read from the independent worktree checkout only, never
  from the PR's own pasted text.
- `docs/issue-2285/reports/conformance-review.md` (present in this tree,
  the prior review of PR #2344) -- source of the R5 citation-drift
  finding this session's Spec citation check re-verified was actually
  fixed in the redelivery.
- `docs/issue-2241/proposals/2026-08-25-stage-2-consult-skill-source-confirmation.md`
  (on `main`, present in this tree) -- the authoritative scope and "How
  you'll know it worked" bar this observation checked the redelivered
  PR against.

## Open findings

None. The one open finding from this issue's prior execution-observation
round (citation drift against PR #2344, `docs/issue-2285/reports/execution-observation.md`
at commit `8fefe7ffd678d9b0e15010ee27b014d51bec77ae` on `main`) is
confirmed fixed in PR #2367 -- canonical: see Spec citation check above
for the full independent re-derivation of all eleven citations against
the PR worktree's actual `consult.py`/`skills.py` line numbers. No
resolution path is needed since no finding is open.

## Next steps

None -- `loop_state` above is this record kind's terminal value,
`handed-off`, and no open finding needs a resolution path.
