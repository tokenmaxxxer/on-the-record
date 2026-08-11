---
code_under_review:
  - docs/specs/enforcement-boundary.md
  - docs/specs/generated-paths.md
  - docs/specs/reconciled-index.md
  - tests/test_gates.py
  - on-the-record/hooks/gate-registration-guard.sh
  - on-the-record/hooks/test_gate_registration_guard.py
  - on-the-record/hooks/hooks.json
type: fix
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Delivered the approved proposal at
docs/issue-759/proposals/2026-08-11-boundary-registration-guard.md
(approved via issue comment `APPROVE issue-759/implementation`), both
halves:

1. Added the two missing rows for `record-claim-shape-directive.sh`
   (issue #730's hook) to `docs/specs/enforcement-boundary.md`
   (verdict `contract`, same act-class as the `directive.sh` row) and
   `docs/specs/generated-paths.md` (classification `n/a`, confirmed no
   write call in the script). This alone turns
   gates/test_boundary.py's t_all_gates_modules_recorded and
   gates/test_generated_paths.py's t_all_generators_recorded_and_disjoint
   green.
2. Fixed tests/test_gates.py's
   t_find_violations_uses_record_evidence_for_keywordless_merge by
   adding a `closure_sweep._pr_index_all = lambda root: (None, True)`
   mock (with matching teardown) so `find_violations` takes the
   per-branch fallback path the test's other mocks already target,
   mirroring the fix gates/test_closure_sweep.py's
   test_pr_view_failure_is_a_skip already landed for the same
   issue-682 fast-path regression.
3. Added `on-the-record/hooks/gate-registration-guard.sh`, a new
   `PreToolUse`+`Bash` `git commit` hook: when the staged set includes a
   newly-added `gates/*.py` (excluding `test_*.py`/`__init__.py`),
   `on-the-record/hooks/*.sh`, or `.github/workflows/*.yml` file, it
   denies the commit (exit 2) unless that file's basename has a row in
   `docs/specs/enforcement-boundary.md` (and, for a hook script, also
   `docs/specs/generated-paths.md`). Checked in at mode `100755`
   (confirmed via `git ls-files -s`). Fails open on any environment gap
   (`ORCHESTRATE_OFF`, missing `python3`/`git`, non-`git commit` Bash
   command, no matching staged file); fails closed only on a
   positively-determined missing registration.
4. Added `on-the-record/hooks/test_gate_registration_guard.py`, 12
   `t_*`-named pytest cases driving the script itself via
   `subprocess.run(["bash", str(GUARD)])` against a real git repo
   fixture: red (new gate module / new hook script, no row -> denied),
   green (row staged in the same commit -> passes), the issue's own
   stated empty-state green case (a change touching no new mechanism
   file passes untouched), an already-registered-module-edit green
   case, a `test_*.py`/`__init__.py` exclusion green case,
   `ORCHESTRATE_OFF`/non-commit-command bypass cases, an explicit
   `os.access(GUARD, os.X_OK)` assertion (after-proposal hunt, stance 4
   — see Hunt below), and two cases added after the before-landing hunt
   (stance 0, see Hunt below) reproducing and closing a rename/copy
   bypass.
5. Wired the new hook into `on-the-record/hooks/hooks.json`'s
   `PreToolUse`+`Bash` matcher array, next to
   `role-axis-completeness-guard.sh`.
6. Added `gate-registration-guard.sh`'s own rows to
   `docs/specs/enforcement-boundary.md` (`contract`) and
   `docs/specs/generated-paths.md` (`n/a`, reads/validates only), then
   ran `python3 gates/spec_index.py --update` — no diff, since neither
   spec file is one of `docs/specs/reconciled-index.md`'s three tracked
   rows (`protocol.md`, `protocol.ko.md`, `README.md`); ran anyway per
   the contract's "any `docs/specs/*` edit" requirement.

## Why

`main` kept landing red because the only check for boundary-spec
registration was a pytest assertion nothing runs automatically (this
repo carries no CI, #460) — #689 fixed the identical registration gap
once and it recurred within a day. This closes both the immediate
red-main state and the recurrence path: a landing-time hook now blocks
the same class of omission before it lands, instead of relying on
someone remembering to run the suite.

## Upstream

Based on: docs/issue-759/proposals/2026-08-11-boundary-registration-guard.md

## What did not work

None — no attempted approach was written then undone during this
build; the two hunt findings below were gaps in the approved design,
not abandoned attempts.

## Hunt

Two dispatches per the warrant directive, both recorded at
docs/issue-759/reports/implementation/hunt-2026-08-11-boundary-registration-guard.md
(this session's before-landing dispatch appended to the same file the
prior session's after-proposal dispatch already started).

closed_checks:
- check: after-proposal hunt, stance 4 (write-set-cannot-carry-this-work)
  code_sha: same as code_under_review above (working-tree files, no
  commit sha assigned to this uncommitted transition)
  finding: the frozen write set never named the executable-bit
  requirement for gate-registration-guard.sh, and no listed test
  checked it — hooks.json invokes every hook by its raw path with no
  interpreter prefix, so a missing +x bit fails silently (exit 126) at
  real invocation time even though every sibling test drives its
  script via subprocess.run(["bash", str(script)]), blind to the
  file's own execute permission (issue #459 hit this exact gap once).
  resolution: checked the script in at mode 100755 (chmod 755 before
  staging; confirmed via `git ls-files -s
  on-the-record/hooks/gate-registration-guard.sh` -> 100755) and added
  t_script_is_executable to
  on-the-record/hooks/test_gate_registration_guard.py, asserting
  os.access(GUARD, os.X_OK).
- check: before-landing hunt, stance 0 (assume-the-gate-is-bypassable)
  code_sha: same as code_under_review above
  finding: the guard's git diff --cached --name-status parsing only
  treated status exactly "A" as a registration target. A rename/copy
  of an existing, unrelated tracked file into a gates/*.py or
  on-the-record/hooks/*.sh path reports status "R100"/"C100", not "A"
  — so the rename step alone passed the guard silently, and a
  follow-up content edit on that now-tracked path showed as plain "M",
  which the guard's own design intentionally leaves untouched (editing
  an already-registered module's internals). The two-step sequence
  (git mv into a target path, then edit) landed a real, unregistered
  gate module through two ordinary git commit invocations without the
  hook ever returning non-zero. Reproduced in a scratch /tmp repo (not
  this repo's git state); full reproduction commands are in the
  hunt-record file's "before-landing — stance 0" section.
  resolution: broadened the status check in
  on-the-record/hooks/gate-registration-guard.sh from status == "A" to
  status == "A" or status[:1] in ("R", "C"), so a rename/copy's
  destination path (the last tab-separated field, same as an "A" row)
  is now checked for a registration row at the rename step itself.
  Added two regression cases to
  on-the-record/hooks/test_gate_registration_guard.py:
  t_rename_of_unrelated_tracked_file_into_new_gate_path_denies_commit
  (reproduces the hunt's exact scenario: git mv an unrelated tracked
  file into a new gate module path with no row -> denied at the rename
  commit) and t_rename_into_new_gate_path_with_row_in_same_commit_passes
  (green case: the row staged in the same rename commit -> passes).
  Re-ran python3 -m pytest
  on-the-record/hooks/test_gate_registration_guard.py -q and confirmed
  the fix closes the bypass (see Acceptance verification below).

## Acceptance verification

- issue #759 acceptance 1 — `main` restored to green — checked:
  `python3 -m pytest gates/ tests/ -q` — result: pass, derived: `python3 -m pytest gates/ tests/ -q`

```
$ python3 -m pytest gates/ tests/ -q
............................................................................ [ ...]
911 passed, 2 skipped in ...s
```

- issue #759 acceptance 2 — a fixture asserts a new gate module with no
  boundary row is denied at the landing path, and a change touching no
  registration target passes (the stated empty-state green case) —
  checked: `python3 -m pytest on-the-record/hooks/test_gate_registration_guard.py -q`
  — result: pass, derived: `python3 -m pytest on-the-record/hooks/test_gate_registration_guard.py -q`

```
$ python3 -m pytest on-the-record/hooks/test_gate_registration_guard.py -q
............
12 passed in ...s
```

## Open findings

None outstanding — both hunt findings above are resolved in this same
commit and closed above.
