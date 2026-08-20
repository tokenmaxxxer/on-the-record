# Current-state survey — issue #1742 conformance-review

## Target artifact and spec
- Target: commit df7046f7 ("issue-1742: phase-2 delivery — spawn.py
  --skills additive mount (#1744)"), touching `spawn.py` and
  `test/test_spawn_skills_mount.py`.
  canonical: `git show df7046f7 --stat` (read directly)
- Spec: issue #1742 body, Acceptance section (3 numbered criteria, each
  naming a `test/test_spawn_skills_mount.py` check).
  canonical: `gh issue view 1742` (read directly)

## Scout skip record
Skip condition: spec literally leaves no design decision open — this
role's phase-1 output is a mechanical requirement-list derivation from
the issue's own numbered Acceptance section, not a build with a field
to survey best-in-class exemplars for.

## What exists today (board state)
canonical: `find docs/issue-1742 -type f` (read directly)
- Board condition per role spec (issue #521): implementation commit
  landed on `main` (df7046f7) and no conformance-review record file
  exists yet for that sha — the `find` output above listed only
  `reports/implementation.md`, `reports/implementation/survey.md`,
  `proposals/skills-mount.md`; no conformance-review report path and no
  `reports/conformance-review/` directory prior to this session's
  writes.

## Test suite state
canonical: `python3 -m pytest test/test_spawn_skills_mount.py -v` (executed this session)
```
derived: python3 -m pytest test/test_spawn_skills_mount.py -v
11 passed in 0.86s
```
canonical: pytest run above (executed this session)
acceptance: python3 -m pytest test/test_spawn_skills_mount.py -v — result: 11 passed

## Requirement list (from issue #1742 Acceptance, verbatim-derived)
canonical: `gh issue view 1742` (read directly, Acceptance section)

1. `--skills a,b` mounts named skills (as extra `--plugin-dir` entries)
   and the no-flag path is argv/env-byte-identical to before.
   - Named check: "argv/env/workspace-layout assertions for both cases;
     byte-identical no-flag case diffs the assembled argv+env against
     the pre-change fixture."
2. canonical: `gh issue view 1742` (read directly, Acceptance item 2)
   Unknown skill name fails closed (non-zero exit) before any
   workspace/branch creation.
   - Named check: "unknown-name case ... asserting non-zero exit and no
     workspace/branch creation."
3. canonical: `gh issue view 1742` (read directly, Acceptance item 3)
   Skill list + skill-repository SHA appear in the roster entry and the
   co-injected directive text when `--skills` is used; absent
   otherwise.
   - Named check: "record-fields case."

## Notable surface for phase 2 (candidate divergences, not verdicted here)
- Requirement 1's named check text specifies diffing against "the
  pre-change fixture." The landed test class
  `SpawnCmdByteIdenticalNoFlagTest` has no stored fixture file; its own
  docstring states one doesn't exist in this repo and substitutes a
  same-call self-comparison (`skill_dirs=None` vs explicit `None`
  defaults) instead.
  canonical: `test/test_spawn_skills_mount.py` lines 21-46 (read directly, df7046f7)
- Requirement 3's test class `RecordFieldsCarrySkillsAndShaTest`
  constructs the roster-entry dict and task-string append inline in the
  test file rather than calling `spawn._spawn_one`/
  `spawn.roster_register`; only `UnknownSkillFailsClosedBeforeWorkspaceTest`
  (requirement 2) exercises `_spawn_one` for real.
  canonical: `test/test_spawn_skills_mount.py` lines 154-217 (read directly, df7046f7)

Both items are flagged as candidates for phase-2 verdicting, not
resolved here — phase 1 of this role produces a requirement list, never
a verdict.
