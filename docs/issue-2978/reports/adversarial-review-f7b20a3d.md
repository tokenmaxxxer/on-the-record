---
issue: 2978
role: adversarial-review-f7b20a3d
author: adversarial-review-f7b20a3d
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: d9a6845f6f1602d918a1c3a7e95ce0c023db89b5
loop_state: landed
type: code
breaking: true
verdict: pass
upstream:
  - path: gates/spawn_on_pr.py
    sha: d9a6845f6f1602d918a1c3a7e95ce0c023db89b5
  - path: watchdog.py
    sha: d9a6845f6f1602d918a1c3a7e95ce0c023db89b5
  - path: gates/closure_sweep.py
    sha: e2ad4e5f46e54f9e9ced116ab7a40b23121b6839
---

# issue-2978 — adversarial-review-f7b20a3d record

## What was done

Independently re-verified PR #3012 (branch
`issue-2978/observability-signal-golden+test-derivation-5c7f5864`) after
its fix-round commit `d9a6845f6f1602d918a1c3a7e95ce0c023db89b5`, which
responds to PR #3021's independent-verification finding (merged commit
`7ee493e5`): `gates/spawn_on_pr.py`'s no-PR-yet discriminator (`_slug is
None`) conflated "no deliverable record ever landed" (0 non-verifying
board records — the ordinary quiet case #2978 fixed) with "2+
non-verifying records, ambiguous which is the deliverable" (a case where
a deliverable demonstrably DID land) — the second silently swallowed a
genuine #2379-class unmappable-branch report.

canonical: `gh pr view 3012 --json headRefName,headRefOid,commits`
output fetched this turn — `headRefOid: d9a6845f6f1602d918a1c3a7e95ce0c023db89b5`,
4 commits (`f0d8c2eb` PR #3012's original fix, `eb05833c`/`34b95473` PR
#3021's own record/deviation-log, `d9a6845f` the fix-round commit
responding to PR #3021's finding). canonical: `gh pr view 3021` output
fetched this turn (state: MERGED, title references "spawn-on-pr defect
found").

**Reproduction, isolated worktree.** Fetched `pull/3012/head` and added
`git worktree add /tmp/verify-2978-3012/wt d9a6845f` (separate from this
session's own checkout). Re-ran all four issue-#2978 acceptance checks
against that worktree:

```
$ python3 -m pytest tests/ -k spawn_on_pr_no_pr_yet -q
1 passed in 0.88s
$ python3 -m pytest tests/ -k spawn_on_pr_genuinely_missing_branch -q
1 passed in 0.91s
$ python3 -m pytest tests/ -k closure_sweep_record_after_merge -q
1 passed in 0.88s
$ python3 -m pytest tests/ -k closure_sweep_genuine_violation -q
1 passed in 1.00s
```
derived: the four commands above, executed live against
`d9a6845f6f1602d918a1c3a7e95ce0c023db89b5` in
`/tmp/verify-2978-3012/wt` this turn.

**Re-derived the live board population figure myself** rather than
citing PR #3021's own number — wrote a fresh script, not copied from PR
#3012's or PR #3021's own test/record files, calling
`spawn_on_pr._deliverable_candidate_count()` over the real
`spawn.board(root)` for every board subject:

```
$ python3 -c '<inline board-population script, see below>'
total subjects=700 zero=1 one=553 many(2+)=146
```
derived: inline `python3 -` heredoc script run against
`/tmp/verify-2978-3012/wt` (root `.`) this turn, calling
`spawn_on_pr.spawn.board()` and `spawn_on_pr._deliverable_candidate_count()`
directly, no mocking:
```python
b = spawn_on_pr.spawn.board(Path("."))
zero = sum(1 for sb in b.values() if spawn_on_pr._deliverable_candidate_count(sb) == 0)
many = sum(1 for sb in b.values() if spawn_on_pr._deliverable_candidate_count(sb) >= 2)
# total=700, zero=1, one=553, many(2+)=146
```
146 of 700 (derived: script above, executed this turn) matches PR
#3021's cited figure at the same magnitude on the fixed code — the fix
changes what `missing_verification()` does with that population, not the
population itself, so an unchanged count is expected, not a regression
signal.

**Reproduced PR #3021's finding against the FIXED code directly**, with
my own fixture (not reused from PR #3012's new regression test, though
that test's `SpawnOnPrAmbiguousRecordSetIsStillReported` case — read via
`git show d9a6845f:tests/test_watchdog_normal_state_not_violation_2978.py`,
a path that exists on PR #3012's branch but is untracked on this
session's own `adversarial-review-f7b20a3d` branch — constructs the same
shape and independently passed above). Two subjects, `issue-99001` (2
non-verifying records, no `verifies_subject` marker — PR #3021's
ambiguous shape) and `issue-99002` (1 verifying-only record — the
ordinary no-PR-yet shape), both called through
`spawn_on_pr.missing_verification()` with `pr_index={}` (branch
confirmed missing from the index):

```
=== AMBIGUOUS (issue-99001) ===
printed: '[spawn-on-pr] issue-99001: deliverable record 모호함 (2건,
verifies_subject 미표시로 특정 불가) — 브랜치도 pr_index 에서 찾지 못함 —
이번 틱은 건너뜀 (deficit=2)'

=== QUIET/NO-PR-YET (issue-99002) ===
printed: ''
```
derived: inline `python3 -` heredoc script run against
`/tmp/verify-2978-3012/wt` this turn, mocking only `spawn.board` and
`load_merged_seen` (not `subject_deliverable_record` or
`_deliverable_candidate_count` — those ran unmocked, on the real
production code path).

Result: the ambiguous-record-set case (PR #3021's finding) now reports
under its own message and one-shot marker; the genuinely-no-deliverable-
yet case still stays silent — the original false positive issue #2978
was filed to remove was not reintroduced. canonical: the two script
outputs quoted directly above, produced this turn.

**Code read**, `git show d9a6845f -- gates/spawn_on_pr.py` (output
quoted/paraphrased below, full diff read this turn): adds
`_deliverable_candidate_count()` (`gates/spawn_on_pr.py:224-236` on the
fix-round head), which reuses the exact same predicate
`subject_deliverable_record()` already uses
(`fm.get("verifies_subject") != "true"`) — not a new, potentially
divergent comparison:
```python
def _deliverable_candidate_count(subject_board: dict) -> int:
    return len([1 for fm in subject_board.values()
                if fm.get("verifies_subject") != "true"])
```
`missing_verification()` (`gates/spawn_on_pr.py:508-529` on the
fix-round head) branches on `candidate_count`: `0` → `continue` (silent,
matches acceptance-check 1, verified above); `2+` → reports under the
new `[spawn-on-pr] {subject}: deliverable record 모호함` message via a
new one-shot marker in its own state bucket
(`ambiguous_deliverable_record_reported` in
`watchdog.py:830-847`), separate from the pre-existing
`unmappable_subject_branch_reported` bucket so the two distinct findings
("record set is ambiguous" vs. "branch confirmed missing") don't
collapse into the same reported-once key. canonical: `git show d9a6845f
-- gates/spawn_on_pr.py` and `sed -n '790,860p' watchdog.py`, both read
this turn against `/tmp/verify-2978-3012/wt`.

**Closure-sweep half: confirmed untouched.**
```
$ git diff --stat f0d8c2eb d9a6845f -- gates/closure_sweep.py
(no output)
```
derived: the command above, executed this turn against
`/tmp/verify-2978-3012/wt` — zero-line output confirms no diff. PR
#3021's own audit of the closure-sweep half (sound, no defect) stands
unchanged since nothing there moved between PR #3012's original commit
and the fix-round head.

**Broader regression sweep, base vs. fix commit.**
```
$ python3 -m pytest tests/ gates/ test/ -q     (worktree at d9a6845f, PR #3012's fix-round head)
16 failed, 721 passed, 3 xfailed in 32.47s
$ python3 -m pytest tests/ gates/ test/ -q     (worktree at 005a3ec6, PR #3012's pre-PR base)
16 failed, 716 passed, 3 xfailed in 31.90s
```
derived: both commands, executed this turn against two separate
`git worktree` checkouts (`/tmp/verify-2978-3012/wt` at `d9a6845f`,
`/tmp/verify-2978-3012/base` at `005a3ec6`). Diffed the two `FAILED`
line-sets by eye this turn: both list the identical 16 test IDs (e.g.
`tests/test_spawn_gate_wiring.py`, class `HooksJsonWiringIsAdditive`,
failing with `fatal: 'origin' does not appear to be a git repository` —
a worktree-isolation artifact from the detached, remote-less worktree,
not code this fix introduced) — same 16 at both commits, none unique to
the fix-round head. The 716 → 721 delta is exactly the five new tests in
`tests/test_watchdog_normal_state_not_violation_2978.py` (path untracked
on this session's own branch; present on PR #3012's branch, confirmed
via `git show d9a6845f:tests/test_watchdog_normal_state_not_violation_2978.py`
this turn). Zero new regressions from this fix.

Also ran the PR's own claimed test-plan line directly:
```
$ python3 -m pytest test/test_watchdog_heartbeat_noise.py gates/test_spawn_on_pr.py -q
33 passed in 1.01s
```
derived: executed this turn against `/tmp/verify-2978-3012/wt`.

Both worktrees removed after use (`git worktree remove --force`, both
paths, this turn) — no leftover state outside this session's own
checkout. derived: `git worktree list` re-run this turn after removal,
showing only this session's own checkout.

## Why

Per the task's framing: verify independently rather than trust PR
#3012's or PR #3021's own claims. Re-derived the population figure
(derived above, "Re-derived the live board population figure myself"
paragraph: `total=700 zero=1 many(2+)=146`) from a fresh script instead
of citing PR #3021's number, built fixtures not copied from the PR's or
the test file's own constructions, and checked both the target case
(ambiguous-record-set now reports) and its inverse (no-PR-yet stays
quiet, closure-sweep untouched) rather than stopping once the primary
claim cleared — per
`defect-verification-independence-from-upstream-verdicts` (invoked this
turn via the Skill tool).

## What did not work

None.

## Upstream basis

- `gates/spawn_on_pr.py` at `d9a6845f6f1602d918a1c3a7e95ce0c023db89b5` —
  `_deliverable_candidate_count()` and the branch in
  `missing_verification()` that reports the ambiguous-record-set case.
  canonical: `git show d9a6845f -- gates/spawn_on_pr.py`, read this
  turn (quoted above under "What was done").
- `watchdog.py` at `d9a6845f6f1602d918a1c3a7e95ce0c023db89b5` —
  `_watchdog_note_ambiguous_deliverable_record()`, the new one-shot
  marker. canonical: `sed -n '790,860p' watchdog.py`, read this turn
  against `/tmp/verify-2978-3012/wt`.
- `gates/closure_sweep.py` at `e2ad4e5f46e54f9e9ced116ab7a40b23121b6839`
  (its actual last-touched sha, per `git log -1 --format=%H -- gates/closure_sweep.py`
  run this turn) — confirmed zero diff against this file between PR
  #3012's original commit (`f0d8c2eb`) and the fix-round head
  (`d9a6845f`). derived: `git diff --stat f0d8c2eb d9a6845f --
  gates/closure_sweep.py`, executed this turn (quoted above).
- PR #3021, merged commit `7ee493e5`
  (`docs/issue-2978/reports/adversarial-review-1df63424.md`, path
  present on `main`, read this turn via `git show
  7ee493e5:docs/issue-2978/reports/adversarial-review-1df63424.md`) —
  the prior finding this fix-round responds to.

## Open findings

None — none survived independent reproduction. canonical: the four
acceptance-check runs, the two hand-written repro scripts, and the two
regression sweeps, all quoted above under "What was done" and all
executed this turn against `/tmp/verify-2978-3012/wt` /
`/tmp/verify-2978-3012/base`.

## Next steps

None — terminal record.

acceptance: `python3 -m pytest tests/ -k spawn_on_pr_no_pr_yet -q` —
result:
```
1 passed in 0.88s
```
acceptance: `python3 -m pytest tests/ -k spawn_on_pr_genuinely_missing_branch -q` —
result:
```
1 passed in 0.91s
```
acceptance: `python3 -m pytest tests/ -k closure_sweep_record_after_merge -q` —
result:
```
1 passed in 0.88s
```
acceptance: `python3 -m pytest tests/ -k closure_sweep_genuine_violation -q` —
result:
```
1 passed in 1.00s
```
All four of issue #2978's acceptance checks pass on the fix-round head
(runs above, executed this turn against `/tmp/verify-2978-3012/wt`);
nothing further to do.

## Skill verdicts

- skill-verdict: adversarial-review — applied: invoked; this session's
  structure (fresh session with no access to PR #3012's or PR #3021's
  authoring reasoning, isolated `git worktree` reproduction, fixtures
  authored independently rather than reused) instantiates the
  builder/evaluator separation this skill's procedure describes — read
  via the Skill tool this turn before applying.
- skill-verdict: defect-verification-independence-from-upstream-verdicts
  — applied: invoked; re-derived the population figure from a fresh
  script instead of citing PR #3021's number (rule 3; result
  `total=700 many(2+)=146`, matching PR #3021's magnitude, derived
  above), built fixtures not copied from the PR's/test's own
  constructions (rule 2, edge case: ambiguous-record-set), and checked
  the inverse direction after the primary claim cleared rather than
  stopping (rule 4) — read via the Skill tool this turn before applying.
- skill-verdict: verify-finding-record — not-applicable: this session's
  designated record target is this file
  (`docs/issue-2978/reports/adversarial-review-f7b20a3d.md`), per the
  role skeleton and the task's explicit instruction to write the
  verdict here with `verifies_subject` set. `docs/issue-2978/reports/defect-verification.md`
  is untracked — never created for this session (checked: `git ls-files
  | grep "issue-2978/reports/defect-verification"` this turn — no
  output, exit 1; other issues' `defect-verification.md` files exist
  in this repo but none under `docs/issue-2978/`) — the skill's
  per-attempt evidentiary-rigor principles (evidence, steps, outcome
  fields) were still followed within this record's own shape.
- other mounted skills: work-in-english — applied throughout (this
  record, all commit/PR-facing text in English); not separately invoked
  via the Skill tool since it requires no procedural steps beyond the
  language policy itself.
