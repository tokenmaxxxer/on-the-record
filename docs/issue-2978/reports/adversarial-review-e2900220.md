---
issue: 2978
role: adversarial-review-e2900220
author: adversarial-review-e2900220
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: d9a6845f6f1602d918a1c3a7e95ce0c023db89b5
loop_state: landed
type: code
breaking: false
verdict: pass
upstream:
  - path: gates/spawn_on_pr.py
    sha: d9a6845f6f1602d918a1c3a7e95ce0c023db89b5
  - path: docs/issue-2978/reports/observability-signal-golden+test-derivation-5c7f5864.md
    sha: d9a6845f6f1602d918a1c3a7e95ce0c023db89b5
  - path: docs/issue-2978/reports/adversarial-review-1df63424.md
    sha: 7ee493e5bcfe76751ae5e4361de6b86275c4b6ff
---

# issue-2978 — adversarial-review-e2900220 record

## What was done

Re-verified PR #3012 (issue #2978's watchdog false-positive fix) after
its fix round responding to PR #3021's independent-verification finding.

canonical: `gh pr view 3012 --json headRefOid,headRefName` output fetched
this turn — `headRefOid: d9a6845f6f1602d918a1c3a7e95ce0c023db89b5`,
`headRefName: issue-2978/observability-signal-golden+test-derivation-5c7f5864`,
state OPEN.

Fetched that head into an isolated worktree (`git worktree add
/tmp/verify-2978-d9a6845f d9a6845f6f1602d918a1c3a7e95ce0c023db89b5`,
removed afterward) and re-ran all four of issue #2978's own acceptance
checks there:

- acceptance: `python3 -m pytest tests/ -k spawn_on_pr_no_pr_yet -q` — result:
  ```
  1 passed in 0.95s
  ```
- acceptance: `python3 -m pytest tests/ -k spawn_on_pr_genuinely_missing_branch -q` — result:
  ```
  1 passed in 0.99s
  ```
- acceptance: `python3 -m pytest tests/ -k closure_sweep_record_after_merge -q` — result:
  ```
  1 passed in 0.87s
  ```
- acceptance: `python3 -m pytest tests/ -k closure_sweep_genuine_violation -q` — result:
  ```
  1 passed in 0.94s
  ```

canonical: `git log --oneline -20` output, read this turn inside the
worktree at `d9a6845f` — the fix round is one new commit
(`d9a6845f`, "distinguish ambiguous deliverable record set from
no-PR-yet in spawn-on-pr") on top of `f0d8c2eb`, the commit PR #3021's
own `upstream:` frontmatter cited as what it audited.

Independently reproduced PR #3021's finding against the fixed code,
using fresh, self-constructed board fixtures distinct from both PR
#3021's own reproduction snippet (`issue-50001`,
`implementation`/`conformance-review`, authors carol/dave, per
`canonical: docs/issue-2978/reports/adversarial-review-1df63424.md`
read from `main` this turn) and the shipped regression test added by
this fix round in `tests/test_watchdog_normal_state_not_violation_2978.py`
(untracked on this session's own branch, existing only on the fix
branch inside the worktree; `issue-97003`,
`implementation`/`conformance-review`, authors alice/bob) — per
`defect-verification-independence-from-upstream-verdicts` rule 3
(re-derive rather than cite), run this turn inside the worktree:

```python
# Case A -- genuinely no deliverable record ever landed (the ordinary
# quiet case #2978 was filed to restore): issue-88801, one
# verifies_subject:true record only, author erin.
board_no_pr_yet = {"issue-88801": {"execution-observation":
    {"verifies_subject": "true", "author": "erin"}}}
spawn_on_pr.missing_verification(root, issue_states={88801: "OPEN"}, pr_index={})

# Case B -- ambiguous, 2+ non-verifying records (a deliverable
# demonstrably DID land, which one is ambiguous): issue-88802,
# "coding"/"execution-observation" records, authors frank/grace.
board_ambiguous = {"issue-88802": {
    "coding": {"author": "frank"},
    "execution-observation": {"author": "grace"}}}
spawn_on_pr.missing_verification(root, issue_states={88802: "OPEN"}, pr_index={})
```
result:
```
Case A: {} printed: [] unmappable_marker_called: False ambiguous_marker_called: False
Case B: {}
printed: [spawn-on-pr] issue-88802: deliverable record 모호함 (2건, verifies_subject 미표시로 특정 불가) — 브랜치도 pr_index 에서 찾지 못함 — 이번 틱은 건너뜀 (deficit=2)
ambiguous_marker_called_once: 1 unmappable_marker_called: False
```
Case A confirms the inverse also holds: the fix does not reintroduce
the original false positive (0-candidate "no PR yet" stays quiet). Case
B confirms PR #3021's finding is fixed here in this same reproduction
run: the 2+-candidate ambiguous case now reports, under its own
distinct marker/message (`_watchdog_note_ambiguous_deliverable_record`),
separate from the confirmed-single-deliverable unmappable-branch path
(`_watchdog_note_unmappable_subject_branch`, not called in Case B, per
the `unmappable_marker_called: False` result printed above).

Re-derived the live board population figure myself rather than citing
PR #3021's number — derived: `python3 -c` snippet run this turn inside
the same worktree:
```python
board = spawn_on_pr.spawn.board(Path("."))
total = len(board)
ambiguous = [s for s, sb in board.items()
             if len([1 for _, fm in sb.items()
                     if fm.get("verifies_subject") != "true"]) > 1]
zero = [s for s, sb in board.items()
        if len([1 for _, fm in sb.items()
                if fm.get("verifies_subject") != "true"]) == 0]
```
result: `total=700, ambiguous=146, zero=1, exactly-one=553` (146/700 =
20.9%) — matches the fraction PR #3021 cited in
`docs/issue-2978/reports/adversarial-review-1df63424.md` (read from
`main` this turn), re-derived independently against the current
worktree checkout rather than copied from that record.

Checked the closure-sweep half is untouched — canonical:
`docs/issue-2978/reports/adversarial-review-1df63424.md` (read from
`main` this turn), Open finding 2, states it audited
`gates/closure_sweep.py` at `f0d8c2eb` and found it sound, reusing
`check_runner.touches_implementation_paths()` verbatim. derived: `git
diff f0d8c2eb8fdf2b685203ab39b9921708ae86bab7
d9a6845f6f1602d918a1c3a7e95ce0c023db89b5 -- gates/closure_sweep.py`, run
this turn inside the worktree — result: empty diff (no output), i.e.
byte-identical to the commit that record already audited as sound.

derived: `git diff --stat f0d8c2eb8fdf2b685203ab39b9921708ae86bab7
d9a6845f6f1602d918a1c3a7e95ce0c023db89b5`, run this turn — the fix round
touches only `gates/spawn_on_pr.py` (the discriminator fix),
`spawn.py`/`watchdog.py` (a new one-shot marker function,
`_watchdog_note_ambiguous_deliverable_record`, wired through
`spawn.py`'s re-export block the same way its sibling
`_watchdog_note_unmappable_subject_branch` already is), and the fix's
own record/deviation-log/test files — no other product code touched.

Ran a broader regression sweep (not claimed by the PR's own test plan,
run to check for collateral damage from the follow-up fix) — acceptance:
`python3 -m pytest tests/ test/ gates/ -q` inside the worktree — result:
```
16 failed, 721 passed, 3 xfailed in 32.38s
```
derived: `python3 -m pytest tests/ test/ gates/ -q 2>&1 | grep "^FAILED" | sort`
run this turn — the 16 failing test names produced by that command are
byte-identical to the 16 PR #3021 already listed in `## Open findings`
of `docs/issue-2978/reports/adversarial-review-1df63424.md` (read from
`main` this turn) as pre-existing/unrelated at the prior commit
(`f0d8c2eb`) — hook-wiring and skill-selection tests untouched by this
diff (e.g. `test_convention_equivalence.py::ApprovalGateEquivalenceTest`,
`test_spawn_cross_family_skill_selection.py::*`). The `721 passed` here
vs. that record's `720 passed` at `f0d8c2eb` is exactly the one new
regression test this fix round adds
(`test_spawn_on_pr_ambiguous_record_set_still_reported`, untracked
outside the fix branch); derived: `721 - 720 = 1` matches that one new
test.

acceptance: `python3 -m pytest test/test_watchdog_heartbeat_noise.py
gates/test_spawn_on_pr.py
tests/test_watchdog_normal_state_not_violation_2978.py -q` inside the
worktree (all three paths exist on the fix branch inside the worktree;
the third is untracked outside it, per the "What was done" paragraph
above) — result:
```
38 passed in 0.88s
```

## Why

Per `defect-verification-independence-from-upstream-verdicts` (skill
invoked this session): treated PR #3021's "fail" verdict and the fix
commit's own claim of having restored the distinction as claims to
independently re-test, not facts to cite. Re-derived every figure
(board population, failing-test set) and every reproduction (both
directions of the discriminator) from fresh, self-constructed fixtures
rather than re-running or trusting the shipped test file or PR #3021's
own snippet verbatim — rule 2's edge-case requirement is satisfied by
constructing both the 0-candidate and 2+-candidate cases myself, not
just re-running the happy path the PR's own test plan claims.

canonical: the reproduction transcript and diff/pytest outputs captured
in `## What was done` above, all produced this turn inside
`/tmp/verify-2978-d9a6845f`.

Per `adversarial-review` (skill invoked this session): treated the fix's
own inline comments and commit message as claims about behavior, not as
evidence of behavior — every claim in `## What was done` above is backed
by a command this session actually ran inside an isolated worktree, not
by reading the diff's prose.

## What did not work

None.

## Upstream basis

PR #3012, branch `issue-2978/observability-signal-golden+test-derivation-5c7f5864`,
head `d9a6845f6f1602d918a1c3a7e95ce0c023db89b5`:
- `f0d8c2e` — the original fix (`gates/spawn_on_pr.py`,
  `gates/closure_sweep.py`) that PR #3021 (`7ee493e5`,
  `docs/issue-2978/reports/adversarial-review-1df63424.md`) found sound
  on the closure-sweep half and defective on the spawn-on-pr half —
  canonical: that record, read from `main` this turn.
- `d9a6845f` — this fix round's follow-up commit, resolving PR #3021's
  finding (`_deliverable_candidate_count()`, a new
  `_watchdog_note_ambiguous_deliverable_record()` one-shot marker, and
  the `spawn_on_pr_ambiguous_record_set_still_reported` regression test
  in `tests/test_watchdog_normal_state_not_violation_2978.py`, untracked
  outside the fix branch) — canonical: `git show
  d9a6845f6f1602d918a1c3a7e95ce0c023db89b5` commit message and diff,
  read this turn inside the worktree.

## Open findings

None. acceptance: `python3 -m pytest tests/ -k spawn_on_pr_no_pr_yet -q
&& python3 -m pytest tests/ -k spawn_on_pr_genuinely_missing_branch -q
&& python3 -m pytest tests/ -k closure_sweep_record_after_merge -q &&
python3 -m pytest tests/ -k closure_sweep_genuine_violation -q` (all
four run this turn inside `/tmp/verify-2978-d9a6845f`, individually
above) — result:
```
1 passed in 0.95s
1 passed in 0.99s
1 passed in 0.87s
1 passed in 0.94s
```
acceptance: `python3 -m pytest tests/ test/ gates/ -q` (regression
sweep, run this turn inside the same worktree) — result:
```
16 failed, 721 passed, 3 xfailed in 32.38s
```
together with the two independent reproduction cases (Case A/Case B)
and the re-derived `total=700, ambiguous=146` board figure and empty
`closure_sweep.py` diff in `## What was done` above, this covers every
must-not condition issue #2978 lists plus PR #3021's specific finding,
and none of them surfaced a new defect.

## Next steps

None. acceptance: `python3 -m pytest test/test_watchdog_heartbeat_noise.py
gates/test_spawn_on_pr.py tests/test_watchdog_normal_state_not_violation_2978.py -q`
(run this turn inside `/tmp/verify-2978-d9a6845f`) — result:
```
38 passed in 0.88s
```
verdict is pass, `loop_state: landed`.

skill-verdict: adversarial-review — applied: invoked; used its
evidence-over-claims discipline to treat the fix diff's own comments and
commit message as unverified claims, backing every statement in this
record with a command actually run this turn rather than a reading of
the diff's prose
skill-verdict: defect-verification-independence-from-upstream-verdicts —
applied: invoked; re-derived the board figure (`total=700,
ambiguous=146`, derived this turn per `## What was done` above) and the
16-name failing-test set independently rather than citing them, and
constructed fresh board fixtures (distinct subject names/authors from
both PR #3021's own snippet and the shipped regression test) for both
the 0-candidate and 2+-candidate reproduction cases per rule 2's
edge-case requirement
skill-verdict: verify-finding-record — not-applicable: this session's
assigned record area is docs/issue-2978/reports/adversarial-review-e2900220.md,
not docs/issue-2978/reports/defect-verification.md, which this skill
writes to exclusively
skill-verdict: work-in-english — applied: invoked; wrote this record,
all in-session commands and comments in English per the policy
