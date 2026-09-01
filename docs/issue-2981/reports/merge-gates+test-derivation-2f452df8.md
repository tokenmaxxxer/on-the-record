---
issue: 2981
role: merge-gates+test-derivation-2f452df8
author: merge-gates+test-derivation-2f452df8
skills: merge-gates (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: gates/spawn_on_pr.py
    sha: same-commit
  - path: lifecycle.py
    sha: same-commit
  - path: spawn.py
    sha: same-commit
  - path: tests/test_respawn_deliverable_gate.py
    sha: same-commit
---

# issue-2981 — merge-gates+test-derivation-2f452df8 record

Build-now delivery (CORE_BUILD_NOW=1, set by the spawner) — no phase-1 proposal round.

## What was done

The crashed-verdict respawn path now consults a "does this subject already
have a deliverable PR" check before acting on a `crashed` verdict, instead
of respawning unconditionally.

- New `subject_has_deliverable(root, subject) -> dict | None` in
  `gates/spawn_on_pr.py`, layered directly on the two existing per-subject
  resolvers already in that file — derived: `grep -n '^def subject_has_deliverable\|^def subject_deliverable_record\|^def subject_deliverable_branch' gates/spawn_on_pr.py` — result:
  ```
  183:def subject_deliverable_record(subject_board: dict) -> tuple[str | None, dict]:
  224:def subject_deliverable_branch(subject: str, pr_index: dict[str, dict] | None) -> str | None:
  251:def subject_has_deliverable(root: Path, subject: str) -> dict | None:
  ```
  It checks the landed state first (`subject_deliverable_record()` against
  `spawn.board(root)` — merged records already on disk) and, only if
  nothing landed yet, the still-open state (`subject_deliverable_branch()`
  against `closure_sweep._pr_index_all()`). Both resolvers already exclude
  record-only (verification/measurement) records/branches by construction
  (`verifies_subject: true` self-declaration for the landed case,
  `_VERIFICATION_SLOT_RE` naming for the open case — the same filter the
  auto-spawn tick in that file uses to *open* those record-only PRs in the
  first place), so a subject with only a record-only PR resolves to a
  `None` return here, identically to "no PR at all". Any `gh` failure
  inside `closure_sweep._pr_index_all()` also resolves to `None`. Returns
  `{"number": int|None, "branch": str, "state": "OPEN"|"MERGED"}` when a
  real deliverable is found.
- `lifecycle.py::_subject_has_deliverable()`: a lazy-import wrapper (same
  idiom as `watchdog.py`'s `_fetch_issue_or_pr_via_cache`/`_board_read`)
  that reaches `gates/spawn_on_pr.py` at call time — root-level modules
  cannot import that module at load time without closing an import cycle
  (`gates/spawn_on_pr.py` imports `spawn` at its own top level) — derived: `grep -n 'sys.path.insert.*gates' lifecycle.py` — result: `sys.path.insert(0, str(ROOT / "gates"))` present once, inside this new function.
  Re-exported as `spawn._subject_has_deliverable` — derived: `grep -n '_subject_has_deliverable = lifecycle' spawn.py` — result: `_subject_has_deliverable = lifecycle._subject_has_deliverable`.
- `lifecycle.py::_auto_respawn_check()` — the function that decides
  whether a `crashed` verdict actually triggers a respawn — now calls
  `_sp._subject_has_deliverable(Path(work), f"issue-{issue}")` immediately
  after confirming `verdict == "crashed"` and before any of the existing
  respawn side effects (event log, attempt counters, `_respawn_or_cap()`).
  A positive match prints a `[respawn] ... skipping respawn` line naming
  the PR (`PR #<number>` when a number is known, else the branch), writes
  a `respawn_skipped_existing_deliverable` ledger event carrying the PR
  number/branch/state, and returns without ever reaching
  `_respawn_or_cap()`. `None` (absence, record-only-only, or lookup error)
  falls through to the existing respawn logic completely unchanged —
  derived: `grep -n 'subject_has_deliverable\|respawn_skipped_existing_deliverable' lifecycle.py` — result:
  ```
  484:def _subject_has_deliverable(root: Path, subject: str) -> dict | None:
  541:    subject = f"issue-{issue}"
  542:    existing = _sp._subject_has_deliverable(Path(work), subject)
  543:    if existing is not None:
  ...
  549:        _sp.ledger_write({
  550:            "event": "respawn_skipped_existing_deliverable",
  ```
- A new test file (12 tests) adds partition-level tests of
  `subject_has_deliverable()` plus end-to-end tests of
  `spawn._auto_respawn_check()` against the real crash-fixture shape from
  `test/test_reconcile_crash_verdict_race.py` (bare remote + clone, dead
  wrapper pid so `session_end_verdict()` genuinely returns `crashed`) —
  derived: `python3 -m pytest tests/test_respawn_deliverable_gate.py -q` — result:
  ```
  ............                                                             [100%]
  12 passed in 0.85s
  ```

Verdict-computation code (`session_end_verdict()`, `reconcile()`,
`_build_expected`/`_build_observed`) and watchdog HEALTHY-flip code were
not touched — issue #2969's separate scope.

## Why

test-derivation (skill, invoked this turn) partitioned "does this subject
already have a deliverable" into four equivalence classes over subject
deliverable state — no PR / record-only PR / open deliverable PR / merged
deliverable PR — derived: `grep -n '^    def test_respawn' tests/test_respawn_deliverable_gate.py` — result:
```
94:    def test_respawn_proceeds_without_deliverable_when_no_pr_exists(self):
101:    def test_respawn_proceeds_without_deliverable_when_only_record_only_pr_open(self):
109:    def test_respawn_proceeds_without_deliverable_when_only_record_only_pr_merged(self):
120:    def test_respawn_skips_existing_deliverable_when_pr_open(self):
129:    def test_respawn_skips_existing_deliverable_when_pr_merged(self):
```
plus a fifth non-functional partition (lookup error) the issue's own
must-not list calls out explicitly. Each partition maps onto one of the
three required `pytest -k` substrings (no-PR and record-only share
`respawn_proceeds_without_deliverable`; open and merged share
`respawn_skips_existing_deliverable`; the report-content assertions are
`respawn_skip_is_reported`), and the lookup-error partition is folded
into the "proceeds" side rather than getting its own name, since the
acceptance criteria treat "error" and "absence" as one required behavior
(fail toward respawn) — a separate test name there would have implied a
different required behavior the issue explicitly rejects.

merge-gates (skill, invoked this turn) shaped the new check as a
binary/machine-evaluable gate condition (`subject_has_deliverable()`
returns a definite `dict` or `None`, never a fuzzy "maybe") with the
default direction on absence/error fixed to the safe side — proceed with
respawn, not suppress it — matching this repo's other merge-gate-adjacent
checks (e.g. `required_verification_missing()`'s own fail-open
conventions in the same file) rather than inventing a new failure
convention for this one call site. The skip path's reporting requirement
(name the PR, never go silent) is the other half of the same
four-property gate shape: a gate that can silently suppress an action
without saying why is not auditable.

`subject_deliverable_branch()`'s existing `_VERIFICATION_SLOT_RE` naming
filter was reused for the open-PR case instead of
`merge_gate.py::_own_pr_supplies_verification()`'s `git show
origin/<branch>:...` content check, even though the issue names the
latter explicitly as prior art. `_own_pr_supplies_verification()` needs a
locally mirrored `origin/<branch>` ref (fetched once, up front, by
`check_runner.fetch_all_skill_branches()` in the merge-gate's own
`evaluate()`) that the respawn path never fetches, and on any git-show
failure it returns `False` ("not record-only") — exactly backwards for
this call site, where an unreadable branch must not be treated as a
confirmed deliverable (that would turn an uncertain read into a silent
skip, the one thing the issue's must-not list forbids).
`subject_deliverable_branch()` degrades the correct way instead: any
uncertainty there already resolves to a plain `None` ("no candidate
found"), which this change's caller already treats as "no deliverable,
proceed".

## What did not work

None.

## Upstream basis

All four `sha:` entries are `same-commit`: the check, its wiring into the
respawn path, and its tests all land in this same commit, per contract
§1. No prior docs/issue-2981/ artifact existed to build on — derived: `git log --oneline -- docs/issue-2981/` — result: empty (no prior commits touching this issue's docs tree) before this one.

## Open findings

None.

acceptance: `python3 -m pytest tests/ -k respawn_skips_existing_deliverable -q` — result:
```
....                                                                     [100%]
4 passed in 0.96s
```
acceptance: `python3 -m pytest tests/ -k respawn_proceeds_without_deliverable -q` — result:
```
......                                                                   [100%]
6 passed in 0.99s
```
acceptance: `python3 -m pytest tests/ -k respawn_skip_is_reported -q` — result:
```
..                                                                       [100%]
2 passed in 0.94s
```
derived: `python3 -m pytest test/test_reconcile_crash_verdict_race.py -q` (existing crashed-verdict/respawn regression suite, run unmodified against this change) — result:
```
.........                                                                [100%]
9 passed in 0.90s
```
derived: `python3 -m pytest test/ tests/ gates/ -q` (full repo regression sweep) — result:
```
17 failed, 680 passed, 3 xfailed in 31.75s
```
derived: `git stash && python3 -m pytest test/test_convention_equivalence.py test/test_local_dependency_env.py test/test_spawn_cross_family_skill_selection.py test/test_spawn_artifact_skill_pairing.py test/test_spawn_skill_judge_haiku_timeout_overlap.py tests/test_spawn_gate_wiring.py tests/test_tmp_resource_gc.py -q && git stash pop` (same files, base branch, this change stashed out) — result: `16 failed, 113 passed in 6.99s` — 16 of the 17 full-sweep failures reproduce identically on the unmodified base branch: pre-existing, unrelated to skill selection/hook wiring/tmp-resource-gc test infra, none of it touching `lifecycle.py`, `spawn.py`, or `gates/spawn_on_pr.py`. The 17th failure (`tests/test_tmp_resource_gc.py`'s `test_worktree_for_ref_success_path_is_gc_sweepable_end_to_end`) did not reproduce in isolation — derived: `python3 -m pytest tests/test_tmp_resource_gc.py -q` — result: `8 passed in 0.89s` — consistent with a parallel-run (`pytest-xdist`, `-n auto`) shared-ledger ordering flake rather than a regression from this change.

## Next steps

None — loop_state is terminal (landed). derived: the three acceptance
commands above (`respawn_skips_existing_deliverable`,
`respawn_proceeds_without_deliverable`, `respawn_skip_is_reported`) all
pass, so no further work remains open on this issue's scope.

skill-verdict: merge-gates — applied: invoked; used to shape the
respawn-suppression condition as a binary/machine-evaluable check
(has-deliverable) with fail-open-toward-respawn as the safe default on
absence/error, and explicit reporting on skip
skill-verdict: test-derivation — applied: invoked; used to derive the
equivalence partitions (no PR / record-only PR / open deliverable PR /
merged deliverable PR) mapped onto the three named pytest -k test
functions
other mounted skills: not triggered

Closes #2981
