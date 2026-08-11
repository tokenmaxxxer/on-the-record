# Current-state survey — issue #817 step 2 (implementation)

## Skip condition

Scout skipped: pure bugfix, no product-facing design decision open.
canonical: docs/issue-817/reports/defect-verification/current-state.md (read this session)
That merged step-1 record (PR#820) already pins the exact mechanism and
the fix shape; this step only implements it.

## Write set

- `harness/driver.py` — `instantiate_fixture_target` needs `git init` +
  an initial commit after `shutil.copytree`, so the fixture mirrors a
  real installed target's `.git` ancestry.
- new test file under `harness/` — regression test asserting the
  instantiated fixture has a reachable git root (`git rev-parse
  --show-toplevel` succeeds inside it).
- new implementation record under `docs/issue-817/reports/` — this
  role's phase-2 record.

## Evidence read

canonical: docs/issue-817/reports/defect-verification/current-state.md (read this session)
That merged step-1 record confirms `deliverable-guard.sh`'s
git-root-absence branch is the sole active bypass — relative-cwd and
the role-session branch were both ruled OUT with evidence there. Root
cause: `harness/driver.py`'s `instantiate_fixture_target` (function
body around lines 23-32) does `shutil.copytree` only, producing a
fixture with no `.git` anywhere in its ancestry, unlike every real
installed target (which is a git checkout). The record names the fix
as making the harness faithful (git-init the fixture), not touching
the guard, which it verified is correct for real targets.

canonical: on-the-record/hooks/deliverable-guard.sh (read this session)
Lines around 118-124 read:
```
    root = _git_root(cwd)
    if root is None:
        sys.exit(0)
```
canonical: on-the-record/hooks/deliverable-guard.sh (read this session, same file as above)
This confirms the branch is present and unmodified as of this survey.

## No alternative design decision

The fix shape (git-init the fixture copy) is dictated by the step-1
finding; the only implementation choice — plain `git init` + commit vs.
some heavier fixture-authoring change — has no real alternative: the
fixture must end up as a real, committed git repo to be faithful to a
real target, so there is nothing else to weigh.
