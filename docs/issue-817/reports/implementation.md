---
code_under_review:
  - harness/driver.py
  - harness/test_driver.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #817 step 2

## What was done

`harness/driver.py`'s `instantiate_fixture_target` now `git init`s the
copied fixture and makes one initial commit (`git add -A` + `git
commit`, with a fixed harness committer identity), so the returned
directory is a real git repo with a reachable `.git` root — matching
every real installed target. Added `harness/test_driver.py` asserting
`git rev-parse --show-toplevel` succeeds inside a freshly instantiated
fixture and resolves to the fixture's own directory.

## Why

canonical: docs/issue-817/reports/defect-verification/current-state.md (read this session)
The merged step-1 record (PR#820) pinned the root cause as a harness
fidelity gap, not a guard bug: `deliverable-guard.sh` correctly denies
un-delegated writes whenever a `.git` root is reachable from `cwd`
(verified this session — see Acceptance verification below), and only
exits 0 silently when no git root exists anywhere in the write's
ancestry. `instantiate_fixture_target` produced exactly that
git-root-less state via a bare `shutil.copytree`, so every #776 harness
run was measuring a fixture the guard was never designed to protect.
Making the fixture a faithful git checkout closes the gap without
touching the guard.

## Upstream basis

canonical: docs/issue-817/reports/defect-verification/current-state.md (read this session)
docs/issue-817/reports/defect-verification/current-state.md (PR#820, merged).

## Acceptance verification

checked: instantiate a fixture with the fixed `instantiate_fixture_target` outside any scratch/tmp-exempt path, then pipe a Write/Edit-shaped PreToolUse payload targeting a file inside it to `on-the-record/hooks/deliverable-guard.sh` with `CLAUDE_ROLE` unset — result: denied

canonical: on-the-record/hooks/deliverable-guard.sh run this session (live subprocess, not summarized)
```
$ python3 -c "from driver import instantiate_fixture_target; instantiate_fixture_target('/home/jwjung/fxcheck')"
$ cd /home/jwjung/fxcheck && env -u CLAUDE_ROLE bash -c '
echo "{\"cwd\":\"/home/jwjung/fxcheck\",\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"/home/jwjung/fxcheck/fixture_target/__init__.py\"}}" \
  | bash on-the-record/hooks/deliverable-guard.sh; echo rc=$?'
orchestrate: this is an orchestrator session and /home/jwjung/fxcheck/fixture_target/__init__.py is a deliverable path in a board repo. Deliverables are role work: draft the issue, get the user's confirmation, and spawn the role (spawn.py <role> ... --issue <n>). You author only confirmed issues, PR comments, and docs/specs/approvers.md.
rc=2
```
Before the fix (fixture instantiated by the un-patched, `shutil.copytree`-only function, i.e. no `.git` anywhere in its ancestry), the identical payload against the identical guard exited `rc=0` with no stderr — this was the reproduction step confirming the mechanism before applying the fix (temp fixture instantiated under `/tmp`, then re-run outside `/tmp` to rule out the scratch-path exemption as a confound).

checked: `harness/test_driver.py` new test suite — result: pass
canonical: pytest run this session (raw output, not summarized)
```
$ cd harness && python3 -m pytest test_driver.py -q
.                                                                        [100%]
1 passed in 0.06s
```

## Doc placement

- No env var, config key, dependency, or migration introduced — no
  handbook update required.
- No new library-or-format choice over a named alternative and no
  changed public signature/wire format — the one design choice (fix
  the fixture vs. patch the guard) is recorded in this record's "Why"
  section and in the phase-1 proposal's Rationale section, not as a
  separate architecture-decision-record entry, since it changes no
  interface.
- No benchmark/investigation numbers beyond the pass/fail evidence
  already inlined above — no additional reports entry beyond this
  record.

## What did not work

None.

## Hunt

closed_checks:
- name: guard-unchanged-check
  code_sha: harness/driver.py, harness/test_driver.py (working tree, this record)
  canonical: git status run this session (read this session)
  result: confirmed `on-the-record/hooks/deliverable-guard.sh` untouched by this change (only `harness/driver.py` and new `harness/test_driver.py` are in the write set); diff scope verified via `git status` at commit time.

## Open findings

None.
