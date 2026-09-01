---
issue: 2981
role: silent-failure-audit-5c0dd300
author: silent-failure-audit-5c0dd300
skills: silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-2981/reports/merge-gates+test-derivation-2f452df8.md
    sha: same-commit
  - path: docs/issue-2976/reports/adversarial-review-8afe9ef3.md (independent verification of PR #3002, live-reproduced the gap this record fixes)
    sha: 7961f712dbb2afbf34a3b85aaec76ec04a2c8320
---

# issue-2981 — silent-failure-audit-5c0dd300 record

Build-now delivery (CORE_BUILD_NOW=1, set by the spawner) — no phase-1
proposal round. Follow-up on PR #3002 (branch
`issue-2981/merge-gates+test-derivation-2f452df8`), fixing a gap PR #3006
(independent verification of PR #3002) live-reproduced.

## What was done

PR #3006 found that `gates/spawn_on_pr.py`'s still-open-PR record-only
exclusion — `_VERIFICATION_SLOT_RE = re.compile(r"^independent-verification-\d+$")`,
used inside `subject_deliverable_branch()` to keep a record-only
verification/measurement PR from being misresolved as a subject's
deliverable — matched only that one literal slug. This repo's other real
record-only branch convention, `adversarial-review-*` (every independent
verification actually spawned in this repo today uses that convention, not
`independent-verification-<N>`), was NOT excluded, so an
`adversarial-review-*` PR would be misresolved as the deliverable and
suppress a legitimate respawn — the exact inversion #2981 exists to
prevent, just triggered by a different branch name than the issue's
original report.

Fixed per this session's spawning instructions, reusing the standard issue
#2974 already established in `gates/check_runner.py` for the identical
record-only-vs-implementation question: decide by whether the PR's diff
touches paths outside `docs/`, never by a branch-name/slug pattern.

- `gates/spawn_on_pr.py`: removed `_VERIFICATION_SLOT_RE` and its one call
  site. Added `_branch_looks_like_deliverable(root, pr_number) -> bool`,
  which calls the already-landed `check_runner.pr_diff_paths()` (`gh pr
  diff <pr> --name-only`) and `check_runner.touches_implementation_paths()`
  — derived: `grep -n "^def pr_diff_paths\|^def touches_implementation_paths" gates/check_runner.py` — result:
  ```
  461:def pr_diff_paths(repo: Path, pr: int) -> list[str] | None:
  474:def touches_implementation_paths(paths: list[str] | None) -> bool:
  ```
  `subject_deliverable_branch()` now calls this per `{subject}/*` candidate
  branch instead of matching the branch suffix against the old regex —
  derived: `grep -n "_branch_looks_like_deliverable\|_VERIFICATION_SLOT_RE" gates/spawn_on_pr.py` — result:
  ```
  gates/spawn_on_pr.py:70:# below for what replaced the branch/roster exclusion the old tuple also
  gates/spawn_on_pr.py:71:# drove (originally a regex matching that literal slug, `_VERIFICATION_
  gates/spawn_on_pr.py:72:# SLOT_RE`; issue #2981 retired it -- see that function's docstring).
  gates/spawn_on_pr.py:229:def _branch_looks_like_deliverable(root: Path, pr_number: int | None) -> bool:
  gates/spawn_on_pr.py:258:def subject_deliverable_branch(root: Path, subject: str,
  gates/spawn_on_pr.py:286:                  and _branch_looks_like_deliverable(root, entry.get("number"))]
  ```
  (no remaining functional use of the old regex — the three grep hits left
  are historical prose comments about the regex it replaced.)
- `subject_deliverable_branch()` gained a leading `root: Path` parameter
  (needed to read each candidate's diff) — threaded through its three call
  sites: `subject_has_deliverable()`, `missing_verification()`, and
  `_missing_verification_closed()`, all of which already had `root` in
  scope.
- `_branch_looks_like_deliverable()`'s fail direction is deliberately the
  OPPOSITE of `touches_implementation_paths()`'s own `paths is None ->
  True` default: an unreadable/`None` diff here returns `False` ("not a
  confirmed deliverable"), so an unreadable branch falls through to "no
  deliverable found" (respawn proceeds) rather than being mistaken for a
  confirmed deliverable that suppresses one — preserving issue #2981's own
  must-not ("absence or lookup error must default to respawn, never to a
  silent skip"). `check_runner`'s own fail-closed default fits its own
  caller (score as implementation when uncertain); it would be backwards
  here.
- Tests: `tests/test_respawn_deliverable_gate.py` — added
  `test_respawn_proceeds_without_deliverable_when_only_adversarial_review_pr_open`,
  which reproduces PR #3006's exact finding against an `adversarial-review-*`
  branch and proves it is now excluded; added a `check_runner.pr_diff_paths`
  mock to the two pre-existing tests that resolve a real still-open branch
  (`...only_record_only_pr_open`, `...skips_existing_deliverable_when_pr_open`)
  since the diff-content check is now a real (mockable) `gh` call instead of
  a pure name match. `gates/test_spawn_on_pr.py` — updated the
  `subject_deliverable_branch` monkeypatch lambda's signature (now takes
  `root` first) and added a `check_runner.pr_diff_paths` mock to
  `test_closed_and_open_subjects_mixed_only_open_unmappable_branch_reported`
  (the one pre-existing test this change broke, since its `pr_index` entry
  needs a diff-content signal now).

Not touched, per the spawning instructions' explicit scope limit:
`lifecycle.py::_self_trigger_respawn()` — confirmed by this session's own
diff, derived: `git diff --stat` (this session's changes only) — result:
```
 gates/spawn_on_pr.py                   | 103 +++++++++++++++++++++++----------
 gates/test_spawn_on_pr.py              |   4 +-
 tests/test_respawn_deliverable_gate.py |  25 +++++++-
 3 files changed, 98 insertions(+), 34 deletions(-)
```
— `lifecycle.py` and `spawn.py` do not appear.

## Why

The alternative rejected: extending `_VERIFICATION_SLOT_RE` with a second
alternation branch for `adversarial-review-*` (`^(independent-verification-
\d+|adversarial-review-[0-9a-f]+)$` or similar). That was explicitly the
approach this session's spawning instructions ruled out — it fixes today's
two known record-only conventions but leaves the same class of bug for the
next one (any future record-only branch naming convention this repo
adopts would need a third alternation, discovered only after it silently
inverts the gate again, the same way `adversarial-review-*` did here).
Issue #2974 already solved the identical classification problem
(record-only vs. implementation PR) the diff-content way in
`check_runner.py`; reusing that standard here means the two places in this
codebase that need to answer "is this PR record-only" now agree on one
property of the PR (what its diff touches) instead of maintaining two
independently-drifting name lists.

## What did not work

Initially called `check_runner.pr_diff_paths()`/`touches_implementation_paths()`
expecting them to already be present — this session's branch
(`issue-2981/merge-gates+test-derivation-2f452df8`, PR #3002) was cut
before issue #2974 (which added those functions) landed on `main`, so the
first test run failed with `AttributeError: module 'check_runner' has no
attribute 'pr_diff_paths'`. Resolved by merging `origin/main` into the
branch (`git merge origin/main --no-edit`, clean, no conflicts) before
writing the fix, rather than reimplementing issue #2974's diff-classification
logic locally.

## Upstream basis

`gates/check_runner.py`'s `pr_diff_paths()`/`touches_implementation_paths()`
(reused, not modified) landed in commit `7961f712` (issue #2974, PR #2994),
pulled into this branch via the merge above. This session's own code and
test changes are all `same-commit` (this commit). `docs/issue-2981/reports/
merge-gates+test-derivation-2f452df8.md` is PR #3002's own record, the
deliverable this record follows up on.

## Open findings

PR #3006's other finding — `_self_trigger_respawn()` not consulting the
deliverable-existence gate — is explicitly out of scope for this session
(per the spawning instructions: issue #2969's fix round already
established, with a code argument, that `_self_trigger_respawn()` is
reached only after `_spawn_one()` confirmed process exit and
`roster_remove()` already deleted the roster entry, making a second
confirmation there structurally impossible — that argument is under
independent re-verification in a separate session right now). Not
addressed here.

canonical: `spawn.py` — `rc = proc.wait()` / `roster_remove(roster_key)`
run before `_self_trigger_respawn(outcome, roster_key, ...)` is called in
the same function's `finally` block — derived: `grep -n "proc.wait()\|roster_remove(roster_key)\|_self_trigger_respawn(outcome" spawn.py` — result:
```
4958:        rc = proc.wait()
4959:        roster_remove(roster_key)
5132:        _self_trigger_respawn(outcome, roster_key, cwd, issue, skill,
```

## Next steps

None — pushed as a follow-up commit on `issue-2981/merge-gates+test-derivation-2f452df8`,
updating PR #3002 directly (per the spawning instructions: "follow-up on
the SAME branch ... (PR #3002)"), rather than opening a new PR.

## Acceptance checks (executed-live)

- `python3 -m pytest tests/ -k respawn_skips_existing_deliverable -q` — result:
  ```
  ....                                                                     [100%]
  4 passed in 1.18s
  ```
- `python3 -m pytest tests/ -k respawn_proceeds_without_deliverable -q` — result:
  ```
  .......                                                                  [100%]
  7 passed in 0.95s
  ```
- `python3 -m pytest tests/ -k respawn_skip_is_reported -q` — result:
  ```
  ..                                                                       [100%]
  2 passed in 0.93s
  ```
- `python3 -m pytest test/ tests/ gates/ -q` (full sweep) — result: `16 failed, 706 passed, 3 xfailed` —
  derived: same 16 pre-existing failures reproduce identically with this
  session's changes `git stash`ed out (`16 failed, 705 passed, 3 xfailed`,
  passed count differs only by the one new test this session added); none
  of the 16 touch `gates/spawn_on_pr.py`, `gates/check_runner.py`, or
  `tests/test_respawn_deliverable_gate.py`.

skill-verdict: silent-failure-audit — applied: invoked; audited
`_branch_looks_like_deliverable()`'s two failure paths (`pr_number is
None`, `check_runner.pr_diff_paths()` returning `None` on a `gh` read
failure). Both fall through to `False` (not-a-deliverable), correctly
matching `subject_has_deliverable()`'s must-not ("absence or lookup error
must default to respawn, never to a silent skip") — verified live against
the sandbox's own `gh` failure mode (no git remote in the test tmpdir ->
`gh pr diff` exits 1 in ~20ms, no network, no hang). The audit did find one
real silent-absorption: the `gh pr diff` read failure was being folded
into the same unlogged `False` return as a genuine record-only
classification, with no way for an operator to tell "no deliverable" from
"gh degraded, defaulted to no deliverable" — a sustained `gh` outage would
silently misclassify every open PR as record-only. Fixed in the same
commit: `_branch_looks_like_deliverable()` now prints to stderr on the
`paths is None` path before returning `False` — derived: `grep -n "gh 로 못 읽었다" gates/spawn_on_pr.py` — result:
```
gates/spawn_on_pr.py:263:        print(f"[spawn-on-pr] PR #{pr_number} 의 diff 를 gh 로 못 읽었다 -- "
```
Re-ran the three acceptance checks and the full sweep after this addition
— acceptance: `python3 -m pytest tests/ -k respawn_skips_existing_deliverable -q` — result:
```
4 passed in 0.92s
```
acceptance: `python3 -m pytest tests/ -k respawn_proceeds_without_deliverable -q` — result:
```
7 passed in 1.00s
```
acceptance: `python3 -m pytest tests/ -k respawn_skip_is_reported -q` — result:
```
2 passed in 0.93s
```
acceptance: `python3 -m pytest test/ tests/ gates/ -q` — result:
```
16 failed, 706 passed, 3 xfailed
```
unchanged from before this addition, confirming the added visibility
didn't change any decision, only its observability.

other mounted skills: not triggered (work-in-english — this record and all
commit/PR text are already English; merge-gates — no gate design decision
was open here, this session consulted an already-landed gate's own
diff-content standard rather than designing a new one).
